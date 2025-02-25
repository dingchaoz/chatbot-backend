from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel

from llama_index.core import Settings as LlamaSettings
from app.core.config import settings

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from fastapi.responses import StreamingResponse
import json
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
)
from llama_index.llms.deepseek import DeepSeek

router = APIRouter(prefix="/chatrooms", tags=["chatrooms"])

class TestRequest(BaseModel):
    message: str

@router.post("/chatrooms/test")
async def test(*, request_in: TestRequest) -> Any:
    llm = DeepSeek(
        model=settings.DEEPSEEK_MODEL_NAME,
        api_key=settings.DEEPSEEK_API_KEY,
        api_base=settings.DEEPSEEK_API_BASE
    )
    LlamaSettings.embed_model = HuggingFaceEmbedding(
        model_name=settings.HUGGING_FACE_EMBEDDING_MODEL_NAME
    )

    reader = SimpleDirectoryReader(input_files=[settings.PDF_FILE_PATH])
    data = reader.load_data()

    index = VectorStoreIndex.from_documents(documents=data, show_progress=True)

    query_engine = index.as_query_engine(llm=llm, streaming=True, similarity_top_k=3)
    response = query_engine.query(
        f"{request_in.message}"
        "Show statements in bullet form and show page reference after each statement. And add a reference to the original sentence under each statement"
    )

    async def generate_response():
        full_response = ""
        try:
            for chunk in response.response_gen:
                if chunk:
                    yield f"data: {json.dumps({'type': 'message', 'content': chunk})}\n\n"

                    clean_chunk = (
                        chunk
                        .replace("data: ", "")
                        .replace("\n\n", "")
                        .replace("[DONE]", "")
                    )

                    full_response += clean_chunk
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': 'An unexpected error occurred. Please try again later.'})}\n\n"
            return

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate_response(), media_type="text/event-stream")
