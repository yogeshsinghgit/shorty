from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from loguru import logger
from fastapi.middleware.cors import CORSMiddleware

from src.database.db_client import connect_to_mongo, close_mongo_connection
from src.database.indexes import create_indexes
from src.common.config.settings import get_settings

from src.domains.health_check.routes import router as health_check_router
from src.domains.shortner.routes import router as shortner_router


settings = get_settings()



@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info(f"Starting {settings.app_name}")

    await connect_to_mongo()
    await create_indexes()
    try:
        yield
    finally:
        await close_mongo_connection()
    logger.info(f"Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    description="URL Shortner",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    # openapi_tags=openapi_tags,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "defaultModelExpandDepth": 3,
        "docExpansion": "list",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "tryItOutEnabled": True,
    },
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    health_check_router,
    prefix="/api/v1"
)

app.include_router(
    shortner_router,
    prefix="/api/v1"
)



if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
