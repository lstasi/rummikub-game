"""Meld models with validation logic."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict

from .exceptions import InvalidMeldError, JokerAssignmentError
from .tiles import TileUtils, Color, NumberedTile


class MeldKind(str, Enum):
    """Types of melds in Rummikub."""
    GROUP = "group"
    RUN = "run"


def _generate_meld_id(kind: MeldKind, tiles: List[str]) -> str:
    """Generate a deterministic meld ID based on tile composition.
    
    For groups: sorts tiles by color order (black, red, blue, orange)
    For runs: sorts tiles by position/number (jokers maintain their position)
    
    Args:
        kind: The meld kind (GROUP or RUN)
        tiles: List of tile IDs
        
    Returns:
        Deterministic meld ID as concatenated sorted tile IDs with "-"
    """
    if kind == MeldKind.GROUP:
        # For groups, sort by color order: black, red, blue, orange
        # Define color order for sorting
        color_order = {Color.BLACK: 0, Color.RED: 1, Color.BLUE: 2, Color.ORANGE: 3}
        
        def group_sort_key(tile_id: str) -> int:
            if TileUtils.is_joker(tile_id):
                # Jokers go last in groups (they'll be assigned remaining colors)
                return 4
            else:
                color = TileUtils.get_color(tile_id)
                return color_order[color]
        
        sorted_tiles = sorted(tiles, key=group_sort_key)
        
    else:  # RUN
        # For runs, maintain the original order since position matters
        # The tiles should already be in correct sequence order
        sorted_tiles = tiles
    
    return "-".join(sorted_tiles)


@dataclass
class Meld:
    """A meld (group or run) containing tiles.
    
    This represents a valid combination of tiles on the board.
    The tiles list maintains order for runs; for groups, order
    doesn't affect validity but is preserved for deterministic serialization.
    
    The meld ID is deterministically generated from the sorted tile IDs.
    """
    
    kind: MeldKind
    tiles: List[str]
    id: str = field(init=False)
    
    def __post_init__(self):
        """Basic validation and ID generation."""
        if not self.tiles:
            raise InvalidMeldError("Meld cannot be empty")
        
        # Size validation
        # Groups are limited to 3-4 tiles (one per color)
        # Runs can be 3-13 tiles (consecutive numbers, limited only by tile range 1-13)
        if self.kind == MeldKind.GROUP and not (3 <= len(self.tiles) <= 4):
            raise InvalidMeldError("Group must have 3-4 tiles", "size")
        elif self.kind == MeldKind.RUN and len(self.tiles) < 3:
            raise InvalidMeldError("Run must have at least 3 tiles", "size")
        
        # For groups, sort tiles in deterministic order (Black-Red-Blue-Orange, jokers last)
        # This ensures frontend doesn't need to worry about joker positioning
        if self.kind == MeldKind.GROUP:
            color_order = {Color.BLACK: 0, Color.RED: 1, Color.BLUE: 2, Color.ORANGE: 3}
            
            def group_sort_key(tile_id: str) -> int:
                if TileUtils.is_joker(tile_id):
                    return 4  # Jokers go last
                else:
                    color = TileUtils.get_color(tile_id)
                    return color_order[color]
            
            self.tiles = sorted(self.tiles, key=group_sort_key)
        
        # Generate deterministic ID
        self.id = _generate_meld_id(self.kind, self.tiles)
    
    def validate(self) -> None:
        """Validate meld with tile IDs.
        
        Raises:
            InvalidMeldError: If meld is invalid
            JokerAssignmentError: If jokers cannot be assigned
        """
        if self.kind == MeldKind.GROUP:
            self._validate_group(self.tiles)
        else:  # RUN
            self._validate_run(self.tiles)
    
    def _validate_group(self, tile_ids: List[str]) -> None:
        """Validate that tiles form a valid group."""
        # Separate jokers and numbered tiles
        jokers = [tid for tid in tile_ids if TileUtils.is_joker(tid)]
        numbered = [tid for tid in tile_ids if TileUtils.is_numbered(tid)]
        
        if len(jokers) + len(numbered) != len(tile_ids):
            raise InvalidMeldError("All tiles must be either numbered or jokers")
        
        # If no numbered tiles, cannot determine the group's number
        if not numbered:
            raise JokerAssignmentError("Cannot determine group number with only jokers")
        
        # All numbered tiles must have the same number
        numbers = {TileUtils.get_number(tid) for tid in numbered}
        if len(numbers) != 1:
            raise InvalidMeldError("All numbered tiles in group must have same number", "mixed-numbers")
        
        # All numbered tiles must have distinct colors
        numbered_colors = {TileUtils.get_color(tid) for tid in numbered}
        if len(numbered_colors) != len(numbered):
            raise InvalidMeldError("Group cannot have duplicate colors", "color-duplication")
        
        # Check that we don't have too many tiles for available colors
        available_colors = set(Color)
        if len(tile_ids) > len(available_colors):
            raise InvalidMeldError("Group cannot have more tiles than available colors", "size")
        
        # Validate joker assignment is possible
        self._assign_jokers_in_group(tile_ids)
    
    def _validate_run(self, tile_ids: List[str]) -> None:
        """Validate that tiles form a valid run."""
        # Separate jokers and numbered tiles with their positions
        jokers = [(i, tid) for i, tid in enumerate(tile_ids) if TileUtils.is_joker(tid)]
        numbered = [(i, tid) for i, tid in enumerate(tile_ids) if TileUtils.is_numbered(tid)]
        
        if len(jokers) + len(numbered) != len(tile_ids):
            raise InvalidMeldError("All tiles must be either numbered or jokers")
        
        # If no numbered tiles, cannot determine the run's color
        if not numbered:
            raise JokerAssignmentError("Cannot determine run color with only jokers")
        
        # All numbered tiles must have the same color
        run_colors = {TileUtils.get_color(tid) for pos, tid in numbered}
        if len(run_colors) != 1:
            raise InvalidMeldError("Run tiles must all have the same color", "mixed-colors")
        
        # Validate sequence logic
        self._assign_jokers_in_run(tile_ids)
    
    def _assign_jokers_in_group(self, tile_ids: List[str]) -> Dict[str, NumberedTile]:
        """Assign jokers in a group meld and return their resolved values."""
        # Separate jokers and numbered tiles
        jokers = [tid for tid in tile_ids if TileUtils.is_joker(tid)]
        numbered = [tid for tid in tile_ids if TileUtils.is_numbered(tid)]
        
        # Get the group number and used colors
        if not numbered:
            raise JokerAssignmentError("Cannot determine group number with only jokers")
        
        # We know all numbered tiles have the same number from validation
        group_number = TileUtils.get_number(numbered[0])
        used_colors = {TileUtils.get_color(tid) for tid in numbered}
        
        # Assign jokers to available colors
        available_colors = set(Color) - used_colors
        if len(jokers) > len(available_colors):
            raise JokerAssignmentError("Too many jokers for available colors in group")
        
        joker_assignments = {}
        available_colors_list = list(available_colors)
        for i, joker_id in enumerate(jokers):
            assigned_color = available_colors_list[i]
            joker_assignments[joker_id] = NumberedTile(number=group_number, color=assigned_color)
        
        return joker_assignments
    
    def _assign_jokers_in_run(self, tile_ids: List[str]) -> Dict[str, NumberedTile]:
        """Assign jokers in a run meld and return their resolved values."""
        # Separate jokers and numbered tiles with positions
        jokers = [(i, tid) for i, tid in enumerate(tile_ids) if TileUtils.is_joker(tid)]
        numbered = [(i, tid) for i, tid in enumerate(tile_ids) if TileUtils.is_numbered(tid)]
        
        # Get run color
        if not numbered:
            raise JokerAssignmentError("Cannot determine run color with only jokers")
        
        # We know all numbered tiles have the same color from validation  
        run_color = TileUtils.get_color(numbered[0][1])
        
        # Get numbered positions and their values
        numbered_positions = [(pos, TileUtils.get_number(tid)) for pos, tid in numbered]
        
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
        expected_end = expected_start + len(tile_ids) - 1
        if expected_start < 1 or expected_end > 13:
            raise InvalidMeldError("Run sequence goes outside valid range (1-13)", "invalid-range")
        
        # Assign jokers to their positions in the sequence
        joker_assignments = {}
        for pos, joker_id in jokers:
            expected_number = expected_start + pos
            joker_assignments[joker_id] = NumberedTile(number=expected_number, color=run_color)
        
        return joker_assignments
    
    def get_value(self) -> int:
        """Calculate the face value of this meld.
        
        Returns:
            Sum of face values (jokers count as their represented value)
        """
        if self.kind == MeldKind.GROUP:
            joker_assignments = self._assign_jokers_in_group(self.tiles)
        else:  # RUN
            joker_assignments = self._assign_jokers_in_run(self.tiles)
        
        total = 0
        for tile_id in self.tiles:
            if TileUtils.is_joker(tile_id):
                # Get joker's assigned value
                assigned_tile = joker_assignments[tile_id]
                total += assigned_tile.number
            else:
                # Regular numbered tile
                total += TileUtils.get_number(tile_id)
        
        return total
    
    def __str__(self) -> str:
        return f"{self.kind.value.title()} meld with {len(self.tiles)} tiles"