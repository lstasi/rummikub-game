# UI Design

Web-based user interface for the Rummikub game with responsive design, real-time game state updates, and intuitive gameplay interactions.

## Overview

The UI provides a complete web interface for playing Rummikub online, supporting all game functionality through the REST API. The design prioritizes usability, accessibility, and mobile responsiveness while maintaining the visual clarity needed for tile-based gameplay.

### UI Characteristics
- **Web-based**: Single-page application (SPA) using modern web technologies
- **Real-time**: Automatic game state updates via polling or WebSocket (future)
- **Responsive**: Mobile-first design that works on phones, tablets, and desktop
- **Accessible**: Keyboard navigation, screen reader support, high contrast options
- **Visual**: Clear tile representation with color coding and intuitive drag-and-drop

## Technology Stack

### Frontend Framework
- **HTML5/CSS3/JavaScript**: Core web technologies
- **Framework**: React, Vue.js, or vanilla JavaScript (to be decided)
- **Styling**: CSS Grid/Flexbox for layout, CSS variables for theming
- **HTTP Client**: Fetch API or axios for REST API calls
- **State Management**: Component-level state or lightweight state management

### Design System
- **Color Palette**: High contrast colors matching Rummikub tile colors
- **Typography**: Clear, readable fonts optimized for numbers and game text
- **Icons**: Material Design or similar icon library for UI actions
- **Layout**: Grid-based responsive design with mobile-first approach

## User Flows

### 1. Game Discovery & Setup Flow

**Flow**: Home → Game List → Create/Join Game → Game Lobby → Game Start

#### 1.1 Home Screen
**Purpose**: Entry point and navigation hub

**Components**:
- App header with title "Rummikub Online"
- Main navigation buttons:
  - "Create New Game" (primary action)
  - "Join Existing Game" 
  - "How to Play" (rules overview)
- Recent games list (if any stored locally)

**API Usage**: None initially

#### 1.2 Game List Screen
**Purpose**: Browse and join available games

**Components**:
- Games list with cards showing:
  - Game ID (shortened display)
  - Status (waiting_for_players/in_progress)
  - Player count (e.g., "2/4 players")
  - Created time (relative, e.g., "5 minutes ago")
- "Join Game" button for each waiting game
- "Create New Game" floating action button
- Refresh button to update list

**API Usage**:
```
GET /api/v1/games
- Fetch and display available games
- Poll every 5-10 seconds for updates
```

#### 1.3 Create Game Screen
**Purpose**: Set up new game parameters

**Components**:
- Player count selector (2-4 players)
- Player name input field
- "Create Game" submit button
- "Cancel" back to game list

**API Usage**:
```
POST /api/v1/games
- Create game with specified player count
- Automatically join as first player
- Redirect to game lobby
```

#### 1.4 Join Game Screen
**Purpose**: Join existing game

**Components**:
- Game info display (ID, current players, status)
- Player name input field
- "Join Game" submit button
- "Cancel" back to game list

**API Usage**:
```
POST /api/v1/games/{game_id}/players
- Join game with player name
- Handle full game error gracefully
- Redirect to game lobby or game screen
```

### 2. Game Lobby Flow

**Flow**: Waiting for Players → Game Start

#### 2.1 Game Lobby Screen
**Purpose**: Wait for all players to join before game begins

**Components**:
- Game info panel:
  - Game ID (with copy-to-clipboard)
  - Player slots with avatars/names
  - Empty slots showing "Waiting for player..."
- Player list with status indicators
- Chat area (future enhancement)
- "Leave Game" button
- Auto-start notification when game begins

**API Usage**:
```
GET /api/v1/games/{game_id}/players/{player_id}
- Poll every 2-3 seconds for game status updates
- Detect when status changes to "in_progress"
- Automatically navigate to game screen
```

### 3. Gameplay Flow

**Flow**: Game Screen → Take Turn (Play/Draw) → Game End

#### 3.1 Main Game Screen
**Purpose**: Core gameplay interface with all game elements

**Layout Structure**:
```
┌─────────────────────────────────────┐
│ Header: Game Info & Controls        │
├─────────────────────────────────────┤
│                                     │
│ Board Area: Played Melds            │
│ (Scrollable, drag-drop enabled)     │
│                                     │
├─────────────────────────────────────┤
│ Player Rack: My Tiles               │
│ (Drag-drop enabled, sortable)       │
├─────────────────────────────────────┤
│ Actions Panel: Play/Draw/End Turn   │
└─────────────────────────────────────┘
```

