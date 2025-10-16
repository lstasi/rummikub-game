"""Tests for validating that empty moves are rejected."""

import pytest

from rummikub.models import (
    Color, TileUtils, Meld, MeldKind, 
    PlayTilesAction, GameState, Rack,
    InvalidMoveError
)
from rummikub.engine import GameEngine
from rummikub.engine.game_actions import GameActions


class TestEmptyMoveValidation:
    """Test that empty moves (no new tiles played) are properly rejected."""
    
    def test_empty_melds_list_rejected(self):
        """Test that playing with an empty melds list is rejected."""
        # Create and start a game
        game_state = GameState.create_initialized_game(2)
        game_state = GameActions.join_player(game_state, "Alice")
        game_state = GameActions.join_player(game_state, "Bob")
        
        # Get current player
        current_player = game_state.players[game_state.current_player_index]
        
        # Try to play with empty melds list
        action = PlayTilesAction(melds=[])
        
        # Should raise InvalidMoveError
        with pytest.raises(InvalidMoveError, match="Cannot play without placing any new tiles"):
            GameActions.execute_play_action(game_state, current_player.id, action)
    
    def test_no_board_change_rejected(self):
        """Test that submitting the same board state is rejected."""
        # Create and start a game
        game_state = GameState.create_initialized_game(2)
        game_state = GameActions.join_player(game_state, "Alice")
        game_state = GameActions.join_player(game_state, "Bob")
        
        player1 = game_state.players[0]
        player2 = game_state.players[1]
        
        # Set up player1 to have tiles for a valid initial meld
        tiles_for_meld = [
            TileUtils.create_numbered_tile_id(10, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(10, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(10, Color.BLACK, 'a'),
        ]
        
        # Give player1 these tiles
        updated_rack = Rack(tile_ids=list(player1.rack.tile_ids) + tiles_for_meld)
        player1_updated = player1.update(rack=updated_rack)
        game_state = game_state.update_player(player1.id, player1_updated)
        
        # Player1 plays initial meld
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles_for_meld)
        action = PlayTilesAction(melds=[meld])
        game_state = GameActions.execute_play_action(game_state, player1.id, action)
        
        # Now player2 tries to submit the same board (no changes)
        current_board_melds = list(game_state.board.melds)
        action_no_change = PlayTilesAction(melds=current_board_melds)
        
        # Should raise InvalidMoveError
        with pytest.raises(InvalidMoveError, match="Cannot play without placing any new tiles"):
            GameActions.execute_play_action(game_state, player2.id, action_no_change)
    
    def test_valid_play_still_works(self):
        """Test that valid plays with new tiles still work."""
        # Create and start a game
        game_state = GameState.create_initialized_game(2)
        game_state = GameActions.join_player(game_state, "Alice")
        game_state = GameActions.join_player(game_state, "Bob")
        
        player1 = game_state.players[0]
        
        # Set up player1 to have tiles for a valid initial meld
        tiles_for_meld = [
            TileUtils.create_numbered_tile_id(10, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(10, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(10, Color.BLACK, 'a'),
        ]
        
        # Give player1 these tiles
        updated_rack = Rack(tile_ids=list(player1.rack.tile_ids) + tiles_for_meld)
        player1_updated = player1.update(rack=updated_rack)
        game_state = game_state.update_player(player1.id, player1_updated)
        
        # Player1 plays initial meld - should work
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles_for_meld)
        action = PlayTilesAction(melds=[meld])
        
        # Should succeed without raising an exception
        new_state = GameActions.execute_play_action(game_state, player1.id, action)
        
        # Verify the play worked
        assert len(new_state.board.melds) == 1
        assert new_state.players[0].initial_meld_met is True
        # Turn should have advanced to player 2
        assert new_state.current_player_index == 1
    
    def test_rearrangement_with_new_tiles_works(self):
        """Test that rearranging existing melds while adding new tiles works."""
        # Create and start a game
        game_state = GameState.create_initialized_game(2)
        game_state = GameActions.join_player(game_state, "Alice")
        game_state = GameActions.join_player(game_state, "Bob")
        
        player1 = game_state.players[0]
        
        # Set up player1 to have tiles for an initial meld
        initial_tiles = [
            TileUtils.create_numbered_tile_id(10, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(10, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(10, Color.BLACK, 'a'),
        ]
        
        # Give player1 these tiles
        updated_rack = Rack(tile_ids=list(player1.rack.tile_ids) + initial_tiles)
        player1_updated = player1.update(rack=updated_rack)
        game_state = game_state.update_player(player1.id, player1_updated)
        
        # Player1 plays initial meld
        meld = Meld(kind=MeldKind.GROUP, tiles=initial_tiles)
        action = PlayTilesAction(melds=[meld])
        game_state = GameActions.execute_play_action(game_state, player1.id, action)
        
        # Now it's player2's turn
        player2 = game_state.players[1]
        
        # Set up player2 to have tiles for another meld
        additional_tiles = [
            TileUtils.create_numbered_tile_id(11, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(11, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(11, Color.BLACK, 'a'),
        ]
        
        # Give player2 these tiles
        updated_rack = Rack(tile_ids=list(player2.rack.tile_ids) + additional_tiles)
        player2_updated = player2.update(rack=updated_rack)
        game_state = game_state.update_player(player2.id, player2_updated)
        
        # Player2 plays new meld alongside existing one
        existing_meld = game_state.board.melds[0]
        new_meld = Meld(kind=MeldKind.GROUP, tiles=additional_tiles)
        action = PlayTilesAction(melds=[existing_meld, new_meld])
        
        # Should succeed - player2 is adding new tiles
        new_state = GameActions.execute_play_action(game_state, player2.id, action)
        
        # Verify the play worked
        assert len(new_state.board.melds) == 2
        assert new_state.players[1].initial_meld_met is True


class TestGameEngineEmptyMove:
    """Test empty move validation through the GameEngine interface."""
    
    def test_engine_rejects_empty_play(self):
        """Test that GameEngine.execute_play_action rejects empty plays."""
        engine = GameEngine()
        game_state = engine.create_game(2)
        
        # Join players
        game_state = engine.join_game(game_state, "Player1")
        game_state = engine.join_game(game_state, "Player2")
        
        # Get current player
        current_player = game_state.players[game_state.current_player_index]
        
        # Try to play with empty melds
        action = PlayTilesAction(melds=[])
        
        # Should raise InvalidMoveError
        with pytest.raises(InvalidMoveError, match="Cannot play without placing any new tiles"):
            engine.execute_play_action(game_state, current_player.id, action)
