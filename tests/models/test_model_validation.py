"""Tests for model-integrated validation functionality."""

import pytest
from uuid import uuid4

from rummikub.models import (
    Color, NumberedTile, JokerTile, TileInstance, Meld, MeldKind,
    GameState, Player, Rack, Pool, Board,
    InvalidMeldError, JokerAssignmentError, GameStateError
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
            Meld(kind=MeldKind.GROUP, tiles=[uuid4(), uuid4()])
        
        # Too many tiles
        with pytest.raises(InvalidMeldError, match="Group must have 3-4 tiles"):
            Meld(kind=MeldKind.GROUP, tiles=[uuid4() for _ in range(5)])
    
    def test_run_post_init_validates_size(self):
        """Test that invalid run sizes raise error in __post_init__."""
        # Too few tiles
        with pytest.raises(InvalidMeldError, match="Run must have at least 3 tiles"):
            Meld(kind=MeldKind.RUN, tiles=[uuid4(), uuid4()])
    
    def test_valid_group_creation_and_validation(self):
        """Test creating and validating a valid group."""
        tiles = [
            TileInstance(kind=NumberedTile(number=7, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=7, color=Color.BLUE)),
            TileInstance(kind=NumberedTile(number=7, color=Color.ORANGE))
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        # Should not raise an exception
        meld.validate_with_tiles(tile_instances)
    
    def test_invalid_group_duplicate_colors(self):
        """Test that group with duplicate colors is invalid."""
        tiles = [
            TileInstance(kind=NumberedTile(number=7, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=7, color=Color.RED)),  # Duplicate
            TileInstance(kind=NumberedTile(number=7, color=Color.ORANGE))
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        with pytest.raises(InvalidMeldError, match="Group cannot have duplicate colors"):
            meld.validate_with_tiles(tile_instances)
    
    def test_invalid_group_mixed_numbers(self):
        """Test that group with different numbers is invalid."""
        tiles = [
            TileInstance(kind=NumberedTile(number=7, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=8, color=Color.BLUE)),  # Different number
            TileInstance(kind=NumberedTile(number=7, color=Color.ORANGE))
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        with pytest.raises(InvalidMeldError, match="All numbered tiles in group must have same number"):
            meld.validate_with_tiles(tile_instances)
    
    def test_valid_run_creation_and_validation(self):
        """Test creating and validating a valid run."""
        tiles = [
            TileInstance(kind=NumberedTile(number=5, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=6, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=7, color=Color.RED))
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        # Should not raise an exception
        meld.validate_with_tiles(tile_instances)
    
    def test_invalid_run_mixed_colors(self):
        """Test that run with mixed colors is invalid."""
        tiles = [
            TileInstance(kind=NumberedTile(number=5, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=6, color=Color.BLUE)),  # Different color
            TileInstance(kind=NumberedTile(number=7, color=Color.RED))
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        with pytest.raises(InvalidMeldError, match="Run tiles must all have the same color"):
            meld.validate_with_tiles(tile_instances)
    
    def test_invalid_run_non_consecutive(self):
        """Test that run with non-consecutive numbers is invalid."""
        tiles = [
            TileInstance(kind=NumberedTile(number=5, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=7, color=Color.RED)),  # Gap at 6
            TileInstance(kind=NumberedTile(number=8, color=Color.RED))
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        with pytest.raises(InvalidMeldError, match="Run numbers are not consecutive"):
            meld.validate_with_tiles(tile_instances)
    
    def test_valid_group_with_jokers(self):
        """Test valid group containing jokers."""
        tiles = [
            TileInstance(kind=NumberedTile(number=9, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=9, color=Color.BLUE)),
            TileInstance(kind=JokerTile())  # Should become 9 of remaining color
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        # Should not raise an exception
        meld.validate_with_tiles(tile_instances)
    
    def test_valid_run_with_jokers(self):
        """Test valid run containing jokers."""
        tiles = [
            TileInstance(kind=NumberedTile(number=5, color=Color.RED)),
            TileInstance(kind=JokerTile()),  # Should become 6 red
            TileInstance(kind=NumberedTile(number=7, color=Color.RED))
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        # Should not raise an exception
        meld.validate_with_tiles(tile_instances)
    
    def test_invalid_run_out_of_bounds(self):
        """Test that run going beyond 1-13 range is invalid."""
        tiles = [
            TileInstance(kind=NumberedTile(number=12, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=13, color=Color.RED)),
            TileInstance(kind=JokerTile()),  # Would need to be 14, which is invalid
            TileInstance(kind=JokerTile())   # Would need to be 15, which is invalid
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        with pytest.raises(InvalidMeldError, match="Run sequence goes outside valid range"):
            meld.validate_with_tiles(tile_instances)
    
    def test_group_with_only_jokers_invalid(self):
        """Test that group with only jokers is invalid."""
        tiles = [
            TileInstance(kind=JokerTile()),
            TileInstance(kind=JokerTile()),
            TileInstance(kind=JokerTile())
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        with pytest.raises(JokerAssignmentError, match="Cannot determine group number with only jokers"):
            meld.validate_with_tiles(tile_instances)
    
    def test_run_with_only_jokers_invalid(self):
        """Test that run with only jokers is invalid."""
        tiles = [
            TileInstance(kind=JokerTile()),
            TileInstance(kind=JokerTile()),
            TileInstance(kind=JokerTile())
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        with pytest.raises(JokerAssignmentError, match="Cannot determine run color with only jokers"):
            meld.validate_with_tiles(tile_instances)


class TestMeldValueCalculation:
    """Test value calculation integrated into Meld class."""
    
    def test_group_value_calculation(self):
        """Test value calculation for a group."""
        tiles = [
            TileInstance(kind=NumberedTile(number=7, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=7, color=Color.BLUE)),
            TileInstance(kind=NumberedTile(number=7, color=Color.ORANGE))
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        assert meld.get_value(tile_instances) == 21  # 7 + 7 + 7
    
    def test_run_value_calculation(self):
        """Test value calculation for a run."""
        tiles = [
            TileInstance(kind=NumberedTile(number=5, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=6, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=7, color=Color.RED))
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        assert meld.get_value(tile_instances) == 18  # 5 + 6 + 7
    
    def test_group_value_with_jokers(self):
        """Test value calculation for group with jokers."""
        tiles = [
            TileInstance(kind=NumberedTile(number=10, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=10, color=Color.BLUE)),
            TileInstance(kind=JokerTile())  # Should count as 10
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        assert meld.get_value(tile_instances) == 30  # 10 + 10 + 10
    
    def test_run_value_with_jokers(self):
        """Test value calculation for run with jokers."""
        tiles = [
            TileInstance(kind=NumberedTile(number=8, color=Color.BLUE)),
            TileInstance(kind=JokerTile()),  # Should count as 9
            TileInstance(kind=NumberedTile(number=10, color=Color.BLUE))
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        assert meld.get_value(tile_instances) == 27  # 8 + 9 + 10


class TestGameStateValidation:
    """Test validation integrated into GameState class."""
    
    def test_calculate_initial_meld_total_single_meld(self):
        """Test initial meld total calculation with single meld."""
        tiles = [
            TileInstance(kind=NumberedTile(number=10, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=10, color=Color.BLUE)),
            TileInstance(kind=NumberedTile(number=10, color=Color.ORANGE))
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        game_state = GameState(game_id=uuid4())
        total = game_state.calculate_initial_meld_total([meld], tile_instances)
        
        assert total == 30  # 10 + 10 + 10
    
    def test_calculate_initial_meld_total_multiple_melds(self):
        """Test initial meld total calculation with multiple melds."""
        # Group: 7-7-7
        group_tiles = [
            TileInstance(kind=NumberedTile(number=7, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=7, color=Color.BLUE)),
            TileInstance(kind=NumberedTile(number=7, color=Color.ORANGE))
        ]
        group_meld = Meld(kind=MeldKind.GROUP, tiles=[t.id for t in group_tiles])
        
        # Run: 5-6-7 black
        run_tiles = [
            TileInstance(kind=NumberedTile(number=5, color=Color.BLACK)),
            TileInstance(kind=NumberedTile(number=6, color=Color.BLACK)),
            TileInstance(kind=NumberedTile(number=7, color=Color.BLACK))
        ]
        run_meld = Meld(kind=MeldKind.RUN, tiles=[t.id for t in run_tiles])
        
        all_tiles = group_tiles + run_tiles
        tile_instances = {str(t.id): t for t in all_tiles}
        
        game_state = GameState(game_id=uuid4())
        total = game_state.calculate_initial_meld_total([group_meld, run_meld], tile_instances)
        
        assert total == 39  # (7+7+7) + (5+6+7) = 21 + 18
    
    def test_calculate_initial_meld_total_empty(self):
        """Test initial meld total with no melds."""
        game_state = GameState(game_id=uuid4())
        total = game_state.calculate_initial_meld_total([], {})
        
        assert total == 0
    
    def test_validate_tile_ownership_valid(self):
        """Test valid tile ownership validation."""
        tiles = [TileInstance(kind=NumberedTile(number=i, color=Color.RED)) for i in range(1, 6)]
        tile_instances = {str(t.id): t for t in tiles}
        
        # Distribute tiles across game components
        player = Player(name="Test Player", id=uuid4())
        player.rack.tile_ids = [tiles[0].id, tiles[1].id]
        
        pool = Pool(tile_ids=[tiles[2].id, tiles[3].id, tiles[4].id])
        
        board = Board(melds=[])  # Empty board for simplicity
        
        game_state = GameState(
            game_id=uuid4(),
            players=[player],
            pool=pool,
            board=board
        )
        
        # Should not raise an exception
        assert game_state.validate_tile_ownership(tile_instances) is True
    
    def test_validate_tile_ownership_duplicate_in_racks(self):
        """Test tile ownership validation with duplicate tiles."""
        tile = TileInstance(kind=NumberedTile(number=7, color=Color.RED))
        tile_instances = {str(tile.id): tile}
        
        # Same tile in two different player racks
        player1 = Player(name="Player 1", id=uuid4())
        player1.rack.tile_ids = [tile.id]
        
        player2 = Player(name="Player 2", id=uuid4())
        player2.rack.tile_ids = [tile.id]  # Duplicate!
        
        game_state = GameState(
            game_id=uuid4(),
            players=[player1, player2]
        )
        
        with pytest.raises(GameStateError, match="Duplicate tile .* found in player racks"):
            game_state.validate_tile_ownership(tile_instances)
    
    def test_validate_tile_ownership_missing_tiles(self):
        """Test tile ownership validation with missing tiles."""
        tiles = [TileInstance(kind=NumberedTile(number=i, color=Color.RED)) for i in range(1, 4)]
        tile_instances = {str(t.id): t for t in tiles}
        
        # Only include 2 of 3 tiles in game state
        player = Player(name="Test Player", id=uuid4())
        player.rack.tile_ids = [tiles[0].id, tiles[1].id]  # Missing tiles[2]
        
        game_state = GameState(
            game_id=uuid4(),
            players=[player]
        )
        
        with pytest.raises(GameStateError, match="Tiles missing from game state"):
            game_state.validate_tile_ownership(tile_instances)


class TestEdgeCasesAndBoundaries:
    """Test edge cases and boundary conditions."""
    
    def test_minimum_valid_group(self):
        """Test minimum valid group (3 tiles)."""
        tiles = [
            TileInstance(kind=NumberedTile(number=1, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=1, color=Color.BLUE)),
            TileInstance(kind=NumberedTile(number=1, color=Color.ORANGE))
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        # Should not raise an exception
        meld.validate_with_tiles(tile_instances)
        assert meld.get_value(tile_instances) == 3
    
    def test_maximum_valid_group(self):
        """Test maximum valid group (4 tiles)."""
        tiles = [
            TileInstance(kind=NumberedTile(number=13, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=13, color=Color.BLUE)),
            TileInstance(kind=NumberedTile(number=13, color=Color.ORANGE)),
            TileInstance(kind=NumberedTile(number=13, color=Color.BLACK))
        ]
        
        meld = Meld(kind=MeldKind.GROUP, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        # Should not raise an exception
        meld.validate_with_tiles(tile_instances)
        assert meld.get_value(tile_instances) == 52  # 13 * 4
    
    def test_minimum_valid_run(self):
        """Test minimum valid run (3 tiles)."""
        tiles = [
            TileInstance(kind=NumberedTile(number=1, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=2, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=3, color=Color.RED))
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        # Should not raise an exception
        meld.validate_with_tiles(tile_instances)
        assert meld.get_value(tile_instances) == 6  # 1 + 2 + 3
    
    def test_maximum_valid_run(self):
        """Test maximum valid run (all numbers 1-13)."""
        tiles = [
            TileInstance(kind=NumberedTile(number=i, color=Color.BLACK))
            for i in range(1, 14)
        ]
        
        meld = Meld(kind=MeldKind.RUN, tiles=[t.id for t in tiles])
        tile_instances = {str(t.id): t for t in tiles}
        
        # Should not raise an exception
        meld.validate_with_tiles(tile_instances)
        assert meld.get_value(tile_instances) == 91  # sum(1 to 13)
    
    def test_run_at_boundaries(self):
        """Test runs at number boundaries."""
        # Run starting at 1
        tiles_start = [
            TileInstance(kind=NumberedTile(number=1, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=2, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=3, color=Color.RED))
        ]
        
        meld_start = Meld(kind=MeldKind.RUN, tiles=[t.id for t in tiles_start])
        tile_instances_start = {str(t.id): t for t in tiles_start}
        
        # Should not raise an exception
        meld_start.validate_with_tiles(tile_instances_start)
        
        # Run ending at 13
        tiles_end = [
            TileInstance(kind=NumberedTile(number=11, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=12, color=Color.RED)),
            TileInstance(kind=NumberedTile(number=13, color=Color.RED))
        ]
        
        meld_end = Meld(kind=MeldKind.RUN, tiles=[t.id for t in tiles_end])
        tile_instances_end = {str(t.id): t for t in tiles_end}
        
        # Should not raise an exception
        meld_end.validate_with_tiles(tile_instances_end)