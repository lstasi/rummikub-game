"""Game actions module for Rummikub.

This module contains all the game actions that can be performed,
separated from the main game engine for better organization.
"""

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
        # Validate player's turn using game rules
        if not GameRules.validate_player_turn(game_state, player_id):
            if game_state.status != GameStatus.IN_PROGRESS:
                raise GameNotStartedError("Game is not in progress")
            raise NotPlayersTurnError(f"It's not {player_id}'s turn")
        
        # Get player (validates player exists in game)
        player = GameActions._get_player(game_state, player_id)
        
        # Use game rules for validation and execution:
        
        # 1. Identify newly played tiles
        newly_played_tiles = GameRules.identify_newly_played_tiles(action.melds, game_state.board.melds)
        
        # 2. Validate tile ownership
        GameRules.validate_tile_ownership(player, newly_played_tiles)
        
        # 3. Validate all meld structures
        GameRules.validate_meld_structures(action.melds)
        
        # 4. Check initial meld requirement if not yet met
        GameRules.validate_initial_meld_requirement(player, newly_played_tiles, action.melds)
        
        # 5. Update player rack using game rules
        updated_rack = GameRules.update_player_rack(player, newly_played_tiles)
        
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
        
        # Check win condition using game rules
        if GameRules.check_win_condition(updated_player):
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
        # Validate player's turn using game rules
        if not GameRules.validate_player_turn(game_state, player_id):
            if game_state.status != GameStatus.IN_PROGRESS:
                raise GameNotStartedError("Game is not in progress")
            raise NotPlayersTurnError(f"It's not {player_id}'s turn")
        
        # Validate pool is not empty using game rules
        GameRules.validate_pool_not_empty(game_state)
            
        # Get player (validates player exists in game)  
        player = GameActions._get_player(game_state, player_id)
        
        # Use pool method and game rules for draw action:
        drawn_tile, updated_pool = game_state.pool.get_random_tile()
        
        # Add drawn tile to player's rack using game rules
        updated_rack = GameRules.add_tile_to_rack(player, drawn_tile)
        
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
        
        # Check for winner before advancing turn (as requested in feedback)        
        updated_game_state = GameRules.check_for_winner(game_state)
        
        # If game is completed due to winner, return immediately
        if updated_game_state.status == GameStatus.COMPLETED:
            return updated_game_state
                
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
        return GameRules.validate_player_turn(game_state, player_id)

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