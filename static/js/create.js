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
        const numPlayers = parseInt(formData.get('num-players'));
        
        if (numPlayers < 2 || numPlayers > 4) {
            Utils.showError(error, 'Number of players must be between 2 and 4');
            return;
        }
        
        await createGame(numPlayers);
    });
    
    async function createGame(numPlayers) {
        try {
            Utils.hideError(error);
            Utils.showLoading(loading, true);
            form.style.display = 'none';
            
            // Create and join the game (happens automatically now)
            const gameResponse = await API.createGame(numPlayers);
            const gameId = gameResponse.game_id;
            
            // Get authenticated username
            const username = Auth.getUsername();
            
            // Save game state
            GameState.gameId = gameId;
            GameState.playerId = gameResponse.players.find(p => p.name === username)?.id;
            GameState.playerName = username;
            GameState.save();
            
            // Navigate to game page
            Utils.navigateTo('game', { game_id: gameId, name: username });
            
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