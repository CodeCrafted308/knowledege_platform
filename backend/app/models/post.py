from enum import Enum
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PostType(str, Enum):
    text = "text"
    article = "article"
    question = "question"
    discussion = "discussion"


class PostBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    content: str = Field(..., min_length=1)
    post_type: PostType = PostType.text
    tags: List[str] = Field(default_factory=list)


class PostCreate(PostBase):
    pass


class MediaAttachment(BaseModel):
    url: str
    mime_type: str


class PostResponse(PostBase):
    id: str
    author_id: str
    author_name: str
    author_reliability_score: float
    reliability_score: float
    likes_count: int
    comments_count: int
    views_count: int
    is_verified: bool
    verification_reason: str
    attachments: List[MediaAttachment] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class Post(PostResponse):
    liked_by: List[str] = Field(default_factory=list)


class Comment(BaseModel):
    post_id: str
    author_id: str
    author_name: str
    author_reliability_score: float
    content: str = Field(..., min_length=1)
    parent_comment_id: Optional[str] = None
    likes_count: int = 0
    liked_by: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1)
    parent_comment_id: Optional[str] = None


class CommentResponse(CommentCreate):
    id: str
    post_id: str
    author_id: str
    author_name: str
    author_reliability_score: float
    likes_count: int
    created_at: datetime
    updated_at: datetime
