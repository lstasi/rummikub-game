"""Tests for deterministic meld ID generation and updated meld system."""

import pytest
from rummikub.models import Color, TileUtils, Meld, MeldKind, InvalidMeldError


class TestDeterministicMeldIds:
    """Test deterministic meld ID generation system."""
    
    def test_group_deterministic_id_same_tiles_different_order(self):
        """Test that groups with same tiles in different order get same ID."""
        tiles1 = ['7ra', '7ba', '7ka']  # Red, Blue, Black
        tiles2 = ['7ka', '7ra', '7ba']  # Black, Red, Blue (different order)
        tiles3 = ['7ba', '7ka', '7ra']  # Blue, Black, Red (different order)
        
        group1 = Meld(kind=MeldKind.GROUP, tiles=tiles1)
        group2 = Meld(kind=MeldKind.GROUP, tiles=tiles2)
        group3 = Meld(kind=MeldKind.GROUP, tiles=tiles3)
        
        # All should have same ID (sorted by color: Black, Red, Blue)
        expected_id = "7ka-7ra-7ba"
        assert group1.id == expected_id
        assert group2.id == expected_id
        assert group3.id == expected_id
    
    def test_group_color_sorting_order(self):
        """Test that groups sort colors in Black-Red-Blue-Orange order."""
        # Test all 4 colors
        all_colors = [
            TileUtils.create_numbered_tile_id(8, Color.ORANGE, 'a'),  # 8oa
            TileUtils.create_numbered_tile_id(8, Color.BLACK, 'a'),   # 8ka  
            TileUtils.create_numbered_tile_id(8, Color.BLUE, 'a'),    # 8ba
            TileUtils.create_numbered_tile_id(8, Color.RED, 'a')      # 8ra
        ]
        
        # Create group with tiles in "wrong" order
        group = Meld(kind=MeldKind.GROUP, tiles=all_colors)
        
        # Should be sorted: Black, Red, Blue, Orange
        expected_id = "8ka-8ra-8ba-8oa"
        assert group.id == expected_id
    
    def test_group_with_jokers_deterministic_id(self):
        """Test that groups with jokers generate deterministic IDs."""
        # Jokers should go last in the sorted order
        tiles1 = ['7ra', '7ba', 'ja']  # Red, Blue, Joker
        tiles2 = ['ja', '7ra', '7ba']  # Joker, Red, Blue (different order)
        tiles3 = ['7ba', 'ja', '7ra']  # Blue, Joker, Red (different order)
        
        group1 = Meld(kind=MeldKind.GROUP, tiles=tiles1)
        group2 = Meld(kind=MeldKind.GROUP, tiles=tiles2)
        group3 = Meld(kind=MeldKind.GROUP, tiles=tiles3)
        
        # All should have same ID (colors sorted, joker last)
        expected_id = "7ra-7ba-ja"  # Red, Blue, Joker
        assert group1.id == expected_id
        assert group2.id == expected_id
        assert group3.id == expected_id
    
    def test_run_deterministic_id_preserves_order(self):
        """Test that runs preserve their sequence order in ID."""
        tiles = ['5ra', '6ra', '7ra']
        run1 = Meld(kind=MeldKind.RUN, tiles=tiles)
        run2 = Meld(kind=MeldKind.RUN, tiles=tiles.copy())
        
        expected_id = "5ra-6ra-7ra"
        assert run1.id == expected_id
        assert run2.id == expected_id
    
    def test_run_with_joker_preserves_order(self):
        """Test that runs with jokers maintain position in ID."""
        tiles = ['5ra', 'ja', '7ra']  # 5 Red, Joker (6 Red), 7 Red
        run = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        expected_id = "5ra-ja-7ra"
        assert run.id == expected_id
    
    def test_different_tiles_different_ids(self):
        """Test that different tile compositions get different IDs."""
        group1 = Meld(kind=MeldKind.GROUP, tiles=['7ra', '7ba', '7ka'])
        group2 = Meld(kind=MeldKind.GROUP, tiles=['8ra', '8ba', '8ka'])
        
        assert group1.id != group2.id
        assert group1.id == "7ka-7ra-7ba"
        assert group2.id == "8ka-8ra-8ba"
    
    def test_group_vs_run_same_tiles_different_ids(self):
        """Test that group and run with same tiles get different IDs due to sorting."""
        tiles = ['7ra', '7ba', '7ka']
        
        group = Meld(kind=MeldKind.GROUP, tiles=tiles)
        # This would be an invalid run (same number), but testing ID generation only
        
        # Group should sort by color
        assert group.id == "7ka-7ra-7ba"  # Black-Red-Blue order


