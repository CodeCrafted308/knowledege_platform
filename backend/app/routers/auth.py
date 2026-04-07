from fastapi import APIRouter, HTTPException, Depends, status, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import timedelta, datetime
from typing import Any

from app.database import get_database
from app.models import UserCreate, UserLogin, UserResponse, User # Added User here
from app.utils.auth import verify_password, get_password_hash, create_access_token, verify_token
from app.services.user_service import UserService

router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Register a new user"""
    user_service = UserService(db)
    
    if await user_service.get_user_by_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if await user_service.get_user_by_username(user_data.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Hash the password
    hashed_password = get_password_hash(str(user_data.password))
    
    # Create the user
    user = await user_service.create_user(user_data, hashed_password)
    
    # Standardize data for response
    user_dict = user.model_dump() if hasattr(user, 'model_dump') else user.dict()
    return UserResponse(**user_dict)

@router.post("/login")
async def login(user_credentials: UserLogin, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Login user and return access token"""
    
    # 1. Fetch the raw document from MongoDB directly to ensure we get 'hashed_password'
    user_doc = await db.users.find_one({"email": user_credentials.email})
    
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # 2. Get the hashed password from the dictionary
    db_hashed_password = user_doc.get("hashed_password")
    
    if not db_hashed_password:
        raise HTTPException(
            status_code=500, 
            detail="User data is corrupted: missing password hash"
        )

    # 3. Verify password
    if not verify_password(str(user_credentials.password), db_hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # 4. Convert doc to User model for token creation (handles id/_id conversion)
    user_doc["id"] = str(user_doc.pop("_id"))
    user = User(**user_doc)
    
    # 5. Create access token
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    
    # 6. Prepare UserResponse
    user_data = user.model_dump() if hasattr(user, 'model_dump') else user.dict()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user_data)
    }

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Dependency to validate token and return current user"""
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get profile of the currently logged-in user"""
    user_data = current_user.model_dump() if hasattr(current_user, 'model_dump') else current_user.dict()
    return UserResponse(**user_data)