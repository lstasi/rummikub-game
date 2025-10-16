# Home Page Redesign - My Games & Available Games

## ✅ STATUS: COMPLETED (Phases 1-3)

**Implementation Date**: October 14, 2025  
**Completion Status**: Phases 1-5 complete, Phase 6 (polish) deferred

### Summary of Changes

✅ **Backend (Phase 1)**:
- New `GET /games/my-games` endpoint to retrieve games where the authenticated player has joined
- Modified `POST /games` to automatically join the creator after game creation
- Added status query parameter to `GET /games` for filtering

✅ **Frontend (Phase 2)**:
- Redesigned home page with two-column layout (My Games | Available Games)
- Added inline "Quick Create" form for game creation
- Removed navigation to separate create/join pages
- Auto-refresh every 5 seconds for both game lists

✅ **Cleanup (Phase 3)**:
- Deleted `static/pages/create.html` and `static/pages/join.html`
- Deleted `static/js/create.js` and `static/js/join.js`
- Updated `main.py` page routing to only serve home, game, and win pages
- Updated `static/js/win.js` to navigate to home instead of create page

### Screenshots

**Initial Home Page:**
![Home Page Initial](https://github.com/user-attachments/assets/2815ee7e-0aaa-4846-a1cc-79f290b18954)

**With Available Game:**
![Home Page With Game](https://github.com/user-attachments/assets/2c6955b1-ace9-41a2-82c4-80e6aebedca2)

**With Multiple Players:**
![Home Page Two Players](https://github.com/user-attachments/assets/e89b2161-9aab-46fa-a987-0f797f0e6e1a)

---

## Overview

Redesign the home page to consolidate game creation and joining functionality, removing separate Create and Join pages. The new home page will show two lists:
1. **My Games** - Games where the authenticated player has joined
2. **Available Games** - Games with open slots that can be joined

## Goals

- Simplify the user experience by removing Create and Join pages
- Provide better game discovery with two distinct lists
- Allow quick game creation and joining directly from home page
- Reduce navigation complexity

## Current State

### Current Pages
- **home.html** - Shows all available games with Create/Join buttons
- **create.html** - Form to create new game (player name + number of players)
- **join.html** - Form to join existing game (game ID + player name)
- **game.html** - Active game interface
- **win.html** - Victory screen

### Current JavaScript
- **home.js** - Loads all games, navigates to create/join pages
- **create.js** - Handles game creation form, joins game, navigates to game page
- **join.js** - Handles join form, joins game, navigates to game page
- **main.js** - API wrapper with Basic Auth, GameState management
- **game.js** - Game interface logic
- **win.js** - Victory screen logic
- **i18n.js** - Internationalization

### Current API Endpoints
- `GET /games` - List all games
- `POST /games` - Create game (requires Basic Auth)
- `POST /games/{game_id}/players` - Join game (requires Basic Auth)
- `GET /games/{game_id}` - Get game state (requires Basic Auth)
- `POST /games/{game_id}/actions/play` - Play tiles (requires Basic Auth)
- `POST /games/{game_id}/actions/draw` - Draw tile (requires Basic Auth)

## Proposed Changes

### 1. UI Changes

#### Remove Pages
- **Delete**: `static/pages/create.html`
- **Delete**: `static/pages/join.html`
- **Keep**: `static/pages/home.html` (redesign)
- **Keep**: `static/pages/game.html`
- **Keep**: `static/pages/win.html`

#### Remove JavaScript
- **Delete**: `static/js/create.js`
- **Delete**: `static/js/join.js`
- **Modify**: `static/js/home.js` (add create/join functionality)
- **Keep**: `static/js/main.js`
- **Keep**: `static/js/game.js`
- **Keep**: `static/js/win.js`
- **Keep**: `static/js/i18n.js`

#### Redesign Home Page
The new home page will have:

1. **Header Section**
   - Title: "Rummikub Online"
   - Player info display (authenticated username from Basic Auth)
   - Quick create game button with dropdown for player count

2. **My Games Section**
   - List of games where current player has joined
   - Show game status (waiting/in progress/completed)
   - Show current players
   - "Resume Game" button for in-progress games
   - "View Results" button for completed games
   - Empty state: "You haven't joined any games yet"

3. **Available Games Section**
   - List of games with open slots (status = waiting_for_players)
   - Show available slots (e.g., "2/4 players")
   - "Join Game" button
   - Empty state: "No games available - create one!"

4. **Quick Create Panel**
   - Inline form or modal with:
     - Number of players selector (2-4)
     - "Create & Join" button
   - Automatically joins the player after creation

### 2. Backend Changes

#### New API Endpoint Required

**GET `/games/my-games`**
- Returns list of games where the authenticated player (from Basic Auth) has joined
- Response filters games by checking if player.name matches the authenticated username
- Returns same GameStateResponse format as GET /games

Example:
```json
{
  "games": [
    {
      "game_id": "uuid",
      "status": "in_progress",
      "num_players": 4,
      "players": [...],
      "current_player_name": "Alice",
      ...
    }
  ]
}
```

#### Modified Endpoint Behavior

**GET `/games`**
- Currently returns all games
- Should be modified to return only games with status "waiting_for_players" (available games)
- OR add query parameter `?status=waiting_for_players` to filter

**POST `/games`**
- Currently creates game but doesn't join
- Should automatically join the authenticated player after creation
- This simplifies the flow: create → already joined → redirect to game

### 3. Frontend Logic Changes

#### Modified home.js
New functionality to implement:
- Load two separate lists: my games and available games
- Create game inline (modal or expandable section)
- Auto-join on create
- Direct join without separate page
- Resume game navigation
- Refresh both lists periodically

#### Modified main.js
- No changes needed for API wrapper (already has Basic Auth)
- GameState already stores playerName from Basic Auth

#### Navigation Flow Changes

**Current Flow:**
1. Home → Create page → Fill form → API create → API join → Game page
2. Home → Join page → Fill form → API join → Game page

**New Flow:**
1. Home → Click "Create" → Select players → API create+join → Game page
2. Home → Click "Join" on available game → API join → Game page
3. Home → Click "Resume" on my game → Game page (no API call needed)

### 4. CSS Changes

#### Remove CSS (if any specific to create/join pages)
- Review `static/css/main.css` for create/join specific styles
- Remove unused styles

#### Add CSS for new home page layout
- Two-column or stacked layout for My Games / Available Games
- Game card styling for both lists
- Quick create panel/modal styling
- Responsive design for mobile

## Implementation Plan - TODO List

### Phase 1: Backend API Changes ✅ COMPLETED

- [x] 1.1. Create new endpoint `GET /games/my-games` in `src/rummikub/api/main.py`
  - Add route handler that filters games by authenticated player name
  - Use PlayerNameDep to get current player
  - Return games where player is in players list
  
- [x] 1.2. Modify `POST /games` endpoint to auto-join creator
  - After creating game, automatically call join_game
  - Return the game state with player already joined
  
- [x] 1.3. Add query parameter to `GET /games` for status filtering (optional)
  - Add `status` query parameter
  - Filter games by status if provided
  - Default behavior: return all games (backward compatible)

- [x] 1.4. Add tests for new endpoint
  - Test `GET /games/my-games` with various scenarios
  - Test auto-join on `POST /games`
  - Update existing tests if needed

- [x] 1.5. Update API documentation (`doc/API.md`)
  - Document new `GET /games/my-games` endpoint
  - Document modified `POST /games` behavior
  - Add examples

### Phase 2: Frontend - Home Page Redesign ✅ COMPLETED

- [x] 2.1. Backup current home.html before changes
  - Copy to `/tmp` for reference

- [x] 2.2. Redesign `static/pages/home.html`
  - Remove "Create Game" and "Join Game" navigation buttons
  - Add two sections: "My Games" and "Available Games"
  - Add quick create form/modal
  - Add player info display in header
  - Update structure and layout

- [x] 2.3. Rewrite `static/js/home.js`
  - Remove navigation to create/join pages
  - Add loadMyGames() function (calls /games/my-games)
  - Add loadAvailableGames() function (calls /games?status=waiting or /games)
  - Add createAndJoinGame() function (inline create)
  - Add joinGameDirect() function (join from available games)
  - Add resumeGame() function (navigate to game page)
  - Update displayGames() to handle two separate lists
  - Implement periodic refresh for both lists

- [x] 2.4. Update CSS in `static/css/main.css`
  - Add styles for two-column/stacked layout
  - Add styles for "My Games" section
  - Add styles for "Available Games" section
  - Add styles for quick create panel
  - Remove create/join page specific styles
  - Ensure responsive design

### Phase 3: Remove Create and Join Pages ✅ COMPLETED

- [x] 3.1. Delete `static/pages/create.html`
- [x] 3.2. Delete `static/pages/join.html`
- [x] 3.3. Delete `static/js/create.js`
- [x] 3.4. Delete `static/js/join.js`

### Phase 4: Update Navigation and References ✅ COMPLETED

- [x] 4.1. Update `main.py` page routing
  - Remove 'create' and 'join' from page_files mapping
  - Ensure only 'home', 'game', and 'win' are valid pages

- [x] 4.2. Update `static/js/main.js` if needed
  - Remove any references to create/join pages
  - Ensure Utils.navigateTo() doesn't create broken links

- [x] 4.3. Search for any remaining references
  - Search all files for 'create.html', 'join.html'
  - Search for Utils.navigateTo('create') and Utils.navigateTo('join')
  - Remove or update references (updated win.js)

### Phase 5: Testing and Validation ✅ COMPLETED

- [x] 5.1. Manual testing - Home page functionality
  - Test loading my games list ✅
  - Test loading available games list ✅
  - Test creating game with quick create ✅ (via API)
  - Test joining available game ✅ (via API)
  - Test resuming game from my games ✅
  - Test with no games ✅
  - Test with multiple games ✅

- [x] 5.2. Manual testing - Authentication flow
  - Test with different player names ✅ (Alice and Bob)
  - Verify my games shows only my games ✅ (via API)
  - Verify available games shows joinable games ✅

- [x] 5.3. Manual testing - Navigation
  - Ensure no broken links to create/join pages ✅
  - Ensure game page still works ✅
  - Ensure win page still works ✅ (updated to navigate to home)
  - Test browser back/forward buttons ✅

- [x] 5.4. Run quality gates
  - `ruff check .` ✅
  - `mypy src/` ✅
  - Run relevant tests ✅

- [x] 5.5. Update documentation
  - Update HOME_PAGE_REDESIGN.md to mark completion ✅
  - README.md doesn't reference create/join pages

### Phase 6: Cleanup and Polish ⚠️ DEFERRED

- [ ] 6.1. Remove unused CSS classes
  - Search for orphaned CSS rules
  - Clean up main.css
  - Note: Existing CSS is minimal and not causing issues

- [ ] 6.2. Update i18n translations if needed
  - Add new strings for "My Games", "Available Games"
  - Remove create/join page strings
  - Note: i18n currently uses data-i18n attributes, implementation deferred

- [ ] 6.3. Final review
  - Check for console errors ✅ (only expected auth errors before login)
  - Verify responsive design ✅ (CSS includes mobile breakpoints)
  - Test on different browsers ⚠️ (tested in Playwright/Chromium)
  - Performance check (page load, list refresh) ✅ (5 second refresh interval)

## Key Decisions & Considerations

### Decision 1: Auto-join on Create
**Decision**: POST /games should automatically join the creator
**Rationale**: Simplifies flow, reduces API calls, better UX
**Impact**: Breaking change - existing clients expecting create-only behavior will need update

### Decision 2: My Games Endpoint
**Decision**: Create separate `/games/my-games` endpoint instead of filtering client-side
**Rationale**: 
- Backend has player context from Basic Auth
- Reduces data transfer (don't send all games to filter)
- Better separation of concerns
- Easier to add pagination later
**Alternative**: Client-side filtering of all games
**Chosen**: Server-side filtering with new endpoint

### Decision 3: Available Games Definition
**Decision**: Available games = games with status "waiting_for_players"
**Rationale**: Clear definition, matches user expectation
**Note**: Could later expand to show in-progress games the player can spectate

### Decision 4: Quick Create UI Pattern
**Decision**: Inline expandable form on home page
**Rationale**: 
- Keeps user on same page
- Faster workflow
- Mobile-friendly
**Alternative**: Modal dialog
**Flexible**: Can choose either in implementation

### Decision 5: Game Card Design
**Decision**: Reuse existing game card component but enhance for two contexts
**Rationale**: Consistency, less code duplication
**Enhancements**: 
- My Games: Add "Resume" button, show position in turn order
- Available Games: Show open slots, "Join" button

## Data Flow Diagrams

### Create Game Flow (New)
```
User clicks "Create Game" 
→ Selects number of players
→ Clicks "Create & Join"
→ Frontend: POST /games {num_players: N}
→ Backend: Create game + Auto-join authenticated player
→ Backend: Return game state with player joined
→ Frontend: Save gameId, navigate to /game?game_id=X
```

### Join Game Flow (New)
```
User sees available game in list
→ Clicks "Join" button
→ Frontend: POST /games/{game_id}/players
→ Backend: Join authenticated player to game
→ Backend: Return game state
→ Frontend: Save gameId, navigate to /game?game_id=X
```

### Load Home Page Flow (New)
```
User navigates to home page
→ Browser prompts for Basic Auth (if not cached)
→ User enters player name as username
→ Frontend: Parallel requests:
   - GET /games/my-games (games I'm in)
   - GET /games (available games to join)
→ Backend: Returns filtered lists based on authenticated player
→ Frontend: Display two lists
→ Set up periodic refresh (every 5 seconds)
```

## Breaking Changes

1. **POST /games behavior change**: Now auto-joins the creator
   - Clients expecting create-only will break
   - Workaround: None needed - new behavior is better

2. **Page structure change**: Create and join pages removed
   - Direct links to /create or /join will 404
   - Workaround: Update any bookmarks/external links to home page

3. **Navigation flow**: No longer uses separate pages
   - Browser back button behavior changes
   - Workaround: None needed - simpler flow

## Non-Breaking Enhancements

1. **GET /games**: Can optionally add status filter without breaking existing behavior
2. **New endpoint**: GET /games/my-games is purely additive
3. **Frontend**: All changes are in presentation layer

## Security Considerations

- All endpoints still require Basic Auth
- My games list only shows games for authenticated player
- No unauthorized access to other players' game lists
- No changes to authentication mechanism

## Performance Considerations

- Two API calls on home page load (my-games + available-games)
  - Can be optimized with parallel requests
  - Caching can be added later
- Periodic refresh should use reasonable interval (5 seconds)
- Consider pagination if game lists grow large

## Future Enhancements (Out of Scope)

- Pagination for game lists
- Search/filter functionality
- Game history / statistics
- Spectator mode for in-progress games
- Game invitations / notifications
- Private games with passwords
- Custom game settings

## Success Criteria

1. ✅ Create and Join pages are removed
2. ✅ Home page shows "My Games" list (games I'm in)
3. ✅ Home page shows "Available Games" list (joinable games)
4. ✅ Can create and join game from home page directly
5. ✅ Can join available game from home page directly
6. ✅ Can resume my games from home page
7. ✅ No broken navigation or references
8. ✅ All tests passing
9. ✅ Quality gates passing (ruff, mypy)
10. ✅ Documentation updated

## Rollback Plan

If issues arise:
1. Git revert commits in reverse order
2. Restore create.html and join.html from git history
3. Restore create.js and join.js from git history
4. Restore main.py page routing
5. Revert API endpoint changes
6. Run tests to verify rollback

## Timeline Estimate

- Phase 1 (Backend): ~2-3 commits, 30-45 minutes
- Phase 2 (Frontend): ~3-4 commits, 45-60 minutes
- Phase 3 (Remove pages): ~1 commit, 10 minutes
- Phase 4 (Navigation): ~1 commit, 15 minutes
- Phase 5 (Testing): ~1-2 commits, 30 minutes
- Phase 6 (Cleanup): ~1 commit, 15 minutes

**Total**: ~8-12 commits, ~2.5-3 hours

## References

- Current Basic Auth implementation: See commits 7f9fdac, 75a5977, 6d8bcbf, 1c46f5e
- GameService interface: `src/rummikub/service/`
- API models: `src/rummikub/api/models.py`
- Current home page: `static/pages/home.html`, `static/js/home.js`
