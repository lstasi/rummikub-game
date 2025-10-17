// Game page JavaScript

document.addEventListener('DOMContentLoaded', async () => {
    // Get game parameters
    const params = Utils.getUrlParams();
    const gameId = params.game_id || GameState.gameId;
    let playerId = GameState.playerId; // playerId is set when joining/creating game
    
    if (!gameId) {
        Utils.navigateTo('home');
        return;
    }
    
    // UI elements
    const gameStatus = document.getElementById('game-status');
    const playersList = document.getElementById('players-list');
    const board = document.getElementById('board');
    const rack = document.getElementById('rack');
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const debugInfo = document.getElementById('debug-info');
    
    // Action buttons
    const pushToBoardBtn = document.getElementById('push-to-board-btn');
    const removeFromBoardBtn = document.getElementById('remove-from-board-btn');
    const breakMeldBtn = document.getElementById('break-meld-btn');
    const groupMeldBtn = document.getElementById('group-meld-btn');
    const drawTileBtn = document.getElementById('draw-tile-btn');
    const endTurnBtn = document.getElementById('end-turn-btn');
    const resetBtn = document.getElementById('reset-btn');
    
    // Sorting buttons
    const sortByNumberBtn = document.getElementById('sort-by-number');
    const sortByColorBtn = document.getElementById('sort-by-color');
    
    // Game state
    let serverGameState = null; // State from server
    let localBoardState = null; // Local modifications for current turn
    let playerRackState = null; // Local rack state
    let initialTurnBoardState = null; // Board state at start of turn
    let initialTurnRackState = null; // Rack state at start of turn
    let selectedTiles = new Set();
    let selectedMelds = new Set();
    
    // Initialize
    await loadGameState();
    setupEventListeners();
    startPolling();
    
    function setupEventListeners() {
        pushToBoardBtn.addEventListener('click', pushToBoard);
        removeFromBoardBtn.addEventListener('click', removeFromBoard);
        breakMeldBtn.addEventListener('click', breakMeld);
        groupMeldBtn.addEventListener('click', groupMeld);
        drawTileBtn.addEventListener('click', drawTile);
        endTurnBtn.addEventListener('click', endTurn);
        resetBtn.addEventListener('click', resetTurn);
        
        sortByNumberBtn.addEventListener('click', () => sortRack('number'));
        sortByColorBtn.addEventListener('click', () => sortRack('color'));
        
        // Debug toggle
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'd') {
                e.preventDefault();
                toggleDebugInfo();
            }
        });
    }
    
    function toggleDebugInfo() {
        const debugVisible = debugInfo.style.display !== 'none';
        debugInfo.style.display = debugVisible ? 'none' : 'block';
        updateDebugInfo();
    }
    
    function updateDebugInfo() {
        if (debugInfo.style.display === 'none') return;
        
        const debugContent = document.getElementById('debug-content');
        debugContent.innerHTML = `
            <p><strong>Server State:</strong></p>
            <pre>${JSON.stringify(serverGameState, null, 2)}</pre>
            <p><strong>Local Board State:</strong></p>
            <pre>${JSON.stringify(localBoardState, null, 2)}</pre>
            <p><strong>Player Rack:</strong></p>
            <pre>${JSON.stringify(playerRackState, null, 2)}</pre>
            <p><strong>Initial Turn Board:</strong></p>
            <pre>${JSON.stringify(initialTurnBoardState, null, 2)}</pre>
            <p><strong>Initial Turn Rack:</strong></p>
            <pre>${JSON.stringify(initialTurnRackState, null, 2)}</pre>
            <p><strong>Selected Tiles:</strong> ${Array.from(selectedTiles).join(', ')}</p>
            <p><strong>Selected Melds:</strong> ${Array.from(selectedMelds).join(', ')}</p>
        `;
    }
    
    async function loadGameState() {
        try {
            Utils.showLoading(loading, true);
            Utils.hideError(error);
            
            // Player must have joined via home page first (playerId is required)
            if (!playerId) {
                throw new Error('Player ID not found. Please join the game from the home page.');
            }
            
            const response = await API.getGameState(gameId, playerId);
            serverGameState = response;
            
            // Initialize local state from server state
            resetLocalState();
            
            updateUI();
            Utils.showLoading(loading, false);
            
        } catch (error) {
            console.error('Failed to load game state:', error);
            Utils.showLoading(loading, false);
            
            let errorMessage = 'Failed to load game. Please try again.';
            if (error.message.includes('not found')) {
                errorMessage = 'Game not found.';
            }
            
            showApiError(error, errorMessage);
        }
    }
    
    function resetLocalState() {
        // Reset local board state to match server
        localBoardState = {
            melds: serverGameState ? [...serverGameState.board.melds] : []
        };
        
        // Reset player rack state
        const myPlayer = serverGameState?.players.find(p => p.id === playerId);
        playerRackState = {
            tiles: myPlayer?.rack ? [...myPlayer.rack.tiles] : []
        };
        
        // Capture initial turn state for reset functionality
        initialTurnBoardState = {
            melds: serverGameState ? [...serverGameState.board.melds] : []
        };
        initialTurnRackState = {
            tiles: myPlayer?.rack ? [...myPlayer.rack.tiles] : []
        };
        
        // Clear selections
        selectedTiles.clear();
        selectedMelds.clear();
    }
    
    function showApiError(error, fallbackMessage) {
        let errorMessage = fallbackMessage;
        let debugMessage = '';
        
        // Extract detailed error message from API response
        if (error.response && error.response.data && error.response.data.error) {
            const apiError = error.response.data.error;
            errorMessage = apiError.message || fallbackMessage;
            debugMessage = `Code: ${apiError.code}`;
            if (apiError.details) {
                debugMessage += `, Details: ${JSON.stringify(apiError.details)}`;
            }
        } else if (error.response) {
            debugMessage = `HTTP ${error.response.status}: ${JSON.stringify(error.response.data)}`;
        } else if (error.message) {
            debugMessage = error.message;
        }
        
        // Show error message in the UI error element
        const errorElement = document.getElementById('error');
        const fullMessage = debugMessage ? `${errorMessage}\n\nDebug: ${debugMessage}` : errorMessage;
        Utils.showError(errorElement, fullMessage);
        console.error('API Error:', error);
    }
    
    function startPolling() {
        setInterval(async () => {
            if (playerId && serverGameState && serverGameState.status !== 'completed') {
                try {
                    const response = await API.getGameState(gameId, playerId);
                    const wasMyTurn = isCurrentPlayer(playerId);
                    serverGameState = response;
                    
                    // If it wasn't my turn before but is now, reset local state
                    if (!wasMyTurn && isCurrentPlayer(playerId)) {
                        resetLocalState();
                    }
                    
                    updateUI();
                } catch (error) {
                    // Only log polling errors in debug mode or if they're not routine connection issues
                    if (debugInfo.style.display !== 'none' || !error.response || error.response.status >= 500) {
                        console.error('Polling failed:', error);
                    }
                }
            }
        }, 3000); // Poll every 3 seconds
    }
    
    function updateUI() {
        if (!serverGameState) return;
        
        updateGameStatus();
        updatePlayersList();
        updateBoard();
        updateRack();
        updateActionButtons();
        updateDebugInfo();
        
        // Check for game end
        if (serverGameState.status === 'completed') {
            Utils.navigateTo('win', { 
                game_id: gameId, 
                winner: serverGameState.winner_player_id 
            });
        }
    }
    
    function updateGameStatus() {
        const status = serverGameState.status.replace('_', ' ').toUpperCase();
        const currentPlayerName = getCurrentPlayerName();
        const turnIndicator = isCurrentPlayer(playerId) ? '(YOUR TURN)' : '';
        gameStatus.textContent = `${status} - ${currentPlayerName}'s turn ${turnIndicator}`;
    }
    
    function updatePlayersList() {
        playersList.innerHTML = '';
        
        serverGameState.players.forEach(player => {
            const playerCard = document.createElement('div');
            playerCard.className = 'player-card';
            
            if (player.id === playerId) {
                playerCard.classList.add('me');
            }
            
            if (isCurrentPlayer(player.id)) {
                playerCard.classList.add('current-player');
            }
            
            // For current player, show local rack count, for others show server count
            let tileCount;
            if (player.id === playerId) {
                tileCount = playerRackState.tiles.length;
            } else {
                tileCount = player.rack ? player.rack.tiles.length : player.rack_size;
            }
            
            const initialMeldIcon = player.initial_meld_met ? '✓' : '✗';
            const initialMeldClass = player.initial_meld_met ? 'initial-meld-met' : 'initial-meld-not-met';
            const initialMeldTitle = player.initial_meld_met ? 'Initial meld met' : 'Needs initial meld (30+ pts)';
            
            playerCard.innerHTML = `
                <div class="player-name">${player.name}</div>
                <div class="player-tiles">${tileCount} tiles</div>
                <div class="initial-meld-status ${initialMeldClass}" title="${initialMeldTitle}">${initialMeldIcon}</div>
            `;
            
            playersList.appendChild(playerCard);
        });
    }
    
    function updateBoard() {
        board.innerHTML = '';
        
        // Use local board state (shows pending changes)
        if (!localBoardState.melds || localBoardState.melds.length === 0) {
            const noMeldsDiv = document.createElement('div');
            noMeldsDiv.id = 'no-melds';
            noMeldsDiv.className = 'no-melds';
            noMeldsDiv.textContent = 'No melds on board yet';
            board.appendChild(noMeldsDiv);
            return;
        }
        
        localBoardState.melds.forEach(meld => {
            const meldElement = createMeldElement(meld);
            board.appendChild(meldElement);
        });
    }
    
    function updateRack() {
        rack.innerHTML = '';
        
        // Use local rack state (shows pending changes)
        if (!playerRackState.tiles) return;
        
        playerRackState.tiles.forEach(tileId => {
            const tileElement = createTileElement(tileId, 'rack');
            rack.appendChild(tileElement);
        });
    }
    
    function createMeldElement(meld) {
        const meldDiv = document.createElement('div');
        meldDiv.className = 'meld';
        meldDiv.dataset.meldId = meld.id;
        
        if (selectedMelds.has(meld.id)) {
            meldDiv.classList.add('selected');
        }
        
        meld.tiles.forEach(tileId => {
            const tileElement = createTileElement(tileId, 'board', meld.id);
            meldDiv.appendChild(tileElement);
        });
        
        // Only add meld-level click handler for individual tiles (not groups/runs)
        // This allows clicking on the background of individual tiles to select the meld
        if (meld.kind === 'individual') {
            meldDiv.addEventListener('click', (e) => {
                // Only trigger if clicking on the meld div itself, not a tile
                if (e.target === meldDiv) {
                    toggleMeldSelection(meld.id);
                }
            });
        }
        
        return meldDiv;
    }
    
    function createTileElement(tileId, location, meldId = null) {
        const tile = document.createElement('div');
        tile.className = 'tile';
        tile.dataset.tileId = tileId;
        tile.dataset.location = location;
        if (meldId) {
            tile.dataset.meldId = meldId;
        }
        
        // Parse tile ID to get display info
        const { display, color } = parseTileId(tileId);
        tile.textContent = display;
        tile.classList.add(color);
        
        if (selectedTiles.has(tileId)) {
            tile.classList.add('selected');
        }
        
        // Add click handler for tiles in rack and on board
        tile.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent meld click from firing
            toggleTileSelection(tileId);
        });
        
        return tile;
    }
    
    function parseTileId(tileId) {
        if (tileId.startsWith('j')) {
            return { display: 'J', color: 'joker' };
        }
        
        const match = tileId.match(/^(\d+)([krbo])([ab])$/);
        if (match) {
            const number = match[1];
            const colorCode = match[2];
            const colorMap = { k: 'black', r: 'red', b: 'blue', o: 'orange' };
            return { display: number, color: colorMap[colorCode] };
        }
        
        return { display: '?', color: 'black' };
    }
    
    function toggleTileSelection(tileId) {
        if (selectedTiles.has(tileId)) {
            selectedTiles.delete(tileId);
        } else {
            selectedTiles.add(tileId);
        }
        updateUI();
    }
    
    function toggleMeldSelection(meldId) {
        if (selectedMelds.has(meldId)) {
            selectedMelds.delete(meldId);
        } else {
            selectedMelds.add(meldId);
        }
        updateUI();
    }
    
    function updateActionButtons() {
        const isMyTurn = isCurrentPlayer(playerId);
        const hasSelectedTiles = selectedTiles.size > 0;
        const hasSelectedMelds = selectedMelds.size > 0;
        
        // Check if selected melds contain melds that can be broken (groups or runs)
        const hasBreakableMelds = Array.from(selectedMelds).some(meldId => {
            const meld = localBoardState.melds.find(m => m.id === meldId);
            return meld && (meld.kind === 'group' || meld.kind === 'run');
        });
        
        // Check if we can group tiles (need at least 2 tiles selected)
        const canGroupTiles = selectedTiles.size >= 2;
        
        // Check if selected tiles from rack can be removed from board
        // (only tiles that were originally in rack at turn start can be removed)
        const canRemoveFromBoard = Array.from(selectedTiles).some(tileId => 
            initialTurnRackState?.tiles.includes(tileId)
        );
        
        // Push to board: only works with tiles from rack
        const tilesInRack = Array.from(selectedTiles).filter(tileId => 
            playerRackState.tiles.includes(tileId)
        );
        
        pushToBoardBtn.disabled = !isMyTurn || tilesInRack.length === 0;
        removeFromBoardBtn.disabled = !isMyTurn || !hasSelectedTiles || !canRemoveFromBoard;
        breakMeldBtn.disabled = !isMyTurn || !hasSelectedMelds || !hasBreakableMelds;
        groupMeldBtn.disabled = !isMyTurn || !canGroupTiles;
        drawTileBtn.disabled = !isMyTurn;
        endTurnBtn.disabled = !isMyTurn;
    }
    
    function getCurrentPlayerName() {
        if (!serverGameState) return '';
        const currentPlayer = serverGameState.players[serverGameState.current_player_index];
        return currentPlayer ? currentPlayer.name : '';
    }
    
    function isCurrentPlayer(pId) {
        if (!serverGameState) return false;
        const currentPlayer = serverGameState.players[serverGameState.current_player_index];
        return currentPlayer && currentPlayer.id === pId;
    }
    
    // Action functions - Local modifications only (no API calls)
    function pushToBoard() {
        if (selectedTiles.size === 0) return;
        
        // Only push tiles that are currently in the rack
        const selectedTilesArray = Array.from(selectedTiles).filter(tileId => 
            playerRackState.tiles.includes(tileId)
        );
        
        if (selectedTilesArray.length === 0) return;
        
        selectedTilesArray.forEach(tileId => {
            const individualMeld = {
                id: `meld-${Date.now()}-${Math.random()}`,
                kind: 'individual', // Individual tile, not a group or run
                tiles: [tileId]
            };
            
            // Add to local board state as individual tile
            localBoardState.melds.push(individualMeld);
            
            // Remove tile from local rack
            const index = playerRackState.tiles.indexOf(tileId);
            if (index > -1) {
                playerRackState.tiles.splice(index, 1);
            }
        });
        
        selectedTiles.clear();
        updateUI();
    }
    
    function removeFromBoard() {
        if (selectedTiles.size === 0) return;
        
        // Only allow removing tiles that were originally in rack at turn start
        const selectedTilesArray = Array.from(selectedTiles).filter(tileId => 
            initialTurnRackState?.tiles.includes(tileId)
        );
        
        if (selectedTilesArray.length === 0) return;
        
        // Track which melds to remove completely
        const meldsToRemove = new Set();
        
        // Remove tiles from melds
        localBoardState.melds.forEach(meld => {
            const tilesToRemove = meld.tiles.filter(t => selectedTilesArray.includes(t));
            if (tilesToRemove.length > 0) {
                // Remove tiles from this meld
                meld.tiles = meld.tiles.filter(t => !tilesToRemove.includes(t));
                
                // Mark meld for removal if it's now empty
                if (meld.tiles.length === 0) {
                    meldsToRemove.add(meld.id);
                }
                
                // Add tiles back to rack
                playerRackState.tiles.push(...tilesToRemove);
            }
        });
        
        // Remove empty melds
        localBoardState.melds = localBoardState.melds.filter(meld => 
            !meldsToRemove.has(meld.id)
        );
        
        // Clear selections
        selectedTiles.clear();
        updateUI();
    }
    
    function breakMeld() {
        if (selectedMelds.size === 0) return;
        
        // Break melds into individual tiles (works for both groups and runs)
        selectedMelds.forEach(meldId => {
            const meld = localBoardState.melds.find(m => m.id === meldId);
            if (meld && (meld.kind === 'group' || meld.kind === 'run')) {
                // Create individual tile "melds" for each tile in the meld
                meld.tiles.forEach(tileId => {
                    const individualMeld = {
                        id: `meld-${Date.now()}-${Math.random()}`,
                        kind: 'individual',
                        tiles: [tileId]
                    };
                    localBoardState.melds.push(individualMeld);
                });
            }
        });
        
        // Remove selected melds (groups and runs) from board
        localBoardState.melds = localBoardState.melds.filter(meld => {
            if (selectedMelds.has(meld.id)) {
                // Only remove group and run melds, keep individual tiles
                return meld.kind !== 'group' && meld.kind !== 'run';
            }
            return true;
        });
        
        selectedMelds.clear();
        updateUI();
    }
    
    function groupMeld() {
        // Now works with selected tiles instead of selected melds
        if (selectedTiles.size < 2) return;
        
        // Get all selected tiles
        const selectedTilesArray = Array.from(selectedTiles);
        
        // Track which melds these tiles came from
        const meldsToModify = new Map(); // meldId -> tiles to remove
        const tilesToGroup = [...selectedTilesArray];
        
        // Find which melds contain the selected tiles
        localBoardState.melds.forEach(meld => {
            const tilesInThisMeld = meld.tiles.filter(t => selectedTiles.has(t));
            if (tilesInThisMeld.length > 0) {
                meldsToModify.set(meld.id, tilesInThisMeld);
            }
        });
        
        // Remove selected tiles from their original melds
        meldsToModify.forEach((tilesToRemove, meldId) => {
            const meld = localBoardState.melds.find(m => m.id === meldId);
            if (meld) {
                // Remove tiles from this meld
                meld.tiles = meld.tiles.filter(t => !tilesToRemove.includes(t));
            }
        });
        
        // Remove empty melds (melds with no tiles left)
        localBoardState.melds = localBoardState.melds.filter(meld => meld.tiles.length > 0);
        
        // Determine if this should be a group or run based on tiles
        const meldKind = detectMeldKind(tilesToGroup);
        
        // Sort tiles if it's a run
        let sortedTiles = tilesToGroup;
        if (meldKind === 'run') {
            sortedTiles = sortTilesForRun(tilesToGroup);
        }
        
        // Create new meld with selected tiles
        const newMeld = {
            id: `meld-${Date.now()}-${Math.random()}`,
            kind: meldKind,
            tiles: sortedTiles
        };
        
        localBoardState.melds.push(newMeld);
        
        // Clear selections
        selectedTiles.clear();
        updateUI();
    }
    
    function detectMeldKind(tiles) {
        // Try to detect if tiles form a run or group
        // For simplicity, check if all numbered tiles have same number (group) or same color (run)
        const numberedTiles = tiles.filter(t => !t.startsWith('j'));
        
        if (numberedTiles.length === 0) {
            // Only jokers - default to group
            return 'group';
        }
        
        // Extract numbers and colors
        const numbers = numberedTiles.map(t => {
            const match = t.match(/^(\d+)/);
            return match ? parseInt(match[1]) : 0;
        });
        
        const colors = numberedTiles.map(t => {
            const match = t.match(/[krbo]/);
            return match ? match[0] : '';
        });
        
        // Check if all have same number (potential group)
        const allSameNumber = numbers.every(n => n === numbers[0]);
        
        // Check if all have same color (potential run)
        const allSameColor = colors.every(c => c === colors[0]);
        
        // If all same color and different numbers, it's likely a run
        if (allSameColor && !allSameNumber) {
            return 'run';
        }
        
        // Default to group
        return 'group';
    }
    
    function sortTilesForRun(tiles) {
        // Sort tiles by their number value
        // For runs, we need to sort numbered tiles and keep jokers in relative positions
        // The backend will handle joker validation and assignment
        const numberedTiles = tiles.filter(t => !t.startsWith('j'));
        const jokerTiles = tiles.filter(t => t.startsWith('j'));
        
        // Sort numbered tiles by number
        numberedTiles.sort((a, b) => {
            const aNum = parseInt(a.match(/^(\d+)/)?.[1] || '0');
            const bNum = parseInt(b.match(/^(\d+)/)?.[1] || '0');
            return aNum - bNum;
        });
        
        // For now, append jokers at the end
        // The backend validation will properly handle joker positions
        return [...numberedTiles, ...jokerTiles];
    }
    
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
    
    async function endTurn() {
        if (!isCurrentPlayer(playerId)) return;
        
        // Check if there are local changes to commit
        const hasChanges = !arraysEqual(localBoardState.melds, serverGameState.board.melds);
        
        if (hasChanges) {
            try {
                // Send the current local board state to server
                const meldsToSend = localBoardState.melds.map(meld => ({
                    id: meld.id,
                    kind: meld.kind,
                    tiles: meld.tiles
                }));
                
                await API.playTiles(gameId, playerId, meldsToSend);
                // Immediately reload game state to refresh board and rack
                const response = await API.getGameState(gameId, playerId);
                serverGameState = response;
                resetLocalState();
                updateUI();
            } catch (error) {
                showApiError(error, 'Failed to play tiles. Check the error above and fix your melds.');
                return;
            }
        } else {
            // No changes, just draw a tile to end turn
            await drawTile();
        }
    }
    
    function resetTurn() {
        // Reset local state back to initial turn state (no API calls)
        localBoardState = {
            melds: initialTurnBoardState ? [...initialTurnBoardState.melds] : []
        };
        playerRackState = {
            tiles: initialTurnRackState ? [...initialTurnRackState.tiles] : []
        };
        
        // Clear selections
        selectedTiles.clear();
        selectedMelds.clear();
        
        updateUI();
    }
    
    function sortRack(method) {
        if (method === 'number') {
            playerRackState.tiles.sort((a, b) => {
                const aNum = parseInt(a.match(/\d+/)?.[0] || '0');
                const bNum = parseInt(b.match(/\d+/)?.[0] || '0');
                return aNum - bNum;
            });
        } else if (method === 'color') {
            playerRackState.tiles.sort((a, b) => {
                const aColor = a.match(/[krbo]/)?.[0] || 'z';
                const bColor = b.match(/[krbo]/)?.[0] || 'z';
                return aColor.localeCompare(bColor);
            });
        }
        updateUI();
    }
    
    function arraysEqual(a, b) {
        return JSON.stringify(a) === JSON.stringify(b);
    }
});