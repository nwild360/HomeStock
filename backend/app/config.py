from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError, field_validator
from typing import List

class Settings(BaseSettings):
    # Environment Config
    ENVIRONMENT: str = Field(default="development")  # "development" or "production"

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        if v.lower() not in ("development", "production"):
            raise ValueError(f"ENVIRONMENT must be 'development' or 'production', got: {v}")
        return v.lower()

    @field_validator("COOKIE_SAMESITE")
    @classmethod
    def validate_cookie_samesite(cls, v: str) -> str:
        if v.lower() not in ("strict", "lax", "none"):
            raise ValueError(f"COOKIE_SAMESITE must be 'strict', 'lax', or 'none', got: {v}")
        return v.lower()

    # Database Config
    POSTGRES_USER: str = Field(default="homestock_user")
    POSTGRES_PASSWORD: str = Field(default="change_me_now")
    POSTGRES_DB: str = Field(default="homestock")
    POSTGRES_HOST: str = Field(default="db")
    POSTGRES_PORT: int = Field(default=5432)

    # CORS settings
    CORS_ORIGINS: str = Field(default="http://localhost:5173")

    # Frontend URL — used by OIDC callback to redirect back after authentication
    FRONTEND_URL: str = Field(default="http://localhost:5173")

    # Cookie security settings
    COOKIE_SECURE: bool = Field(default=True)  # Set to True in production (HTTPS)
    COOKIE_SAMESITE: str = Field(default="lax")  # "strict", "lax", or "none"

    # Directory where backup ZIP files are stored. Must be an absolute path.
    BACKUP_STORAGE_PATH: str = Field(default="/app/backups")

    @field_validator("BACKUP_STORAGE_PATH")
    @classmethod
    def validate_backup_storage_path(cls, v: str) -> str:
        if not v.startswith("/"):
            raise ValueError(
                f"BACKUP_STORAGE_PATH must be an absolute path, got: {v!r}"
            )
        return v

    # Backup HMAC signing secret — authenticates server-created backups on restore.
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    BACKUP_HMAC_SECRET: str = Field(...)

    @field_validator("BACKUP_HMAC_SECRET")
    @classmethod
    def validate_backup_hmac_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "BACKUP_HMAC_SECRET must be at least 32 characters. "
                "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if len(set(v)) < 8:
            raise ValueError(
                "BACKUP_HMAC_SECRET has insufficient entropy (fewer than 8 unique characters). "
                "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v

    # Backup encryption key — AES-256-GCM key for encrypting backup files at rest.
    # Must be exactly 64 hex characters (32 bytes). Keep separate from BACKUP_HMAC_SECRET.
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    BACKUP_ENCRYPTION_KEY: str = Field(...)

    @field_validator("BACKUP_ENCRYPTION_KEY")
    @classmethod
    def validate_backup_encryption_key(cls, v: str) -> str:
        try:
            key_bytes = bytes.fromhex(v)
        except ValueError:
            raise ValueError(
                "BACKUP_ENCRYPTION_KEY must be a hex string. "
                "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if len(key_bytes) != 32:
            raise ValueError(
                "BACKUP_ENCRYPTION_KEY must be exactly 64 hex characters (32 bytes). "
                "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v

    # Note: JWT signing uses Ed25519 (EdDSA) keys for compact, secure signatures
    # Keys are ephemeral and regenerated on container restart

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

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        raise SystemExit(f"CONFIG ERROR: {e}") from e
