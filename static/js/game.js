// Game page JavaScript

document.addEventListener('DOMContentLoaded', async () => {
    // Get game parameters
    const params = Utils.getUrlParams();
    const gameId = params.game_id || GameState.gameId;
    const playerName = params.name || GameState.playerName;
    
    if (!gameId || !playerName) {
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
    const leaveGameBtn = document.getElementById('leave-game-btn');
    
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
    let playerId = null;
    
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
        leaveGameBtn.addEventListener('click', leaveGame);
        
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
            
            // If we don't have playerId, we need to find it by joining
            if (!playerId) {
                const response = await API.joinGame(gameId, playerName);
                playerId = response.players.find(p => p.name === playerName)?.id;
                GameState.playerId = playerId;
                GameState.save();
            }
            
            if (!playerId) {
                throw new Error('Could not find player in game');
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
            
            const initialMeldStatus = player.initial_meld_met ? 'Initial meld met' : 'Needs initial meld (30+ pts)';
            const initialMeldClass = player.initial_meld_met ? 'initial-meld-met' : 'initial-meld-not-met';
            
            playerCard.innerHTML = `
                <div class="player-name">${player.name}</div>
                <div class="player-tiles">${tileCount} tiles</div>
                <div class="initial-meld-status ${initialMeldClass}">${initialMeldStatus}</div>
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
            const tileElement = createTileElement(tileId, 'board');
            meldDiv.appendChild(tileElement);
        });
        
        meldDiv.addEventListener('click', () => {
            toggleMeldSelection(meld.id);
        });
        
        return meldDiv;
    }
    
    function createTileElement(tileId, location) {
        const tile = document.createElement('div');
        tile.className = 'tile';
        tile.dataset.tileId = tileId;
        tile.dataset.location = location;
        
        // Parse tile ID to get display info
        const { display, color } = parseTileId(tileId);
        tile.textContent = display;
        tile.classList.add(color);
        
        if (selectedTiles.has(tileId)) {
            tile.classList.add('selected');
        }
        
        if (location === 'rack') {
            tile.addEventListener('click', () => {
                toggleTileSelection(tileId);
            });
        }
        
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
        
        // Check if selected melds contain group melds (for break action)
        const hasGroupMelds = Array.from(selectedMelds).some(meldId => {
            const meld = localBoardState.melds.find(m => m.id === meldId);
            return meld && meld.kind === 'group';
        });
        
        // Check if selected melds are all individual tiles (for group action)
        const hasOnlyIndividualTiles = Array.from(selectedMelds).every(meldId => {
            const meld = localBoardState.melds.find(m => m.id === meldId);
            return meld && meld.kind === 'individual';
        }) && selectedMelds.size >= 2;
        
        // Check if selected melds can be removed (individual tiles that were originally in rack)
        const canRemoveFromBoard = Array.from(selectedMelds).some(meldId => {
            const meld = localBoardState.melds.find(m => m.id === meldId);
            if (meld && meld.kind === 'individual') {
                return meld.tiles.some(tileId => initialTurnRackState?.tiles.includes(tileId));
            }
            return false;
        });
        
        pushToBoardBtn.disabled = !isMyTurn || !hasSelectedTiles;
        removeFromBoardBtn.disabled = !isMyTurn || !hasSelectedMelds || !canRemoveFromBoard;
        breakMeldBtn.disabled = !isMyTurn || !hasSelectedMelds || !hasGroupMelds;
        groupMeldBtn.disabled = !isMyTurn || !hasOnlyIndividualTiles;
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
        
        // Create individual tile "melds" for each selected tile (UI representation)
        const selectedTilesArray = Array.from(selectedTiles);
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
        if (selectedMelds.size === 0) return;
        
        // Only allow removing tiles that were originally in rack at turn start
        // and prevent removing tiles that are part of actual melds (groups/runs)
        selectedMelds.forEach(meldId => {
            const meld = localBoardState.melds.find(m => m.id === meldId);
            if (meld) {
                // Don't allow removing actual melds (groups/runs), only individual tiles
                if (meld.kind === 'group' || meld.kind === 'run') {
                    return; // Skip this meld
                }
                
                // Check if these tiles were originally in the player's rack
                const tilesFromOriginalRack = meld.tiles.filter(tileId => 
                    initialTurnRackState.tiles.includes(tileId)
                );
                
                // Only move tiles that were originally in rack back to rack
                if (tilesFromOriginalRack.length > 0) {
                    playerRackState.tiles.push(...tilesFromOriginalRack);
                }
            }
        });
        
        // Remove selected melds from board (only individual tiles, not actual melds)
        localBoardState.melds = localBoardState.melds.filter(meld => {
            if (selectedMelds.has(meld.id)) {
                // Only remove individual tiles, not actual melds
                return meld.kind === 'group' || meld.kind === 'run';
            }
            return true;
        });
        
        selectedMelds.clear();
        updateUI();
    }
    
    function breakMeld() {
        if (selectedMelds.size === 0) return;
        
        // Only break Group Melds (not runs or individual tiles)
        selectedMelds.forEach(meldId => {
            const meld = localBoardState.melds.find(m => m.id === meldId);
            if (meld && meld.kind === 'group') {
                // Create individual tile "melds" for each tile in the group
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
        
        // Remove selected group melds from board
        localBoardState.melds = localBoardState.melds.filter(meld => {
            if (selectedMelds.has(meld.id)) {
                // Only remove group melds
                return meld.kind !== 'group';
            }
            return true;
        });
        
        selectedMelds.clear();
        updateUI();
    }
    
    function groupMeld() {
        if (selectedMelds.size < 2) return;
        
        // Only group individual tiles (not existing groups or runs)
        const selectedMeldObjects = localBoardState.melds.filter(
            meld => selectedMelds.has(meld.id) && meld.kind === 'individual'
        );
        
        if (selectedMeldObjects.length < 2) return; // Need at least 2 individual tiles
        
        // Combine individual tiles into one new group meld
        const allTiles = selectedMeldObjects.flatMap(meld => meld.tiles);
        
        const newGroupMeld = {
            id: `meld-${Date.now()}`,
            kind: 'group', // Create a group meld
            tiles: allTiles
        };
        
        // Remove selected individual tile melds and add new group meld
        localBoardState.melds = localBoardState.melds.filter(meld => {
            if (selectedMelds.has(meld.id)) {
                // Only remove individual tiles
                return meld.kind !== 'individual';
            }
            return true;
        });
        localBoardState.melds.push(newGroupMeld);
        
        selectedMelds.clear();
        updateUI();
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
    
    function leaveGame() {
        if (confirm('Are you sure you want to leave the game?')) {
            GameState.clear();
            Utils.navigateTo('home');
        }
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