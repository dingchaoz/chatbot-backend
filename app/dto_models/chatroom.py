from enum import Enum
from typing import Optional

from pydantic import BaseModel

class MessageSenderEnum(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"

class MessageCommentReactionEnum(str, Enum):
    LIKE = "LIKE"
    DISLIKE = "DISLIKE"

class MessageCommentUpdateRequest(BaseModel):
  comment_reaction: Optional[MessageCommentReactionEnum] = None
  comment_content: Optional[str] = None
