from typing import Any
from fastapi import APIRouter, Query
from pydantic import BaseModel

from llama_index.core import Settings as LlamaSettings
from app.api.deps import SessionDep
from app.core.config import settings

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from fastapi.responses import StreamingResponse
import json
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
)
from llama_index.llms.deepseek import DeepSeek
from app import crud
from app.dto_models.chatroom import MessageCommentUpsertRequest, MessageSenderEnum
from app.utils import get_pagination_info

router = APIRouter(prefix="/chatrooms", tags=["chatrooms"])

class TestRequest(BaseModel):
    message: str

@router.get("/chatrooms")
async def get_chatrooms(
    *,
    session: SessionDep,
    limit: int = Query(10, le=100),
    offset: int = Query(0, ge=0),
) -> Any:
    """Retrieve all chatrooms."""
    result = crud.get_all_chatrooms(session=session, limit=limit, offset=offset)
    chatrooms = result["chatrooms"]
    total = result["total"]

    pagination_info = get_pagination_info(total, limit, offset)
    response = {
        "data": chatrooms,
        "pagination": {
            "count": len(chatrooms),
            "total": total,
            **pagination_info
        }
    }
    
    return response

@router.post("/chatrooms")
async def create_chatroom(
    *,
    session: SessionDep,
) -> Any:
    """Create a new chatroom."""
    new_chatroom = crud.create_chatroom(session=session)
    return {"chatroom": new_chatroom}

@router.get("/chatrooms/messages/comments")
async def get_messages_with_comments(
    *,
    session: SessionDep,
) -> Any:
    """Retrieve all messages that have comments."""
    messages_with_comments = crud.get_messages_with_comments(session=session)
    return {"data": messages_with_comments}

@router.post("/chatrooms/messages/{message_id}/comments")
async def upsert_comment(
    *,
    session: SessionDep,
    message_id: int,
    request_in: MessageCommentUpsertRequest,
) -> Any:
    """Add or update a comment for a specified message if the sender is 'ASSISTANT'."""
    message = crud.get_message(session=session, id=message_id)
    if not message or message.sender != MessageSenderEnum.ASSISTANT:
        return {"error": "Message not found."}

    result = crud.upsert_message_comment(session=session, chatroom_id=message.chatroom_id, message_id=message_id, reaction=request_in.reaction, content=request_in.content)
    return {"message": "Comment success."}

@router.delete("/chatrooms/messages/{message_id}/comments")
async def delete_comment(
    *,
    session: SessionDep,
    message_id: int
) -> Any:
    """Delete the comment for a specified message if the sender is 'ASSISTANT'."""
    result = crud.delete_comment_by_message_id(session=session, message_id=message_id)
    return result

@router.post("/chatrooms/{chatroom_id}/chat")
async def chat_in_chatroom(
    *,
    session: SessionDep,
    chatroom_id: int,
    request_in: TestRequest
) -> Any:
    chatroom = crud.get_chatroom(session=session, id=chatroom_id)
    if not chatroom:
        return {"error": "Chatroom not found."}
    
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

        user_message = crud.create_message(
            session=session,
            sender=MessageSenderEnum.USER,
            content=request_in.message,
            chatroom_id=chatroom_id,
        )
        crud.create_message(
            session=session,
            sender=MessageSenderEnum.ASSISTANT,
            content=full_response,
            chatroom_id=chatroom_id,
            previous_message_id=user_message.id
        )
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate_response(), media_type="text/event-stream")

@router.delete("/chatrooms/{chatroom_id}")
async def delete_chatroom(
    *,
    session: SessionDep,
    chatroom_id: int,
) -> Any:
    """Delete a chatroom and its associated messages and comments."""
    crud.delete_chatroom(session=session, chatroom_id=chatroom_id)
    return {"message": "Chatroom deleted."}

@router.get("/chatrooms/{chatroom_id}/messages")
async def get_messages_by_chatroom(
    *,
    session: SessionDep,
    chatroom_id: int,
    limit: int = Query(10, le=100),
    offset: int = Query(0, ge=0),
) -> Any:
    """Retrieve messages for a specified chatroom with pagination."""
    result = crud.get_messages_by_chatroom_id(session=session, chatroom_id=chatroom_id, limit=limit, offset=offset)

    messages = result["messages"]
    total = result["total"]

    pagination_info = get_pagination_info(total, limit, offset)
    response = {
        "data": messages,
        "pagination": {
            "count": len(messages),
            "total": total,
            **pagination_info
        }
    }
    
    return response
