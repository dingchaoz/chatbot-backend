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
from app.dto_models.chatroom import MessageCommentUpdateRequest, MessageSenderEnum
from app.utils import get_pagination_info
from fastapi import APIRouter, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)

router = APIRouter(prefix="/chatrooms", tags=["chatrooms"])

class TestRequest(BaseModel):
    message: str

@router.get("")
async def get_chatrooms(
    *,
    session: SessionDep,
    limit: int = Query(10, le=100),
    offset: int = Query(0, ge=0),
) -> Any:
    """Retrieve chatrooms."""
    result = crud.get_chatrooms(session=session, limit=limit, offset=offset)
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

@router.post("")
async def create_chatroom(
    *,
    session: SessionDep,
) -> Any:
    """Create a new chatroom."""
    new_chatroom = crud.create_chatroom(session=session)
    return {"chatroom": new_chatroom}

@router.get("/messages/comments")
async def get_messages(
    *,
    session: SessionDep,
    limit: int = Query(10, le=100),
    offset: int = Query(0, ge=0),
) -> Any:
    """Retrieve messages with comment."""
    result = crud.get_messages_with_comment(session=session, limit=limit, offset=offset)
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

@router.post("/messages/{message_id}/comments")
async def upsert_comment(
    *,
    session: SessionDep,
    message_id: int,
    request_in: MessageCommentUpdateRequest,
) -> Any:
    """Update a message comment if the sender is 'ASSISTANT'."""
    message = crud.get_message(session=session, id=message_id)
    if not message or message.sender != MessageSenderEnum.ASSISTANT:
        return {"error": "Message not found."}

    crud.update_message_comment(session=session, message_id=message_id, comment_reaction=request_in.comment_reaction, comment_content=request_in.comment_content)
    return {"message": "Comment success."}

@router.post("/{chatroom_id}/chat")
async def chat_in_chatroom(
    *,
    session: SessionDep,
    chatroom_id: int,
    request_in: TestRequest,
    request: Request
) -> Any:
    
    chatroom = crud.get_chatroom(session=session, id=chatroom_id)
    if not chatroom:
        return {"error": "Chatroom not found."}
    
    start_time = time.time() 
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
                        yield f"data: {json.dumps({'type': 'message', 'content': chunk})}\n\n"
                        # Process the chunk as in your example
                        full_response += chunk

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
                yield f"data: {json.dumps({'type': 'done', 'content': 'An unexpected error occurred'})}\n\n"
                return

            execution_time = time.time() - start_time

            # Print the full response (for debugging or logging)
            print(full_response)
            # Combine all unique referenced context parts
            referenced_context = "\n\nreferenced context:\n" + "\n".join(referenced_context_parts)
            # Print the formatted referenced context
            print(f"Referenced Context:\n{referenced_context}")
            # Yield the referenced context
            yield f"data: {json.dumps({'type': 'message', 'content': referenced_context})}\n\n"

            full_response += referenced_context
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
                previous_message_id=user_message.id,
                execution_time=execution_time
            )
            if not chatroom.title:
                title = request_in.message[:100]
                description = (full_response.replace("\n", " "))[:100]
                crud.update_chatroom_comment(
                    session=session,
                    chatroom_id=chatroom_id,
                    title=title,
                    description=description
                )

            # Signal completion
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(generate_response(), media_type="text/event-stream")

    except Exception as e:
        logging.error(f"Error in process_query: {e}")
        return StreamingResponse(
            (f"data: {json.dumps({'type': 'error', 'content': 'An unexpected error occurred'})}\n\n" for _ in range(1)),
            media_type="text/event-stream")

@router.delete("/{chatroom_id}")
async def delete_chatroom(
    *,
    session: SessionDep,
    chatroom_id: int,
) -> Any:
    """Delete a chatroom and its associated messages and comments."""
    crud.delete_chatroom(session=session, chatroom_id=chatroom_id)
    return {"message": "Chatroom deleted."}

@router.get("/{chatroom_id}/messages")
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
