"""Main FastAPI application with API endpoints."""


import logging
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

from .dependencies import GameServiceDep, PlayerNameDep
from .models import (
    GamesListResponse,
    GameStateResponse,
    CreateGameRequest,
    PlayTilesRequest,
    DrawTileRequest,
    MeldResponse,
    PlayerResponse,
    BoardResponse,
    RackResponse,
)
from .exception_handlers import handle_domain_exceptions

# Set up logging
logger = logging.getLogger(__name__)


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


def _convert_game_state_to_response(game_state, requesting_player_id: str | None = None, original_game_state=None) -> GameStateResponse:
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
            # For other players, get rack size from original state if available
            if original_game_state:
                original_player = next((p for p in original_game_state.players if p.id == player.id), None)
                player_response.rack_size = len(original_player.rack.tile_ids) if original_player else len(player.rack.tile_ids)
            else:
                player_response.rack_size = len(player.rack.tile_ids)
        
        players.append(player_response)
    
    return GameStateResponse(
        game_id=str(game_state.game_id),
        status=game_state.status.value,
        num_players=game_state.num_players,
        players=players,
        current_player_index=game_state.current_player_index,
        pool_size=len(game_state.pool),
        board=board,
        created_at=game_state.created_at,
        updated_at=game_state.updated_at,
        winner_player_id=game_state.winner_player_id
    )


@app.get("/games", response_model=GamesListResponse)
async def get_games(
    game_service: GameServiceDep,
    player_name: PlayerNameDep,
    status: str | None = None
) -> GamesListResponse:
    """Retrieve a list of available games (excluding games where the authenticated player has already joined).
    
    Requires Basic Auth with player name as username.
    
    Args:
        game_service: Game service dependency
        player_name: Authenticated player name from Basic Auth header
        status: Optional status filter (e.g., 'waiting_for_players', 'in_progress', 'completed')
    """
    games = game_service.get_games()
    
    # Filter by status if provided
    if status:
        from ..models.game import GameStatus
        try:
            status_enum = GameStatus(status)
            games = [game for game in games if game.status == status_enum]
        except ValueError:
            # Invalid status value, ignore filter
            logger.warning(f"Invalid status filter: {status}")
    
    # Filter out games where the authenticated player has already joined
    filtered_games = []
    for game in games:
        player_in_game = False
        for player in game.players:
            if player.name == player_name:
                player_in_game = True
                break
        if not player_in_game:
            filtered_games.append(game)
    games = filtered_games
    
    # Convert to response format
    game_responses = [
        _convert_game_state_to_response(game) for game in games
    ]
    
    return GamesListResponse(games=game_responses)


@app.get("/games/my-games", response_model=GamesListResponse)
async def get_my_games(
    game_service: GameServiceDep,
    player_name: PlayerNameDep
) -> GamesListResponse:
    """Retrieve a list of games where the authenticated player has joined.
    
    Requires Basic Auth with player name as username.
    """
    games = game_service.get_games()
    
    # Filter games where the authenticated player is a participant
    my_games = []
    for game in games:
        for player in game.players:
            if player.name == player_name:
                my_games.append(game)
                break
    
    # Convert to response format
    game_responses = [
        _convert_game_state_to_response(game) for game in my_games
    ]
    
    return GamesListResponse(games=game_responses)


@app.post("/games", response_model=GameStateResponse)
async def create_game(
    request: CreateGameRequest,
    game_service: GameServiceDep,
    player_name: PlayerNameDep
) -> GameStateResponse:
    """Create a new game and automatically join the creator.
    
    Requires Basic Auth with player name as username.
    """
    # Create the game
    game_state = game_service.create_game(request.num_players)
    
    # Automatically join the creator to the game
    game_state = game_service.join_game(str(game_state.game_id), player_name)
    
    # Find the creator player ID for response
    creator_player_id = None
    for player in game_state.players:
        if player.name == player_name:
            creator_player_id = player.id
            break
    
    return _convert_game_state_to_response(game_state, creator_player_id)


@app.post("/games/{game_id}/players", response_model=GameStateResponse)
async def join_game(
    game_id: str,
    game_service: GameServiceDep,
    player_name: PlayerNameDep
) -> GameStateResponse:
    """Join a game by game ID.
    
    Requires Basic Auth with player name as username.
    """
    # Get original state before joining for rack sizes
    try:
        original_game_state = game_service._load_game_state(game_id)
    except GameNotFoundError:
        original_game_state = None
    
    # Join the game (returns curated state for the joining player)
    game_state = game_service.join_game(game_id, player_name)
    
    # Find the player who just joined to return their curated view
    requesting_player = None
    for player in game_state.players:
        if player.name == player_name:
            requesting_player = player.id
            break
    
    return _convert_game_state_to_response(game_state, requesting_player, original_game_state)


@app.get("/games/{game_id}/players/{player_id}", response_model=GameStateResponse)
async def get_game_state(
    game_id: str,
    player_id: str,
    game_service: GameServiceDep
) -> GameStateResponse:
    """Get game state for a specific player."""
    # Only log non-routine state requests to reduce polling noise
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
            logger.warning(f"Player {player_id} not found in game {game_id}")
            from ..models.exceptions import PlayerNotInGameError
            raise PlayerNotInGameError("Player not in game")
        
        # Get curated game state for this player
        curated_game_state = game_service._curate_game_state_for_player(game_state, player_id)
        
        return _convert_game_state_to_response(curated_game_state, player_id, game_state)
    
    except GameNotFoundError:
        logger.warning(f"Game {game_id} not found for player {player_id}")
        raise GameNotFoundError("Game not found")


@app.post("/games/{game_id}/players/{player_id}/actions/play", response_model=GameStateResponse)
async def play_tiles(
    game_id: str,
    player_id: str,
    request: PlayTilesRequest,
    game_service: GameServiceDep
) -> GameStateResponse:
    """Execute a play tiles action."""
    
    logger.info(f"Player {player_id} attempting to play tiles in game {game_id} with {len(request.melds)} melds")
    
    # Convert request to domain action
    from ..models.melds import Meld, MeldKind
    melds = []
    for i, meld_req in enumerate(request.melds):
        meld = Meld(
            kind=MeldKind(meld_req.kind),
            tiles=meld_req.tiles
        )
        logger.debug(f"Meld {i}: {meld_req.kind} with {len(meld_req.tiles)} tiles")
        melds.append(meld)
    
    action = PlayTilesAction(melds=melds)
    
    # Execute action
    try:
        game_state = game_service.execute_turn(game_id, player_id, action)
        logger.info(f"Play tiles action successful for player {player_id} in game {game_id}")
        return _convert_game_state_to_response(game_state, player_id)
    except Exception as e:
        logger.error(f"Play tiles action failed for player {player_id} in game {game_id}: {e}")
        raise


@app.post("/games/{game_id}/players/{player_id}/actions/draw", response_model=GameStateResponse)
async def draw_tile(
    game_id: str,
    player_id: str,
    request: DrawTileRequest,
    game_service: GameServiceDep
) -> GameStateResponse:
    """Draw a tile from the pool."""
    
    logger.info(f"Player {player_id} attempting to draw tile in game {game_id}")
    
    # Create draw action
    action = DrawAction()
    
    # Execute action
    try:
        game_state = game_service.execute_turn(game_id, player_id, action)
        logger.info(f"Draw tile action successful for player {player_id} in game {game_id}")
        return _convert_game_state_to_response(game_state, player_id)
    except Exception as e:
        logger.error(f"Draw tile action failed for player {player_id} in game {game_id}: {e}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}