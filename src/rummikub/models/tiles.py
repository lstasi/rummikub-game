"""Tile-related models: Color, NumberedTile, JokerTile, and tile utility functions."""

from dataclasses import dataclass
from enum import Enum
from typing import Union, List

from .exceptions import InvalidNumberError


class Color(str, Enum):
    """Tile colors in Rummikub."""
    BLACK = "black"
    RED = "red"  
    BLUE = "blue"
    ORANGE = "orange"


@dataclass(frozen=True)
class NumberedTile:
    """A numbered tile with a specific color and number (1-13)."""
    
    number: int
    color: Color
    type: str = "numbered"
    
    def __post_init__(self):
        """Validate tile number after initialization."""
        if not (1 <= self.number <= 13):
            raise InvalidNumberError(f"Tile number must be 1-13, got {self.number}")
    
    def __str__(self) -> str:
        return f"{self.color.value.title()} {self.number}"


@dataclass(frozen=True)
class JokerTile:
    """A joker tile that can represent any numbered tile contextually."""
    
    type: str = "joker"
    
    def __str__(self) -> str:
        return "Joker"


# Union type for tile kinds (kept for validation purposes)
TileKind = Union[NumberedTile, JokerTile]


# Tile utility functions - work directly with tile ID strings
class TileUtils:
    """Static utility functions for working with tile ID strings.
    
    Tile IDs follow these formats:
    - Numbered tiles: "{number}{color_code}{copy}" (e.g., "7ra" = Red 7 copy A)
    - Joker tiles: "j{copy}" (e.g., "ja" = Joker copy A)
    
    Color codes: 'k'=black, 'r'=red, 'b'=blue, 'o'=orange
    Copy identifiers: 'a' and 'b' (for the two copies of each tile)
    """
    
    # Color code mappings
    COLOR_CODES = {
        Color.BLACK: 'k',
        Color.RED: 'r', 
        Color.BLUE: 'b',
        Color.ORANGE: 'o'
    }
    
    CODE_TO_COLOR = {v: k for k, v in COLOR_CODES.items()}
    
    @staticmethod
    def is_joker(tile_id: str) -> bool:
        """Check if a tile ID represents a joker.
        
        Args:
            tile_id: Tile identifier string
            
        Returns:
            True if tile is a joker
        """
        return tile_id.startswith('j')
    
    @staticmethod
    def is_numbered(tile_id: str) -> bool:
        """Check if a tile ID represents a numbered tile.
        
        Args:
            tile_id: Tile identifier string
            
        Returns:
            True if tile is numbered
        """
        return not tile_id.startswith('j')
    
    @staticmethod
    def get_number(tile_id: str) -> int:
        """Extract the number from a numbered tile ID.
        
        Args:
            tile_id: Tile identifier string
            
        Returns:
            Tile number (1-13)
            
        Raises:
            ValueError: If tile is a joker or invalid format
        """
        if TileUtils.is_joker(tile_id):
            raise ValueError(f"Cannot get number from joker tile: {tile_id}")
        
        # Extract number part (everything before color code and copy)
        if len(tile_id) < 3:
            raise ValueError(f"Invalid tile ID format: {tile_id}")
        
        # Handle 1-2 digit numbers
        if tile_id[1].isdigit():  # Two digit number (10, 11, 12, 13)
            return int(tile_id[:2])
        else:  # One digit number (1-9)
            return int(tile_id[0])
    
    @staticmethod
    def get_color(tile_id: str) -> Color:
        """Extract the color from a numbered tile ID.
        
        Args:
            tile_id: Tile identifier string
            
        Returns:
            Tile color
            
        Raises:
            ValueError: If tile is a joker or invalid format
        """
        if TileUtils.is_joker(tile_id):
            raise ValueError(f"Cannot get color from joker tile: {tile_id}")
        
        # Color code is the second-to-last character
        if len(tile_id) < 3:
            raise ValueError(f"Invalid tile ID format: {tile_id}")
        
        color_code = tile_id[-2]
        if color_code not in TileUtils.CODE_TO_COLOR:
            raise ValueError(f"Invalid color code: {color_code}")
        
        return TileUtils.CODE_TO_COLOR[color_code]
    
    @staticmethod
    def get_copy(tile_id: str) -> str:
        """Extract the copy identifier from a tile ID.
        
        Args:
            tile_id: Tile identifier string
            
        Returns:
            Copy identifier ('a' or 'b')
        """
        return tile_id[-1]
    
    @staticmethod
    def get_value(tile_id: str) -> int:
        """Get the point value of a tile.
        
        For numbered tiles, returns the number.
        For jokers, this method should not be called directly - 
        joker values depend on context in melds.
        
        Args:
            tile_id: Tile identifier string
            
        Returns:
            Point value of the tile
            
        Raises:
            ValueError: If tile is a joker (context-dependent value)
        """
        if TileUtils.is_joker(tile_id):
            raise ValueError(f"Joker value is context-dependent: {tile_id}")
        
        return TileUtils.get_number(tile_id)
    
    @staticmethod
    def create_numbered_tile_id(number: int, color: Color, copy: str) -> str:
        """Create a numbered tile ID.
        
        Args:
            number: Tile number (1-13)
            color: Tile color
            copy: Copy identifier ('a' or 'b')
            
        Returns:
            Tile ID in format {number}{color_code}{copy}
        """
        # Validate inputs
        if not (1 <= number <= 13):
            raise InvalidNumberError(f"Tile number must be 1-13, got {number}")
        
        if copy not in ('a', 'b'):
            raise ValueError(f"Copy must be 'a' or 'b', got {copy}")
        
        color_code = TileUtils.COLOR_CODES[color]
        return f"{number}{color_code}{copy}"
    
    @staticmethod
    def create_joker_tile_id(copy: str) -> str:
        """Create a joker tile ID.
        
        Args:
            copy: Copy identifier ('a' or 'b')
            
        Returns:
            Tile ID in format j{copy}
        """
        if copy not in ('a', 'b'):
            raise ValueError(f"Copy must be 'a' or 'b', got {copy}")
        
        return f"j{copy}"
    
    @staticmethod
    def create_full_tile_set() -> List[str]:
        """Create a complete set of all 106 tile IDs for Rummikub.
        
        Creates:
        - 104 numbered tiles: 2 copies of each number (1-13) in each color (4 colors)
        - 2 joker tiles
        
        Returns:
            List of all tile IDs
        """
        tile_ids = []
        
        # Create 104 numbered tiles (2 of each number 1-13 in each of 4 colors)
        for color in Color:
            for number in range(1, 14):  # 1-13 inclusive
                for copy in ['a', 'b']:  # 2 copies of each
                    tile_id = TileUtils.create_numbered_tile_id(number, color, copy)
                    tile_ids.append(tile_id)
        
        # Create 2 joker tiles
        for copy in ['a', 'b']:
            tile_id = TileUtils.create_joker_tile_id(copy)
            tile_ids.append(tile_id)
        
        return tile_ids
    
    @staticmethod
    def format_tile(tile_id: str) -> str:
        """Format a tile ID for display.
        
        Args:
            tile_id: Tile identifier string
            
        Returns:
            Human-readable tile description
        """
        if TileUtils.is_joker(tile_id):
            return "Joker"
        else:
            number = TileUtils.get_number(tile_id)
            color = TileUtils.get_color(tile_id)
            return f"{color.value.title()} {number}"