from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class BadgeType(str, Enum):
    NEWCOMER = "newcomer"
    RELIABLE_SOURCE = "reliable_source"
    EXPERT_CONTRIBUTOR = "expert_contributor"
    TRUSTED_AUTHOR = "trusted_author"
    KNOWLEDGE_MASTER = "knowledge_master"

class User(BaseModel):
    id: Optional[str] = None
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    hashed_password: str
    bio: Optional[str] = Field(None, max_length=500)
    profile_picture: Optional[str] = None
    reliability_score: float = Field(default=0.0, ge=0.0, le=100.0)
    badges: List[BadgeType] = Field(default_factory=lambda: [BadgeType.NEWCOMER])
    followers_count: int = Field(default=0, ge=0)
    following_count: int = Field(default=0, ge=0)
    posts_count: int = Field(default=0, ge=0)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)

    
    #@validator('password')
    #def validate_password(cls, v):
        #if len(v) < 8:
           # raise ValueError('Password must be at least 8 characters long')
        #if not any(c.isupper() for c in v):
          #  raise ValueError('Password must contain at least one uppercase letter')
        #if not any(c.islower() for c in v):
           # raise ValueError('Password must contain at least one lowercase letter')
        #if not any(c.isdigit() for c in v):
           # raise ValueError('Password must contain at least one digit')
        #return v 
    

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    reliability_score: float
    badges: List[BadgeType]
    followers_count: int
    following_count: int
    posts_count: int
    created_at: datetime
    updated_at: datetime

class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    profile_picture: Optional[str] = None
