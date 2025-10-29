# Jitsi Meet Integration

## Overview

This document describes the integration of Jitsi Meet video conferencing into the Rummikub game to enable real-time audio and video communication between players during gameplay.

## Integration Approach

### Technology Choice: Jitsi Meet External API

We use the **Jitsi Meet External API** for the following reasons:

1. **Easy Integration**: Simple JavaScript API that can be embedded in any web page
2. **No Backend Changes**: Pure frontend integration, no server-side modifications needed
3. **Flexibility**: Supports both public Jitsi servers (meet.jit.si) and self-hosted instances
4. **Feature-Rich**: Built-in controls for audio/video muting, screen sharing, chat, etc.
5. **Free & Open Source**: No licensing costs, fully open-source solution
6. **Cross-Platform**: Works on desktop browsers, mobile browsers, with automatic device adaptation

### Embedded vs External

**Chosen Approach: Embedded Integration**

- Video conference embedded directly in the game screen
- Appears as a collapsible panel in the game UI
- Maintains game flow without requiring separate window/tab
- Automatic room creation based on game ID

Alternative (not implemented): External link to Jitsi Meet in a separate window - rejected because it disrupts game flow and requires manual room management.

## Architecture

### Frontend Components

#### 1. Jitsi Container Component
- Location: Added to `static/pages/game.html`
- Collapsible panel in the game interface
- Can be minimized to save screen space during gameplay
- Positioned to not obstruct game board or player rack

#### 2. Jitsi Controller Module
- Location: `static/js/jitsi.js` (new file)
- Manages Jitsi Meet API lifecycle
- Handles conference initialization and cleanup
- Provides controls for mute/unmute, video on/off
- Manages UI state (expanded/collapsed)

#### 3. Integration Points
- Initialized when game screen loads
- Room name derived from game ID (ensures players in same game join same room)
- User name derived from player name
- Automatically disposes when leaving game screen

### Configuration

#### Environment Variables
```bash
# Jitsi server configuration (optional, defaults to meet.jit.si)
JITSI_DOMAIN=meet.jit.si

# Feature flags
JITSI_ENABLED=true
```

#### JavaScript Configuration
Configuration is passed to the Jitsi API during initialization:

```javascript
const jitsiConfig = {
    domain: 'meet.jit.si', // Configurable
    roomName: gameId,
    parentNode: document.getElementById('jitsi-container'),
    width: '100%',
    height: '100%',
    userInfo: {
        displayName: playerName
    },
    configOverwrite: {
        startWithAudioMuted: false,
        startWithVideoMuted: true,
        enableWelcomePage: false,
        prejoinPageEnabled: false,
        disableDeepLinking: true
    },
    interfaceConfigOverwrite: {
        TOOLBAR_BUTTONS: [
            'microphone', 'camera', 'hangup',
            'chat', 'raisehand', 'tileview'
        ],
        SHOW_JITSI_WATERMARK: false,
        SHOW_WATERMARK_FOR_GUESTS: false
    }
};
```

## UI Design

### Game Screen Layout

```
┌─────────────────────────────────────────────────────┐
│ Header: Game Info & Controls                        │
├──────────────────────────┬──────────────────────────┤
│                          │                          │
│                          │  Video Conference Panel  │
│                          │  [Collapsible]           │
│  Board Area              │  - Player 1 video        │
│  (Main game board)       │  - Player 2 video        │
│                          │  - Player 3 video        │
│                          │  - Player 4 video        │
│                          │                          │
│                          │  Controls:               │
│                          │  [🎤] [📹] [💬] [_]      │
├──────────────────────────┴──────────────────────────┤
│ Player Rack: My Tiles                               │
├─────────────────────────────────────────────────────┤
│ Actions Panel: Play/Draw/End Turn                   │
└─────────────────────────────────────────────────────┘
```

### Responsive Behavior

**Desktop (> 1024px)**:
- Video panel on right side of board
- Default width: 300-400px
- Can be minimized to icon bar

**Tablet (768px - 1024px)**:
- Video panel overlays board area (floating)
- Smaller default size
- Can be minimized to corner icon

**Mobile (< 768px)**:
- Video panel as full-screen overlay (toggle view)
- Button to switch between game and video view
- Picture-in-picture mode where supported

### UI Controls

#### Video Panel Controls
1. **Minimize/Maximize Button** - Collapse panel to icon bar
2. **Microphone Toggle** - Mute/unmute audio
3. **Camera Toggle** - Enable/disable video
4. **Chat Button** - Open Jitsi chat sidebar
5. **Leave Call Button** - Disconnect from video conference

#### State Indicators
- Microphone muted: Red indicator on mic icon
- Video disabled: Camera icon crossed out
- Connection status: Green/yellow/red dot
- Participant count: Number badge

## Implementation Details

### Security & Privacy

1. **No Recording by Default**: Video is not recorded unless explicitly enabled
2. **Room Privacy**: Rooms use unique game IDs, making them hard to guess
3. **Optional Participation**: Players can join game without enabling video/audio
4. **Self-Hosted Option**: Organizations can use their own Jitsi server

### Performance Considerations

