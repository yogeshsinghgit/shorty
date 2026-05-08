from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from src.domains.shortner.models import urlInputModel, urlOutputModel
from src.domains.shortner.service import (
    create_short_url as create_short_url_service,
    resolve_short_code
)


router = APIRouter(prefix="/shorty", tags=["shortner"])


@router.post("/", response_model=urlOutputModel)
async def create_short_url(url_schema: urlInputModel):
    """
    Create a new short URL.
    """
    return await create_short_url_service(url_schema)


@router.get("/{short_code}")
async def redirect_to_long_url(short_code: str):
    """
    Redirect to the original long URL.
    """
    long_url = await resolve_short_code(short_code)
    return RedirectResponse(url=long_url)