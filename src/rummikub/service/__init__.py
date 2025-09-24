"""Rummikub game service package.

This package provides persistence and concurrency control for multiplayer 
Rummikub games using Redis as the backend.
"""

from .game_service import GameService
from .exceptions import (
    ServiceError,
    GameNotFoundError,
    ConcurrentModificationError
)

__all__ = [
    "GameService",
    "ServiceError", 
    "GameNotFoundError",
    "ConcurrentModificationError"
]