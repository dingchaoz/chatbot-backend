from typing import Any
from fastapi import APIRouter, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import json

from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.postprocessor import SimilarityPostprocessor

router = APIRouter(prefix="/chatrooms", tags=["chatrooms"])

class TestRequest(BaseModel):
    message: str

@router.post("/chatrooms/test")
async def test(request: Request, request_in: TestRequest) -> Any:
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

    # Configure response synthesizer with LLM
    response_synthesizer = get_response_synthesizer(llm=llm,streaming=True)

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
        Show statements in bullet form and show page reference after each statement. 
        And add a reference to the original sentence under each statement"""
    )

    async def generate_response():
        full_response = ""
        try:
            for chunk in response.response_gen:
                if chunk:
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                chunk = chunk.replace("data: ", "").replace("\n\n", "").replace("[DONE]", "")
                full_response += chunk
        except Exception as e:
            yield f"data: {json.dumps({'error': 'An unexpected error occurred'})}\n\n"
            return
        print(full_response)
        yield f"data: {json.dumps({'content': 'Response complete'})}\n\n"

    return StreamingResponse(generate_response(), media_type="text/event-stream")
