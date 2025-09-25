"""Tests for API endpoints using FastAPI TestClient."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
import fakeredis

from src.rummikub.api import app
from src.rummikub.service import GameService
from src.rummikub.models import GameState, Player, Rack, GameStatus
from src.rummikub.service.exceptions import GameNotFoundError


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def mock_game_service(mock_redis):
    """Mock GameService for testing."""
    return GameService(mock_redis)


@pytest.fixture
def client(mock_game_service):
    """FastAPI TestClient with dependency overrides."""
    
    def override_get_game_service():
        return mock_game_service
    
    # Override the dependency
    from src.rummikub.api.dependencies import get_game_service
    app.dependency_overrides[get_game_service] = override_get_game_service
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_game_state():
    """Sample game state for testing."""
    from datetime import datetime
    from src.rummikub.models import Board, Pool
    
    player1 = Player(
        id="player-1",
        name="Alice",
        initial_meld_met=False,
        rack=Rack(tile_ids=["1ra", "2ra", "3ra"])
    )
    
    player2 = Player(
        id="player-2", 
        name="Bob",
        initial_meld_met=False,
        rack=Rack(tile_ids=["4kb", "5kb", "6kb"])
    )
    
    return GameState(
        game_id="test-game-id",
        players=[player1, player2],
        current_player_index=0,
        pool=Pool(tile_ids=["7ro", "8ro", "9ro"]),
        board=Board(melds=[]),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        status=GameStatus.IN_PROGRESS
    )


class TestGamesList:
    """Tests for GET /api/v1/games endpoint."""
    
    def test_get_games_empty_list(self, client, mock_game_service):
        """Test getting empty games list."""
        mock_game_service.get_games = Mock(return_value=[])
        
        response = client.get("/api/v1/games")
        
        assert response.status_code == 200
        data = response.json()
        assert data == {"games": []}

    def test_get_games_with_games(self, client, mock_game_service, sample_game_state):
        """Test getting games list with games."""
        mock_game_service.get_games = Mock(return_value=[sample_game_state])
        
        response = client.get("/api/v1/games")
        
        assert response.status_code == 200
        data = response.json()
        assert "games" in data
        assert len(data["games"]) == 1
        
        game = data["games"][0]
        assert game["game_id"] == "test-game-id"
        assert game["status"] == "in_progress"
        assert len(game["players"]) == 2
        
        # Check that rack details are hidden in list view
        for player in game["players"]:
            assert "rack" not in player or player["rack"] is None
            assert "rack_size" in player


class TestCreateGame:
    """Tests for POST /api/v1/games endpoint."""
    
    def test_create_game_success(self, client, mock_game_service, sample_game_state):
        """Test successful game creation."""
        mock_game_service.create_game = Mock(return_value=sample_game_state)
        
        response = client.post("/api/v1/games", json={"num_players": 2})
        
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == "test-game-id"
        assert data["status"] == "in_progress"
        
        mock_game_service.create_game.assert_called_once_with(2)

    def test_create_game_invalid_players(self, client):
        """Test game creation with invalid number of players."""
        response = client.post("/api/v1/games", json={"num_players": 1})
        
        assert response.status_code == 422  # Validation error
        
        response = client.post("/api/v1/games", json={"num_players": 5})
        
        assert response.status_code == 422  # Validation error


class TestJoinGame:
    """Tests for POST /api/v1/games/{game_id}/players endpoint."""
    
    def test_join_game_success(self, client, mock_game_service, sample_game_state):
        """Test successful game joining."""
        mock_game_service.join_game = Mock(return_value=sample_game_state)
        
        response = client.post(
            "/api/v1/games/test-game-id/players",
            json={"player_name": "Charlie"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == "test-game-id"
        
        mock_game_service.join_game.assert_called_once_with("test-game-id", "Charlie")

    def test_join_game_not_found(self, client, mock_game_service):
        """Test joining non-existent game."""
        mock_game_service.join_game = Mock(side_effect=GameNotFoundError("Game not found"))
        
        response = client.post(
            "/api/v1/games/nonexistent/players",
            json={"player_name": "Charlie"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "GAME_NOT_FOUND"

    def test_join_game_invalid_name(self, client):
        """Test joining game with invalid player name."""
        response = client.post(
            "/api/v1/games/test-game-id/players",
            json={"player_name": ""}
        )
        
        assert response.status_code == 422  # Validation error


class TestGetGameState:
    """Tests for GET /api/v1/games/{game_id}/players/{player_id} endpoint."""
    
    def test_get_game_state_success(self, client, mock_game_service, sample_game_state):
        """Test successful game state retrieval."""
        mock_game_service.get_games = Mock(return_value=[sample_game_state])
        mock_game_service.get_game = Mock(return_value=sample_game_state)
        
        response = client.get("/api/v1/games/test-game-id/players/player-1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == "test-game-id"
        
        # Check that the requesting player's rack is shown
        requesting_player = next(p for p in data["players"] if p["id"] == "player-1")
        assert "rack" in requesting_player
        assert requesting_player["rack"] is not None
        
        # Check that other players' racks are hidden
        other_player = next(p for p in data["players"] if p["id"] == "player-2")
        assert "rack_size" in other_player
        assert other_player["rack"] is None

    def test_get_game_state_game_not_found(self, client, mock_game_service):
        """Test getting state for non-existent game."""
        mock_game_service.get_games = Mock(return_value=[])
        
        response = client.get("/api/v1/games/nonexistent/players/player-1")
        
        assert response.status_code == 404

    def test_get_game_state_player_not_in_game(self, client, mock_game_service, sample_game_state):
        """Test getting state for player not in game."""
        mock_game_service.get_games = Mock(return_value=[sample_game_state])
        
        response = client.get("/api/v1/games/test-game-id/players/nonexistent-player")
        
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "PLAYER_NOT_IN_GAME"


class TestPlayTiles:
    """Tests for POST /api/v1/games/{game_id}/players/{player_id}/actions/play endpoint."""
    
    def test_play_tiles_success(self, client, mock_game_service, sample_game_state):
        """Test successful tile play."""
        mock_game_service.execute_turn = Mock(return_value=sample_game_state)
        
        play_request = {
            "melds": [
                {
                    "id": "meld-1",
                    "kind": "group", 
                    "tiles": ["1ra", "1kb", "1bo"]
                }
            ]
        }
        
        response = client.post(
            "/api/v1/games/test-game-id/players/player-1/actions/play",
            json=play_request
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == "test-game-id"
        
        # Verify that execute_turn was called with correct parameters
        mock_game_service.execute_turn.assert_called_once()
        args = mock_game_service.execute_turn.call_args
        assert args[0][0] == "test-game-id"  # game_id
        assert args[0][1] == "player-1"      # player_id
        assert hasattr(args[0][2], "melds")  # action has melds attribute

    def test_play_tiles_invalid_meld(self, client, mock_game_service):
        """Test play tiles with invalid meld."""
        from src.rummikub.models.exceptions import InvalidMeldError
        
        mock_game_service.execute_turn = Mock(
            side_effect=InvalidMeldError("Invalid meld: not enough tiles")
        )
        
        play_request = {
            "melds": [
                {
                    "id": "meld-1",
                    "kind": "group",
                    "tiles": ["1ra", "1kb"]  # Only 2 tiles, invalid for group
                }
            ]
        }
        
        response = client.post(
            "/api/v1/games/test-game-id/players/player-1/actions/play",
            json=play_request
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "INVALID_MELD"


class TestDrawTile:
    """Tests for POST /api/v1/games/{game_id}/players/{player_id}/actions/draw endpoint."""
    
    def test_draw_tile_success(self, client, mock_game_service, sample_game_state):
        """Test successful tile draw."""
        mock_game_service.execute_turn = Mock(return_value=sample_game_state)
        
        response = client.post(
            "/api/v1/games/test-game-id/players/player-1/actions/draw",
            json={}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == "test-game-id"
        
        # Verify that execute_turn was called with draw action
        mock_game_service.execute_turn.assert_called_once()
        args = mock_game_service.execute_turn.call_args
        assert args[0][0] == "test-game-id"  # game_id
        assert args[0][1] == "player-1"      # player_id
        assert args[0][2].type == "draw"     # action type

    def test_draw_tile_pool_empty(self, client, mock_game_service):
        """Test drawing tile from empty pool."""
        from src.rummikub.models.exceptions import PoolEmptyError
        
        mock_game_service.execute_turn = Mock(side_effect=PoolEmptyError("Pool is empty"))
        
        response = client.post(
            "/api/v1/games/test-game-id/players/player-1/actions/draw",
            json={}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "POOL_EMPTY"


class TestHealthCheck:
    """Tests for /health endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "healthy"}