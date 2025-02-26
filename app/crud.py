from sqlalchemy import func
from sqlmodel import Session, desc, select, delete
from app.dto_models.chatroom import MessageSenderEnum
from app.models import Chatroom, Message, MessageComment
from sqlalchemy.orm import selectinload

def get_all_chatrooms(*, session: Session, limit: int, offset: int):
    """Retrieve all chatrooms sorted by created_at in descending order."""
    chatrooms = session.exec(
        select(Chatroom)
        .order_by(desc(Chatroom.created_at))
        .limit(limit)
        .offset(offset)
    ).all()

    total_count = session.exec(
        select(func.count())
        .select_from(Chatroom)
    ).one()

    return {
        "chatrooms": chatrooms,
        "total": total_count
    }

def create_chatroom(*, session: Session) -> Chatroom:
    """Create a new chatroom."""
    chatroom = Chatroom()
    session.add(chatroom)
    session.commit()
    session.refresh(chatroom)
    return chatroom

def delete_chatroom(*, session: Session, chatroom_id: int):
    """Delete a chatroom and its associated messages and messages comments."""
    session.exec(delete(MessageComment).where(MessageComment.chatroom_id == chatroom_id))
    session.exec(delete(Message).where(Message.chatroom_id == chatroom_id))
    session.exec(delete(Chatroom).where(Chatroom.id == chatroom_id))
    session.commit()

def get_messages_by_chatroom_id(*, session: Session, chatroom_id: int, limit: int, offset: int):
    """Retrieve all messages for a specified chatroom_id along with their comments."""
    messages = session.exec(
        select(Message)
        .where(Message.chatroom_id == chatroom_id)
        .options(selectinload(Message.comment))
        .order_by(desc(Message.created_at))
        .limit(limit)
        .offset(offset)
    ).all()

    total_count = session.exec(
        select(func.count())
        .select_from(Message)
        .where(Message.chatroom_id == chatroom_id)
    ).one()

    return {
        "messages": messages,
        "total": total_count
    }

def create_message(
        *,
        session: Session,
        sender: MessageSenderEnum,
        content: str,
        chatroom_id: int,
        previous_message_id: int = None
    ) -> Message:
    message = Message(
        sender=sender,
        content=content,
        chatroom_id=chatroom_id,
        previous_message_id=previous_message_id
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message

def upsert_message_comment(*, session: Session, chatroom_id: int, message_id: int, reaction: str, content: str):
    """Create or update a message comment."""
    # Check if the comment already exists
    existing_comment = session.exec(select(MessageComment).where(MessageComment.message_id == message_id)).first()
    if existing_comment:
        # Update existing comment
        existing_comment.reaction = reaction
        existing_comment.content = content
        session.add(existing_comment)
    else:
        # Create new comment
        new_comment = MessageComment(chatroom_id=chatroom_id, message_id=message_id, reaction=reaction, content=content)
        session.add(new_comment)
    session.commit()

def delete_comment(*, session: Session, message_id: int):
    """Delete the comment for a specified message."""
    comment_to_delete = session.exec(select(MessageComment).where(MessageComment.message_id == message_id)).first()
    if comment_to_delete:
        session.delete(comment_to_delete)
        session.commit()

def get_messages_with_comments(*, session: Session):
    """Retrieve all messages along with their associated comments."""
    statement = (
        select(Message)
        .options(selectinload(Message.comment))  # Load related MessageComments
    )
    return session.exec(statement).all()

def delete_comment_by_message_id(*, session: Session, message_id: int):
    """Delete the comment for a specified message."""
    session.exec(delete(MessageComment).where(MessageComment.message_id == message_id))

def get_message(*, session: Session, id: int):
    statement = select(Message).where(Message.id == id)
    message = session.exec(statement).first()
    return message

def get_chatroom(*, session: Session, id: int):
    statement = select(Chatroom).where(Chatroom.id == id)
    chatroom = session.exec(statement).first()
    return chatroom