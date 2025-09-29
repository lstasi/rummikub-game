"""Comprehensive tests for GameService with Redis persistence."""

import pytest
from uuid import uuid4
import redis
from redis.exceptions import ConnectionError as RedisConnectionError

from rummikub.models import (
    GameState, GameStatus, DrawAction
)
from rummikub.service import GameService
from rummikub.service.exceptions import GameNotFoundError


class TestGameServiceBasics:
    """Test basic GameService functionality."""
    
    def setup_method(self):
        """Set up test fixtures with real Redis."""
        try:
            # Connect to Redis (default localhost:6379)
            self.redis = redis.Redis(
                host='localhost',
                port=6379,
                db=15,  # Use database 15 for testing to avoid conflicts
                decode_responses=False  # Keep as bytes to match service expectations
            )
            # Test connection
            self.redis.ping()
            
            # Clean up any existing test data
            self.cleanup_redis()
            
        except (RedisConnectionError, ConnectionRefusedError) as e:
            pytest.skip(f"Redis server not available: {e}")
        
        self.service = GameService(self.redis)
    
    def teardown_method(self):
        """Clean up after each test."""
        if hasattr(self, 'redis'):
            self.cleanup_redis()
    
    def cleanup_redis(self):
        """Remove all test data from Redis."""
        try:
            # Delete all rummikub test keys
            keys = self.redis.keys("rummikub:*")
            if keys:
                self.redis.delete(*keys)
        except Exception:
            # Ignore cleanup errors
            pass
    
    def test_service_creation(self):
        """Test that GameService can be created with Redis client."""
        assert self.service is not None
        assert self.service.redis == self.redis
        assert self.service.engine is not None
        assert self.service.session_id is not None
        assert len(self.service.session_id) == 36  # UUID string length
    
    def test_create_game_basic(self):
        """Test basic game creation."""
        game_state = self.service.create_game(2)
        
        # Verify game state structure
        assert isinstance(game_state, GameState)
        assert game_state.status == GameStatus.WAITING_FOR_PLAYERS
        assert game_state.num_players == 2
        assert len(game_state.players) == 2
        assert game_state.game_id is not None
        
        # Verify Redis persistence
        key = f"rummikub:games:{game_state.game_id}"
        assert self.redis.exists(key)
    
    def test_join_game_basic(self):
        """Test basic player joining."""
        game_state = self.service.create_game(2)
        
        # Join first player
        updated_state = self.service.join_game(str(game_state.game_id), "Alice")
        
        # Find Alice
        alice = None
        for player in updated_state.players:
            if player.name == "Alice":
                alice = player
                break
        
        assert alice is not None
        assert alice.joined is True
        assert alice.name == "Alice"
        assert len(alice.rack.tile_ids) == 14  # Should see own tiles
    
    def test_get_game_basic(self):
        """Test basic game retrieval."""
        game_state = self.service.create_game(2)
        self.service.join_game(str(game_state.game_id), "Alice")
        
        # Retrieve game for Alice
        retrieved_state = self.service.get_game(str(game_state.game_id), "Alice")
        
        assert retrieved_state is not None
        assert retrieved_state.game_id == game_state.game_id
    
    def test_execute_draw_action_basic(self):
        """Test basic draw action execution."""
        # Create and start game
        game_state = self.service.create_game(2)
        self.service.join_game(str(game_state.game_id), "Alice")
        started_state = self.service.join_game(str(game_state.game_id), "Bob")
        
        # Get Alice's player ID
        alice = None
        for player in started_state.players:
            if player.name == "Alice":
                alice = player
                break
        
        assert alice is not None
        
        # Execute draw action
        draw_action = DrawAction()
        updated_state = self.service.execute_turn(str(game_state.game_id), alice.id, draw_action)
        
        # Verify action was executed
        assert isinstance(updated_state, GameState)
        
        # Alice should have one more tile (15 total)
        updated_alice = None
        for player in updated_state.players:
            if player.name == "Alice":
                updated_alice = player
                break
        
        assert updated_alice is not None
        assert len(updated_alice.rack.tile_ids) == 15
    
    def test_serialization_basic(self):
        """Test basic serialization and deserialization."""
        game_state = self.service.create_game(2)
        
        # Serialize
        serialized = self.service._serialize_game_state(game_state)
        assert isinstance(serialized, str)
        
        # Deserialize
        deserialized = self.service._deserialize_game_state(serialized)
        
        # Verify round trip
        assert deserialized.game_id == game_state.game_id
        assert deserialized.status == game_state.status
        assert deserialized.num_players == game_state.num_players
        assert len(deserialized.players) == len(game_state.players)
    
    def test_lock_basic(self):
        """Test basic locking functionality."""
        game_state = self.service.create_game(2)
        game_id = str(game_state.game_id)
        lock_key = f"rummikub:games:{game_id}:lock"
        
        # Lock should not exist initially
        assert self.redis.get(lock_key) is None
        
        # Acquire lock
        with self.service._game_lock(game_id):
            # Lock should exist
            lock_value = self.redis.get(lock_key)
            assert lock_value is not None
            # Handle bytes vs string comparison for real Redis
            lock_value_str = lock_value.decode('utf-8') if isinstance(lock_value, bytes) else str(lock_value)
            assert lock_value_str == self.service.session_id
        
        # Lock should be released
        assert self.redis.get(lock_key) is None
    
    def test_error_handling_basic(self):
        """Test basic error handling."""
        fake_game_id = str(uuid4())
        
        # Test GameNotFoundError
        with pytest.raises(GameNotFoundError):
            self.service.join_game(fake_game_id, "Alice")
        
        # Test non-existent game returns None
        result = self.service.get_game(fake_game_id, "Alice")
        assert result is None
    
    def test_state_curation_basic(self):
        """Test basic state curation."""
        game_state = self.service.create_game(2)  # Use 2 players for faster test
        self.service.join_game(str(game_state.game_id), "Alice")
        bob_state = self.service.join_game(str(game_state.game_id), "Bob")
        
        # Now the game should be started and tiles dealt
        assert bob_state.status.value == "in_progress"
        
        # bob_state is curated for Bob - he should see his tiles, Alice's should be empty
        alice_in_bob_view = None
        bob_in_bob_view = None
        for player in bob_state.players:
            if player.name == "Alice":
                alice_in_bob_view = player
            elif player.name == "Bob":
                bob_in_bob_view = player
        
        assert alice_in_bob_view is not None
        assert bob_in_bob_view is not None
        
        # Bob should see his own tiles (14 tiles) in his view
        assert len(bob_in_bob_view.rack.tile_ids) == 14
        
        # Alice should have empty rack in Bob's view (curated)
        assert len(alice_in_bob_view.rack.tile_ids) == 0
        
        # Now get Alice's view - she should see her tiles
        alice_view = self.service.get_game(str(game_state.game_id), "Alice")
        assert alice_view is not None
        
        alice_in_alice_view = None
        bob_in_alice_view = None
        for player in alice_view.players:
            if player.name == "Alice":
                alice_in_alice_view = player
            elif player.name == "Bob":
                bob_in_alice_view = player
        
        assert alice_in_alice_view is not None
        assert bob_in_alice_view is not None
        
        # Alice should see her own tiles (14 tiles) in her view
        assert len(alice_in_alice_view.rack.tile_ids) == 14
        
        # Bob should have empty rack in Alice's view (curated)
        assert len(bob_in_alice_view.rack.tile_ids) == 0
    
    def test_ttl_handling_basic(self):
        """Test basic TTL handling."""
        game_state = self.service.create_game(2)
        
        # Active games should have no TTL
        key = f"rummikub:games:{game_state.game_id}"
        ttl = self.redis.ttl(key)
        assert ttl == -1  # No TTL
        
        # Completed games should have TTL
        completed_state = game_state._copy_with(status=GameStatus.COMPLETED)
        self.service._save_game_state(completed_state)
        
        ttl = self.redis.ttl(key)
        assert ttl > 0  # Should have TTL
        assert ttl <= 24 * 60 * 60  # Should be <= 24 hours
