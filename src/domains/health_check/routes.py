from datetime import datetime, UTC

from fastapi import APIRouter
from loguru import logger

from src.database.db_client import client
from src.common.config.settings import get_settings


router = APIRouter(
    prefix="/health",
    tags=["Health"]
)

settings = get_settings()


@router.get("/")
async def health_check():
    """
    Basic health check endpoint.
    """

    logger.info("Health check endpoint called")

    return {
        "status": "healthy",
        "service": settings.app_name,
        "timestamp": datetime.now(UTC)
    }


@router.get("/mongodb")
async def mongodb_health_check():
    """
    MongoDB health check endpoint.
    """

    try:
        # await client.admin.command("ping")

        logger.info("MongoDB health check successful")

        return {
            "status": "healthy",
            "database": "mongodb"
        }

    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")

        return {
            "status": "unhealthy",
            "database": "mongodb",
            "error": str(e)
        }