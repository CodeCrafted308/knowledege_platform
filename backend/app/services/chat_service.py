from datetime import datetime
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument
from bson import ObjectId

from app.models import Message, MessageCreate, MessageResponse, User, PostCreate
from app.services.post_service import PostService


class ChatService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.messages_collection = db.messages
        self.users_collection = db.users

    async def send_message(self, message: MessageCreate) -> MessageResponse:
        # Get sender and receiver names
        sender = await self.users_collection.find_one({"_id": ObjectId(message.sender_id)})
        receiver = await self.users_collection.find_one({"_id": ObjectId(message.receiver_id)})

        if not sender or not receiver:
            raise ValueError("Sender or receiver not found")

        message_doc = {
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "content": message.content,
            "message_type": message.message_type,
            "metadata": message.metadata or {},
            "is_challenge": message.is_challenge,
            "thread_root_id": message.thread_root_id,
            "challenge_status": "open" if message.is_challenge else None,
            "best_answer_id": None,
            "sender_name": sender["full_name"] or sender["username"],
            "receiver_name": receiver["full_name"] or receiver["username"],
            "is_read": False,
            "created_at": datetime.utcnow()
        }

        result = await self.messages_collection.insert_one(message_doc)
        message_doc["id"] = str(result.inserted_id)

        return MessageResponse(**message_doc)

    async def get_conversation(self, user_id: str, other_user_id: str, limit: int = 50) -> List[MessageResponse]:
        # Get messages between two users
        query = {
            "$or": [
                {"sender_id": user_id, "receiver_id": other_user_id},
                {"sender_id": other_user_id, "receiver_id": user_id}
            ]
        }

        messages = await self.messages_collection.find(query).sort("created_at", -1).limit(limit).to_list(length=None)
        messages.reverse()  # Oldest first

        return [MessageResponse(id=str(msg["_id"]), **{k: v for k, v in msg.items() if k != "_id"}) for msg in messages]

    async def mark_messages_read(self, user_id: str, other_user_id: str):
        # Mark messages from other_user to user as read
        await self.messages_collection.update_many(
            {"sender_id": other_user_id, "receiver_id": user_id, "is_read": False},
            {"$set": {"is_read": True}}
        )

    async def get_unread_count(self, user_id: str) -> int:
        # Count unread messages for user
        return await self.messages_collection.count_documents(
            {"receiver_id": user_id, "is_read": False}
        )

    async def get_knowledge_suggestions(self, query: str, limit: int = 5) -> List[dict]:
        post_service = PostService(self.db)
        return await post_service.search_posts(query=query, skip=0, limit=limit)

    async def export_message_to_article(
        self,
        message_id: str,
        user_id: str,
        author_name: str,
        author_reliability_score: float,
        is_admin: bool,
        title: Optional[str] = None
    ) -> Optional[dict]:
        try:
            message_doc = await self.messages_collection.find_one({"_id": ObjectId(message_id)})
        except Exception:
            return None

        if not message_doc:
            return None

        if message_doc.get("sender_id") != user_id and not is_admin:
            return None

        other_user_id = message_doc["receiver_id"] if message_doc["sender_id"] == user_id else message_doc["sender_id"]
        conversation = await self.get_conversation(user_id, other_user_id, limit=50)
        article_title = title or f"Chat summary: {message_doc['content'][:60]}"
        article_content = self._format_conversation_for_article(conversation, message_doc)

        post_service = PostService(self.db)
        post_data = PostCreate(
            title=article_title,
            content=article_content,
            post_type="article",
            tags=["chat-export"]
        )

        article = await post_service.create_post(
            post_data=post_data,
            author_id=user_id,
            author_name=author_name,
            author_reliability_score=author_reliability_score
        )

        return article

    def _format_conversation_for_article(self, messages: List[MessageResponse], root_message: dict) -> str:
        lines = [
            f"## Summary of the conversation exported from chat",
            f"**Context:** {root_message.get('content', '')}",
            "",
            "### Why this matters",
            "The following content has been collated from a real chat thread and formatted as a clean, shareable article.",
            "",
            "### Conversation transcript"
        ]

        for msg in messages:
            role_label = "You" if msg.sender_id == root_message.get("sender_id") else msg.sender_name
            lines.append(f"**{role_label}**: {msg.content}")

        lines.append("")
        lines.append("---")
        lines.append("*Original chat thread provides context for this knowledge export.*")
        if root_message.get("id"):
            lines.append(f"*Source message ID: {root_message.get('id')}*")
        return "\n\n".join(lines)

    async def mark_best_answer(self, challenge_id: str, answer_id: str, user_id: str, is_admin: bool = False) -> bool:
        try:
            challenge = await self.messages_collection.find_one({"_id": ObjectId(challenge_id), "is_challenge": True})
        except Exception:
            return False

        if not challenge:
            return False

        if challenge.get("sender_id") != user_id and not is_admin:
            return False

        answer = await self.messages_collection.find_one({"_id": ObjectId(answer_id), "thread_root_id": challenge_id})
        if not answer:
            return False

        await self.messages_collection.update_one(
            {"_id": ObjectId(challenge_id)},
            {
                "$set": {
                    "best_answer_id": answer_id,
                    "challenge_status": "solved"
                }
            }
        )
        return True

    async def get_solved_challenges(self, limit: int = 20) -> List[dict]:
        challenges = []
        cursor = self.messages_collection.find({"is_challenge": True, "challenge_status": "solved"}).sort("updated_at", -1).limit(limit)
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            challenges.append(doc)
        return challenges

    async def update_message(self, message_id: str, user_id: str, content: str) -> Optional[dict]:
        updated = await self.messages_collection.find_one_and_update(
            {"_id": ObjectId(message_id), "sender_id": user_id},
            {
                "$set": {
                    "content": content,
                    "edited": True,
                    "updated_at": datetime.utcnow()
                }
            },
            return_document=ReturnDocument.AFTER
        )
        if updated:
            updated["id"] = str(updated.pop("_id"))
            return updated
        return None

    async def delete_message(self, message_id: str, user_id: str) -> bool:
        result = await self.messages_collection.delete_one(
            {"_id": ObjectId(message_id), "sender_id": user_id}
        )
        return result.deleted_count == 1

    async def get_recent_conversations(self, user_id: str, limit: int = 20) -> List[dict]:
        # Get recent conversations with last message
        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"sender_id": user_id},
                        {"receiver_id": user_id}
                    ]
                }
            },
            {
                "$sort": {"created_at": -1}
            },
            {
                "$group": {
                    "_id": {
                        "$cond": {
                            "if": {"$eq": ["$sender_id", user_id]},
                            "then": "$receiver_id",
                            "else": "$sender_id"
                        }
                    },
                    "last_message": {"$first": "$$ROOT"},
                    "unread_count": {
                        "$sum": {
                            "$cond": {
                                "if": {"$and": [{"$eq": ["$receiver_id", user_id]}, {"$eq": ["$is_read", False]}]},
                                "then": 1,
                                "else": 0
                            }
                        }
                    }
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "let": {"userId": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": ["$_id", {"$toObjectId": "$$userId"}]
                                }
                            }
                        }
                    ],
                    "as": "user"
                }
            },
            {
                "$unwind": "$user"
            },
            {
                "$project": {
                    "user_id": "$_id",
                    "username": "$user.username",
                    "full_name": "$user.full_name",
                    "last_message": {
                        "id": {"$toString": "$last_message._id"},
                        "sender_id": "$last_message.sender_id",
                        "receiver_id": "$last_message.receiver_id",
                        "content": "$last_message.content",
                        "message_type": "$last_message.message_type",
                        "sender_name": "$last_message.sender_name",
                        "receiver_name": "$last_message.receiver_name",
                        "is_read": "$last_message.is_read",
                        "created_at": "$last_message.created_at"
                    },
                    "unread_count": 1
                }
            },
            {
                "$limit": limit
            }
        ]

        conversations = await self.messages_collection.aggregate(pipeline).to_list(length=None)
        return conversations