"""Meld models with validation logic."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from .tiles import TileInstance, NumberedTile

from .base import generate_uuid
from .exceptions import InvalidMeldError, JokerAssignmentError


class MeldKind(str, Enum):
    """Types of melds in Rummikub."""
    GROUP = "group"
    RUN = "run"


@dataclass
class Meld:
    """A meld (group or run) containing tiles.
    
    This represents a valid combination of tiles on the board.
    The tiles list maintains order for runs; for groups, order
    doesn't affect validity but is preserved for deterministic serialization.
    
    Note: Basic validation (non-empty) happens at creation, but full validation
    requiring tile instances should be done via validate_with_tiles().
    """
    
    kind: MeldKind
    tiles: List[UUID]
    id: UUID = field(default_factory=generate_uuid)
    
    def __post_init__(self):
        """Basic validation that doesn't require tile instances."""
        if not self.tiles:
            raise InvalidMeldError("Meld cannot be empty")
        
        # Size validation
        if self.kind == MeldKind.GROUP and not (3 <= len(self.tiles) <= 4):
            raise InvalidMeldError("Group must have 3-4 tiles", "size")
        elif self.kind == MeldKind.RUN and len(self.tiles) < 3:
            raise InvalidMeldError("Run must have at least 3 tiles", "size")
    
    def validate_with_tiles(self, tile_instances: Dict[str, "TileInstance"]) -> None:
        """Validate meld with actual tile instances.
        
        Args:
            tile_instances: Dictionary mapping tile IDs to tile instances
            
        Raises:
            InvalidMeldError: If meld is invalid
            JokerAssignmentError: If jokers cannot be assigned
        """
        # Import here to avoid circular imports
        
        tiles = [tile_instances[str(tile_id)] for tile_id in self.tiles]
        
        if self.kind == MeldKind.GROUP:
            self._validate_group(tiles)
        else:  # RUN
            self._validate_run(tiles)
    
    def _validate_group(self, tiles: List["TileInstance"]) -> None:
        """Validate that tiles form a valid group."""
        from .tiles import NumberedTile
        
        # Separate jokers and numbered tiles
        jokers = [t for t in tiles if t.is_joker]
        numbered = [t for t in tiles if t.is_numbered]
        
        if len(jokers) + len(numbered) != len(tiles):
            raise InvalidMeldError("All tiles must be either numbered or jokers")
        
        # If no numbered tiles, cannot determine the group's number
        if not numbered:
            raise JokerAssignmentError("Cannot determine group number with only jokers")
        
        # All numbered tiles must have the same number
        numbers = {tile.kind.number for tile in numbered if isinstance(tile.kind, NumberedTile)}
        if len(numbers) != 1:
            raise InvalidMeldError("All numbered tiles in group must have same number", "mixed-numbers")
        
        # All numbered tiles must have distinct colors
        numbered_colors = {tile.kind.color for tile in numbered if isinstance(tile.kind, NumberedTile)}
        if len(numbered_colors) != len(numbered):
            raise InvalidMeldError("Group cannot have duplicate colors", "color-duplication")
        
        # Check that we don't have too many tiles for available colors
        from .tiles import Color
        available_colors = set(Color)
        if len(tiles) > len(available_colors):
            raise InvalidMeldError("Group cannot have more tiles than available colors", "size")
        
        # Validate joker assignment is possible
        self._assign_jokers_in_group(tiles)
    
    def _validate_run(self, tiles: List["TileInstance"]) -> None:
        """Validate that tiles form a valid run."""
        from .tiles import NumberedTile
        
        # Separate jokers and numbered tiles
        jokers = [(i, t) for i, t in enumerate(tiles) if t.is_joker]
        numbered = [(i, t) for i, t in enumerate(tiles) if t.is_numbered]
        
        if len(jokers) + len(numbered) != len(tiles):
            raise InvalidMeldError("All tiles must be either numbered or jokers")
        
        # If no numbered tiles, cannot determine the run's color
        if not numbered:
            raise JokerAssignmentError("Cannot determine run color with only jokers")
        
        # All numbered tiles must have the same color
        run_colors = {tile.kind.color for pos, tile in numbered if isinstance(tile.kind, NumberedTile)}
        if len(run_colors) != 1:
            raise InvalidMeldError("Run tiles must all have the same color", "mixed-colors")
        
        # Validate sequence logic
        self._assign_jokers_in_run(tiles)
    
    def _assign_jokers_in_group(self, tiles: List["TileInstance"]) -> Dict[str, "NumberedTile"]:
        """Assign jokers in a group meld and return their resolved values."""
        from .tiles import NumberedTile, Color
        
        # Separate jokers and numbered tiles
        jokers = [t for t in tiles if t.is_joker]
        numbered = [t for t in tiles if t.is_numbered]
        
        # Get the group number and used colors
        if not numbered:
            raise JokerAssignmentError("Cannot determine group number with only jokers")
        
        # We know all numbered tiles have the same number from validation
        first_numbered = numbered[0]
        if not isinstance(first_numbered.kind, NumberedTile):
            raise JokerAssignmentError("Expected NumberedTile")
        group_number = first_numbered.kind.number
        used_colors = {tile.kind.color for tile in numbered if isinstance(tile.kind, NumberedTile)}
        
        # Assign jokers to available colors
        available_colors = set(Color) - used_colors
        if len(jokers) > len(available_colors):
            raise JokerAssignmentError("Too many jokers for available colors in group")
        
        joker_assignments = {}
        available_colors_list = list(available_colors)
        for i, joker in enumerate(jokers):
            assigned_color = available_colors_list[i]
            joker_assignments[str(joker.id)] = NumberedTile(number=group_number, color=assigned_color)
        
        return joker_assignments
    
    def _assign_jokers_in_run(self, tiles: List["TileInstance"]) -> Dict[str, "NumberedTile"]:
        """Assign jokers in a run meld and return their resolved values."""
        from .tiles import NumberedTile
        
        # Separate jokers and numbered tiles
        jokers = [(i, t) for i, t in enumerate(tiles) if t.is_joker]
        numbered = [(i, t) for i, t in enumerate(tiles) if t.is_numbered]
        
        # Get run color
        if not numbered:
            raise JokerAssignmentError("Cannot determine run color with only jokers")
        
        # We know all numbered tiles have the same color from validation  
        first_numbered_tile = numbered[0][1]
        if not isinstance(first_numbered_tile.kind, NumberedTile):
            raise JokerAssignmentError("Expected NumberedTile")
        run_color = first_numbered_tile.kind.color
        
        # Get numbered positions and their values
        numbered_positions = [(pos, tile.kind.number) for pos, tile in numbered if isinstance(tile.kind, NumberedTile)]
        
        # Determine the full sequence based on positions and numbers
        start_pos = numbered_positions[0][0]
        start_num = numbered_positions[0][1]
        
        # Calculate what the starting number should be based on the first numbered tile's position
        expected_start = start_num - start_pos
        
        # Validate that all numbered tiles fit the expected sequence
        for pos, num in numbered_positions:
            expected_num = expected_start + pos
            if num != expected_num:
                raise InvalidMeldError("Run numbers are not consecutive", "non-consecutive")
            if not (1 <= expected_num <= 13):
                raise InvalidMeldError("Run contains invalid numbers (must be 1-13)", "invalid-range")
        
        # Check sequence doesn't wrap around
        expected_end = expected_start + len(tiles) - 1
        if expected_start < 1 or expected_end > 13:
            raise InvalidMeldError("Run sequence goes outside valid range (1-13)", "invalid-range")
        
        # Assign jokers to their positions in the sequence
        joker_assignments = {}
        for pos, joker in jokers:
            expected_number = expected_start + pos
            joker_assignments[str(joker.id)] = NumberedTile(number=expected_number, color=run_color)
        
        return joker_assignments
    
    def get_value(self, tile_instances: Dict[str, "TileInstance"]) -> int:
        """Calculate the face value of this meld.
        
        Args:
            tile_instances: Dictionary mapping tile IDs to tile instances
            
        Returns:
            Sum of face values (jokers count as their represented value)
        """
        from .tiles import NumberedTile
        
        tiles = [tile_instances[str(tile_id)] for tile_id in self.tiles]
        
        if self.kind == MeldKind.GROUP:
            joker_assignments = self._assign_jokers_in_group(tiles)
        else:  # RUN
            joker_assignments = self._assign_jokers_in_run(tiles)
        
        total = 0
        for tile in tiles:
            if tile.is_joker:
                # Get joker's assigned value
                assigned_tile = joker_assignments[str(tile.id)]
                total += assigned_tile.number
            else:
                # Regular numbered tile
                if isinstance(tile.kind, NumberedTile):
                    total += tile.kind.number
                else:
                    raise InvalidMeldError("Invalid tile type in meld")
        
        return total
    
    def __str__(self) -> str:
        return f"{self.kind.value.title()} meld with {len(self.tiles)} tiles"