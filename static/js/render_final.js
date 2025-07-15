/**
 * Final Render System - Complete modular implementation
 * This file replaces render.js with the fully modular system
 * All functionality has been extracted into modules
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
 * Initialize the complete modular render system
 */
async function initializeModularRender() {
    logger.info('🚀 Initializing complete modular render system...');
    
    try {
        // Load all modules
        await moduleLoader.loadAllModules();
        
        // Get essential modules
        const core = moduleLoader.getModule('core');
        const network = moduleLoader.getModule('network');
        const gameState = moduleLoader.getModule('gameState');
        const renderEngine = moduleLoader.getModule('renderEngine');
        const inputHandler = moduleLoader.getModule('inputHandler');
        const uiSystems = moduleLoader.getModule('uiSystems');
        
        // Initialize global state
        const globals = core.initializeGlobals();
        window.token = globals.token;
        window.board = globals.board;
        window.two = globals.two;
        window.transportHighlightGroup = globals.transportHighlightGroup;
        
        // Initialize game state
        core.initializeGameState();
        
        // Initialize network
        if (globals.token) {
            network.initializeSocket(globals.token);
        }
        
        // Initialize Two.js renderer
        await initializeTwoJS();
        
        // Initialize controls
        initializeControls();
        
        // Initialize input handlers
        inputHandler.initializeInputHandlers();
        
        // Start the main update cycle
        await gameState.update();
        
        logger.info('✅ Complete modular render system initialized successfully');
        
    } catch (error) {
        logger.error('❌ Failed to initialize modular render system:', error);
        throw error;
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
    
    // Wait for initial board data
    const gameState = moduleLoader.getModule('gameState');
    await gameState.update();
    
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
    
    // Render the board
    const renderEngine = moduleLoader.getModule('renderEngine');
    await renderEngine.rerender();
}

/**
 * Initialize controls
 */
function initializeControls() {
    const gameActions = moduleLoader.getModule('gameActions');
    const gameState = moduleLoader.getModule('gameState');
    const uiSystems = moduleLoader.getModule('uiSystems');
    
    // End turn button
    const buttonendturn = document.getElementsByClassName('buttonendturn');
    if (buttonendturn && buttonendturn.length > 0) {
        Array.from(buttonendturn).forEach(btn => {
            btn.onclick = window.debounce(gameActions.armyEndTurn, 500);
        });
    }
    
    // End game button
    const buttonendgame = document.getElementsByClassName('buttonendgame');
    if (buttonendgame && buttonendgame.length > 0) {
        Array.from(buttonendgame).forEach(btn => {
            btn.onclick = gameActions.endGame;
        });
    }
    
    // Rerender button
    const buttonrerender = document.getElementsByClassName('buttonrerender');
    if (buttonrerender && buttonrerender.length > 0) {
        Array.from(buttonrerender).forEach(btn => {
            btn.onclick = window.debounce(() => {
                const renderEngine = moduleLoader.getModule('renderEngine');
                renderEngine.rerender();
            }, 300);
        });
    }
    
    // Show map toggle
    const inputshowmap = document.getElementById('inputshowmap');
    if (inputshowmap) {
        inputshowmap.onchange = () => {
            const renderEngine = moduleLoader.getModule('renderEngine');
            renderEngine.rerender();
        };
    }
    
    // Chat button
    const buttonchat = document.getElementById('buttonchat');
    if (buttonchat) {
        buttonchat.onclick = uiSystems.chat;
    }
    
    // Chat input
    const inputchat = document.getElementById('inputchat');
    if (inputchat) {
        inputchat.onkeypress = uiSystems.chat;
    }
    
    // Show chat toggle
    const inputshowchat = document.getElementById('inputshowchat');
    if (inputshowchat) {
        inputshowchat.onchange = uiSystems.showChat;
    }
    
    // Show JSON toggle
    const inputshowjson = document.getElementById('inputshowjson');
    if (inputshowjson) {
        inputshowjson.onchange = uiSystems.showJson;
    }
}

// ===== LEGACY COMPATIBILITY LAYER =====

// These functions provide backward compatibility
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

// Context menu functions
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

// Notification function
window.showNotification = function(message, type = 'info') {
    const uiSystems = moduleLoader.getModule('uiSystems');
    if (uiSystems?.showTransportFeedback) {
        return uiSystems.showTransportFeedback(message, type);
    }
};

// ===== DEBOUNCE UTILITY =====
window.debounce = function(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
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