1. **Lazy Loading**: Jitsi API loaded only when needed (game screen)
2. **Bandwidth**: Video quality adapts to available bandwidth
3. **CPU Usage**: Video codec optimization handled by Jitsi
4. **Mobile Battery**: Option to disable video on mobile to save battery

### Browser Compatibility

- **Chrome/Edge**: Full support
- **Firefox**: Full support
- **Safari**: Full support (iOS 14.3+)
- **Mobile Browsers**: Supported on modern iOS/Android

Requires:
- WebRTC support
- MediaDevices API access
- User permission for camera/microphone

## User Experience Flow

### Joining Game with Video

1. Player navigates to game screen
2. Video panel appears (collapsed by default)
3. Player clicks "Join Video Call" button
4. Browser prompts for camera/microphone permissions
5. After granting permissions, player joins video room
6. Other players' videos appear automatically
7. Player can start/stop video, mute/unmute at any time

### During Gameplay

1. Video panel stays visible but minimized by default
2. Player can expand to see larger video feeds
3. Visual indicators show who is speaking
4. Video doesn't interfere with game controls
5. Chat available for text communication

### Leaving Game

1. Player clicks "Leave Game" or closes browser
2. Jitsi connection automatically disconnects
3. Video resources cleaned up
4. Other players notified of departure

## Configuration Options

### Per-Game Settings (Future Enhancement)

Potential future features:
- Game creator can enable/disable video for that game
- Maximum participants in video call
- Default audio/video state (on/off)
- Recording permissions

### User Preferences (Future Enhancement)

Potential user settings:
- Default microphone/camera selection
- Video quality preference
- Background blur/virtual background
- Audio input/output devices

## Deployment Considerations

### Using Public Jitsi Instance (meet.jit.si)

**Pros**:
- No infrastructure needed
- Zero configuration
- Always up-to-date
- Free to use

**Cons**:
- Dependent on external service
- Limited control over features
- Potential privacy concerns
- Usage limits may apply

**Configuration**: No changes needed, works out of the box.

### Using Self-Hosted Jitsi Instance

**Pros**:
- Full control over infrastructure
- Better privacy
- Customizable features
- No external dependencies

**Cons**:
- Requires server infrastructure
- Maintenance overhead
- SSL certificates needed
- More complex setup

**Configuration**:
1. Deploy Jitsi Meet server (see: https://jitsi.github.io/handbook/docs/devops-guide/devops-guide-quickstart)
2. Set environment variable: `JITSI_DOMAIN=your-jitsi-server.com`
3. Update `static/js/jitsi.js` configuration

### Docker Deployment

For self-hosted Jitsi with the Rummikub app:

```yaml
# docker-compose.yml addition
services:
  jitsi:
    image: jitsi/web:stable
    ports:
      - "8443:443"
      - "8000:80"
    environment:
      - ENABLE_AUTH=0
      - ENABLE_GUESTS=1
    volumes:
      - ./jitsi-config:/config
```

## Testing Strategy

### Manual Testing Checklist

- [ ] Video panel loads correctly on game screen
- [ ] Multiple players can join same video room
- [ ] Audio/video controls work (mute/unmute)
- [ ] Panel can be minimized and restored
- [ ] Video works on different browsers (Chrome, Firefox, Safari)
- [ ] Mobile responsive behavior works correctly
- [ ] Video disconnects when leaving game
- [ ] Error handling when camera/microphone denied
- [ ] Performance acceptable with 4 players on video

### Automated Testing

No automated tests for Jitsi integration due to:
- External dependency on Jitsi API
- Requires real media devices
- Complex WebRTC interactions

Integration is tested manually through user acceptance testing.

## Future Enhancements

### Phase 1 (Current)
- [x] Basic video/audio integration
- [x] Collapsible panel UI
- [x] Essential controls (mute/camera)

### Phase 2 (Future)
- [ ] Picture-in-picture mode
- [ ] Screen sharing for showing tile strategies
- [ ] Recording game sessions
- [ ] Virtual backgrounds
- [ ] Noise suppression

### Phase 3 (Future)
- [ ] Game-specific video layouts
- [ ] Integrated reactions/emojis
- [ ] Video highlights at game end
- [ ] Replay with audio commentary

## Troubleshooting

### Common Issues

**Issue**: Video panel is blank
- **Cause**: Jitsi API failed to load
- **Solution**: Check browser console, verify network connectivity

**Issue**: Camera/microphone not working
- **Cause**: Browser permissions denied
- **Solution**: Check browser settings, grant permissions

**Issue**: Poor video quality
- **Cause**: Limited bandwidth
- **Solution**: Reduce video quality or disable video, use audio only

**Issue**: Echo or audio feedback
- **Cause**: Multiple devices playing audio
- **Solution**: Use headphones or mute one device

## References

- [Jitsi Meet External API Documentation](https://jitsi.github.io/handbook/docs/dev-guide/dev-guide-iframe)
- [Jitsi Configuration Options](https://github.com/jitsi/jitsi-meet/blob/master/config.js)
- [Self-Hosting Guide](https://jitsi.github.io/handbook/docs/devops-guide/)
- [WebRTC Best Practices](https://webrtc.org/getting-started/overview)
