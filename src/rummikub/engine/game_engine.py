"""Game engine implementation for Rummikub.

This module contains the core game engine that enforces all Rummikub rules
and manages game state transitions.
"""

from typing import Dict, List
from uuid import UUID

from ..models import (
    GameState, GameStatus, Player, PlayTilesAction, TileInstance, Meld,
    # Exceptions
    GameNotFoundError, GameFullError, GameNotStartedError, GameFinishedError,
    NotPlayersTurnError, PlayerNotInGameError, InitialMeldNotMetError,
    InvalidMoveError, TileNotOwnedError, PoolEmptyError, InvalidBoardStateError,
    JokerRetrievalError, JokerNotReusedError, GameStateError
)
from .game_rules import GameRules
from .game_actions import GameActions


class GameEngine:
    """Game engine that enforces Rummikub rules and manages game state.
    
    The engine is stateless - all state is passed as parameters and returned
    as new GameState objects. This ensures thread safety and makes the engine
    easy to test and reason about.
    """

    def create_game(self, num_players: int) -> GameState:
        """Initialize a new game with specified number of players (2-4).
        
        Args:
            num_players: Number of players for this game (must be 2-4, but games can accommodate up to 4)
            
        Returns:
            New GameState with WAITING_FOR_PLAYERS status and initialized pool
            
        Raises:
            GameStateError: If num_players is not between 2 and 4
        """
        from ..models.game import Pool
        
        # Validate num_players but don't strictly enforce it - allow flexibility
        if not (2 <= num_players <= 4):
            raise GameStateError(f"Number of players must be between 2 and 4, got {num_players}")
        
        # Create the base game state (generates UUID internally)
        game_state = GameState.create_new_game(None, num_players)
        
        # Initialize the complete tile pool
        pool = Pool.create_full_pool()
        
        # Return game state with initialized pool
        return GameState(
            game_id=game_state.game_id,
            players=game_state.players,
            pool=pool,
            board=game_state.board,
            current_player_index=game_state.current_player_index,
            status=game_state.status,
            created_at=game_state.created_at,
            updated_at=game_state.updated_at
        )

    def join_game(self, game_state: GameState, player_name: str) -> GameState:
        """Join a player to the game and deal tiles from pool.
        
        Args:
            game_state: Current game state
            player_name: Display name for the player (used as ID if unique)
            
        Returns:
            Updated GameState with new player added and tiles dealt
            
        Raises:
            GameFullError: If game already has maximum players
            GameNotStartedError: If game is not in waiting_for_players status
            InvalidMoveError: If player name already exists in the game
        """
        if game_state.status != GameStatus.WAITING_FOR_PLAYERS:
            raise GameNotStartedError("Can only join games waiting for players")
            
        if len(game_state.players) >= 4:
            raise GameFullError("Game already has maximum 4 players")
        
        # Check if player with this name already exists (by name, not ID)
        for existing_player in game_state.players:
            if existing_player.name == player_name:
                raise InvalidMoveError(f"Player with name '{player_name}' already in game")
        
        # Create rack from pool (handles tile dealing and pool reduction)
        player_rack, updated_pool = game_state.pool.create_rack(14)
        
        # Create new player (generates UUID internally)
        new_player = Player.create_player(player_name, player_rack)
        
        # Add player to game
        updated_players = game_state.players + [new_player]
        
        return GameState(
            game_id=game_state.game_id,
            players=updated_players,
            pool=updated_pool,
            board=game_state.board,
            current_player_index=game_state.current_player_index,
            status=game_state.status,
            created_at=game_state.created_at,
            updated_at=game_state.updated_at
        )
    
    def start_game(self, game_state: GameState) -> GameState:
        """Explicitly start the game after all players are added.
        
        Args:
            game_state: Game state with players added
            
        Returns:
            GameState with status IN_PROGRESS and tiles dealt
            
        Raises:
            GameStateError: If game has wrong number of players or is already started
        """
        if game_state.status != GameStatus.WAITING_FOR_PLAYERS:
            raise GameNotStartedError("Game can only be started from waiting_for_players status")
            
        if len(game_state.players) < 2:
            raise GameStateError("Need at least 2 players to start game")
            
        if len(game_state.players) > 4:
            raise GameStateError("Cannot have more than 4 players")
        
        return self._start_game(game_state)

    def get_game_status(self, game_state: GameState) -> GameStatus:
        """Get current game status.
        
        Args:
            game_state: Current game state
            
        Returns:
            Current GameStatus enum value
        """
        return game_state.status

    def get_current_player(self, game_state: GameState) -> str:
        """Get the ID of the player whose turn it is.
        
        Args:
            game_state: Current game state
            
        Returns:
            Player ID of current player
            
        Raises:
            GameNotStartedError: If game hasn't started yet
            GameFinishedError: If game is already finished
        """
        if game_state.status == GameStatus.WAITING_FOR_PLAYERS:
            raise GameNotStartedError("Game hasn't started yet")
        if game_state.status == GameStatus.COMPLETED:
            raise GameFinishedError("Game is already finished")
            
        return game_state.players[game_state.current_player_index].id

    def can_player_act(self, game_state: GameState, player_id: str) -> bool:
        """Check if the specified player can take actions.
        
        Args:
            game_state: Current game state
            player_id: Player to check
            
        Returns:
            True if it's the player's turn and game is active
        """
        return GameActions._can_player_act(game_state, player_id)

    def advance_turn(self, game_state: GameState) -> GameState:
        """Move to the next player's turn.
        
        Args:
            game_state: Current game state
            
        Returns:
            Updated GameState with next player's turn
        """
        return GameActions.advance_turn(game_state)

    def execute_play_action(self, game_state: GameState, player_id: str, action: PlayTilesAction) -> GameState:
        """Execute tile play action (placement and/or rearrangement).
        
        Args:
            game_state: Current game state
            player_id: Player attempting the action
            action: PlayTilesAction containing new board state
            
        Returns:
            Updated GameState after successful play
        """
        return GameActions.execute_play_action(game_state, player_id, action)

    def execute_draw_action(self, game_state: GameState, player_id: str) -> GameState:
        """Draw a tile from the pool.
        
        Args:
            game_state: Current game state
            player_id: Player attempting to draw
            
        Returns:
            Updated GameState after successful draw
        """
        return GameActions.execute_draw_action(game_state, player_id)

    def validate_initial_meld(self, tiles: List[TileInstance], melds: List[Meld]) -> bool:
        """Check if proposed melds meet initial meld requirement (>= 30 points).
        
        Args:
            tiles: Available tile instances
            melds: Proposed melds to validate
            
        Returns:
            True if melds total >= 30 points
        """
        return GameRules.validate_initial_meld(tiles, melds)

    def check_win_condition(self, game_state: GameState, player_id: str) -> bool:
        """Check if player has emptied their rack and won.
        
        Args:
            game_state: Current game state
            player_id: Player to check for win
            
        Returns:
            True if player has won
        """
        return GameRules.check_win_condition(game_state, player_id)

    def _start_game(self, game_state: GameState) -> GameState:
        """Start the game - players already have tiles dealt when they joined.
        
        Args:
            game_state: Game state with all players added and tiles dealt
            
        Returns:
            Updated GameState with status IN_PROGRESS
        """
        # Since pool is initialized at game creation and tiles are dealt when players join,
        # we just need to change the status to IN_PROGRESS
        return GameState(
            game_id=game_state.game_id,
            players=game_state.players,
            pool=game_state.pool,
            board=game_state.board,
            current_player_index=0,  # First player starts
            status=GameStatus.IN_PROGRESS,
            created_at=game_state.created_at,
            updated_at=game_state.updated_at
        )