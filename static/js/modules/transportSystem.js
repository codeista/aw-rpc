/**
 * Transport System Module - Handles unit loading, unloading, and transport operations
 * Extracted from render.js as part of modularization effort
 */

import { jsonrpc } from './network.js';
import { getBoard, getTile, update } from './gameState.js';
import { showTransportFeedback, showCargoInfo } from './uiSystems.js';
import { renderTransportHighlights } from './renderEngine.js';

// Ensure logger exists
if (typeof window.logger === 'undefined') {
    window.logger = console; // Fallback to console if logger.js isn't loaded
}
const logger = window.logger;

// ===== TRANSPORT STATE =====
const transportState = {
    transportHighlights: {
        loadableUnits: [],
        unloadPositions: [],
        selectedTransport: null
    },
    transportHighlightGroup: null
};

// Make transportHighlights globally accessible
if (window) {
    window.transportHighlights = transportState.transportHighlights;
}

// ===== TRANSPORT UNIT CHECKS =====

/**
 * Check if a unit is a transport unit
 * @param {Object} unit - Unit object
 * @returns {boolean} True if transport unit
 */
export function isTransportUnit(unit) {
    if (!unit || !unit.type) return false;
    const transportTypes = ['APC', 'LANDER', 'TCOPTER', 'CRUISER', 'CARRIER', 'BLACKBOAT'];
    const unitType = unit.type?.name || unit.type || '';
    return transportTypes.includes(unitType);
}

/**
 * Check if a unit is a transport (for rendering)
 * @param {Object} unit - Unit object
 * @returns {boolean} True if transport unit
 */
export function isTransportUnitForRender(unit) {
    if (!unit || !unit.type) return false;
    const transportTypes = ['APC', 'LANDER', 'TCOPTER', 'CRUISER', 'CARRIER', 'BLACKBOAT'];
    return transportTypes.includes(unit.type);
}

/**
 * Get cargo count for rendering
 * @param {Object} unit - Unit object
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
        
        if (actualCargoCount > 0) {
            return actualCargoCount;
        }
    }
    
    // Method 2: Check unit.cargo_units array
    if (unit.cargo_units && Array.isArray(unit.cargo_units)) {
        return unit.cargo_units.length;
    }
    
    // Method 3: Check unit.current_cargo number
    if (typeof unit.current_cargo === 'number') {
        return unit.current_cargo;
    }
    
    return 0;
}

// ===== TRANSPORT SELECTION =====

/**
 * Handle transport selection logic
 * @param {Object} tile - Selected tile
 */
export function handleTransportSelectionLogic(tile) {
    if (!tile.unit) {
        clearTransportHighlights();
        return;
    }
    
    // Get cargo/transport information (ONLY for transport units)
    if (tile.unit && isTransportUnit(tile.unit)) {
        // Set selectedUnit for transport units (needed for Black Boat repair)
        logger.debug('🚛 Transport unit clicked, setting selectedUnit:', tile);
        if (window.gameState) {
            window.gameState.selectedUnit = tile;
        }
        
        const board = getBoard();
        if (board) {
            board.selected = tile;
        }
        
        jsonrpc('get_cargo_info', {x: tile.x, y: tile.y}).then(result => {
            if (result?.success && result.cargo_info) {
                const cargoInfo = result.cargo_info;
                
                // Show transport-specific highlights
                if (cargoInfo.is_transport) {
                    if (cargoInfo.current_cargo > 0) {
                        // Transport has cargo - show unload positions
                        showUnloadPositionsHighlight(tile.x, tile.y);
                    } else {
                        // Empty transport - show loadable units nearby
                        showLoadableUnitsHighlight(tile.x, tile.y);
                    }
                }
                
                // Show cargo information to user
                showCargoInfo(tile.unit, cargoInfo);
            } else {
                // If cargo info fails, just clear highlights
                clearTransportHighlights();
            }
        }).catch(error => {
            logger.error('Failed to get cargo info:', error);
            clearTransportHighlights();
        });
    } else {
        // For non-transport units, clear any existing transport highlights
        clearTransportHighlights();
    }
}

// ===== HIGHLIGHT MANAGEMENT =====

/**
 * Clear transport highlights
 */
export function clearTransportHighlights() {
    // Remove all transport-related CSS classes
    const tiles = document.querySelectorAll('.tile');
    tiles.forEach(tile => {
        tile.classList.remove('loadable-unit', 'unload-position');
    });
    
    // Clear state
    transportState.transportHighlights = {
        loadableUnits: [],
        unloadPositions: [],
        selectedTransport: null
    };
    
    // Update global reference
    window.transportHighlights = transportState.transportHighlights;
    
    // Clear visual highlights
    if (transportState.transportHighlightGroup && window.two) {
        window.two.remove(transportState.transportHighlightGroup);
        transportState.transportHighlightGroup = null;
    }
}

