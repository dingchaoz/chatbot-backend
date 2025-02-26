from typing import Any
from fastapi import APIRouter, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import json
import logging


# Configure logging
logging.basicConfig(level=logging.DEBUG)

router = APIRouter(prefix="/chatrooms", tags=["chatrooms"])

class TestRequest(BaseModel):
    message: str

@router.post("/chatrooms/test")
async def test(request: Request, request_in: TestRequest) -> Any:
    try: 
        # Use pre-initialized retriever, synthesizer, and query engine
        retriever = request.app.state.retriever
        query_engine = request.app.state.query_engine

        # Retrieve relevant information
        retrieved_docs = retriever.retrieve(request_in.message)

        # Extract the text from the retrieved documents
        context = " ".join([doc.text for doc in retrieved_docs])

        # Use the query engine to process the request with context
        response = query_engine.query(
            f"""{request_in.message}
            Context: {context}
            """
        )

        async def generate_response():
            full_response = ""
            # Collect source nodes to ensure uniqueness
            seen_node_ids = []
            referenced_context_parts = []

            try:
                # Iterate over the generator from response
                for chunk in response.response_gen:
                    if chunk:
                        # Yield the chunk as SSE data
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                        # Process the chunk as in your example
                        cleaned_chunk = chunk.replace("data: ", "").replace("\n\n", "").replace("[DONE]", "")
                        full_response += cleaned_chunk

                # Collect unique source nodes from this chunk
                for node in response.source_nodes:
                    logging.debug(f"Processing node: {node}")
                    if node.node.node_id not in seen_node_ids:
                        text = node.node.text.replace("\n", " ")
                        seen_node_ids.append(node.node.node_id)
                        index = seen_node_ids.index(node.node.node_id) + 1  # 1-based index
                        referenced_context_parts.append(f"{index}: {text}")


            except Exception as e:
                logging.error(f"Error during response generation: {e}")
                yield f"data: {json.dumps({'error': 'An unexpected error occurred'})}\n\n"
                return

            # Print the full response (for debugging or logging)
            print(full_response)
                        # Combine all unique referenced context parts
            referenced_context = "\n".join(referenced_context_parts)
            # Print the formatted referenced context
            print(f"Referenced Context:\n{referenced_context}")
            # Yield the referenced context
            yield f"data: {json.dumps({'referenced_context': referenced_context})}\n\n"
            # Signal completion
            yield f"data: {json.dumps({'content': 'Response complete'})}\n\n"

        return StreamingResponse(generate_response(), media_type="text/event-stream")

    except Exception as e:
        logging.error(f"Error in process_query: {e}")
        return StreamingResponse(
            (f"data: {json.dumps({'error': 'An unexpected error occurred'})}\n\n" for _ in range(1)),
            media_type="text/event-stream")