from typing import Optional

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime, timedelta, timezone

class BaseSQLModel(SQLModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False, sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)})

class Chatroom(BaseSQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    messages: list["Message"] = Relationship(back_populates="chatroom")

class Message(BaseSQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sender: str
    content: str
    chatroom_id: int = Field(foreign_key="chatroom.id")
    previous_message_id: Optional[int] = Field(default=None, foreign_key="message.id")
    execution_time: Optional[int] = Field(default=None)
    comment_reaction: Optional[str] = Field(default=None)
    comment_content: Optional[str] = Field(default=None)

    chatroom: Chatroom = Relationship(back_populates="messages")
    # previous_message: Optional["Message"] = Relationship(sa_relationship_kwargs={"remote_side": "Message.id"})
    previous_message: Optional["Message"] = Relationship(
        sa_relationship_kwargs=dict(remote_side = "Message.id")
    )
    next_message: list["Message"] = Relationship(back_populates='previous_message')
