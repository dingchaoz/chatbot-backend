from typing import Any
from fastapi import APIRouter, Request
from pydantic import BaseModel

from llama_index.core import Settings as LlamaSettings
from app.core.config import settings

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from fastapi.responses import StreamingResponse
import json

router = APIRouter(prefix="/chatrooms", tags=["chatrooms"])

class TestRequest(BaseModel):
    message: str

@router.post("/chatrooms/test")
async def test(request: Request, request_in: TestRequest) -> Any:
    index = request.app.state.index
    llm = request.app.state.llm

    query_engine = index.as_query_engine(llm=llm, streaming=True, similarity_top_k=3)
    response = query_engine.query(
        f"""{request_in.message}
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
