"""Game rules validation module for Rummikub.

This module contains all the validation logic for Rummikub game rules,
separated from the main game engine for better organization.
"""

from typing import Dict, List
from uuid import UUID

from ..models import (
    GameState, Player, Meld, TileInstance, GameStatus
)


class GameRules:
    """Class containing all Rummikub game rule validations."""
    
    @staticmethod
    def validate_initial_meld(tiles: List[TileInstance], melds: List[Meld]) -> bool:
        """Check if proposed melds meet initial meld requirement (>= 30 points).
        
        Args:
            tiles: Available tile instances (mapping for validation)
            melds: Proposed melds to validate
            
        Returns:
            True if melds total >= 30 points
        """
        if not melds:
            return False
            
        # Create tile instances mapping for validation
        tile_instances = {str(tile.id): tile for tile in tiles}
        
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

    @staticmethod
    def check_win_condition(game_state: GameState, player_id: str) -> bool:
        """Check if player has emptied their rack and won.
        
        Args:
            game_state: Current game state
            player_id: Player to check for win
            
        Returns:
            True if player has won
        """
        for player in game_state.players:
            if player.id == player_id:
                return len(player.rack.tile_ids) == 0
        return False