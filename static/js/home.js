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
            // Load both user's games and available games to join
            const [userGamesResponse, availableGamesResponse] = await Promise.all([
                API.getGames(),
                API.getAvailableGames()
            ]);
            displayGames(userGamesResponse.games || [], availableGamesResponse.games || []);
        } catch (error) {
            console.error('Failed to load games:', error);
            // Don't show error on home page, just show no games
            displayGames([], []);
        }
    }
    
    function displayGames(userGames, availableGames) {
        gamesList.innerHTML = '';
        
        if (userGames.length === 0 && availableGames.length === 0) {
            noGames.style.display = 'block';
            return;
        }
        
        noGames.style.display = 'none';
        
        // Display user's games
        if (userGames.length > 0) {
            const userGamesHeader = document.createElement('h3');
            userGamesHeader.textContent = 'My Games';
            userGamesHeader.style.marginTop = '0';
            gamesList.appendChild(userGamesHeader);
            
            userGames.forEach(game => {
                const gameCard = createGameCard(game, false);
                gamesList.appendChild(gameCard);
            });
        }
        
        // Display available games to join
        if (availableGames.length > 0) {
            const availableGamesHeader = document.createElement('h3');
            availableGamesHeader.textContent = 'Available Games to Join';
            availableGamesHeader.style.marginTop = '20px';
            gamesList.appendChild(availableGamesHeader);
            
            availableGames.forEach(game => {
                const gameCard = createGameCard(game, true);
                gamesList.appendChild(gameCard);
            });
        }
    }
    
    function createGameCard(game, showJoinButton) {
        const card = document.createElement('div');
        card.className = 'game-card';
        
        const statusClass = game.status === 'waiting_for_players' ? 'status-waiting' : 
                          game.status === 'in_progress' ? 'status-in-progress' : 'status-completed';
        
        // Create player names (no links, just display)
        let playersSection = '';
        if (game.players && game.players.length > 0) {
            const playerNames = game.players.map(player => player.name).join(', ');
            playersSection = `<p>Players: ${playerNames}</p>`;
        }
        
        // Show join button for available games, otherwise show status or "View Game" for user's games
        let actionButton = '';
        if (showJoinButton) {
            actionButton = `<button class="btn btn-primary join-btn" data-game-id="${game.game_id}">Join Game</button>`;
        } else if (game.status === 'in_progress' || game.status === 'waiting_for_players') {
            // For user's games, show "View Game" button
            actionButton = `<button class="btn btn-primary view-game-btn" data-game-id="${game.game_id}">View Game</button>`;
        } else {
            actionButton = `<button class="btn btn-secondary" disabled>Game ${game.status.replace('_', ' ')}</button>`;
        }
        
        card.innerHTML = `
            <h3>Game ${Utils.shortId(game.game_id)}</h3>
            <p><span class="game-status ${statusClass}">${game.status.replace('_', ' ')}</span></p>
            <p>Players: ${game.players.length}/${game.num_players}</p>
            ${playersSection}
            <p>Created: ${Utils.formatTime(game.created_at)}</p>
            <div style="margin-top: 15px;">
                ${actionButton}
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
        
        // Add view game functionality
        const viewGameBtn = card.querySelector('.view-game-btn');
        if (viewGameBtn) {
            viewGameBtn.addEventListener('click', () => {
                const gameId = viewGameBtn.dataset.gameId;
                // Navigate to game page with saved player info
                Utils.navigateTo('game', { game_id: gameId });
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