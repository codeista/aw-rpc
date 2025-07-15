/**
 * Movement System Module - Handles unit movement calculations and highlighting
 * Extracted from render.js as part of modularization effort
 */

import { jsonrpc } from './network.js';
import { getBoard, getTile } from './gameState.js';
import { renderMovementHighlights } from './renderEngine.js';

// Ensure logger exists
if (typeof window.logger === 'undefined') {
    window.logger = console; // Fallback to console if logger.js isn't loaded
}
const logger = window.logger;

// ===== MOVEMENT STATE =====
const movementState = {
    movementHighlights: [],
    movementHighlightGroup: null
};

// Make movementHighlights globally accessible
if (window) {
    window.movementHighlights = movementState.movementHighlights;
}

// ===== MOVEMENT RANGE CALCULATION =====

/**
 * Show movement range for a unit
 * @param {number} unitX - Unit X coordinate
 * @param {number} unitY - Unit Y coordinate
 */
export function showMovementRange(unitX, unitY) {
    logger.debug(`🚶 Showing movement range for unit at (${unitX}, ${unitY})`);
    
    // Use the backend movement highlights RPC
    jsonrpc('get_movement_highlights', {x: unitX, y: unitY})
        .then(result => {
            if (result?.success && result.moves) {
                applyMovementHighlights(result.moves);
            } else {
                // Fallback to local calculation
                logger.debug('Backend movement failed, calculating locally');
                calculateMovementRangeLocally(unitX, unitY);
            }
        })
        .catch(error => {
            logger.error('Movement range request failed:', error);
            calculateMovementRangeLocally(unitX, unitY);
        });
}

/**
 * Highlight movement range for a unit (older interface)
 * @param {number} unitX - Unit X coordinate
 * @param {number} unitY - Unit Y coordinate
 */
export function highlightMovementRange(unitX, unitY) {
    logger.debug(`🚶 Highlighting movement range for unit at (${unitX}, ${unitY})`);
    
    // Get movement range data from backend
    jsonrpc('get_unit_valid_moves', {x: unitX, y: unitY})
        .then(result => {
            if (result?.success && result.moves) {
                clearMovementHighlights();
                
                result.moves.forEach(move => {
                    highlightMovementTile(move.x, move.y, 'movement-range');
                });
                
                // Render the highlights
                renderMovementHighlights();
            } else {
                // Fallback: calculate movement range locally
                calculateMovementRangeLocally(unitX, unitY);
            }
        })
        .catch(error => {
            logger.error('Movement range request failed:', error);
            calculateMovementRangeLocally(unitX, unitY);
        });
}

/**
 * Apply movement highlights from server data
 * @param {Array} moves - Array of valid move positions
 */
function applyMovementHighlights(moves) {
    // Clear existing highlights
    clearMovementHighlightsData();
    
    // Store new highlights
    movementState.movementHighlights = moves.map(move => ({
        x: move.x,
        y: move.y,
        type: 'movement-range'
    }));
    
    // Update global reference
    window.movementHighlights = movementState.movementHighlights;
    
    // Update the board tiles to mark them as moveable
    const board = getBoard();
    if (board?.grid) {
        moves.forEach(move => {
            const tile = board.grid.find(t => t.x === move.x && t.y === move.y);
            if (tile) {
                tile.can_be_moved_to = true;
            }
        });
    }
    
    // Force immediate rendering
    renderMovementHighlights();
}

/**
 * Calculate movement range locally (fallback)
 * @param {number} unitX - Unit X coordinate
 * @param {number} unitY - Unit Y coordinate
 */
function calculateMovementRangeLocally(unitX, unitY) {
    logger.debug('Calculating movement range locally');
    
    const board = getBoard();
    if (!board?.grid) return;
    
    // Don't clear if we already have highlights
    if (movementState.movementHighlights.length > 0) {
        return;
    }
    
    // Get the selected unit
    const selectedTile = board.grid.find(t => t.x === unitX && t.y === unitY);
    const selectedUnit = selectedTile?.unit;
    
    if (!selectedUnit) {
        logger.error('No unit found at position');
        return;
    }
    
    // Get movement range (use unit's movement stat if available)
    const movementRange = selectedUnit.movement || selectedUnit.moveRange || 5;
    
    // Calculate valid moves
    const validMoves = calculateMovementWithCosts(unitX, unitY, movementRange, selectedUnit);
    
    // Clear and apply highlights
    clearMovementHighlights();
    
    validMoves.forEach(move => {
        highlightMovementTile(move.x, move.y, 'movement-range');
    });
    
    // Render the highlights
    renderMovementHighlights();
}

