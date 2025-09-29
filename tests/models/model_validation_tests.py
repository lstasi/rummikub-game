"""Tests for model-integrated validation functionality."""

import pytest

from rummikub.models import (
    Color, TileUtils, Meld, MeldKind,
    GameState, InvalidMeldError, JokerAssignmentError
)


class TestMeldValidation:
    """Test validation integrated into Meld class."""
    
    def test_meld_post_init_validates_empty(self):
        """Test that empty meld raises error in __post_init__."""
        with pytest.raises(InvalidMeldError, match="Meld cannot be empty"):
            Meld(kind=MeldKind.GROUP, tiles=[])
    
    def test_group_post_init_validates_size(self):
        """Test that invalid group sizes raise error in __post_init__."""
        # Too few tiles
        with pytest.raises(InvalidMeldError, match="Group must have 3-4 tiles"):
            Meld(kind=MeldKind.GROUP, tiles=["7ra", "7ba"])
        
        # Too many tiles
        with pytest.raises(InvalidMeldError, match="Group must have 3-4 tiles"):
            Meld(kind=MeldKind.GROUP, tiles=["7ra", "7ba", "7ka", "7oa", "8ra"])
    
    def test_run_post_init_validates_size(self):
        """Test that invalid run sizes raise error in __post_init__."""
        # Too few tiles
        with pytest.raises(InvalidMeldError, match="Run must have at least 3 tiles"):
            Meld(kind=MeldKind.RUN, tiles=["5ra", "6ra"])
    
    def test_valid_group_creation_and_validation(self):
        """Test creating and validating a valid group."""
        tiles = [
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.ORANGE, 'a')
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        # Should not raise an exception
        meld.validate()
    
    def test_invalid_group_duplicate_colors(self):
        """Test that group with duplicate colors is invalid."""
        tiles = [
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.RED, 'b'),  # Duplicate color
            TileUtils.create_numbered_tile_id(7, Color.ORANGE, 'a')
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        with pytest.raises(InvalidMeldError, match="Group cannot have duplicate colors"):
            meld.validate()
    
    def test_invalid_group_mixed_numbers(self):
        """Test that group with different numbers is invalid."""
        tiles = [
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(8, Color.BLUE, 'a'),  # Different number
            TileUtils.create_numbered_tile_id(7, Color.ORANGE, 'a')
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        with pytest.raises(InvalidMeldError, match="All numbered tiles in group must have same number"):
            meld.validate()
    
    def test_valid_run_creation_and_validation(self):
        """Test creating and validating a valid run."""
        tiles = [
            TileUtils.create_numbered_tile_id(5, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(6, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a')
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should not raise an exception
        meld.validate()
    
    def test_invalid_run_mixed_colors(self):
        """Test that run with mixed colors is invalid."""
        tiles = [
            TileUtils.create_numbered_tile_id(5, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(6, Color.BLUE, 'a'),  # Different color
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a')
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        with pytest.raises(InvalidMeldError, match="same color"):
            meld.validate()
    
    def test_invalid_run_non_consecutive(self):
        """Test that run with non-consecutive numbers is invalid."""
        tiles = [
            TileUtils.create_numbered_tile_id(5, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),  # Gap at 6
            TileUtils.create_numbered_tile_id(8, Color.RED, 'a')
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        with pytest.raises(InvalidMeldError, match="consecutive"):
            meld.validate()
    
    def test_valid_group_with_jokers(self):
        """Test valid group containing jokers."""
        tiles = [
            TileUtils.create_numbered_tile_id(9, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(9, Color.BLUE, 'a'),
            TileUtils.create_joker_tile_id('a')  # Should become 9 of remaining color
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        # Should not raise an exception
        meld.validate()
    
    def test_valid_run_with_jokers(self):
        """Test valid run containing jokers."""
        tiles = [
            TileUtils.create_numbered_tile_id(5, Color.RED, 'a'),
            TileUtils.create_joker_tile_id('a'),  # Should become 6 red
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a')
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should not raise an exception
        meld.validate()
    
    def test_invalid_run_out_of_bounds(self):
        """Test that run going beyond 1-13 range is invalid."""
        tiles = [
            TileUtils.create_numbered_tile_id(12, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(13, Color.RED, 'a'),
            TileUtils.create_joker_tile_id('a'),  # Would need to be 14, which is invalid
            TileUtils.create_joker_tile_id('b')   # Would need to be 15, which is invalid
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        with pytest.raises(InvalidMeldError, match="valid range"):
            meld.validate()
    
    def test_group_with_only_jokers_invalid(self):
        """Test that group with only jokers is invalid."""
        tiles = [
            TileUtils.create_joker_tile_id('a'),
            TileUtils.create_joker_tile_id('b'),
            "ja"  # Use string ID directly since we need 3 unique jokers
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        with pytest.raises(JokerAssignmentError, match="Cannot determine group number"):
            meld.validate()
    
    def test_run_with_only_jokers_invalid(self):
        """Test that run with only jokers is invalid."""
        tiles = [
            TileUtils.create_joker_tile_id('a'),
            TileUtils.create_joker_tile_id('b'),
            "ja"  # Use string ID directly since we need 3 unique jokers
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        with pytest.raises(JokerAssignmentError, match="Cannot determine run color"):
            meld.validate()


class TestMeldValueCalculation:
    """Test value calculation integrated into Meld class."""
    
    def test_group_value_calculation(self):
        """Test value calculation for a group."""
        tiles = [
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.ORANGE, 'a')
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        assert meld.get_value() == 21  # 7 + 7 + 7
    
    def test_run_value_calculation(self):
        """Test value calculation for a run."""
        tiles = [
            TileUtils.create_numbered_tile_id(5, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(6, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a')
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        assert meld.get_value() == 18  # 5 + 6 + 7
    
    def test_group_value_with_jokers(self):
        """Test value calculation for group with jokers."""
        tiles = [
            TileUtils.create_numbered_tile_id(10, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(10, Color.BLUE, 'a'),
            TileUtils.create_joker_tile_id('a')  # Should count as 10
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        assert meld.get_value() == 30  # 10 + 10 + 10
    
    def test_run_value_with_jokers(self):
        """Test value calculation for run with jokers."""
        tiles = [
            TileUtils.create_numbered_tile_id(8, Color.BLUE, 'a'),
            TileUtils.create_joker_tile_id('a'),  # Should count as 9
            TileUtils.create_numbered_tile_id(10, Color.BLUE, 'a')
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        assert meld.get_value() == 27  # 8 + 9 + 10


class TestGameStateValidation:
    """Test validation integrated into GameState class."""
    
    def test_calculate_initial_meld_total_single_meld(self):
        """Test initial meld total calculation with single meld."""
        tiles = [
            TileUtils.create_numbered_tile_id(10, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(10, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(10, Color.ORANGE, 'a')
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        game_state = GameState.create_new_game()
        total = game_state.calculate_initial_meld_total([meld])
        
        assert total == 30  # 10 + 10 + 10
    
    def test_calculate_initial_meld_total_multiple_melds(self):
        """Test initial meld total calculation with multiple melds."""
        # Group: 7-7-7
        group_tiles = [
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.ORANGE, 'a')
        ]
        group_meld = Meld(kind=MeldKind.GROUP, tiles=group_tiles)
        
        # Run: 5-6-7 black
        run_tiles = [
            TileUtils.create_numbered_tile_id(5, Color.BLACK, 'a'),
            TileUtils.create_numbered_tile_id(6, Color.BLACK, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.BLACK, 'a')
        ]
        run_meld = Meld(kind=MeldKind.RUN, tiles=run_tiles)
        
        game_state = GameState.create_new_game()
        total = game_state.calculate_initial_meld_total([group_meld, run_meld])
        
        assert total == 39  # (7+7+7) + (5+6+7) = 21 + 18
    
    def test_calculate_initial_meld_total_empty(self):
        """Test initial meld total with no melds."""
        game_state = GameState.create_new_game()
        total = game_state.calculate_initial_meld_total([])
        
        assert total == 0
    
    # Tile ownership validation tests removed - they tested old GameState structure
    
    # GameState tile ownership tests removed - they tested old API structure


class TestEdgeCasesAndBoundaries:
    """Test edge cases and boundary conditions."""
    
    def test_minimum_valid_group(self):
        """Test minimum valid group (3 tiles)."""
        tiles = [
            TileUtils.create_numbered_tile_id(1, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(1, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(1, Color.ORANGE, 'a')
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        # Should be valid
        meld.validate()
        assert meld.get_value() == 3
    
    def test_maximum_valid_group(self):
        """Test maximum valid group (4 tiles)."""
        tiles = [
            TileUtils.create_numbered_tile_id(13, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(13, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(13, Color.ORANGE, 'a'),
            TileUtils.create_numbered_tile_id(13, Color.BLACK, 'a')
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        # Should be valid
        meld.validate()
        assert meld.get_value() == 52  # 13 * 4
    
    def test_minimum_valid_run(self):
        """Test minimum valid run (3 tiles)."""
        tiles = [
            TileUtils.create_numbered_tile_id(1, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(2, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(3, Color.RED, 'a')
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should be valid
        meld.validate()
        assert meld.get_value() == 6  # 1 + 2 + 3
    
    def test_maximum_valid_run(self):
        """Test maximum valid run (all numbers 1-13)."""
        tiles = [
            TileUtils.create_numbered_tile_id(i, Color.BLACK, 'a')
            for i in range(1, 14)
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should not raise an exception
        meld.validate()
        assert meld.get_value() == 91  # sum(1 to 13)
    
    def test_run_at_boundaries(self):
        """Test runs at number boundaries."""
        # Run starting at 1
        # Test run at start (1-2-3)
        tiles_start = [
            TileUtils.create_numbered_tile_id(1, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(2, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(3, Color.RED, 'a')
        ]
        
        meld_start = Meld(kind=MeldKind.RUN, tiles=tiles_start)
        
        # Should be valid
        meld_start.validate()
        
        # Run ending at 13
        # Test run at end (11-12-13)
        tiles_end = [
            TileUtils.create_numbered_tile_id(11, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(12, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(13, Color.RED, 'a')
        ]
        
        meld_end = Meld(kind=MeldKind.RUN, tiles=tiles_end)
        
        # Should be valid
        meld_end.validate()