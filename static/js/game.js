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
    
    // Action buttons
    const pushToBoardBtn = document.getElementById('push-to-board-btn');
    const removeFromBoardBtn = document.getElementById('remove-from-board-btn');
    const breakMeldBtn = document.getElementById('break-meld-btn');
    const groupMeldBtn = document.getElementById('group-meld-btn');
    const drawTileBtn = document.getElementById('draw-tile-btn');
    const endTurnBtn = document.getElementById('end-turn-btn');
    const leaveGameBtn = document.getElementById('leave-game-btn');
    
    // Sorting buttons
    const sortByNumberBtn = document.getElementById('sort-by-number');
    const sortByColorBtn = document.getElementById('sort-by-color');
    
    // Game state
    let currentGameState = null;
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
        leaveGameBtn.addEventListener('click', leaveGame);
        
        sortByNumberBtn.addEventListener('click', () => sortRack('number'));
        sortByColorBtn.addEventListener('click', () => sortRack('color'));
    }
    
    async function loadGameState() {
        try {
            Utils.showLoading(loading, true);
            
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
            currentGameState = response;
            
            updateUI();
            Utils.showLoading(loading, false);
            
        } catch (error) {
            console.error('Failed to load game state:', error);
            Utils.showLoading(loading, false);
            
            let errorMessage = 'Failed to load game. Please try again.';
            if (error.message.includes('not found')) {
                errorMessage = 'Game not found.';
            }
            
            Utils.showError(error, errorMessage);
        }
    }
    
    function startPolling() {
        setInterval(async () => {
            if (playerId && currentGameState && currentGameState.status !== 'completed') {
                try {
                    const response = await API.getGameState(gameId, playerId);
                    currentGameState = response;
                    updateUI();
                } catch (error) {
                    console.error('Polling failed:', error);
                }
            }
        }, 3000); // Poll every 3 seconds
    }
    
    function updateUI() {
        if (!currentGameState) return;
        
        updateGameStatus();
        updatePlayersList();
        updateBoard();
        updateRack();
        updateActionButtons();
        
        // Check for game end
        if (currentGameState.status === 'completed') {
            Utils.navigateTo('win', { 
                game_id: gameId, 
                winner: currentGameState.winner_player_id 
            });
        }
    }
    
    function updateGameStatus() {
        const status = currentGameState.status.replace('_', ' ').toUpperCase();
        const currentPlayerName = getCurrentPlayerName();
        gameStatus.textContent = `${status} - ${currentPlayerName}'s turn`;
    }
    
    function updatePlayersList() {
        playersList.innerHTML = '';
        
        currentGameState.players.forEach(player => {
            const playerCard = document.createElement('div');
            playerCard.className = 'player-card';
            
            if (player.id === playerId) {
                playerCard.classList.add('me');
            }
            
            if (isCurrentPlayer(player.id)) {
                playerCard.classList.add('current-player');
            }
            
            const tileCount = player.rack ? player.rack.tiles.length : player.rack_size;
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
        const noMelds = document.getElementById('no-melds');
        
        if (!currentGameState.board.melds || currentGameState.board.melds.length === 0) {
            if (!noMelds) {
                const noMeldsDiv = document.createElement('div');
                noMeldsDiv.id = 'no-melds';
                noMeldsDiv.className = 'no-melds';
                noMeldsDiv.textContent = 'No melds on board yet';
                board.appendChild(noMeldsDiv);
            }
            return;
        }
        
        currentGameState.board.melds.forEach(meld => {
            const meldElement = createMeldElement(meld);
            board.appendChild(meldElement);
        });
    }
    
    function updateRack() {
        rack.innerHTML = '';
        
        const myPlayer = currentGameState.players.find(p => p.id === playerId);
        if (!myPlayer || !myPlayer.rack) return;
        
        myPlayer.rack.tiles.forEach(tileId => {
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
        
        pushToBoardBtn.disabled = !isMyTurn || !hasSelectedTiles;
        removeFromBoardBtn.disabled = !isMyTurn || !hasSelectedMelds;
        breakMeldBtn.disabled = !isMyTurn || !hasSelectedMelds;
        groupMeldBtn.disabled = !isMyTurn || selectedMelds.size < 2;
        drawTileBtn.disabled = !isMyTurn;
        endTurnBtn.disabled = !isMyTurn;
    }
    
    function getCurrentPlayerName() {
        if (!currentGameState) return '';
        const currentPlayer = currentGameState.players[currentGameState.current_player_index];
        return currentPlayer ? currentPlayer.name : '';
    }
    
    function isCurrentPlayer(pId) {
        if (!currentGameState) return false;
        const currentPlayer = currentGameState.players[currentGameState.current_player_index];
        return currentPlayer && currentPlayer.id === pId;
    }
    
    // Action functions (simplified for MVP)
    async function pushToBoard() {
        if (selectedTiles.size === 0) return;
        
        // For MVP: Create a simple meld with selected tiles
        const selectedTilesArray = Array.from(selectedTiles);
        const newMeld = {
            id: `meld-${Date.now()}`,
            kind: 'group', // Default to group for simplicity
            tiles: selectedTilesArray
        };
        
        try {
            const melds = [...currentGameState.board.melds, newMeld];
            await API.playTiles(gameId, playerId, melds);
            selectedTiles.clear();
        } catch (error) {
            Utils.showError(error, error.message);
        }
    }
    
    async function removeFromBoard() {
        // Remove selected melds from board
        try {
            const remainingMelds = currentGameState.board.melds.filter(
                meld => !selectedMelds.has(meld.id)
            );
            await API.playTiles(gameId, playerId, remainingMelds);
            selectedMelds.clear();
        } catch (error) {
            Utils.showError(error, error.message);
        }
    }
    
    async function breakMeld() {
        // For MVP: Just remove the selected melds
        await removeFromBoard();
    }
    
    async function groupMeld() {
        // For MVP: Combine selected melds into one
        if (selectedMelds.size < 2) return;
        
        try {
            const selectedMeldObjects = currentGameState.board.melds.filter(
                meld => selectedMelds.has(meld.id)
            );
            const allTiles = selectedMeldObjects.flatMap(meld => meld.tiles);
            
            const newMeld = {
                id: `meld-${Date.now()}`,
                kind: 'group',
                tiles: allTiles
            };
            
            const remainingMelds = currentGameState.board.melds.filter(
                meld => !selectedMelds.has(meld.id)
            );
            
            const melds = [...remainingMelds, newMeld];
            await API.playTiles(gameId, playerId, melds);
            selectedMelds.clear();
        } catch (error) {
            Utils.showError(error, error.message);
        }
    }
    
    async function drawTile() {
        try {
            await API.drawTile(gameId, playerId);
        } catch (error) {
            Utils.showError(error, error.message);
        }
    }
    
    async function endTurn() {
        // For MVP: End turn is automatic after actions
        alert('Turn ends automatically after playing tiles or drawing a tile.');
    }
    
    function leaveGame() {
        if (confirm('Are you sure you want to leave the game?')) {
            GameState.clear();
            Utils.navigateTo('home');
        }
    }
    
    function sortRack(method) {
        // This would sort the visual representation
        // For MVP, just show a message
        alert(`Sorting by ${method} - feature coming soon!`);
    }
});