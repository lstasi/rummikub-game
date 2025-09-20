"""Tests for initialization and validation methods."""

import pytest
from uuid import uuid4

from rummikub.models import (
    Color, NumberedTile, JokerTile, TileInstance, 
    GameState, Player, Rack, Pool,
    GameStateError
)


class TestPoolInitialization:
    """Test Pool initialization and validation methods."""
    
    def test_create_full_pool_success(self):
        """Test successful creation of complete pool."""
        pool, tile_instances = Pool.create_full_pool()
        
        # Basic counts
        assert len(pool) == 106
        assert len(tile_instances) == 106
        
        # All tile IDs should be in tile_instances
        for tile_id in pool.tile_ids:
            assert str(tile_id) in tile_instances
    
    def test_create_full_pool_contains_correct_tiles(self):
        """Test that created pool contains exactly the right tiles."""
        pool, tile_instances = Pool.create_full_pool()
        
        # Count by type
        numbered_tiles = {}  # (number, color) -> count
        joker_count = 0
        
        for tile_id in pool.tile_ids:
            tile = tile_instances[str(tile_id)]
            
            if isinstance(tile.kind, NumberedTile):
                key = (tile.kind.number, tile.kind.color)
                numbered_tiles[key] = numbered_tiles.get(key, 0) + 1
            elif isinstance(tile.kind, JokerTile):
                joker_count += 1
        
        # Check numbered tiles: 2 of each number (1-13) in each color (4 colors)
        assert len(numbered_tiles) == 52  # 4 colors * 13 numbers
        
        for color in Color:
            for number in range(1, 14):
                key = (number, color)
                assert key in numbered_tiles
                assert numbered_tiles[key] == 2
        
        # Check jokers
        assert joker_count == 2
    
    def test_validate_complete_pool_success(self):
        """Test successful validation of complete pool."""
        pool, tile_instances = Pool.create_full_pool()
        
        # Should pass validation without raising exception
        result = pool.validate_complete_pool(tile_instances)
        assert result is True
    
    def test_validate_complete_pool_wrong_count(self):
        """Test validation failure with wrong tile count."""
        pool, tile_instances = Pool.create_full_pool()
        
        # Remove one tile
        removed_tile_id = pool.tile_ids.pop()
        del tile_instances[str(removed_tile_id)]
        
        with pytest.raises(GameStateError, match="Pool must contain exactly 106 tiles, got 105"):
            pool.validate_complete_pool(tile_instances)
    
    def test_validate_complete_pool_duplicate_tiles(self):
        """Test validation failure with duplicate tile IDs."""
        pool, tile_instances = Pool.create_full_pool()
        
        # Duplicate the first tile ID (don't change total count to test duplicate detection)
        duplicate_tile_id = pool.tile_ids[0]
        pool.tile_ids.pop()  # Remove last tile
        pool.tile_ids.append(duplicate_tile_id)  # Add duplicate
        
        with pytest.raises(GameStateError, match="Pool contains duplicate tile IDs"):
            pool.validate_complete_pool(tile_instances)
    
    def test_validate_complete_pool_missing_tile_instance(self):
        """Test validation failure when tile_instances is missing a tile."""
        pool, tile_instances = Pool.create_full_pool()
        
        # Remove tile from tile_instances but not from pool.tile_ids
        first_tile_id = str(pool.tile_ids[0])
        del tile_instances[first_tile_id]
        
        with pytest.raises(GameStateError, match=f"Tile {pool.tile_ids[0]} not found in tile_instances"):
            pool.validate_complete_pool(tile_instances)


class TestRackValidation:
    """Test Rack validation methods."""
    
    def test_validate_initial_rack_size_success(self):
        """Test successful validation of 14-tile rack."""
        tile_ids = [uuid4() for _ in range(14)]
        rack = Rack(tile_ids=tile_ids)
        
        result = rack.validate_initial_rack_size()
        assert result is True
    
    def test_validate_initial_rack_size_too_few(self):
        """Test validation failure with too few tiles."""
        tile_ids = [uuid4() for _ in range(10)]
        rack = Rack(tile_ids=tile_ids)
        
        with pytest.raises(GameStateError, match="Initial rack must contain exactly 14 tiles, got 10"):
            rack.validate_initial_rack_size()
    
    def test_validate_initial_rack_size_too_many(self):
        """Test validation failure with too many tiles."""
        tile_ids = [uuid4() for _ in range(20)]
        rack = Rack(tile_ids=tile_ids)
        
        with pytest.raises(GameStateError, match="Initial rack must contain exactly 14 tiles, got 20"):
            rack.validate_initial_rack_size()
    
    def test_validate_initial_rack_size_empty(self):
        """Test validation failure with empty rack."""
        rack = Rack()  # Empty rack
        
        with pytest.raises(GameStateError, match="Initial rack must contain exactly 14 tiles, got 0"):
            rack.validate_initial_rack_size()


