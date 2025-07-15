/**
 * Game Actions Module - Handles all game actions like unit operations, turn management
 * Extracted from render.js as part of modularization effort
 */

import { jsonrpc } from './network.js';
import { getBoard, setSelectedTile, update, getSelectedTile } from './gameState.js';
import { showTransportFeedback, showLoadingIndicator, hideLoadingIndicator, showCargoInfo } from './uiSystems.js';

// Ensure logger exists
if (typeof window.logger === 'undefined') {
    window.logger = console; // Fallback to console if logger.js isn't loaded
}
const logger = window.logger;

// ===== TURN MANAGEMENT =====

/**
 * End the current army's turn
 */
export async function armyEndTurn() {
    logger.debug('🔄 Ending turn...');
    
    // Use operation queue with high priority
    if (window.operationQueue) {
        return window.operationQueue.add(async () => {
            // Clear ALL highlights before ending turn
            if (window.clearAllHighlights) {
                window.clearAllHighlights();
            }
            
            // Clean up transport state
            if (window.cleanupTransportState) {
                window.cleanupTransportState();
            }
            
            // Clear selection state
            setSelectedTile(null);
            
            // Clear game state
            if (window.gameState) {
                window.gameState.selectedUnit = null;
                window.gameState.movementPhase = false;
                window.gameState.showingAttackTargets = false;
                window.gameState.attackHighlights = [];
            }
            
            // Make the RPC call
            return jsonrpc('army_end_turn', {});
        }, {
            id: 'end-turn',
            description: 'Ending turn',
            priority: 10,
            showLoading: true,
            preventDuplicate: true
        }).then(result => {
            logger.info('✅ Turn ended successfully');
            // Force complete re-render
            if (window.forceSceneRefresh) {
                window.forceSceneRefresh();
            }
            update();
        }).catch(error => {
            logger.error('❌ Failed to end turn:', error);
            alert('Failed to end turn: ' + (error.message || error));
        });
    } else {
        // Fallback without operation queue
        try {
            await jsonrpc('army_end_turn', {});
            update();
        } catch (error) {
            logger.error('Failed to end turn:', error);
        }
    }
}

/**
 * End the game
 */
export function endGame() {
    jsonrpc('end_game', {}).then(() => {
        logger.info('Game ended');
        update();
    }).catch(error => {
        logger.error('Failed to end game:', error);
    });
}

// ===== UNIT SELECTION =====

/**
 * Select a unit
 * @param {Object} tile - Tile containing unit to select
 */
export function unitSelect(tile) {
    jsonrpc('unit_select', {x: tile.x, y: tile.y}).then(() => {
        // Update gameState for context menu
        if (tile.unit && window.gameState) {
            window.gameState.selectedUnit = tile.unit;
            window.gameState.selectedUnit.x = tile.x;
            window.gameState.selectedUnit.y = tile.y;
        }
        update();
    }).catch(error => {
        logger.error('Failed to select unit:', error);
    });
}

/**
 * Select unit with movement and attack range display
 * @param {Object} tile - Tile containing unit to select
 */
export function unitSelectWithTransportAndRange(tile) {
    try {
        // Step 1: Basic unit selection
        jsonrpc('unit_select', {x: tile.x, y: tile.y});
        
        // Step 2: Show movement range AND attack targets
        if (tile.unit && tile.unit.army === getBoard()?.current_turn) {
            // Show movement range
            if (window.showMovementRange) {
                window.showMovementRange(tile.x, tile.y);
            }
            
            // Show attack targets after a short delay
            setTimeout(() => {
                if (window.showAttackTargets) {
                    window.showAttackTargets(tile.x, tile.y);
                }
            }, 200);
        } else {
            if (window.clearAllHighlights) {
                window.clearAllHighlights();
            }
        }
        
        // Step 3: Handle transport functionality
        if (window.handleTransportSelectionLogic) {
            window.handleTransportSelectionLogic(tile);
        }
        
    } catch (error) {
        logger.error('SELECTION_FIX: Unit selection failed:', error);
        jsonrpc('unit_select', {x: tile.x, y: tile.y});
    }
}

// ===== UNIT MOVEMENT =====

/**
 * Move a unit
 * @param {Object} targetTile - Target tile to move to
 */
