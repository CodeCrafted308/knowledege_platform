from pymongo import MongoClient

try:
    client = MongoClient("mongodb://127.0.0.1:27017/")
    db = client["knowledge_platform"]
    print("Databases found:", client.list_database_names())
    print("Connection Successful!")
except Exception as e:
    print(f"Error: {e}")