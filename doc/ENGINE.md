# Game Engine

Responsibilities, public API, validation rules, and algorithms for gameplay, including initial meld and rearrangements.

## Overview

The Game Engine is responsible for enforcing Rummikub game rules and managing game state transitions. It operates on the domain models and provides a high-level API for game operations while ensuring all rules are validated.

## Responsibilities

### Core Game Management
- Game initialization (dealing tiles, setting up initial state)
- Turn management and player rotation
- Game state validation and consistency
- Win condition detection
- Score calculation (when applicable)

### Move Validation and Execution
- Validate and execute tile placements on the board
- Validate and execute board rearrangements
- Initial meld validation (>= 30 points requirement)
- Joker substitution and retrieval logic
- Ensure all board combinations remain valid after moves

### Rule Enforcement
- Enforce valid group and run formations
- Validate tile availability and ownership
- Ensure players can only act on their turn
- Enforce initial meld requirement before first play

## Public API Contracts

### Game Lifecycle

```python
class GameEngine:
    def create_game(self, game_id: UUID, num_players: int) -> GameState:
        """Initialize a new game with specified number of players (2-4)."""
    
    def add_player(self, game_state: GameState, player_id: str, player_name: str = None) -> GameState:
        """Add a player to the game. Deals 14 tiles when game is full and starts."""
    
    def get_game_status(self, game_state: GameState) -> GameStatus:
        """Get current game status (waiting_for_players, in_progress, completed)."""
```

### Turn Management

```python
    def get_current_player(self, game_state: GameState) -> str:
        """Get the ID of the player whose turn it is."""
    
    def can_player_act(self, game_state: GameState, player_id: str) -> bool:
        """Check if the specified player can take actions."""
    
    def advance_turn(self, game_state: GameState) -> GameState:
        """Move to the next player's turn. Called after successful move or draw."""
```

### Move Execution

```python
    def execute_play_action(self, game_state: GameState, player_id: str, action: PlayTilesAction) -> GameState:
        """
        Execute tile play action (placement and/or rearrangement). Validates:
        - Player's turn
        - Tile ownership
        - Initial meld requirement (if not met)
        - All resulting combinations are valid
        - Board remains in valid state
        - No tiles are lost or duplicated in rearrangements
        """
    
    def execute_draw_action(self, game_state: GameState, player_id: str) -> GameState:
        """
        Draw a tile from the pool. Validates:
        - Player's turn  
        - Pool is not empty
        - Player hasn't already made a move this turn
        """
```

### Validation Helpers

```python
    def validate_initial_meld(self, tiles: List[TileInstance], melds: List[Meld]) -> bool:
        """Check if proposed melds meet initial meld requirement (>= 30 points)."""
    
    def validate_joker_retrieval(self, game_state: GameState, meld_id: UUID, 
                                replacement_tile: TileInstance, new_joker_usage: List[Meld]) -> bool:
        """Validate that joker retrieval is legal and joker is reused in same turn."""
    
    def check_win_condition(self, game_state: GameState, player_id: str) -> bool:
        """Check if player has emptied their rack and won."""
    
    def calculate_scores(self, game_state: GameState) -> Dict[str, int]:
        """Calculate penalty scores based on remaining tiles in racks."""
```

## State Transitions

### Game Setup Flow
1. `create_game()` → GameStatus.WAITING_FOR_PLAYERS
2. `add_player()` × N → GameStatus.WAITING_FOR_PLAYERS  
3. `add_player()` (reaches min players) → GameStatus.IN_PROGRESS
   - Deal 14 tiles to each player
   - Initialize turn order
   - Set current player

### Turn Flow
1. **Player Action Phase:**
   - `execute_play_action()` OR `execute_draw_action()`
   - Validate move according to rules
   - Update game state
   
2. **Turn Transition:**
   - Check win condition
   - If won → GameStatus.COMPLETED
   - Else → `advance_turn()` → next player

### Move Validation Sequence
1. **Pre-move validation:**
   - Verify player's turn
   - Check tile ownership
   - Validate move structure

2. **Rule-specific validation:**
   - Initial meld requirement (if applicable)
   - Combination validity (groups/runs)
   - Joker usage rules
   - Board state consistency

3. **Post-move validation:**
   - All board combinations valid
   - No tiles lost/duplicated
   - Game state consistency

## Error Taxonomy

### Game State Errors (extend GameStateError)
- `GameNotFoundError`: Game ID does not exist  
- `GameFullError`: Attempting to add player to full game
- `GameNotStartedError`: Attempting gameplay actions before game starts
- `GameFinishedError`: Attempting actions on completed game

### Turn Management Errors (extend GameStateError)
- `NotPlayersTurnError`: Player attempting action out of turn
- `PlayerNotInGameError`: Unknown player attempting action

### Move Validation Errors (extend ValidationError)
- `InitialMeldNotMetError`: First play doesn't meet 30-point requirement
- `InvalidMoveError`: Generic invalid move (with specific reason)
- `TileNotOwnedError`: Player doesn't own specified tiles
- `PoolEmptyError`: Attempting to draw from empty pool
- `InvalidBoardStateError`: Resulting board state has invalid combinations

### Joker-Related Errors (extend JokerAssignmentError)
- `JokerRetrievalError`: Invalid joker substitution attempt  
- `JokerNotReusedError`: Retrieved joker not used in same turn

*Note: These engine-specific exceptions will be added to `src/rummikub/models/exceptions.py` during implementation.*

## Algorithms

### Initial Meld Validation
```
1. For each proposed meld:
   a. Calculate meld value (including joker values)
   b. Sum total value
2. Return total >= 30
```

### Board Rearrangement Validation
```
1. Extract all tile IDs from current board
2. Extract all tile IDs from proposed board  
3. Verify sets are identical (no tiles added/removed)
4. Validate each meld in proposed board
5. Return all validations pass
```

### Joker Value Calculation
```
For joker in group:
  - Value = number of the group
For joker in run:
  - Value = position-based number in sequence
For ambiguous cases:
  - Raise AmbiguousJokerError
```

### Win Detection
```
1. Check if player's rack is empty
2. Verify all board combinations are valid
3. Return true if both conditions met
```

## Implementation Notes

- Engine is stateless - all state passed as parameters
- Engine does not persist state - returns updated GameState objects
- Validation is strict - any rule violation raises appropriate error
- Thread-safe by design (no shared mutable state)
- Joker logic handles all edge cases defined in RUMMIKUB_RULES.md
- Uses existing model validation where possible, adds game-level validation on top
