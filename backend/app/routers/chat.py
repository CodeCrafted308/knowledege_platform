from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi import status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
import json
from datetime import datetime

from app.database import get_database
from app.models import MessageCreate, MessageResponse, MessageUpdate, User
from app.services import ChatService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory storage for active connections (user_id -> websocket)
active_connections = {}

@router.websocket("/ws/{user_id}")
async def chat_websocket(websocket: WebSocket, user_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    await websocket.accept()
    active_connections[user_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Validate message
            if "receiver_id" not in message_data or "content" not in message_data:
                await websocket.send_text(json.dumps({"error": "Invalid message format"}))
                continue

            message_create = MessageCreate(
                sender_id=user_id,
                receiver_id=message_data["receiver_id"],
                content=message_data["content"],
                message_type=message_data.get("message_type", "text")
            )

            chat_service = ChatService(db)
            message = await chat_service.send_message(message_create)

            # Send to receiver if online
            if message_data["receiver_id"] in active_connections:
                receiver_ws = active_connections[message_data["receiver_id"]]
                await receiver_ws.send_text(json.dumps({
                    "type": "new_message",
                    "message": message.model_dump(mode="json")
                }))

            # Confirm to sender
            await websocket.send_text(json.dumps({
                "type": "message_sent",
                "message": message.model_dump(mode="json")
            }))

    except WebSocketDisconnect:
        del active_connections[user_id]

@router.get("/conversations", response_model=List[dict])
async def get_recent_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    chat_service = ChatService(db)
    conversations = await chat_service.get_recent_conversations(str(current_user.id))
    return conversations

@router.put("/message/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: str,
    message_update: MessageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    chat_service = ChatService(db)
    updated_message = await chat_service.update_message(message_id, str(current_user.id), message_update.content)
    if not updated_message:
        raise HTTPException(status_code=404, detail="Message not found or not owned by the user")
    return MessageResponse(**updated_message)

@router.delete("/message/{message_id}")
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    chat_service = ChatService(db)
    deleted = await chat_service.delete_message(message_id, str(current_user.id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Message not found or not owned by the user")
    return {"deleted": True}

class ExportRequest(BaseModel):
    title: Optional[str] = None

@router.post("/message/{message_id}/export")
async def export_message_to_kb(
    message_id: str,
    export_request: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    chat_service = ChatService(db)
    article = await chat_service.export_message_to_article(
        message_id,
        str(current_user.id),
        current_user.full_name,
        current_user.reliability_score,
        current_user.is_admin,
        export_request.title
    )
    if not article:
        raise HTTPException(status_code=404, detail="Message not found or not authorized")
    return article

@router.get("/knowledge-suggestions")
async def get_knowledge_suggestions(
    q: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    chat_service = ChatService(db)
    suggestions = await chat_service.get_knowledge_suggestions(q)
    return suggestions

@router.put("/challenge/{challenge_id}/best-answer/{answer_id}")
async def mark_best_answer(
    challenge_id: str,
    answer_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    chat_service = ChatService(db)
    updated = await chat_service.mark_best_answer(challenge_id, answer_id, str(current_user.id), current_user.is_admin)
    if not updated:
        raise HTTPException(status_code=404, detail="Challenge not found or not authorized")
    return {"marked_best_answer": True}

@router.get("/challenges/solved")
async def get_solved_challenges(db: AsyncIOMotorDatabase = Depends(get_database)):
    chat_service = ChatService(db)
    solved = await chat_service.get_solved_challenges()
    return solved

@router.get("/conversation/{other_user_id}", response_model=List[MessageResponse])
async def get_conversation(
    other_user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    chat_service = ChatService(db)
    messages = await chat_service.get_conversation(str(current_user.id), other_user_id)
    await chat_service.mark_messages_read(str(current_user.id), other_user_id)
    return messages

@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    chat_service = ChatService(db)
    count = await chat_service.get_unread_count(str(current_user.id))
    return {"unread_count": count}

@router.get("/active-users")
async def get_active_users(db: AsyncIOMotorDatabase = Depends(get_database)):
    # Return list of active user IDs
    return {"active_users": list(active_connections.keys())}