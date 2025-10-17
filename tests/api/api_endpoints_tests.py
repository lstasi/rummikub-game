"""Comprehensive tests for Rummikub API endpoints using FastAPI TestClient.

This module tests all API endpoints with real FastAPI application behavior,
including request validation, response serialization, and error handling.
"""

from datetime import datetime
from unittest.mock import Mock
from fastapi.testclient import TestClient

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
        """Set up test environment with FakeRedis for testing."""
        import fakeredis
        # Use FakeRedis for testing
        self.redis_client = fakeredis.FakeRedis(decode_responses=True)
        self.game_service = GameService(self.redis_client)
        
        # Override dependency for real service
        def override_get_game_service():
            return self.game_service
        
        from src.rummikub.api.dependencies import get_game_service
        app.dependency_overrides[get_game_service] = override_get_game_service
        
        self.client = TestClient(app)
        
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
        """Test basic game creation endpoint with auto-join."""
        import base64
        
        # Create auth header
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        response = self.client.post("/games", json={"num_players": 2}, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "game_id" in data
        assert data["status"] == "waiting_for_players"
        assert data["num_players"] == 2
        assert len(data["players"]) == 1  # Creator is auto-joined
        assert data["players"][0]["name"] == "Alice"
        assert data["players"][0]["rack"] is not None  # Creator sees their rack
        assert len(data["players"][0]["rack"]["tiles"]) == 14
        assert data["current_player_index"] == 0
        assert data["pool_size"] == 78  # 106 - (2 * 14) tiles pre-dealt for 2-player game
        assert "board" in data
        assert len(data["board"]["melds"]) == 0
        assert "created_at" in data
        assert "updated_at" in data
        assert data["winner_player_id"] is None
    
    def test_create_game_invalid_players(self):
        """Test game creation with invalid player counts."""
        import base64
        
        # Create auth header
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        # Too few players
        response = self.client.post("/games", json={"num_players": 1}, headers=headers)
        assert response.status_code == 422
        
        # Too many players
        response = self.client.post("/games", json={"num_players": 5}, headers=headers)
        assert response.status_code == 422
    
    def test_get_games_empty(self):
        """Test getting games list when no games exist."""
        import base64
        
        # Add Basic Auth header
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        response = self.client.get("/games", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data == {"games": []}
    
    def test_get_games_with_games(self):
        """Test getting games list with existing games."""
        import base64
        
        # Create auth header for Alice
        alice_credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        alice_headers = {"Authorization": f"Basic {alice_credentials}"}
        
        # Create a game first (creator auto-joins)
        create_response = self.client.post("/games", json={"num_players": 2}, headers=alice_headers)
        assert create_response.status_code == 200
        
        # Get games list as Bob (should see Alice's game since Bob hasn't joined)
        bob_credentials = base64.b64encode(b"Bob:password").decode("utf-8")
        bob_headers = {"Authorization": f"Basic {bob_credentials}"}
        response = self.client.get("/games", headers=bob_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "games" in data
        assert len(data["games"]) == 1
        
        game = data["games"][0]
        assert "game_id" in game
        assert game["status"] == "waiting_for_players"
        assert game["num_players"] == 2
        assert len(game["players"]) == 1  # Creator is joined
    
    def test_join_game_first_player(self):
        """Test joining game as second player (creator is first)."""
        import base64
        
        # Create game with Alice as creator (auto-joined as first player)
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        create_response = self.client.post("/games", json={"num_players": 2}, headers=headers)
        game_id = create_response.json()["game_id"]
        
        # Join as second player (Bob) - now using Basic Auth
        bob_credentials = base64.b64encode(b"Bob:password").decode("utf-8")
        bob_headers = {"Authorization": f"Basic {bob_credentials}"}
        response = self.client.post(
            f"/games/{game_id}/players",
            json={},
            headers=bob_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["game_id"] == game_id
        assert data["status"] == "in_progress"  # Game starts with 2 players
        assert len(data["players"]) == 2
        
        # Bob should see his rack
        bob = next(p for p in data["players"] if p["name"] == "Bob")
        assert bob["rack"] is not None
        assert len(bob["rack"]["tiles"]) == 14  # Initial tiles dealt
        
        # Alice's rack should be hidden from Bob's view
        alice = next(p for p in data["players"] if p["name"] == "Alice")
        assert alice["rack"] is None
    
    def test_join_game_second_player_starts_game(self):
        """Test that joining as third player in a 3-player game keeps it waiting."""
        import base64
        
        # Create game with Alice as creator (auto-joined as first player)
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        create_response = self.client.post("/games", json={"num_players": 3}, headers=headers)
        game_id = create_response.json()["game_id"]
        
        # Join as second player (Bob) - now using Basic Auth
        bob_credentials = base64.b64encode(b"Bob:password").decode("utf-8")
        bob_headers = {"Authorization": f"Basic {bob_credentials}"}
        self.client.post(
            f"/games/{game_id}/players",
            json={},
            headers=bob_headers
        )
        
        # Join as third player (Charlie) - game should start now
        charlie_credentials = base64.b64encode(b"Charlie:password").decode("utf-8")
        charlie_headers = {"Authorization": f"Basic {charlie_credentials}"}
        response = self.client.post(
            f"/games/{game_id}/players",
            json={},
            headers=charlie_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "in_progress"  # Game automatically started with 3 players
        assert len(data["players"]) == 3
        
        # Charlie should see his tiles (returned view is for Charlie)
        charlie = next(p for p in data["players"] if p["name"] == "Charlie")
        assert charlie["rack"] is not None
        assert len(charlie["rack"]["tiles"]) == 14
        
        # Other players' racks should be hidden from Charlie's view  
        alice = next(p for p in data["players"] if p["name"] == "Alice")
        assert alice["rack"] is None
        bob = next(p for p in data["players"] if p["name"] == "Bob")
        assert bob["rack"] is None
        assert alice["rack_size"] == 14
    
    def test_join_game_invalid_name(self):
        """Test joining game with invalid player name (empty username in Auth header)."""
        import base64
        
        # Create game with Alice as creator
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        create_response = self.client.post("/games", json={"num_players": 2}, headers=headers)
        game_id = create_response.json()["game_id"]
        
        # Empty name in Auth header - this should be caught by auth validation
        empty_credentials = base64.b64encode(b":password").decode("utf-8")
        empty_headers = {"Authorization": f"Basic {empty_credentials}"}
        response = self.client.post(
            f"/games/{game_id}/players",
            json={},
            headers=empty_headers
        )
        assert response.status_code == 401  # Auth validation error
    
    def test_join_nonexistent_game(self):
        """Test joining non-existent game."""
        import base64
        
        # Try to join with Basic Auth
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        response = self.client.post(
            "/games/nonexistent-id/players",
            json={},
            headers=headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "GAME_NOT_FOUND"
    
    def test_get_game_state_player_view(self):
        """Test getting game state from player's perspective."""
        import base64
        
        # Create game with Alice as creator (auto-joined)
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        create_response = self.client.post("/games", json={"num_players": 2}, headers=headers)
        game_id = create_response.json()["game_id"]
        alice_id = create_response.json()["players"][0]["id"]
        
        # Bob joins
        bob_credentials = base64.b64encode(b"Bob:password").decode("utf-8")
        bob_headers = {"Authorization": f"Basic {bob_credentials}"}
        self.client.post(
            f"/games/{game_id}/players",
            json={},
            headers=bob_headers
        )
        
        # Get Alice's view
        response = self.client.get(f"/games/{game_id}/players/{alice_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Alice should see her tiles
        alice = next(p for p in data["players"] if p["name"] == "Alice")
        assert alice["rack"] is not None
        assert len(alice["rack"]["tiles"]) == 14
        
        # Bob's tiles should be hidden from Alice
        bob = next(p for p in data["players"] if p["name"] == "Bob")
        assert bob["rack"] is None
        assert bob["rack_size"] == 14
    
    def test_get_game_state_nonexistent_game(self):
        """Test getting game state for non-existent game."""
        response = self.client.get("/games/nonexistent/players/player-id")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "GAME_NOT_FOUND"
    
    def test_get_game_state_player_not_in_game(self):
        """Test getting game state for player not in game."""
        import base64
        
        # Create game with Alice as creator (auto-joined)
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        create_response = self.client.post("/games", json={"num_players": 2}, headers=headers)
        game_id = create_response.json()["game_id"]
        
        # Try to get state for non-existent player
        response = self.client.get(f"/games/{game_id}/players/fake-player-id")
        
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "PLAYER_NOT_IN_GAME"
    
    def test_draw_tile_action(self):
        """Test draw tile action endpoint."""
        import base64
        
        # Create game with Alice as creator (auto-joined)
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        create_response = self.client.post("/games", json={"num_players": 2}, headers=headers)
        game_id = create_response.json()["game_id"]
        alice_id = create_response.json()["players"][0]["id"]
        
        # Start game by adding second player
        bob_credentials = base64.b64encode(b"Bob:password").decode("utf-8")
        bob_headers = {"Authorization": f"Basic {bob_credentials}"}
        self.client.post(f"/games/{game_id}/players", json={}, headers=bob_headers)
        
        # Draw tile (Alice's turn)
        response = self.client.post(
            f"/games/{game_id}/players/{alice_id}/actions/draw",
            json={}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Alice should now have 15 tiles (14 + 1 drawn)
        alice = next(p for p in data["players"] if p["name"] == "Alice")
        assert len(alice["rack"]["tiles"]) == 15
        
        # Should be Bob's turn now
        assert data["current_player_index"] == 1
    
    def test_play_tiles_valid_meld(self):
        """Test play tiles action with valid meld."""
        import base64
        
        # Create game with Alice as creator (auto-joined)
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        create_response = self.client.post("/games", json={"num_players": 2}, headers=headers)
        game_id = create_response.json()["game_id"]
        alice_id = create_response.json()["players"][0]["id"]
        
        # Start game by adding second player
        bob_credentials = base64.b64encode(b"Bob:password").decode("utf-8")
        bob_headers = {"Authorization": f"Basic {bob_credentials}"}
        self.client.post(f"/games/{game_id}/players", json={}, headers=bob_headers)
        
        # Get Alice's tiles to construct a valid meld
        state_response = self.client.get(f"/games/{game_id}/players/{alice_id}")
        alice_tiles = state_response.json()["players"][0]["rack"]["tiles"]
        
        # Try to play the first 3 tiles as a group
        # Note: Random tiles are unlikely to form a valid group, so we expect this to fail
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
            json=play_request
        )
        
        # Random tiles will almost certainly not form a valid meld
        # This test just verifies the endpoint returns proper error format
        # Should be a domain validation error (meld validation, initial meld, or tile ownership)
        assert response.status_code in [422, 400, 200]  # 200 if we get lucky with valid tiles
        if response.status_code != 200:
            data = response.json()
            assert "error" in data
            assert "code" in data["error"]
    
    def test_play_tiles_invalid_format(self):
        """Test play tiles with invalid request format."""
        import base64
        
        # Create game with Alice as creator (auto-joined)
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        create_response = self.client.post("/games", json={"num_players": 2}, headers=headers)
        game_id = create_response.json()["game_id"]
        alice_id = create_response.json()["players"][0]["id"]
        
        # Invalid meld format
        response = self.client.post(
            f"/games/{game_id}/players/{alice_id}/actions/play",
            json={"melds": [{"invalid": "format"}]}
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
        import base64
        
        # Create game without players first
        empty_game = self.create_sample_game_state(status=GameStatus.WAITING_FOR_PLAYERS)
        empty_game.players = []
        self.mock_service.create_game.return_value = empty_game
        
        # Mock join to return game with Alice
        joined_game = self.create_sample_game_state(status=GameStatus.WAITING_FOR_PLAYERS)
        self.mock_service.join_game.return_value = joined_game
        
        # Add Basic Auth header
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        response = self.client.post("/games", json={"num_players": 3}, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == "12345678-1234-5678-1234-567812345678"
        
        self.mock_service.create_game.assert_called_once_with(3)
        self.mock_service.join_game.assert_called_once()  # Verify auto-join was called
    
    def test_join_game_mocked(self):
        """Test join game endpoint with mocked service."""
        import base64
        
        sample_game = self.create_sample_game_state()
        self.mock_service.join_game.return_value = sample_game
        self.mock_service._load_game_state.side_effect = GameNotFoundError("Not found")
        
        # Add Basic Auth header
        credentials = base64.b64encode(b"Charlie:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        response = self.client.post(
            "/games/12345678-1234-5678-1234-567812345678/players",
            json={},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == "12345678-1234-5678-1234-567812345678"
        
        self.mock_service.join_game.assert_called_once_with("12345678-1234-5678-1234-567812345678", "Charlie")
    
    def test_get_games_mocked(self):
        """Test get games endpoint with mocked service."""
        import base64
        
        sample_games = [
            self.create_sample_game_state("12345678-1234-5678-1234-567812345671"),
            self.create_sample_game_state("12345678-1234-5678-1234-567812345672")
        ]
        self.mock_service.get_games.return_value = sample_games
        
        # Add Basic Auth header
        credentials = base64.b64encode(b"TestUser:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        response = self.client.get("/games", headers=headers)
        
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
        import base64
        
        self.mock_service.join_game.side_effect = GameNotFoundError("Game not found")
        
        # Add Basic Auth header
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        response = self.client.post(
            "/games/nonexistent/players",
            json={},
            headers=headers
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


class TestNewAPIEndpoints:
    """Tests for new API endpoints: my-games, auto-join, and status filtering."""
    
    def setup_method(self):
        """Set up test environment with mocked service."""
        self.mock_service = Mock(spec=GameService)
        
        def override_get_game_service():
            return self.mock_service
        
        from src.rummikub.api.dependencies import get_game_service
        app.dependency_overrides[get_game_service] = override_get_game_service
        
        self.client = TestClient(app)
    
    def teardown_method(self):
        """Clean up after each test."""
        app.dependency_overrides.clear()
    
    def create_sample_game_state(self, game_id="12345678-1234-5678-1234-567812345678", status=GameStatus.IN_PROGRESS, players_data=None):
        """Helper to create sample game state with custom players."""
        from uuid import UUID, uuid4
        
        if players_data is None:
            players_data = [
                ("player-1", "Alice"),
                ("player-2", "Bob")
            ]
        
        players = []
        for player_id, player_name in players_data:
            players.append(Player(
                id=player_id,
                name=player_name,
                initial_meld_met=False,
                rack=Rack(tile_ids=["1ra", "2ra", "3ra"])
            ))
        
        # Generate a valid UUID from the game_id string
        if isinstance(game_id, str) and not game_id.count('-') == 4:
            # If it's a simple string like "game-1", create a valid UUID
            game_uuid = uuid4()
        else:
            game_uuid = UUID(game_id) if isinstance(game_id, str) else game_id
        
        return GameState(
            game_id=game_uuid,
            players=players,
            current_player_index=0,
            pool=Pool(tile_ids=["3kb", "4kb", "5kb"]),
            board=Board(melds=[]),
            status=status,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_get_my_games_with_auth(self):
        """Test GET /games/my-games endpoint with Basic Auth."""
        import base64
        
        # Create sample games - some with Alice, some without
        game1 = self.create_sample_game_state("game-1", players_data=[("p1", "Alice"), ("p2", "Bob")])
        game2 = self.create_sample_game_state("game-2", players_data=[("p3", "Charlie"), ("p4", "Dave")])
        game3 = self.create_sample_game_state("game-3", players_data=[("p5", "Alice"), ("p6", "Eve")])
        
        self.mock_service.get_games.return_value = [game1, game2, game3]
        
        # Create Basic Auth header for Alice
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        response = self.client.get("/games/my-games", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["games"]) == 2  # Only game1 and game3 where Alice is a player
        
        # Verify Alice is in all returned games
        for game_data in data["games"]:
            player_names = [p["name"] for p in game_data["players"]]
            assert "Alice" in player_names
    
    def test_get_my_games_no_auth(self):
        """Test GET /games/my-games endpoint without authentication."""
        response = self.client.get("/games/my-games")
        
        assert response.status_code == 401
        data = response.json()
        assert "Authorization" in data["detail"] or "authorization" in data["detail"].lower()
    
    def test_get_my_games_empty(self):
        """Test GET /games/my-games when player has no games."""
        import base64
        
        # Create sample games without Alice
        game1 = self.create_sample_game_state("game-1", players_data=[("p1", "Bob"), ("p2", "Charlie")])
        
        self.mock_service.get_games.return_value = [game1]
        
        # Create Basic Auth header for Alice
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        response = self.client.get("/games/my-games", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["games"]) == 0
    
    def test_create_game_with_auto_join(self):
        """Test POST /games endpoint with auto-join functionality."""
        import base64
        
        # Mock the create_game to return a game without players
        empty_game = self.create_sample_game_state(status=GameStatus.WAITING_FOR_PLAYERS, players_data=[])
        self.mock_service.create_game.return_value = empty_game
        
        # Mock join_game to return game with Alice joined
        joined_game = self.create_sample_game_state(players_data=[("player-1", "Alice")])
        self.mock_service.join_game.return_value = joined_game
        
        # Create Basic Auth header for Alice
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        response = self.client.post("/games", json={"num_players": 4}, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify create_game was called
        self.mock_service.create_game.assert_called_once_with(4)
        
        # Verify join_game was called with the game_id and player name
        self.mock_service.join_game.assert_called_once()
        join_args = self.mock_service.join_game.call_args
        assert join_args[0][1] == "Alice"  # player_name
        
        # Verify response includes the joined player
        assert len(data["players"]) == 1
        assert data["players"][0]["name"] == "Alice"
    
    def test_create_game_no_auth(self):
        """Test POST /games endpoint without authentication."""
        response = self.client.post("/games", json={"num_players": 2})
        
        assert response.status_code == 401
        data = response.json()
        assert "Authorization" in data["detail"] or "authorization" in data["detail"].lower()
    
    def test_get_games_with_status_filter(self):
        """Test GET /games endpoint with status query parameter."""
        import base64
        
        # Create games with different statuses
        game1 = self.create_sample_game_state("game-1", status=GameStatus.WAITING_FOR_PLAYERS)
        game2 = self.create_sample_game_state("game-2", status=GameStatus.IN_PROGRESS)
        game3 = self.create_sample_game_state("game-3", status=GameStatus.WAITING_FOR_PLAYERS)
        
        self.mock_service.get_games.return_value = [game1, game2, game3]
        
        # Add Basic Auth header
        credentials = base64.b64encode(b"TestUser:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        # Test filtering by waiting_for_players
        response = self.client.get("/games?status=waiting_for_players", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["games"]) == 2  # Only game1 and game3
        for game in data["games"]:
            assert game["status"] == "waiting_for_players"
    
    def test_get_games_with_invalid_status_filter(self):
        """Test GET /games endpoint with invalid status filter."""
        import base64
        
        game1 = self.create_sample_game_state("game-1", status=GameStatus.IN_PROGRESS)
        
        self.mock_service.get_games.return_value = [game1]
        
        # Add Basic Auth header
        credentials = base64.b64encode(b"TestUser:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        # Test with invalid status - should ignore filter and return all
        response = self.client.get("/games?status=invalid_status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["games"]) == 1  # Returns all games when filter is invalid
    
    def test_get_games_without_status_filter(self):
        """Test GET /games endpoint without status filter (backward compatibility)."""
        import base64
        
        game1 = self.create_sample_game_state("game-1", status=GameStatus.WAITING_FOR_PLAYERS)
        game2 = self.create_sample_game_state("game-2", status=GameStatus.IN_PROGRESS)
        
        self.mock_service.get_games.return_value = [game1, game2]
        
        # Add Basic Auth header
        credentials = base64.b64encode(b"TestUser:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        response = self.client.get("/games", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["games"]) == 2  # Returns all games