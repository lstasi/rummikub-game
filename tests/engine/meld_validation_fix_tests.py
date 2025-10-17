"""Tests to verify that meld validation is properly enforced when playing tiles.

This test suite specifically verifies the fix for the bug where invalid melds
were being accepted on the board because GameRules.validate_meld_structures()
was only checking size constraints, not the actual meld content validation.
"""

import pytest

from rummikub.models import Color, Meld, MeldKind
from rummikub.models.tiles import TileUtils
from rummikub.models.exceptions import InvalidBoardStateError
from rummikub.engine.game_rules import GameRules


class TestMeldValidationFix:
    """Test that meld validation properly rejects invalid melds."""
    
    def test_reject_group_with_duplicate_colors(self):
        """Test that groups with duplicate colors are rejected."""
        # Create an invalid group - two RED tiles (same color)
        tiles = [
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.RED, 'b'),  # Duplicate color - INVALID
            TileUtils.create_numbered_tile_id(7, Color.BLUE, 'a')
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        # Should raise InvalidBoardStateError
        with pytest.raises(InvalidBoardStateError, match="duplicate colors"):
            GameRules.validate_meld_structures([meld])
    
    def test_reject_group_with_mixed_numbers(self):
        """Test that groups with mixed numbers are rejected."""
        # Create an invalid group - different numbers
        tiles = [
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(8, Color.BLUE, 'a'),  # Different number - INVALID
            TileUtils.create_numbered_tile_id(7, Color.BLACK, 'a')
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        # Should raise InvalidBoardStateError
        with pytest.raises(InvalidBoardStateError, match="same number"):
            GameRules.validate_meld_structures([meld])
    
    def test_reject_run_with_non_consecutive_numbers(self):
        """Test that runs with non-consecutive numbers are rejected."""
        # Create an invalid run - gap in sequence (1, 2, 5)
        tiles = [
            TileUtils.create_numbered_tile_id(1, Color.ORANGE, 'a'),
            TileUtils.create_numbered_tile_id(2, Color.ORANGE, 'a'),
            TileUtils.create_numbered_tile_id(5, Color.ORANGE, 'a')  # Gap in sequence - INVALID
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should raise InvalidBoardStateError
        with pytest.raises(InvalidBoardStateError, match="not consecutive"):
            GameRules.validate_meld_structures([meld])
    
    def test_reject_run_with_mixed_colors(self):
        """Test that runs with mixed colors are rejected."""
        # Create an invalid run - different colors
        tiles = [
            TileUtils.create_numbered_tile_id(1, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(2, Color.BLUE, 'a'),  # Different color - INVALID
            TileUtils.create_numbered_tile_id(3, Color.RED, 'a')
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should raise InvalidBoardStateError
        with pytest.raises(InvalidBoardStateError, match="same color"):
            GameRules.validate_meld_structures([meld])
    
    def test_accept_valid_group(self):
        """Test that valid groups are accepted."""
        # Create a valid group - same number, different colors
        tiles = [
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.BLACK, 'a')
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        # Should not raise any exception
        GameRules.validate_meld_structures([meld])
    
    def test_accept_valid_run(self):
        """Test that valid runs are accepted."""
        # Create a valid run - consecutive numbers, same color
        tiles = [
            TileUtils.create_numbered_tile_id(5, Color.ORANGE, 'a'),
            TileUtils.create_numbered_tile_id(6, Color.ORANGE, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.ORANGE, 'a'),
            TileUtils.create_numbered_tile_id(8, Color.ORANGE, 'a')
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should not raise any exception
        GameRules.validate_meld_structures([meld])
    
    def test_reject_multiple_melds_with_one_invalid(self):
        """Test that validation rejects when one meld in a list is invalid."""
        # Create a valid group
        valid_tiles = [
            TileUtils.create_numbered_tile_id(10, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(10, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(10, Color.BLACK, 'a')
        ]
        valid_meld = Meld(kind=MeldKind.GROUP, tiles=valid_tiles)
        
        # Create an invalid run
        invalid_tiles = [
            TileUtils.create_numbered_tile_id(1, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(2, Color.BLUE, 'a'),  # Different color - INVALID
            TileUtils.create_numbered_tile_id(3, Color.RED, 'a')
        ]
        invalid_meld = Meld(kind=MeldKind.RUN, tiles=invalid_tiles)
        
        # Should raise InvalidBoardStateError due to the invalid run
        with pytest.raises(InvalidBoardStateError, match="same color"):
            GameRules.validate_meld_structures([valid_meld, invalid_meld])