**Components**:

**Header Panel**:
- Game status indicator
- Current player highlight
- Turn timer (future)
- Players list with:
  - Names and tile counts
  - Initial meld status indicators
  - Active player highlighting
- Menu button (settings, rules, leave game)

**Board Area**:
- Central play area showing all melds
- Each meld displayed as grouped tiles
- Visual grouping (border/background) for each meld
- Drag-and-drop zones for new melds
- Empty state: "No melds played yet"

**Player Rack**:
- Bottom panel showing player's tiles
- Tiles displayed as draggable cards
- Sort options (by number, by color, by groups)
- Tile counter showing remaining count
- Visual feedback for selected tiles

**Actions Panel**:
- "Play Tiles" button (enabled when tiles selected)
- "Draw Tile" button (alternative action)
- "End Turn" button (confirm current move)
- "Undo" button (revert current move)

#### 3.2 Tile Representation

**Visual Design**:
- Rectangular cards with rounded corners
- Color-coded backgrounds (black, red, blue, orange)
- Large, clear numbers in contrasting text
- Joker tiles with special "J" symbol
- Selected state with highlight border
- Dragging state with shadow/opacity

**Interaction States**:
- Default: Clear visibility, clickable
- Selected: Highlighted border, ready to move
- Dragging: Reduced opacity, following cursor
- Disabled: Grayed out (opponent tiles)

#### 3.3 Meld Building Interface

**Components**:
- **Meld Zones**: Visual areas on board for placing melds
- **Group Helper**: Visual feedback for valid groups (same number, different colors)
- **Run Helper**: Visual feedback for valid runs (consecutive numbers, same color)
- **Invalid Feedback**: Red highlighting for invalid combinations
- **Meld Validation**: Real-time feedback on meld validity

**Interaction Flow**:
1. Select tiles from rack by clicking/tapping
2. Drag selected tiles to board area
3. Drop tiles to form new meld or add to existing meld
4. Visual feedback shows if combination is valid
5. Confirm placement with "Play Tiles" action

### 4. Turn Actions Flow

#### 4.1 Play Tiles Action
**Purpose**: Place tiles on board in valid combinations

**UI Flow**:
1. Player selects tiles from rack
2. Arranges tiles on board (drag-and-drop)
3. System validates meld formations
4. Player confirms with "Play Tiles" button
5. API call executes the move
6. Game state updates for all players

**API Usage**:
```
POST /api/v1/games/{game_id}/players/{player_id}/actions/play
- Send complete board state after player's moves
- Handle validation errors with clear feedback
- Update game state on success
```

**Error Handling**:
- Invalid meld: Highlight problematic tiles with error message
- Initial meld not met: Show point total and requirement
- Tile not owned: Reset tiles to rack with error message
- Not player's turn: Show "Wait for your turn" message

#### 4.2 Draw Tile Action
**Purpose**: Draw a tile when unable to play

**UI Flow**:
1. Player clicks "Draw Tile" button
2. Confirmation dialog (optional)
3. API call executes draw
4. New tile appears in player's rack
5. Turn advances to next player

**API Usage**:
```
POST /api/v1/games/{game_id}/players/{player_id}/actions/draw
- Simple draw action with empty body
- Handle pool empty error gracefully
- Update rack with new tile
```

### 5. Game End Flow

**Flow**: Win Condition → Game Over Screen → New Game Options

#### 5.1 Game Over Screen
**Purpose**: Display game results and next actions

**Components**:
- Winner announcement with celebration animation
- Final scores and tile counts for all players
- Game summary (duration, total turns)
- Action buttons:
  - "Play Again" (new game with same players)
  - "New Game" (return to game list)
  - "Share Results" (future)

**API Usage**:
```
GET /api/v1/games/{game_id}/players/{player_id}
- Final game state with winner_player_id set
- Display complete final scores
```

## API Integration Patterns

### 1. Game State Polling
**Purpose**: Keep UI synchronized with server state

**Implementation**:
```javascript
// Poll every 3-5 seconds during active gameplay
const pollGameState = async () => {
  try {
    const response = await fetch(`/api/v1/games/${gameId}/players/${playerId}`);
    const gameState = await response.json();
    updateUI(gameState);
  } catch (error) {
    handleApiError(error);
  }
};

setInterval(pollGameState, 3000);
```

**Optimization**:
- Pause polling when game is complete
- Increase frequency during active turns
- Use ETag headers for cache efficiency (future)

