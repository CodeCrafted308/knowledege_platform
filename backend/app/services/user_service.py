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
            "is_admin": False,
            "is_suspended": False,
            "suspension_reason": None,
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
    
    # ====== ADMIN OPERATIONS ======
    
    async def get_all_users(self, skip: int = 0, limit: int = 50) -> tuple[list, int]:
        """Get all users with pagination"""
        users = []
        cursor = self.users_collection.find().skip(skip).limit(limit)
        async for user_doc in cursor:
            user_doc["id"] = str(user_doc.pop("_id"))
            users.append(UserResponse(**user_doc))
        
        total_count = await self.users_collection.count_documents({})
        return users, total_count
    
    async def search_users(self, query: str, skip: int = 0, limit: int = 50) -> tuple[list, int]:
        """Search users by username, email, or full name"""
        search_filter = {
            "$or": [
                {"username": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}},
                {"full_name": {"$regex": query, "$options": "i"}}
            ]
        }
        
        users = []
        cursor = self.users_collection.find(search_filter).skip(skip).limit(limit)
        async for user_doc in cursor:
            user_doc["id"] = str(user_doc.pop("_id"))
            users.append(UserResponse(**user_doc))
        
        total_count = await self.users_collection.count_documents(search_filter)
        return users, total_count
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user account completely"""
        try:
            result = await self.users_collection.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except:
            return False
    
    async def suspend_user(self, user_id: str, reason: str) -> bool:
        """Suspend a user account"""
        try:
            await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "is_suspended": True,
                        "is_active": False,
                        "suspension_reason": reason,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return True
        except:
            return False
    
    async def activate_user(self, user_id: str) -> bool:
        """Activate/unsuspend a suspended user"""
        try:
            await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "is_suspended": False,
                        "is_active": True,
                        "suspension_reason": None,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return True
        except:
            return False
    
    async def make_admin(self, user_id: str) -> bool:
        """Promote a user to admin"""
        try:
            await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "is_admin": True,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return True
        except:
            return False
    
    async def remove_admin(self, user_id: str) -> bool:
        """Demote an admin user to regular user"""
        try:
            await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "is_admin": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return True
        except:
            return False
    
    async def get_suspended_users(self) -> list:
        """Get all suspended users"""
        users = []
        cursor = self.users_collection.find({"is_suspended": True})
        async for user_doc in cursor:
            user_doc["id"] = str(user_doc.pop("_id"))
            users.append(UserResponse(**user_doc))
        return users
