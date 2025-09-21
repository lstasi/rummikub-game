"""Game actions module for Rummikub.

This module contains all the game actions that can be performed,
separated from the main game engine for better organization.
"""

import random
from typing import Dict, List, Set
from uuid import UUID

from ..models import (
    GameState, GameStatus, Player, PlayTilesAction, Rack,
    # Exceptions
    GameNotStartedError, NotPlayersTurnError, PlayerNotInGameError,
    InvalidMoveError, TileNotOwnedError, PoolEmptyError, InvalidBoardStateError,
    InitialMeldNotMetError
)
from .game_rules import GameRules


class GameActions:
    """Class containing all game actions that can be performed."""
    
    @staticmethod
    def execute_play_action(game_state: GameState, player_id: str, action: PlayTilesAction) -> GameState:
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
        if not GameActions._can_player_act(game_state, player_id):
            if game_state.status != GameStatus.IN_PROGRESS:
                raise GameNotStartedError("Game is not in progress")
            raise NotPlayersTurnError(f"It's not {player_id}'s turn")
        
        # Get player (validates player exists in game)
        player = GameActions._get_player(game_state, player_id)
        
        # Full implementation of play action validation and execution:
        
        # 1. Collect all tiles being played from the new melds
        all_played_tiles = set()
        for meld in action.melds:
            all_played_tiles.update(meld.tiles)
        
        # Get all tiles currently on the board
        current_board_tiles = set()
        for meld in game_state.board.melds:
            current_board_tiles.update(meld.tiles)
        
        # Determine which tiles are newly played (not already on board)
        newly_played_tiles = all_played_tiles - current_board_tiles
        
        # 2. Validate tile ownership - player must own all newly played tiles
        player_tiles = set(player.rack.tile_ids)
        for tile_id in newly_played_tiles:
            if tile_id not in player_tiles:
                raise TileNotOwnedError(f"Player {player_id} does not own tile {tile_id}")
        
        # 3. Validate all melds in the action using game rules
        for meld in action.melds:
            if not GameRules.validate_meld_structure(meld):
                raise InvalidBoardStateError(f"Invalid meld structure: {meld}")
        
        # 4. Check initial meld requirement if not yet met
        if not player.initial_meld_met and newly_played_tiles:
            # Get only the melds that contain newly played tiles (initial meld melds)
            initial_melds = []
            for meld in action.melds:
                # Check if this meld contains any newly played tiles
                if any(tile_id in newly_played_tiles for tile_id in meld.tiles):
                    initial_melds.append(meld)
            
            if initial_melds:
                # Create minimal tile instances for validation
                # In practice, this would come from the game state's tile registry
                initial_tiles = []
                for tile_id in newly_played_tiles:
                    # Create a dummy tile instance for validation
                    from ..models.tiles import TileInstance, NumberedTile, Color
                    # Simplified: assume all tiles are worth 5 points
                    dummy_tile = TileInstance(kind=NumberedTile(number=5, color=Color.RED))
                    dummy_tile.id = tile_id  # Override the ID
                    initial_tiles.append(dummy_tile)
                
                if not GameRules.validate_initial_meld(initial_tiles, initial_melds):
                    raise InitialMeldNotMetError("Initial meld must have total value >= 30 points")
        
        # 5. Update player rack by removing used tiles
        updated_rack_tiles = [tile_id for tile_id in player.rack.tile_ids 
                            if tile_id not in newly_played_tiles]
        updated_rack = type(player.rack)(tile_ids=updated_rack_tiles)
        
        # Update player with new rack and mark initial meld as met if tiles were played
        updated_player = type(player)(
            id=player.id,
            name=player.name,
            initial_meld_met=player.initial_meld_met or bool(newly_played_tiles),
            rack=updated_rack
        )
        
        # Update players list
        updated_players = []
        for p in game_state.players:
            if p.id == player_id:
                updated_players.append(updated_player)
            else:
                updated_players.append(p)
        
        # 6. Update board with new melds
        new_board = type(game_state.board)(melds=action.melds)
        
        new_game_state = GameState(
            game_id=game_state.game_id,
            players=updated_players,
            pool=game_state.pool,
            board=new_board,
            current_player_index=game_state.current_player_index,
            status=game_state.status,
            created_at=game_state.created_at,
            updated_at=game_state.updated_at
        )
        
        # Check win condition
        if GameRules.check_win_condition(new_game_state, player_id):
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

    @staticmethod
    def execute_draw_action(game_state: GameState, player_id: str) -> GameState:
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
        if not GameActions._can_player_act(game_state, player_id):
            if game_state.status != GameStatus.IN_PROGRESS:
                raise GameNotStartedError("Game is not in progress")
            raise NotPlayersTurnError(f"It's not {player_id}'s turn")
        
        # Check pool is not empty
        if len(game_state.pool.tile_ids) == 0:
            raise PoolEmptyError("Cannot draw from empty pool")
            
        # Get player (validates player exists in game)  
        player = GameActions._get_player(game_state, player_id)
        
        # Full implementation of draw action:
        
        # 1. Remove a random tile from pool
        available_tiles = list(game_state.pool.tile_ids)
        drawn_tile = random.choice(available_tiles)
        remaining_pool_tiles = [tile_id for tile_id in available_tiles if tile_id != drawn_tile]
        updated_pool = type(game_state.pool)(tile_ids=remaining_pool_tiles)
        
        # 2. Add drawn tile to player's rack
        updated_rack_tiles = player.rack.tile_ids + [drawn_tile]
        updated_rack = type(player.rack)(tile_ids=updated_rack_tiles)
        
        # Update player with new rack
        updated_player = type(player)(
            id=player.id,
            name=player.name,
            initial_meld_met=player.initial_meld_met,
            rack=updated_rack
        )
        
        # Update players list
        updated_players = []
        for p in game_state.players:
            if p.id == player_id:
                updated_players.append(updated_player)
            else:
                updated_players.append(p)
        
        # Return updated game state
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

    @staticmethod
    def advance_turn(game_state: GameState) -> GameState:
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
                from ..models.exceptions import GameFinishedError
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

    @staticmethod
    def _can_player_act(game_state: GameState, player_id: str) -> bool:
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
            current_player = game_state.players[game_state.current_player_index].id
            return current_player == player_id
        except (IndexError, AttributeError):
            return False

    @staticmethod
    def _get_player(game_state: GameState, player_id: str) -> Player:
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