import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Added for media serving
from pydantic_settings import BaseSettings

# Import your local modules
from app.routers import auth, users, posts, connections, admin
from app.database import connect_to_mongo, close_mongo_connection

class Settings(BaseSettings):
    mongodb_url: str = "mongodb://127.0.0.1:27017"
    database_name: str = "knowledge_platform"
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

settings = Settings()

app = FastAPI(
    title="Knowledge Sharing Platform",
    description="A platform for sharing reliable content with analysis and scoring",
    version="1.0.0"
)

# --- MEDIA STORAGE CONFIGURATION ---
# Create the uploads directory if it doesn't exist
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../uploads"))
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Mount the static directory so files are accessible via URL
# Example: http://127.0.0.1:8000/uploads/filename.jpg
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --- CRITICAL CORS CONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This allows EVERY port (5500, 5501, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE LIFECYCLE ---
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# --- ROUTER INCLUSION ---
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])
app.include_router(connections.router, prefix="/api/connections", tags=["connections"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
async def root():
    return {
        "message": "Knowledge Sharing Platform API",
        "status": "online",
        "docs": "/docs",
        "media_root": "/uploads"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)