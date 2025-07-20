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
            currentTurn: window.board?.current_turn,
            hasUnit: !!tile.unit,
            hasSelected: !!window.board?.selected
        });
        
        return (tile.mapTile.type === 'FACTORY' || 
                tile.mapTile.type === 'AIRPORT' || 
                tile.mapTile.type === 'PORT') &&
               tile.mapTile.army === window.board.current_turn &&
               !tile.unit &&
               !window.board.selected;
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
        const logger = window.logger || console;
        
        // Debug unit selection condition
        if (tile.unit) {
            logger.info('Unit selection check:', {
                unitArmy: tile.unit.army,
                currentTurn: window.board.current_turn,
                armyMatch: tile.unit.army === window.board.current_turn,
                onMovementHighlight: window.movementHighlights?.some(h => h.x === tile.x && h.y === tile.y),
                canMove: tile.unit.can_move,
                tileType: tile.mapTile?.type
            });
        }
        
        return tile.unit && 
               tile.unit.army === window.board.current_turn &&
               !window.movementHighlights?.some(h => h.x === tile.x && h.y === tile.y);
    },
    handle: (tile, event) => {
        const logger = window.logger || console;
        
        // If clicking on already selected unit with movement highlights shown, don't deselect
        if (window.board.selected?.x === tile.x && window.board.selected?.y === tile.y) {
            if (window.movementHighlights && window.movementHighlights.length > 0) {
                logger.info('Keeping unit selected - movement highlights active');
                return true; // Keep selection
            }
            
            logger.info('Deselecting unit');
            window.board.selected = null;
            clearAllHighlights();
            if (typeof clearMovementHighlights === 'function') {
                clearMovementHighlights();
            }
            if (typeof clearMovementHighlightsData === 'function') {
                clearMovementHighlightsData();
            }
        } else {
            // Clear previous selection first
            if (window.board.selected) {
                clearAllHighlights();
                if (typeof clearMovementHighlights === 'function') {
                    clearMovementHighlights();
                }
                if (typeof clearMovementHighlightsData === 'function') {
                    clearMovementHighlightsData();
                }
            }
            
            // Select new unit
            logger.info(`Selecting unit at (${tile.x}, ${tile.y})`);
            window.board.selected = tile;
            
            // Store in gameState too for compatibility
            if (window.gameState) {
                window.gameState.selectedUnit = tile;
                window.gameState.selectedX = tile.x;
                window.gameState.selectedY = tile.y;
            }
            
            // Show movement range only if unit can move
            if (tile.unit.can_move) {
                if (typeof highlightMovementRange === 'function') {
                    highlightMovementRange(tile.x, tile.y);
                } else if (typeof showMovementRange === 'function') {
                    showMovementRange(tile.x, tile.y);
                } else if (typeof unitSelectWithMovementHighlighting === 'function') {
                    unitSelectWithMovementHighlighting(tile);
                }
            } else {
                logger.info('Unit cannot move this turn');
            }
            
            // Show attack targets if applicable
            if (tile.unit.can_attack && typeof showAttackTargets === 'function') {
                setTimeout(() => showAttackTargets(tile.x, tile.y), 100);
            }
            
            // Handle transport features AFTER selection
            if (typeof isTransportUnit === 'function' && isTransportUnit(tile.unit)) {
                // It's a transport - prepare exit options (but don't show yet)
                if (typeof window.transportState !== 'undefined') {
                    window.transportState.selectedTransport = tile;
                }
            }
            
            if (typeof canUnitBoardTransports === 'function' && canUnitBoardTransports(tile.unit)) {
                // Unit can board transports - show nearby transports
                if (typeof showLoadableTransports === 'function') {
                    showLoadableTransports(tile.x, tile.y);
                }
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
        const logger = window.logger || console;
        const hasSelected = !!window.board.selected;
        const hasNoUnit = !tile.unit;
        const isHighlighted = window.movementHighlights?.some(h => h.x === tile.x && h.y === tile.y);
        const canMoveToTile = !!tile.can_be_moved_to;
        
        logger.debug('Movement handler check:', {
            tile: {x: tile.x, y: tile.y},
            hasSelected,
            hasNoUnit,
            isHighlighted,
            canMoveToTile,
            movementHighlights: window.movementHighlights?.length || 0
        });
        
        return hasSelected && hasNoUnit && (isHighlighted || canMoveToTile);
    },
    handle: (tile, event) => {
        const logger = window.logger || console;
        logger.info(`Moving unit to (${tile.x}, ${tile.y})`);
        
        // Use the proper unitMove function from gameActions module
        if (typeof window.unitMove === 'function') {
            logger.info('Using window.unitMove');
            window.unitMove(tile);
        } else if (typeof unitMove === 'function') {
            logger.info('Using global unitMove');
            unitMove(tile);
        } else if (typeof window.executeMovement === 'function') {
            logger.info('Using window.executeMovement');
            window.executeMovement(tile);
        } else {
            logger.error('No movement function found');
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
        return window.board.selected && 
               tile.unit && 
               tile.unit.army !== window.board.current_turn &&
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
        if (window.board.selected?.unit && canUnitBoardTransports(window.board.selected.unit)) {
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
    const drawDiv = document.getElementById('draw');
    if (drawDiv) {
        // Find the actual canvas element (Two.js creates it inside the div)
        const actualCanvas = drawDiv.querySelector('canvas');
        if (actualCanvas) {
            // Remove ALL old handlers
            actualCanvas.onclick = null;
            actualCanvas.onmousedown = null;
            actualCanvas.onmouseup = null;
            
            // Add our centralized handler
            actualCanvas.onclick = function centralizedClickHandler(event) {
                // Debug: confirm handler is called (remove this later)
                // console.error('🚨 CENTRALIZED HANDLER CALLED!');
                
                const x = event.offsetX;
                const y = event.offsetY;
                const tile = window.tileAt(x, y);
                
                // Debug logging (reduce noise once working)
                // console.error(`🖱️ CENTRALIZED HANDLER: Click at pixel (${x}, ${y})`);
                
                // Use the tile directly without coordinate offset workarounds
                
                if (tile) {
                    console.error('🖱️ CENTRALIZED HANDLER: Calling processClick');
                    processClick(tile, event);
                    console.error('🖱️ CENTRALIZED HANDLER: processClick returned');
                } else {
                    console.error('🖱️ CENTRALIZED HANDLER: No tile found!');
                }
            };
            
            // Also override the global functions
            window.canvasClick = actualCanvas.onclick;
            window.advanceWarsCanvasClick = actualCanvas.onclick;
            
            logger.info('✅ Canvas click handler replaced with centralized system');
        } else {
            logger.warn('Canvas element not found yet, will retry...');
            setTimeout(initializeClickHandler, 500);
        }
    }
}

// Clear highlights when clicking empty tiles
registerClickHandler('fallback', {
    name: 'clear-on-empty',
    priority: 0,
    condition: (tile, event) => {
        // Clear if clicking on empty tile that's not a movement highlight
        const hasUnit = !!tile.unit;
        const hasMovementHighlight = window.movementHighlights?.some(h => h.x === tile.x && h.y === tile.y);
        const canBeAttacked = !!tile.can_be_attacked;
        
        const logger = window.logger || console;
        logger.info(`Fallback handler check: hasUnit=${hasUnit}, hasMovementHighlight=${hasMovementHighlight}, canBeAttacked=${canBeAttacked}`);
        logger.info('Tile unit:', tile.unit);
        
        return !hasUnit && !hasMovementHighlight && !canBeAttacked;
    },
    handle: (tile, event) => {
        const logger = window.logger || console;
        logger.info('Clearing selection - clicked empty tile');
        
        // Clear selection
        window.board.selected = null;
        
        // Clear all highlights
        clearAllHighlights();
        if (typeof clearMovementHighlights === 'function') {
            clearMovementHighlights();
        }
        if (typeof clearMovementHighlightsData === 'function') {
            clearMovementHighlightsData();
        }
        
        // Force visual update
        if (window.two) {
            window.two.update();
        }
        
        return true;
    }
});

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
        // Wait longer to ensure render_legacy.js has finished
        setTimeout(initializeClickHandler, 3000);
    });
} else {
    // Wait longer to ensure render_legacy.js has finished
    setTimeout(initializeClickHandler, 3000);
}

// Also add a watcher to ensure our handler stays in place
setInterval(() => {
    const canvas = document.querySelector('#draw canvas');
    if (canvas && canvas.onclick && canvas.onclick.name !== 'centralizedClickHandler') {
        console.log('Re-initializing centralized click handler...');
        initializeClickHandler();
    }
}, 3000);