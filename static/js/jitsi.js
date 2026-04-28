// Jitsi Meet integration module for video/audio conferencing

class JitsiManager {
    constructor() {
        this.api = null;
        this.isInitialized = false;
        this.isMinimized = false;
        this.domain = 'meet.jit.si'; // Can be configured via environment
        this.roomName = null;
        this.playerName = null;
    }

    /**
     * Initialize Jitsi Meet conference
     * @param {string} gameId - The game ID to use as room name
     * @param {string} playerName - The player's display name
     */
    async initialize(gameId, playerName) {
        if (this.isInitialized) {
            console.warn('Jitsi already initialized');
            return;
        }

        this.roomName = `rummikub-${gameId}`;
        this.playerName = playerName || 'Player';

        // Wait for Jitsi External API to load
        if (typeof JitsiMeetExternalAPI === 'undefined') {
            console.error('Jitsi Meet External API not loaded');
            return;
        }

        try {
            const containerElement = document.getElementById('jitsi-meet-container');
            if (!containerElement) {
                console.error('Jitsi container element not found');
                return;
            }

            const options = {
                roomName: this.roomName,
                width: '100%',
                height: '100%',
                parentNode: containerElement,
                userInfo: {
                    displayName: this.playerName
                },
                configOverwrite: {
                    startWithAudioMuted: false,
                    startWithVideoMuted: true,
                    disableDeepLinking: true,
                    prejoinPageEnabled: false,
                    enableWelcomePage: false,
                    enableClosePage: false,
                    defaultLanguage: 'en',
                    disableInviteFunctions: true,
                    doNotStoreRoom: true,
                    startScreenSharing: false,
                    enableNoisyMicDetection: true
                },
                interfaceConfigOverwrite: {
                    TOOLBAR_BUTTONS: [
                        'microphone',
                        'camera',
                        'hangup',
                        'chat',
                        'raisehand',
                        'tileview',
                        'settings'
                    ],
                    SHOW_JITSI_WATERMARK: false,
                    SHOW_WATERMARK_FOR_GUESTS: false,
                    SHOW_BRAND_WATERMARK: false,
                    SHOW_POWERED_BY: false,
                    DISABLE_JOIN_LEAVE_NOTIFICATIONS: false,
                    DISABLE_VIDEO_BACKGROUND: false,
                    DEFAULT_BACKGROUND: '#474747',
                    DEFAULT_REMOTE_DISPLAY_NAME: 'Player',
                    MOBILE_APP_PROMO: false
                }
            };

            this.api = new JitsiMeetExternalAPI(this.domain, options);
            this.isInitialized = true;

            // Set up event listeners
            this.setupEventListeners();

            console.log(`Jitsi Meet initialized for room: ${this.roomName}`);
        } catch (error) {
            console.error('Error initializing Jitsi Meet:', error);
        }
    }

    /**
     * Set up Jitsi event listeners
     */
    setupEventListeners() {
        if (!this.api) return;

        this.api.addListener('videoConferenceJoined', (event) => {
            console.log('Video conference joined:', event);
            this.updateConnectionStatus('connected');
        });

        this.api.addListener('videoConferenceLeft', (event) => {
            console.log('Video conference left:', event);
            this.updateConnectionStatus('disconnected');
        });

        this.api.addListener('participantJoined', (event) => {
            console.log('Participant joined:', event);
        });

        this.api.addListener('participantLeft', (event) => {
            console.log('Participant left:', event);
        });

        this.api.addListener('audioMuteStatusChanged', (event) => {
            console.log('Audio mute status changed:', event.muted);
            this.updateAudioStatus(event.muted);
        });

        this.api.addListener('videoMuteStatusChanged', (event) => {
            console.log('Video mute status changed:', event.muted);
            this.updateVideoStatus(event.muted);
        });

        this.api.addListener('readyToClose', () => {
            console.log('Jitsi ready to close');
            this.dispose();
        });
    }

    /**
     * Toggle microphone mute
     */
    toggleAudio() {
        if (!this.api) return;
        this.api.executeCommand('toggleAudio');
    }

    /**
     * Toggle video mute
     */
    toggleVideo() {
        if (!this.api) return;
        this.api.executeCommand('toggleVideo');
    }

    /**
     * Toggle chat
     */
    toggleChat() {
        if (!this.api) return;
        this.api.executeCommand('toggleChat');
    }

    /**
     * Hang up / leave conference
     */
    hangup() {
        if (!this.api) return;
        this.api.executeCommand('hangup');
    }

    /**
     * Toggle minimize/maximize video panel
     */
    toggleMinimize() {
        const videoPanel = document.getElementById('jitsi-video-panel');
        const minimizeBtn = document.getElementById('jitsi-minimize-btn');
        
        if (!videoPanel) return;

        this.isMinimized = !this.isMinimized;
        
        if (this.isMinimized) {
            videoPanel.classList.add('minimized');
            if (minimizeBtn) {
                minimizeBtn.textContent = '□';
                minimizeBtn.title = 'Maximize video';
            }
        } else {
            videoPanel.classList.remove('minimized');
            if (minimizeBtn) {
                minimizeBtn.textContent = '_';
                minimizeBtn.title = 'Minimize video';
            }
        }
    }

    /**
     * Update connection status indicator
     */
    updateConnectionStatus(status) {
        const indicator = document.getElementById('jitsi-connection-status');
        if (!indicator) return;

        indicator.className = 'connection-status';
        if (status === 'connected') {
            indicator.classList.add('connected');
            indicator.title = 'Connected';
        } else if (status === 'connecting') {
            indicator.classList.add('connecting');
            indicator.title = 'Connecting...';
        } else {
            indicator.classList.add('disconnected');
            indicator.title = 'Disconnected';
        }
    }

    /**
     * Update audio status indicator
     */
    updateAudioStatus(muted) {
        const audioBtn = document.getElementById('jitsi-audio-btn');
        if (!audioBtn) return;

        if (muted) {
            audioBtn.classList.add('muted');
            audioBtn.textContent = '🔇';
            audioBtn.title = 'Unmute microphone';
        } else {
            audioBtn.classList.remove('muted');
            audioBtn.textContent = '🎤';
            audioBtn.title = 'Mute microphone';
        }
    }

    /**
     * Update video status indicator
     */
    updateVideoStatus(muted) {
        const videoBtn = document.getElementById('jitsi-video-btn');
        if (!videoBtn) return;

        if (muted) {
            videoBtn.classList.add('disabled');
            videoBtn.textContent = '📹';
            videoBtn.title = 'Turn on camera';
        } else {
            videoBtn.classList.remove('disabled');
            videoBtn.textContent = '📹';
            videoBtn.title = 'Turn off camera';
        }
    }

    /**
     * Get current participant count
     */
    getParticipantCount() {
        if (!this.api) return 0;
        
        try {
            return this.api.getNumberOfParticipants();
        } catch (error) {
            console.error('Error getting participant count:', error);
            return 0;
        }
    }

    /**
     * Clean up and dispose Jitsi instance
     */
    dispose() {
        if (this.api) {
            try {
                this.api.dispose();
                console.log('Jitsi Meet disposed');
            } catch (error) {
                console.error('Error disposing Jitsi Meet:', error);
            }
            this.api = null;
        }
        this.isInitialized = false;
        this.isMinimized = false;
    }

    /**
     * Check if Jitsi is initialized
     */
    isReady() {
        return this.isInitialized && this.api !== null;
    }
}

// Create global instance
const jitsiManager = new JitsiManager();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { JitsiManager, jitsiManager };
}
