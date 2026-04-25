import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from pydantic_settings import BaseSettings, SettingsConfigDict # Added SettingsConfigDict

# Setup logging
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # MongoDB Settings
    mongodb_url: str = "mongodb://127.0.0.1:27017" 
    database_name: str = "knowledge_platform"

    # JWT Settings (These were missing and causing the error!)
    jwt_secret_key: str = "your-secret-key-here-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # This "model_config" tells Pydantic to ignore extra fields instead of crashing
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore" # This is the safety net
    )

# Initialize settings
settings = Settings()

# Global variables for the connection
client: AsyncIOMotorClient = None
database = None

async def connect_to_mongo():
    """Initialize MongoDB connection with a ping test"""
    global client, database
    try:
        client = AsyncIOMotorClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=5000
        )
        # Ping test
        await client.admin.command('ping')
        
        database = client[settings.database_name]
        print(f"[SUCCESS] Connected to MongoDB: {settings.database_name}")
        
    except Exception as e:
        print(f"[ERROR] Could not connect to MongoDB: {e}")
        raise ConnectionFailure("MongoDB is not reachable.")

async def close_mongo_connection():
    """Cleanly close the MongoDB connection"""
    global client
    if client:
        client.close()
        print("[INFO] MongoDB connection closed.")

async def get_database():
    """Dependency to get the database instance."""
    return database

def get_collection(collection_name: str):
    """Get a specific collection directly"""
    if database is None:
        raise RuntimeError("Database not initialized.")
    return database[collection_name]