"""Tests for TileUtils functionality and string-based tile system."""

import pytest
from rummikub.models import Color, TileUtils, InvalidNumberError


class TestTileUtils:
    """Test TileUtils static methods for working with tile ID strings."""
    
    def test_create_numbered_tile_id(self):
        """Test creating numbered tile IDs."""
        tile_id = TileUtils.create_numbered_tile_id(7, Color.RED, 'a')
        assert tile_id == "7ra"
        
        tile_id = TileUtils.create_numbered_tile_id(13, Color.BLACK, 'b')
        assert tile_id == "13kb"
        
        tile_id = TileUtils.create_numbered_tile_id(1, Color.ORANGE, 'a')
        assert tile_id == "1oa"
    
    def test_create_numbered_tile_id_validation(self):
        """Test validation of numbered tile creation."""
        with pytest.raises(InvalidNumberError):
            TileUtils.create_numbered_tile_id(0, Color.RED, 'a')
        
        with pytest.raises(InvalidNumberError):
            TileUtils.create_numbered_tile_id(14, Color.RED, 'a')
        
        with pytest.raises(ValueError, match="Copy must be 'a' or 'b'"):
            TileUtils.create_numbered_tile_id(7, Color.RED, 'c')
    
    def test_create_joker_tile_id(self):
        """Test creating joker tile IDs."""
        joker_id = TileUtils.create_joker_tile_id('a')
        assert joker_id == "ja"
        
        joker_id = TileUtils.create_joker_tile_id('b')
        assert joker_id == "jb"
    
    def test_create_joker_tile_id_validation(self):
        """Test validation of joker tile creation."""
        with pytest.raises(ValueError, match="Copy must be 'a' or 'b'"):
            TileUtils.create_joker_tile_id('c')
    
    def test_is_joker(self):
        """Test joker detection."""
        assert TileUtils.is_joker("ja") is True
        assert TileUtils.is_joker("jb") is True
        assert TileUtils.is_joker("7ra") is False
        assert TileUtils.is_joker("13kb") is False
    
    def test_is_numbered(self):
        """Test numbered tile detection."""
        assert TileUtils.is_numbered("7ra") is True
        assert TileUtils.is_numbered("13kb") is True
        assert TileUtils.is_numbered("1oa") is True
        assert TileUtils.is_numbered("ja") is False
        assert TileUtils.is_numbered("jb") is False
    
    def test_get_number(self):
        """Test extracting number from numbered tiles."""
        assert TileUtils.get_number("7ra") == 7
        assert TileUtils.get_number("13kb") == 13
        assert TileUtils.get_number("1oa") == 1
        assert TileUtils.get_number("10ba") == 10
    
    def test_get_number_with_joker_raises(self):
        """Test that getting number from joker raises error."""
        with pytest.raises(ValueError, match="Cannot get number from joker tile"):
            TileUtils.get_number("ja")
    
    def test_get_color(self):
        """Test extracting color from numbered tiles."""
        assert TileUtils.get_color("7ra") == Color.RED
        assert TileUtils.get_color("13kb") == Color.BLACK
        assert TileUtils.get_color("1oa") == Color.ORANGE
        assert TileUtils.get_color("10ba") == Color.BLUE
    
    def test_get_color_with_joker_raises(self):
        """Test that getting color from joker raises error."""
        with pytest.raises(ValueError, match="Cannot get color from joker tile"):
            TileUtils.get_color("ja")
    
    def test_get_copy(self):
        """Test extracting copy identifier."""
        assert TileUtils.get_copy("7ra") == "a"
        assert TileUtils.get_copy("13kb") == "b"
        assert TileUtils.get_copy("ja") == "a"
        assert TileUtils.get_copy("jb") == "b"
    
    def test_get_value(self):
        """Test getting point value from numbered tiles."""
        assert TileUtils.get_value("7ra") == 7
        assert TileUtils.get_value("13kb") == 13
        assert TileUtils.get_value("1oa") == 1
    
    def test_get_value_with_joker_raises(self):
        """Test that getting value from joker raises error."""
        with pytest.raises(ValueError, match="Joker value is context-dependent"):
            TileUtils.get_value("ja")
    
    def test_format_tile(self):
        """Test formatting tiles for display."""
        assert TileUtils.format_tile("7ra") == "Red 7"
        assert TileUtils.format_tile("13kb") == "Black 13"
        assert TileUtils.format_tile("1oa") == "Orange 1"
        assert TileUtils.format_tile("ja") == "Joker"
        assert TileUtils.format_tile("jb") == "Joker"
    
    def test_create_full_tile_set(self):
        """Test creating complete tile set."""
        all_tiles = TileUtils.create_full_tile_set()
        
        # Should have exactly 106 tiles
        assert len(all_tiles) == 106
        
        # Count jokers and numbered tiles
        jokers = [t for t in all_tiles if TileUtils.is_joker(t)]
        numbered = [t for t in all_tiles if TileUtils.is_numbered(t)]
        
        assert len(jokers) == 2
        assert len(numbered) == 104
        
        # Check jokers
        assert "ja" in all_tiles
        assert "jb" in all_tiles
        
        # Check we have 2 of each numbered tile (each number 1-13 in each color)
        for color in Color:
            for number in range(1, 14):
                tile_a = TileUtils.create_numbered_tile_id(number, color, 'a')
                tile_b = TileUtils.create_numbered_tile_id(number, color, 'b')
                assert tile_a in all_tiles
                assert tile_b in all_tiles