export function unitMove(targetTile) {
    const board = getBoard();
    const source = board?.selected || window.gameState?.selectedUnit;
    
    if (!source) {
        logger.error('No unit selected for movement');
        return;
    }
    
    jsonrpc('unit_move', {
        x: source.x,
        y: source.y,
        x2: targetTile.x,
        y2: targetTile.y
    }).then(result => {
        // Update the selected tile position
        setSelectedTile(targetTile);
        
        // Clear movement highlights but keep unit selected for potential attack
        if (window.clearMovementHighlights) {
            window.clearMovementHighlights();
        }
        
        // Show attack options from new position
        setTimeout(() => {
            if (window.showAttackTargets) {
                window.showAttackTargets(targetTile.x, targetTile.y);
            }
        }, 300);
        
        // Update the board
        update();
    }).catch(error => {
        logger.error('Failed to move unit:', error);
        alert('Move failed: ' + (error.message || error));
    });
}

// ===== UNIT COMBAT =====

/**
 * Attack with a unit
 * @param {Object} targetTile - Target tile to attack
 */
export function unitAttack(targetTile) {
    const board = getBoard();
    const source = board?.selected;
    
    if (!source) {
        logger.error('No unit selected for attack');
        return;
    }
    
    // Use operation queue to prevent double-attacks
    if (window.operationQueue) {
        window.operationQueue.add(
            () => jsonrpc('unit_attack', {x: source.x, y: source.y, x2: targetTile.x, y2: targetTile.y}),
            {
                id: `attack-${source.x}-${source.y}-${targetTile.x}-${targetTile.y}`,
                description: 'Attacking',
                priority: 8,
                showLoading: true,
                preventDuplicate: true
            }
        ).then(result => {
            logger.info('⚔️ Attack completed');
            
            // Clear all highlights after attack
            if (window.clearAllHighlights) {
                window.clearAllHighlights();
            }
            
            // Clear selection
            setSelectedTile(null);
            
            // Update board
            update();
        }).catch(error => {
            logger.error('❌ Attack failed:', error);
            alert('Attack failed: ' + (error.message || error));
        });
    } else {
        // Fallback without operation queue
        jsonrpc('unit_attack', {
            x: source.x,
            y: source.y,
            x2: targetTile.x,
            y2: targetTile.y
        }).then(() => {
            update();
        }).catch(error => {
            logger.error('Attack failed:', error);
        });
    }
}

/**
 * Attack with combat preview
 * @param {Object} targetTile - Target tile to attack
 */
export async function unitAttackWithPreview(targetTile) {
    const board = getBoard();
    const source = board?.selected;
    
    if (!source) {
        logger.error('No unit selected for attack');
        return;
    }
    
    // Show combat preview
    if (window.showCombatPreview) {
        window.showCombatPreview(source.x, source.y, targetTile.x, targetTile.y);
    } else {
        // Fallback to regular attack
        unitAttack(targetTile);
    }
}

// ===== UNIT ACTIONS =====

/**
 * Make unit wait
 * @param {Object} tile - Tile containing unit
 */
export function unitWait(tile) {
    jsonrpc('unit_wait', {x: tile.x, y: tile.y}).then(result => {
        // Manually update unit flags after wait
        const board = getBoard();
        if (board?.grid) {
            const unitTile = board.grid.find(t => t.x === tile.x && t.y === tile.y);
            if (unitTile?.unit) {
                logger.debug('📝 Unit waited - marking as unavailable');
                unitTile.unit.can_move = false;
                unitTile.unit.can_attack = false;
                unitTile.unit.can_capture = false;
            }
        }
        
        // Clear highlights
        if (window.clearAllHighlights) {
            window.clearAllHighlights();
        }
        
        // Update board
        update();
    }).catch(error => {
        logger.error('Failed to wait unit:', error);
    });
}

/**
 * Capture property with unit
 * @param {Object} tile - Tile containing unit
 */
export function unitCapture(tile) {
    jsonrpc('capture_tile', {x: tile.x, y: tile.y}).then(result => {
        // Manually update unit flags after capture
        const board = getBoard();
        if (board?.grid) {
            const unitTile = board.grid.find(t => t.x === tile.x && t.y === tile.y);
            if (unitTile?.unit) {
                logger.info('📝 Unit captured - marking as unavailable');
                unitTile.unit.can_move = false;
                unitTile.unit.can_attack = false;
                unitTile.unit.can_capture = false;
            }
        }
        
        // Clear highlights
        if (window.clearAllHighlights) {
            window.clearAllHighlights();
        }
        
        // Update board
        update();
    }).catch(error => {
        logger.error('Failed to capture:', error);
    });
}

