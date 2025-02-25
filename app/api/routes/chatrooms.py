from typing import Any
from fastapi import APIRouter, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import json
import logging
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.prompts import PromptTemplate

# Configure logging
logging.basicConfig(level=logging.DEBUG)

router = APIRouter(prefix="/chatrooms", tags=["chatrooms"])

class TestRequest(BaseModel):
    message: str

@router.post("/chatrooms/test")
async def test(request: Request, request_in: TestRequest) -> Any:
    try: 
        index = request.app.state.index
        llm = request.app.state.llm
        # memory = ChatMemoryBuffer(token_limit=1500)

        # Configure retriever with similarity_top_k = 5
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=5,
        )

        # Retrieve relevant information
        retrieved_docs = retriever.retrieve(request_in.message)

        # Extract the text from the retrieved documents
        context = " ".join([doc.text for doc in retrieved_docs])

        # Define a custom QA prompt template
        qa_prompt_tmpl = (
            "You are a helpful assistant. Below is some context retrieved from documents, followed by the chat history. "
            "Please respond to the user's message using the provided context. Format your response as bullet points, "
            "and after each statement, reference the original sentence from the context that supports it by saying (Ref: sentence).\n\n"
            "Context:\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "Given the context information and not prior knowledge, "
            "answer the query.\n"
            "Query: {query_str}\n"
            "Answer: "
        )
        qa_prompt = PromptTemplate(qa_prompt_tmpl)

        # Configure response synthesizer with LLM
        response_synthesizer = get_response_synthesizer(llm=llm,streaming=True,text_qa_template=qa_prompt)

        # Assemble query engine
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
            node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.7)],
        )

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