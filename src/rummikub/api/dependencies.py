"""Dependency injection setup for FastAPI."""

from typing import Annotated
import os

from fastapi import Depends
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


# Type aliases for dependency injection
GameServiceDep = Annotated[GameService, Depends(get_game_service)]