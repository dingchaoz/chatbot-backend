from sqlalchemy import func
from sqlmodel import Session, desc, select, delete
from app.dto_models.chatroom import MessageSenderEnum
from app.models import Chatroom, Message
from sqlalchemy.orm import selectinload, aliased, joinedload

def get_chatrooms(*, session: Session, limit: int, offset: int):
    """Retrieve chatrooms."""
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
    session.exec(delete(Message).where(Message.chatroom_id == chatroom_id))
    session.exec(delete(Chatroom).where(Chatroom.id == chatroom_id))
    session.commit()

def get_messages_by_chatroom_id(*, session: Session, chatroom_id: int, limit: int, offset: int):
    """Retrieve all messages for a specified chatroom_id along with their comments."""
    messages = session.exec(
        select(Message)
        .where(Message.chatroom_id == chatroom_id)
        .order_by(desc(Message.created_at))
        .limit(limit)
        .offset(offset)
    ).all()

    print('---messages', messages)

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
        previous_message_id: int = None,
        execution_time: int = None
    ) -> Message:
    message = Message(
        sender=sender,
        content=content,
        chatroom_id=chatroom_id,
        previous_message_id=previous_message_id,
        execution_time=execution_time
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message

def update_chatroom_comment(*, session: Session, chatroom_id: int, title: str, description: str):
    """Update a chatroom comment."""
    chatroom_to_update = session.exec(select(Chatroom).where(Chatroom.id == chatroom_id)).first()
    
    if chatroom_to_update:
        chatroom_to_update.title = title
        chatroom_to_update.description = description
        session.add(chatroom_to_update)
        session.commit()

def update_message_comment(*, session: Session, message_id: int, comment_reaction: str, comment_content: str):
    """Update a message comment."""
    message_to_update = session.exec(select(Message).where(Message.id == message_id)).first()
    
    if message_to_update:
        message_to_update.comment_reaction = comment_reaction
        message_to_update.comment_content = comment_content
        session.add(message_to_update)
        session.commit()

def get_messages_with_comment(*, session: Session, limit: int, offset: int):
    """Retrieve messages with comment."""
    PreviousMessage = aliased(Message)
    messages = session.exec(
        select(Message)
        # .join(PreviousMessage, Message.previous_message_id == PreviousMessage.id, isouter=True)  # Join on previous_message_id
        # .options(selectinload(Message.previous_message))
        .options(selectinload(Message.next_message))
        # .options(joinedload(Message.previous_message))
        # .join(Message.previous_message)
        .where(
            (Message.comment_reaction.isnot(None)) | 
            (Message.comment_content.isnot(None))
        )
        .order_by(desc(Message.created_at))
        # .limit(limit)
        # .offset(offset)
    ).all()

    total_count = session.exec(
        select(func.count())
        .select_from(Message)
        .where(
            (Message.comment_reaction.isnot(None)) | 
            (Message.comment_content.isnot(None))
        )
    ).one()

    return {
        "messages": messages,
        "total": total_count
    }

def get_message(*, session: Session, id: int):
    statement = select(Message).where(Message.id == id)
    message = session.exec(statement).first()
    return message

def get_chatroom(*, session: Session, id: int):
    statement = select(Chatroom).where(Chatroom.id == id)
    chatroom = session.exec(statement).first()
    return chatroom