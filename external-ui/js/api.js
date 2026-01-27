/**
 * API Client para Panel Kryon
 * Maneja autenticación JWT, llamadas HTTP y estado de usuario
 */

const API_URL = 'http://127.0.0.1:8000';
const TOKEN_KEY = 'kryon_token';
const LEGACY_TOKEN_KEY = 'token';
const USER_KEY = 'kryon_user';

// ─────────────────────────────────────────────────────
// Token Management
// ─────────────────────────────────────────────────────
function getToken() {
    return localStorage.getItem(TOKEN_KEY) || localStorage.getItem(LEGACY_TOKEN_KEY);
}

function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(LEGACY_TOKEN_KEY, token);
}

function removeToken() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(LEGACY_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

function getUser() {
    const data = localStorage.getItem(USER_KEY);
    return data ? JSON.parse(data) : null;
}

function setUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

// ─────────────────────────────────────────────────────
// HTTP Client
// ─────────────────────────────────────────────────────
async function apiCall(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const config = { ...options, headers };
    
    if (options.body && typeof options.body === 'object') {
        config.body = JSON.stringify(options.body);
    }
    
    try {
        const response = await fetch(`${API_URL}${endpoint}`, config);
        
        if (response.status === 401) {
            removeToken();
            window.location.href = '/login.html';
            throw new Error('Sesión expirada');
        }
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
            throw new Error(error.detail || `Error ${response.status}`);
        }
        
        if (response.status === 204) return null;
        return await response.json();
    } catch (error) {
        if (error.message === 'Sesión expirada') throw error;
        console.error('API Error:', error);
        throw error;
    }
}

// ─────────────────────────────────────────────────────
// Auth Functions
// ─────────────────────────────────────────────────────
async function login(email, password) {
    const data = await apiCall('/api/auth/login', {
        method: 'POST',
        body: { email, password },
    });
    
    if (data.access_token) {
        setToken(data.access_token);
        return await getProfile();
    }
    throw new Error('No se recibió token');
}

async function register(email, password, name = null) {
    const body = { email, password };
    if (name) body.name = name;
    
    const data = await apiCall('/api/auth/register', {
        method: 'POST',
        body,
    });
    
    if (data.access_token) {
        setToken(data.access_token);
        return await getProfile();
    }
    throw new Error('No se recibió token');
}

async function getProfile() {
    const user = await apiCall('/api/auth/me');
    setUser(user);
    return user;
}

function logout() {
    removeToken();
    window.location.href = '/login.html';
}

function isAuthenticated() {
    return !!getToken();
}

function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/login.html';
        return false;
    }
    return true;
}

// ─────────────────────────────────────────────────────
// Therapies
// ─────────────────────────────────────────────────────
async function getTherapies(category = null) {
    let url = '/api/therapies';
    if (category) {
        url += `?category=${encodeURIComponent(category)}`;
    }
    return await apiCall(url);
}

async function getTherapy(id) {
    return await apiCall(`/api/therapies/${id}`);
}

// ─────────────────────────────────────────────────────
// Sessions
// ─────────────────────────────────────────────────────
async function startSession(therapyId, options = {}) {
    return await apiCall('/api/sessions/start', {
        method: 'POST',
        body: {
            therapy_id: therapyId,
            duration_planned_sec: options.duration || 600,
            playlist_id: options.playlistId || null,
            color_mode: options.colorMode || null,
            arduino_connected: options.arduinoConnected || false,
        },
    });
}

async function endSession(sessionId, status = 'completed', durationActual = null) {
    return await apiCall(`/api/sessions/${sessionId}/end`, {
        method: 'POST',
        body: {
            status,
            duration_actual_sec: durationActual,
        },
    });
}

async function getActiveSession() {
    return await apiCall('/api/sessions/active');
}

async function getMySessions(limit = 20) {
    return await apiCall(`/api/sessions/my?limit=${limit}`);
}

// ─────────────────────────────────────────────────────
// Playlists
// ─────────────────────────────────────────────────────
async function getPlaylists() {
    return await apiCall('/api/playlists');
}

async function getPlaylist(id) {
    return await apiCall(`/api/playlists/${id}`);
}

async function createPlaylist(name) {
    return await apiCall('/api/playlists', {
        method: 'POST',
        body: { name },
    });
}

async function updatePlaylist(id, name) {
    return await apiCall(`/api/playlists/${id}`, {
        method: 'PUT',
        body: { name },
    });
}

