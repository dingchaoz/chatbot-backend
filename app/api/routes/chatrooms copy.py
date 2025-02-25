from typing import Any
from fastapi import APIRouter, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import json

from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core import PromptTemplate
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.llms import ChatMessage, MessageRole

router = APIRouter(prefix="/chatrooms", tags=["chatrooms"])

class TestRequest(BaseModel):
    message: str

@router.post("/chatrooms/test")
async def process_query(request: Request, request_in: TestRequest) -> Any:
    # Load index and LLM from request state
    index = request.app.state.index
    llm = request.app.state.llm

    # Configure memory buffer for chat history
    memory = ChatMemoryBuffer(token_limit=1500)

    # Configure retriever with similarity_top_k = 5
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=5,
    )

    # Define a custom chat template to instruct the model
    custom_chat_template = PromptTemplate(
        """You are a helpful assistant. Below is some context retrieved from documents, followed by the chat history. Please respond to the user's message using the provided context. Format your response as bullet points, and after each statement, reference the original sentence from the context that supports it by saying (Ref: sentence).

Context:
{context_str}

Chat History:
{chat_history}

User: {user_message}

Assistant:"""
    )

    # Define prefix messages
    prefix_messages = [
        ChatMessage(content="You are an AI assistant specialized in providing information about Paul Graham's essays.", role=MessageRole.SYSTEM),
        ChatMessage(content="Feel free to ask me anything about Paul Graham's work.", role=MessageRole.ASSISTANT),
    ]

    # Create the ContextChatEngine with custom template
    chat_engine = ContextChatEngine(
        retriever=retriever,
        memory=memory,
        llm=llm,
        prefix_messages=prefix_messages

    )

    # Use stream_chat for streaming response
    response = chat_engine.stream_chat(request_in.message)
    print(response)

    async def generate_response():
        full_response = ""
        # Collect source nodes to ensure uniqueness
        seen_node_ids = set()
        referenced_context_parts = []

        try:
            # Iterate over the generator from stream_chat
            for chunk in response:
                if chunk.delta:  # Use .delta for the text content of the chunk
                    # Yield the chunk as SSE data
                    yield f"data: {json.dumps({'content': chunk.delta})}\n\n"
                    # Process the chunk as in your example
                    cleaned_chunk = chunk.delta.replace("data: ", "").replace("\n\n", "").replace("[DONE]", "")
                    full_response += cleaned_chunk

                # Collect unique source nodes from this chunk
                for node in chunk.source_nodes:
                    if node.node.node_id not in seen_node_ids:
                        seen_node_ids.add(node.node.node_id)
                        referenced_context_parts.append(f"- {node.node.text}")

        except Exception as e:
            yield f"data: {json.dumps({'error': 'An unexpected error occurred'})}\n\n"
            return

        # Print the full response (for debugging or logging)
        print(full_response)

        # Combine all unique referenced context parts
        referenced_context = "\n".join(referenced_context_parts)
        # Yield the referenced context
        yield f"data: {json.dumps({'referenced_context': referenced_context})}\n\n"
        # Signal completion
        yield f"data: {json.dumps({'content': 'Response complete'})}\n\n"

    return StreamingResponse(generate_response(), media_type="text/event-stream")
