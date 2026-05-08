from loguru import logger
from pymongo import ASCENDING, DESCENDING

from src.database.db_client import get_database


async def create_indexes():
    try:
        db = get_database().urls

        # Primary lookup index
        await db.create_index(
            [("short_code", ASCENDING)],
            unique=True,
            name="unique_short_code_index",
        )

        # Show all URLs created by this user, newest first
        await db.create_index(
            [
                ("user_id", ASCENDING),
                ("created_at", DESCENDING),
            ],
        )

        logger.info("MongoDB indexes created successfully")

    except Exception as e:
        logger.error(f"Failed to create MongoDB indexes: {e}")
        raise