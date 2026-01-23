/**
 * Session Broadcast Channel Module
 * Sincronización entre ventana principal y pantalla externa
 * 
 * Mensajes del protocolo:
 * - SESSION_START    - Nueva sesión iniciada
 * - SESSION_END      - Sesión terminada
 * - THERAPY_CHANGE   - Cambio de terapia (playlist)
 * - PLAY             - Reproducir
 * - PAUSE            - Pausar
 * - STOP             - Detener
 * - TIMER_SYNC       - Sincronización de tiempo
 * - VOLUME_CHANGE    - Cambio de volumen
 * - COLOR_CHANGE     - Cambio de color (Arduino)
 * - PING/PONG        - Keep-alive
 */

const SessionChannel = (() => {
    // ─────────────────────────────────────────────────────
    // Constants
    // ─────────────────────────────────────────────────────
    const CHANNEL_NAME = 'kryon-session-channel';
    const PING_INTERVAL = 5000;
    const PONG_TIMEOUT = 2000;
    
    // ─────────────────────────────────────────────────────
    // State
    // ─────────────────────────────────────────────────────
    let channel = null;
    let role = null; // 'controller' | 'display'
    let isConnected = false;
    let peerConnected = false;
    let pingInterval = null;
    let pongTimeout = null;
    let lastPong = null;
    
    const listeners = {
        message: [],
        peerConnect: [],
        peerDisconnect: [],
        error: [],
    };
    
    // Current state to sync
    let currentState = {
        therapy: null,
        session: null,
        isPlaying: false,
        elapsed: 0,
        total: 0,
        volume: 80,
        colorMode: null,
        playlist: null,
        playlistIndex: 0,
        playVideo: true,
        videoOnly: false,
    };
    
    // ─────────────────────────────────────────────────────
    // Event System
    // ─────────────────────────────────────────────────────
    function on(event, callback) {
        if (listeners[event]) {
            listeners[event].push(callback);
        }
        return () => off(event, callback);
    }
    
    function off(event, callback) {
        if (listeners[event]) {
            listeners[event] = listeners[event].filter(cb => cb !== callback);
        }
    }
    
    function emit(event, data) {
        if (listeners[event]) {
            listeners[event].forEach(cb => {
                try { cb(data); } catch (e) { console.error('Listener error:', e); }
            });
        }
    }
    
    // ─────────────────────────────────────────────────────
    // Channel Management
    // ─────────────────────────────────────────────────────
    function init(channelRole) {
        if (channel) {
            console.warn('Channel already initialized');
            return;
        }
        
        if (!('BroadcastChannel' in window)) {
            console.error('BroadcastChannel not supported');
            return;
        }
        
        role = channelRole;
        channel = new BroadcastChannel(CHANNEL_NAME);
        
        channel.onmessage = handleMessage;
        channel.onmessageerror = (e) => {
            console.error('Channel message error:', e);
            emit('error', e);
        };
        
        isConnected = true;
        
        // Announce presence
        send('HELLO', { role });
        
        // Start ping if controller
        if (role === 'controller') {
            startPing();
        }
        
        console.log(`SessionChannel initialized as ${role}`);
    }
    
    function destroy() {
        if (pingInterval) {
            clearInterval(pingInterval);
            pingInterval = null;
        }
        
        if (pongTimeout) {
            clearTimeout(pongTimeout);
            pongTimeout = null;
        }
        
        if (channel) {
            send('GOODBYE', { role });
            channel.close();
            channel = null;
        }
        
        isConnected = false;
        peerConnected = false;
        role = null;
    }
    
    // ─────────────────────────────────────────────────────
    // Message Handling
    // ─────────────────────────────────────────────────────
    function handleMessage(event) {
        const { type, payload, from, timestamp } = event.data;
        
        // Ignore own messages
        if (from === role) return;
        
        switch (type) {
            case 'HELLO':
                peerConnected = true;
                lastPong = Date.now();
                emit('peerConnect', payload);
                // Send current state to new peer
                if (role === 'controller') {
                    sendFullState();
                }
                break;
                
            case 'GOODBYE':
                peerConnected = false;
                emit('peerDisconnect', payload);
                break;
                
            case 'PING':
                send('PONG', { timestamp: payload.timestamp });
                break;
                
            case 'PONG':
                lastPong = Date.now();
                peerConnected = true;
                if (pongTimeout) {
                    clearTimeout(pongTimeout);
                    pongTimeout = null;
                }
                break;
                
            case 'FULL_STATE':
                // Display receives full state from controller
                if (role === 'display') {
                    currentState = { ...currentState, ...payload };
                }
                emit('message', { type, payload });
                break;
                
            default:
                // Update local state based on message
                updateStateFromMessage(type, payload);
                emit('message', { type, payload });
        }
    }
    
    function updateStateFromMessage(type, payload) {
        switch (type) {
            case 'SESSION_START':
                currentState.session = payload.session;
                currentState.therapy = payload.therapy;
                currentState.total = payload.duration || 0;
                currentState.elapsed = 0;
                currentState.isPlaying = false;
                currentState.colorMode = payload.colorMode || null;
                if (payload.playlist !== undefined) currentState.playlist = payload.playlist;
                if (payload.playlistIndex !== undefined) currentState.playlistIndex = payload.playlistIndex;
                if (payload.playVideo !== undefined) currentState.playVideo = payload.playVideo;
                if (payload.videoOnly !== undefined) currentState.videoOnly = payload.videoOnly;
                break;
                
            case 'SESSION_END':
                currentState.session = null;
                currentState.therapy = null;
                currentState.isPlaying = false;
                break;
                
            case 'THERAPY_CHANGE':
                currentState.therapy = payload.therapy;
                currentState.total = payload.duration || 0;
                currentState.elapsed = 0;
                currentState.playlistIndex = payload.index || 0;
                currentState.colorMode = payload.colorMode || null;
                if (payload.playVideo !== undefined) currentState.playVideo = payload.playVideo;
                if (payload.videoOnly !== undefined) currentState.videoOnly = payload.videoOnly;
                if (payload.playlist !== undefined) currentState.playlist = payload.playlist;
                break;
                
            case 'PLAY':
                currentState.isPlaying = true;
                break;
                
            case 'PAUSE':
                currentState.isPlaying = false;
                break;
                
            case 'STOP':
                currentState.isPlaying = false;
                break;
                
            case 'TIMER_SYNC':
                currentState.elapsed = payload.elapsed;
                currentState.total = payload.total;
                currentState.isPlaying = payload.isPlaying;
                break;
                
            case 'VOLUME_CHANGE':
                currentState.volume = payload.volume;
                break;
                
            case 'COLOR_CHANGE':
                currentState.colorMode = payload.colorMode;
                break;
                
            case 'PLAYLIST_UPDATE':
                currentState.playlist = payload.playlist;
                currentState.playlistIndex = payload.index;
                break;
        }
    }
    
    // ─────────────────────────────────────────────────────
    // Sending
    // ─────────────────────────────────────────────────────
    function send(type, payload = {}) {
        if (!channel) {
            console.warn('Channel not initialized');
            return false;
        }
        
        channel.postMessage({
            type,
            payload,
            from: role,
            timestamp: Date.now(),
        });
        
        return true;
    }
    
    function sendFullState() {
        send('FULL_STATE', currentState);
    }
    
    // ─────────────────────────────────────────────────────
    // Keep-alive
    // ─────────────────────────────────────────────────────
    function startPing() {
        if (pingInterval) return;
        
        pingInterval = setInterval(() => {
            send('PING', { timestamp: Date.now() });
            
            // Set timeout for pong
            pongTimeout = setTimeout(() => {
                if (lastPong && Date.now() - lastPong > PING_INTERVAL + PONG_TIMEOUT) {
                    if (peerConnected) {
                        peerConnected = false;
                        emit('peerDisconnect', { reason: 'timeout' });
                    }
                }
            }, PONG_TIMEOUT);
            
        }, PING_INTERVAL);
    }
    
    // ─────────────────────────────────────────────────────
    // Controller Commands (for session.html)
    // ─────────────────────────────────────────────────────
    const Controller = {
        startSession(session, therapy, options = {}) {
            currentState.session = session;
            currentState.therapy = therapy;
            currentState.total = options.duration || therapy.default_duration_sec || 600;
            currentState.elapsed = 0;
            currentState.colorMode = options.colorMode || therapy.color_mode || null;
            currentState.playlist = options.playlist || null;
            currentState.playlistIndex = options.playlistIndex || 0;
            currentState.playVideo = options.playVideo !== undefined ? options.playVideo : true;
            currentState.videoOnly = options.videoOnly || false;
            
            send('SESSION_START', {
                session,
                therapy,
                duration: currentState.total,
                colorMode: currentState.colorMode,
                playlist: currentState.playlist,
                playlistIndex: currentState.playlistIndex,
                playVideo: currentState.playVideo,
                videoOnly: currentState.videoOnly,
            });
        },
        
        endSession(status = 'completed') {
            send('SESSION_END', { status, session: currentState.session });
            currentState.session = null;
            currentState.therapy = null;
        },
        
        changeTherapy(therapy, index = 0) {
            // Backwards-compatible signature:
            // changeTherapy(therapy, index)
            // changeTherapy(therapy, index, options)
            const options = arguments.length >= 3 ? (arguments[2] || {}) : {};

            currentState.therapy = therapy;
            currentState.total = options.duration || therapy.default_duration_sec || 600;
            currentState.elapsed = 0;
            currentState.playlist = options.playlist !== undefined ? options.playlist : currentState.playlist;
            currentState.playlistIndex = options.playlistIndex !== undefined ? options.playlistIndex : index;
            currentState.colorMode = options.colorMode || therapy.color_mode || null;
            if (options.playVideo !== undefined) currentState.playVideo = options.playVideo;
            if (options.videoOnly !== undefined) currentState.videoOnly = options.videoOnly;

            send('THERAPY_CHANGE', {
                therapy,
                duration: currentState.total,
                index: currentState.playlistIndex,
                colorMode: currentState.colorMode,
                playlist: currentState.playlist,
                playVideo: currentState.playVideo,
                videoOnly: currentState.videoOnly,
            });
        },
        
        play() {
            currentState.isPlaying = true;
            send('PLAY', {});
        },
        
        pause() {
            currentState.isPlaying = false;
            send('PAUSE', {});
        },
        
        stop() {
            currentState.isPlaying = false;
            send('STOP', {});
        },
        
        syncTimer(elapsed, total, isPlaying) {
            currentState.elapsed = elapsed;
            currentState.total = total;
            currentState.isPlaying = isPlaying;
            send('TIMER_SYNC', { elapsed, total, isPlaying });
        },
        
        setVolume(volume) {
            currentState.volume = volume;
            send('VOLUME_CHANGE', { volume });
        },
        
        setColor(colorMode) {
            currentState.colorMode = colorMode;
            send('COLOR_CHANGE', { colorMode });
        },
        
        updatePlaylist(playlist, index) {
            currentState.playlist = playlist;
            currentState.playlistIndex = index;
            send('PLAYLIST_UPDATE', { playlist, index });
        },
    };
    
    // ─────────────────────────────────────────────────────
    // Getters
    // ─────────────────────────────────────────────────────
    function getState() {
        return { ...currentState };
    }
    
    function getRole() {
        return role;
    }
    
    function isPeerConnected() {
        return peerConnected;
    }
    
    function isChannelConnected() {
        return isConnected;
    }
    
    // ─────────────────────────────────────────────────────
    // Public API
    // ─────────────────────────────────────────────────────
    return {
        // Lifecycle
        init,
        destroy,
        
        // Events
        on,
        off,
        
        // State
        getState,
        getRole,
        isPeerConnected,
        isChannelConnected,
        
        // Sending
        send,
        sendFullState,
        
        // Controller shortcuts
        Controller,
    };
})();

// Export
window.SessionChannel = SessionChannel;
