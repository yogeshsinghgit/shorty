from loguru import logger
from typing import Optional
from uuid import UUID
import threading

from src.database.db_client import get_database
from src.database.shortner.schema import ShortURLSchema


class ShortURLRepository:
    def __init__(self):
        self.collection = get_database().shortner.urls

    async def create_url(self, url_schema: ShortURLSchema) -> Optional[UUID]:
        """
        Create a new URL shortner.
        """

        try:
            logger.info(f"Creating URL shortner: {url_schema}")

            result = await self.collection.insert_one(url_schema.model_dump())

            logger.info(f"URL shortner created: {result}")

            return result.inserted_id
        
        except Exception as e:
            logger.error(f"Error creating URL shortner: {e}")

            raise


    async def find_url_by_short_code(self, short_code: str) -> Optional[ShortURLSchema]:
        """
        Find a URL shortner by short code.
        """

        try:
            logger.info(f"Finding URL shortner by short code: {short_code}")

            url = await self.collection.find_one({"short_code": short_code})

            logger.info(f"URL shortner found: {url}")

            return url
        
        except Exception as e:
            logger.error(f"Error finding URL shortner by short code: {e}")

            raise

    async def delete_url(self, short_code: str) -> Optional[int]:
        """
        Delete a URL shortner.
        """

        try:
            logger.info(f"Deleting URL shortner: {short_code}")

            result = await self.collection.delete_one({"short_code": short_code})

            logger.info(f"URL shortner deleted: {result}")

            return result.deleted_count
        
        except Exception as e:
            logger.error(f"Error deleting URL shortner: {e}")

            raise

    async def update_url(self, short_code: str, url_schema: ShortURLSchema) -> Optional[int]:
        """
        Update a URL shortner.
        """

        try:
            logger.info(f"Updating URL shortner: {short_code}")

            result = await self.collection.update_one({"short_code": short_code}, {"$set": url_schema.model_dump()})

            logger.info(f"URL shortner updated: {result}")

            return result.modified_count
        
        except Exception as e:
            logger.error(f"Error updating URL shortner: {e}")

            raise

    
    async def activate_url(self, short_code: str) -> Optional[int]:
        """
        Activate a URL shortner.
        """

        try:
            logger.info(f"Activating URL shortner: {short_code}")

            result = await self.collection.update_one({"short_code": short_code}, {"$set": {"is_active": True}})

            logger.info(f"URL shortner activated: {result}")

            return result.modified_count
        
        except Exception as e:
            logger.error(f"Error activating URL shortner: {e}")

            raise

    
    async def deactivate_url(self, short_code: str) -> Optional[int]:
        """
        Deactivate a URL shortner.
        """

        try:
            logger.info(f"Deactivating URL shortner: {short_code}")

            result = await self.collection.update_one({"short_code": short_code}, {"$set": {"is_deleted": True}})

            logger.info(f"URL shortner deactivated: {result}")

            return result.modified_count
        
        except Exception as e:
            logger.error(f"Error deactivating URL shortner: {e}")

            raise



# Global repository instance with thread-safe initialization


_short_url_repository: Optional[ShortURLRepository] = None
_short_url_repository_lock = threading.Lock()


def get_short_url_repository() -> ShortURLRepository:
    """Get the global actor repository instance (thread-safe)."""
    global _short_url_repository
    if _short_url_repository is not None:  # Fast path: already initialized
        return _short_url_repository
    with _short_url_repository_lock:
        if _short_url_repository is None:  # Double-check after acquiring lock
            _short_url_repository = ShortURLRepository()
        return _short_url_repository


# Convenience functions for direct access
async def create_url(url_schema: ShortURLSchema) -> Optional[UUID]:
    """Create a new URL shortner."""
    return await get_short_url_repository().create_url(url_schema)


async def find_url_by_short_code(short_code: str) -> Optional[ShortURLSchema]:
    """Find a URL shortner by short code."""
    return await get_short_url_repository().find_url_by_short_code(short_code)


async def delete_url(short_code: str) -> Optional[int]:
    """Delete a URL shortner."""
    return await get_short_url_repository().delete_url(short_code)


async def update_url(short_code: str, url_schema: ShortURLSchema) -> Optional[int]:
    """Update a URL shortner."""
    return await get_short_url_repository().update_url(short_code, url_schema)


async def activate_url(short_code: str) -> Optional[int]:
    """Activate a URL shortner."""
    return await get_short_url_repository().activate_url(short_code)


async def deactivate_url(short_code: str) -> Optional[int]:
    """Deactivate a URL shortner."""
    return await get_short_url_repository().deactivate_url(short_code)
