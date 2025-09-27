// Create game page JavaScript

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('create-game-form');
    const backBtn = document.getElementById('back-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    
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
        const playerName = formData.get('player-name').trim();
        const numPlayers = parseInt(formData.get('num-players'));
        
        if (!playerName) {
            Utils.showError(error, 'Please enter your name');
            return;
        }
        
        if (playerName.length > 50) {
            Utils.showError(error, 'Name must be 50 characters or less');
            return;
        }
        
        if (numPlayers < 2 || numPlayers > 4) {
            Utils.showError(error, 'Number of players must be between 2 and 4');
            return;
        }
        
        await createGame(playerName, numPlayers);
    });
    
    async function createGame(playerName, numPlayers) {
        try {
            Utils.hideError(error);
            Utils.showLoading(loading, true);
            form.style.display = 'none';
            
            // Create the game
            const gameResponse = await API.createGame(numPlayers);
            const gameId = gameResponse.game_id;
            
            // Join the game as the first player
            const joinResponse = await API.joinGame(gameId, playerName);
            
            // Save game state
            GameState.gameId = gameId;
            GameState.playerId = joinResponse.players.find(p => p.name === playerName)?.id;
            GameState.playerName = playerName;
            GameState.save();
            
            // Navigate to game page
            Utils.navigateTo('game', { game_id: gameId, name: playerName });
            
        } catch (error) {
            console.error('Failed to create game:', error);
            Utils.showLoading(loading, false);
            form.style.display = 'block';
            
            let errorMessage = 'Failed to create game. Please try again.';
            if (error.message.includes('players')) {
                errorMessage = 'Invalid number of players selected.';
            }
            
            Utils.showError(error, errorMessage);
        }
    }
});