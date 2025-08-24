from fastapi import Header, HTTPException, status
import re

async def require_idempotency_key(
    idempotency_key: str = Header(..., description="Unique key for idempotent operations")
):
    """
    Dependency for requiring and validating idempotency keys.
    Ensures keys are valid UUIDs or meet specific format requirements.
    """
    if not re.match(r'^[a-zA-Z0-9\-_]{8,64}$', idempotency_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid idempotency key format"
        )
    return idempotency_key