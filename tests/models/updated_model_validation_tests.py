"""Updated model validation tests using TileUtils and new string-based tile system."""

import pytest

from rummikub.models import (
    Color, TileUtils, Meld, MeldKind, GameState, Pool, InvalidMeldError, JokerAssignmentError
)


class TestUpdatedMeldValidation:
    """Test validation with the updated tile system."""
    
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
        
        # Test deterministic ID generation
        expected_id = "7ra-7ba-7oa"  # Red-Blue-Orange order
        assert meld.id == expected_id
        
        # Test value calculation
        assert meld.get_value() == 21  # 7 + 7 + 7
    
    def test_invalid_group_duplicate_colors(self):
        """Test that group with duplicate colors is invalid."""
        tiles = [
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.RED, 'b'),  # Duplicate color
            TileUtils.create_numbered_tile_id(7, Color.ORANGE, 'a')
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        with pytest.raises(InvalidMeldError, match="duplicate colors"):
            meld.validate()
    
    def test_invalid_group_mixed_numbers(self):
        """Test that group with different numbers is invalid."""
        tiles = [
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(8, Color.BLUE, 'a'),  # Different number
            TileUtils.create_numbered_tile_id(7, Color.ORANGE, 'a')
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        with pytest.raises(InvalidMeldError, match="same number"):
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
        
        # Test ID preserves sequence order
        expected_id = "5ra-6ra-7ra"
        assert meld.id == expected_id
        
        # Test value calculation
        assert meld.get_value() == 18  # 5 + 6 + 7
    
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
        """Test valid group with jokers."""
        tiles = [
            TileUtils.create_numbered_tile_id(9, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(9, Color.BLUE, 'a'),
            TileUtils.create_joker_tile_id('a')  # Should become 9 of remaining color
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        # Should not raise an exception
        meld.validate()
        
        # Test value calculation (joker counts as 9)
        assert meld.get_value() == 27  # 9 + 9 + 9
        
        # Test deterministic ID with joker last
        expected_id = "9ra-9ba-ja"  # Red-Blue-Joker order
        assert meld.id == expected_id
    
    def test_valid_run_with_jokers(self):
        """Test valid run with jokers."""
        tiles = [
            TileUtils.create_numbered_tile_id(5, Color.RED, 'a'),
            TileUtils.create_joker_tile_id('a'),  # Should become 6 red
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a')
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should not raise an exception
        meld.validate()
        
        # Test value calculation (joker counts as 6)
        assert meld.get_value() == 18  # 5 + 6 + 7
        
        # Test ID preserves order with joker in position
        expected_id = "5ra-ja-7ra"
        assert meld.id == expected_id
    
    def test_invalid_run_out_of_bounds(self):
        """Test that run going out of bounds is invalid."""
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
            TileUtils.create_joker_tile_id('a')  # Duplicate ID, but test handles it
        ]
        
        # Create unique joker IDs for testing
        tiles = ["ja", "jb", "ja"]  # Using string IDs directly
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        with pytest.raises(JokerAssignmentError, match="Cannot determine group number"):
            meld.validate()
    
    def test_run_with_only_jokers_invalid(self):
        """Test that run with only jokers is invalid."""
        tiles = ["ja", "jb", "ja"]  # All jokers
        
        meld = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        with pytest.raises(JokerAssignmentError, match="Cannot determine run color"):
            meld.validate()
    
    def test_deterministic_id_consistency(self):
        """Test that meld IDs are consistent across operations."""
        # Same tiles in different order should produce same ID for groups
        tiles1 = ['8ka', '8ra', '8ba', '8oa']  # Black, Red, Blue, Orange
        tiles2 = ['8oa', '8ba', '8ra', '8ka']  # Orange, Blue, Red, Black (different order)
        
        group1 = Meld(kind=MeldKind.GROUP, tiles=tiles1)
        group2 = Meld(kind=MeldKind.GROUP, tiles=tiles2)
        
        # Both should have same ID (sorted by color)
        expected_id = "8ka-8ra-8ba-8oa"  # Black-Red-Blue-Orange order
        assert group1.id == expected_id
        assert group2.id == expected_id
        
        # Both should validate and have same value
        group1.validate()
        group2.validate()
        assert group1.get_value() == group2.get_value() == 32  # 8 * 4
    
    def test_complex_group_all_colors(self):
        """Test group with all 4 colors."""
        tiles = [
            TileUtils.create_numbered_tile_id(11, Color.BLACK, 'a'),
            TileUtils.create_numbered_tile_id(11, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(11, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(11, Color.ORANGE, 'a')
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        # Should validate successfully
        meld.validate()
        
        # Should have correct value
        assert meld.get_value() == 44  # 11 * 4
        
        # Should have deterministic ID in color order
        expected_id = "11ka-11ra-11ba-11oa"
        assert meld.id == expected_id


class TestUpdatedGameStateValidation:
    """Test game state validation with new tile system."""
    
    def test_pool_creation_and_validation(self):
        """Test pool creation with new tile system."""
        pool = Pool.create_full_pool()
        
        # Should validate successfully
        pool.validate_complete_pool()
        
        # Should have correct composition
        assert len(pool.tile_ids) == 106
        
        jokers = [t for t in pool.tile_ids if TileUtils.is_joker(t)]
        numbered = [t for t in pool.tile_ids if TileUtils.is_numbered(t)]
        
        assert len(jokers) == 2
        assert len(numbered) == 104
    
    def test_game_initialization_with_tile_dealing(self):
        """Test game initialization deals tiles correctly."""
        game = GameState.create_initialized_game(2)
        
        # Should have 2 players with 14 tiles each
        assert len(game.players) == 2
        for player in game.players:
            assert len(player.rack.tile_ids) == 14
        
        # Pool should have remaining tiles
        expected_pool_size = 106 - (2 * 14)  # 106 - 28 = 78
        assert len(game.pool.tile_ids) == expected_pool_size
        
        # All tiles should be valid strings
        all_tiles = []
        for player in game.players:
            all_tiles.extend(player.rack.tile_ids)
        all_tiles.extend(game.pool.tile_ids)
        
        assert len(all_tiles) == 106
        for tile_id in all_tiles:
            assert isinstance(tile_id, str)
            assert TileUtils.is_joker(tile_id) or TileUtils.is_numbered(tile_id)
    
    def test_calculate_initial_meld_total(self):
        """Test initial meld total calculation with new system."""
        # Create melds that total >= 30
        meld1 = Meld(kind=MeldKind.GROUP, tiles=[
            TileUtils.create_numbered_tile_id(10, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(10, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(10, Color.BLACK, 'a')
        ])
        
        meld2 = Meld(kind=MeldKind.RUN, tiles=[
            TileUtils.create_numbered_tile_id(1, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(2, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(3, Color.RED, 'a')
        ])
        
        game = GameState.create_new_game()
        total = game.calculate_initial_meld_total([meld1, meld2])
        
        # Should be 30 + 6 = 36
        assert total == 36
        
        # Test empty melds
        assert game.calculate_initial_meld_total([]) == 0