/**
 * Show loadable units highlight
 * @param {number} transportX - Transport X coordinate
 * @param {number} transportY - Transport Y coordinate
 */
export function showLoadableUnitsHighlight(transportX, transportY) {
    clearTransportHighlights();
    
    jsonrpc('get_loadable_units', {x: transportX, y: transportY}).then(result => {
        if (result?.success && result.loadable_units) {
            transportState.transportHighlights.loadableUnits = result.loadable_units;
            transportState.transportHighlights.selectedTransport = {x: transportX, y: transportY};
            
            // Update global reference
            window.transportHighlights = transportState.transportHighlights;
            
            // Add visual highlights
            const highlights = result.loadable_units.map(unit => ({
                x: unit.x,
                y: unit.y,
                type: 'loadable-transport'
            }));
            
            window.transportHighlights = highlights;
            renderTransportHighlights();
            
            showTransportFeedback(`${result.loadable_units.length} units can be loaded. Ctrl+Click to load.`);
        } else {
            showTransportFeedback("No units available to load.");
        }
    }).catch(error => {
        logger.error('Failed to get loadable units:', error);
        showTransportFeedback("Failed to get loadable units.");
    });
}

/**
 * Show unload positions highlight
 * @param {number} transportX - Transport X coordinate
 * @param {number} transportY - Transport Y coordinate
 */
export function showUnloadPositionsHighlight(transportX, transportY) {
    clearTransportHighlights();
    
    jsonrpc('get_unload_positions', {x: transportX, y: transportY}).then(result => {
        if (result?.success && result.valid_positions) {
            transportState.transportHighlights.unloadPositions = result.valid_positions;
            transportState.transportHighlights.selectedTransport = {x: transportX, y: transportY};
            
            // Update global reference
            window.transportHighlights = transportState.transportHighlights;
            
            // Add visual highlights
            const highlights = result.valid_positions.map(pos => ({
                x: pos.x,
                y: pos.y,
                type: 'exit-position'
            }));
            
            window.transportHighlights = highlights;
            renderTransportHighlights();
            
            showTransportFeedback(`${result.valid_positions.length} positions available. Alt+Click to unload.`);
        } else {
            showTransportFeedback("No valid unload positions.");
        }
    }).catch(error => {
        logger.error('Failed to get unload positions:', error);
        showTransportFeedback("Failed to get unload positions.");
    });
}

// ===== LOAD/UNLOAD OPERATIONS =====

/**
 * Attempt to load a unit into transport
 * @param {number} transportX - Transport X coordinate
 * @param {number} transportY - Transport Y coordinate
 * @param {number} cargoX - Cargo unit X coordinate
 * @param {number} cargoY - Cargo unit Y coordinate
 */
export function attemptLoadUnit(transportX, transportY, cargoX, cargoY) {
    jsonrpc('cargo_board_transport', {
        transport_x: transportX,
        transport_y: transportY,
        cargo_x: cargoX,
        cargo_y: cargoY
    }).then(result => {
        if (result?.success) {
            showTransportFeedback(result.message || 'Unit loaded successfully', 'success');
            clearTransportHighlights();
            update();
        } else {
            showTransportFeedback(`Load failed: ${result?.error || result?.message || 'Unknown error'}`, 'error');
        }
    }).catch(error => {
        logger.error('Load error:', error);
        showTransportFeedback(`Load failed: ${error.message || 'Unknown error'}`, 'error');
    });
}

/**
 * Attempt to unload a unit from transport
 * @param {number} transportX - Transport X coordinate
 * @param {number} transportY - Transport Y coordinate
 * @param {number} unloadX - Unload position X coordinate
 * @param {number} unloadY - Unload position Y coordinate
 * @param {number} cargoIndex - Index of cargo to unload
 */
export function attemptUnloadUnit(transportX, transportY, unloadX, unloadY, cargoIndex = 0) {
    jsonrpc('cargo_exit_transport', {
        transport_x: transportX,
        transport_y: transportY,
        exit_x: unloadX,
        exit_y: unloadY,
        cargo_index: cargoIndex
    }).then(result => {
        if (result?.success) {
            showTransportFeedback(result.message || 'Unit unloaded successfully', 'success');
            clearTransportHighlights();
            update();
        } else {
            showTransportFeedback(`Unload failed: ${result?.error || result?.message || 'Unknown error'}`, 'error');
        }
    }).catch(error => {
        logger.error('Unload error:', error);
        showTransportFeedback(`Unload failed: ${error.message || 'Unknown error'}`, 'error');
    });
}

