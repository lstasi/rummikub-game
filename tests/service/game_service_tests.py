"""Tests for the GameService with Redis persistence."""

import pytest

import fakeredis

from rummikub.service import GameService, GameNotFoundError, ConcurrentModificationError
from rummikub.models import GameState, GameStatus, DrawAction


class TestGameService:
    """Test cases for GameService functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.redis = fakeredis.FakeRedis()
        self.service = GameService(self.redis)

    def test_create_game(self):
        """Test creating a new game."""
        # Act
        game_state = self.service.create_game(num_players=4)
        
        # Assert
        assert isinstance(game_state, GameState)
        assert game_state.status == GameStatus.WAITING_FOR_PLAYERS
        assert game_state.num_players == 4
        assert len(game_state.players) == 4  # Pre-initialized players
        
        # Check that game is persisted in Redis
        key = f"rummikub:games:{game_state.game_id}"
        assert self.redis.exists(key)

    def test_join_game_new_player(self):
        """Test joining a new player to a game."""
        # Arrange
        game_state = self.service.create_game(num_players=4)
        
        # Act
        updated_state = self.service.join_game(str(game_state.game_id), "Alice")
        
        # Assert
        assert len(updated_state.players) == 4
        # Find the player that joined
        alice = None
        for player in updated_state.players:
            if player.name == "Alice":
                alice = player
                break
        assert alice is not None
        assert alice.joined is True
        assert alice.name == "Alice"

    def test_join_game_existing_player(self):
        """Test rejoining with same player name returns curated state."""
        # Arrange
        game_state = self.service.create_game(num_players=4)
        first_join = self.service.join_game(str(game_state.game_id), "Alice")
        
        # Act - join again with same name
        second_join = self.service.join_game(str(game_state.game_id), "Alice")
        
        # Assert
        assert len(second_join.players) == 4
        # Should return the same player
        alice_first = None
        alice_second = None
        for player in first_join.players:
            if player.name == "Alice":
                alice_first = player
                break
        for player in second_join.players:
            if player.name == "Alice":
                alice_second = player
                break
        
        assert alice_first.id == alice_second.id

    def test_join_game_not_found(self):
        """Test joining a non-existent game raises error."""
        # Act & Assert
        with pytest.raises(GameNotFoundError):
            self.service.join_game("non-existent-game", "Alice")

    def test_get_game_existing(self):
        """Test retrieving an existing game."""
        # Arrange
        game_state = self.service.create_game(num_players=4)
        self.service.join_game(str(game_state.game_id), "Alice")
        
        # Act
        retrieved_state = self.service.get_game(str(game_state.game_id), "Alice")
        
        # Assert
        assert retrieved_state is not None
        assert retrieved_state.game_id == game_state.game_id

    def test_get_game_not_found(self):
        """Test retrieving a non-existent game returns None."""
        # Act
        result = self.service.get_game("non-existent-game", "Alice")
        
        # Assert
        assert result is None

    def test_get_game_player_not_found(self):
        """Test retrieving game with non-existent player returns None."""
        # Arrange
        game_state = self.service.create_game(num_players=4)
        
        # Act
        result = self.service.get_game(str(game_state.game_id), "NonExistentPlayer")
        
        # Assert
        assert result is None

    def test_get_games(self):
        """Test retrieving all games."""
        # Arrange
        game1 = self.service.create_game(num_players=4)
        game2 = self.service.create_game(num_players=3)
        
        # Act
        games = self.service.get_games()
        
        # Assert
        assert len(games) == 2
        game_ids = {game.game_id for game in games}
        assert game1.game_id in game_ids
        assert game2.game_id in game_ids

    def test_get_games_empty(self):
        """Test retrieving games when none exist."""
        # Act
        games = self.service.get_games()
        
        # Assert
        assert games == []

    def test_execute_turn_draw_action(self):
        """Test executing a draw action."""
        # Arrange
        game_state = self.service.create_game(num_players=4)
        joined_state = self.service.join_game(str(game_state.game_id), "Alice")
        alice = None
        for player in joined_state.players:
            if player.name == "Alice":
                alice = player
                break
        
        # Start the game to enable turn execution
        started_game = self.service.engine.start_game(joined_state)
        self.service._save_game_state(started_game)
        
        action = DrawAction()
        
        # Act
        updated_state = self.service.execute_turn(str(game_state.game_id), alice.id, action)
        
        # Assert
        assert isinstance(updated_state, GameState)
        # The player should have drawn a tile
        updated_alice = None
        for player in updated_state.players:
            if player.id == alice.id:
                updated_alice = player
                break
        assert updated_alice is not None
        # Check that Alice's rack has one more tile than initial
        assert len(updated_alice.rack.tile_ids) == 15  # 14 initial + 1 drawn

    def test_game_state_curation(self):
        """Test that game state is properly curated for players."""
        # Arrange
        game_state = self.service.create_game(num_players=4)
        self.service.join_game(str(game_state.game_id), "Alice")
        self.service.join_game(str(game_state.game_id), "Bob")
        
        # Act - get game state for Alice
        alice_view = self.service.get_game(str(game_state.game_id), "Alice")
        
        # Assert
        assert alice_view is not None
        alice_player = None
        bob_player = None
        
        for player in alice_view.players:
            if player.name == "Alice":
                alice_player = player
            elif player.name == "Bob":
                bob_player = player
        
        assert alice_player is not None
        assert bob_player is not None
        
        # Alice should see her own tiles
        assert len(alice_player.rack.tile_ids) == 14
        
        # Bob's rack should be empty in Alice's view (privacy)
        assert len(bob_player.rack.tile_ids) == 0

    def test_serialization_round_trip(self):
        """Test that game state serialization and deserialization works correctly."""
        # Arrange
        game_state = self.service.create_game(num_players=4)
        
        # Act - serialize and deserialize
        serialized = self.service._serialize_game_state(game_state)
        deserialized = self.service._deserialize_game_state(serialized)
        
        # Assert
        assert deserialized.game_id == game_state.game_id
        assert deserialized.status == game_state.status
        assert deserialized.num_players == game_state.num_players
        assert len(deserialized.players) == len(game_state.players)
        assert len(deserialized.pool.tile_ids) == len(game_state.pool.tile_ids)

    def test_concurrent_access_protection(self):
        """Test that concurrent access is properly protected with locks."""
        # Arrange
        game_state = self.service.create_game(num_players=4)
        game_id = str(game_state.game_id)
        
        # Simulate lock acquisition
        lock_key = f"rummikub:games:{game_id}:lock"
        
        # Act - try to acquire lock
        with self.service._game_lock(game_id):
            # Verify lock is set
            assert self.redis.get(lock_key) is not None
        
        # Assert - lock should be released after context
        assert self.redis.get(lock_key) is None

    def test_concurrent_modification_error(self):
        """Test that concurrent modification raises appropriate error."""
        # Arrange
        game_state = self.service.create_game(num_players=4)
        game_id = str(game_state.game_id)
        lock_key = f"rummikub:games:{game_id}:lock"
        
        # Simulate another session holding the lock
        self.redis.set(lock_key, "other-session", ex=5)
        
        # Act & Assert
        with pytest.raises(ConcurrentModificationError):
            with self.service._game_lock(game_id):
                pass

    def test_ttl_for_completed_games(self):
        """Test that completed games get TTL set."""
        # Arrange
        game_state = self.service.create_game(num_players=4)
        # Mark game as completed
        completed_state = game_state._copy_with(status=GameStatus.COMPLETED)
        
        # Act
        self.service._save_game_state(completed_state)
        
        # Assert
        key = f"rummikub:games:{game_state.game_id}"
        ttl = self.redis.ttl(key)
        assert ttl > 0  # Should have TTL set
        assert ttl <= 24 * 60 * 60  # Should be <= 24 hours

    def test_no_ttl_for_active_games(self):
        """Test that active games don't get TTL."""
        # Arrange
        game_state = self.service.create_game(num_players=4)
        
        # Act
        self.service._save_game_state(game_state)
        
        # Assert
        key = f"rummikub:games:{game_state.game_id}"
        ttl = self.redis.ttl(key)
        assert ttl == -1  # No TTL set

    def test_find_player_by_name(self):
        """Test finding player by name utility method."""
        # Arrange
        game_state = self.service.create_game(num_players=4)
        joined_state = self.service.join_game(str(game_state.game_id), "Alice")
        
        # Act
        found_player = self.service._find_player_by_name(joined_state, "Alice")
        not_found_player = self.service._find_player_by_name(joined_state, "NonExistent")
        
        # Assert
        assert found_player is not None
        assert found_player.name == "Alice"
        assert not_found_player is None

    def test_invalid_action_type(self):
        """Test that invalid action types raise appropriate error."""
        # Arrange
        game_state = self.service.create_game(num_players=4)
        joined_state = self.service.join_game(str(game_state.game_id), "Alice")
        alice = None
        for player in joined_state.players:
            if player.name == "Alice":
                alice = player
                break
        
        # Act & Assert
        with pytest.raises(ValueError, match="Unknown action type"):
            self.service.execute_turn(str(game_state.game_id), alice.id, "invalid_action")