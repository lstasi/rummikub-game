"""Validation utilities and pure functions for Rummikub game logic."""

from collections import Counter
from typing import Dict, List, Set, Tuple

from .exceptions import InvalidMeldError, JokerAssignmentError
from .melds import Meld, MeldKind
from .tiles import Color, NumberedTile, TileInstance, TileKind


def is_valid_group(tiles: List[TileInstance]) -> bool:
    """Check if tiles form a valid group.
    
    A valid group has:
    - 3-4 tiles
    - Same number
    - All distinct colors
    - Jokers allowed (substitute for missing colors)
    
    Args:
        tiles: List of tile instances
        
    Returns:
        True if tiles form a valid group
    """
    if not (3 <= len(tiles) <= 4):
        return False
    
    try:
        assign_jokers_in_group(tiles)
        return True
    except (InvalidMeldError, JokerAssignmentError):
        return False


def is_valid_run(tiles: List[TileInstance]) -> bool:
    """Check if tiles form a valid run.
    
    A valid run has:
    - 3+ tiles
    - Same color  
    - Consecutive numbers
    - Jokers allowed (substitute for missing numbers)
    
    Args:
        tiles: List of tile instances
        
    Returns:
        True if tiles form a valid run
    """
    if len(tiles) < 3:
        return False
    
    try:
        assign_jokers_in_run(tiles)
        return True
    except (InvalidMeldError, JokerAssignmentError):
        return False


def assign_jokers_in_group(tiles: List[TileInstance]) -> Dict[str, NumberedTile]:
    """Assign jokers in a group meld and return their resolved values.
    
    Args:
        tiles: List of tile instances forming a group
        
    Returns:
        Dictionary mapping joker tile IDs to their resolved NumberedTile values
        
    Raises:
        InvalidMeldError: If group is invalid
        JokerAssignmentError: If jokers cannot be assigned
    """
    if not (3 <= len(tiles) <= 4):
        raise InvalidMeldError("Group must have 3-4 tiles", "size")
    
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
    
    group_number = numbers.pop()
    
    # All numbered tiles must have distinct colors
    numbered_colors = {tile.kind.color for tile in numbered if isinstance(tile.kind, NumberedTile)}
    if len(numbered_colors) != len(numbered):
        raise InvalidMeldError("Group cannot have duplicate colors", "color-duplication")
    
    # Assign jokers to missing colors
    all_colors = set(Color)
    missing_colors = all_colors - numbered_colors
    
    if len(jokers) > len(missing_colors):
        raise JokerAssignmentError(f"Too many jokers: need {len(jokers)}, only {len(missing_colors)} colors missing")
    
    # Assign jokers to missing colors (deterministic assignment)
    joker_assignments = {}
    for i, joker in enumerate(jokers):
        assigned_color = sorted(missing_colors)[i]  # Deterministic order
        joker_assignments[str(joker.id)] = NumberedTile(number=group_number, color=assigned_color)
        missing_colors.remove(assigned_color)
    
    return joker_assignments


def assign_jokers_in_run(tiles: List[TileInstance]) -> Dict[str, NumberedTile]:
    """Assign jokers in a run meld and return their resolved values.
    
    Args:
        tiles: List of tile instances forming a run (should be in position order)
        
    Returns:
        Dictionary mapping joker tile IDs to their resolved NumberedTile values
        
    Raises:
        InvalidMeldError: If run is invalid
        JokerAssignmentError: If jokers cannot be assigned
    """
    if len(tiles) < 3:
        raise InvalidMeldError("Run must have at least 3 tiles", "size")
    
    # Separate jokers and numbered tiles
    jokers = [(i, t) for i, t in enumerate(tiles) if t.is_joker]
    numbered = [(i, t) for i, t in enumerate(tiles) if t.is_numbered]
    
    if len(jokers) + len(numbered) != len(tiles):
        raise InvalidMeldError("All tiles must be either numbered or jokers")
    
    # If no numbered tiles, cannot determine the run's color
    if not numbered:
        raise JokerAssignmentError("Cannot determine run color with only jokers")
    
    # All numbered tiles must have the same color
    numbered_tiles = [t for _, t in numbered]
    colors = {tile.kind.color for tile in numbered_tiles if isinstance(tile.kind, NumberedTile)}
    if len(colors) != 1:
        raise InvalidMeldError("All tiles in run must have same color", "mixed-colors")
    
    run_color = colors.pop()
    
    # Build the expected sequence
    if not numbered:
        raise JokerAssignmentError("No numbered tiles to determine sequence")
    
    # Get positions and numbers of numbered tiles
    numbered_positions = [(pos, tile.kind.number) for pos, tile in numbered if isinstance(tile.kind, NumberedTile)]
    numbered_positions.sort()  # Sort by position
    
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
        raise InvalidMeldError("Run sequence out of valid range (1-13)", "invalid-range")
    
    # Assign jokers to their positions in the sequence
    joker_assignments = {}
    for pos, joker in jokers:
        expected_number = expected_start + pos
        joker_assignments[str(joker.id)] = NumberedTile(number=expected_number, color=run_color)
    
    return joker_assignments


