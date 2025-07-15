/**
 * Combat System Module - Handles combat calculations, targeting, and attack execution
 * Extracted from render.js as part of modularization effort
 */

import { jsonrpc } from './network.js';
import { getBoard, getTile, update } from './gameState.js';
import { renderAttackHighlights } from './renderEngine.js';

// Ensure logger exists
if (typeof window.logger === 'undefined') {
    window.logger = console; // Fallback to console if logger.js isn't loaded
}
const logger = window.logger;

// ===== COMBAT STATE =====
const combatState = {
    attackHighlights: [],
    attackHighlightGroup: null,
    showingAttackTargets: false
};

// Make attackHighlights globally accessible through gameState
if (window.gameState) {
    window.gameState.attackHighlights = combatState.attackHighlights;
    window.gameState.showingAttackTargets = combatState.showingAttackTargets;
}

// ===== ATTACK TARGETING =====

/**
 * Show attack targets for a unit
 * @param {number} unitX - Unit X coordinate
 * @param {number} unitY - Unit Y coordinate
 */
export function showAttackTargets(unitX, unitY) {
    logger.debug(`⚔️ Showing attack targets for unit at (${unitX}, ${unitY})`);
    
    const board = getBoard();
    if (!board?.grid) return;
    
    // Get the unit to check if it's indirect and has moved
    const tile = board.grid.find(t => t.x === unitX && t.y === unitY);
    const unit = tile?.unit;
    
    // CHECK: If indirect unit has moved, don't show attack targets
    if (unit && isIndirectUnit(unit) && hasMoved(unit)) {
        logger.debug('Indirect unit has moved - no attack targets');
        clearAttackHighlights();
        return;
    }
    
    jsonrpc('get_attack_targets', {
        unit_x: unitX,
        unit_y: unitY
    }).then(result => {
        if (result?.success && result.targets?.length > 0) {
            logger.debug(`Found ${result.targets.length} attack targets`);
            
            // Clear existing attack highlights
            clearAttackHighlights();
            
            // Add new attack highlights
            result.targets.forEach(target => {
                highlightAttackTile(target.x, target.y);
            });
            
            // Update state
            combatState.showingAttackTargets = true;
            if (window.gameState) {
                window.gameState.showingAttackTargets = true;
            }
            
            // Render the highlights
            renderAttackHighlights();
        } else {
            logger.debug('No attack targets found');
            clearAttackHighlights();
        }
    }).catch(error => {
        logger.error('Failed to get attack targets:', error);
        clearAttackHighlights();
    });
}

/**
 * Show attack targets after unit has moved
 * @param {number} unitX - Unit X coordinate  
 * @param {number} unitY - Unit Y coordinate
 */
export function showAttackTargetsAfterMove(unitX, unitY) {
    logger.debug(`⚔️ Checking for attack targets after move at (${unitX}, ${unitY})`);
    
    jsonrpc('get_attack_targets', {
        unit_x: unitX,
        unit_y: unitY
    }).then(result => {
        if (result?.success && result.targets?.length > 0) {
            logger.debug(`Found ${result.targets.length} attack targets after move`);
            
            combatState.showingAttackTargets = true;
            if (window.gameState) {
                window.gameState.showingAttackTargets = true;
            }
            
            clearAttackHighlights();
            
            result.targets.forEach(target => {
                highlightAttackTile(target.x, target.y);
            });
            
            renderAttackHighlights();
        } else {
            logger.debug('No attack targets after move - unit is done');
            // No attack targets - unit is done
            if (window.endUnitTurn) {
                window.endUnitTurn();
            }
        }
    }).catch(error => {
        logger.error('Failed to get attack targets:', error);
        if (window.endUnitTurn) {
            window.endUnitTurn();
        }
    });
}

/**
 * Highlight attack range for a unit
 * @param {number} unitX - Unit X coordinate
 * @param {number} unitY - Unit Y coordinate
 */
export function highlightAttackRange(unitX, unitY) {
    jsonrpc('get_attack_targets', {
        unit_x: unitX,
        unit_y: unitY
    }).then(result => {
        if (result?.success) {
            if (window.clearRangeHighlights) {
                window.clearRangeHighlights();
            }
            
            result.targets?.forEach(target => {
                if (window.highlightTile) {
                    window.highlightTile(target.x, target.y, 'attack-range');
                }
            });
        }
    }).catch(error => {
        logger.error('Failed to get attack targets:', error);
    });
}

// ===== COMBAT PREVIEW =====

