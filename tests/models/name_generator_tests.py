"""Tests for game name generator."""

from rummikub.models import GameNameGenerator


class TestGameNameGenerator:
    """Test game name generator functionality."""
    
    def test_generate_name(self):
        """Test name generation."""
        name = GameNameGenerator.generate()
        
        # Check format: "[Action] [Preposition] [Location]"
        parts = name.split(" ", 2)
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}: {name}"
        
        action, preposition, location = parts
        assert action in GameNameGenerator.ACTIONS
        assert preposition in GameNameGenerator.PREPOSITIONS
        assert location in GameNameGenerator.LOCATIONS
    
    def test_generate_multiple_names_are_valid(self):
        """Test that multiple generated names are all valid."""
        for _ in range(10):
            name = GameNameGenerator.generate()
            parts = name.split(" ", 2)
            assert len(parts) == 3
            assert isinstance(name, str)
            assert len(name) > 0
    
    def test_names_can_vary(self):
        """Test that name generation produces variety."""
        # Generate multiple names and check we get at least some variety
        names = set()
        for _ in range(100):
            names.add(GameNameGenerator.generate())
        
        # With 23 actions, 5 prepositions, and 22 locations,
        # we have 2530 possible combinations
        # After 100 generations, we should have at least 50 unique names
        assert len(names) >= 50, f"Expected at least 50 unique names, got {len(names)}"
    
    def test_word_lists(self):
        """Test that word lists are properly merged."""
        # Check all words are present (spot checking from each original theme)
        
        # Fantasy words
        assert "Quest" in GameNameGenerator.ACTIONS
        assert "Gondor" in GameNameGenerator.LOCATIONS
        
        # Sci-fi words
        assert "Incursion" in GameNameGenerator.ACTIONS
        assert "Mars" in GameNameGenerator.LOCATIONS
        assert "on" in GameNameGenerator.PREPOSITIONS
        
        # Classic words
        assert "Battle" in GameNameGenerator.ACTIONS
        assert "Tokyo" in GameNameGenerator.LOCATIONS
        assert "in" in GameNameGenerator.PREPOSITIONS
    
    def test_word_list_sizes(self):
        """Test that merged word lists have expected sizes."""
        # 22 unique actions (6 fantasy + 5 scifi + 15 classic - 4 duplicates: Siege, Defense, Quest x2)
        assert len(GameNameGenerator.ACTIONS) == 22
        
        # 5 unique prepositions
        assert len(GameNameGenerator.PREPOSITIONS) == 5
        
        # 22 locations (5 fantasy + 5 scifi + 12 classic)
        assert len(GameNameGenerator.LOCATIONS) == 22