async function deletePlaylist(id) {
    return await apiCall(`/api/playlists/${id}`, {
        method: 'DELETE',
    });
}

async function addToPlaylist(playlistId, therapyId, options = {}) {
    return await apiCall(`/api/playlists/${playlistId}/items`, {
        method: 'POST',
        body: {
            therapy_id: therapyId,
            duration_override: options.duration || null,
            color_mode_override: options.colorMode || null,
        },
    });
}

async function removeFromPlaylist(playlistId, itemId) {
    return await apiCall(`/api/playlists/${playlistId}/items/${itemId}`, {
        method: 'DELETE',
    });
}

async function reorderPlaylist(playlistId, itemIds) {
    return await apiCall(`/api/playlists/${playlistId}/reorder`, {
        method: 'POST',
        body: { item_ids: itemIds },
    });
}

// ─────────────────────────────────────────────────────
// Categories & Light Modes
// ─────────────────────────────────────────────────────
async function getCategories() {
    return await apiCall('/api/categories');
}

async function getLightModes() {
    return await apiCall('/api/categories/light-modes');
}

// ─────────────────────────────────────────────────────
// Duration Types & Limits
// ─────────────────────────────────────────────────────
/**
 * Límites estrictos de tiempo:
 * - Corto: 0-5 min (0-300 seg)
 * - Mediano: 6-20 min (360-1200 seg)
 * - Largo: 21 min - 3 hrs (1260-10800 seg)
 */
const DURATION_LIMITS = {
    corto:   { min: 0, max: 300, label: '0-5 min', defaultLabel: 'Corto (5 min)' },
    mediano: { min: 360, max: 1200, label: '6-20 min', defaultLabel: 'Mediano (20 min)' },
    largo:   { min: 1260, max: 10800, label: '21 min - 3 hrs', defaultLabel: 'Largo (hasta 3 hrs)' },
};

/**
 * Obtiene los límites de duración para un tipo
 * @param {string} durationType - 'corto' | 'mediano' | 'largo'
 * @returns {Object} { min, max, label }
 */
function getDurationLimits(durationType) {
    return DURATION_LIMITS[durationType] || DURATION_LIMITS.corto;
}

/**
 * Determina el tipo de duración basado en segundos
 * @param {number} seconds - Duración en segundos
 * @returns {string} 'corto' | 'mediano' | 'largo'
 */
function getDurationTypeFromSeconds(seconds) {
    if (seconds <= DURATION_LIMITS.corto.max) return 'corto';
    if (seconds <= DURATION_LIMITS.mediano.max) return 'mediano';
    return 'largo';
}
// Updated: 2026-01-26 - Added automatic duration detection


/**
 * Obtiene la URL del audio y duración máxima según el tipo
 * @param {Object} therapy - Objeto de terapia con audio_corto_url, etc.
 * @param {string} durationType - 'corto' | 'mediano' | 'largo'
 * @returns {Object} { audioUrl, maxDuration, label }
 */
function getAudioForDuration(therapy, durationType) {
    const limits = DURATION_LIMITS[durationType] || DURATION_LIMITS.corto;
    
    const config = {
        corto: {
            audioUrl: therapy.audio_corto_url,
            maxDuration: Math.min(therapy.duration_corto_sec || 300, limits.max),
        },
        mediano: {
            audioUrl: therapy.audio_mediano_url,
            maxDuration: Math.min(therapy.duration_mediano_sec || 1200, limits.max),
        },
        largo: {
            audioUrl: therapy.audio_largo_url,
            maxDuration: Math.min(therapy.duration_largo_sec || 10800, limits.max),
        },
    };
    
    const selected = config[durationType] || config.corto;
    return {
        ...selected,
        label: limits.label,
        durationType,
    };
}

/**
 * Valida que una duración esté dentro de los límites del tipo
 * @param {number} seconds - Duración en segundos
 * @param {string} durationType - 'corto' | 'mediano' | 'largo'
 * @returns {boolean}
 */
function isDurationValid(seconds, durationType) {
    const limits = DURATION_LIMITS[durationType];
    if (!limits) return false;
    return seconds >= limits.min && seconds <= limits.max;
}

/**
 * Obtiene las etiquetas personalizadas de duración o defaults
 * @param {Object} therapy - Terapia con posible durationLabels
 * @returns {Object} { corto, mediano, largo }
 */
