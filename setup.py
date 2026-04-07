#!/usr/bin/env python3
"""
Setup script for Knowledge Sharing Platform
This script helps set up the development environment
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"STEP: {description}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ SUCCESS: {description}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: {description}")
        print(f"Error message: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ ERROR: Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path("backend/.env")
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    print("Creating .env file...")
    env_content = """# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=knowledge_platform

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
"""
    
    try:
        env_file.parent.mkdir(parents=True, exist_ok=True)
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully")
        print("⚠️  Please update JWT_SECRET_KEY in backend/.env file for production")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def download_nltk_data():
    """Download required NLTK data"""
    print("Downloading NLTK data...")
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        print("✅ NLTK data downloaded successfully")
        return True
    except Exception as e:
        print(f"❌ Error downloading NLTK data: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Knowledge Sharing Platform Setup")
    print("This script will set up your development environment")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment (optional)
    create_venv = input("\nDo you want to create a virtual environment? (y/n): ").lower().strip()
    if create_venv == 'y':
        if not run_command("python -m venv venv", "Creating virtual environment"):
            print("⚠️  Continuing without virtual environment")
        else:
            # Activate virtual environment
            if sys.platform == "win32":
                activate_cmd = "venv\\Scripts\\activate"
            else:
                activate_cmd = "source venv/bin/activate"
            print(f"\nTo activate the virtual environment, run:")
            print(f"  {activate_cmd}")
    
    # Install dependencies
    if not run_command("pip install -r backend/requirements.txt", "Installing Python dependencies"):
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        sys.exit(1)
    
    # Download NLTK data
    if not download_nltk_data():
        print("⚠️  NLTK data download failed, you may need to download manually")
    
    print("\n" + "="*50)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("="*50)
    
    print("\n📋 NEXT STEPS:")
    print("1. Make sure MongoDB is running on localhost:27017")
    print("2. Update backend/.env file with your MongoDB connection string if needed")
    print("3. Change JWT_SECRET_KEY in backend/.env file for production")
    print("4. Run backend server:")
    print("   cd backend")
    print("   python main.py")
    print("5. Open frontend/index.html in your browser")
    print("6. Visit http://localhost:8000/docs for API documentation")
    
    print("\n📚 USEFUL COMMANDS:")
    print("- Start backend: cd backend && python main.py")
    print("- Start with auto-reload: cd backend && uvicorn main:app --reload")
    print("- View API docs: http://localhost:8000/docs")
    print("- Test API: http://localhost:8000/health")
    
    print("\n🔧 TROUBLESHOOTING:")
    print("- If MongoDB connection fails, check if MongoDB is running")
    print("- If port 8000 is in use, change it in backend/main.py")
    print("- For NLTK errors, run: python -c \"import nltk; nltk.download('punkt'); nltk.download('stopwords')\"")
    
    print("\n✨ Happy coding! Start sharing reliable knowledge!")

if __name__ == "__main__":
    main()
