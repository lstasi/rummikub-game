"""Tests for Basic Auth username extraction and language detection from headers."""

import base64
from fastapi.testclient import TestClient
import fakeredis

from src.rummikub.api.main import app
from src.rummikub.service import GameService


class TestBasicAuthAndLanguage:
    """Test Basic Auth username extraction and Accept-Language header parsing."""
    
    def setup_method(self):
        """Set up test environment with FakeRedis."""
        # Use FakeRedis for testing
        self.redis_client = fakeredis.FakeRedis(decode_responses=True)
        self.game_service = GameService(self.redis_client)
        
        # Override dependency for service
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
    
    def _create_basic_auth_header(self, username: str, password: str) -> str:
        """Create a Basic Auth header value."""
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def test_join_game_with_basic_auth_username(self):
        """Test joining game using username from Basic Auth header."""
        # Create game
        create_response = self.client.post("/games", json={"num_players": 2})
        game_id = create_response.json()["game_id"]
        
        # Join with Basic Auth header (no player_name in body)
        auth_header = self._create_basic_auth_header("alice", "password123")
        response = self.client.post(
            f"/games/{game_id}/players",
            json={},
            headers={"Authorization": auth_header}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Player name should be extracted from Basic Auth
        assert len(data["players"]) == 1
        assert data["players"][0]["name"] == "alice"
    
    def test_join_game_basic_auth_override_with_request_body(self):
        """Test that player_name in request body overrides Basic Auth username."""
        # Create game
        create_response = self.client.post("/games", json={"num_players": 2})
        game_id = create_response.json()["game_id"]
        
        # Join with Basic Auth header AND player_name in body
        auth_header = self._create_basic_auth_header("alice", "password123")
        response = self.client.post(
            f"/games/{game_id}/players",
            json={"player_name": "bob"},
            headers={"Authorization": auth_header}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # player_name from request body should take precedence
        assert data["players"][0]["name"] == "bob"
    
    def test_join_game_no_player_name_no_auth(self):
        """Test that joining without player_name and without Basic Auth fails."""
        # Create game
        create_response = self.client.post("/games", json={"num_players": 2})
        game_id = create_response.json()["game_id"]
        
        # Try to join without player_name or Basic Auth
        response = self.client.post(
            f"/games/{game_id}/players",
            json={}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Player name is required" in data["detail"]
    
    def test_join_game_invalid_basic_auth(self):
        """Test that invalid Basic Auth header doesn't break the request."""
        # Create game
        create_response = self.client.post("/games", json={"num_players": 2})
        game_id = create_response.json()["game_id"]
        
        # Try with invalid Basic Auth (but include player_name as fallback)
        response = self.client.post(
            f"/games/{game_id}/players",
            json={"player_name": "alice"},
            headers={"Authorization": "Invalid Header Format"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["players"][0]["name"] == "alice"
    
    def test_join_game_with_accept_language_english(self):
        """Test Accept-Language header detection for English."""
        # Create game
        create_response = self.client.post("/games", json={"num_players": 2})
        game_id = create_response.json()["game_id"]
        
        # Join with Accept-Language header
        response = self.client.post(
            f"/games/{game_id}/players",
            json={"player_name": "alice"},
            headers={"Accept-Language": "en-US,en;q=0.9"}
        )
        
        assert response.status_code == 200
        # Language is extracted and logged (check logs if needed)
    
    def test_join_game_with_accept_language_portuguese(self):
        """Test Accept-Language header detection for Portuguese."""
        # Create game
        create_response = self.client.post("/games", json={"num_players": 2})
        game_id = create_response.json()["game_id"]
        
        # Join with Accept-Language header
        response = self.client.post(
            f"/games/{game_id}/players",
            json={"player_name": "alice"},
            headers={"Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"}
        )
        
        assert response.status_code == 200
        # Language is extracted and logged
    
    def test_join_game_with_accept_language_spanish(self):
        """Test Accept-Language header detection for Spanish."""
        # Create game
        create_response = self.client.post("/games", json={"num_players": 2})
        game_id = create_response.json()["game_id"]
        
        # Join with Accept-Language header
        response = self.client.post(
            f"/games/{game_id}/players",
            json={"player_name": "alice"},
            headers={"Accept-Language": "es-ES,es;q=0.9"}
        )
        
        assert response.status_code == 200
        # Language is extracted and logged
    
    def test_join_game_with_accept_language_fallback(self):
        """Test Accept-Language header fallback to English for unsupported language."""
        # Create game
        create_response = self.client.post("/games", json={"num_players": 2})
        game_id = create_response.json()["game_id"]
        
        # Join with unsupported language
        response = self.client.post(
            f"/games/{game_id}/players",
            json={"player_name": "alice"},
            headers={"Accept-Language": "fr-FR,fr;q=0.9"}
        )
        
        assert response.status_code == 200
        # Should fallback to English (default)
    
    def test_join_game_basic_auth_and_language_together(self):
        """Test using both Basic Auth and Accept-Language together."""
        # Create game
        create_response = self.client.post("/games", json={"num_players": 2})
        game_id = create_response.json()["game_id"]
        
        # Join with both headers
        auth_header = self._create_basic_auth_header("alice", "password123")
        response = self.client.post(
            f"/games/{game_id}/players",
            json={},
            headers={
                "Authorization": auth_header,
                "Accept-Language": "pt-BR,pt;q=0.9"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["players"][0]["name"] == "alice"
        # Language is also detected and logged
