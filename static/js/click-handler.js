/**
 * Centralized Click Handler System
 * 
 * This module provides a unified, priority-based click handling system
 * for the Advance Wars game. All click events are routed through this
 * system to ensure proper handling order and prevent conflicts.
 */

// ===== CLICK HANDLER REGISTRY =====
const clickHandlers = {
    // Priority 1: Modal/Overlay interactions (highest priority)
    modals: [],
    
    // Priority 2: Special keyboard modifiers (Ctrl, Alt, Shift)
    modifiers: [],
    
    // Priority 3: Context-specific actions (transport unload, attack targets)
    contextual: [],
    
    // Priority 4: Production buildings
    production: [],
    
    // Priority 5: Unit selection
    selection: [],
    
    // Priority 6: Movement
    movement: [],
    
    // Priority 7: Default/fallback handlers
    fallback: []
};

// ===== HANDLER REGISTRATION =====
/**
 * Register a click handler with a specific priority
 * @param {string} category - Handler category (modals, modifiers, contextual, etc.)
 * @param {Object} handler - Handler configuration
 * @param {string} handler.name - Unique name for the handler
 * @param {Function} handler.condition - Function to check if handler should run
 * @param {Function} handler.handle - Function to handle the click
 * @param {number} handler.priority - Priority within category (lower = higher priority)
 */
function registerClickHandler(category, handler) {
    if (!clickHandlers[category]) {
        console.error(`Invalid handler category: ${category}`);
        return;
    }
    
    // Remove existing handler with same name
    clickHandlers[category] = clickHandlers[category].filter(h => h.name !== handler.name);
    
    // Add new handler
    clickHandlers[category].push(handler);
    
    // Sort by priority within category
    clickHandlers[category].sort((a, b) => (a.priority || 0) - (b.priority || 0));
    
    console.log(`✅ Registered click handler: ${handler.name} in ${category}`);
}

// ===== MAIN CLICK DISPATCHER =====
/**
 * Process a click event through the handler chain
 * @param {Object} tile - The tile that was clicked
 * @param {Event} event - The original click event
 * @returns {boolean} - True if handled, false otherwise
 */
function processClick(tile, event) {
    const logger = window.logger || console;
    
    // Check if board is loaded
    if (!window.board) {
        logger.warn('Click ignored - board not loaded yet');
        return false;
    }
    
    // Log all clicks for debugging
    logger.info('🖱️ Click detected:', {
        tile: `(${tile.x}, ${tile.y})`,
        type: tile.mapTile?.type,
        army: tile.mapTile?.army,
        hasUnit: !!tile.unit,
        currentTurn: window.board?.current_turn
    });
    
    // Enhanced debugging for tile detection
    logger.debug('Click processing started', {
        tile: { x: tile.x, y: tile.y, type: tile.mapTile?.type },
        pixelCoords: { x: event.offsetX, y: event.offsetY },
        tileSize: window.TILESIZE,
        calculatedTile: {
            x: Math.floor(event.offsetX / (window.TILESIZE || 16)),
            y: Math.floor(event.offsetY / (window.TILESIZE || 16))
        },
        boardLoaded: !!window.board,
        currentTurn: window.board?.current_turn,
        modifiers: {
            ctrl: event.ctrlKey,
            alt: event.altKey,
            shift: event.shiftKey
        }
    });
    
    // Process handlers in priority order
    const categories = ['modals', 'modifiers', 'contextual', 'production', 'selection', 'movement', 'fallback'];
    
    for (const category of categories) {
        for (const handler of clickHandlers[category]) {
            try {
                // Check if handler condition is met
                if (handler.condition(tile, event)) {
                    logger.debug(`Handler ${handler.name} condition met`);
                    
                    // Execute handler
                    const handled = handler.handle(tile, event);
                    
                    if (handled) {
                        logger.debug(`Click handled by: ${handler.name}`);
                        return true;
                    }
                }
            } catch (error) {
                logger.error(`Error in handler ${handler.name}:`, error);
            }
        }
    }
    
    logger.debug('No handler processed the click');
    return false;
}

// ===== BUILT-IN HANDLERS =====

