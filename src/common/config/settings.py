from functools import lru_cache
from typing import List
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(override=False)


class Settings(BaseSettings):
    """Application Settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Settings
    app_name: str = "shorty-configurator"
    debug: bool = Field(default=False, validation_alias="DEBUG")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    # Server Settings
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")

    # Scheduler settings
    scheduler_enabled: bool = Field(
        default=False,
        validation_alias="SCHEDULER_ENABLED",
    )

    # MongoDB settings
    mongo_db_test_url: str = Field(validation_alias="MONGO_URI")
    mongodb_database: str = Field(validation_alias="mongodb_database")
    mongodb_user_name: str = Field(validation_alias="mongodb_user_name")
    mongodb_password: str = Field(validation_alias="mongodb_password")
    mongodb_host: str = Field(validation_alias="mongodb_host")
    mongodb_port: str = Field(validation_alias="mongodb_port")

    # Security settings
    secret_key: str = Field(validation_alias="SECRET_KEY")

    blocked_domains: List[str] = Field(
        default=[
            "localhost",
            "127.0.0.1",
        ],
        validation_alias="BLOCKED_DOMAINS"
    )

    access_token_expire_minutes: int = Field(
        default=30,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    # CORS settings
    allowed_origins: List[str] = Field(
        default=[
            "http://localhost",
            "http://localhost:3000",
        ]
    )

    @property
    def mongodb_url(self) -> str:
        """Construct MongoDB connection URL from components."""
        if not self.mongodb_user_name or not self.mongodb_password:
            return f"mongodb://{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_database}"

        escaped_user = quote_plus(self.mongodb_user_name)
        escaped_password = quote_plus(self.mongodb_password)
        return (
            f"mongodb://{escaped_user}:"
            f"{escaped_password}@"
            f"{self.mongodb_host}:"
            f"{self.mongodb_port}/"
            f"{self.mongodb_database}?authSource=admin"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()