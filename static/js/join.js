// Join game page JavaScript

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('join-game-form');
    const gameIdInput = document.getElementById('game-id');
    const backBtn = document.getElementById('back-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    
    // Check for URL parameters
    const params = Utils.getUrlParams();
    if (params.game_id) {
        gameIdInput.value = params.game_id;
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
        
        if (!gameId) {
            Utils.showError(error, 'Please enter a game ID');
            return;
        }
        
        await joinGame(gameId);
    });
    
    async function joinGame(gameId) {
        try {
            Utils.hideError(error);
            Utils.showLoading(loading, true);
            form.style.display = 'none';
            
            // Join the game using authenticated username from HA-PROXY
            const response = await API.joinGame(gameId);
            
            // Get the current player's info from the response
            // The server knows who we are from the Authorization header
            const currentPlayer = response.players[response.players.length - 1]; // Last player is the one who just joined
            
            // Save game state
            GameState.gameId = gameId;
            GameState.playerId = currentPlayer.id;
            GameState.playerName = currentPlayer.name;
            GameState.save();
            
            // Navigate to game page
            Utils.navigateTo('game', { game_id: gameId });
            
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