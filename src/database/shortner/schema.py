from bson import ObjectId
from pydantic import BaseModel, Field, field_serializer, ConfigDict, HttpUrl
from typing import Optional
from datetime import datetime, timezone

from src.common.models import PyObjectId


class ShortURLSchema(BaseModel):
    id: PyObjectId = Field(
        default_factory=PyObjectId, 
        alias="_id"
    )

    long_url: HttpUrl
    short_code: str

    created_by: Optional[PyObjectId] = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    is_deleted: bool = False

    click_count: int = 0

    expires_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="ignore"
    )

    @field_serializer("long_url", when_used="always")
    def serialize_long_url(self, value: HttpUrl) -> str:
        return str(value)

    @field_serializer("id", when_used="json")
    def serialize_id(self, value: PyObjectId) -> str:
        return str(value)

    @field_serializer("created_by", when_used="json")
    def serialize_created_by(self, value: Optional[PyObjectId]) -> Optional[str]:
        return str(value) if value else None