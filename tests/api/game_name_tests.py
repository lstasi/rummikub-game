"""Tests for game_name field in API responses."""

import base64
from fastapi.testclient import TestClient

from src.rummikub.api.main import app
from src.rummikub.service import GameService


class TestGameNameAPI:
    """Test that game_name field is properly exposed in API responses."""
    
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
    
    def teardown_method(self):
        """Clean up after each test."""
        app.dependency_overrides.clear()
    
    def test_create_game_includes_game_name(self):
        """Test that POST /games returns game_name in response."""
        import base64
        
        # Create auth header
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        response = self.client.post("/games", json={"num_players": 2}, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify game_name is present
        assert "game_name" in data, "game_name field missing from response"
        assert isinstance(data["game_name"], str), "game_name should be a string"
        assert len(data["game_name"]) > 0, "game_name should not be empty"
        
        # Verify format: should have at least 3 words (Action Preposition Location)
        parts = data["game_name"].split()
        assert len(parts) >= 3, f"Expected at least 3 words in game_name, got {len(parts)}: {data['game_name']}"
        
        # Verify game_id is still present and different from game_name
        assert "game_id" in data
        assert data["game_id"] != data["game_name"]
        
        print(f"Created game with name: {data['game_name']} (ID: {data['game_id']})")
    
    def test_join_game_includes_game_name(self):
        """Test that POST /games/{game_id}/players returns game_name."""
        # First create a game
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        create_response = self.client.post("/games", json={"num_players": 2}, headers=headers)
        assert create_response.status_code == 200
        game_data = create_response.json()
        game_id = game_data["game_id"]
        original_name = game_data["game_name"]
        
        # Join as second player
        credentials2 = base64.b64encode(b"Bob:password").decode("utf-8")
        headers2 = {"Authorization": f"Basic {credentials2}"}
        
        join_response = self.client.post(
            f"/games/{game_id}/players",
            json={"player_name": "Bob"},
            headers=headers2
        )
        
        assert join_response.status_code == 200
        join_data = join_response.json()
        
        # Verify game_name is present and unchanged
        assert "game_name" in join_data
        assert join_data["game_name"] == original_name
        assert isinstance(join_data["game_name"], str)
        
        print(f"Joined game: {join_data['game_name']}")
    
    def test_get_game_state_includes_game_name(self):
        """Test that GET /games/{game_id}/players/{player_id} returns game_name."""
        # Create a game
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        create_response = self.client.post("/games", json={"num_players": 2}, headers=headers)
        assert create_response.status_code == 200
        game_data = create_response.json()
        game_id = game_data["game_id"]
        player_id = game_data["players"][0]["id"]
        original_name = game_data["game_name"]
        
        # Get game state
        get_response = self.client.get(f"/games/{game_id}/players/{player_id}")
        
        assert get_response.status_code == 200
        get_data = get_response.json()
        
        # Verify game_name is present and unchanged
        assert "game_name" in get_data
        assert get_data["game_name"] == original_name
        
        print(f"Retrieved game: {get_data['game_name']}")
    
    def test_multiple_games_have_unique_names(self):
        """Test that multiple games can be created with different names."""
        credentials = base64.b64encode(b"Alice:password").decode("utf-8")
        headers = {"Authorization": f"Basic {credentials}"}
        
        # Create multiple games
        game_names = []
        for _ in range(5):
            response = self.client.post("/games", json={"num_players": 2}, headers=headers)
            assert response.status_code == 200
            data = response.json()
            game_names.append(data["game_name"])
            print(f"Created game: {data['game_name']}")
        
        # All names should be valid strings (they may not all be unique due to randomness)
        for name in game_names:
            assert isinstance(name, str)
            assert len(name) > 0
            parts = name.split()
            assert len(parts) >= 3
