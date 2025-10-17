"""Tests for improved joker validation in runs.

This test suite verifies the fix for joker validation that ensures
numbered tiles in a run are properly consecutive considering their positions.
"""

import pytest

from rummikub.models import Color, Meld, MeldKind
from rummikub.models.tiles import TileUtils
from rummikub.models.exceptions import InvalidBoardStateError
from rummikub.engine.game_rules import GameRules


class TestJokerRunValidationFix:
    """Test that runs with jokers properly validate gaps between numbered tiles."""
    
    def test_reject_run_with_large_gap_and_single_joker(self):
        """Test that [3, joker, 8] is rejected - gap is too large for one joker."""
        tiles = [
            TileUtils.create_numbered_tile_id(3, Color.RED, 'a'),
            TileUtils.create_joker_tile_id('a'),
            TileUtils.create_numbered_tile_id(8, Color.RED, 'a'),
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should raise InvalidBoardStateError because the gap between 3 and 8 is 5,
        # but there's only 1 position (joker) between them
        with pytest.raises(InvalidBoardStateError, match="not consecutive"):
            GameRules.validate_meld_structures([meld])
    
    def test_reject_run_with_non_consecutive_numbered_tiles(self):
        """Test that [2, 5, 8] is rejected - numbers aren't consecutive."""
        tiles = [
            TileUtils.create_numbered_tile_id(2, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(5, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(8, Color.BLUE, 'a'),
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should raise InvalidBoardStateError because the gaps are too large
        with pytest.raises(InvalidBoardStateError, match="not consecutive"):
            GameRules.validate_meld_structures([meld])
    
    def test_accept_valid_run_with_joker_in_middle(self):
        """Test that [5, joker, 7] is accepted - joker fills gap correctly."""
        tiles = [
            TileUtils.create_numbered_tile_id(5, Color.RED, 'a'),
            TileUtils.create_joker_tile_id('a'),
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a')
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should not raise exception - joker correctly fills the gap at position 1
        GameRules.validate_meld_structures([meld])
        assert meld.get_value() == 18  # 5 + 6 + 7
    
    def test_accept_valid_run_with_joker_at_end(self):
        """Test that [2, 3, joker] is accepted - valid extension."""
        tiles = [
            TileUtils.create_numbered_tile_id(2, Color.ORANGE, 'a'),
            TileUtils.create_numbered_tile_id(3, Color.ORANGE, 'a'),
            TileUtils.create_joker_tile_id('a'),
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should not raise exception - represents [2, 3, 4]
        GameRules.validate_meld_structures([meld])
        assert meld.get_value() == 9  # 2 + 3 + 4
    
    def test_accept_valid_run_with_joker_at_start(self):
        """Test that [joker, 2, 3] is accepted - valid extension."""
        tiles = [
            TileUtils.create_joker_tile_id('a'),
            TileUtils.create_numbered_tile_id(2, Color.BLACK, 'a'),
            TileUtils.create_numbered_tile_id(3, Color.BLACK, 'a'),
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should not raise exception - represents [1, 2, 3]
        GameRules.validate_meld_structures([meld])
        assert meld.get_value() == 6  # 1 + 2 + 3
    
    def test_accept_valid_run_with_multiple_jokers(self):
        """Test that [8, joker, joker, 11] is accepted."""
        tiles = [
            TileUtils.create_numbered_tile_id(8, Color.BLACK, 'a'),
            TileUtils.create_joker_tile_id('a'),
            TileUtils.create_joker_tile_id('b'),
            TileUtils.create_numbered_tile_id(11, Color.BLACK, 'a')
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should not raise exception - represents [8, 9, 10, 11]
        GameRules.validate_meld_structures([meld])
        assert meld.get_value() == 38  # 8 + 9 + 10 + 11
    
    def test_reject_run_with_misaligned_numbered_tiles(self):
        """Test that [1, 4, joker] is rejected - gap between 1 and 4 doesn't match positions."""
        tiles = [
            TileUtils.create_numbered_tile_id(1, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(4, Color.RED, 'a'),
            TileUtils.create_joker_tile_id('a'),
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should raise InvalidBoardStateError: 
        # - Numbered tiles at positions 0 and 1 with values 1 and 4
        # - Position gap = 1, number gap = 3 (doesn't match!)
        with pytest.raises(InvalidBoardStateError, match="not consecutive"):
            GameRules.validate_meld_structures([meld])
