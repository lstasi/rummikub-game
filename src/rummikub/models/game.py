"""Game state models: Player, Rack, Pool, Board, and GameState."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, TYPE_CHECKING
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from .tiles import TileInstance

from .base import generate_uuid
from .exceptions import GameStateError
from .melds import Meld


@dataclass
class Rack:
    """A player's rack containing their tiles (hidden from other players)."""
    
    tile_ids: List[UUID] = field(default_factory=list)
    
    def __len__(self) -> int:
        """Return the number of tiles in the rack."""
        return len(self.tile_ids)
    
    def is_empty(self) -> bool:
        """Return True if the rack has no tiles."""
        return len(self.tile_ids) == 0
    
    def validate_initial_rack_size(self) -> bool:
        """Validate that rack contains exactly 14 tiles for initial game setup.
        
        According to Rummikub rules, each player starts with exactly 14 tiles.
        
        Returns:
            True if validation passes
            
        Raises:
            GameStateError: If rack doesn't contain exactly 14 tiles
        """
        if len(self.tile_ids) != 14:
            raise GameStateError(f"Initial rack must contain exactly 14 tiles, got {len(self.tile_ids)}")
        return True


@dataclass
class Pool:
    """The pool of face-down tiles available to draw from."""
    
    tile_ids: List[UUID] = field(default_factory=list)
    
    def __len__(self) -> int:
        """Return the number of tiles in the pool."""
        return len(self.tile_ids)
    
    def is_empty(self) -> bool:
        """Return True if the pool has no tiles."""
        return len(self.tile_ids) == 0
    
    @classmethod
    def create_full_pool(cls) -> tuple["Pool", Dict[str, "TileInstance"]]:
        """Create a complete pool with all 106 tiles according to Rummikub rules.
        
        Creates:
        - 104 numbered tiles: 2 copies of each number (1-13) in each color (4 colors)
        - 2 joker tiles
        
        Returns:
            Tuple of (Pool instance, dictionary mapping tile IDs to TileInstance objects)
            
        Raises:
            GameStateError: If pool creation fails validation
        """
        from .tiles import TileInstance, NumberedTile, JokerTile, Color
        
        tile_instances = {}
        tile_ids = []
        
        # Create 104 numbered tiles (2 of each number 1-13 in each of 4 colors)
        for color in Color:
            for number in range(1, 14):  # 1-13 inclusive
                for copy in range(2):  # 2 copies of each
                    tile = TileInstance(kind=NumberedTile(number=number, color=color))
                    tile_instances[str(tile.id)] = tile
                    tile_ids.append(tile.id)
        
        # Create 2 joker tiles
        for _ in range(2):
            joker = TileInstance(kind=JokerTile())
            tile_instances[str(joker.id)] = joker
            tile_ids.append(joker.id)
        
        # Create pool and validate
        pool = cls(tile_ids=tile_ids)
        pool.validate_complete_pool(tile_instances)
        
        return pool, tile_instances
        
    def create_rack(self, num_tiles: int = 14) -> tuple["Rack", "Pool"]:
        """Create a rack by dealing tiles from this pool.
        
        Args:
            num_tiles: Number of tiles to deal (default 14)
            
        Returns:
            Tuple of (Rack with dealt tiles, updated Pool with remaining tiles)
            
        Raises:
            PoolEmptyError: If not enough tiles in pool
        """
        import random
        
        if len(self.tile_ids) < num_tiles:
            from .exceptions import PoolEmptyError
            raise PoolEmptyError(f"Not enough tiles in pool. Need {num_tiles}, have {len(self.tile_ids)}")
        
        # Randomly select tiles
        available_tiles = list(self.tile_ids)
        random.shuffle(available_tiles)
        dealt_tiles = available_tiles[:num_tiles]
        remaining_tiles = available_tiles[num_tiles:]
        
        # Create rack and updated pool
        rack = Rack(tile_ids=dealt_tiles)
        updated_pool = Pool(tile_ids=remaining_tiles)
        
        return rack, updated_pool
        
    def get_random_tile(self) -> tuple[UUID, "Pool"]:
        """Get a random tile from this pool.
        
        Returns:
            Tuple of (tile ID, updated Pool with remaining tiles)
            
        Raises:
            PoolEmptyError: If pool is empty
        """
        import random
        
        if self.is_empty():
            from .exceptions import PoolEmptyError
            raise PoolEmptyError("Cannot draw from empty pool")
        
        # Choose random tile
        tile_id = random.choice(self.tile_ids)
        remaining_tiles = [tid for tid in self.tile_ids if tid != tile_id]
        
        updated_pool = Pool(tile_ids=remaining_tiles)
        return tile_id, updated_pool
    
    def validate_complete_pool(self, tile_instances: Dict[str, "TileInstance"]) -> bool:
        """Validate that pool contains exactly the correct set of tiles.
        
        Validates:
        - No duplicate tile instances
        - Total of 106 tiles
        - Exactly 2 copies of each numbered tile (1-13 in each of 4 colors = 104 tiles)
        - Exactly 2 joker tiles
        
        Args:
            tile_instances: Dictionary mapping tile IDs to TileInstance objects
            
        Returns:
            True if validation passes
            
        Raises:
            GameStateError: If validation fails
        """
        from .tiles import NumberedTile, JokerTile, Color
        
        # Check for duplicate tile IDs first
        if len(set(self.tile_ids)) != len(self.tile_ids):
            raise GameStateError("Pool contains duplicate tile IDs")
        
        if len(self.tile_ids) != 106:
            raise GameStateError(f"Pool must contain exactly 106 tiles, got {len(self.tile_ids)}")
        
        # Count tiles by type
        numbered_tile_counts: Dict[tuple[int, str], int] = {}  # (number, color) -> count
        joker_count = 0
        
        for tile_id in self.tile_ids:
            tile_id_str = str(tile_id)
            if tile_id_str not in tile_instances:
                raise GameStateError(f"Tile {tile_id} not found in tile_instances")
                
            tile = tile_instances[tile_id_str]
            
            if isinstance(tile.kind, NumberedTile):
                key = (tile.kind.number, tile.kind.color)
                numbered_tile_counts[key] = numbered_tile_counts.get(key, 0) + 1
            elif isinstance(tile.kind, JokerTile):
                joker_count += 1
            else:
                raise GameStateError(f"Unknown tile kind: {type(tile.kind)}")
        
        # Validate jokers first: should have exactly 2
        if joker_count != 2:
            raise GameStateError(f"Expected exactly 2 joker tiles, got {joker_count}")
        
        # Validate numbered tiles: should have exactly 2 of each (number, color) combination
        expected_numbered_count = 4 * 13  # 4 colors * 13 numbers = 52 unique combinations
        if len(numbered_tile_counts) != expected_numbered_count:
            raise GameStateError(f"Expected {expected_numbered_count} unique numbered tile types, got {len(numbered_tile_counts)}")
        
        for color in Color:
            for number in range(1, 14):
                key = (number, color)
                count = numbered_tile_counts.get(key, 0)
                if count != 2:
                    raise GameStateError(f"Expected exactly 2 copies of {color.value} {number}, got {count}")
        
        # Validate jokers: should have exactly 2
        if joker_count != 2:
            raise GameStateError(f"Expected exactly 2 joker tiles, got {joker_count}")
        
        return True


