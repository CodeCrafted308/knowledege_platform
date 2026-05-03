from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    sender_id: str
    receiver_id: str
    content: str = Field(..., min_length=1, max_length=1000)
    message_type: str = "text"  # text, image, code, poll, etc.
    metadata: Optional[dict] = None
    is_challenge: bool = False
    thread_root_id: Optional[str] = None


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)


class MessageResponse(MessageBase):
    id: str
    sender_name: str
    receiver_name: str
    is_read: bool = False
    edited: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


class Message(MessageResponse):
    pass