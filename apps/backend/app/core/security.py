import os
from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv()

def require_internal_api_key(x_api_key: str = Header(default="")):
    internal_api_key = os.getenv("INTERNAL_API_KEY", "")
    if not internal_api_key or x_api_key != internal_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
