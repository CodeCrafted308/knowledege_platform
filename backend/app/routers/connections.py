from fastapi import APIRouter, HTTPException, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List

from app.database import get_database
from app.models import ConnectionRequest, ConnectionResponse, ConnectionStatus
from app.services.connection_service import ConnectionService
from app.routers.auth import get_current_user

router = APIRouter()

@router.post("/request", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def send_connection_request(
    connection_request: ConnectionRequest,
    current_user = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Send a connection request"""
    connection_service = ConnectionService(db)
    
    try:
        connection = await connection_service.send_connection_request(
            requester_id=current_user.id,
            requested_id=connection_request.requested_id
        )
        return connection
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{connection_id}/accept", response_model=ConnectionResponse)
async def accept_connection_request(
    connection_id: str,
    current_user = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Accept a connection request"""
    connection_service = ConnectionService(db)
    
    try:
        connection = await connection_service.accept_connection_request(
            connection_id=connection_id,
            user_id=current_user.id
        )
        return connection
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{connection_id}/reject", response_model=ConnectionResponse)
async def reject_connection_request(
    connection_id: str,
    current_user = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Reject a connection request"""
    connection_service = ConnectionService(db)
    
    try:
        connection = await connection_service.reject_connection_request(
            connection_id=connection_id,
            user_id=current_user.id
        )
        return connection
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/pending", response_model=List[ConnectionResponse])
async def get_pending_requests(
    current_user = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get pending connection requests"""
    connection_service = ConnectionService(db)
    connections = await connection_service.get_pending_requests(current_user.id)
    return connections

@router.get("/my-connections", response_model=List[ConnectionResponse])
async def get_my_connections(
    current_user = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get current user's connections"""
    connection_service = ConnectionService(db)
    connections = await connection_service.get_user_connections(current_user.id)
    return connections
