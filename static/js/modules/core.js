/**
 * Core Module - Constants, utilities, and basic state management
 * Extracted from render.js as part of modularization effort
 */

// ===== CONSTANTS =====
export const TILESIZE = 16;
export const TRANSPORT_HIGHLIGHT_OPACITY = 0.3;
export const TRANSPORT_BORDER_WIDTH = 2;

// Tileset paths
export const TILESETS = {
    terrain: {
        transparent: '/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png',
        normal: '/static/img/Advance_Wars_Dual_Strike_Tileset_Normal.png',
        blackhole_transparent: '/static/img/aw2_blackhole_tileset_normal_transparent.png',
        blackhole_normal: '/static/img/aw2_blackhole_tileset_normal.png'
    },
    units: {
        blackhole_transparent: '/static/img/aw2_blackhole_units_map_transparent.png',
        blackhole_normal: '/static/img/aw2_blackhole_units_map.png'
    }
};

// Transport unit types
export const TRANSPORT_UNIT_TYPES = ['APC', 'LANDER', 'TCOPTER', 'CRUISER', 'CARRIER', 'BLACKBOAT'];

// ===== UTILITY FUNCTIONS =====

/**
 * Generate a UUID v4
 * @returns {string} UUID string
 */
export function uuidv4() {
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
}

/**
 * Check if a unit is a transport unit for rendering purposes
 * @param {Object} unit - Unit object
 * @returns {boolean} True if unit is a transport
 */
export function isTransportUnitForRender(unit) {
    if (!unit || !unit.type) return false;
    return TRANSPORT_UNIT_TYPES.includes(unit.type);
}

/**
 * Get cargo count for a transport unit
 * @param {Object} unit - Transport unit object
 * @returns {number} Number of cargo units
 */
export function getCargoCountForRender(unit) {
    if (!unit) return 0;
    
    // Method 1: Check unit.cargo array
    if (unit.cargo && Array.isArray(unit.cargo)) {
        // Count non-null cargo slots
        const actualCargoCount = unit.cargo.filter(cargo => 
            cargo !== null && 
            cargo !== undefined && 
            typeof cargo === 'object'
        ).length;
        
        return actualCargoCount;
    }
    
    // Method 2: Check unit.status.cargo array  
    if (unit.status && unit.status.cargo && Array.isArray(unit.status.cargo)) {
        const actualCargoCount = unit.status.cargo.filter(cargo => 
            cargo !== null && 
            cargo !== undefined && 
            typeof cargo === 'object'
        ).length;
        
        return actualCargoCount;
    }
    
    // Method 3: Check for explicit cargo count property
    if (typeof unit.cargo_count === 'number') {
        return unit.cargo_count;
    }
    
    // Method 4: Check status cargo count
    if (unit.status && typeof unit.status.cargo_count === 'number') {
        return unit.status.cargo_count;
    }
    
    return 0;
}

/**
 * Get selected terrain tileset path
 * @returns {string} Tileset image path
 */
export function getSelectedTerrainTileset() {
    const select = document.getElementById('terrainTilesetSelect');
    if (!select) return TILESETS.terrain.transparent; // fallback
    
    return TILESETS.terrain[select.value] || TILESETS.terrain.transparent;
}

/**
 * Get selected unit tileset path
 * @returns {string} Tileset image path
 */
export function getSelectedUnitTileset() {
    const select = document.getElementById('unitTilesetSelect');
    if (!select) return TILESETS.units.blackhole_transparent; // fallback
    
    return TILESETS.units[select.value] || TILESETS.units.blackhole_transparent;
}

// ===== GAME STATE MANAGEMENT =====

/**
 * Initialize the global game state
 * @returns {Object} Game state object
 */
export function initializeGameState() {
    if (!window.gameState) {
        window.gameState = {
            selectedUnit: null,
            movementPhase: false,
            showingAttackTargets: false,
            attackHighlights: [],
            operationInProgress: false
        };
    }
    return window.gameState;
}

/**
 * Get the current game state
 * @returns {Object} Current game state
 */
export function getGameState() {
    return window.gameState || initializeGameState();
}

/**
 * Update game state properties
 * @param {Object} updates - Object with properties to update
 */
export function updateGameState(updates) {
    const state = getGameState();
    Object.assign(state, updates);
}

/**
 * Reset game state to initial values
 */
export function resetGameState() {
    updateGameState({
        selectedUnit: null,
        movementPhase: false,
        showingAttackTargets: false,
        attackHighlights: [],
        operationInProgress: false
    });
}

// ===== GLOBAL VARIABLES ACCESS =====

/**
 * Get the game token from the DOM
 * @returns {string} Game token
 */
export function getGameToken() {
    const drawElement = document.getElementById('draw');
    return drawElement ? drawElement.getAttribute('x-token') : null;
}

/**
 * Initialize global variables with safe defaults
 * @returns {Object} Object containing global references
 */
export function initializeGlobals() {
    return {
        token: getGameToken(),
        board: null,
        two: null,
        transportHighlightGroup: null
    };
}

// ===== VALIDATION UTILITIES =====

/**
 * Validate coordinates are within bounds
 * @param {number} x - X coordinate
 * @param {number} y - Y coordinate
 * @param {Object} board - Board object with width/height
 * @returns {boolean} True if coordinates are valid
 */
export function isValidCoordinate(x, y, board) {
    if (!board || typeof x !== 'number' || typeof y !== 'number') return false;
    return x >= 0 && y >= 0 && x < board.width && y < board.height;
}

/**
 * Validate unit object has required properties
 * @param {Object} unit - Unit object to validate
 * @returns {boolean} True if unit is valid
 */
export function isValidUnit(unit) {
    return unit && 
           typeof unit === 'object' && 
           unit.type && 
           unit.army;
}

/**
 * Safe property access with default value
 * @param {Object} obj - Object to access
 * @param {string} path - Property path (e.g., 'unit.status.health')
 * @param {*} defaultValue - Default value if property doesn't exist
 * @returns {*} Property value or default
 */
export function safeGet(obj, path, defaultValue = null) {
    try {
        return path.split('.').reduce((current, key) => current?.[key], obj) ?? defaultValue;
    } catch {
        return defaultValue;
    }
}

// Initialize game state on module load
initializeGameState();