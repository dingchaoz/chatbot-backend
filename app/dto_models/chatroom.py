from enum import Enum

from pydantic import BaseModel

class MessageSenderEnum(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"

class MessageCommentReactionEnum(str, Enum):
    LIKE = "LIKE"
    DISLIKE = "DISLIKE"

class MessageCommentUpsertRequest(BaseModel):
  reaction: MessageCommentReactionEnum
  content: str
