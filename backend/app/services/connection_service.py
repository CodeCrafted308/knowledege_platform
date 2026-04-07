from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import List

from app.models import Connection, ConnectionRequest, ConnectionResponse, ConnectionStatus
from app.services.user_service import UserService

class ConnectionService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.connections_collection = db.connections
        self.user_service = UserService(db)
    
    async def send_connection_request(self, requester_id: str, requested_id: str) -> ConnectionResponse:
        """Send a connection request"""
        
        # Check if connection already exists
        existing_connection = await self.get_connection_between_users(requester_id, requested_id)
        if existing_connection:
            raise Exception("Connection already exists or pending")
        
        # Check if trying to connect to self
        if requester_id == requested_id:
            raise Exception("Cannot connect to yourself")
        
        connection_dict = {
            "requester_id": requester_id,
            "requested_id": requested_id,
            "status": ConnectionStatus.PENDING,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.connections_collection.insert_one(connection_dict)
        connection_dict["id"] = str(result.inserted_id)
        
        return ConnectionResponse(**connection_dict)
    
    async def accept_connection_request(self, connection_id: str, user_id: str) -> ConnectionResponse:
        """Accept a connection request"""
        try:
            obj_id = ObjectId(connection_id)
            connection = await self.connections_collection.find_one({"_id": obj_id})
            
            if not connection:
                raise Exception("Connection request not found")
            
            # Check if user is the requested user
            if connection["requested_id"] != user_id:
                raise Exception("Not authorized to accept this request")
            
            # Update connection status
            await self.connections_collection.update_one(
                {"_id": obj_id},
                {
                    "$set": {
                        "status": ConnectionStatus.ACCEPTED,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Update user counts
            await self.user_service.increment_followers_count(connection["requester_id"])
            await self.user_service.increment_following_count(user_id)
            
            connection["id"] = str(connection.pop("_id"))
            connection["status"] = ConnectionStatus.ACCEPTED
            
            return ConnectionResponse(**connection)
            
        except:
            raise Exception("Failed to accept connection request")
    
    async def reject_connection_request(self, connection_id: str, user_id: str) -> ConnectionResponse:
        """Reject a connection request"""
        try:
            obj_id = ObjectId(connection_id)
            connection = await self.connections_collection.find_one({"_id": obj_id})
            
            if not connection:
                raise Exception("Connection request not found")
            
            # Check if user is the requested user
            if connection["requested_id"] != user_id:
                raise Exception("Not authorized to reject this request")
            
            # Update connection status
            await self.connections_collection.update_one(
                {"_id": obj_id},
                {
                    "$set": {
                        "status": ConnectionStatus.REJECTED,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            connection["id"] = str(connection.pop("_id"))
            connection["status"] = ConnectionStatus.REJECTED
            
            return ConnectionResponse(**connection)
            
        except:
            raise Exception("Failed to reject connection request")
    
    async def get_connection_by_id(self, connection_id: str) -> ConnectionResponse:
        """Get connection by ID"""
        try:
            obj_id = ObjectId(connection_id)
            connection_doc = await self.connections_collection.find_one({"_id": obj_id})
            if connection_doc:
                connection_doc["id"] = str(connection_doc.pop("_id"))
                return ConnectionResponse(**connection_doc)
        except:
            pass
        return None
    
    async def get_connection_between_users(self, user1_id: str, user2_id: str) -> ConnectionResponse:
        """Get connection between two users"""
        connection_doc = await self.connections_collection.find_one({
            "$or": [
                {"requester_id": user1_id, "requested_id": user2_id},
                {"requester_id": user2_id, "requested_id": user1_id}
            ]
        })
        
        if connection_doc:
            connection_doc["id"] = str(connection_doc.pop("_id"))
            return ConnectionResponse(**connection_doc)
        return None
    
    async def get_user_connections(self, user_id: str, status: ConnectionStatus = None) -> List[ConnectionResponse]:
        """Get user's connections"""
        connections = []
        
        filter_dict = {
            "$or": [
                {"requester_id": user_id},
                {"requested_id": user_id}
            ]
        }
        
        if status:
            filter_dict["status"] = status
        
        cursor = self.connections_collection.find(filter_dict).sort("created_at", -1)
        
        async for connection_doc in cursor:
            connection_doc["id"] = str(connection_doc.pop("_id"))
            connections.append(ConnectionResponse(**connection_doc))
        
        return connections
    
    async def get_pending_requests(self, user_id: str) -> List[ConnectionResponse]:
        """Get pending connection requests for a user"""
        connections = []
        
        cursor = self.connections_collection.find({
            "requested_id": user_id,
            "status": ConnectionStatus.PENDING
        }).sort("created_at", -1)
        
        async for connection_doc in cursor:
            connection_doc["id"] = str(connection_doc.pop("_id"))
            connections.append(ConnectionResponse(**connection_doc))
        
        return connections
