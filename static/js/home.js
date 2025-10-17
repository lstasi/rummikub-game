// Home page JavaScript for Rummikub Online - Redesigned

document.addEventListener('DOMContentLoaded', async () => {
    // DOM elements
    const myGamesList = document.getElementById('my-games-list');
    const availableGamesList = document.getElementById('available-games-list');
    const noMyGames = document.getElementById('no-my-games');
    const noAvailableGames = document.getElementById('no-available-games');
    const quickCreateBtn = document.getElementById('quick-create-btn');
    const numPlayersSelect = document.getElementById('num-players-select');
    const howToPlayBtn = document.getElementById('how-to-play-btn');
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const playerNameDisplay = document.getElementById('player-name-display');
    const playerInfo = document.getElementById('player-info');
    
    // Load game state (for gameId and playerId only)
    GameState.load();
    
    // Load both game lists on page load
    await loadAllGames();
    
    // Set up periodic refresh for both lists
    setInterval(loadAllGames, 5000); // Refresh every 5 seconds
    
    // Event listeners
    quickCreateBtn.addEventListener('click', async () => {
        await createAndJoinGame();
    });
    
    howToPlayBtn.addEventListener('click', () => {
        showRules();
    });
    
    // Load both my games and available games
    async function loadAllGames() {
        await Promise.all([
            loadMyGames(),
            loadAvailableGames()
        ]);
    }
    
    // Load games where the current player has joined
    async function loadMyGames() {
        try {
            const response = await API.getMyGames();
            displayMyGames(response.games || []);
        } catch (err) {
            console.error('Failed to load my games:', err);
            // If authentication fails or no player context, just show empty list
            displayMyGames([]);
        }
    }
    
    // Load available games (waiting for players)
    async function loadAvailableGames() {
        try {
            const response = await API.getGames('waiting_for_players');
            displayAvailableGames(response.games || []);
        } catch (err) {
            console.error('Failed to load available games:', err);
            displayAvailableGames([]);
        }
    }
    
    // Display my games list
    function displayMyGames(games) {
        myGamesList.innerHTML = '';
        
        if (games.length === 0) {
            noMyGames.style.display = 'block';
            return;
        }
        
        noMyGames.style.display = 'none';
        
        games.forEach(game => {
            const gameCard = createMyGameCard(game);
            myGamesList.appendChild(gameCard);
        });
    }
    
    // Display available games list
    function displayAvailableGames(games) {
        availableGamesList.innerHTML = '';
        
        if (games.length === 0) {
            noAvailableGames.style.display = 'block';
            return;
        }
        
        noAvailableGames.style.display = 'none';
        
        games.forEach(game => {
            const gameCard = createAvailableGameCard(game);
            availableGamesList.appendChild(gameCard);
        });
    }
    
    // Create game card for "My Games" section
    function createMyGameCard(game) {
        const card = document.createElement('div');
        card.className = 'game-card my-game-card';
        
        const statusClass = game.status === 'waiting_for_players' ? 'status-waiting' : 
                          game.status === 'in_progress' ? 'status-in-progress' : 'status-completed';
        
        // Determine the action button based on status
        let actionButton = '';
        if (game.status === 'waiting_for_players') {
            actionButton = `<button class="btn btn-warning resume-btn" data-game-id="${game.game_id}">Wait for Players</button>`;
        } else if (game.status === 'in_progress') {
            actionButton = `<button class="btn btn-primary resume-btn" data-game-id="${game.game_id}">Resume Game</button>`;
        } else if (game.status === 'completed') {
            actionButton = `<button class="btn btn-secondary" disabled>Game Completed</button>`;
        }
        
        // Create player list
        let playersSection = '';
        if (game.players && game.players.length > 0) {
            const playerNames = game.players.map(player => player.name).join(', ');
            playersSection = `<p>Players: ${playerNames}</p>`;
        }
        
        // Show current turn info if game is in progress
        let turnInfo = '';
        if (game.status === 'in_progress' && game.current_player_name) {
            turnInfo = `<p><strong>Current turn:</strong> ${game.current_player_name}</p>`;
        }
        
        card.innerHTML = `
            <h3>Game ${Utils.shortId(game.game_id)}</h3>
            <p><span class="game-status ${statusClass}">${game.status.replace('_', ' ')}</span></p>
            <p>Players: ${game.players.length}/${game.num_players}</p>
            ${playersSection}
            ${turnInfo}
            <p>Created: ${Utils.formatTime(game.created_at)}</p>
            <div style="margin-top: 15px; display: flex; gap: 10px;">
                ${actionButton}
                <button class="btn btn-danger delete-btn" data-game-id="${game.game_id}">Delete</button>
            </div>
        `;
        
        // Add resume functionality
        const resumeBtn = card.querySelector('.resume-btn');
        if (resumeBtn) {
            resumeBtn.addEventListener('click', () => {
                const gameId = resumeBtn.dataset.gameId;
                resumeGame(gameId);
            });
        }
        
        // Add delete functionality
        const deleteBtn = card.querySelector('.delete-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                const gameId = deleteBtn.dataset.gameId;
                deleteGameConfirm(gameId);
            });
        }
        
        return card;
    }
    
    // Create game card for "Available Games" section
    function createAvailableGameCard(game) {
        const card = document.createElement('div');
        card.className = 'game-card available-game-card';
        
        const statusClass = 'status-waiting';
        
        // Create player list
        let playersSection = '';
        if (game.players && game.players.length > 0) {
            const playerNames = game.players.map(player => player.name).join(', ');
            playersSection = `<p>Players: ${playerNames}</p>`;
        }
        
        card.innerHTML = `
            <h3>Game ${Utils.shortId(game.game_id)}</h3>
            <p><span class="game-status ${statusClass}">${game.status.replace('_', ' ')}</span></p>
            <p>Players: ${game.players.length}/${game.num_players}</p>
            ${playersSection}
            <p>Created: ${Utils.formatTime(game.created_at)}</p>
            <div style="margin-top: 15px;">
                <button class="btn btn-primary join-btn" data-game-id="${game.game_id}">Join Game</button>
            </div>
        `;
        
        // Add join functionality
        const joinBtn = card.querySelector('.join-btn');
        if (joinBtn) {
            joinBtn.addEventListener('click', () => {
                const gameId = joinBtn.dataset.gameId;
                joinGameDirect(gameId);
            });
        }
        
        return card;
    }
    
    // Create a new game and automatically join it
    async function createAndJoinGame() {
        try {
            Utils.hideError(error);
            Utils.showLoading(loading, true);
            quickCreateBtn.disabled = true;
            
            const numPlayers = parseInt(numPlayersSelect.value);
            
            // The backend automatically joins the creator (from Auth header)
            const response = await API.createGame(numPlayers);
            const gameId = response.game_id;
            
            // The backend returns the authenticated player's ID
            // Find the first player (which is the creator who just joined)
            if (response.players && response.players.length > 0) {
                const player = response.players[0]; // Creator is always first
                
                // Save game state (without player name - it comes from backend)
                GameState.gameId = gameId;
                GameState.playerId = player.id;
                GameState.save();
                
                // Navigate to game page
                Utils.navigateTo('game', { game_id: gameId });
            } else {
                throw new Error('Failed to find player in game after creation');
            }
            
        } catch (err) {
            console.error('Failed to create game:', err);
            Utils.showLoading(loading, false);
            quickCreateBtn.disabled = false;
            
            let errorMessage = 'Failed to create game. Please try again.';
            if (err.message.includes('Authentication required') || err.message.includes('401')) {
                errorMessage = 'Authentication required. Please refresh the page and enter your player name in the browser prompt.';
            }
            
            Utils.showError(error, errorMessage);
            
            // Hide error after 5 seconds
            setTimeout(() => Utils.hideError(error), 5000);
        }
    }
    
    // Join an available game directly
    async function joinGameDirect(gameId) {
        try {
            Utils.hideError(error);
            
            // Join the game (player name comes from Auth header)
            const response = await API.joinGame(gameId);
            
            // Backend returns the authenticated player's info
            // Find the player who just joined (the one with the matching name from Auth)
            if (response.players && response.players.length > 0) {
                // The backend returns the player's ID in the response
                // We need to find which player ID belongs to us
                // The easiest way is to look for the player with rack data (only visible to us)
                let myPlayer = null;
                for (const player of response.players) {
                    if (player.rack && player.rack.tiles) {
                        myPlayer = player;
                        break;
                    }
                }
                
                if (myPlayer) {
                    // Save game state (without player name - it comes from backend)
                    GameState.gameId = gameId;
                    GameState.playerId = myPlayer.id;
                    GameState.save();
                    
                    // Navigate to game page
                    Utils.navigateTo('game', { game_id: gameId });
                } else {
                    throw new Error('Failed to find player in game after joining');
                }
            } else {
                throw new Error('Failed to find player in game after joining');
            }
            
        } catch (err) {
            console.error('Failed to join game:', err);
            
            let errorMessage = 'Failed to join game. Please try again.';
            if (err.message.includes('not found')) {
                errorMessage = 'Game not found.';
            } else if (err.message.includes('full')) {
                errorMessage = 'Game is full. Cannot join.';
            } else if (err.message.includes('completed')) {
                errorMessage = 'Game has already ended.';
            } else if (err.message.includes('already')) {
                errorMessage = 'You are already in this game.';
            } else if (err.message.includes('Authentication required') || err.message.includes('401')) {
                errorMessage = 'Authentication required. Please refresh the page and enter your player name in the browser prompt.';
            }
            
            Utils.showError(error, errorMessage);
            
            // Hide error after 5 seconds
            setTimeout(() => Utils.hideError(error), 5000);
        }
    }
    
    // Resume a game (navigate to game page)
    async function resumeGame(gameId) {
        try {
            // Check if we have playerId in localStorage
            GameState.load();
            
            // If localStorage is missing or doesn't have playerId for this game, re-join
            if (!GameState.playerId || GameState.gameId !== gameId) {
                Utils.hideError(error);
                
                // Re-join the game to get our playerId (backend uses Auth header)
                const response = await API.joinGame(gameId);
                
                // Find our player (the one with rack data visible to us)
                let myPlayer = null;
                for (const player of response.players) {
                    if (player.rack && player.rack.tiles) {
                        myPlayer = player;
                        break;
                    }
                }
                
                if (myPlayer) {
                    // Save game state
                    GameState.gameId = gameId;
                    GameState.playerId = myPlayer.id;
                    GameState.save();
                } else {
                    throw new Error('Failed to find player in game after re-joining');
                }
            }
            
            // Navigate to game page
            Utils.navigateTo('game', { game_id: gameId });
            
        } catch (err) {
            console.error('Failed to resume game:', err);
            
            let errorMessage = 'Failed to resume game. Please try again.';
            if (err.message.includes('already')) {
                // If already in game but we don't have playerId, we need to handle this
                // This shouldn't happen normally, but if it does, we can try to get the game state
                errorMessage = 'Already in game. Refreshing...';
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else if (err.message.includes('full')) {
                errorMessage = 'Game is full.';
            } else if (err.message.includes('not found')) {
                errorMessage = 'Game not found.';
            }
            
            Utils.showError(error, errorMessage);
            setTimeout(() => Utils.hideError(error), 5000);
        }
    }
    
    // Delete a game with confirmation
    async function deleteGameConfirm(gameId) {
        if (!confirm('Are you sure you want to delete this game? This action cannot be undone.')) {
            return;
        }
        
        try {
            Utils.hideError(error);
            
            // Delete the game
            await API.deleteGame(gameId);
            
            // If this was the current game, clear it from localStorage
            GameState.load();
            if (GameState.gameId === gameId) {
                GameState.clear();
            }
            
            // Refresh both game lists immediately
            await loadAllGames();
            
        } catch (err) {
            console.error('Failed to delete game:', err);
            
            let errorMessage = 'Failed to delete game. Please try again.';
            if (err.message.includes('not found')) {
                errorMessage = 'Game not found. It may have already been deleted.';
                // Refresh the lists since the game is gone
                await loadAllGames();
            }
            
            Utils.showError(error, errorMessage);
            
            // Hide error after 5 seconds
            setTimeout(() => Utils.hideError(error), 5000);
        }
    }
    
    // Show rules dialog
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