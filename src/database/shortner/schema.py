from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_serializer, ConfigDict, HttpUrl
from typing import Optional
from datetime import datetime, timezone


class ShortURLSchema(BaseModel):
    id: UUID = Field(default_factory=uuid4)

    long_url: HttpUrl
    short_code: str

    created_by: Optional[UUID] = None

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

    @field_serializer("id", when_used="json")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)