class TestGameStateInitialization:
    """Test GameState initialization and validation methods."""
    
    def test_create_new_game_success(self):
        """Test successful creation of new game with valid player counts."""
        game_id = uuid4()
        
        # Test all valid player counts
        for num_players in [2, 3, 4]:
            game_state = GameState.create_new_game(game_id, num_players)
            assert game_state.game_id == game_id
            assert game_state.status.value == "waiting_for_players"
    
    def test_create_new_game_invalid_player_counts(self):
        """Test creation failure with invalid player counts."""
        game_id = uuid4()
        
        # Test invalid counts
        invalid_counts = [0, 1, 5, 6, -1, 100]
        
        for num_players in invalid_counts:
            with pytest.raises(GameStateError, match=f"Number of players must be between 2 and 4, got {num_players}"):
                GameState.create_new_game(game_id, num_players)
    
    def test_validate_player_count_success(self):
        """Test successful player count validation."""
        game_id = uuid4()
        game_state = GameState(game_id=game_id)
        
        # Test valid player counts
        for num_players in [2, 3, 4]:
            game_state.players = [Player(id=f"player_{i}") for i in range(num_players)]
            result = game_state.validate_player_count()
            assert result is True
    
    def test_validate_player_count_invalid(self):
        """Test player count validation with invalid counts."""
        game_id = uuid4()
        game_state = GameState(game_id=game_id)
        
        # Test too few players
        game_state.players = [Player(id="player_1")]
        with pytest.raises(GameStateError, match="Number of players must be between 2 and 4, got 1"):
            game_state.validate_player_count()
        
        # Test too many players
        game_state.players = [Player(id=f"player_{i}") for i in range(5)]
        with pytest.raises(GameStateError, match="Number of players must be between 2 and 4, got 5"):
            game_state.validate_player_count()
        
        # Test no players
        game_state.players = []
        with pytest.raises(GameStateError, match="Number of players must be between 2 and 4, got 0"):
            game_state.validate_player_count()


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple components."""
    
    def test_complete_game_initialization(self):
        """Test a complete game setup scenario."""
        # Create game state
        game_id = uuid4()
        game_state = GameState.create_new_game(game_id, 3)
        
        # Create full pool
        pool, tile_instances = Pool.create_full_pool()
        game_state.pool = pool
        
        # Create players with properly sized racks
        for i in range(3):
            player = Player(id=f"player_{i}", name=f"Player {i+1}")
            # Give each player 14 tiles from the pool
            player_tiles = []
            for _ in range(14):
                if pool.tile_ids:
                    tile_id = pool.tile_ids.pop(0)  # Take from front of pool
                    player_tiles.append(tile_id)
            
            player.rack = Rack(tile_ids=player_tiles)
            player.rack.validate_initial_rack_size()  # Should pass
            game_state.players.append(player)
        
        # Validate game state
        game_state.validate_player_count()  # Should pass
        
        # Validate tile ownership (remaining tiles in pool + player racks should equal original set)
        game_state.validate_tile_ownership(tile_instances)  # Should pass
        
        # Check final counts
        assert len(game_state.players) == 3
        assert len(pool) == 106 - (3 * 14)  # 106 - 42 = 64 tiles remaining
        assert all(len(player.rack) == 14 for player in game_state.players)
    
    def test_edge_case_minimum_players(self):
        """Test edge case with minimum number of players (2)."""
        game_id = uuid4()
        game_state = GameState.create_new_game(game_id, 2)
        
        # Add 2 players
        for i in range(2):
            player = Player(id=f"player_{i}")
            game_state.players.append(player)
        
        # Should validate successfully
        game_state.validate_player_count()
    
    def test_edge_case_maximum_players(self):
        """Test edge case with maximum number of players (4)."""
        game_id = uuid4()
        game_state = GameState.create_new_game(game_id, 4)
        
        # Add 4 players
        for i in range(4):
            player = Player(id=f"player_{i}")
            game_state.players.append(player)
        
        # Should validate successfully
        game_state.validate_player_count()