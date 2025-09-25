"""Exception handlers for mapping domain exceptions to HTTP responses."""

from fastapi import Request
from fastapi.responses import JSONResponse

from ..models.exceptions import (
    InvalidMeldError,
    InitialMeldNotMetError,
    TileNotOwnedError,
    GameNotStartedError,
    GameFinishedError,
    NotPlayersTurnError,
    PoolEmptyError,
    PlayerNotInGameError,
    GameStateError
)
from ..service.exceptions import GameNotFoundError, ConcurrentModificationError
from .models import ErrorResponse, ErrorDetail


def create_error_response(code: str, message: str, details: dict | None = None, status_code: int = 400) -> JSONResponse:
    """Create standardized error response."""
    error_response = ErrorResponse(
        error=ErrorDetail(code=code, message=message, details=details)
    )
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump()
    )


# Exception handler mapping
async def handle_domain_exceptions(request: Request, exc: Exception) -> JSONResponse:
    """Handle domain-specific exceptions and map to appropriate HTTP responses."""
    
    # Game state exceptions
    if isinstance(exc, GameNotFoundError):
        return create_error_response(
            code="GAME_NOT_FOUND",
            message="Game not found",
            status_code=404
        )
    
    elif isinstance(exc, ConcurrentModificationError):
        return create_error_response(
            code="CONCURRENT_MODIFICATION",
            message="Game state changed during operation",
            status_code=503
        )
    
    elif isinstance(exc, GameNotStartedError):
        return create_error_response(
            code="GAME_NOT_STARTED",
            message="Game has not started yet",
            status_code=400
        )
    
    elif isinstance(exc, GameFinishedError):
        return create_error_response(
            code="GAME_COMPLETED",
            message="Game has already completed",
            status_code=400
        )
    
    # Player and turn exceptions
    elif isinstance(exc, PlayerNotInGameError):
        return create_error_response(
            code="PLAYER_NOT_IN_GAME",
            message="Player is not in this game",
            status_code=403
        )
    
    elif isinstance(exc, NotPlayersTurnError):
        return create_error_response(
            code="NOT_PLAYER_TURN",
            message="It is not this player's turn",
            status_code=403
        )
    
    # Tile and meld exceptions
    elif isinstance(exc, TileNotOwnedError):
        return create_error_response(
            code="TILE_NOT_OWNED",
            message="Player doesn't own specified tiles",
            status_code=422
        )
    
    elif isinstance(exc, InvalidMeldError):
        return create_error_response(
            code="INVALID_MELD",
            message=str(exc),
            status_code=422
        )
    
    elif isinstance(exc, InitialMeldNotMetError):
        return create_error_response(
            code="INSUFFICIENT_INITIAL_MELD",
            message=str(exc),
            status_code=422
        )
    
    elif isinstance(exc, PoolEmptyError):
        return create_error_response(
            code="POOL_EMPTY",
            message="No tiles left in pool",
            status_code=400
        )
    
    elif isinstance(exc, GameStateError):
        return create_error_response(
            code="INVALID_GAME_STATE",
            message=str(exc),
            status_code=400
        )
    
    # Generic server error for unhandled exceptions
    else:
        return create_error_response(
            code="INTERNAL_ERROR",
            message="Unexpected server error",
            status_code=500
        )