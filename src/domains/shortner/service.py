
from fastapi.exceptions import HTTPException
from src.domains.shortner.core.generator import validate_custom_code, generate_short_code
from src.domains.shortner.core.validators import validate_url
from src.domains.shortner.models import urlInputModel, urlOutputModel
from src.database.shortner.lib import (
    create_url,
    deactivate_url,
    activate_url,
    find_url_by_short_code,
    delete_url
)

from src.database.shortner.schema import ShortURLSchema



from pymongo.errors import DuplicateKeyError

async def create_short_url(url_schema: urlInputModel):
    long_url = str(url_schema.long_url)
    
    # step 1 validate url
    # Note: resolve_dns=False to keep it async-safe for now. 
    # DNS resolution optimization is planned in the next step.
    validation_result = await validate_url(url=long_url, resolve_dns=False)
    if not validation_result.valid:
        raise HTTPException(
            status_code=400,
            detail=validation_result.reason
        )

    # step 2 & 3: Atomic Insert with Retry (Collision Handling)
    max_attempts = 5
    for _ in range(max_attempts):
        short_code = generate_short_code()
        
        new_url_schema = ShortURLSchema(
            long_url=url_schema.long_url,
            short_code=short_code
        )
        
        try:
            url_id = await create_url(new_url_schema)
            if url_id:
                # step 4 return output to user
                return urlOutputModel(
                    id=str(new_url_schema.id),
                    long_url=str(new_url_schema.long_url),
                    short_code=new_url_schema.short_code,
                    expires_at=new_url_schema.expires_at
                )
        except DuplicateKeyError:
            # Collision occurred (race condition or pure luck). Retry.
            continue
    
    # If we reach here, we failed to generate a unique code after max_attempts
    raise HTTPException(
        status_code=500,
        detail="Failed to generate a unique short code after several attempts."
    )


async def resolve_short_code(short_code: str) -> str:
    """
    Resolve a short code to its original long URL.
    """
    url_data = await find_url_by_short_code(short_code=short_code)
    
    if not url_data:
        raise HTTPException(
            status_code=404,
            detail="Short URL not found."
        )
    
    if url_data.get("is_deleted"):
        raise HTTPException(
            status_code=410,
            detail="This short URL has been deleted."
        )
    
    # Check for expiration
    expires_at = url_data.get("expires_at")
    if expires_at:
        from datetime import datetime, timezone
        # Handle both datetime objects and strings if necessary
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        
        if datetime.now(timezone.utc) > (expires_at.replace(tzinfo=timezone.utc) if expires_at.tzinfo is None else expires_at):
             raise HTTPException(
                status_code=410,
                detail="This short URL has expired."
            )

    return str(url_data.get("long_url"))