// ===== UNIT CREATION =====

/**
 * Create land unit at factory
 * @param {Object} tile - Factory tile
 */
export function unitCreate(tile) {
    showUnitCreationModal(tile, 'land');
}

/**
 * Create air unit at airport
 * @param {Object} tile - Airport tile
 */
export function airunitCreate(tile) {
    showUnitCreationModal(tile, 'air');
}

/**
 * Create sea unit at port
 * @param {Object} tile - Port tile
 */
export function seaunitCreate(tile) {
    showUnitCreationModal(tile, 'sea');
}

/**
 * Show unit creation modal
 * @param {Object} tile - Production tile
 * @param {string} type - Unit type category (land/air/sea)
 */
function showUnitCreationModal(tile, type) {
    const modal = document.getElementById('modalcreate');
    const span = document.getElementsByClassName('close')[0];
    const select = document.getElementById('selectcreate');
    const btn = document.getElementById('buttoncreate');
    
    if (!modal || !select || !btn) {
        logger.error('Unit creation modal elements not found');
        return;
    }
    
    // Clear previous options
    select.innerHTML = '';
    
    // Add appropriate unit options based on type
    const unitOptions = {
        land: ['INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 'NEOTANK', 'MEGATANK', 'APC', 'ARTILLERY', 'ROCKET', 'ANTIAIR', 'MISSILE', 'PIPERUNNER'],
        air: ['FIGHTER', 'BOMBER', 'BCOPTER', 'TCOPTER', 'STEALTH', 'BLACKBOMB'],
        sea: ['BATTLESHIP', 'CRUISER', 'LANDER', 'SUB', 'CARRIER', 'BLACKBOAT']
    };
    
    const units = unitOptions[type] || [];
    units.forEach(unitType => {
        const option = document.createElement('option');
        option.value = unitType;
        option.textContent = unitType;
        select.appendChild(option);
    });
    
    // Show modal
    modal.style.display = 'block';
    
    // Set up event handlers
    span.onclick = () => {
        modal.style.display = 'none';
    };
    
    window.onclick = (ev) => {
        if (ev.target === modal) {
            modal.style.display = 'none';
        }
    };
    
    btn.onclick = () => {
        modal.style.display = 'none';
        const unitType = select.value;
        const army = tile.mapTile.army;
        
        // Use operation queue if available
        if (window.operationQueue) {
            window.operationQueue.add(
                () => jsonrpc('unit_create', {army: army, unit_type: unitType, x: tile.x, y: tile.y}),
                {
                    id: `create-${unitType}-${tile.x}-${tile.y}`,
                    description: `Creating ${unitType}`,
                    priority: 7,
                    showLoading: true,
                    preventDuplicate: true
                }
            ).then(result => {
                logger.info(`✅ Created ${unitType} at (${tile.x}, ${tile.y})`);
                update();
            }).catch(error => {
                logger.error('❌ Unit creation failed:', error);
                alert('Failed to create unit: ' + (error.message || error));
            });
        } else {
            // Fallback without operation queue
            jsonrpc('unit_create', {
                army: army,
                unit_type: unitType,
                x: tile.x,
                y: tile.y
            }).then(() => {
                update();
            }).catch(error => {
                logger.error('Unit creation failed:', error);
            });
        }
    };
}

// ===== TRANSPORT OPERATIONS =====

/**
 * Load unit into transport
 * @param {Object} transportTile - Transport tile
 */
export function unitLoad(transportTile) {
    const board = getBoard();
    const source = board?.selected || window.gameState?.selectedUnit;
    
    if (!source) {
        logger.error('No unit selected for loading');
        return;
    }
    
    jsonrpc('cargo_board_transport', {
        cargo_x: source.x,
        cargo_y: source.y,
        transport_x: transportTile.x,
        transport_y: transportTile.y
    }).then(result => {
        showTransportFeedback('Unit loaded successfully', 'success');
        
        // Clear selection and highlights
        setSelectedTile(null);
        if (window.clearAllHighlights) {
            window.clearAllHighlights();
        }
        
        update();
    }).catch(error => {
        logger.error('Failed to load unit:', error);
        showTransportFeedback('Failed to load unit: ' + (error.message || error), 'error');
    });
}

/**
 * Unload unit from transport
 * @param {Object} targetTile - Target tile for unloading
 */
export function unitUnload(targetTile) {
    const board = getBoard();
    const source = board?.selected || window.gameState?.selectedUnit;
    
    if (!source) {
        logger.error('No transport selected for unloading');
        return;
    }
    
    // First, get cargo info to see what units are in the transport
    jsonrpc('get_cargo_info', {x: source.x, y: source.y}).then(cargoResult => {
        if (!cargoResult?.cargo_units || cargoResult.cargo_units.length === 0) {
            showTransportFeedback('No units to unload', 'error');
            return;
        }
        
        // If multiple units, show selection UI
        if (cargoResult.cargo_units.length > 1 && window.CargoSelectionUI) {
            const ui = new window.CargoSelectionUI();
            ui.show(cargoResult.cargo_units, (selectedIndex) => {
                performUnload(source, targetTile, selectedIndex);
            });
        } else {
            // Single unit, unload at index 0
            performUnload(source, targetTile, 0);
        }
    }).catch(error => {
        logger.error('Failed to get cargo info:', error);
        showTransportFeedback('Failed to unload: ' + (error.message || error), 'error');
    });
}

/**
 * Perform the actual unload operation
 * @param {Object} transport - Transport tile
 * @param {Object} targetTile - Target tile
 * @param {number} cargoIndex - Index of cargo to unload
 */
function performUnload(transport, targetTile, cargoIndex) {
    jsonrpc('cargo_exit_transport', {
        transport_x: transport.x,
        transport_y: transport.y,
        exit_x: targetTile.x,
        exit_y: targetTile.y,
        cargo_index: cargoIndex
    }).then(result => {
        showTransportFeedback('Unit unloaded successfully', 'success');
        
        // Clear selection and highlights
        setSelectedTile(null);
        if (window.clearAllHighlights) {
            window.clearAllHighlights();
        }
        
        update();
    }).catch(error => {
        logger.error('Failed to unload unit:', error);
        showTransportFeedback('Failed to unload: ' + (error.message || error), 'error');
    });
}

/**
 * Select unit for unloading (shows cargo selection UI)
 * @param {Object} tile - Transport tile
 */
export function unitUnloadSelect(tile) {
    jsonrpc('get_cargo_info', {x: tile.x, y: tile.y}).then(result => {
        if (result?.cargo_units && result.cargo_units.length > 0) {
            showCargoInfo(tile.unit, result);
            
            if (result.cargo_units.length > 1 && window.CargoSelectionUI) {
                const ui = new window.CargoSelectionUI();
                ui.show(result.cargo_units, (selectedIndex) => {
                    // Store selected index for later unload
                    if (window.gameState) {
                        window.gameState.selectedCargoIndex = selectedIndex;
                    }
                    showTransportFeedback(`Selected unit ${selectedIndex + 1} for unloading`, 'info');
                });
            }
        } else {
            showTransportFeedback('No units to unload', 'error');
        }
    }).catch(error => {
        logger.error('Failed to get cargo info:', error);
    });
}

// ===== MODULE INITIALIZATION =====

/**
 * Initialize the game actions module
 */
export function initializeGameActionsModule() {
    logger.info('Initializing game actions module...');
    
    // Set up global references for legacy compatibility
    if (window) {
        // Turn management
        window.armyEndTurn = armyEndTurn;
        window.endGame = endGame;
        
        // Unit selection
        window.unitSelect = unitSelect;
        window.unitSelectWithTransportAndRange = unitSelectWithTransportAndRange;
        
        // Unit movement
        window.unitMove = unitMove;
        
        // Unit combat
        window.unitAttack = unitAttack;
        window.unitAttackWithPreview = unitAttackWithPreview;
        
        // Unit actions
        window.unitWait = unitWait;
        window.unitCapture = unitCapture;
        
        // Unit creation
        window.unitCreate = unitCreate;
        window.airunitCreate = airunitCreate;
        window.seaunitCreate = seaunitCreate;
        
        // Transport operations
        window.unitLoad = unitLoad;
        window.unitUnload = unitUnload;
        window.unitUnloadSelect = unitUnloadSelect;
    }
    
    logger.info('Game actions module initialized');
}

// Initialize on module load
initializeGameActionsModule();