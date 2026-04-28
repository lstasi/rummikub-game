// Main JavaScript utilities for Rummikub Online

// API base URL
const API_BASE = '/api/v1';

// Utility functions
const Utils = {
    // Get URL parameters
    getUrlParams() {
        const params = new URLSearchParams(window.location.search);
        const result = {};
        for (const [key, value] of params) {
            result[key] = value;
        }
        return result;
    },
    
    // Navigate to a page with optional parameters
    navigateTo(page, params = {}) {
        const url = new URL(window.location.origin);
        url.searchParams.set('page', page);
        
        // Preserve lang parameter if it exists
        const currentParams = this.getUrlParams();
        if (currentParams.lang) {
            url.searchParams.set('lang', currentParams.lang);
        }
        
        for (const [key, value] of Object.entries(params)) {
            if (value) {
                url.searchParams.set(key, value);
            }
        }
        
        window.location.href = url.toString();
    },
    
    // Show/hide loading state
    showLoading(element, show = true) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.style.display = show ? 'block' : 'none';
        }
    },
    
    // Show error message
    showError(element, message) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            // Clear existing content
            element.innerHTML = '';
            
            // Create message span
            const messageSpan = document.createElement('span');
            messageSpan.textContent = message;
            messageSpan.className = 'error-message';
            
            // Create close button
            const closeBtn = document.createElement('button');
            closeBtn.textContent = '×';
            closeBtn.className = 'error-close';
            closeBtn.setAttribute('aria-label', 'Close error');
            closeBtn.onclick = () => this.hideError(element);
            
            // Append elements
            element.appendChild(messageSpan);
            element.appendChild(closeBtn);
            element.style.display = 'block';
        }
    },
    
    // Hide error message
    hideError(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.style.display = 'none';
        }
    },
    
    // Format timestamp
    formatTime(isoString) {
        const date = new Date(isoString);
        const now = new Date();
        const diff = Math.floor((now - date) / 60000); // minutes
        
        if (diff < 1) return 'Just now';
        if (diff < 60) return `${diff}m ago`;
        if (diff < 1440) return `${Math.floor(diff / 60)}h ago`;
        return date.toLocaleDateString();
    },
    
    // Generate short ID for display
    shortId(id) {
        return id ? id.substring(0, 8) : '';
    }
};

// API wrapper
const API = {
    async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',  // Include credentials (cookies, Basic Auth) in requests
            ...options
        };
        
        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }
        
        try {
            const response = await fetch(url, config);
            let data;
            
            try {
                data = await response.json();
            } catch (parseError) {
                data = { error: { message: 'Invalid JSON response', raw: await response.text() } };
            }
            
            if (!response.ok) {
                const error = new Error(data.error?.message || `HTTP ${response.status}`);
                error.response = {
                    status: response.status,
                    statusText: response.statusText,
                    data: data
                };
                error.requestUrl = url;
                error.requestConfig = config;
                throw error;
            }
            
            return data;
        } catch (error) {
            console.error('API request failed:', { url, config, error });
            throw error;
        }
    },
    
    // Game endpoints
    async getGames(status = null) {
        const endpoint = status ? `/games?status=${status}` : '/games';
        return this.request(endpoint);
    },
    
    async getMyGames() {
        return this.request('/games/my-games');
    },
    
    async createGame(numPlayers) {
        return this.request('/games', {
            method: 'POST',
            body: { num_players: numPlayers }
        });
    },
    
    async joinGame(gameId) {
        return this.request(`/games/${gameId}/players`, {
            method: 'POST',
            body: {}
        });
    },
    
    async getGameState(gameId, playerId) {
        return this.request(`/games/${gameId}/players/${playerId}`);
    },
    
    async playTiles(gameId, playerId, melds) {
        return this.request(`/games/${gameId}/players/${playerId}/actions/play`, {
            method: 'POST',
            body: { melds }
        });
    },
    
    async drawTile(gameId, playerId) {
        return this.request(`/games/${gameId}/players/${playerId}/actions/draw`, {
            method: 'POST',
            body: {}
        });
    }
};

// Game state management
const GameState = {
    current: null,
    playerId: null,
    gameId: null,
    
    // Save game info to localStorage (player name comes from Auth header, not stored)
    save() {
        localStorage.setItem('rummikub_game', JSON.stringify({
            gameId: this.gameId,
            playerId: this.playerId
        }));
    },
    
    // Load game info from localStorage
    load() {
        const saved = localStorage.getItem('rummikub_game');
        if (saved) {
            const data = JSON.parse(saved);
            this.gameId = data.gameId;
            this.playerId = data.playerId;
        }
    },
    
    // Clear game info
    clear() {
        localStorage.removeItem('rummikub_game');
        this.current = null;
        this.playerId = null;
        this.gameId = null;
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    GameState.load();
    
    // Initialize i18n if available
    if (window.I18n) {
        I18n.init();
    }
    
    // Check if we have URL parameters for direct joining
    const params = Utils.getUrlParams();
    if (params.game_id && params.name && !params.page) {
        // Direct join via URL parameters
        Utils.navigateTo('game', { game_id: params.game_id, name: params.name });
    }
});

// Export for global use
window.Utils = Utils;
window.API = API;
window.GameState = GameState;