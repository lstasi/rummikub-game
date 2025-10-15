"""Dependency injection setup for FastAPI."""

from typing import Annotated, Optional
import os
import base64

from fastapi import Depends, HTTPException, Header, status
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


def get_player_name(authorization: Optional[str] = Header(None)) -> str:
    """Extract player name from HTTP Basic Auth header.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        Player name from Basic Auth username
        
    Raises:
        HTTPException: 401 if authorization header is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    if not authorization.startswith("Basic "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme. Expected Basic Auth",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    try:
        # Decode base64 credentials
        encoded_credentials = authorization[6:]  # Remove "Basic " prefix
        decoded = base64.b64decode(encoded_credentials).decode("utf-8")
        username, _ = decoded.split(":", 1)  # Split username:password
        
        if not username:
            raise ValueError("Empty username")
            
        return username
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authorization format: {str(e)}",
            headers={"WWW-Authenticate": "Basic"},
        )


# Type aliases for dependency injection
GameServiceDep = Annotated[GameService, Depends(get_game_service)]
PlayerNameDep = Annotated[str, Depends(get_player_name)]