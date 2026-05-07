from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger

from src.common.config.settings import get_settings

settings = get_settings()


client: AsyncIOMotorClient | None = None


async def connect_to_mongo():
    global client

    try:
        client = AsyncIOMotorClient(settings.mongo_db_test_url)

        await client.admin.command("ping")

        logger.info("Successfully connected to MongoDB")

    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise


async def close_mongo_connection():
    global client

    if client:
        client.close()
        logger.info("MongoDB connection closed")


def get_database():
    if client is None:
        raise Exception("MongoDB client is not initialized")

    return client[settings.mongodb_database]