// ===== CLICK HANDLERS =====

/**
 * Handle transport operations from click events
 * @param {Object} tile - Clicked tile
 * @param {Event} event - Click event
 * @returns {boolean} True if transport operation was handled
 */
export function handleTransportOperations(tile, event) {
    // Only handle if we have the required functions
    if (!handleLoadingClick || !handleUnloadingClick) {
        return false;
    }
    
    try {
        // Handle Ctrl+Click for loading
        if (event.ctrlKey) {
            return handleLoadingClick(tile);
        }
        
        // Handle Alt+Click for unloading
        if (event.altKey) {
            return handleUnloadingClick(tile);
        }
        
        return false; // No transport operation
    } catch (error) {
        logger.error('TRANSPORT_FIX: Transport operation failed:', error);
        showTransportFeedback('Transport operation failed: ' + error.message, 'error');
        return false;
    }
}

/**
 * Handle loading click
 * @param {Object} tile - Clicked tile
 * @returns {boolean} True if loading was handled
 */
export function handleLoadingClick(tile) {
    // Check if this tile has a loadable unit highlighted
    const isLoadable = transportState.transportHighlights.loadableUnits.some(unit =>
        unit.x === tile.x && unit.y === tile.y
    );
    
    if (isLoadable && transportState.transportHighlights.selectedTransport) {
        attemptLoadUnit(
            transportState.transportHighlights.selectedTransport.x,
            transportState.transportHighlights.selectedTransport.y,
            tile.x,
            tile.y
        );
        return true; // Transport operation handled
    }
    
    return false;
}

/**
 * Handle unloading click
 * @param {Object} tile - Clicked tile
 * @returns {boolean} True if unloading was handled
 */
export function handleUnloadingClick(tile) {
    // Check if this tile is a valid unload position
    const isUnloadable = transportState.transportHighlights.unloadPositions.some(pos =>
        pos.x === tile.x && pos.y === tile.y
    );
    
    if (isUnloadable && transportState.transportHighlights.selectedTransport) {
        const transport = transportState.transportHighlights.selectedTransport;
        
        // Get cargo info first
        jsonrpc('get_cargo_info', {x: transport.x, y: transport.y}).then(cargoResult => {
            if (!cargoResult || cargoResult.error) {
                logger.error('Failed to get cargo info:', cargoResult?.error);
                return;
            }
            
            const cargoUnits = cargoResult.cargo_units || cargoResult.cargo || [];
            if (cargoUnits.length === 0) {
                logger.warn('Transport has no cargo to unload');
                showTransportFeedback('No cargo to unload', 'error');
                return;
            }
            
            // If only one unit, unload it directly
            if (cargoUnits.length === 1) {
                attemptUnloadUnit(transport.x, transport.y, tile.x, tile.y, 0);
            } else {
                // Show cargo selection UI for multiple units
                if (window.CargoSelectionUI) {
                    const ui = new window.CargoSelectionUI();
                    ui.show(cargoUnits, (selectedIndex) => {
                        attemptUnloadUnit(transport.x, transport.y, tile.x, tile.y, selectedIndex);
                    });
                } else {
                    // Fallback: unload first unit
                    attemptUnloadUnit(transport.x, transport.y, tile.x, tile.y, 0);
                }
            }
        }).catch(error => {
            logger.error('Failed to get cargo info:', error);
            showTransportFeedback('Failed to get cargo info', 'error');
        });
        
        return true; // Transport operation handled
    }
    
    return false;
}

/**
 * Handle transport alt-click
 * @param {Object} tile - Clicked tile
 * @param {Event} event - Click event
 * @returns {boolean} True if handled
 */
export function handleTransportAltClick(tile, event) {
    // Check if we're alt-clicking on a transport with cargo
    if (tile.unit && isTransportUnit(tile.unit)) {
        jsonrpc('get_cargo_info', {x: tile.x, y: tile.y}).then(result => {
            if (result?.success && result.cargo_info && result.cargo_info.current_cargo > 0) {
                showUnloadPositionsHighlight(tile.x, tile.y);
            }
        });
        return true;
    }
    return false;
}

/**
 * Handle transport right-click
 * @param {Object} tile - Clicked tile
 * @param {Event} event - Click event
 * @returns {boolean} True if handled
 */
