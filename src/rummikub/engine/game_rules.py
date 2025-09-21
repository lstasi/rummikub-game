"""Game rules validation module for Rummikub.

This module contains all the validation logic for Rummikub game rules,
separated from the main game engine for better organization.
"""

from typing import Dict, List
from uuid import UUID

from ..models import (
    GameState, Player, Meld, TileInstance, GameStatus,
    # Exceptions
    InitialMeldNotMetError, JokerRetrievalError, JokerNotReusedError
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
    def validate_joker_retrieval(game_state: GameState, meld_id: UUID, 
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
        # Find the meld containing the joker
        target_meld = None
        for meld in game_state.board.melds:
            if meld.id == meld_id:
                target_meld = meld
                break
                
        if not target_meld:
            raise JokerRetrievalError(f"Meld {meld_id} not found on board")
        
        # Check if meld actually contains a joker
        # Note: This is simplified - in full implementation would check tile instances
        if len(target_meld.tiles) == 0:
            raise JokerRetrievalError("Cannot retrieve joker from empty meld")
            
        # Validate that replacement tile makes the original meld still valid
        # Simplified validation - assumes the replacement is appropriate
        
        # Check that joker is being reused in the same turn
        if not new_joker_usage:
            raise JokerNotReusedError("Retrieved joker must be reused in the same turn")
            
        # Validate that new joker usage creates valid melds
        joker_count = 0
        for meld in new_joker_usage:
            # Count jokers being used (simplified check)
            if len(meld.tiles) >= 3:  # Basic meld size validation
                joker_count += 1  # Simplified - assumes one joker per meld
                
        if joker_count == 0:
            raise JokerNotReusedError("Retrieved joker must be used in new melds")
            
        return True

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
    def calculate_scores(game_state: GameState) -> Dict[str, int]:
        """Calculate penalty scores based on remaining tiles in racks.
        
        Args:
            game_state: Completed game state
            
        Returns:
            Dictionary mapping player IDs to their penalty scores
        """
        scores = {}
        for player in game_state.players:
            penalty_score = 0
            
            # Calculate penalty based on tiles remaining in rack
            for tile_id in player.rack.tile_ids:
                # Simplified scoring - in full implementation would get actual tile values
                # For now, assume each tile is worth 5 points penalty
                # Jokers would be worth 30 points, numbered tiles their face value
                penalty_score += 5  # Simplified penalty per tile
                
            scores[player.id] = penalty_score
            
        return scores

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