### 2. Error Handling Strategy
**Purpose**: Graceful handling of API errors and validation failures

**Implementation**:
```javascript
const handleApiError = (error, action) => {
  switch (error.code) {
    case 'NOT_PLAYERS_TURN':
      showMessage('Please wait for your turn');
      break;
    case 'INVALID_MELD':
      highlightInvalidTiles(error.details.tiles);
      showMessage(error.message);
      break;
    case 'INITIAL_MELD_NOT_MET':
      showInitialMeldHelper(error.details.required_points);
      break;
    default:
      showGenericError(error.message);
  }
};
```

### 3. Optimistic Updates
**Purpose**: Immediate UI feedback before server confirmation

**Implementation**:
- Update UI immediately for player actions
- Revert on API error response
- Show loading states during API calls
- Queue actions to prevent race conditions

## Component Architecture

### 1. Core Components

#### GameBoard Component
**Responsibilities**:
- Render all melds on the board
- Handle drag-and-drop for tile placement
- Validate meld formations visually
- Manage board layout and scrolling

#### PlayerRack Component
**Responsibilities**:
- Display player's tiles in organized layout
- Handle tile selection and deselection
- Support sorting and filtering options
- Provide drag source for tile movement

#### TileComponent
**Responsibilities**:
- Render individual tile appearance
- Handle click and drag interactions
- Show selection and disabled states
- Display tile value and color correctly

#### GameHeader Component
**Responsibilities**:
- Show game status and current player
- Display all players with their states
- Provide game controls and menu access
- Handle responsive layout changes

### 2. Layout Components

#### GameScreen Layout
**Responsive Behavior**:
- Desktop: Side-by-side board and rack
- Tablet: Stacked layout with larger touch targets
- Mobile: Full-screen modes with toggle between board/rack views

#### Modal System
**Components**:
- Game rules overlay
- Settings panel
- Error message dialogs
- Confirmation dialogs for actions

## Accessibility Features

### 1. Keyboard Navigation
**Implementation**:
- Tab navigation through all interactive elements
- Arrow keys for tile selection and movement
- Enter/Space for action confirmation
- Escape key for canceling actions

### 2. Screen Reader Support
**Features**:
- ARIA labels for all game elements
- Descriptive text for tile values and colors
- Game state announcements
- Turn change notifications

### 3. Visual Accessibility
**Features**:
- High contrast mode option
- Customizable color schemes for color blindness
- Large text mode
- Reduced motion options

## Mobile Considerations

### 1. Touch Interactions
**Optimizations**:
- Large touch targets (minimum 44px)
- Touch-friendly drag and drop
- Haptic feedback for actions (where supported)
- Swipe gestures for navigation

### 2. Screen Size Adaptations
**Responsive Design**:
- Collapsible sections for small screens
- Full-screen board mode
- Optimized rack layout for portrait/landscape
- Context-aware hiding of less important elements

### 3. Performance
**Mobile Optimizations**:
- Lazy loading of non-critical components
- Efficient re-rendering strategies
- Minimize API calls and payload sizes
- Progressive Web App (PWA) capabilities

## Technical Implementation Notes

### 1. State Management
**Client-Side State**:
- Game state received from API
- UI state (selected tiles, modal states)
- Player preferences and settings
- Local game history

### 2. Real-time Updates
**Current Implementation**: Polling-based updates
**Future Enhancement**: WebSocket integration for real-time gameplay

### 3. Offline Capability
**Future Enhancement**:
- Service worker for offline play
- Local storage for game state persistence
- Sync when connection restored

### 4. Performance Monitoring
**Metrics to Track**:
- API response times
- UI rendering performance
- User action completion rates
- Error frequencies by type

## Development Phases

### Phase 1: Core Gameplay MVP
**Features**:
- Basic game screens (list, create, join, play)
- Essential game mechanics (play tiles, draw, turn management)
- Simple tile and board representation
- API integration for all core functions

### Phase 2: Enhanced UX
**Features**:
- Improved visual design and animations
- Drag-and-drop tile interactions
- Better error handling and feedback
- Responsive design optimizations

### Phase 3: Advanced Features
**Features**:
- Real-time updates via WebSocket
- Advanced accessibility features
- PWA capabilities and offline support
- Game statistics and history

This UI design provides a complete foundation for implementing a fully functional Rummikub game interface that leverages all the available API endpoints while providing an intuitive and accessible user experience.
