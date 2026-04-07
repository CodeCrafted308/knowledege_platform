from fastapi import APIRouter, HTTPException, Depends, status, Query, UploadFile, File, Form, Response
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
import os
import uuid
from pathlib import Path

from app.database import get_database
from app.models import PostCreate, PostResponse, CommentCreate, CommentResponse
from app.services.post_service import PostService
from app.routers.auth import get_current_user

router = APIRouter()

# Create uploads directory if it doesn't exist (same as main.py)
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create a new post"""
    post_service = PostService(db)

    post = await post_service.create_post(
        post_data=post_data,
        author_id=current_user.id,
        author_name=current_user.full_name,
        author_reliability_score=current_user.reliability_score
    )

    return post

@router.post("/with-file", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post_with_file(
    title: str = Form(...),
    content: str = Form(...),
    post_type: str = Form("text"),
    tags: str = Form(""),
    files: Optional[List[UploadFile]] = File(None),
    current_user = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create a new post with optional file uploads"""
    post_service = PostService(db)

    attachments = []
    if files:
        image_count = 0
        video_count = 0

        for file in files:
            if not file.filename:
                continue

            if file.content_type.startswith("image/"):
                image_count += 1
            elif file.content_type.startswith("video/"):
                video_count += 1
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only image and video files are supported."
                )

            if image_count > 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You can upload up to 5 images."
                )
            if video_count > 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You can upload up to 1 video."
                )

            file_extension = Path(file.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = UPLOAD_DIR / unique_filename

            with open(file_path, "wb") as buffer:
                content_bytes = await file.read()
                buffer.write(content_bytes)

            attachments.append({
                "url": f"/uploads/{unique_filename}",
                "mime_type": file.content_type
            })

    # Create post data
    post_data = PostCreate(
        title=title,
        content=content,
        post_type=post_type,
        tags=[tag.strip() for tag in tags.split(",") if tag.strip()]
    )

    post = await post_service.create_post_with_file(
        post_data=post_data,
        author_id=current_user.id,
        author_name=current_user.full_name,
        author_reliability_score=current_user.reliability_score,
        attachments=attachments
    )

    return post

@router.get("/", response_model=List[PostResponse])
async def get_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|likes_count|reliability_score)$"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get posts with pagination"""
    post_service = PostService(db)
    posts = await post_service.get_posts(skip=skip, limit=limit, sort_by=sort_by)
    return posts

@router.get("/search", response_model=List[PostResponse])
async def search_posts(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Search posts"""
    post_service = PostService(db)
    posts = await post_service.search_posts(query=q, skip=skip, limit=limit)
    return posts

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get a specific post"""
    post_service = PostService(db)
    post = await post_service.get_post_by_id(post_id)
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    return post

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: str,
    current_user = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete a post created by the current user"""
    post_service = PostService(db)
    post = await post_service.get_post_by_id(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this post"
        )
    await post_service.delete_post(post_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{post_id}/like")
async def like_post(
    post_id: str,
    current_user = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Like or unlike a post"""
    post_service = PostService(db)
    success = await post_service.like_post(post_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    return {"message": "Post liked/unliked successfully"}

@router.post("/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: str,
    comment_data: CommentCreate,
    current_user = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create a comment on a post"""
    post_service = PostService(db)
    
    # Check if post exists
    post = await post_service.get_post_by_id(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    comment = await post_service.create_comment(
        comment_data=comment_data,
        post_id=post_id,
        author_id=current_user.id,
        author_name=current_user.full_name,
        author_reliability_score=current_user.reliability_score
    )
    
    return comment

@router.get("/{post_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    post_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get comments for a post"""
    post_service = PostService(db)
    
    # Check if post exists
    post = await post_service.get_post_by_id(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    comments = await post_service.get_comments_by_post(post_id, skip=skip, limit=limit)
    return comments

@router.get("/user/{user_id}", response_model=List[PostResponse])
async def get_user_posts(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get posts by a specific user"""
    post_service = PostService(db)
    posts = await post_service.get_posts_by_author(user_id, skip=skip, limit=limit)
    return posts
