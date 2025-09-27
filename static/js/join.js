// Join game page JavaScript

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('join-game-form');
    const gameIdInput = document.getElementById('game-id');
    const playerNameInput = document.getElementById('player-name');
    const backBtn = document.getElementById('back-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    
    // Check for URL parameters
    const params = Utils.getUrlParams();
    if (params.game_id) {
        gameIdInput.value = params.game_id;
    }
    if (params.name) {
        playerNameInput.value = params.name;
    }
    
    // Event listeners
    backBtn.addEventListener('click', () => {
        Utils.navigateTo('home');
    });
    
    cancelBtn.addEventListener('click', () => {
        Utils.navigateTo('home');
    });
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(form);
        const gameId = formData.get('game-id').trim();
        const playerName = formData.get('player-name').trim();
        
        if (!gameId) {
            Utils.showError(error, 'Please enter a game ID');
            return;
        }
        
        if (!playerName) {
            Utils.showError(error, 'Please enter your name');
            return;
        }
        
        if (playerName.length > 50) {
            Utils.showError(error, 'Name must be 50 characters or less');
            return;
        }
        
        await joinGame(gameId, playerName);
    });
    
    async function joinGame(gameId, playerName) {
        try {
            Utils.hideError(error);
            Utils.showLoading(loading, true);
            form.style.display = 'none';
            
            // Join the game
            const response = await API.joinGame(gameId, playerName);
            
            // Save game state
            GameState.gameId = gameId;
            GameState.playerId = response.players.find(p => p.name === playerName)?.id;
            GameState.playerName = playerName;
            GameState.save();
            
            // Navigate to game page
            Utils.navigateTo('game', { game_id: gameId, name: playerName });
            
        } catch (error) {
            console.error('Failed to join game:', error);
            Utils.showLoading(loading, false);
            form.style.display = 'block';
            
            let errorMessage = 'Failed to join game. Please check the game ID and try again.';
            
            if (error.message.includes('not found')) {
                errorMessage = 'Game not found. Please check the game ID.';
            } else if (error.message.includes('full')) {
                errorMessage = 'Game is full. Cannot join.';
            } else if (error.message.includes('completed')) {
                errorMessage = 'Game has already ended.';
            } else if (error.message.includes('already')) {
                errorMessage = 'You are already in this game.';
            }
            
            Utils.showError(error, errorMessage);
        }
    }
});