"""Game rules validation module for Rummikub.

This module contains all the validation logic for Rummikub game rules,
separated from the main game engine for better organization.
"""

import logging
from typing import List, Set

from ..models import (
    GameState, Player, Meld, GameStatus
)
from ..models.exceptions import (
    TileNotOwnedError, InitialMeldNotMetError, InvalidBoardStateError
)

# Create logger for game rules validation
logger = logging.getLogger(__name__)


class GameRules:
    """Class containing all Rummikub game rule validations."""
    
    @staticmethod
    def validate_player_turn(game_state: GameState, player_id: str) -> bool:
        """Validate that it's the specified player's turn."""
        logger.debug(f"Validating player turn for player {player_id}")
        logger.debug(f"Game status: {game_state.status}, current_player_index: {game_state.current_player_index}")
        
        is_valid = (game_state.status == GameStatus.IN_PROGRESS and 
                   game_state.current_player_index is not None and
                   len(game_state.players) > game_state.current_player_index and
                   game_state.players[game_state.current_player_index].id == player_id)
        
        if not is_valid:
            logger.debug(f"Player turn validation failed for {player_id}: "
                        f"status={game_state.status}, index={game_state.current_player_index}, "
                        f"player_count={len(game_state.players)}")
        else:
            logger.debug(f"Player turn validation passed for {player_id}")
        
        return is_valid
    
    @staticmethod
    def validate_tile_ownership(player: Player, newly_played_tiles: Set[str]) -> None:
        """Validate that player owns all newly played tiles.
        
        Args:
            player: Player attempting the action
            newly_played_tiles: Set of tile IDs being played
            
        Raises:
            TileNotOwnedError: If player doesn't own any of the tiles
        """
        logger.debug(f"Validating tile ownership for player {player.id}")
        logger.debug(f"Player has {len(player.rack.tile_ids)} tiles in rack")
        logger.debug(f"Attempting to play {len(newly_played_tiles)} tiles: {newly_played_tiles}")
        
        player_tiles = set(player.rack.tile_ids)
        for tile_id in newly_played_tiles:
            if tile_id not in player_tiles:
                logger.error(f"Tile ownership validation failed: Player {player.id} does not own tile {tile_id}")
                logger.debug(f"Player tiles: {player_tiles}")
                raise TileNotOwnedError(f"Player {player.id} does not own tile {tile_id}")
        
        logger.debug(f"Tile ownership validation passed for player {player.id}")
    
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
        logger.debug(f"Validating {len(melds)} meld structures")
        
        for i, meld in enumerate(melds):
            logger.debug(f"Validating meld {i}: {meld.kind.value} with {len(meld.tiles)} tiles")
            
            if not GameRules.validate_meld_structure(meld):
                logger.error(f"Meld structure validation failed for meld {i}: {meld}")
                raise InvalidBoardStateError(f"Invalid meld structure: {meld}")
                
        logger.debug("All meld structures validated successfully")
    
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
        logger.debug(f"Validating initial meld requirement for player {player.id}")
        logger.debug(f"Player initial meld met: {player.initial_meld_met}")
        logger.debug(f"Newly played tiles count: {len(newly_played_tiles)}")
        
        if not player.initial_meld_met and newly_played_tiles:
            # Get only the melds that contain newly played tiles (initial meld melds)
            initial_melds = []
            for meld in action_melds:
                if any(tile_id in newly_played_tiles for tile_id in meld.tiles):
                    initial_melds.append(meld)
            
            logger.debug(f"Found {len(initial_melds)} melds for initial meld validation")
            
            is_valid = GameRules.validate_initial_meld(initial_melds)
            logger.debug(f"Initial meld validation result: {is_valid}")
            
            if not is_valid:
                logger.error(f"Initial meld requirement not met for player {player.id}")
                raise InitialMeldNotMetError("Initial meld must total at least 30 points")
        else:
            logger.debug("Initial meld requirement check skipped (already met or no new tiles)")
    
    @staticmethod
    def validate_pool_not_empty(game_state: GameState) -> None:
        """Validate that the pool is not empty.
        
        Args:
            game_state: Current game state
            
        Raises:
            PoolEmptyError: If the pool is empty
        """
        from ..models.exceptions import PoolEmptyError
        
        pool_size = len(game_state.pool.tile_ids)
        logger.debug(f"Validating pool not empty: pool has {pool_size} tiles")
        
        if pool_size == 0:
            logger.error("Pool empty validation failed: cannot draw from empty pool")
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
                    game_name=game_state.game_name,
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
                rack_size = len(player.rack.tile_ids)
                initial_meld_met = player.initial_meld_met
                has_won = rack_size == 0 and initial_meld_met
                
                logger.debug(f"Win condition check for player {player_id}: "
                           f"rack_size={rack_size}, initial_meld_met={initial_meld_met}, won={has_won}")
                
                return has_won
        return False

    @staticmethod
    def validate_initial_meld(melds: List[Meld]) -> bool:
        """Check if proposed melds meet initial meld requirement (>= 30 points).
        
        Args:
            melds: Proposed melds to validate
            
        Returns:
            True if melds total >= 30 points
        """
        if not melds:
            logger.debug("Initial meld validation: no melds provided")
            return False
        
        logger.debug(f"Validating initial meld with {len(melds)} melds")
        
        total_value = 0
        for i, meld in enumerate(melds):
            try:
                # Validate the meld structure first
                meld.validate()
                # Get the value of the meld
                meld_value = meld.get_value()
                total_value += meld_value
                logger.debug(f"Meld {i}: {meld.kind.value} worth {meld_value} points")
            except Exception as e:
                # If meld is invalid, the initial meld is invalid
                logger.debug(f"Meld {i} validation failed: {e}")
                return False
        
        is_valid = total_value >= 30
        logger.debug(f"Initial meld total value: {total_value}, valid (>=30): {is_valid}")
        return is_valid

    @staticmethod
    def validate_meld_structure(meld: Meld) -> bool:
        """Validate basic meld structure (size constraints).
        
        Groups must have 3-4 tiles (limited by the 4 available colors).
        Runs must have at least 3 tiles and can be up to 13 tiles
        (limited only by the tile number range 1-13).
        
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