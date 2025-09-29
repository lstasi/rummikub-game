"""Integration tests for the updated tile and meld system."""

from rummikub.models import (
    Color, TileUtils, Meld, MeldKind, Pool, GameState, Rack
)


class TestSystemIntegration:
    """Test complete system integration with string-based tiles and deterministic melds."""
    
    def test_complete_game_creation_flow(self):
        """Test creating a game with the new tile system."""
        # Create a complete game
        game = GameState.create_initialized_game(2)
        
        # Verify pool was created correctly
        assert len(game.pool.tile_ids) == 78  # 106 - 28 (14 tiles per player * 2 players)
        
        # Verify all tiles are strings
        for tile_id in game.pool.tile_ids:
            assert isinstance(tile_id, str)
            assert TileUtils.is_joker(tile_id) or TileUtils.is_numbered(tile_id)
        
        # Verify players have tiles
        for player in game.players:
            assert len(player.rack.tile_ids) == 14
            for tile_id in player.rack.tile_ids:
                assert isinstance(tile_id, str)
    
    def test_meld_creation_and_validation_in_game_context(self):
        """Test creating and validating melds in game context."""
        # Create specific tiles for testing
        group_tiles = [
            TileUtils.create_numbered_tile_id(7, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.BLUE, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.BLACK, 'a')
        ]
        
        run_tiles = [
            TileUtils.create_numbered_tile_id(5, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(6, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(7, Color.RED, 'b')  # Different copy
        ]
        
        # Create melds
        group = Meld(kind=MeldKind.GROUP, tiles=group_tiles)
        run = Meld(kind=MeldKind.RUN, tiles=run_tiles)
        
        # Validate and get values
        group.validate()
        run.validate()
        
        assert group.get_value() == 21
        assert run.get_value() == 18
        
        # Check deterministic IDs
        assert group.id == "7ka-7ra-7ba"  # Black-Red-Blue order
        assert run.id == "5ra-6ra-7rb"    # Sequence order
    
    def test_pool_validation_with_string_tiles(self):
        """Test pool validation works with string tile system."""
        pool = Pool.create_full_pool()
        
        # Should validate successfully
        pool.validate_complete_pool()
        
        # Should have correct tile composition
        jokers = [t for t in pool.tile_ids if TileUtils.is_joker(t)]
        numbered = [t for t in pool.tile_ids if TileUtils.is_numbered(t)]
        
        assert len(jokers) == 2
        assert len(numbered) == 104
        assert len(pool.tile_ids) == 106
    
    def test_rack_operations_with_string_tiles(self):
        """Test rack operations work with string tiles."""
        # Create some test tiles
        tiles = [
            TileUtils.create_numbered_tile_id(1, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(2, Color.BLUE, 'a'),
            TileUtils.create_joker_tile_id('a')
        ]
        
        rack = Rack(tile_ids=tiles)
        
        assert len(rack) == 3
        assert not rack.is_empty()
        
        # Test that tiles are accessible
        assert "1ra" in rack.tile_ids
        assert "2ba" in rack.tile_ids
        assert "ja" in rack.tile_ids
    
    def test_meld_id_consistency_across_operations(self):
        """Test that meld IDs remain consistent across game operations."""
        # Create a group that could appear in different contexts
        tiles = ['10ka', '10ra', '10ba']
        
        # Create same meld multiple times
        group1 = Meld(kind=MeldKind.GROUP, tiles=tiles)
        group2 = Meld(kind=MeldKind.GROUP, tiles=tiles.copy())
        group3 = Meld(kind=MeldKind.GROUP, tiles=['10ra', '10ba', '10ka'])  # Different order
        
        # All should have same ID
        expected_id = "10ka-10ra-10ba"
        assert group1.id == expected_id
        assert group2.id == expected_id  
        assert group3.id == expected_id
        
        # Validation and value calculation shouldn't change ID
        group1.validate()
        value1 = group1.get_value()
        
        group2.validate()
        value2 = group2.get_value()
        
        assert group1.id == expected_id
        assert group2.id == expected_id
        assert value1 == value2 == 30
    
    def test_complex_group_with_joker_deterministic_id(self):
        """Test complex group with joker has deterministic ID."""
        # Create group: Red 12, Blue 12, Joker (should become Black or Orange 12)
        tiles = [
            TileUtils.create_numbered_tile_id(12, Color.RED, 'a'),
            TileUtils.create_numbered_tile_id(12, Color.BLUE, 'a'),
            TileUtils.create_joker_tile_id('a')
        ]
        
        # Test different input orders
        group1 = Meld(kind=MeldKind.GROUP, tiles=tiles)
        group2 = Meld(kind=MeldKind.GROUP, tiles=[tiles[2], tiles[0], tiles[1]])  # Joker first
        group3 = Meld(kind=MeldKind.GROUP, tiles=[tiles[1], tiles[2], tiles[0]])  # Mixed order
        
        # All should have same ID (Red-Blue-Joker in that order, as colors sort first)
        expected_id = "12ra-12ba-ja"
        assert group1.id == expected_id
        assert group2.id == expected_id
        assert group3.id == expected_id
        
        # All should validate and have same value
        for group in [group1, group2, group3]:
            group.validate()
            assert group.get_value() == 36  # 12 + 12 + 12
    
    def test_run_with_multiple_jokers(self):
        """Test run with multiple jokers maintains order."""
        # Create run: 8 Red, Joker (9 Red), Joker (10 Red), 11 Red
        tiles = [
            TileUtils.create_numbered_tile_id(8, Color.RED, 'a'),
            TileUtils.create_joker_tile_id('a'),
            TileUtils.create_joker_tile_id('b'),
            TileUtils.create_numbered_tile_id(11, Color.RED, 'a')
        ]
        
        run = Meld(kind=MeldKind.RUN, tiles=tiles)
        
        # ID should preserve exact order (critical for runs)
        expected_id = "8ra-ja-jb-11ra"
        assert run.id == expected_id
        
        # Should validate and calculate correct value
        run.validate()
        assert run.get_value() == 38  # 8 + 9 + 10 + 11