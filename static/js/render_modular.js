/**
 * Modular Render System - Main entry point
 * This is the cleaned up version that uses all extracted modules
 */

// Import all modules
import './logger.js';
import './errorHandler.js';
import './cargo-selection.js';
import moduleLoader from './modules/moduleLoader.js';

// Ensure logger exists
if (typeof window.logger === 'undefined') {
    window.logger = console;
}
const logger = window.logger;

// ===== INITIALIZATION =====

/**
 * Initialize the modular render system
 */
async function initializeModularRender() {
    logger.info('🚀 Initializing modular render system...');
    
    try {
        // Load all modules
        await moduleLoader.loadAllModules();
        
        // Get essential modules
        const core = moduleLoader.getModule('core');
        const network = moduleLoader.getModule('network');
        const gameState = moduleLoader.getModule('gameState');
        const renderEngine = moduleLoader.getModule('renderEngine');
        
        // Initialize Two.js renderer
        await initializeTwoJS();
        
        // Start the main update cycle
        if (gameState?.update) {
            await gameState.update();
        }
        
        logger.info('✅ Modular render system initialized successfully');
        
    } catch (error) {
        logger.error('❌ Failed to initialize modular render system:', error);
        
        // Fallback to legacy render.js
        logger.warn('🔄 Falling back to legacy render system...');
        const script = document.createElement('script');
        script.src = '/static/js/render.js';
        document.head.appendChild(script);
    }
}

/**
 * Initialize Two.js renderer
 */
async function initializeTwoJS() {
    const draw = document.getElementById('draw');
    if (!draw) {
        throw new Error('Draw element not found');
    }
    
    const board = window.board;
    if (!board) {
        throw new Error('Board not initialized');
    }
    
    const TILESIZE = window.TILESIZE || 16;
    const width = board.width * TILESIZE;
    const height = board.height * TILESIZE;
    const extraHeight = TILESIZE;
    
    // Initialize Two.js
    const params = {
        type: Two.Types.canvas,
        width: width,
        height: height + extraHeight,
        autostart: false
    };
    
    window.two = new Two(params).appendTo(draw);
    window.two.scene.translation.set(0, extraHeight);
    
    logger.info('✅ Two.js initialized');
    
    // Set up canvas event handlers
    const canvas = draw.querySelector('canvas');
    if (canvas) {
        const inputHandler = moduleLoader.getModule('inputHandler');
        if (inputHandler?.initializeInputHandlers) {
            inputHandler.initializeInputHandlers();
        }
        
        // Add mobile support if needed
        const mobileSupport = moduleLoader.getModule('mobileSupport');
        if (mobileSupport?.isTouchDevice && mobileSupport.isTouchDevice()) {
            if (mobileSupport.addTouchSupport) {
                mobileSupport.addTouchSupport(canvas);
            }
        }
    }
}

// ===== LEGACY COMPATIBILITY FUNCTIONS =====

// These functions provide backward compatibility with the original render.js
// They delegate to the appropriate modules

window.update = function() {
    const gameState = moduleLoader.getModule('gameState');
    if (gameState?.update) {
        return gameState.update();
    }
};

window.rerender = function() {
    const renderEngine = moduleLoader.getModule('renderEngine');
    if (renderEngine?.rerender) {
        return renderEngine.rerender();
    }
};

window.unitSelect = function(tile) {
    const gameActions = moduleLoader.getModule('gameActions');
    if (gameActions?.unitSelect) {
        return gameActions.unitSelect(tile);
    }
};

window.unitMove = function(tile) {
    const gameActions = moduleLoader.getModule('gameActions');
    if (gameActions?.unitMove) {
        return gameActions.unitMove(tile);
    }
};

window.unitAttack = function(tile) {
    const gameActions = moduleLoader.getModule('gameActions');
    if (gameActions?.unitAttack) {
        return gameActions.unitAttack(tile);
    }
};

window.unitWait = function(tile) {
    const gameActions = moduleLoader.getModule('gameActions');
    if (gameActions?.unitWait) {
        return gameActions.unitWait(tile);
    }
};

window.unitCapture = function(tile) {
    const gameActions = moduleLoader.getModule('gameActions');
    if (gameActions?.unitCapture) {
        return gameActions.unitCapture(tile);
    }
};

window.armyEndTurn = function() {
    const gameActions = moduleLoader.getModule('gameActions');
    if (gameActions?.armyEndTurn) {
        return gameActions.armyEndTurn();
    }
};

window.endGame = function() {
    const gameActions = moduleLoader.getModule('gameActions');
    if (gameActions?.endGame) {
        return gameActions.endGame();
    }
};

// ===== CONTEXT MENU SYSTEM =====

window.showUnitContextMenu = function(x, y, selectedUnit, targetUnit) {
    const uiSystems = moduleLoader.getModule('uiSystems');
    if (uiSystems?.showUnitContextMenu) {
        return uiSystems.showUnitContextMenu(x, y, selectedUnit, targetUnit);
    }
};

window.hideContextMenu = function() {
    const uiSystems = moduleLoader.getModule('uiSystems');
    if (uiSystems?.hideUnitContextMenu) {
        return uiSystems.hideUnitContextMenu();
    }
};

window.contextMenuAction = function(action) {
    logger.debug('Context menu action:', action);
    
    if (!window.contextMenuData) {
        logger.error('No context menu data available');
        return;
    }
    
    const { selectedUnit, targetUnit } = window.contextMenuData;
    
    if (action === 'repair') {
        // Perform Black Boat repair
        logger.debug('Attempting repair:', selectedUnit, 'repairing', targetUnit);
        
        const network = moduleLoader.getModule('network');
        const core = moduleLoader.getModule('core');
        
        if (network?.jsonrpc && core?.getGameToken) {
            const repairParams = {
                blackboat_x: selectedUnit.x,
                blackboat_y: selectedUnit.y,
                target_x: targetUnit.x,
                target_y: targetUnit.y,
                hp_to_repair: 2  // Repair 2 HP (max for Black Boat)
            };
            
            network.jsonrpc('repair_unit', repairParams).then(result => {
                const uiSystems = moduleLoader.getModule('uiSystems');
                if (result.error) {
                    if (uiSystems?.showTransportFeedback) {
                        uiSystems.showTransportFeedback('Repair failed: ' + result.error, 'error');
                    }
                } else {
                    const message = `Repaired ${result.hp_repaired || 2} HP for ${result.repair_cost || 0} funds`;
                    if (uiSystems?.showTransportFeedback) {
                        uiSystems.showTransportFeedback(message, 'success');
                    }
                    // Refresh the board
                    window.update();
                }
            });
        }
    }
    
    window.hideContextMenu();
};

// ===== NOTIFICATION SYSTEM =====

window.showNotification = function(message, type = 'info') {
    const uiSystems = moduleLoader.getModule('uiSystems');
    if (uiSystems?.showTransportFeedback) {
        return uiSystems.showTransportFeedback(message, type);
    }
};

// ===== DOM READY INITIALIZATION =====

/**
 * Initialize when DOM is ready
 */
function initializeWhenReady() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeModularRender);
    } else {
        initializeModularRender();
    }
}

// Start initialization
initializeWhenReady();

// Export for debugging
window.moduleLoader = moduleLoader;