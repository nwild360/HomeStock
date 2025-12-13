from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError, field_validator
from typing import List

class Settings(BaseSettings):
    # Environment Config
    ENVIRONMENT: str = Field(default="development")  # "development" or "production"

    # Database Config
    POSTGRES_USER: str = Field(default="homestock_user")
    POSTGRES_PASSWORD: str = Field(default="change_me_now")
    POSTGRES_DB: str = Field(default="homestock")
    POSTGRES_HOST: str = Field(default="db")
    POSTGRES_PORT: int = Field(default=5432)

    # CORS settings
    CORS_ORIGINS: str = Field(default="http://localhost:5173")

    # Cookie security settings
    COOKIE_SECURE: bool = Field(default=True)  # Set to True in production (HTTPS)
    COOKIE_SAMESITE: str = Field(default="lax")  # "strict", "lax", or "none"

    # Note: JWT signing now uses dynamically generated RSA + Dilithium keys
    # No SECRET_KEY needed - keys are ephemeral and regenerated on container restart 

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
        raise SystemExit(f"CONFIG ERROR: {e}") from e
