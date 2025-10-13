"""Dependency injection setup for FastAPI."""

from typing import Annotated
import os
import base64
import binascii

from fastapi import Depends, HTTPException, Header
from redis import Redis

from ..service import GameService

# Global fake redis instance for testing
_fake_redis_instance = None


def get_redis_client() -> Redis:
    """Get Redis client instance."""
    global _fake_redis_instance
    
    use_fake = os.getenv("USE_FAKE_REDIS", "false").lower() == "true"
    if use_fake:
        import fakeredis
        if _fake_redis_instance is None:
            _fake_redis_instance = fakeredis.FakeRedis(decode_responses=True)
        return _fake_redis_instance
    
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(redis_url, decode_responses=True)


def get_game_service(redis_client: Annotated[Redis, Depends(get_redis_client)]) -> GameService:
    """Get GameService instance with Redis dependency."""
    return GameService(redis_client)


def get_current_username(authorization: str | None = Header(None)) -> str:
    """Extract username from HTTP Basic Auth header.
    
    Args:
        authorization: Authorization header value (e.g., "Basic base64(username:password)")
        
    Returns:
        Username extracted from the auth header
        
    Raises:
        HTTPException: 401 if no auth header or invalid format
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Check if it's Basic auth
    if not authorization.startswith("Basic "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication scheme. Use Basic authentication.",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Extract the base64 encoded credentials
    try:
        encoded_credentials = authorization[6:]  # Remove "Basic " prefix
        decoded_bytes = base64.b64decode(encoded_credentials)
        decoded_str = decoded_bytes.decode("utf-8")
        
        # Split username:password (we only care about username)
        if ":" in decoded_str:
            username, _ = decoded_str.split(":", 1)
        else:
            username = decoded_str
        
        if not username or not username.strip():
            raise HTTPException(
                status_code=401,
                detail="Username cannot be empty",
                headers={"WWW-Authenticate": "Basic"},
            )
        
        return username.strip()
    
    except (binascii.Error, UnicodeDecodeError) as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authorization header format: {e}",
            headers={"WWW-Authenticate": "Basic"},
        )


# Type aliases for dependency injection
GameServiceDep = Annotated[GameService, Depends(get_game_service)]
CurrentUserDep = Annotated[str, Depends(get_current_username)]