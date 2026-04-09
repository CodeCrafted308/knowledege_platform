from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import List, Dict

from app.models import Post, PostCreate, PostResponse, Comment, CommentCreate, CommentResponse
from app.services.content_analysis import ContentAnalyzer
from app.services.badge_service import BadgeService
from app.services.user_service import UserService

class PostService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.posts_collection = db.posts
        self.comments_collection = db.comments
        self.content_analyzer = ContentAnalyzer()
        self.badge_service = BadgeService()
        self.user_service = UserService(db)
    
    async def create_post(self, post_data: PostCreate, author_id: str, author_name: str, 
                         author_reliability_score: float) -> PostResponse:
        """Create a new post with content analysis"""
        
        # Analyze content for reliability
        analysis = self.content_analyzer.analyze_content(
            post_data.content, author_reliability_score
        )
        
        post_dict = {
            "title": post_data.title,
            "content": post_data.content,
            "author_id": author_id,
            "author_name": author_name,
            "author_reliability_score": author_reliability_score,
            "post_type": post_data.post_type,
            "tags": post_data.tags,
            "attachments": [],
            "reliability_score": analysis["reliability_score"],
            "likes_count": 0,
            "comments_count": 0,
            "views_count": 0,
            "is_verified": analysis["reliability_score"] >= 80,
            "verification_reason": f"Reliability score: {analysis['reliability_score']:.1f}%",
            "liked_by": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.posts_collection.insert_one(post_dict)
        post_dict["id"] = str(result.inserted_id)
        
        # Update user's posts count
        await self.user_service.increment_posts_count(author_id)
        
        # Update user's reliability score based on new post
        await self._update_user_reliability_score(author_id)
        
        return PostResponse(**post_dict)
    
    async def create_post_with_file(self, post_data: PostCreate, author_id: str, author_name: str, 
                                   author_reliability_score: float, attachments: list = None) -> PostResponse:
        """Create a new post with optional file attachments"""
        
        # Analyze content for reliability
        analysis = self.content_analyzer.analyze_content(
            post_data.content, author_reliability_score
        )
        
        post_dict = {
            "title": post_data.title,
            "content": post_data.content,
            "author_id": author_id,
            "author_name": author_name,
            "author_reliability_score": author_reliability_score,
            "post_type": post_data.post_type,
            "tags": post_data.tags,
            "attachments": attachments or [],
            "reliability_score": analysis["reliability_score"],
            "likes_count": 0,
            "comments_count": 0,
            "views_count": 0,
            "is_verified": analysis["reliability_score"] >= 80,
            "verification_reason": f"Reliability score: {analysis['reliability_score']:.1f}%",
            "liked_by": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.posts_collection.insert_one(post_dict)
        post_dict["id"] = str(result.inserted_id)
        
        # Update user's posts count
        await self.user_service.increment_posts_count(author_id)
        
        # Update user's reliability score based on new post
        await self._update_user_reliability_score(author_id)
        
        return PostResponse(**post_dict)
    
    async def get_post_by_id(self, post_id: str) -> PostResponse:
        """Get a post by ID"""
        try:
            obj_id = ObjectId(post_id)
            post_doc = await self.posts_collection.find_one({"_id": obj_id})
            if post_doc:
                post_doc["id"] = str(post_doc.pop("_id"))
                return PostResponse(**post_doc)
        except:
            pass
        return None
    
    async def get_posts(self, skip: int = 0, limit: int = 10, sort_by: str = "created_at") -> List[PostResponse]:
        """Get posts with pagination"""
        posts = []
        cursor = self.posts_collection.find().sort(sort_by, -1).skip(skip).limit(limit)
        
        async for post_doc in cursor:
            post_doc["id"] = str(post_doc.pop("_id"))
            posts.append(PostResponse(**post_doc))
        
        return posts
    
    async def get_posts_by_author(self, author_id: str, skip: int = 0, limit: int = 10) -> List[PostResponse]:
        """Get posts by a specific author"""
        posts = []
        cursor = self.posts_collection.find({"author_id": author_id}).sort("created_at", -1).skip(skip).limit(limit)
        
        async for post_doc in cursor:
            post_doc["id"] = str(post_doc.pop("_id"))
            posts.append(PostResponse(**post_doc))
        
        return posts
    
    async def like_post(self, post_id: str, user_id: str) -> bool:
        """Like or unlike a post"""
        try:
            obj_id = ObjectId(post_id)
            post = await self.posts_collection.find_one({"_id": obj_id})
            
            if not post:
                return False
            
            if user_id in post.get("liked_by", []):
                # Unlike the post
                await self.posts_collection.update_one(
                    {"_id": obj_id},
                    {
                        "$pull": {"liked_by": user_id},
                        "$inc": {"likes_count": -1},
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
            else:
                # Like the post
                await self.posts_collection.update_one(
                    {"_id": obj_id},
                    {
                        "$push": {"liked_by": user_id},
                    "$inc": {"likes_count": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                    }
                )
            
            return True
        except:
            return False
    
    async def delete_post(self, post_id: str) -> bool:
        """Delete a post and its comments."""
        try:
            obj_id = ObjectId(post_id)
            result = await self.posts_collection.delete_one({"_id": obj_id})
            if result.deleted_count == 0:
                return False
            await self.comments_collection.delete_many({"post_id": post_id})
            return True
        except:
            return False
    
    async def create_comment(self, comment_data: CommentCreate, post_id: str, 
                           author_id: str, author_name: str, author_reliability_score: float) -> CommentResponse:
        """Create a new comment"""
        
        comment_dict = {
            "post_id": post_id,
            "author_id": author_id,
            "author_name": author_name,
            "author_reliability_score": author_reliability_score,
            "content": comment_data.content,
            "parent_comment_id": comment_data.parent_comment_id,
            "likes_count": 0,
            "liked_by": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.comments_collection.insert_one(comment_dict)
        comment_dict["id"] = str(result.inserted_id)
        
        # Update post's comments count
        await self.posts_collection.update_one(
            {"_id": ObjectId(post_id)},
            {
                "$inc": {"comments_count": 1},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return CommentResponse(**comment_dict)
    
    async def get_comments_by_post(self, post_id: str, skip: int = 0, limit: int = 50) -> List[CommentResponse]:
        """Get comments for a post"""
        comments = []
        cursor = self.comments_collection.find({"post_id": post_id}).sort("created_at", 1).skip(skip).limit(limit)
        
        async for comment_doc in cursor:
            comment_doc["id"] = str(comment_doc.pop("_id"))
            comments.append(CommentResponse(**comment_doc))
        
        return comments
    
    async def search_posts(self, query: str, skip: int = 0, limit: int = 10) -> List[PostResponse]:
        """Search posts by title, content, or tags"""
        posts = []
        search_filter = {
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"content": {"$regex": query, "$options": "i"}},
                {"tags": {"$in": [query]}}
            ]
        }
        
        cursor = self.posts_collection.find(search_filter).sort("created_at", -1).skip(skip).limit(limit)
        
        async for post_doc in cursor:
            post_doc["id"] = str(post_doc.pop("_id"))
            posts.append(PostResponse(**post_doc))
        
        return posts
    
    async def _update_user_reliability_score(self, user_id: str):
        """Update user's reliability score based on their posts"""
        # Get all user's posts
        posts = await self.get_posts_by_author(user_id, skip=0, limit=100)
        
        if not posts:
            return
        
        # Calculate average reliability score from posts
        total_score = sum(post.reliability_score for post in posts)
        avg_score = round(total_score / len(posts), 2)  # FIX: Round for determinism
        
        # Update user's reliability score
        await self.user_service.update_user_reliability_score(user_id, avg_score)
        
        # Update user's badges
        user = await self.user_service.get_user_by_id(user_id)
        if user:
            new_badges = self.badge_service.evaluate_user_badges(
                avg_score, len(posts), user.badges
            )
            await self.user_service.update_user_badges(user_id, new_badges)
