// Win page JavaScript

document.addEventListener('DOMContentLoaded', () => {
    const params = Utils.getUrlParams();
    const winnerId = params.winner;
    const gameId = params.game_id;
    
    const winnerText = document.getElementById('winner-text');
    const finalScores = document.getElementById('final-scores');
    const gameDuration = document.getElementById('game-duration');
    const totalTurns = document.getElementById('total-turns');
    
    const playAgainBtn = document.getElementById('play-again-btn');
    const newGameBtn = document.getElementById('new-game-btn');
    const homeBtn = document.getElementById('home-btn');
    
    // Load game results
    loadGameResults();
    
    // Event listeners
    playAgainBtn.addEventListener('click', () => {
        // For MVP: Just go to create game
        Utils.navigateTo('create');
    });
    
    newGameBtn.addEventListener('click', () => {
        Utils.navigateTo('create');
    });
    
    homeBtn.addEventListener('click', () => {
        GameState.clear();
        Utils.navigateTo('home');
    });
    
    async function loadGameResults() {
        try {
            if (gameId && GameState.playerId) {
                const response = await API.getGameState(gameId, GameState.playerId);
                displayResults(response);
            } else {
                // Generic win message if we don't have game details
                winnerText.textContent = 'Game Over!';
                displayGenericResults();
            }
        } catch (error) {
            console.error('Failed to load game results:', error);
            displayGenericResults();
        }
    }
    
    function displayResults(gameState) {
        // Find winner
        const winner = gameState.players.find(p => p.id === gameState.winner_player_id);
        const winnerName = winner ? winner.name : 'Unknown Player';
        
        // Check if current player won
        const isCurrentPlayerWinner = gameState.winner_player_id === GameState.playerId;
        
        if (isCurrentPlayerWinner) {
            winnerText.textContent = 'Congratulations! You Won! 🎉';
            winnerText.style.color = '#27ae60';
        } else {
            winnerText.textContent = `${winnerName} Won!`;
        }
        
        // Display scores (tile counts)
        displayScores(gameState.players);
        
        // Calculate game duration
        const startTime = new Date(gameState.created_at);
        const endTime = new Date(gameState.updated_at);
        const duration = Math.floor((endTime - startTime) / 60000); // minutes
        
        gameDuration.textContent = `Game Duration: ${duration} minutes`;
        totalTurns.textContent = `Total Players: ${gameState.players.length}`;
    }
    
    function displayScores(players) {
        finalScores.innerHTML = '';
        
        // Sort players by tile count (winner first with 0 tiles)
        const sortedPlayers = [...players].sort((a, b) => {
            const aCount = a.rack ? a.rack.tiles.length : a.rack_size || 0;
            const bCount = b.rack ? b.rack.tiles.length : b.rack_size || 0;
            return aCount - bCount;
        });
        
        sortedPlayers.forEach((player, index) => {
            const scoreItem = document.createElement('div');
            scoreItem.className = 'score-item';
            
            const tileCount = player.rack ? player.rack.tiles.length : player.rack_size || 0;
            const position = index === 0 ? '🏆' : `${index + 1}.`;
            
            scoreItem.innerHTML = `
                <span>${position} ${player.name}</span>
                <span>${tileCount} tiles remaining</span>
            `;
            
            if (index === 0) {
                scoreItem.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
                scoreItem.style.color = 'white';
                scoreItem.style.fontWeight = 'bold';
            }
            
            finalScores.appendChild(scoreItem);
        });
    }
    
    function displayGenericResults() {
        winnerText.textContent = 'Game Complete!';
        
        finalScores.innerHTML = `
            <div class="score-item">
                <span>Game results not available</span>
                <span>-</span>
            </div>
        `;
        
        gameDuration.textContent = 'Duration: Unknown';
        totalTurns.textContent = 'Players: Unknown';
    }
});