from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class ConnectionStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class Connection(BaseModel):
    id: Optional[str] = None
    requester_id: str
    requested_id: str
    status: ConnectionStatus = ConnectionStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ConnectionRequest(BaseModel):
    requested_id: str

class ConnectionResponse(BaseModel):
    id: str
    requester_id: str
    requested_id: str
    status: ConnectionStatus
    created_at: datetime
    updated_at: datetime