/**
 * Show combat preview before attacking
 * @param {number} attackerX - Attacker X coordinate
 * @param {number} attackerY - Attacker Y coordinate
 * @param {number} defenderX - Defender X coordinate
 * @param {number} defenderY - Defender Y coordinate
 */
export async function showCombatPreview(attackerX, attackerY, defenderX, defenderY) {
    try {
        const result = await jsonrpc('combat_preview', {
            attacker_x: attackerX,
            attacker_y: attackerY,
            defender_x: defenderX,
            defender_y: defenderY
        });
        
        if (result.success) {
            showCombatPreviewModal(result, attackerX, attackerY, defenderX, defenderY);
        } else {
            alert('Cannot preview combat: ' + result.error);
            // Fallback to regular attack
            unitAttackRegular(defenderX, defenderY);
        }
    } catch (error) {
        logger.error('Combat preview error:', error);
        // Fallback to regular attack
        unitAttackRegular(defenderX, defenderY);
    }
}

/**
 * Show combat preview modal
 * @param {Object} previewData - Combat preview data
 * @param {number} attackerX - Attacker X coordinate
 * @param {number} attackerY - Attacker Y coordinate
 * @param {number} defenderX - Defender X coordinate
 * @param {number} defenderY - Defender Y coordinate
 */
function showCombatPreviewModal(previewData, attackerX, attackerY, defenderX, defenderY) {
    const modalContent = `
        <span class="close">&times;</span>
        <h3>Combat Preview</h3>
        <div style="display: flex; justify-content: space-between; margin: 15px 0;">
            <div style="flex: 1; margin: 0 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px;">
                <h4>Your Attack</h4>
                <p><strong>Damage:</strong> ${previewData.attacker_damage}%</p>
                <p><strong>Range:</strong> ${previewData.damage_range || 'N/A'}</p>
                ${previewData.terrain_bonus > 0 ? `<p><em>Enemy has +${previewData.terrain_bonus} terrain defense</em></p>` : ''}
                ${previewData.ammo_warning ? '<p style="color: red;"><em>⚠ Low ammo!</em></p>' : ''}
            </div>
            <div style="flex: 1; margin: 0 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px;">
                <h4>Counter Attack</h4>
                ${previewData.can_counter ? 
                    `<p><strong>Damage:</strong> ${previewData.counter_damage}%</p>
                     <p><strong>Range:</strong> ${previewData.counter_range || 'N/A'}</p>` : 
                    '<p><em>No counter attack possible</em></p>'}
            </div>
        </div>
        <div style="text-align: center; margin-top: 20px;">
            <button onclick="confirmCombat(${attackerX}, ${attackerY}, ${defenderX}, ${defenderY})" 
                    style="margin: 0 10px; padding: 10px 20px; font-size: 16px; background: #d9534f; color: white; border: none; border-radius: 5px; cursor: pointer;">
                Attack!
            </button>
            <button onclick="cancelCombat()" 
                    style="margin: 0 10px; padding: 10px 20px; font-size: 16px; background: #6c757d; color: white; border: none; border-radius: 5px; cursor: pointer;">
                Cancel
            </button>
        </div>
    `;
    
    // Use existing modal system
    const modal = document.getElementById('modalcreate');
    if (!modal) {
        logger.error('Modal element not found');
        return;
    }
    
    const modalContentDiv = modal.querySelector('.modal-content');
    if (modalContentDiv) {
        // Store original content
        modalContentDiv.dataset.originalContent = modalContentDiv.innerHTML;
        modalContentDiv.innerHTML = modalContent;
    }
    
    modal.style.display = 'block';
    
    // Add close button functionality
    const closeBtn = modal.querySelector('.close');
    if (closeBtn) {
        closeBtn.onclick = cancelCombat;
    }
    
    // Store combat preview functions globally for onclick handlers
    window.confirmCombat = confirmCombat;
    window.cancelCombat = cancelCombat;
}

/**
 * Confirm and execute combat
 * @param {number} attackerX - Attacker X coordinate
 * @param {number} attackerY - Attacker Y coordinate
 * @param {number} defenderX - Defender X coordinate
 * @param {number} defenderY - Defender Y coordinate
 */
function confirmCombat(attackerX, attackerY, defenderX, defenderY) {
    // Close modal
    cancelCombat();
    
    // Execute enhanced attack
    enhancedAttack(attackerX, attackerY, defenderX, defenderY).then(() => {
        logger.info('✅ Enhanced attack completed');
        // End unit turn after attack
        if (window.endUnitTurn) {
            window.endUnitTurn();
        }
    }).catch(error => {
        logger.error('❌ Enhanced attack failed:', error);
        if (window.endUnitTurn) {
            window.endUnitTurn();
        }
    });
}