function getDurationLabels(therapy) {
    const defaults = {
        corto: 'Corto (5 min)',
        mediano: 'Mediano (20 min)',
        largo: 'Largo (hasta 3 hrs)',
    };
    
    if (therapy.duration_labels) {
        try {
            const custom = typeof therapy.duration_labels === 'string' 
                ? JSON.parse(therapy.duration_labels) 
                : therapy.duration_labels;
            return {
                corto: custom.corto || defaults.corto,
                mediano: custom.mediano || defaults.mediano,
                largo: custom.largo || defaults.largo,
            };
        } catch (e) {
            return defaults;
        }
    }
    return defaults;
}

// ─────────────────────────────────────────────────────
// Light Modes (hardcoded for offline use)
// ─────────────────────────────────────────────────────
const LIGHT_MODES = [
    { id: 'general', name: 'Patrón Complejo', icon: '🔄', color: '#06b6d4', esp32Command: 'general', description: '11 patrones variables' },
    { id: 'intermitente', name: 'Intermitente', icon: '⚡', color: '#f59e0b', esp32Command: 'intermitente', description: 'Cambio rápido 500ms' },
    { id: 'pausado', name: 'Pausado', icon: '⏸️', color: '#8b5cf6', esp32Command: 'pausado', description: 'Cambio lento 1.5s' },
    { id: 'cascada', name: 'Cascada', icon: '🌊', color: '#10b981', esp32Command: 'cascada', description: 'Efecto cascada' },
    { id: 'cascrev', name: 'Cascada Reversa', icon: '🌊', color: '#182521', esp32Command: 'cascrev', description: 'Cascada invertida' },
    { id: 'rojo', name: 'Solo Rojo', icon: '🔴', color: '#ef4444', esp32Command: 'rojo', description: 'Rojo sólido' },
    { id: 'verde', name: 'Solo Verde', icon: '🟢', color: '#22c55e', esp32Command: 'verde', description: 'Verde sólido' },
    { id: 'azul', name: 'Solo Azul', icon: '🔵', color: '#3b82f6', esp32Command: 'azul', description: 'Azul sólido' },
    { id: 'blanco', name: 'Solo Blanco', icon: '⚪', color: '#ffffff', esp32Command: 'blanco', description: 'Blanco sólido' },
];

function getLightModesLocal() {
    return LIGHT_MODES;
}

function getLightModeById(id) {
    return LIGHT_MODES.find(m => m.id === id) || LIGHT_MODES[0];
}

// ─────────────────────────────────────────────────────
// Utilities
// ─────────────────────────────────────────────────────
function formatDuration(seconds) {
    if (!seconds || isNaN(seconds) || seconds <= 0) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function formatDurationLong(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (secs === 0) return `${mins} min`;
    return `${mins} min ${secs} seg`;
}

function getMediaUrl(path) {
    if (!path) return null;
    if (path.startsWith('http')) return path;
    // Si ya empieza con /media, no duplicar
    if (path.startsWith('/media/')) {
        return `${API_URL}${path}`;
    }
    // Si empieza con /, usar como está
    if (path.startsWith('/')) {
        return `${API_URL}${path}`;
    }
    // Si es solo el nombre de archivo, agregar prefijo
    return `${API_URL}/media/${path}`;
}

// ─────────────────────────────────────────────────────
// Export for use in HTML
// ─────────────────────────────────────────────────────
window.KryonAPI = {
    // Token
    getToken,
    setToken,
    removeToken,
    getUser,
    setUser,
    
    // Auth
    login,
    register,
    logout,
    getProfile,
    isAuthenticated,
    requireAuth,
    
    // Therapies
    getTherapies,
    getTherapy,
    
    // Categories & Light Modes
    getCategories,
    getLightModes,
    getLightModesLocal,
    getLightModeById,
    LIGHT_MODES,
    
    // Duration
    DURATION_LIMITS,
    getDurationLimits,
    getDurationTypeFromSeconds,
    getAudioForDuration,
    isDurationValid,
    getDurationLabels,
    
    // Sessions
    startSession,
    endSession,
    getActiveSession,
    getMySessions,
    
    // Playlists
    getPlaylists,
    getPlaylist,
    createPlaylist,
    updatePlaylist,
    deletePlaylist,
    addToPlaylist,
    removeFromPlaylist,
    reorderPlaylist,
    
    // Utils
    formatDuration,
    formatDurationLong,
    getMediaUrl,
    
    // Raw API call
    apiCall,
    API_URL,
    BASE_URL: API_URL,
};
