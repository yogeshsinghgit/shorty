from functools import lru_cache
from dotenv import load_dotenv
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

load_dotenv(override=False)


class Settings(BaseSettings):
    """Application Settings."""


    # Application Settings
    app_name: str = "shorty-configurator"
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Server Settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")

    # Scheduler settings
    scheduler_enabled: bool = Field(default=False, alias="SCHEDULER_ENABLED")


    # MongoDB settings
    mongodb_database: str = Field(env="mongodb_database")
    mongodb_user_name: str = Field(env="mongodb_user_name")
    mongodb_password: str = Field(env="mongodb_password")
    mongodb_host: str = Field(env="mongodb_host")
    mongodb_port: str = Field(env="mongodb_port")


     # Security settings
    secret_key: str = Field(env="SECRET_KEY")
    access_token_expire_minutes: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # CORS settings
    allowed_origins: List[str] = Field(
        default=[
            "http://localhost",
            "http://localhost:3000",
        ]
    )


    # Computed properties for derived settings
    @property
    def mongodb_url(self) -> str:
        """Construct MongoDB connection URL from components."""
        return f"mongodb://{self.mongodb_user_name}:{self.mongodb_password}@{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_database}?authSource=admin"


    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
@lru_cache
def get_settings() -> Settings:
    return Settings()
