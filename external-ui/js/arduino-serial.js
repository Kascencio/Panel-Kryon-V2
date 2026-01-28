/**
 * Arduino/ESP32 Web Serial API Module
 * Comunicación bidireccional con ESP32 + NeoPixel via USB Serial
 * 
 * Protocolo de comandos (compatible con firmware ESP32):
 * - inicio:modo,intensidad  - Iniciar modo (general, rojo, verde, azul, blanco, intermitente, pausado, cascada, cascrev)
 * - intensidad:0-100        - Cambiar intensidad/brillo
 * - test                    - Iniciar self-test (10s)
 * - test:off                - Cancelar self-test
 * - stop                    - Detener todo
 * - completado              - Alias de stop
 */

const ArduinoSerial = (() => {
    // ─────────────────────────────────────────────────────
    // State
    // ─────────────────────────────────────────────────────
    let port = null;
    let reader = null;
    let writer = null;
    let readLoopRunning = false;
    let connectionState = 'disconnected'; // disconnected, connecting, connected, error
    let lastSentIntensity = -1; // Track last sent value to avoid duplicates
    let intensityDebounceTimer = null;
    
    // Storage key for remembered device
    const STORAGE_KEY = 'arduino_device_info';
    
    const listeners = {
        connect: [],
        disconnect: [],
        data: [],
        error: [],
        stateChange: [],
    };
    
    // ─────────────────────────────────────────────────────
    // Feature Detection
    // ─────────────────────────────────────────────────────
    function isSupported() {
        return 'serial' in navigator;
    }
    
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
    
    function setState(state) {
        connectionState = state;
        emit('stateChange', state);
    }
    
    // ─────────────────────────────────────────────────────
    // Connection
    // ─────────────────────────────────────────────────────
    
    /**
     * Guardar info del dispositivo para auto-reconexión
     */
    function saveDeviceInfo(portInfo) {
        try {
            const info = portInfo.getInfo ? portInfo.getInfo() : {};
            if (info.usbVendorId) {
                localStorage.setItem(STORAGE_KEY, JSON.stringify({
                    usbVendorId: info.usbVendorId,
                    usbProductId: info.usbProductId,
                    savedAt: Date.now()
                }));
                console.log('Dispositivo Arduino guardado para auto-reconexión');
            }
        } catch (e) {
            console.warn('No se pudo guardar info del dispositivo:', e);
        }
    }
    
    /**
     * Obtener info del dispositivo guardado
     */
    function getSavedDeviceInfo() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            return saved ? JSON.parse(saved) : null;
        } catch (e) {
            return null;
        }
    }
    
    /**
     * Olvidar dispositivo guardado
     */
    function forgetDevice() {
        localStorage.removeItem(STORAGE_KEY);
        console.log('Dispositivo Arduino olvidado');
    }
    
    /**
     * Intentar auto-reconexión con dispositivo guardado
     */
    async function autoConnect() {
        if (!isSupported()) return false;
        if (port) return true; // Ya conectado
        
        try {
            // Obtener puertos ya autorizados
            const ports = await navigator.serial.getPorts();
            if (ports.length === 0) return false;
            
            const savedInfo = getSavedDeviceInfo();
            
            // Buscar el puerto guardado o usar el primero disponible
            let targetPort = null;
            
            if (savedInfo) {
                targetPort = ports.find(p => {
                    const info = p.getInfo ? p.getInfo() : {};
                    return info.usbVendorId === savedInfo.usbVendorId &&
                           info.usbProductId === savedInfo.usbProductId;
                });
            }
            
            // Si no encontramos el guardado, usar el primero
            if (!targetPort && ports.length > 0) {
                targetPort = ports[0];
            }
            
            if (!targetPort) return false;
            
            setState('connecting');
            port = targetPort;
            
            // Abrir puerto
            await port.open({
                baudRate: 115200,
                dataBits: 8,
                stopBits: 1,
                parity: 'none',
                flowControl: 'none',
            });
            
            // Setup streams
            const textEncoder = new TextEncoderStream();
            const textDecoder = new TextDecoderStream();
            
            textEncoder.readable.pipeTo(port.writable);
            port.readable.pipeTo(textDecoder.writable);
            
            writer = textEncoder.writable.getWriter();
            reader = textDecoder.readable.getReader();
            
            // Start read loop
            startReadLoop();
            
            // Guardar info del dispositivo
            saveDeviceInfo(port);
            
            setState('connected');
            emit('connect', { port, auto: true });
            
            console.log('Arduino auto-conectado');
            return true;
            
        } catch (error) {
            console.log('Auto-conexión falló:', error.message);
            port = null;
            reader = null;
            writer = null;
            setState('disconnected');
            return false;
        }
    }
    
    async function connect(options = {}) {
        if (!isSupported()) {
            throw new Error('Web Serial API no soportada en este navegador');
        }
        
        if (port) {
            console.warn('Ya hay una conexión activa');
            return true;
        }
        
        setState('connecting');
        
        try {
            // Request port with Arduino filters
            const filters = options.filters || [
                { usbVendorId: 0x2341 }, // Arduino
                { usbVendorId: 0x1A86 }, // CH340 (clones)
                { usbVendorId: 0x10C4 }, // CP210x
                { usbVendorId: 0x0403 }, // FTDI
            ];
            
            port = await navigator.serial.requestPort({ filters });
            
            // Open port
            await port.open({
                baudRate: options.baudRate || 115200,
                dataBits: 8,
                stopBits: 1,
                parity: 'none',
                flowControl: 'none',
            });
            
            // Setup streams
            const textEncoder = new TextEncoderStream();
            const textDecoder = new TextDecoderStream();
            
            textEncoder.readable.pipeTo(port.writable);
            port.readable.pipeTo(textDecoder.writable);
            
            writer = textEncoder.writable.getWriter();
            reader = textDecoder.readable.getReader();
            
            // Start read loop
            startReadLoop();
            
            // Guardar info del dispositivo para auto-reconexión futura
            saveDeviceInfo(port);
            
            setState('connected');
            emit('connect', { port });
            
            console.log('Arduino conectado');
            return true;
            
        } catch (error) {
            port = null;
            reader = null;
            writer = null;
            
            if (error.name === 'NotFoundError') {
                setState('disconnected');
                console.log('Selección de puerto cancelada');
                return false;
            }
            
            setState('error');
            emit('error', error);
            throw error;
        }
    }
    
    async function disconnect() {
        if (!port) return;
        
        try {
            readLoopRunning = false;
            
            if (reader) {
                await reader.cancel();
                reader.releaseLock();
                reader = null;
            }
            
            if (writer) {
                await writer.close();
                writer = null;
            }
            
            await port.close();
            port = null;
            
            setState('disconnected');
            emit('disconnect', {});
            
            console.log('Arduino desconectado');
            
        } catch (error) {
            console.error('Error al desconectar:', error);
            port = null;
            reader = null;
            writer = null;
            setState('disconnected');
        }
    }
    
    async function startReadLoop() {
        readLoopRunning = true;
        let buffer = '';
        
        try {
            while (readLoopRunning && reader) {
                const { value, done } = await reader.read();
                
                if (done) {
                    readLoopRunning = false;
                    break;
                }
                
                if (value) {
                    buffer += value;
                    
                    // Process complete lines
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';
                    
                    for (const line of lines) {
                        const trimmed = line.trim();
                        if (trimmed) {
                            emit('data', trimmed);
                            processResponse(trimmed);
                        }
                    }
                }
            }
        } catch (error) {
            if (readLoopRunning) {
                console.error('Read loop error:', error);
                emit('error', error);
                disconnect();
            }
        }
    }
    
    function processResponse(data) {
        // Parse ESP32 responses
        if (data.startsWith('>>')) {
            console.log('ESP32:', data);
            emit('status', { message: data });
        } else {
            console.log('ESP32 data:', data);
        }
    }
    
    function parseStatus(statusStr) {
        const parts = statusStr.split(',');
        const status = {};
        for (const part of parts) {
            const [key, value] = part.split('=');
            if (key && value !== undefined) {
                status[key.trim()] = isNaN(value) ? value : parseInt(value);
            }
        }
        return status;
    }
    
    // ─────────────────────────────────────────────────────
    // Commands (Protocolo ESP32)
    // ─────────────────────────────────────────────────────
    async function send(command) {
        if (!writer) {
            throw new Error('ESP32 no conectado');
        }
        
        try {
            await writer.write(command + '\n');
            console.log('Enviado a ESP32:', command);
            return true;
        } catch (error) {
            console.error('Error enviando comando:', error);
            emit('error', error);
            throw error;
        }
    }
    
    /**
     * Iniciar un modo de iluminación
     * @param {string} mode - Modo: general, rojo, verde, azul, blanco, intermitente, pausado, cascada, cascrev
     * @param {number} intensity - Intensidad 0-100 (opcional)
     */
    async function startMode(mode, intensity = null) {
        const cmd = intensity !== null 
            ? `inicio:${mode},${intensity}` 
            : `inicio:${mode}`;
        return send(cmd);
    }
    
    /**
     * Establecer intensidad/brillo (0-100%)
     * Con debounce para evitar saturar el serial
     */
    async function setBrightness(value, immediate = false) {
        const brightness = Math.max(0, Math.min(100, Math.round(Number(value))));
        
        // Si es el mismo valor que ya enviamos, no reenviar (excepto extremos)
        if (brightness === lastSentIntensity && brightness !== 0 && brightness !== 100) {
            return true;
        }
        
        // Clear pending debounce
        if (intensityDebounceTimer) {
            clearTimeout(intensityDebounceTimer);
            intensityDebounceTimer = null;
        }
        
        // Para valores extremos (0 o 100) o immediate, enviar inmediatamente
        if (immediate || brightness === 0 || brightness === 100) {
            lastSentIntensity = brightness;
            currentIntensity = brightness;
            console.log(`[Arduino] Enviando intensidad: ${brightness}% (inmediato)`);
            return send(`intensidad:${brightness}`);
        }
        
        // Para otros valores, debounce de 50ms para evitar saturar
        return new Promise((resolve) => {
            intensityDebounceTimer = setTimeout(async () => {
                lastSentIntensity = brightness;
                currentIntensity = brightness;
                console.log(`[Arduino] Enviando intensidad: ${brightness}%`);
                try {
                    await send(`intensidad:${brightness}`);
                    resolve(true);
                } catch (e) {
                    resolve(false);
                }
            }, 50);
        });
    }
    
    /**
     * Enviar intensidad inmediatamente sin debounce
     * Útil para cuando sueltas el slider
     */
    async function setBrightnessImmediate(value) {
        return setBrightness(value, true);
    }
    
    /**
     * Detener todo (apagar LEDs)
     */
    async function stop() {
        return send('stop');
    }
    
    /**
     * Marcar terapia como completada (alias de stop)
     */
    async function complete() {
        return send('completado');
    }
    
    /**
     * Iniciar self-test (10 segundos)
     */
    async function selfTest() {
        return send('test');
    }
    
    /**
     * Cancelar self-test
     */
    async function cancelSelfTest() {
        return send('test:off');
    }
    
    // ─────────────────────────────────────────────────────
    // Therapy Helpers (compatibilidad con session.html)
    // ─────────────────────────────────────────────────────
    let currentIntensity = 50;
    
    async function startTherapy(colorMode = null) {
        const mode = colorMode ? mapColorToMode(colorMode) : 'general';
        return startMode(mode, currentIntensity);
    }
    
    async function stopTherapy() {
        return stop();
    }
    
    async function pauseTherapy() {
        // ESP32 no tiene pausa, usamos stop
        return stop();
    }
    
    async function resumeTherapy() {
        // Reiniciar el último modo
        return startMode('general', currentIntensity);
    }
    
    /**
     * Mapea nombres de color/modo de terapia a modos del ESP32
     */
    function mapColorToMode(colorMode) {
        const modeMap = {
            'rojo': 'rojo',
            'red': 'rojo',
            'verde': 'verde',
            'green': 'verde',
            'azul': 'azul',
            'blue': 'azul',
            'blanco': 'blanco',
            'white': 'blanco',
            'rainbow': 'cascada',
            'cascada': 'cascada',
            'cascade': 'cascada',
            'cascrev': 'cascrev',
            'intermitente': 'intermitente',
            'blink': 'intermitente',
            'pulse': 'intermitente',
            'pausado': 'pausado',
            'breathe': 'pausado',
            'general': 'general',
            'default': 'general',
        };
        return modeMap[colorMode?.toLowerCase()] || 'general';
    }
    
    // ─────────────────────────────────────────────────────
    // Getters
    // ─────────────────────────────────────────────────────
    function isConnected() {
        return connectionState === 'connected';
    }
    
    function getState() {
        return connectionState;
    }
    
    function getIntensity() {
        return currentIntensity;
    }
    
    function setIntensity(value) {
        currentIntensity = Math.max(0, Math.min(100, parseInt(value)));
    }
    
    // ─────────────────────────────────────────────────────
    // Mode Presets (mapeados a modos del ESP32)
    // ─────────────────────────────────────────────────────
    const MODE_PRESETS = {
        'rojo': { mode: 'rojo', label: 'Rojo', color: '#ff0000' },
        'verde': { mode: 'verde', label: 'Verde', color: '#00ff00' },
        'azul': { mode: 'azul', label: 'Azul', color: '#0000ff' },
        'blanco': { mode: 'blanco', label: 'Blanco', color: '#ffffff' },
        'general': { mode: 'general', label: 'General', color: 'linear-gradient(90deg, blue, red, green)' },
        'intermitente': { mode: 'intermitente', label: 'Intermitente', color: '#ffff00' },
        'pausado': { mode: 'pausado', label: 'Pausado', color: '#88aaff' },
        'cascada': { mode: 'cascada', label: 'Cascada', color: 'linear-gradient(180deg, red, green, blue)' },
        'cascrev': { mode: 'cascrev', label: 'Cascada Rev', color: 'linear-gradient(0deg, red, green, blue)' },
    };
    
    /**
     * Aplicar un preset de modo
     */
    async function applyPreset(presetName) {
        const preset = MODE_PRESETS[presetName?.toLowerCase()] || MODE_PRESETS['general'];
        await startMode(preset.mode, currentIntensity);
        return preset;
    }
    
    /**
     * Obtener lista de modos disponibles
     */
    function getAvailableModes() {
        return Object.keys(MODE_PRESETS);
    }
    
    // ─────────────────────────────────────────────────────
    // Auto-reconnect on disconnect
    // ─────────────────────────────────────────────────────
    if (typeof navigator !== 'undefined' && navigator.serial) {
        navigator.serial.addEventListener('disconnect', (event) => {
            if (port && event.target === port) {
                console.log('Arduino desconectado físicamente');
                port = null;
                reader = null;
                writer = null;
                readLoopRunning = false;
                setState('disconnected');
                emit('disconnect', { unexpected: true });
            }
        });
    }
    
    // ─────────────────────────────────────────────────────
    // Public API
    // ─────────────────────────────────────────────────────
    return {
        // Feature detection
        isSupported,
        
        // Connection
        connect,
        disconnect,
        autoConnect,
        isConnected,
        getState,
        
        // Device memory
        getSavedDeviceInfo,
        forgetDevice,
        
        // Events
        on,
        off,
        
        // Raw command
        send,
        
        // ESP32 Commands
        startMode,
        setBrightness,
        setBrightnessImmediate,
        stop,
        complete,
        selfTest,
        cancelSelfTest,
        
        // Therapy helpers (compatibilidad)
        startTherapy,
        stopTherapy,
        pauseTherapy,
        resumeTherapy,
        
        // Presets
        applyPreset,
        getAvailableModes,
        MODE_PRESETS,
        
        // Intensity
        getIntensity,
        setIntensity,
    };
})();

// Export
window.ArduinoSerial = ArduinoSerial;
