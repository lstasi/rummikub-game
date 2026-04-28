# UI Refresh Bug Fix

## Status

Implemented in the current UI.

## What Was Fixed

The game page now reloads server state immediately after successful draw and play submissions.

Current behavior in `static/js/game.js`:
- `drawTile()` calls the draw endpoint, then reloads the game state, resets local state, and updates the UI.
- `endTurn()` does the same after a successful play submission.

This avoids waiting for the next polling cycle before the acting player sees the updated board and rack.

## Why The Fix Matters

Without the immediate reload, the UI could show stale local state after the server had already accepted a move or draw.

## Remaining Adjacent Gaps

- Winner display still depends on the unresolved `winner_player_id` bug documented in `doc/CODE_REVIEW.md`.
- The UI still relies on polling for remote-player updates.

## Verification Checklist

1. Draw a tile and confirm the rack updates immediately.
2. Submit a valid board change and confirm the board and rack update immediately.
3. Confirm polling still keeps non-acting players synchronized afterward.
