from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from bson import ObjectId
from datetime import datetime
from pathlib import Path
import uuid

from app.database import get_database
from app.models import UserResponse, UserUpdate
from app.services.user_service import UserService
from app.services.badge_service import BadgeService
from app.routers.auth import get_current_user
from app.utils.auth import get_password_hash

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(**current_user.dict())

@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update current user profile including password handling"""
    user_service = UserService(db)
    
    # Use model_dump for Pydantic v2 compatibility
    # exclude_unset=True ensures we only touch fields the user actually changed
    update_data = user_update.model_dump(exclude_unset=True) if hasattr(user_update, 'model_dump') else user_update.dict(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields were provided to update"
        )
    
    # If the user is updating their password, hash it before saving
    if "password" in update_data and update_data["password"]:
        raw_password = str(update_data.pop("password"))
        update_data["hashed_password"] = get_password_hash(raw_password)
    
    # Add timestamp
    update_data["updated_at"] = datetime.utcnow()
    
    # Update user in database using the current_user's ID
    result = await user_service.users_collection.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": update_data}
    )
    
    # Return the fresh data from the DB
    updated_user = await user_service.get_user_by_id(current_user.id)
    
    # Handle the conversion to UserResponse safely
    user_dict = updated_user.model_dump() if hasattr(updated_user, 'model_dump') else updated_user.dict()
    return UserResponse(**user_dict)

@router.post("/me/profile-picture", response_model=UserResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Upload or update the current user's profile picture."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are supported for profile pictures."
        )

    upload_dir = Path(__file__).resolve().parent.parent.parent.parent / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = upload_dir / unique_filename

    content_bytes = await file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content_bytes)

    profile_picture_url = f"/uploads/{unique_filename}"

    user_service = UserService(db)
    await user_service.users_collection.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"profile_picture": profile_picture_url, "updated_at": datetime.utcnow()}}
    )

    updated_user = await user_service.get_user_by_id(current_user.id)
    user_dict = updated_user.model_dump() if hasattr(updated_user, 'model_dump') else updated_user.dict()
    return UserResponse(**user_dict)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get a specific user's profile"""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**user.dict())

@router.get("/{user_id}/badges")
async def get_user_badges(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get user's badges and progress"""
    user_service = UserService(db)
    badge_service = BadgeService()
    
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    all_badges_info = badge_service.get_all_badges_info()
    next_badge_progress = badge_service.get_next_badge_progress(
        user.reliability_score, user.posts_count
    )
    
    return {
        "current_badges": [badge.value for badge in user.badges],
        "reliability_score": user.reliability_score,
        "posts_count": user.posts_count,
        "all_badges": all_badges_info,
        "next_badge_progress": next_badge_progress
    }

@router.get("/", response_model=List[UserResponse])
async def search_users(
    q: str = None,
    limit: int = 10,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Search users by name or username, or get top users"""
    user_service = UserService(db)
    
    if q:
        # Search users
        users = []
        cursor = user_service.users_collection.find({
            "$or": [
                {"username": {"$regex": q, "$options": "i"}},
                {"full_name": {"$regex": q, "$options": "i"}}
            ]
        }).limit(limit)
        
        async for user_doc in cursor:
            user_doc["id"] = str(user_doc.pop("_id"))
            users.append(UserResponse(**user_doc))
    else:
        # Get top users by reliability score
        users = []
        cursor = user_service.users_collection.find(
            {"is_active": True}
        ).sort("reliability_score", -1).limit(limit)
        
        async for user_doc in cursor:
            user_doc["id"] = str(user_doc.pop("_id"))
            users.append(UserResponse(**user_doc))
    
    return users