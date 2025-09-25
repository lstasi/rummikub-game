"""Game rules validation module for Rummikub.

This module contains all the validation logic for Rummikub game rules,
separated from the main game engine for better organization.
"""

from typing import Dict, List, Set

from ..models import (
    GameState, Player, Meld, TileInstance, GameStatus
)
from ..models.exceptions import (
    TileNotOwnedError, InitialMeldNotMetError, InvalidBoardStateError
)


class GameRules:
    """Class containing all Rummikub game rule validations."""
    
    @staticmethod
    def validate_player_turn(game_state: GameState, player_id: str) -> bool:
        """Validate that it's the specified player's turn."""
        return (game_state.status == GameStatus.IN_PROGRESS and 
                game_state.current_player_index is not None and
                len(game_state.players) > game_state.current_player_index and
                game_state.players[game_state.current_player_index].id == player_id)
    
    @staticmethod
    def validate_tile_ownership(player: Player, newly_played_tiles: Set[str]) -> None:
        """Validate that player owns all newly played tiles.
        
        Args:
            player: Player attempting the action
            newly_played_tiles: Set of tile IDs being played
            
        Raises:
            TileNotOwnedError: If player doesn't own any of the tiles
        """
        player_tiles = set(player.rack.tile_ids)
        for tile_id in newly_played_tiles:
            if tile_id not in player_tiles:
                raise TileNotOwnedError(f"Player {player.id} does not own tile {tile_id}")
    
    @staticmethod
    def identify_newly_played_tiles(action_melds: List[Meld], current_board_melds: List[Meld]) -> Set[str]:
        """Identify which tiles are newly played (not already on board).
        
        Args:
            action_melds: Melds from the play action
            current_board_melds: Current melds on the board
            
        Returns:
            Set of tile IDs that are newly played
        """
        # Collect all tiles being played from the new melds
        all_played_tiles = set()
        for meld in action_melds:
            all_played_tiles.update(meld.tiles)
        
        # Get all tiles currently on the board
        current_board_tiles = set()
        for meld in current_board_melds:
            current_board_tiles.update(meld.tiles)
        
        # Return newly played tiles
        return all_played_tiles - current_board_tiles
    
    @staticmethod
    def validate_meld_structures(melds: List[Meld]) -> None:
        """Validate that all melds have proper structure.
        
        Args:
            melds: List of melds to validate
            
        Raises:
            InvalidBoardStateError: If any meld has invalid structure
        """
        for meld in melds:
            if not GameRules.validate_meld_structure(meld):
                raise InvalidBoardStateError(f"Invalid meld structure: {meld}")
    
    @staticmethod
    def validate_initial_meld_requirement(player: Player, newly_played_tiles: Set[str], 
                                        action_melds: List[Meld]) -> None:
        """Validate initial meld requirement if not yet met.
        
        Args:
            player: Player attempting the action
            newly_played_tiles: Set of newly played tile IDs
            action_melds: Melds from the play action
            
        Raises:
            InitialMeldNotMetError: If initial meld requirement not met
        """
        if not player.initial_meld_met and newly_played_tiles:
            # Get only the melds that contain newly played tiles (initial meld melds)
            initial_melds = []
            for meld in action_melds:
                if any(tile_id in newly_played_tiles for tile_id in meld.tiles):
                    initial_melds.append(meld)
            
            # We need tile instances for validation - create them
            # TODO: This is a placeholder - need access to tile instances
            tile_instances: Dict[str, TileInstance] = {}  # This should come from game state
            
            if not GameRules.validate_initial_meld(tile_instances, initial_melds):
                raise InitialMeldNotMetError("Initial meld must total at least 30 points")
    
    @staticmethod
    def validate_pool_not_empty(game_state: GameState) -> None:
        """Validate that the pool is not empty.
        
        Args:
            game_state: Current game state
            
        Raises:
            PoolEmptyError: If the pool is empty
        """
        from ..models.exceptions import PoolEmptyError
        if len(game_state.pool.tile_ids) == 0:
            raise PoolEmptyError("Cannot draw from empty pool")
    
    @staticmethod
    def check_for_winner(game_state: GameState) -> GameState:
        """Check all players for win condition and update game status if winner found.
        
        Args:
            game_state: Current game state
            
        Returns:
            Updated GameState (completed if winner found, otherwise unchanged)
        """
        # Check if any player has won (empty rack)
        for player in game_state.players:
            if GameRules.check_win_condition(game_state, player.id):
                # Player has won - mark game as completed
                return GameState(
                    game_id=game_state.game_id,
                    players=game_state.players,
                    pool=game_state.pool,
                    board=game_state.board,
                    current_player_index=game_state.current_player_index,
                    status=GameStatus.COMPLETED,
                    created_at=game_state.created_at,
                    updated_at=game_state.updated_at
                )
        
        return game_state

    @staticmethod
    def check_win_condition(game_state: GameState, player_id: str) -> bool:
        """Check if player has emptied their rack and won.
        
        Args:
            game_state: Current game state
            player_id: Player to check for win
            
        Returns:
            True if player has won (empty rack and initial meld met)
        """
        for player in game_state.players:
            if player.id == player_id:
                # Player wins if rack is empty AND initial meld requirement is met
                return len(player.rack.tile_ids) == 0 and player.initial_meld_met
        return False

    @staticmethod
    def validate_initial_meld(tiles: Dict[str, TileInstance], melds: List[Meld]) -> bool:
        """Check if proposed melds meet initial meld requirement (>= 30 points).
        
        Args:
            tiles: Tile instances mapping (tile_id -> TileInstance)
            melds: Proposed melds to validate
            
        Returns:
            True if melds total >= 30 points
        """
        if not melds:
            return False
            
        # tiles is already the correct mapping format
        tile_instances = tiles
        
        total_value = 0
        for meld in melds:
            try:
                # Validate the meld structure first
                meld.validate_with_tiles(tile_instances)
                # Get the value of the meld
                meld_value = meld.get_value(tile_instances)
                total_value += meld_value
            except Exception:
                # If meld is invalid, the initial meld is invalid
                return False
                
        return total_value >= 30

    @staticmethod
    def validate_meld_structure(meld: Meld) -> bool:
        """Validate basic meld structure (size constraints).
        
        Args:
            meld: Meld to validate
            
        Returns:
            True if meld structure is valid
        """
        if len(meld.tiles) == 0:
            return False
            
        if meld.kind.value == "group":
            return 3 <= len(meld.tiles) <= 4
        elif meld.kind.value == "run":
            return len(meld.tiles) >= 3
            
        return False