@dataclass
class Board:
    """The game board containing all visible melds."""
    
    melds: List[Meld] = field(default_factory=list)
    
    def __len__(self) -> int:
        """Return the number of melds on the board."""
        return len(self.melds)
    
    def is_empty(self) -> bool:
        """Return True if the board has no melds."""
        return len(self.melds) == 0
    
    def add_melds(self, new_melds: List[Meld]) -> "Board":
        """Add new melds to the board and return updated board.
        
        Args:
            new_melds: List of melds to add
            
        Returns:
            New Board instance with melds added
        """
        updated_melds = self.melds + new_melds
        return Board(melds=updated_melds)
    
    def replace_melds(self, new_melds: List[Meld]) -> "Board":
        """Replace all melds on the board with new ones.
        
        Args:
            new_melds: List of melds to replace current melds
            
        Returns:
            New Board instance with replaced melds
        """
        return Board(melds=new_melds)


@dataclass
class Player:
    """A player in the game."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    name: Optional[str] = None
    initial_meld_met: bool = False
    rack: Rack = field(default_factory=Rack)
    joined: bool = False
    
    @classmethod
    def create_player(cls, name: str = None, rack: Rack = None) -> "Player":
        """Create a new player with UUID and optional rack.
        
        Args:
            name: Player name (optional)
            rack: Optional pre-created rack
            
        Returns:
            New Player instance with generated UUID
        """
        return cls(
            name=name,
            rack=rack or Rack(),
            joined=name is not None
        )
    
    def update(self, **changes) -> "Player":
        """Update player with specified changes and return new instance.
        
        Args:
            **changes: Fields to update
            
        Returns:
            New Player instance with updates applied
        """
        # Get current values
        current_values = {
            'id': self.id,
            'name': self.name,
            'initial_meld_met': self.initial_meld_met,
            'rack': self.rack,
            'joined': self.joined
        }
        
        # Apply changes
        current_values.update(changes)
        
        return Player(**current_values)
    
    def remove_tiles_from_rack(self, tile_ids: set[UUID]) -> "Player":
        """Remove specified tiles from rack and return updated player.
        
        Args:
            tile_ids: Set of tile IDs to remove
            
        Returns:
            Updated Player with tiles removed from rack
        """
        remaining_tiles = [tid for tid in self.rack.tile_ids if tid not in tile_ids]
        new_rack = Rack(tile_ids=remaining_tiles)
        return self.update(rack=new_rack)
    
    def add_tile_to_rack(self, tile_id: UUID) -> "Player":
        """Add a tile to rack and return updated player.
        
        Args:
            tile_id: ID of tile to add
            
        Returns:
            Updated Player with tile added to rack
        """
        updated_rack_tiles = self.rack.tile_ids + [tile_id]
        new_rack = Rack(tile_ids=updated_rack_tiles)
        return self.update(rack=new_rack)


class GameStatus(str, Enum):
    """Game status enumeration."""
    WAITING_FOR_PLAYERS = "waiting_for_players"
    IN_PROGRESS = "in_progress"  
    COMPLETED = "completed"


@dataclass
class GameState:
    """Complete state of a Rummikub game."""
    
    game_id: UUID = field(default_factory=uuid4)
    players: List[Player] = field(default_factory=list)
    current_player_index: int = 0
    pool: Pool = field(default_factory=Pool)
    board: Board = field(default_factory=Board)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: GameStatus = GameStatus.WAITING_FOR_PLAYERS
    winner_player_id: Optional[str] = None
    id: UUID = field(default_factory=generate_uuid)
    num_players: int = 4
    
    @classmethod 
    def create_initialized_game(cls, num_players: int) -> "GameState":
        """Create a new game with initialized pool and player slots.
        
        Args:
            num_players: Number of players (2-4)
            
        Returns:
            New GameState with pool and players initialized
        """
        if not (2 <= num_players <= 4):
            raise GameStateError(f"Number of players must be between 2 and 4, got {num_players}")
            
        # Create pool with tiles and tile instances
        pool, _ = Pool.create_full_pool()
        
        # Create empty players for the specified number of players
        players = []
        for _ in range(num_players):
            # Create players with racks but not joined yet
            rack, pool = pool.create_rack(14)
            player = Player.create_player(name=None, rack=rack)
            players.append(player)
        
        return cls(
            players=players,
            pool=pool,
            num_players=num_players
        )
    
    @classmethod
    def create_new_game(cls, game_id: UUID = None, num_players: int = None) -> "GameState":
        """Create a new game state with auto-generated or provided UUID.
        
        Args:
            game_id: Unique identifier for the game (optional, auto-generated if not provided)
            num_players: Number of players (optional, must be 2-4 according to Rummikub rules)
            
        Returns:
            New GameState instance (empty, for testing purposes)
            
        Raises:
            GameStateError: If num_players is provided and not within valid range (2-4)
        """
        if num_players is not None and not (2 <= num_players <= 4):
            raise GameStateError(f"Number of players must be between 2 and 4, got {num_players}")
        
        if game_id is None:
            game_id = uuid4()
            
        # Create empty game state for testing (don't auto-initialize)
        return cls(
            game_id=game_id,
            num_players=num_players or 4,
            players=[]  # Explicitly empty for backwards compatibility
        )
    
    def update_player(self, player_id: str, updated_player: Player) -> "GameState":
        """Update a player in the game state and return new game state.
        
        Args:
            player_id: ID of player to update
            updated_player: Updated player instance
            
        Returns:
            New GameState with updated player
        """
        updated_players = []
        for player in self.players:
            if player.id == player_id:
                updated_players.append(updated_player)
            else:
                updated_players.append(player)
        
        return self._copy_with(players=updated_players)
    
    def update_board(self, new_board: Board) -> "GameState":
        """Update the board and return new game state.
        
        Args:
            new_board: Updated board instance
            
        Returns:
            New GameState with updated board
        """
        return self._copy_with(board=new_board)
    
    def _copy_with(self, **changes) -> "GameState":
        """Create a copy of game state with specified changes.
        
        Args:
            **changes: Fields to update
            
        Returns:
            New GameState instance with changes applied
        """
        current_values = {
            'game_id': self.game_id,
            'players': self.players,
            'current_player_index': self.current_player_index,
            'pool': self.pool,
            'board': self.board,
            'created_at': self.created_at,
            'updated_at': datetime.utcnow(),
            'status': self.status,
            'winner_player_id': self.winner_player_id,
            'id': self.id,
            'num_players': self.num_players
        }
        
        current_values.update(changes)
        return GameState(**current_values)
    
    def validate_player_count(self) -> bool:
        """Validate that the number of players is within the valid range.
        
        According to Rummikub rules, games support 2-4 players.
        
        Returns:
            True if validation passes
            
        Raises:
            GameStateError: If player count is not within valid range
        """
        num_players = len(self.players)
        if not (2 <= num_players <= 4):
            raise GameStateError(f"Number of players must be between 2 and 4, got {num_players}")
        return True
    
    def validate_tile_ownership(self, tile_instances: Dict[str, "TileInstance"]) -> bool:
        """Validate that all tiles are properly allocated and no duplicates exist.
        
        Args:
            tile_instances: Dictionary mapping tile IDs to tile instances
            
        Returns:
            True if tile ownership is valid
            
        Raises:
            GameStateError: If tile ownership is invalid
        """
        
        # Collect all tile IDs from all sources
        all_tile_ids = set()
        
        # Tiles in player racks
        for player in self.players:
            for tile_id in player.rack.tile_ids:
                if tile_id in all_tile_ids:
                    raise GameStateError(f"Duplicate tile {tile_id} found in player racks")
                all_tile_ids.add(tile_id)
        
        # Tiles in pool
        for tile_id in self.pool.tile_ids:
            if tile_id in all_tile_ids:
                raise GameStateError(f"Duplicate tile {tile_id} found in pool")
            all_tile_ids.add(tile_id)
        
        # Tiles on board
        for meld in self.board.melds:
            for tile_id in meld.tiles:
                if tile_id in all_tile_ids:
                    raise GameStateError(f"Duplicate tile {tile_id} found on board")
                all_tile_ids.add(tile_id)
        
        # Verify all tiles in tile_instances are accounted for
        expected_tile_ids = set(str(tid) for tid in tile_instances.keys())
        actual_tile_ids = set(str(tid) for tid in all_tile_ids)
        
        if expected_tile_ids != actual_tile_ids:
            missing = expected_tile_ids - actual_tile_ids
            extra = actual_tile_ids - expected_tile_ids
            if missing:
                raise GameStateError(f"Tiles missing from game state: {missing}")
            if extra:
                raise GameStateError(f"Extra tiles in game state: {extra}")
        
        return True
    
    def calculate_initial_meld_total(self, melds: List[Meld], tile_instances: Dict[str, "TileInstance"]) -> int:
        """Calculate total value of melds for initial meld requirement.
        
        Args:
            melds: List of melds to calculate total for
            tile_instances: Dictionary mapping tile IDs to tile instances
            
        Returns:
            Sum of all meld values
        """
        return sum(meld.get_value(tile_instances) for meld in melds)