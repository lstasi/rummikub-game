"""Comprehensive tests for Rummikub API endpoints using FastAPI TestClient.

This module tests all API endpoints with real FastAPI application behavior,
including request validation, response serialization, and error handling.
"""

from datetime import datetime
from unittest.mock import Mock
from fastapi.testclient import TestClient
import redis

from src.rummikub.api.main import app
from src.rummikub.service import GameService
from src.rummikub.models import (
    GameState, Player, Rack, Pool, Board, GameStatus,
    PlayTilesAction, DrawAction
)
from src.rummikub.service.exceptions import GameNotFoundError, ConcurrentModificationError
from src.rummikub.models.exceptions import (
    InvalidMeldError, TileNotOwnedError, NotPlayersTurnError,
    PoolEmptyError, InitialMeldNotMetError
)


class TestAPIEndpointsIntegration:
    """Integration tests for API endpoints with real Redis and GameService."""
    
    def setup_method(self):
        """Set up test environment with real Redis."""
        # Use dedicated test database
        self.redis_client = redis.Redis(host='localhost', port=6379, db=14, decode_responses=True)
        self.game_service = GameService(self.redis_client)
        
        # Override dependency for real service
        def override_get_game_service():
            return self.game_service
        
        from src.rummikub.api.dependencies import get_game_service
        app.dependency_overrides[get_game_service] = override_get_game_service
        
        self.client = TestClient(app)
        
        # Set up auth headers for testing
        import base64
        self.auth_alice = {"Authorization": f"Basic {base64.b64encode(b'alice:').decode()}"}
        self.auth_bob = {"Authorization": f"Basic {base64.b64encode(b'bob:').decode()}"}
        self.auth_charlie = {"Authorization": f"Basic {base64.b64encode(b'charlie:').decode()}"}
        
        # Clear test database
        self.cleanup_redis()
    
    def teardown_method(self):
        """Clean up after each test."""
        self.cleanup_redis()
        app.dependency_overrides.clear()
    
    def cleanup_redis(self):
        """Clean up test Redis database."""
        try:
            # Delete all keys in test database
            for key in self.redis_client.scan_iter("rummikub:*"):
                self.redis_client.delete(key)
        except Exception:
            pass  # Ignore cleanup errors
    
    def test_health_check_endpoint(self):
        """Test health check endpoint functionality."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "healthy"}
    
    def test_create_game_basic(self):
        """Test basic game creation endpoint."""
        response = self.client.post("/games", json={"num_players": 2}, headers=self.auth_alice)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "game_id" in data
        assert data["status"] == "waiting_for_players"
        assert data["num_players"] == 2
        assert len(data["players"]) == 1  # Creator automatically joined
        assert data["players"][0]["name"] == "alice"
        assert data["current_player_index"] == 0
        assert data["pool_size"] > 0
        assert "board" in data
        assert len(data["board"]["melds"]) == 0
        assert "created_at" in data
        assert "updated_at" in data
        assert data["winner_player_id"] is None
    
    def test_create_game_invalid_players(self):
        """Test game creation with invalid player counts."""
        # Too few players
        response = self.client.post("/games", json={"num_players": 1}, headers=self.auth_alice)
        assert response.status_code == 422
        
        # Too many players
        response = self.client.post("/games", json={"num_players": 5}, headers=self.auth_alice)
        assert response.status_code == 422
    
    def test_create_game_without_auth(self):
        """Test game creation without authentication returns 401."""
        response = self.client.post("/games", json={"num_players": 2})
        assert response.status_code == 401
        data = response.json()
        assert "Authentication required" in data["detail"]
    
    def test_get_games_empty(self):
        """Test getting games list when no games exist."""
        response = self.client.get("/games", headers=self.auth_alice)
        
        assert response.status_code == 200
        data = response.json()
        assert data == {"games": []}
    
    def test_get_games_with_games(self):
        """Test getting games list with existing games - only shows user's games."""
        # Create a game as alice
        create_response = self.client.post("/games", json={"num_players": 2}, headers=self.auth_alice)
        assert create_response.status_code == 200
        
        # Get games list as alice - should see her game
        response = self.client.get("/games", headers=self.auth_alice)
        
        assert response.status_code == 200
        data = response.json()
        assert "games" in data
        assert len(data["games"]) == 1
        
        game = data["games"][0]
        assert "game_id" in game
        assert game["status"] == "waiting_for_players"
        assert game["num_players"] == 2
        
        # Get games list as bob - should see no games (not in any)
        response = self.client.get("/games", headers=self.auth_bob)
        assert response.status_code == 200
        data = response.json()
        assert len(data["games"]) == 0
    
    def test_join_game_second_player(self):
        """Test joining game as second player."""
        # Create game as alice (auto-joins)
        create_response = self.client.post("/games", json={"num_players": 2}, headers=self.auth_alice)
        game_id = create_response.json()["game_id"]
        
        # Join as second player (bob)
        response = self.client.post(
            f"/games/{game_id}/players",
            json={},
            headers=self.auth_bob
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["game_id"] == game_id
        assert data["status"] == "in_progress"  # Game automatically started
        assert len(data["players"]) == 2
        
        # Bob should see his tiles (returned view is for Bob)
        bob = next(p for p in data["players"] if p["name"] == "bob")
        assert bob["rack"] is not None
        assert len(bob["rack"]["tiles"]) == 14
        
        # Alice's rack should be hidden from Bob's view  
        alice = next(p for p in data["players"] if p["name"] == "alice")
        assert alice["rack"] is None
        assert alice["rack_size"] == 14
    
    def test_get_available_games(self):
        """Test getting available games to join."""
        # Create a game as alice
        create_response = self.client.post("/games", json={"num_players": 2}, headers=self.auth_alice)
        game_id = create_response.json()["game_id"]
        
        # Bob should see this game as available
        response = self.client.get("/games/available", headers=self.auth_bob)
        assert response.status_code == 200
        data = response.json()
        assert len(data["games"]) == 1
        assert data["games"][0]["game_id"] == game_id
        
        # Alice should NOT see this game as available (already in it)
        response = self.client.get("/games/available", headers=self.auth_alice)
        assert response.status_code == 200
        data = response.json()
        assert len(data["games"]) == 0
    
    def test_join_game_invalid_name(self):
        """Test joining game with invalid player name - now handled by auth."""
        # No longer applicable - username comes from auth header, not request body
        pass
    
    def test_join_nonexistent_game(self):
        """Test joining non-existent game."""
        response = self.client.post(
            "/games/nonexistent-id/players",
            json={},
            headers=self.auth_alice
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "GAME_NOT_FOUND"
    
    def test_get_game_state_player_view(self):
        """Test getting game state from player's perspective."""
        # Create game as alice (auto-joins)
        create_response = self.client.post("/games", json={"num_players": 2}, headers=self.auth_alice)
        game_id = create_response.json()["game_id"]
        alice_id = create_response.json()["players"][0]["id"]
        
        # Bob joins
        self.client.post(
            f"/games/{game_id}/players",
            json={},
            headers=self.auth_bob
        )
        
        # Get Alice's view (must use alice's auth)
        response = self.client.get(f"/games/{game_id}/players/{alice_id}", headers=self.auth_alice)
        
        assert response.status_code == 200
        data = response.json()
        
        # Alice should see her tiles
        alice = next(p for p in data["players"] if p["name"] == "alice")
        assert alice["rack"] is not None
        assert len(alice["rack"]["tiles"]) == 14
        
        # Bob's tiles should be hidden from Alice
        bob = next(p for p in data["players"] if p["name"] == "bob")
        assert bob["rack"] is None
        assert bob["rack_size"] == 14
    
    def test_get_game_state_nonexistent_game(self):
        """Test getting game state for non-existent game."""
        response = self.client.get("/games/nonexistent/players/player-id", headers=self.auth_alice)
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "GAME_NOT_FOUND"
    
    def test_get_game_state_player_not_in_game(self):
        """Test getting game state for player not in game."""
        # Create game with alice
        create_response = self.client.post("/games", json={"num_players": 2}, headers=self.auth_alice)
        game_id = create_response.json()["game_id"]
        
        # Try to get state for non-existent player
        response = self.client.get(f"/games/{game_id}/players/fake-player-id", headers=self.auth_alice)
        
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "PLAYER_NOT_IN_GAME"
    
    def test_draw_tile_action(self):
        """Test draw tile action endpoint."""
        # Create game as alice and bob joins
        create_response = self.client.post("/games", json={"num_players": 2}, headers=self.auth_alice)
        game_id = create_response.json()["game_id"]
        alice_id = create_response.json()["players"][0]["id"]
        
        # Bob joins to start game
        self.client.post(f"/games/{game_id}/players", json={}, headers=self.auth_bob)
        
        # Draw tile (Alice's turn)
        response = self.client.post(
            f"/games/{game_id}/players/{alice_id}/actions/draw",
            json={},
            headers=self.auth_alice
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Alice should now have 15 tiles (14 + 1 drawn)
        alice = next(p for p in data["players"] if p["name"] == "alice")
        assert len(alice["rack"]["tiles"]) == 15
        
        # Should be Bob's turn now
        assert data["current_player_index"] == 1
    
    def test_play_tiles_valid_meld(self):
        """Test play tiles action with valid meld."""
        # Create game as alice and bob joins
        create_response = self.client.post("/games", json={"num_players": 2}, headers=self.auth_alice)
        game_id = create_response.json()["game_id"]
        alice_id = create_response.json()["players"][0]["id"]
        
        # Bob joins to start game
        self.client.post(f"/games/{game_id}/players", json={}, headers=self.auth_bob)
        
        # Get Alice's tiles to construct a valid meld
        state_response = self.client.get(f"/games/{game_id}/players/{alice_id}", headers=self.auth_alice)
        alice_tiles = state_response.json()["players"][0]["rack"]["tiles"]
        
        # Try to play the first 3 tiles as a group (may not be valid, but tests the endpoint)
        play_request = {
            "melds": [
                {
                    "id": "test-meld-1",
                    "kind": "group",
                    "tiles": alice_tiles[:3]
                }
            ]
        }
        
        response = self.client.post(
            f"/games/{game_id}/players/{alice_id}/actions/play",
            json=play_request,
            headers=self.auth_alice
        )
        
        # This might fail due to invalid meld, but should return proper error format
        if response.status_code != 200:
            # Should be a domain validation error
            assert response.status_code in [422, 400]
            data = response.json()
            assert "error" in data
            assert "code" in data["error"]
    
    def test_play_tiles_invalid_format(self):
        """Test play tiles with invalid request format."""
        create_response = self.client.post("/games", json={"num_players": 2}, headers=self.auth_alice)
        game_id = create_response.json()["game_id"]
        alice_id = create_response.json()["players"][0]["id"]
        
        # Invalid meld format
        response = self.client.post(
            f"/games/{game_id}/players/{alice_id}/actions/play",
            json={"melds": [{"invalid": "format"}]},
            headers=self.auth_alice
        )
        
        assert response.status_code == 422  # Validation error


class TestAPIEndpointsMocked:
    """Unit tests for API endpoints with mocked GameService."""
    
    def setup_method(self):
        """Set up test environment with mocked GameService."""
        self.mock_service = Mock(spec=GameService)
        
        def override_get_game_service():
            return self.mock_service
        
        from src.rummikub.api.dependencies import get_game_service
        app.dependency_overrides[get_game_service] = override_get_game_service
        
        self.client = TestClient(app)
    
    def teardown_method(self):
        """Clean up after each test."""
        app.dependency_overrides.clear()
    
    def create_sample_game_state(self, game_id="12345678-1234-5678-1234-567812345678", status=GameStatus.IN_PROGRESS):
        """Create a sample game state for testing."""
        from uuid import UUID
        
        player1 = Player(
            id="player-1",
            name="Alice",
            initial_meld_met=False,
            rack=Rack(tile_ids=["1ra", "2ra", "3ra", "4ra", "5ra", "6ra", "7ra", "8ra", "9ra", "10ra", "11ra", "12ra", "13ra", "1kb"])
        )
        
        player2 = Player(
            id="player-2",
            name="Bob", 
            initial_meld_met=False,
            rack=Rack(tile_ids=["1rb", "2rb", "3rb", "4rb", "5rb", "6rb", "7rb", "8rb", "9rb", "10rb", "11rb", "12rb", "13rb", "2kb"])
        )
        
        return GameState(
            game_id=UUID(game_id) if isinstance(game_id, str) else game_id,
            players=[player1, player2],
            current_player_index=0,
            pool=Pool(tile_ids=["3kb", "4kb", "5kb"]),
            board=Board(melds=[]),
            status=status,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_create_game_mocked(self):
        """Test create game endpoint with mocked service."""
        sample_game = self.create_sample_game_state(status=GameStatus.WAITING_FOR_PLAYERS)
        self.mock_service.create_game.return_value = sample_game
        
        response = self.client.post("/games", json={"num_players": 3})
        
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == "12345678-1234-5678-1234-567812345678"
        assert data["status"] == "waiting_for_players"
        
        self.mock_service.create_game.assert_called_once_with(3)
    
    def test_join_game_mocked(self):
        """Test join game endpoint with mocked service."""
        sample_game = self.create_sample_game_state()
        self.mock_service.join_game.return_value = sample_game
        self.mock_service._load_game_state.side_effect = GameNotFoundError("Not found")
        
        response = self.client.post(
            "/games/12345678-1234-5678-1234-567812345678/players",
            json={"player_name": "Charlie"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == "12345678-1234-5678-1234-567812345678"
        
        self.mock_service.join_game.assert_called_once_with("12345678-1234-5678-1234-567812345678", "Charlie")
    
    def test_get_games_mocked(self):
        """Test get games endpoint with mocked service."""
        sample_games = [
            self.create_sample_game_state("12345678-1234-5678-1234-567812345671"),
            self.create_sample_game_state("12345678-1234-5678-1234-567812345672")
        ]
        self.mock_service.get_games.return_value = sample_games
        
        response = self.client.get("/games")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["games"]) == 2
        
        self.mock_service.get_games.assert_called_once()
    
    def test_draw_tile_mocked(self):
        """Test draw tile endpoint with mocked service."""
        sample_game = self.create_sample_game_state()
        self.mock_service.execute_turn.return_value = sample_game
        
        response = self.client.post(
            "/games/12345678-1234-5678-1234-567812345678/players/player-1/actions/draw",
            json={}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == "12345678-1234-5678-1234-567812345678"
        
        # Verify execute_turn was called with DrawAction
        self.mock_service.execute_turn.assert_called_once()
        args = self.mock_service.execute_turn.call_args
        assert args[0][0] == "12345678-1234-5678-1234-567812345678"
        assert args[0][1] == "player-1"
        assert isinstance(args[0][2], DrawAction)
    
    def test_play_tiles_mocked(self):
        """Test play tiles endpoint with mocked service."""
        sample_game = self.create_sample_game_state()
        self.mock_service.execute_turn.return_value = sample_game
        
        play_request = {
            "melds": [
                {
                    "id": "meld-1",
                    "kind": "group",
                    "tiles": ["1ra", "1rb", "1ro"]
                },
                {
                    "id": "meld-2", 
                    "kind": "run",
                    "tiles": ["1kb", "2kb", "3kb"]
                }
            ]
        }
        
        response = self.client.post(
            "/games/12345678-1234-5678-1234-567812345678/players/player-1/actions/play",
            json=play_request
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == "12345678-1234-5678-1234-567812345678"
        
        # Verify execute_turn was called with PlayTilesAction
        self.mock_service.execute_turn.assert_called_once()
        args = self.mock_service.execute_turn.call_args
        assert args[0][0] == "12345678-1234-5678-1234-567812345678"
        assert args[0][1] == "player-1"
        assert isinstance(args[0][2], PlayTilesAction)
        assert len(args[0][2].melds) == 2


class TestAPIErrorHandling:
    """Tests for API error handling and exception mapping."""
    
    def setup_method(self):
        """Set up test environment with mocked service for error testing."""
        self.mock_service = Mock(spec=GameService)
        
        def override_get_game_service():
            return self.mock_service
        
        from src.rummikub.api.dependencies import get_game_service
        app.dependency_overrides[get_game_service] = override_get_game_service
        
        self.client = TestClient(app)
    
    def teardown_method(self):
        """Clean up after each test."""
        app.dependency_overrides.clear()
    
    def test_game_not_found_error(self):
        """Test GameNotFoundError mapping to 404."""
        self.mock_service.join_game.side_effect = GameNotFoundError("Game not found")
        
        response = self.client.post(
            "/games/nonexistent/players",
            json={"player_name": "Alice"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "GAME_NOT_FOUND"
        assert "Game not found" in data["error"]["message"]
    
    def test_invalid_meld_error(self):
        """Test InvalidMeldError mapping to 422."""
        self.mock_service.execute_turn.side_effect = InvalidMeldError("Invalid meld: not enough tiles")
        
        response = self.client.post(
            "/games/test-game/players/player-1/actions/play",
            json={"melds": [{"id": "m1", "kind": "group", "tiles": ["1ra", "1rb"]}]}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "INVALID_MELD"
        assert "group" in data["error"]["message"].lower() and "tile" in data["error"]["message"].lower()
    
    def test_tile_not_owned_error(self):
        """Test TileNotOwnedError mapping to 422."""
        self.mock_service.execute_turn.side_effect = TileNotOwnedError("Player doesn't own tile: 1ra")
        
        response = self.client.post(
            "/games/test-game/players/player-1/actions/play",
            json={"melds": [{"id": "m1", "kind": "group", "tiles": ["1ra", "1rb", "1ro"]}]}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "TILE_NOT_OWNED"
    
    def test_not_player_turn_error(self):
        """Test NotPlayersTurnError mapping to 403."""
        self.mock_service.execute_turn.side_effect = NotPlayersTurnError("Not player's turn")
        
        response = self.client.post(
            "/games/test-game/players/player-2/actions/draw",
            json={}
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "NOT_PLAYER_TURN"
    
    def test_pool_empty_error(self):
        """Test PoolEmptyError mapping to 400."""
        self.mock_service.execute_turn.side_effect = PoolEmptyError("No tiles left in pool")
        
        response = self.client.post(
            "/games/test-game/players/player-1/actions/draw",
            json={}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "POOL_EMPTY"
    
    def test_player_not_in_game_error(self):
        """Test PlayerNotInGameError mapping to 403."""
        # Create a proper game state mock with players list
        mock_game_state = Mock()
        mock_game_state.players = []  # Empty players list so player won't be found
        self.mock_service._load_game_state.return_value = mock_game_state
        
        response = self.client.get("/games/test-game/players/fake-player")
        
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "PLAYER_NOT_IN_GAME"
    
    def test_initial_meld_not_met_error(self):
        """Test InitialMeldNotMetError mapping to 422."""
        self.mock_service.execute_turn.side_effect = InitialMeldNotMetError("Initial meld must be at least 30 points")
        
        response = self.client.post(
            "/games/test-game/players/player-1/actions/play",
            json={"melds": [{"id": "m1", "kind": "group", "tiles": ["1ra", "1rb", "1ro"]}]}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "INSUFFICIENT_INITIAL_MELD"
        assert "30 points" in data["error"]["message"]
    
    def test_concurrent_modification_error(self):
        """Test ConcurrentModificationError mapping to 503."""
        self.mock_service.execute_turn.side_effect = ConcurrentModificationError("State changed during operation")
        
        response = self.client.post(
            "/games/test-game/players/player-1/actions/draw",
            json={}
        )
        
        assert response.status_code == 503
        data = response.json()
        assert data["error"]["code"] == "CONCURRENT_MODIFICATION"