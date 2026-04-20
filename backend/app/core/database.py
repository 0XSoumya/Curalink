from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = None
db = None


async def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client["medical_assistant"]
    print("✅ Connected to MongoDB")


async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("❌ MongoDB connection closed")


def get_db():
    return db