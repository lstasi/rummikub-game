// Home page JavaScript for Rummikub Online

document.addEventListener('DOMContentLoaded', async () => {
    const gamesList = document.getElementById('games-list');
    const noGames = document.getElementById('no-games');
    const createGameBtn = document.getElementById('create-game-btn');
    const joinGameBtn = document.getElementById('join-game-btn');
    const howToPlayBtn = document.getElementById('how-to-play-btn');
    
    // Load games on page load
    await loadGames();
    
    // Set up periodic refresh
    setInterval(loadGames, 5000); // Refresh every 5 seconds
    
    // Event listeners
    createGameBtn.addEventListener('click', () => {
        Utils.navigateTo('create');
    });
    
    joinGameBtn.addEventListener('click', () => {
        Utils.navigateTo('join');
    });
    
    howToPlayBtn.addEventListener('click', () => {
        showRules();
    });
    
    async function loadGames() {
        try {
            const response = await API.getGames();
            displayGames(response.games || []);
        } catch (error) {
            console.error('Failed to load games:', error);
            // Don't show error on home page, just show no games
            displayGames([]);
        }
    }
    
    function displayGames(games) {
        gamesList.innerHTML = '';
        
        if (games.length === 0) {
            noGames.style.display = 'block';
            return;
        }
        
        noGames.style.display = 'none';
        
        games.forEach(game => {
            const gameCard = createGameCard(game);
            gamesList.appendChild(gameCard);
        });
    }
    
    function createGameCard(game) {
        const card = document.createElement('div');
        card.className = 'game-card';
        
        const statusClass = game.status === 'waiting_for_players' ? 'status-waiting' : 
                          game.status === 'in_progress' ? 'status-in-progress' : 'status-completed';
        
        const canJoin = game.status === 'waiting_for_players';
        const joinButton = canJoin ? 
            `<button class="btn btn-primary join-btn" data-game-id="${game.game_id}">Join Game</button>` :
            `<button class="btn btn-secondary" disabled>Game ${game.status.replace('_', ' ')}</button>`;
        
        card.innerHTML = `
            <h3>Game ${Utils.shortId(game.game_id)}</h3>
            <p><span class="game-status ${statusClass}">${game.status.replace('_', ' ')}</span></p>
            <p>Players: ${game.num_players}/${game.num_players}</p>
            <p>Created: ${Utils.formatTime(game.created_at)}</p>
            <div style="margin-top: 15px;">
                ${joinButton}
            </div>
        `;
        
        // Add join functionality
        const joinBtn = card.querySelector('.join-btn');
        if (joinBtn) {
            joinBtn.addEventListener('click', () => {
                const gameId = joinBtn.dataset.gameId;
                Utils.navigateTo('join', { game_id: gameId });
            });
        }
        
        return card;
    }
    
    function showRules() {
        const rulesText = `
Rummikub Rules:

OBJECTIVE: Be the first player to play all tiles from your rack.

SETUP: Each player starts with 14 tiles.

VALID COMBINATIONS:
• Groups: 3-4 tiles of same number, different colors (e.g., 7 red, 7 blue, 7 black)
• Runs: 3+ consecutive numbers of same color (e.g., 4-5-6 red)

INITIAL MELD: Your first play must total at least 30 points.

GAMEPLAY:
• On your turn: Either play tiles OR draw one tile
• You can rearrange existing melds on the board
• All melds must remain valid after your turn

JOKERS: Can represent any tile. Can be retrieved by playing the actual tile.

WIN: First player to play all tiles wins!
        `;
        
        alert(rulesText);
    }
});