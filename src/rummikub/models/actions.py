"""Action and turn models."""

from dataclasses import dataclass, field
from typing import List, Union

from .melds import Meld


@dataclass
class PlayTilesAction:
    """Action representing playing tiles to the board.
    
    This includes placing new melds and rearranging existing ones.
    The melds field represents the complete board state after the action.
    """
    
    type: str = "play_tiles"
    melds: List[Meld] = field(default_factory=list)


@dataclass
class DrawAction:
    """Action representing drawing a tile from the pool."""
    
    type: str = "draw"


# Union type for actions
Action = Union[PlayTilesAction, DrawAction]


@dataclass
class Turn:
    """A turn taken by a player."""
    
    player_id: str
    action: Action