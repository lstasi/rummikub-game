"""Game service implementation with Redis persistence and concurrency control."""

import json
import time
import uuid
from typing import List, Optional
from dataclasses import asdict
from datetime import datetime

from redis import Redis

from ..models import GameState, Player, Action
from ..engine import GameEngine
from .exceptions import GameNotFoundError, ConcurrentModificationError


class GameService:
    """Main service interface for game management with Redis persistence."""
    
    def __init__(self, redis_client: Redis):
        """Initialize the game service.
        
        Args:
            redis_client: Redis client instance for persistence
        """
        self.redis = redis_client
        self.engine = GameEngine()
        self.session_id = str(uuid.uuid4())
    
    def create_game(self, num_players: int) -> GameState:
        """Create new game and return state.
        
        Args:
            num_players: Number of players for the game (2-4)
            
        Returns:
            GameState: New game state
        """
        # Create game via engine
        game_state = self.engine.create_game(num_players)
        
        # Persist game state to Redis
        self._save_game_state(game_state)
        
        return game_state
    
    def join_game(self, game_id: str, player_name: str) -> GameState:
        """Join game by game ID. Returns curated game state for the player.
        
        Args:
            game_id: Game ID to join
            player_name: Name of the player joining
            
        Returns:
            GameState: Curated game state for the player
            
        Raises:
            GameNotFoundError: If game ID not found
        """
        # Acquire lock and get current game state
        with self._game_lock(game_id):
            game_state = self._load_game_state(game_id)
            
            # Check if player already joined
            existing_player = self._find_player_by_name(game_state, player_name)
            if existing_player:
                # Player already joined, return curated state
                return self._curate_game_state_for_player(game_state, existing_player.id)
            
            # Add player to game via engine
            updated_game_state = self.engine.join_game(game_state, player_name)
            
            # Persist updated state
            self._save_game_state(updated_game_state)
            
            # Find the newly added player and return curated state
            new_player = self._find_player_by_name(updated_game_state, player_name)
            if not new_player:
                raise ValueError(f"Player {player_name} not found after joining")
            return self._curate_game_state_for_player(updated_game_state, new_player.id)
    
    def get_game(self, game_id: str, player_name: str) -> Optional[GameState]:
        """Retrieve curated game state for the specific player.
        
        Args:
            game_id: Game ID to retrieve
            player_name: Name of the player requesting the state
            
        Returns:
            GameState: Curated game state for the player, or None if not found
        """
        try:
            game_state = self._load_game_state(game_id)
            player = self._find_player_by_name(game_state, player_name)
            if not player:
                return None
            return self._curate_game_state_for_player(game_state, player.id)
        except GameNotFoundError:
            return None
    
    def get_games(self) -> List[GameState]:
        """Retrieve list of all stored games.
        
        Returns:
            List[GameState]: List of all game states
        """
        game_keys = self.redis.keys("rummikub:games:*")
        # Filter out lock keys
        game_keys = [key for key in game_keys if not key.endswith(":lock")]
        
        games = []
        for key in game_keys:
            try:
                game_data = self.redis.get(key)
                if game_data:
                    game_state = self._deserialize_game_state(str(game_data))
                    games.append(game_state)
            except Exception:
                # Skip corrupted games
                continue
        
        return games
    
    def execute_turn(self, game_id: str, player_id: str, action: Action) -> GameState:
        """Execute player action (play tiles or draw). Includes player validation.
        
        Args:
            game_id: Game ID
            player_id: Player ID executing the action
            action: Action to execute
            
        Returns:
            GameState: Updated game state after action execution
            
        Raises:
            GameNotFoundError: If game ID not found
            Various game engine exceptions for invalid actions
        """
        # Acquire lock for atomic update
        with self._game_lock(game_id):
            # Get current game state
            game_state = self._load_game_state(game_id)
            
            # Execute action via engine based on action type
            from ..models import PlayTilesAction, DrawAction
            if isinstance(action, PlayTilesAction):
                updated_game_state = self.engine.execute_play_action(game_state, player_id, action)
            elif isinstance(action, DrawAction):
                updated_game_state = self.engine.execute_draw_action(game_state, player_id)
            else:
                raise ValueError(f"Unknown action type: {type(action)}")
            
            # Persist updated state
            self._save_game_state(updated_game_state)
            
            # Return curated state for the player
            return self._curate_game_state_for_player(updated_game_state, player_id)
    
    def _load_game_state(self, game_id: str) -> GameState:
        """Load game state from Redis.
        
        Args:
            game_id: Game ID to load
            
        Returns:
            GameState: Loaded game state
            
        Raises:
            GameNotFoundError: If game not found in Redis
        """
        key = f"rummikub:games:{game_id}"
        game_data = self.redis.get(key)
        
        if not game_data:
            raise GameNotFoundError(f"Game {game_id} not found")
        
        return self._deserialize_game_state(str(game_data))
    
    def _save_game_state(self, game_state: GameState) -> None:
        """Save game state to Redis.
        
        Args:
            game_state: Game state to save
        """
        key = f"rummikub:games:{game_state.game_id}"
        serialized_data = self._serialize_game_state(game_state)
        
        # Set TTL based on game status
        if game_state.status.value == "completed":
            # Completed games expire after 24 hours
            self.redis.setex(key, 24 * 60 * 60, serialized_data)
        else:
            # Active games don't expire
            self.redis.set(key, serialized_data)
    
    def _serialize_game_state(self, game_state: GameState) -> str:
        """Serialize game state to JSON string.
        
        Args:
            game_state: Game state to serialize
            
        Returns:
            str: JSON serialized game state
        """
        # Convert dataclass to dict, handling special types
        data = asdict(game_state)
        
        # Convert UUID and datetime fields to strings
        data['game_id'] = str(data['game_id'])
        data['id'] = str(data['id'])
        data['created_at'] = data['created_at'].isoformat()
        data['updated_at'] = data['updated_at'].isoformat()
        
        return json.dumps(data)
    
    def _deserialize_game_state(self, data: str) -> GameState:
        """Deserialize game state from JSON string.
        
        Args:
            data: JSON serialized game state data
            
        Returns:
            GameState: Deserialized game state
        """
        raw_data = json.loads(data)
        
        # Convert string fields back to proper types
        raw_data['game_id'] = uuid.UUID(raw_data['game_id'])
        raw_data['id'] = uuid.UUID(raw_data['id'])
        raw_data['created_at'] = datetime.fromisoformat(raw_data['created_at'])
        raw_data['updated_at'] = datetime.fromisoformat(raw_data['updated_at'])
        
        # Reconstruct nested objects manually for now
        # In a production system, this would use a proper serialization library
        from ..models import Player, Rack, Pool, Board, GameStatus, Meld, MeldKind
        
        # Reconstruct players
        players = []
        for player_data in raw_data['players']:
            rack = Rack(tile_ids=player_data['rack']['tile_ids'])
            player = Player(
                id=player_data['id'],
                name=player_data['name'],
                initial_meld_met=player_data['initial_meld_met'],
                rack=rack,
                joined=player_data['joined']
            )
            players.append(player)
        
        # Reconstruct pool
        pool = Pool(tile_ids=raw_data['pool']['tile_ids'])
        
        # Reconstruct board melds
        melds = []
        for meld_data in raw_data['board']['melds']:
            meld = Meld(
                id=meld_data['id'],
                kind=MeldKind(meld_data['kind']),
                tiles=meld_data['tiles']
            )
            melds.append(meld)
        board = Board(melds=melds)
        
        # Reconstruct GameState
        return GameState(
            game_id=raw_data['game_id'],
            players=players,
            current_player_index=raw_data['current_player_index'],
            pool=pool,
            board=board,
            created_at=raw_data['created_at'],
            updated_at=raw_data['updated_at'],
            status=GameStatus(raw_data['status']),
            winner_player_id=raw_data['winner_player_id'],
            id=raw_data['id'],
            num_players=raw_data['num_players']
        )
    
    def _curate_game_state_for_player(self, game_state: GameState, player_id: str) -> GameState:
        """Curate game state to show only player's own rack, others show count only.
        
        Args:
            game_state: Full game state
            player_id: Player ID to curate for
            
        Returns:
            GameState: Curated game state
        """
        # Create a copy with curated player data
        curated_players = []
        for player in game_state.players:
            if player.id == player_id:
                # Show full rack for the requesting player
                curated_players.append(player)
            else:
                # Show only rack count for other players
                curated_rack = player.rack.__class__(tile_ids=[])  # Empty rack for display
                curated_player = player.update(rack=curated_rack)
                curated_players.append(curated_player)
        
        return game_state._copy_with(players=curated_players)
    
    def _find_player_by_name(self, game_state: GameState, player_name: str) -> Optional[Player]:
        """Find player by name in game state.
        
        Args:
            game_state: Game state to search
            player_name: Player name to find
            
        Returns:
            Player: Found player or None
        """
        for player in game_state.players:
            if player.name == player_name:
                return player
        return None
    
    def _game_lock(self, game_id: str):
        """Context manager for acquiring game lock.
        
        Args:
            game_id: Game ID to lock
        """
        return _GameLock(self.redis, game_id, self.session_id)