// Production Buildings Handler
registerClickHandler('production', {
    name: 'production-buildings',
    priority: 0,
    condition: (tile, event) => {
        // Debug logging
        const logger = window.logger || console;
        logger.debug('Production building check:', {
            type: tile.mapTile?.type,
            army: tile.mapTile?.army,
            currentTurn: board?.current_turn,
            hasUnit: !!tile.unit,
            hasSelected: !!board?.selected
        });
        
        return (tile.mapTile.type === 'FACTORY' || 
                tile.mapTile.type === 'AIRPORT' || 
                tile.mapTile.type === 'PORT') &&
               tile.mapTile.army === board.current_turn &&
               !tile.unit &&
               !board.selected;
    },
    handle: (tile, event) => {
        const logger = window.logger || console;
        logger.info(`Opening production menu for ${tile.mapTile.type}`);
        
        // Call the appropriate production function
        if (tile.mapTile.type === 'FACTORY') {
            if (typeof unitCreate === 'function') {
                unitCreate(tile);
            } else if (typeof window.unitCreate === 'function') {
                window.unitCreate(tile);
            } else {
                logger.error('unitCreate function not found');
                return false;
            }
        } else if (tile.mapTile.type === 'AIRPORT') {
            if (typeof airunitCreate === 'function') {
                airunitCreate(tile);
            } else if (typeof window.airunitCreate === 'function') {
                window.airunitCreate(tile);
            } else {
                logger.error('airunitCreate function not found');
                return false;
            }
        } else if (tile.mapTile.type === 'PORT') {
            if (typeof seaunitCreate === 'function') {
                seaunitCreate(tile);
            } else if (typeof window.seaunitCreate === 'function') {
                window.seaunitCreate(tile);
            } else {
                logger.error('seaunitCreate function not found');
                return false;
            }
        }
        
        return true;
    }
});

// Unit Selection Handler
registerClickHandler('selection', {
    name: 'unit-selection',
    priority: 0,
    condition: (tile, event) => {
        return tile.unit && 
               tile.unit.army === board.current_turn &&
               !window.movementHighlights?.some(h => h.x === tile.x && h.y === tile.y);
    },
    handle: (tile, event) => {
        const logger = window.logger || console;
        
        // If clicking on already selected unit, deselect
        if (board.selected?.x === tile.x && board.selected?.y === tile.y) {
            logger.info('Deselecting unit');
            board.selected = null;
            clearAllHighlights();
        } else {
            // Select new unit
            logger.info(`Selecting unit at (${tile.x}, ${tile.y})`);
            board.selected = tile;
            
            // Show movement range
            if (typeof showMovementRange === 'function') {
                showMovementRange(tile.x, tile.y);
            }
            
            // Show attack targets if applicable
            if (tile.unit.can_attack && typeof showAttackTargets === 'function') {
                setTimeout(() => showAttackTargets(tile.x, tile.y), 100);
            }
        }
        
        return true;
    }
});

// Movement Execution Handler
registerClickHandler('movement', {
    name: 'movement-execution',
    priority: 0,
    condition: (tile, event) => {
        return board.selected && 
               !tile.unit && 
               window.movementHighlights?.some(h => h.x === tile.x && h.y === tile.y);
    },
    handle: (tile, event) => {
        const logger = window.logger || console;
        logger.info(`Moving unit to (${tile.x}, ${tile.y})`);
        
        if (typeof executeMovement === 'function') {
            executeMovement(tile);
        } else {
            logger.error('executeMovement function not found');
            return false;
        }
        
        return true;
    }
});

// Attack Execution Handler
registerClickHandler('contextual', {
    name: 'attack-execution',
    priority: 0,
    condition: (tile, event) => {
        return board.selected && 
               tile.unit && 
               tile.unit.army !== board.current_turn &&
               window.gameState?.attackHighlights?.some(h => h.x === tile.x && h.y === tile.y);
    },
    handle: (tile, event) => {
        const logger = window.logger || console;
        logger.info(`Attacking unit at (${tile.x}, ${tile.y})`);
        
        if (typeof executeAttack === 'function') {
            executeAttack(tile);
        } else {
            logger.error('executeAttack function not found');
            return false;
        }
        
        return true;
    }
});

