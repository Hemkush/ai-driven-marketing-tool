import os
from fastapi import Header, HTTPException

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")

def require_internal_api_key(x_api_key: str = Header(default="")):
    if not INTERNAL_API_KEY or x_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
