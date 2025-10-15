"""Tests for game name generator."""

import pytest
from rummikub.models import GameNameGenerator


class TestGameNameGenerator:
    """Test game name generator functionality."""
    
    def test_generate_fantasy_theme(self):
        """Test fantasy theme name generation."""
        name = GameNameGenerator.generate("fantasy")
        
        # Check format: "[Action] [Preposition] [Location]"
        parts = name.split(" ", 2)
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}: {name}"
        
        action, preposition, location = parts
        assert action in GameNameGenerator.FANTASY_ACTIONS
        assert preposition in GameNameGenerator.FANTASY_PREPOSITIONS
        assert location in GameNameGenerator.FANTASY_LOCATIONS
    
    def test_generate_scifi_theme(self):
        """Test sci-fi theme name generation."""
        name = GameNameGenerator.generate("scifi")
        
        parts = name.split(" ", 2)
        assert len(parts) == 3
        
        action, preposition, location = parts
        assert action in GameNameGenerator.SCIFI_ACTIONS
        assert preposition in GameNameGenerator.SCIFI_PREPOSITIONS
        assert location in GameNameGenerator.SCIFI_LOCATIONS
    
    def test_generate_classic_theme(self):
        """Test classic theme name generation."""
        name = GameNameGenerator.generate("classic")
        
        parts = name.split(" ", 2)
        assert len(parts) == 3
        
        action, preposition, location = parts
        assert action in GameNameGenerator.CLASSIC_ACTIONS
        assert preposition in GameNameGenerator.CLASSIC_PREPOSITIONS
        assert location in GameNameGenerator.CLASSIC_LOCATIONS
    
    def test_generate_default_theme(self):
        """Test that default theme is fantasy."""
        name = GameNameGenerator.generate()
        
        parts = name.split(" ", 2)
        assert len(parts) == 3
        
        action, preposition, location = parts
        assert action in GameNameGenerator.FANTASY_ACTIONS
        assert preposition in GameNameGenerator.FANTASY_PREPOSITIONS
        assert location in GameNameGenerator.FANTASY_LOCATIONS
    
    def test_generate_invalid_theme(self):
        """Test that invalid theme raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            GameNameGenerator.generate("invalid_theme")  # type: ignore
        
        assert "Unsupported theme" in str(exc_info.value)
        assert "invalid_theme" in str(exc_info.value)
    
    def test_generate_multiple_names_are_valid(self):
        """Test that multiple generated names are all valid."""
        for _ in range(10):
            # Test all themes
            for theme in ["fantasy", "scifi", "classic"]:
                name = GameNameGenerator.generate(theme)  # type: ignore
                parts = name.split(" ", 2)
                assert len(parts) == 3
                assert isinstance(name, str)
                assert len(name) > 0
    
    def test_names_can_vary(self):
        """Test that name generation produces variety."""
        # Generate multiple names and check we get at least some variety
        names = set()
        for _ in range(50):
            names.add(GameNameGenerator.generate("fantasy"))
        
        # With 6 actions, 3 prepositions, and 5 locations, we have 90 possible combinations
        # After 50 generations, we should have at least 20 unique names
        assert len(names) >= 20, f"Expected at least 20 unique names, got {len(names)}"
    
    def test_fantasy_theme_word_lists(self):
        """Test that fantasy theme has expected word lists."""
        assert len(GameNameGenerator.FANTASY_ACTIONS) == 6
        assert len(GameNameGenerator.FANTASY_PREPOSITIONS) == 3
        assert len(GameNameGenerator.FANTASY_LOCATIONS) == 5
        
        # Spot check some expected words
        assert "Quest" in GameNameGenerator.FANTASY_ACTIONS
        assert "of" in GameNameGenerator.FANTASY_PREPOSITIONS
        assert "Gondor" in GameNameGenerator.FANTASY_LOCATIONS
    
    def test_scifi_theme_word_lists(self):
        """Test that sci-fi theme has expected word lists."""
        assert len(GameNameGenerator.SCIFI_ACTIONS) == 5
        assert len(GameNameGenerator.SCIFI_PREPOSITIONS) == 3
        assert len(GameNameGenerator.SCIFI_LOCATIONS) == 5
        
        # Spot check some expected words
        assert "Incursion" in GameNameGenerator.SCIFI_ACTIONS
        assert "on" in GameNameGenerator.SCIFI_PREPOSITIONS
        assert "Mars" in GameNameGenerator.SCIFI_LOCATIONS
    
    def test_classic_theme_word_lists(self):
        """Test that classic theme has expected word lists."""
        assert len(GameNameGenerator.CLASSIC_ACTIONS) == 15
        assert len(GameNameGenerator.CLASSIC_PREPOSITIONS) == 4
        assert len(GameNameGenerator.CLASSIC_LOCATIONS) == 12
        
        # Spot check some expected words
        assert "Battle" in GameNameGenerator.CLASSIC_ACTIONS
        assert "in" in GameNameGenerator.CLASSIC_PREPOSITIONS
        assert "Tokyo" in GameNameGenerator.CLASSIC_LOCATIONS
