from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl



class urlInputModel(BaseModel):
    long_url: HttpUrl = Field(
        ... , 
        description="The long URL to be shortened"
    )


class urlOutputModel(BaseModel):
    id: str
    long_url: str
    short_code: str
    expires_at: Optional[datetime]