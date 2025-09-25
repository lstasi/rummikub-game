"""Dependency injection setup for FastAPI."""

from typing import Annotated
import os

from fastapi import Depends
from redis import Redis

from ..service import GameService


def get_redis_client() -> Redis:
    """Get Redis client instance."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(redis_url, decode_responses=True)


def get_game_service(redis_client: Annotated[Redis, Depends(get_redis_client)]) -> GameService:
    """Get GameService instance with Redis dependency."""
    return GameService(redis_client)


# Type aliases for dependency injection
GameServiceDep = Annotated[GameService, Depends(get_game_service)]