/**
 * Calculate valid movement positions considering terrain costs
 * @param {number} startX - Starting X coordinate
 * @param {number} startY - Starting Y coordinate
 * @param {number} maxMovement - Maximum movement range
 * @param {Object} unit - Unit object
 * @returns {Array} Array of valid move positions
 */
export function calculateMovementWithCosts(startX, startY, maxMovement, unit) {
    const validMoves = [];
    const visited = new Set();
    const queue = [{x: startX, y: startY, cost: 0}];
    const board = getBoard();
    
    if (!board?.grid) return validMoves;
    
    while (queue.length > 0) {
        const current = queue.shift();
        const key = `${current.x},${current.y}`;
        
        if (visited.has(key)) continue;
        visited.add(key);
        
        // Add this position as a valid move (except starting position)
        if (current.cost > 0 && current.cost <= maxMovement) {
            const targetTile = board.grid.find(t => t.x === current.x && t.y === current.y);
            if (targetTile && canUnitMoveToTile(unit, targetTile)) {
                validMoves.push({x: current.x, y: current.y, cost: current.cost});
            }
        }
        
        // Check adjacent tiles
        const directions = [[0, -1], [1, 0], [0, 1], [-1, 0]]; // N, E, S, W
        
        for (const [dx, dy] of directions) {
            const newX = current.x + dx;
            const newY = current.y + dy;
            const newKey = `${newX},${newY}`;
            
            // Skip if already visited
            if (visited.has(newKey)) continue;
            
            // Check bounds
            if (newX < 0 || newX >= board.width || newY < 0 || newY >= board.height) continue;
            
            // Get terrain cost
            const tile = board.grid.find(t => t.x === newX && t.y === newY);
            if (!tile) continue;
            
            const movementCost = getMovementCost(unit, tile);
            const totalCost = current.cost + movementCost;
            
            // Skip if cost exceeds movement range
            if (totalCost > maxMovement) continue;
            
            // Add to queue
            queue.push({x: newX, y: newY, cost: totalCost});
        }
    }
    
    return validMoves;
}

/**
 * Get movement cost for a unit on a tile
 * @param {Object} unit - Unit object
 * @param {Object} tile - Tile object
 * @returns {number} Movement cost
 */
function getMovementCost(unit, tile) {
    // Simplified movement costs - would be more complex in full implementation
    const terrainType = tile.mapTile?.type || 'PLAIN';
    
    // Basic terrain costs
    const baseCosts = {
        'PLAIN': 1,
        'ROAD': 1,
        'WOOD': 2,
        'MOUNTAIN': 3,
        'RIVER': 2,
        'SEA': 999, // Impassable for land units
        'REEF': 2,
        'SHOAL': 1
    };
    
    return baseCosts[terrainType] || 1;
}

/**
 * Check if unit can move to a tile
 * @param {Object} unit - Unit object
 * @param {Object} tile - Target tile
 * @returns {boolean} True if unit can move to tile
 */
function canUnitMoveToTile(unit, tile) {
    // Can't move to occupied tiles (except same team for joining)
    if (tile.unit) {
        return tile.unit.army === unit.army && canUnitsJoin(unit, tile.unit);
    }
    
    // Check terrain compatibility
    const terrainType = tile.mapTile?.type || 'PLAIN';
    const unitType = unit.type?.name || unit.type || '';
    
    // Sea units can only move on sea/shoal
    if (isSeaUnit(unitType)) {
        return ['SEA', 'REEF', 'SHOAL'].includes(terrainType);
    }
    
    // Air units can move anywhere
    if (isAirUnit(unitType)) {
        return true;
    }
    
    // Land units can't move on sea
    return !['SEA', 'REEF'].includes(terrainType);
}

/**
 * Check if two units can join
 * @param {Object} unit1 - First unit
 * @param {Object} unit2 - Second unit
 * @returns {boolean} True if units can join
 */
function canUnitsJoin(unit1, unit2) {
    // Units can join if same type and combined HP <= 100
    if (unit1.type !== unit2.type) return false;
    
    const hp1 = unit1.status?.hp || unit1.hp || 100;
    const hp2 = unit2.status?.hp || unit2.hp || 100;
    
    return (hp1 + hp2) <= 100;
}

/**
 * Check if unit is a sea unit
 * @param {string} unitType - Unit type
 * @returns {boolean} True if sea unit
 */
function isSeaUnit(unitType) {
    const seaUnits = ['BATTLESHIP', 'CRUISER', 'LANDER', 'SUB', 'CARRIER', 'BLACKBOAT'];
    return seaUnits.includes(unitType);
}