// Alt-Click Transport Handler
registerClickHandler('modifiers', {
    name: 'alt-click-transport',
    priority: 0,
    condition: (tile, event) => event.altKey,
    handle: (tile, event) => {
        const logger = window.logger || console;
        logger.info('Alt-click detected, handling transport operation');
        
        // Handle transport unload
        if (tile.unit && isTransportUnit(tile.unit) && tile.unit.cargo?.length > 0) {
            if (typeof window.handleTransportAltClick === 'function') {
                return window.handleTransportAltClick(tile, event);
            }
        }
        
        // Handle transport load
        if (board.selected?.unit && canUnitBoardTransports(board.selected.unit)) {
            // Implementation for loading
        }
        
        return true; // Always consume alt-clicks
    }
});

// ===== HELPER FUNCTIONS =====
function clearAllHighlights() {
    if (window.movementHighlights) window.movementHighlights = [];
    if (window.gameState?.attackHighlights) window.gameState.attackHighlights = [];
    if (window.transportHighlights) window.transportHighlights = [];
    
    // Call all clear functions
    ['clearMovementHighlights', 'clearAttackHighlights', 'clearTransportHighlights'].forEach(func => {
        if (typeof window[func] === 'function') window[func]();
    });
    
    // Force visual update
    if (window.two?.update) window.two.update();
}

// ===== INITIALIZATION =====
/**
 * Initialize the click handler system
 * This should be called after all game systems are loaded
 */
function initializeClickHandler() {
    const logger = window.logger || console;
    
    // Check if game is ready
    if (!window.board || !window.tileAt) {
        logger.warn('Game not ready yet, retrying click handler initialization...');
        setTimeout(initializeClickHandler, 1000);
        return;
    }
    
    logger.info('Initializing centralized click handler system');
    
    // Replace the main canvas click handler
    const canvas = document.getElementById('draw');
    if (canvas) {
        // Remove old handlers
        canvas.onclick = null;
        canvas.removeEventListener('click', canvasClick);
        
        // Add new centralized handler
        canvas.addEventListener('click', (event) => {
            // Get the actual canvas element (Two.js creates a canvas inside the div)
            const actualCanvas = canvas.querySelector('canvas');
            if (!actualCanvas) return;
            
            const rect = actualCanvas.getBoundingClientRect();
            const x = event.clientX;
            const y = event.clientY;
            
            // Convert page coordinates to tile
            let tile;
            if (window.canvasScaler) {
                const tileCoords = window.canvasScaler.pageToTile(x, y);
                if (tileCoords.x >= 0 && tileCoords.x < window.board.width && 
                    tileCoords.y >= 0 && tileCoords.y < window.board.height) {
                    tile = window.board.grid[tileCoords.x + tileCoords.y * window.board.width];
                } else {
                    tile = null;
                }
            } else {
                // Fallback to offset coordinates
                tile = window.tileAt(event.offsetX, event.offsetY);
            }
            
            if (tile) {
                processClick(tile, event);
            }
        });
        
        logger.info('Canvas click handler replaced with centralized system');
    }
}

// Fallback Debug Handler
registerClickHandler('fallback', {
    name: 'debug-fallback',
    priority: 999,
    condition: (tile, event) => true, // Always true
    handle: (tile, event) => {
        const logger = window.logger || console;
        logger.warn('Unhandled click on tile:', {
            x: tile.x,
            y: tile.y,
            type: tile.mapTile?.type,
            army: tile.mapTile?.army,
            hasUnit: !!tile.unit,
            currentTurn: board?.current_turn
        });
        return false; // Don't consume the click
    }
});

// ===== EXPORTS =====
window.clickHandler = {
    register: registerClickHandler,
    process: processClick,
    initialize: initializeClickHandler,
    clearHighlights: clearAllHighlights
};

// Override the global click functions to use the new system
window.canvasClick = function(event) {
    const x = event.offsetX;
    const y = event.offsetY;
    const tile = tileAt(x, y);
    
    if (tile) {
        processClick(tile, event);
    }
};

window.advanceWarsCanvasClick = window.canvasClick;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(initializeClickHandler, 500);
    });
} else {
    setTimeout(initializeClickHandler, 500);
}