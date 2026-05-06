"""
Shared FastAPI dependencies.
"""

from __future__ import annotations

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

settings = get_settings()
_bearer = HTTPBearer(auto_error=False)


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> None:
    """
    Optional API key guard.

    If API_KEY is set in the environment, every request to a protected route
    must include:  Authorization: Bearer <API_KEY>

    If API_KEY is empty, all requests are allowed (useful during development).
    """
    if not settings.api_key:
        return  # auth disabled

    if credentials is None or credentials.credentials != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )
