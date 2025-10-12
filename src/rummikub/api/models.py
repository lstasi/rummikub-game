"""Pydantic models for API request/response validation."""

from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class TileKindRequest(BaseModel):
    """Request model for tile kind."""
    type: Literal["numbered", "joker"]
    number: Optional[int] = None
    color: Optional[str] = None


class TileRequest(BaseModel):
    """Request model for a tile."""
    id: str
    kind: TileKindRequest


class MeldRequest(BaseModel):
    """Request model for a meld."""
    id: str
    kind: Literal["group", "run"]
    tiles: List[str]


class PlayTilesRequest(BaseModel):
    """Request body for play tiles action."""
    melds: List[MeldRequest]


class DrawTileRequest(BaseModel):
    """Request body for draw tile action (empty)."""
    pass


class TileKindResponse(BaseModel):
    """Response model for tile kind."""
    type: Literal["numbered", "joker"]
    number: Optional[int] = None
    color: Optional[str] = None


class TileResponse(BaseModel):
    """Response model for a tile."""
    id: str
    kind: TileKindResponse


class MeldResponse(BaseModel):
    """Response model for a meld."""
    id: str
    kind: Literal["group", "run"]
    tiles: List[str]


class RackResponse(BaseModel):
    """Response model for a player's rack."""
    tiles: List[str]


class BoardResponse(BaseModel):
    """Response model for the game board."""
    melds: List[MeldResponse]


class PlayerResponse(BaseModel):
    """Response model for a player."""
    id: str
    name: str
    initial_meld_met: bool
    rack: Optional[RackResponse] = None
    rack_size: Optional[int] = None


class GameStateResponse(BaseModel):
    """Response model for game state."""
    game_id: str
    status: Literal["waiting_for_players", "in_progress", "completed"]
    num_players: int
    players: List[PlayerResponse]
    current_player_index: int
    pool_size: int
    board: BoardResponse
    created_at: datetime
    updated_at: datetime
    winner_player_id: Optional[str] = None


class GamesListResponse(BaseModel):
    """Response model for games list."""
    games: List[GameStateResponse]


class CreateGameRequest(BaseModel):
    """Request body for creating a game."""
    num_players: int = Field(ge=2, le=4, description="Number of players (2-4)")


class JoinGameRequest(BaseModel):
    """Request body for joining a game."""
    player_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Player name (optional if provided via Basic Auth)")


class ErrorDetail(BaseModel):
    """Error detail model."""
    code: str
    message: str
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: ErrorDetail