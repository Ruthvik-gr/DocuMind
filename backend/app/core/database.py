"""
MongoDB Atlas database connection and management.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class Database:
    """Database connection manager for MongoDB Atlas."""

    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None


db = Database()


async def connect_to_mongo():
    """Connect to MongoDB Atlas."""
    try:
        db.client = AsyncIOMotorClient(settings.MONGODB_URL)
        await db.client.admin.command('ping')
        db.database = db.client[settings.MONGODB_DATABASE]
        logger.info(f"Connected to MongoDB Atlas database: {settings.MONGODB_DATABASE}")
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB Atlas: {e}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection."""
    if db.client:
        db.client.close()
        logger.info("Closed MongoDB connection")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    return db.database
