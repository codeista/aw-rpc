/**
 * Animation Integration Module
 * Connects the animation system to game actions
 */

// Wait for animation system to be available
function initializeAnimationIntegration() {
    if (!window.animationSystem) {
        console.error('Animation system not loaded');
        return;
    }
    
    const logger = window.logger || console;
    logger.info('Initializing animation integration...');
    
    // Store original functions
    const originalFunctions = {
        executeMovement: window.executeMovement,
        unitAttack: window.unitAttack,
        unitCapture: window.unitCapture,
        armyEndTurn: window.armyEndTurn,
        showDamagePreview: window.showDamagePreview
    };
    
    // ===== MOVEMENT ANIMATION =====
    if (window.executeMovement) {
        window.executeMovement = function(tile) {
            const board = window.board;
            if (!board || !board.selected) {
                return originalFunctions.executeMovement.call(this, tile);
            }
            
            const fromTile = board.selected;
            const unitSprite = findUnitSprite(fromTile.x, fromTile.y);
            
            if (unitSprite && window.animationSystem.enabled) {
                // Disable input during animation
                setInputEnabled(false);
                
                // Calculate pixel positions
                const TILESIZE = window.TILESIZE || 16;
                const fromX = fromTile.x * TILESIZE + TILESIZE / 2;
                const fromY = (fromTile.y + 1) * TILESIZE + TILESIZE / 2;
                const toX = tile.x * TILESIZE + TILESIZE / 2;
                const toY = (tile.y + 1) * TILESIZE + TILESIZE / 2;
                
                // Start movement animation
                window.animationSystem.animateMovement(
                    unitSprite,
                    fromX, fromY,
                    toX, toY,
                    () => {
                        // Execute actual movement after animation
                        originalFunctions.executeMovement.call(this, tile);
                        setInputEnabled(true);
                    }
                );
            } else {
                // No animation, execute immediately
                originalFunctions.executeMovement.call(this, tile);
            }
        };
    }
    
    // ===== ATTACK ANIMATION =====
    if (window.unitAttack) {
        window.unitAttack = function(targetTile) {
            const board = window.board;
            if (!board || !board.selected) {
                return originalFunctions.unitAttack.call(this, targetTile);
            }
            
            const attackerTile = board.selected;
            
            if (window.animationSystem.enabled) {
                // Get damage preview first
                window.rpc('get_damage_preview', {
                    token: window.token,
                    x: attackerTile.x,
                    y: attackerTile.y,
                    x2: targetTile.x,
                    y2: targetTile.y
                }, (res) => {
                    if (res.error) {
                        return originalFunctions.unitAttack.call(this, targetTile);
                    }
                    
                    // Disable input during animation
                    setInputEnabled(false);
                    
                    // Calculate positions
                    const TILESIZE = window.TILESIZE || 16;
                    const fromX = attackerTile.x * TILESIZE + TILESIZE / 2;
                    const fromY = (attackerTile.y + 1) * TILESIZE + TILESIZE / 2;
                    const toX = targetTile.x * TILESIZE + TILESIZE / 2;
                    const toY = (targetTile.y + 1) * TILESIZE + TILESIZE / 2;
                    
                    // Determine attack type
                    const distance = Math.abs(attackerTile.x - targetTile.x) + Math.abs(attackerTile.y - targetTile.y);
                    const attackType = distance > 1 ? 'indirect' : 'direct';
                    
                    // Start attack animation
                    window.animationSystem.animateAttack(
                        fromX, fromY,
                        toX, toY,
                        attackType,
                        () => {
                            // Show damage numbers
                            if (res.damage_to_target > 0) {
                                window.animationSystem.showDamageNumber(
                                    toX, toY - 20,
                                    Math.round(res.damage_to_target),
                                    '#ff0000'
                                );
                            }
                            
                            // Show counter damage if applicable
                            if (res.damage_to_attacker > 0) {
                                setTimeout(() => {
                                    window.animationSystem.showDamageNumber(
                                        fromX, fromY - 20,
                                        Math.round(res.damage_to_attacker),
                                        '#ff8800'
                                    );
                                }, 300);
                            }
                            
                            // Execute actual attack after animation
                            originalFunctions.unitAttack.call(this, targetTile);
                            setInputEnabled(true);
                        }
                    );
                });
            } else {
                // No animation, execute immediately
                originalFunctions.unitAttack.call(this, targetTile);
            }
        };
    }
    
    // ===== CAPTURE ANIMATION =====
    if (window.unitCapture) {
        window.unitCapture = function(tile) {
            const result = originalFunctions.unitCapture.call(this, tile);
            
            if (window.animationSystem.enabled && tile) {
                // Animate capture progress
                // Estimate progress based on unit HP (each capture reduces by unit HP/10)
                const unit = tile.unit;
                if (unit) {
                    const captureAmount = Math.min(unit.hp, 10);
                    const estimatedProgress = captureAmount * 10; // Rough estimate
                    window.animationSystem.animateCapture(tile, estimatedProgress);
                }
            }
            
            return result;
        };
    }
    
    // ===== TURN TRANSITION ANIMATION =====
    if (window.armyEndTurn) {
        window.armyEndTurn = function() {
            if (window.animationSystem.enabled && window.board) {
                const currentArmy = window.board.current_turn;
                const nextArmy = currentArmy === 'RED' ? 'BLUE' : 'RED';
                
                // Show turn transition
                window.animationSystem.animateTurnTransition(nextArmy, () => {
                    originalFunctions.armyEndTurn.call(this);
                });
            } else {
                originalFunctions.armyEndTurn.call(this);
            }
        };
    }
    
    // ===== SELECTION ANIMATIONS =====
    if (window.unitSelect || window.unitSelectWithTransportAndRange) {
        const selectFunction = window.unitSelectWithTransportAndRange || window.unitSelect;
        const originalSelect = selectFunction;
        
        window.unitSelectWithTransportAndRange = window.unitSelect = function(tile) {
            // Cancel previous selection animation
            if (window._selectionAnimationId) {
                window.animationSystem.cancelAnimation(window._selectionAnimationId);
                window._selectionAnimationId = null;
            }
            
            // Call original function
            const result = originalSelect.call(this, tile);
            
            // Add pulse animation to selected unit
            if (window.animationSystem.enabled && tile && tile.unit) {
                const unitSprite = findUnitSprite(tile.x, tile.y);
                if (unitSprite) {
                    window._selectionAnimationId = window.animationSystem.pulseElement(unitSprite);
                }
            }
            
            return result;
        };
    }
    
    // ===== HELPER FUNCTIONS =====
    
    /**
     * Find unit sprite at given coordinates
     * @param {number} x - Tile X
     * @param {number} y - Tile Y
     * @returns {Object} Two.js sprite object
     */
    function findUnitSprite(x, y) {
        if (!window.two || !window.two.scene) return null;
        
        const TILESIZE = window.TILESIZE || 16;
        const targetX = x * TILESIZE + TILESIZE / 2;
        const targetY = (y + 1) * TILESIZE + TILESIZE / 2;
        
        // Search through Two.js scene children
        for (const child of window.two.scene.children) {
            if (child.translation && 
                Math.abs(child.translation.x - targetX) < 1 &&
                Math.abs(child.translation.y - targetY) < 1) {
                // Check if this is likely a unit sprite
                if (child.width === TILESIZE && child.height === TILESIZE) {
                    return child;
                }
            }
        }
        
        return null;
    }
    
    /**
     * Enable/disable input handling
     * @param {boolean} enabled - Whether input is enabled
     */
    function setInputEnabled(enabled) {
        const canvas = document.getElementById('draw');
        if (canvas) {
            canvas.style.pointerEvents = enabled ? 'auto' : 'none';
        }
        
        // Also disable keyboard shortcuts
        if (window.keyboardShortcuts) {
            window.keyboardShortcuts.setEnabled(enabled);
        }
    }
    
    // ===== ANIMATION SETTINGS UI =====
    
    // Add animation toggle to UI
    const createAnimationToggle = () => {
        const controlPanel = document.querySelector('.control-panel');
        if (!controlPanel) return;
        
        const section = document.createElement('div');
        section.className = 'control-section';
        section.innerHTML = `
            <h3>🎬 Animation Settings</h3>
            <div style="display: flex; align-items: center; gap: 10px; padding: 10px;">
                <label style="flex: 1;">Enable Animations</label>
                <div class="toggle-switch ${window.animationSystem.enabled ? 'active' : ''}" 
                     id="animationToggle" 
                     onclick="toggleAnimations()"
                     style="cursor: pointer;"></div>
            </div>
            <div style="padding: 10px; font-size: 12px; color: #7f8c8d;">
                Animations: movement, attacks, damage numbers, turn transitions
            </div>
        `;
        
        // Insert after game status section
        const gameStatus = controlPanel.querySelector('.control-section');
        if (gameStatus) {
            gameStatus.after(section);
        } else {
            controlPanel.appendChild(section);
        }
    };
    
    // Global toggle function
    window.toggleAnimations = () => {
        const enabled = !window.animationSystem.enabled;
        window.animationSystem.setEnabled(enabled);
        
        const toggle = document.getElementById('animationToggle');
        if (toggle) {
            toggle.classList.toggle('active', enabled);
        }
        
        // Save preference
        localStorage.setItem('animationsEnabled', enabled ? 'true' : 'false');
    };
    
    // Load saved preference
    const savedPref = localStorage.getItem('animationsEnabled');
    if (savedPref === 'false') {
        window.animationSystem.setEnabled(false);
    }
    
    // Create UI when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createAnimationToggle);
    } else {
        createAnimationToggle();
    }
    
    logger.info('Animation integration initialized');
}

// Initialize when both animation system and game are ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Wait a bit for other scripts to load
        setTimeout(initializeAnimationIntegration, 100);
    });
} else {
    setTimeout(initializeAnimationIntegration, 100);
}