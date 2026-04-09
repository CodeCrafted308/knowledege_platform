from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

from app.database import get_database
from app.models import UserResponse
from app.utils.auth import verify_token
from app.services.user_service import UserService

router = APIRouter()
security = HTTPBearer()

def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract and verify token to get current user"""
    token = credentials.credentials
    payload = verify_token(token)
    return payload

async def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncIOMotorDatabase = Depends(get_database)):
    """Verify that the current user is an admin"""
    token = credentials.credentials
    payload = verify_token(token)
    
    user_service = UserService(db)
    user = await user_service.get_user_by_email(payload.get("email"))
    
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user

@router.get("/users", response_model=dict)
async def get_all_users(
    skip: int = 0,
    limit: int = 50,
    admin = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all users (Admin only)"""
    user_service = UserService(db)
    users, total_count = await user_service.get_all_users(skip, limit)
    
    return {
        "users": users,
        "total": total_count,
        "skip": skip,
        "limit": limit
    }

@router.get("/users/search", response_model=dict)
async def search_users(
    query: str,
    skip: int = 0,
    limit: int = 50,
    admin = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Search users by username, email, or full name (Admin only)"""
    if not query or len(query) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query must be at least 2 characters"
        )
    
    user_service = UserService(db)
    users, total_count = await user_service.search_users(query, skip, limit)
    
    return {
        "users": users,
        "total": total_count,
        "query": query,
        "skip": skip,
        "limit": limit
    }

@router.get("/users/suspended", response_model=List[UserResponse])
async def get_suspended_users(
    admin = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all suspended users (Admin only)"""
    user_service = UserService(db)
    users = await user_service.get_suspended_users()
    return users

@router.post("/users/{user_id}/delete")
async def delete_user(
    user_id: str,
    admin = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete a user account (Admin only)"""
    user_service = UserService(db)
    
    # Verify the user exists
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow deleting other admins
    if user.is_admin and user.id != admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete another admin account"
        )
    
    success = await user_service.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
    
    return {
        "message": f"User {user.username} has been deleted",
        "user_id": user_id,
        "status": "deleted"
    }

@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    reason: str,
    admin = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Suspend a user account (Admin only)"""
    user_service = UserService(db)
    
    # Verify the user exists
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow suspending other admins
    if user.is_admin and user.id != admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot suspend another admin account"
        )
    
    success = await user_service.suspend_user(user_id, reason)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend user"
        )
    
    return {
        "message": f"User {user.username} has been suspended",
        "user_id": user_id,
        "reason": reason,
        "status": "suspended"
    }

@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Activate/unsuspend a user account (Admin only)"""
    user_service = UserService(db)
    
    # Verify the user exists
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = await user_service.activate_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )
    
    return {
        "message": f"User {user.username} has been activated",
        "user_id": user_id,
        "status": "activated"
    }

@router.post("/users/{user_id}/make-admin")
async def make_admin(
    user_id: str,
    admin = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Promote a user to admin (Admin only)"""
    user_service = UserService(db)
    
    # Verify the user exists
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already an admin"
        )
    
    success = await user_service.make_admin(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to promote user to admin"
        )
    
    return {
        "message": f"User {user.username} has been promoted to admin",
        "user_id": user_id,
        "status": "admin"
    }

@router.post("/users/{user_id}/remove-admin")
async def remove_admin(
    user_id: str,
    admin = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Demote an admin user to regular user (Admin only)"""
    user_service = UserService(db)
    
    # Verify the user exists
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not an admin"
        )
    
    # Prevent removing your own admin privileges
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot remove your own admin privileges"
        )
    
    success = await user_service.remove_admin(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to demote admin"
        )
    
    return {
        "message": f"User {user.username} has been demoted from admin",
        "user_id": user_id,
        "status": "regular_user"
    }

@router.get("/dashboard")
async def get_dashboard_stats(
    admin = Depends(verify_admin),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get admin dashboard statistics (Admin only)"""
    user_collection = db.users
    
    total_users = await user_collection.count_documents({})
    active_users = await user_collection.count_documents({"is_active": True, "is_suspended": False})
    suspended_users = await user_collection.count_documents({"is_suspended": True})
    admin_users = await user_collection.count_documents({"is_admin": True})
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "suspended_users": suspended_users,
        "admin_users": admin_users
    }