def meld_value(meld: Meld, tile_instances: Dict[str, TileInstance]) -> int:
    """Calculate the face value of a meld.
    
    Args:
        meld: The meld to calculate value for
        tile_instances: Dictionary mapping tile IDs to tile instances
        
    Returns:
        Sum of face values (jokers count as their represented value)
    """
    tiles = [tile_instances[str(tile_id)] for tile_id in meld.tiles]
    
    if meld.kind == MeldKind.GROUP:
        joker_assignments = assign_jokers_in_group(tiles)
    else:  # RUN
        joker_assignments = assign_jokers_in_run(tiles)
    
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


def initial_meld_total(melds: List[Meld], tile_instances: Dict[str, TileInstance]) -> int:
    """Calculate total value of melds for initial meld requirement.
    
    Args:
        melds: List of melds to calculate total for
        tile_instances: Dictionary mapping tile IDs to tile instances
        
    Returns:
        Sum of all meld values
    """
    return sum(meld_value(meld, tile_instances) for meld in melds)


def validate_meld(meld: Meld, tile_instances: Dict[str, TileInstance]) -> bool:
    """Validate that a meld is legal.
    
    Args:
        meld: The meld to validate
        tile_instances: Dictionary mapping tile IDs to tile instances
        
    Returns:
        True if meld is valid
        
    Raises:
        InvalidMeldError: If meld is invalid
    """
    tiles = [tile_instances[str(tile_id)] for tile_id in meld.tiles]
    
    if meld.kind == MeldKind.GROUP:
        return is_valid_group(tiles)
    elif meld.kind == MeldKind.RUN:
        return is_valid_run(tiles)
    else:
        raise InvalidMeldError(f"Unknown meld kind: {meld.kind}")


def validate_tile_ownership(game_state) -> bool:
    """Validate that tiles form a proper partition across racks, board, and pool.
    
    Args:
        game_state: GameState instance to validate
        
    Returns:
        True if tile ownership is valid
        
    Raises:
        GameStateError: If tile ownership is invalid
    """
    from .exceptions import GameStateError
    
    all_tile_ids = set()
    
    # Collect tiles from all racks
    for player in game_state.players:
        rack_tiles = set(str(tid) for tid in player.rack.tile_ids)
        if all_tile_ids & rack_tiles:
            raise GameStateError(f"Duplicate tiles found in player {player.id} rack")
        all_tile_ids.update(rack_tiles)
    
    # Collect tiles from board
    board_tiles = set()
    for meld in game_state.board.melds:
        meld_tiles = set(str(tid) for tid in meld.tiles)
        if board_tiles & meld_tiles:
            raise GameStateError("Duplicate tiles found on board")
        board_tiles.update(meld_tiles)
    
    if all_tile_ids & board_tiles:
        raise GameStateError("Tiles appear in both racks and board")
    all_tile_ids.update(board_tiles)
    
    # Collect tiles from pool
    pool_tiles = set(str(tid) for tid in game_state.pool.tile_ids)
    if all_tile_ids & pool_tiles:
        raise GameStateError("Tiles appear in multiple locations")
    all_tile_ids.update(pool_tiles)
    
    return True