/**
 * Check if unit is an air unit
 * @param {string} unitType - Unit type
 * @returns {boolean} True if air unit
 */
function isAirUnit(unitType) {
    const airUnits = ['FIGHTER', 'BOMBER', 'BCOPTER', 'TCOPTER', 'STEALTH', 'BLACKBOMB'];
    return airUnits.includes(unitType);
}

// ===== HIGHLIGHT MANAGEMENT =====

/**
 * Highlight a movement tile
 * @param {number} x - Tile X coordinate
 * @param {number} y - Tile Y coordinate
 * @param {string} className - CSS class name
 */
function highlightMovementTile(x, y, className) {
    // Add to movement highlights array
    movementState.movementHighlights.push({
        x: x,
        y: y,
        type: className
    });
    
    // Update global reference
    window.movementHighlights = movementState.movementHighlights;
}

/**
 * Clear movement highlights (visual only)
 */
export function clearMovementHighlights() {
    // Clear visual highlights in Two.js ONLY
    if (window.movementHighlightGroup && window.two) {
        window.two.remove(window.movementHighlightGroup);
        window.movementHighlightGroup = null;
    }
    
    // Also clear from movementState
    if (movementState.movementHighlightGroup && window.two) {
        window.two.remove(movementState.movementHighlightGroup);
        movementState.movementHighlightGroup = null;
    }
}

/**
 * Clear movement highlights data
 */
export function clearMovementHighlightsData() {
    // Clear the data array
    movementState.movementHighlights = [];
    window.movementHighlights = [];
    
    // Clear can_be_moved_to flags from all tiles
    const board = getBoard();
    if (board?.grid) {
        board.grid.forEach(tile => {
            tile.can_be_moved_to = false;
        });
    }
}

/**
 * Add movement highlights to scene
 */
export function addMovementHighlightsToScene() {
    if (movementState.movementHighlights.length > 0) {
        renderMovementHighlights();
    }
}

/**
 * Update movement highlights
 */
export function updateMovementHighlights() {
    if (movementState.movementHighlights.length > 0) {
        renderMovementHighlights();
    }
}

// ===== UNIT SELECTION WITH MOVEMENT =====

/**
 * Select unit with movement highlighting
 * @param {Object} tile - Tile containing unit
 */
export function unitSelectWithMovementHighlighting(tile) {
    logger.debug('🎯 Unit select with movement highlighting');
    
    try {
        // Step 1: Basic unit selection
        jsonrpc('unit_select', {x: tile.x, y: tile.y}).then(result => {
            if (result && !result.error) {
                // Set board selection
                const board = getBoard();
                if (board) {
                    board.selected = tile;
                }
                
                // Step 2: Show movement range for selected unit
                if (tile.unit && tile.unit.army === board?.current_turn) {
                    highlightMovementRange(tile.x, tile.y);
                    
                    // Step 3: Also show attack range if available
                    if (window.highlightAttackRange) {
                        setTimeout(() => {
                            window.highlightAttackRange(tile.x, tile.y);
                        }, 100);
                    }
                } else {
                    clearMovementHighlights();
                }
                
                // Step 4: Handle transport functionality if available
                if (window.handleTransportSelectionLogic) {
                    window.handleTransportSelectionLogic(tile);
                }
            } else {
                logger.error('Unit selection failed:', result);
            }
        });
        
    } catch (error) {
        logger.error('Selection error:', error);
        // Fallback to basic selection
        jsonrpc('unit_select', {x: tile.x, y: tile.y});
    }
}

// ===== MODULE INITIALIZATION =====

/**
 * Initialize the movement system module
 */
export function initializeMovementSystemModule() {
    logger.info('Initializing movement system module...');
    
    // Set up global references for legacy compatibility
    if (window) {
        // Movement range functions
        window.showMovementRange = showMovementRange;
        window.highlightMovementRange = highlightMovementRange;
        window.calculateMovementWithCosts = calculateMovementWithCosts;
        
        // Highlight management
        window.clearMovementHighlights = clearMovementHighlights;
        window.clearMovementHighlightsData = clearMovementHighlightsData;
        window.addMovementHighlightsToScene = addMovementHighlightsToScene;
        window.updateMovementHighlights = updateMovementHighlights;
        
        // Unit selection
        window.unitSelectWithMovementHighlighting = unitSelectWithMovementHighlighting;
        
        // Ensure movementHighlights array is accessible
        window.movementHighlights = movementState.movementHighlights;
    }
    
    logger.info('Movement system module initialized');
}

// Initialize on module load
initializeMovementSystemModule();