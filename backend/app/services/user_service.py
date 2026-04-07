from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from datetime import datetime

from app.models import User, UserCreate, UserResponse, BadgeType
from app.utils.auth import get_password_hash

class UserService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db.users
    
    async def create_user(self, user_data: UserCreate, hashed_password: str) -> UserResponse:
        """Create a new user"""
        user_dict = {
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "bio": user_data.bio,
            "hashed_password": hashed_password,
            "reliability_score": 0.0,
            "badges": [BadgeType.NEWCOMER],
            "followers_count": 0,
            "following_count": 0,
            "posts_count": 0,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        try:
            result = await self.users_collection.insert_one(user_dict)
            user_dict["id"] = str(result.inserted_id)
            return UserResponse(**user_dict)
        except DuplicateKeyError:
            raise Exception("User already exists")
    
    async def get_user_by_email(self, email: str) -> User:
        """Get user by email"""
        user_doc = await self.users_collection.find_one({"email": email})
        if user_doc:
            user_doc["id"] = str(user_doc.pop("_id"))
            return User(**user_doc)
        return None
    
    async def get_user_by_username(self, username: str) -> User:
        """Get user by username"""
        user_doc = await self.users_collection.find_one({"username": username})
        if user_doc:
            user_doc["id"] = str(user_doc.pop("_id"))
            return User(**user_doc)
        return None
    
    async def get_user_by_id(self, user_id: str) -> User:
        """Get user by ID"""
        try:
            obj_id = ObjectId(user_id)
            user_doc = await self.users_collection.find_one({"_id": obj_id})
            if user_doc:
                user_doc["id"] = str(user_doc.pop("_id"))
                return User(**user_doc)
        except:
            pass
        return None
    
    async def update_user_reliability_score(self, user_id: str, new_score: float):
        """Update user's reliability score"""
        await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "reliability_score": new_score,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    async def update_user_badges(self, user_id: str, badges: list):
        """Update user's badges"""
        await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "badges": badges,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    async def increment_posts_count(self, user_id: str):
        """Increment user's posts count"""
        await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$inc": {"posts_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
    
    async def increment_followers_count(self, user_id: str):
        """Increment user's followers count"""
        await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$inc": {"followers_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
    
    async def increment_following_count(self, user_id: str):
        """Increment user's following count"""
        await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$inc": {"following_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
