# UI Refresh Bug Fix

## Issue
When pressing "Draw Tile" or "Next Turn" buttons, the board and rack were not refreshing to show the updated game state.

## Root Cause
The game UI relied on a polling mechanism (every 3 seconds) to update the game state. However, the polling logic only called `resetLocalState()` when the turn changed from another player to the current player. 

When a player drew a tile or ended their turn:
- The API call succeeded and updated the server state
- The polling continued but didn't reset the local state because the turn had moved to the next player
- The board and rack displayed stale data until the next polling cycle detected a turn change back to the current player

## Solution
Modified the `drawTile()` and `endTurn()` functions in `static/js/game.js` to immediately:
1. Fetch the updated game state from the server after a successful action
2. Update `serverGameState` with the fresh data
3. Call `resetLocalState()` to synchronize local board and rack state
4. Call `updateUI()` to refresh all UI elements

### Changes Made

**In `drawTile()` function:**
```javascript
async function drawTile() {
    try {
        await API.drawTile(gameId, playerId);
        // Immediately reload game state to refresh board and rack
        const response = await API.getGameState(gameId, playerId);
        serverGameState = response;
        resetLocalState();
        updateUI();
    } catch (error) {
        showApiError(error, 'Failed to draw tile');
    }
}
```

**In `endTurn()` function (when playing tiles):**
```javascript
await API.playTiles(gameId, playerId, meldsToSend);
// Immediately reload game state to refresh board and rack
const response = await API.getGameState(gameId, playerId);
serverGameState = response;
resetLocalState();
updateUI();
```

## Impact
- Board and rack now update immediately when drawing a tile
- Board and rack now update immediately when ending a turn
- No longer dependent on the 3-second polling interval for these specific actions
- Provides instant visual feedback to the player

## Testing
To verify the fix:
1. Start a game with multiple players
2. On a player's turn, click "Draw Tile" - the rack should immediately show the new tile
3. Add some tiles to the board and click "Next Turn" - the board and rack should immediately reflect the changes
4. The UI should update without waiting for the polling cycle
