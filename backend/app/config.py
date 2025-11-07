from pydantic_settings import BaseSettings
from pydantic import AnyUrl, Field, ValidationError, field_validator
from typing import List

class Settings(BaseSettings):
    # Database Config
    POSTGRES_USER: str = Field(default="homestock_user")
    POSTGRES_PASSWORD: str = Field(default="change_me_now")
    POSTGRES_DB: str = Field(default="homestock")
    POSTGRES_HOST: str = Field(default="db")
    POSTGRES_PORT: int = Field(default=5432)

    # CORS settings
    CORS_ORIGINS: str = Field(default="http://localhost:5173")

    # JWT Secret Key for token signing (required, must be secure random string)
    SECRET_KEY: str = Field(..., min_length=32) 

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
