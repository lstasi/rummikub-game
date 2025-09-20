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
    JokerRetrievalError, JokerNotReusedError
)


class GameEngine:
    """Game engine that enforces Rummikub rules and manages game state.
    
    The engine is stateless - all state is passed as parameters and returned
    as new GameState objects. This ensures thread safety and makes the engine
    easy to test and reason about.
    """

    def create_game(self, game_id: UUID, num_players: int) -> GameState:
        """Initialize a new game with specified number of players (2-4).
        
        Args:
            game_id: Unique identifier for the game
            num_players: Number of players for this game (must be 2-4)
            
        Returns:
            New GameState with WAITING_FOR_PLAYERS status
            
        Raises:
            GameStateError: If num_players is not between 2 and 4
        """
        return GameState.create_new_game(game_id, num_players)

    def add_player(self, game_state: GameState, player_id: str, player_name: str = None) -> GameState:
        """Add a player to the game. Deals tiles and starts game when full.
        
        Args:
            game_state: Current game state
            player_id: Unique identifier for the player
            player_name: Optional display name for the player
            
        Returns:
            Updated GameState with new player added
            
        Raises:
            GameFullError: If game already has maximum players
            GameNotStartedError: If game is not in waiting_for_players status
            InvalidMoveError: If player is already in the game
        """
        if game_state.status != GameStatus.WAITING_FOR_PLAYERS:
            raise GameNotStartedError("Can only add players to games waiting for players")
            
        if len(game_state.players) >= 4:
            raise GameFullError("Game already has maximum 4 players")
            
        # Check if player already exists
        for existing_player in game_state.players:
            if existing_player.id == player_id:
                raise InvalidMoveError(f"Player {player_id} already in game")
        
        # Create new player
        new_player = Player(id=player_id, name=player_name or player_id)
        
        # Add player to game
        new_players = game_state.players + [new_player]
        new_game_state = GameState(
            game_id=game_state.game_id,
            players=new_players,
            pool=game_state.pool,
            board=game_state.board,
            current_player_index=game_state.current_player_index,
            status=game_state.status,
            created_at=game_state.created_at,
            updated_at=game_state.updated_at
        )
        
        # If game now has minimum players and is being set to start, start it
        # For this minimal implementation, start immediately when we reach 2 players
        if len(new_players) >= 2:
            return self._start_game(new_game_state)
            
        return new_game_state

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
        if game_state.status != GameStatus.IN_PROGRESS:
            return False
            
        try:
            current_player = self.get_current_player(game_state)
            return current_player == player_id
        except (GameNotStartedError, GameFinishedError):
            return False

    def advance_turn(self, game_state: GameState) -> GameState:
        """Move to the next player's turn.
        
        Args:
            game_state: Current game state
            
        Returns:
            Updated GameState with next player's turn
            
        Raises:
            GameNotStartedError: If game hasn't started yet
            GameFinishedError: If game is already finished
        """
        if game_state.status != GameStatus.IN_PROGRESS:
            if game_state.status == GameStatus.WAITING_FOR_PLAYERS:
                raise GameNotStartedError("Game hasn't started yet")
            else:
                raise GameFinishedError("Game is already finished")
                
        next_index = (game_state.current_player_index + 1) % len(game_state.players)
        
        return GameState(
            game_id=game_state.game_id,
            players=game_state.players,
            pool=game_state.pool,
            board=game_state.board,
            current_player_index=next_index,
            status=game_state.status,
            created_at=game_state.created_at,
            updated_at=game_state.updated_at
        )

    def execute_play_action(self, game_state: GameState, player_id: str, action: PlayTilesAction) -> GameState:
        """Execute tile play action (placement and/or rearrangement).
        
        Args:
            game_state: Current game state
            player_id: Player attempting the action
            action: PlayTilesAction containing new board state
            
        Returns:
            Updated GameState after successful play
            
        Raises:
            NotPlayersTurnError: If it's not the player's turn
            PlayerNotInGameError: If player is not in the game
            TileNotOwnedError: If player doesn't own tiles being played
            InitialMeldNotMetError: If initial meld requirement not met
            InvalidBoardStateError: If resulting board state is invalid
        """
        # Validate player's turn
        if not self.can_player_act(game_state, player_id):
            if game_state.status != GameStatus.IN_PROGRESS:
                raise GameNotStartedError("Game is not in progress")
            raise NotPlayersTurnError(f"It's not {player_id}'s turn")
        
        # Get player (validates player exists in game)
        self._get_player(game_state, player_id)
        
        # TODO: This is a minimal implementation. Full implementation would:
        # 1. Validate tile ownership
        # 2. Check initial meld requirement  
        # 3. Validate all melds in the action
        # 4. Update player rack by removing used tiles
        # 5. Update board with new melds
        # 6. Check win condition
        
        # For now, just return the game state with updated board
        new_board = type(game_state.board)(melds=action.melds)
        
        new_game_state = GameState(
            game_id=game_state.game_id,
            players=game_state.players,
            pool=game_state.pool,
            board=new_board,
            current_player_index=game_state.current_player_index,
            status=game_state.status,
            created_at=game_state.created_at,
            updated_at=game_state.updated_at
        )
        
        # Check win condition
        if self.check_win_condition(new_game_state, player_id):
            new_game_state = GameState(
                game_id=new_game_state.game_id,
                players=new_game_state.players,
                pool=new_game_state.pool,
                board=new_game_state.board,
                current_player_index=new_game_state.current_player_index,
                status=GameStatus.COMPLETED,
                created_at=new_game_state.created_at,
                updated_at=new_game_state.updated_at
            )
            
        return new_game_state

    def execute_draw_action(self, game_state: GameState, player_id: str) -> GameState:
        """Draw a tile from the pool.
        
        Args:
            game_state: Current game state
            player_id: Player attempting to draw
            
        Returns:
            Updated GameState after successful draw
            
        Raises:
            NotPlayersTurnError: If it's not the player's turn
            PlayerNotInGameError: If player is not in the game
            PoolEmptyError: If the pool is empty
        """
        # Validate player's turn
        if not self.can_player_act(game_state, player_id):
            if game_state.status != GameStatus.IN_PROGRESS:
                raise GameNotStartedError("Game is not in progress")
            raise NotPlayersTurnError(f"It's not {player_id}'s turn")
        
        # Check pool is not empty
        if len(game_state.pool.tile_ids) == 0:
            raise PoolEmptyError("Cannot draw from empty pool")
            
        # Get player (validates player exists in game)  
        self._get_player(game_state, player_id)
        
        # TODO: This is a minimal implementation. Full implementation would:
        # 1. Actually remove a tile from pool and add to player's rack
        # 2. Handle tile instances properly
        
        # For now, just return the same game state
        return game_state

    def validate_initial_meld(self, tiles: List[TileInstance], melds: List[Meld]) -> bool:
        """Check if proposed melds meet initial meld requirement (>= 30 points).
        
        Args:
            tiles: Available tile instances
            melds: Proposed melds to validate
            
        Returns:
            True if melds total >= 30 points
        """
        # TODO: Implement proper initial meld validation
        # For now, return True (minimal implementation)
        return True

    def validate_joker_retrieval(self, game_state: GameState, meld_id: UUID, 
                                replacement_tile: TileInstance, new_joker_usage: List[Meld]) -> bool:
        """Validate that joker retrieval is legal and joker is reused in same turn.
        
        Args:
            game_state: Current game state
            meld_id: ID of meld containing joker to retrieve
            replacement_tile: Tile to replace the joker with
            new_joker_usage: New melds where joker will be used
            
        Returns:
            True if joker retrieval is valid
            
        Raises:
            JokerRetrievalError: If retrieval is invalid
            JokerNotReusedError: If joker is not reused
        """
        # TODO: Implement proper joker retrieval validation
        # For now, return True (minimal implementation)
        return True

    def check_win_condition(self, game_state: GameState, player_id: str) -> bool:
        """Check if player has emptied their rack and won.
        
        Args:
            game_state: Current game state
            player_id: Player to check for win
            
        Returns:
            True if player has won
            
        Note:
            In this minimal implementation, we return False to avoid
            automatic wins since tiles aren't being managed properly yet.
        """
        player = self._get_player(game_state, player_id)
        # TODO: In the full implementation, return len(player.rack.tile_ids) == 0
        # For now, return False to prevent automatic wins in minimal implementation
        return False

    def calculate_scores(self, game_state: GameState) -> Dict[str, int]:
        """Calculate penalty scores based on remaining tiles in racks.
        
        Args:
            game_state: Completed game state
            
        Returns:
            Dictionary mapping player IDs to their penalty scores
        """
        scores = {}
        for player in game_state.players:
            # TODO: Calculate actual penalty based on remaining tiles
            # For now, return 0 for all players (minimal implementation)
            scores[player.id] = 0
        return scores

    def _start_game(self, game_state: GameState) -> GameState:
        """Start the game by dealing tiles to all players.
        
        Args:
            game_state: Game state with all players added
            
        Returns:
            Updated GameState with tiles dealt and status IN_PROGRESS
        """
        # TODO: This is a minimal implementation. Full implementation would:
        # 1. Create complete tile pool
        # 2. Deal 14 tiles to each player
        # 3. Update player racks with dealt tiles
        # 4. Update pool by removing dealt tiles
        
        # For now, just change status to IN_PROGRESS
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

    def _get_player(self, game_state: GameState, player_id: str) -> Player:
        """Get player by ID from game state.
        
        Args:
            game_state: Current game state
            player_id: ID of player to find
            
        Returns:
            Player object
            
        Raises:
            PlayerNotInGameError: If player is not found
        """
        for player in game_state.players:
            if player.id == player_id:
                return player
        raise PlayerNotInGameError(f"Player {player_id} not in game")