export function handleTransportRightClick(tile, event) {
    // Check if this is a transport unit
    if (tile.unit && isTransportUnit(tile.unit)) {
        logger.debug('Right-click on transport unit');
        
        // Check for Black Boat repair functionality
        if (tile.unit.type === 'BLACKBOAT' && window.gameState?.selectedUnit) {
            const selectedUnit = window.gameState.selectedUnit;
            
            // Check if selected unit is adjacent and can be repaired
            const dx = Math.abs(selectedUnit.x - tile.x);
            const dy = Math.abs(selectedUnit.y - tile.y);
            const isAdjacent = (dx + dy) === 1;
            const sameTeam = selectedUnit.unit?.army === tile.unit.army;
            const needsRepair = selectedUnit.unit?.hp < 100;
            
            if (isAdjacent && sameTeam && needsRepair) {
                // Show repair context menu
                if (window.showUnitContextMenu) {
                    window.showUnitContextMenu(event.pageX, event.pageY, selectedUnit, tile.unit);
                }
                return true;
            }
        }
        
        // Show cargo info
        jsonrpc('get_cargo_info', {x: tile.x, y: tile.y}).then(result => {
            if (result?.success && result.cargo_info) {
                showCargoInfo(tile.unit, result.cargo_info);
            }
        });
        
        return true;
    }
    
    return false;
}

// ===== TRANSPORT STATUS =====

/**
 * Get transport status for debugging
 */
export function getTransportStatus() {
    logger.debug('=== TRANSPORT STATUS ===');
    logger.debug('Selected Transport:', transportState.transportHighlights.selectedTransport);
    logger.debug('Loadable Units:', transportState.transportHighlights.loadableUnits.length);
    logger.debug('Unload Positions:', transportState.transportHighlights.unloadPositions.length);
    
    const board = getBoard();
    if (board?.selected?.unit && isTransportUnitForRender(board.selected.unit)) {
        jsonrpc('get_cargo_info', {
            x: board.selected.x,
            y: board.selected.y
        }).then(result => {
            if (result?.success) {
                logger.debug('Transport cargo:', result);
                showTransportFeedback(`Transport has ${result.cargo_count || 0} units loaded`);
            }
        });
    }
}

// ===== INITIALIZATION =====

/**
 * Initialize transport system
 */
export function initializeTransportSystem() {
    logger.info('Initializing transport system...');
    
    // Add CSS for transport highlights if not already added
    if (!document.getElementById('transport-styles')) {
        const style = document.createElement('style');
        style.id = 'transport-styles';
        style.textContent = `
            .loadable-unit {
                background-color: rgba(76, 175, 80, 0.3) !important;
                border: 2px solid #4CAF50 !important;
            }
            
            .unload-position {
                background-color: rgba(33, 150, 243, 0.3) !important;
                border: 2px solid #2196F3 !important;
            }
            
            .transport-feedback {
                animation: fadeIn 0.3s ease-in;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
        `;
        document.head.appendChild(style);
    }
    
    logger.info('Transport system initialized');
}

/**
 * Initialize the transport system module
 */
export function initializeTransportSystemModule() {
    logger.info('Initializing transport system module...');
    
    // Set up global references for legacy compatibility
    if (window) {
        // Transport checks
        window.isTransportUnit = isTransportUnit;
        window.isTransportUnitForRender = isTransportUnitForRender;
        window.getCargoCountForRender = getCargoCountForRender;
        
        // Transport selection
        window.handleTransportSelectionLogic = handleTransportSelectionLogic;
        
        // Highlight management
        window.clearTransportHighlights = clearTransportHighlights;
        window.showLoadableUnitsHighlight = showLoadableUnitsHighlight;
        window.showUnloadPositionsHighlight = showUnloadPositionsHighlight;
        
        // Load/unload operations
        window.attemptLoadUnit = attemptLoadUnit;
        window.attemptUnloadUnit = attemptUnloadUnit;
        
        // Click handlers
        window.handleTransportOperations = handleTransportOperations;
        window.handleLoadingClick = handleLoadingClick;
        window.handleUnloadingClick = handleUnloadingClick;
        window.handleTransportAltClick = handleTransportAltClick;
        window.handleTransportRightClick = handleTransportRightClick;
        
        // Transport status
        window.getTransportStatus = getTransportStatus;
        
        // Initialize CSS
        initializeTransportSystem();
    }
    
    logger.info('Transport system module initialized');
}

// Initialize on module load
initializeTransportSystemModule();