/**
 * Cancel combat preview
 */
function cancelCombat() {
    const modal = document.getElementById('modalcreate');
    if (modal) {
        modal.style.display = 'none';
        
        // Restore original content if stored
        const modalContentDiv = modal.querySelector('.modal-content');
        if (modalContentDiv?.dataset.originalContent) {
            modalContentDiv.innerHTML = modalContentDiv.dataset.originalContent;
            delete modalContentDiv.dataset.originalContent;
        }
    }
}

// ===== ATTACK EXECUTION =====

/**
 * Execute attack with enhanced features
 * @param {number} attackerX - Attacker X coordinate
 * @param {number} attackerY - Attacker Y coordinate
 * @param {number} defenderX - Defender X coordinate
 * @param {number} defenderY - Defender Y coordinate
 */
async function enhancedAttack(attackerX, attackerY, defenderX, defenderY) {
    try {
        const result = await jsonrpc('unit_attack_enhanced', {
            attacker_x: attackerX,
            attacker_y: attackerY,
            defender_x: defenderX,
            defender_y: defenderY
        });
        
        if (result.success) {
            logger.info('⚔️ Enhanced attack successful:', result);
            
            // Clear all highlights
            if (window.clearAllHighlights) {
                window.clearAllHighlights();
            }
            
            // Update board
            update();
        } else {
            throw new Error(result.error || 'Attack failed');
        }
    } catch (error) {
        logger.error('Enhanced attack failed, falling back to regular attack:', error);
        // Fallback to regular attack
        unitAttackRegular(defenderX, defenderY);
    }
}

/**
 * Execute regular attack (fallback)
 * @param {number} defenderX - Defender X coordinate
 * @param {number} defenderY - Defender Y coordinate
 */
function unitAttackRegular(defenderX, defenderY) {
    const board = getBoard();
    const selected = board?.selected;
    
    if (!selected) {
        logger.error('No unit selected for attack');
        return;
    }
    
    jsonrpc('unit_attack', {
        x: selected.x,
        y: selected.y,
        x2: defenderX,
        y2: defenderY
    }).then(() => {
        logger.info('⚔️ Regular attack completed');
        update();
    }).catch(error => {
        logger.error('Regular attack failed:', error);
    });
}

/**
 * Execute attack from selected unit
 * @param {Object} targetTile - Target tile to attack
 */
export function executeAttack(targetTile) {
    logger.debug('⚔️ Executing attack on target tile:', targetTile);
    
    const board = getBoard();
    if (!board?.selected?.unit) {
        logger.error('❌ No unit selected for attack');
        return;
    }
    
    const attacker = board.selected;
    
    jsonrpc('unit_attack', {
        x: attacker.x,
        y: attacker.y,
        x2: targetTile.x,
        y2: targetTile.y
    }).then(result => {
        logger.info('⚔️ Attack executed:', result);
        
        // Update unit states after attack
        if (board.grid) {
            const attackerTile = board.grid.find(t => t.x === attacker.x && t.y === attacker.y);
            if (attackerTile?.unit) {
                logger.debug('Marking attacker as unavailable');
                attackerTile.unit.can_move = false;
                attackerTile.unit.can_attack = false;
                attackerTile.unit.can_capture = false;
            }
        }
        
        // Clear highlights
        clearAttackHighlights();
        if (window.clearMovementHighlights) {
            window.clearMovementHighlights();
        }
        
        // Update board
        update();
        
        // End unit turn
        if (window.endUnitTurn) {
            window.endUnitTurn();
        }
    }).catch(error => {
        logger.error('Attack failed:', error);
    });
}

/**
 * Attack with preview
 * @param {Object} targetTile - Target tile to attack
 */
export function unitAttackWithPreview(targetTile) {
    const board = getBoard();
    const source = board?.selected;
    
    if (!source) {
        logger.error('No unit selected for attack');
        return;
    }
    
    // Show combat preview
    showCombatPreview(source.x, source.y, targetTile.x, targetTile.y);
}

// ===== HIGHLIGHT MANAGEMENT =====

/**
 * Highlight an attack tile
 * @param {number} x - Tile X coordinate
 * @param {number} y - Tile Y coordinate
 */
function highlightAttackTile(x, y) {
    combatState.attackHighlights.push({
        x: x,
        y: y,
        type: 'attack-target'
    });
    
    // Update global reference
    if (window.gameState) {
        window.gameState.attackHighlights = combatState.attackHighlights;
    }
}

