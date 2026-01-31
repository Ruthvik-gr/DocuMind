"""
MongoDB Atlas database connection and management.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
from app.config import get_settings
import logging
import asyncio

logger = logging.getLogger(__name__)
settings = get_settings()


class Database:
    """Database connection manager for MongoDB Atlas."""

    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None


db = Database()


async def connect_to_mongo():
    """Connect to MongoDB Atlas with timeout and retry logic."""
    max_retries = 3
    retry_delay = 2  # seconds
    connection_timeout = 10000  # 10 seconds in milliseconds

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to MongoDB (attempt {attempt + 1}/{max_retries})...")

            # Create client with connection timeout
            db.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=connection_timeout,
                connectTimeoutMS=connection_timeout,
                socketTimeoutMS=connection_timeout
            )

            # Test connection with timeout
            await asyncio.wait_for(
                db.client.admin.command('ping'),
                timeout=10.0
            )

            db.database = db.client[settings.MONGODB_DATABASE]
            logger.info(f"Successfully connected to MongoDB Atlas database: {settings.MONGODB_DATABASE}")
            return

        except asyncio.TimeoutError:
            logger.warning(f"MongoDB connection timeout on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Failed to connect to MongoDB: All retries exhausted (timeout)")
                # Don't raise - allow app to start without DB

        except ConnectionFailure as e:
            logger.warning(f"MongoDB connection failed on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to MongoDB: All retries exhausted - {e}")
                # Don't raise - allow app to start without DB

        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                # Don't raise - allow app to start without DB
                logger.error("Failed to connect to MongoDB: Unexpected error")


async def close_mongo_connection():
    """Close MongoDB connection."""
    if db.client:
        db.client.close()
        logger.info("Closed MongoDB connection")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    return db.database
