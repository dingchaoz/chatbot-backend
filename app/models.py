from typing import Optional

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime, timedelta, timezone

class BaseSQLModel(SQLModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False, sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)})

class Chatroom(BaseSQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    messages: list["Message"] = Relationship(back_populates="chatroom")

class Message(BaseSQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sender: str
    content: str
    chatroom_id: int = Field(foreign_key="chatroom.id")
    previous_message_id: Optional[int] = Field(default=None, foreign_key="message.id")
    chatroom: Chatroom = Relationship(back_populates="messages")
    comment: Optional["MessageComment"] = Relationship(back_populates="message")

class MessageComment(BaseSQLModel, table=True):
    __tablename__ = "message_comment"
    id: Optional[int] = Field(default=None, primary_key=True)
    chatroom_id: int = Field(foreign_key="chatroom.id")
    message_id: int = Field(foreign_key="message.id")
    reaction: str
    content: str
    message: Optional["Message"] = Relationship(back_populates="comment")