/**
 * Clear attack highlights
 */
export function clearAttackHighlights() {
    // Clear visual highlights
    if (window.attackHighlightGroup && window.two) {
        window.two.remove(window.attackHighlightGroup);
        window.attackHighlightGroup = null;
    }
    
    // Clear data
    combatState.attackHighlights = [];
    combatState.showingAttackTargets = false;
    
    // Update global references
    if (window.gameState) {
        window.gameState.attackHighlights = [];
        window.gameState.showingAttackTargets = false;
    }
}

/**
 * Check if a tile is attack highlighted
 * @param {number} x - Tile X coordinate
 * @param {number} y - Tile Y coordinate
 * @returns {boolean} True if tile is attack highlighted
 */
export function isAttackHighlighted(x, y) {
    return combatState.attackHighlights.some(h => h.x === x && h.y === y);
}

// ===== UTILITY FUNCTIONS =====

/**
 * Check if unit is an indirect attacker
 * @param {Object} unit - Unit object
 * @returns {boolean} True if indirect unit
 */
function isIndirectUnit(unit) {
    const indirectTypes = ['ARTILLERY', 'ROCKET', 'MISSILE', 'BATTLESHIP', 'CARRIER'];
    const unitType = unit.type?.name || unit.type || '';
    return indirectTypes.includes(unitType);
}

/**
 * Check if unit has already moved
 * @param {Object} unit - Unit object
 * @returns {boolean} True if unit has moved
 */
function hasMoved(unit) {
    // If unit can't move, it has already moved
    return !unit.can_move;
}

/**
 * Perform Advance Wars style attack
 * @param {Object} selectedUnit - Selected unit
 * @param {Object} targetTile - Target tile
 * @returns {boolean} True if attack was handled
 */
export function advanceWarsAttack(selectedUnit, targetTile) {
    if (!window.gameState?.selectedUnit || !combatState.showingAttackTargets) {
        return false;
    }
    
    logger.debug('⚔️ Advance Wars attack:', selectedUnit, targetTile);
    
    // Get actual source coordinates
    const source = {
        x: window.gameState.selectedUnit.x || selectedUnit.x,
        y: window.gameState.selectedUnit.y || selectedUnit.y
    };
    
    // Use preview attack if available
    if (window.unitAttackWithPreview) {
        showCombatPreview(source.x, source.y, targetTile.x, targetTile.y);
    } else {
        // Direct attack
        jsonrpc('unit_attack', {
            x: source.x,
            y: source.y,
            x2: targetTile.x,
            y2: targetTile.y
        }).then(result => {
            logger.info('⚔️ Attack result:', result);
            
            // Update unit flags
            const board = getBoard();
            if (board?.grid) {
                const attackerTile = board.grid.find(t => t.x === source.x && t.y === source.y);
                if (attackerTile?.unit) {
                    logger.info('📝 Manually updating attacker flags to unavailable');
                    attackerTile.unit.can_move = false;
                    attackerTile.unit.can_attack = false;
                    attackerTile.unit.can_capture = false;
                }
            }
            
            // Clear state
            clearAttackHighlights();
            if (window.gameState) {
                window.gameState.selectedUnit = null;
                window.gameState.movementPhase = false;
            }
            
            // Update board
            update();
        }).catch(error => {
            logger.error('❌ Attack failed:', error);
        });
    }
    
    return true;
}

// ===== MODULE INITIALIZATION =====

/**
 * Initialize the combat system module
 */
export function initializeCombatSystemModule() {
    logger.info('Initializing combat system module...');
    
    // Set up global references for legacy compatibility
    if (window) {
        // Attack targeting
        window.showAttackTargets = showAttackTargets;
        window.showAttackTargetsAfterMove = showAttackTargetsAfterMove;
        window.highlightAttackRange = highlightAttackRange;
        
        // Combat preview
        window.showCombatPreview = showCombatPreview;
        window.unitAttackWithPreview = unitAttackWithPreview;
        
        // Attack execution
        window.executeAttack = executeAttack;
        window.advanceWarsAttack = advanceWarsAttack;
        
        // Highlight management
        window.clearAttackHighlights = clearAttackHighlights;
        window.isAttackHighlighted = isAttackHighlighted;
        
        // Render function
        window.renderAttackHighlights = renderAttackHighlights;
    }
    
    logger.info('Combat system module initialized');
}

// Initialize on module load
initializeCombatSystemModule();