class _GameLock:
    """Context manager for Redis-based game locking."""
    
    def __init__(self, redis_client: Redis, game_id: str, session_id: str):
        """Initialize game lock.
        
        Args:
            redis_client: Redis client
            game_id: Game ID to lock
            session_id: Session ID for lock ownership
        """
        self.redis = redis_client
        self.game_id = game_id
        self.session_id = session_id
        self.lock_key = f"rummikub:games:{game_id}:lock"
        self.acquired = False
    
    def __enter__(self):
        """Acquire the lock."""
        # Simple blocking lock with timeout
        max_attempts = 50  # 5 seconds max wait
        for _ in range(max_attempts):
            # Try to acquire lock
            acquired = self.redis.set(
                self.lock_key, 
                self.session_id, 
                nx=True,  # Only set if key doesn't exist
                ex=5      # 5 second expiry
            )
            if acquired:
                self.acquired = True
                return self
            
            # Wait before retry
            time.sleep(0.1)
        
        raise ConcurrentModificationError(f"Could not acquire lock for game {self.game_id}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release the lock if we own it."""
        if self.acquired:
            try:
                # Use Lua script to ensure we only delete if we own the lock
                lua_script = """
                if redis.call("GET", KEYS[1]) == ARGV[1] then
                    return redis.call("DEL", KEYS[1])
                else
                    return 0
                end
                """
                self.redis.eval(lua_script, 1, self.lock_key, self.session_id)  # type: ignore
            except Exception:
                # Fallback for test environments or Redis versions without Lua support
                # Check if we still own the lock and delete
                current_owner = self.redis.get(self.lock_key)
                if current_owner and str(current_owner) == self.session_id:
                    self.redis.delete(self.lock_key)
            self.acquired = False