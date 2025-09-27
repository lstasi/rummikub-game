"""Main FastAPI application with API endpoints."""

from typing import cast


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..models import PlayTilesAction, DrawAction
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

from .dependencies import GameServiceDep
from .models import (
    GamesListResponse,
    GameStateResponse,
    CreateGameRequest,
    JoinGameRequest,
    PlayTilesRequest,
    DrawTileRequest,
    MeldResponse,
    PlayerResponse,
    BoardResponse,
    RackResponse,
)
from .exception_handlers import handle_domain_exceptions


# Create FastAPI app
app = FastAPI(
    title="Rummikub Game API",
    description="REST API for multiplayer Rummikub game with Redis backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(GameNotFoundError, handle_domain_exceptions)
app.add_exception_handler(ConcurrentModificationError, handle_domain_exceptions)
app.add_exception_handler(InvalidMeldError, handle_domain_exceptions)
app.add_exception_handler(InitialMeldNotMetError, handle_domain_exceptions)
app.add_exception_handler(TileNotOwnedError, handle_domain_exceptions)
app.add_exception_handler(GameNotStartedError, handle_domain_exceptions)
app.add_exception_handler(GameFinishedError, handle_domain_exceptions)
app.add_exception_handler(NotPlayersTurnError, handle_domain_exceptions)
app.add_exception_handler(PoolEmptyError, handle_domain_exceptions)
app.add_exception_handler(PlayerNotInGameError, handle_domain_exceptions)
app.add_exception_handler(GameStateError, handle_domain_exceptions)


def _convert_game_state_to_response(game_state, requesting_player_id: str | None = None) -> GameStateResponse:
    """Convert GameState model to API response format."""
    
    # Convert board melds
    board = BoardResponse(
        melds=[
            MeldResponse(
                id=str(meld.id),
                kind=meld.kind.value,
                tiles=meld.tiles
            )
            for meld in game_state.board.melds
        ]
    )
    
    # Convert players with privacy controls - only include joined players
    players = []
    for player in game_state.players:
        # Skip players who haven't joined yet (name is None)
        if player.name is None:
            continue
            
        player_response = PlayerResponse(
            id=player.id,
            name=player.name,
            initial_meld_met=player.initial_meld_met
        )
        
        # Only show full rack to the requesting player
        if requesting_player_id and player.id == requesting_player_id:
            player_response.rack = RackResponse(tiles=player.rack.tile_ids)
        else:
            player_response.rack_size = len(player.rack.tile_ids)
        
        players.append(player_response)
    
    return GameStateResponse(
        game_id=str(game_state.game_id),
        status=game_state.status.value,
        num_players=len(game_state.players),
        players=players,
        current_player_index=game_state.current_player_index,
        pool_size=len(game_state.pool),
        board=board,
        created_at=game_state.created_at,
        updated_at=game_state.updated_at,
        winner_player_id=game_state.winner_player_id
    )


@app.get("/games", response_model=GamesListResponse)
async def get_games(game_service: GameServiceDep) -> GamesListResponse:
    """Retrieve a list of all available games."""
    games = game_service.get_games()
    
    # Convert to response format (no player-specific filtering for list view)
    game_responses = [
        _convert_game_state_to_response(game) for game in games
    ]
    
    return GamesListResponse(games=game_responses)


@app.post("/games", response_model=GameStateResponse)
async def create_game(
    request: CreateGameRequest,
    game_service: GameServiceDep
) -> GameStateResponse:
    """Create a new game."""
    game_state = game_service.create_game(request.num_players)
    return _convert_game_state_to_response(game_state)


@app.post("/games/{game_id}/players", response_model=GameStateResponse)
async def join_game(
    game_id: str,
    request: JoinGameRequest,
    game_service: GameServiceDep
) -> GameStateResponse:
    """Join a game by game ID."""
    game_state = game_service.join_game(game_id, request.player_name)
    
    # Find the player who just joined to return their curated view
    requesting_player = None
    for player in game_state.players:
        if player.name == request.player_name:
            requesting_player = player.id
            break
    
    return _convert_game_state_to_response(game_state, requesting_player)


@app.get("/games/{game_id}/players/{player_id}", response_model=GameStateResponse)
async def get_game_state(
    game_id: str,
    player_id: str,
    game_service: GameServiceDep
) -> GameStateResponse:
    """Get game state for a specific player."""
    try:
        # Load the game state directly
        game_state = game_service._load_game_state(game_id)
        
        # Find the player with this ID
        target_player = None
        for player in game_state.players:
            if player.id == player_id:
                target_player = player
                break
        
        if target_player is None:
            from ..models.exceptions import PlayerNotInGameError
            raise PlayerNotInGameError("Player not in game")
        
        # Get curated game state for this player
        curated_game_state = game_service._curate_game_state_for_player(game_state, player_id)
        
        return _convert_game_state_to_response(curated_game_state, player_id)
    
    except GameNotFoundError:
        raise GameNotFoundError("Game not found")


@app.post("/games/{game_id}/players/{player_id}/actions/play", response_model=GameStateResponse)
async def play_tiles(
    game_id: str,
    player_id: str,
    request: PlayTilesRequest,
    game_service: GameServiceDep
) -> GameStateResponse:
    """Execute a play tiles action."""
    
    # Convert request to domain action
    from ..models.melds import Meld, MeldKind
    melds = []
    for meld_req in request.melds:
        meld = Meld(
            id=meld_req.id,
            kind=MeldKind(meld_req.kind),
            tiles=meld_req.tiles
        )
        melds.append(meld)
    
    action = PlayTilesAction(melds=melds)
    
    # Execute action
    game_state = game_service.execute_turn(game_id, player_id, action)
    return _convert_game_state_to_response(game_state, player_id)


@app.post("/games/{game_id}/players/{player_id}/actions/draw", response_model=GameStateResponse)
async def draw_tile(
    game_id: str,
    player_id: str,
    request: DrawTileRequest,
    game_service: GameServiceDep
) -> GameStateResponse:
    """Draw a tile from the pool."""
    
    # Create draw action
    action = DrawAction()
    
    # Execute action
    game_state = game_service.execute_turn(game_id, player_id, action)
    return _convert_game_state_to_response(game_state, player_id)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}