class TestMeldValidationWithNewSystem:
    """Test that meld validation still works with new tile system."""
    
    def test_valid_group_validation(self):
        """Test validation of valid group."""
        tiles = [
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.BLACK, 'a')
        ]
        
        group = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        # Should not raise exception
        group.validate()
        
        # Should calculate correct value
        assert group.get_value() == 21  # 7 + 7 + 7
    
    def test_valid_run_validation(self):
        """Test validation of valid run."""
        tiles = [
            TileUtils.create_numbered_tile_id(5, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(6, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a')
        ]
        
        run = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should not raise exception
        run.validate()
        
        # Should calculate correct value
        assert run.get_value() == 18  # 5 + 6 + 7
    
    def test_group_with_joker_validation(self):
        """Test validation of group with joker."""
        tiles = [
            TileUtils.create_numbered_tile_id(9, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(9, Color.BLUE, 'a'),  
            TileUtils.create_joker_tile_id('a')  # Should become 9 of remaining color
        ]
        
        group = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        # Should not raise exception
        group.validate()
        
        # Should calculate correct value (joker counts as 9)
        assert group.get_value() == 27  # 9 + 9 + 9
    
    def test_run_with_joker_validation(self):
        """Test validation of run with joker."""
        tiles = [
            TileUtils.create_numbered_tile_id(5, Color.RED, 'a'),
            TileUtils.create_joker_tile_id('a'),  # Should become 6 Red
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a')
        ]
        
        run = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # Should not raise exception
        run.validate()
        
        # Should calculate correct value (joker counts as 6)
        assert run.get_value() == 18  # 5 + 6 + 7
    
    def test_invalid_group_duplicate_colors(self):
        """Test that group with duplicate colors is invalid."""
        tiles = [
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.RED, 'b'),  # Duplicate color
            TileUtils.create_numbered_tile_id(7, Color.BLUE, 'a')
        ]
        
        group = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        with pytest.raises(InvalidMeldError, match="duplicate colors"):
            group.validate()
    
    def test_invalid_run_mixed_colors(self):
        """Test that run with mixed colors is invalid."""
        tiles = [
            TileUtils.create_numbered_tile_id(5, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(6, Color.BLUE, 'a'),  # Different color
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a')
        ]
        
        run = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        with pytest.raises(InvalidMeldError, match="same color"):
            run.validate()
    
    def test_invalid_run_non_consecutive(self):
        """Test that run with non-consecutive numbers is invalid."""
        tiles = [
            TileUtils.create_numbered_tile_id(5, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),  # Gap at 6
            TileUtils.create_numbered_tile_id(8, Color.RED, 'a')
        ]
        
        run = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        with pytest.raises(InvalidMeldError, match="consecutive"):
            run.validate()


class TestMeldIdConsistency:
    """Test that meld IDs remain consistent across operations."""
    
    def test_id_unchanged_after_validation(self):
        """Test that meld ID doesn't change after validation."""
        tiles = ['7ra', '7ba', '7ka']
        group = Meld(kind=MeldKind.GROUP, tiles=tiles)
        
        original_id = group.id
        group.validate()
        
        assert group.id == original_id
    
    def test_id_unchanged_after_get_value(self):
        """Test that meld ID doesn't change after getting value."""
        tiles = ['5ra', '6ra', '7ra']
        run = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        original_id = run.id
        value = run.get_value()
        
        assert run.id == original_id
        assert value == 18
    
    def test_equivalent_melds_have_same_id(self):
        """Test that functionally equivalent melds have same ID."""
        # Create same group in different ways
        tiles1 = ['10ka', '10ra', '10ba', '10oa']  # All 4 colors of 10
        tiles2 = ['10oa', '10ba', '10ra', '10ka']  # Same tiles, different order
        
        group1 = Meld(kind=MeldKind.GROUP, tiles=tiles1)
        group2 = Meld(kind=MeldKind.GROUP, tiles=tiles2)
        
        assert group1.id == group2.id
        
        # Both should validate and have same value
        group1.validate()
        group2.validate()
        
        assert group1.get_value() == group2.get_value() == 40  # 10 * 4