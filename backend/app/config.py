from pydantic_settings import BaseSettings
from pydantic import AnyUrl, Field, ValidationError, field_validator
from typing import List

class Settings(BaseSettings):
    # Required
    DATABASE_URL: AnyUrl

    # CORS settings
    CORS_ORIGINS: str = Field(default="http://localhost:5173")

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        origins = [origin.strip() for origin in v.split(",")]
        for origin in origins:
            if not origin.startswith("http://") and not origin.startswith("https://"):
                raise ValueError(f"Invalid CORS origin: {origin}")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_settings() -> Settings:
    try:
        return Settings()  # triggers validation
    except ValidationError as e:
        # Prefer loud failure on boot instead of surprising runtime errors
        raise SystemExit(f"CONFIG ERROR: {e}")
