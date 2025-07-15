/**
 * Game State Module - Manages all game state including board, selection, and game status
 * Extracted from render.js as part of modularization effort
 */

import { jsonrpc } from './network.js';

// Ensure logger exists
if (typeof window.logger === 'undefined') {
    window.logger = console; // Fallback to console if logger.js isn't loaded
}
const logger = window.logger;

// ===== STATE MANAGEMENT =====

// Private state object
const state = {
    board: null,
    selectedUnit: null,
    movementPhase: false,
    showingAttackTargets: false,
    attackHighlights: [],
    operationInProgress: false,
    previousSelection: null,
    previousTurn: null,
    sceneInitialized: false,
    sceneElements: {
        terrain: {},
        units: {},
        highlights: {}
    }
};

// ===== BOARD STATE MANAGEMENT =====

/**
 * Get the current board state
 * @returns {Object|null} Current board object
 */
export function getBoard() {
    return state.board;
}

/**
 * Set the board state
 * @param {Object} newBoard - New board object
 */
export function setBoard(newBoard) {
    state.board = newBoard;
    // Update global reference for legacy compatibility
    if (window) {
        window.board = newBoard;
    }
}

/**
 * Get a specific tile from the board
 * @param {number} x - X coordinate
 * @param {number} y - Y coordinate
 * @returns {Object|null} Tile object or null if not found
 */
export function getTile(x, y) {
    if (!state.board || !state.board.grid) return null;
    return state.board.grid.find(t => t.x === x && t.y === y);
}

/**
 * Get selected tile
 * @returns {Object|null} Selected tile or null
 */
export function getSelectedTile() {
    return state.board?.selected || null;
}

/**
 * Set selected tile
 * @param {Object|null} tile - Tile to select
 */
export function setSelectedTile(tile) {
    if (state.board) {
        state.board.selected = tile;
    }
}

// ===== GAME STATE MANAGEMENT =====

/**
 * Get the game state object
 * @returns {Object} Game state object
 */
export function getGameState() {
    return {
        selectedUnit: state.selectedUnit,
        movementPhase: state.movementPhase,
        showingAttackTargets: state.showingAttackTargets,
        attackHighlights: state.attackHighlights,
        operationInProgress: state.operationInProgress
    };
}

/**
 * Update game state
 * @param {Object} updates - State updates to apply
 */
export function updateGameState(updates) {
    Object.assign(state, updates);
    
    // Update global gameState for legacy compatibility
    if (window.gameState) {
        Object.assign(window.gameState, updates);
    }
}

/**
 * Reset game state to defaults
 */
export function resetGameState() {
    state.selectedUnit = null;
    state.movementPhase = false;
    state.showingAttackTargets = false;
    state.attackHighlights = [];
    state.operationInProgress = false;
    
    // Update global gameState
    if (window.gameState) {
        window.gameState.selectedUnit = null;
        window.gameState.movementPhase = false;
        window.gameState.showingAttackTargets = false;
        window.gameState.attackHighlights = [];
        window.gameState.operationInProgress = false;
    }
}

// ===== SCENE STATE MANAGEMENT =====

/**
 * Check if scene is initialized
 * @returns {boolean} True if scene is initialized
 */
export function isSceneInitialized() {
    return state.sceneInitialized;
}

/**
 * Set scene initialized state
 * @param {boolean} initialized - Whether scene is initialized
 */
export function setSceneInitialized(initialized) {
    state.sceneInitialized = initialized;
    if (window) {
        window.sceneInitialized = initialized;
    }
}

/**
 * Get scene elements
 * @returns {Object} Scene elements object
 */
export function getSceneElements() {
    return state.sceneElements;
}

/**
 * Force a full scene refresh
 */
export function forceSceneRefresh() {
    state.sceneInitialized = false;
    state.sceneElements = {
        terrain: {},
        units: {},
        highlights: {}
    };
    
    // Update global references
    if (window) {
        window.sceneInitialized = false;
        window.sceneElements = state.sceneElements;
    }
    
    logger.info('Scene refresh forced');
}

// ===== BOARD UPDATE FUNCTIONS =====

/**
 * Main update function - fetches latest board state from server
 * @returns {Promise} Promise that resolves when update is complete
 */
export async function update() {
    // Use operation queue to prevent concurrent updates
    if (window.operationQueue) {
        return window.operationQueue.add(
            () => jsonrpc('game_board', {}),
            {
                id: 'update-board',
                description: 'Updating board',
                priority: 5,
                showLoading: false,
                preventDuplicate: true
            }
        ).then(async function(res) {
            if (res.skipped) {
                logger.debug('Update skipped:', res.reason);
                return;
            }
            
            await handleBoardUpdate(res);
        });
    } else {
        // Fallback without operation queue
        try {
            const res = await jsonrpc('game_board', {});
            await handleBoardUpdate(res);
        } catch (error) {
            logger.error('Board update failed:', error);
        }
    }
}

/**
 * Handle board update from server
 * @param {Object} res - Server response with board data
 */
async function handleBoardUpdate(res) {
    // Preserve current state
    state.previousSelection = state.board?.selected || null;
    state.previousTurn = state.board?.current_turn || null;
    
    // Save movement highlights before updating board
    const savedMovementTiles = [];
    if (state.board?.grid && window.movementHighlights) {
        state.board.grid.forEach(tile => {
            if (tile.can_be_moved_to) {
                savedMovementTiles.push({x: tile.x, y: tile.y});
            }
        });
    }
    
    // Update board data
    setBoard(res);
    
    // Restore movement highlights after update
    if (savedMovementTiles.length > 0 && state.board?.grid) {
        savedMovementTiles.forEach(saved => {
            const tile = state.board.grid.find(t => t.x === saved.x && t.y === saved.y);
            if (tile) {
                tile.can_be_moved_to = true;
            }
        });
    }
    
    // Update game status display
    updateGameStatus(res);
    
    // Handle turn changes
    if (state.previousTurn !== null && state.previousTurn !== res.current_turn) {
        logger.info(`Turn changed from ${state.previousTurn} to ${res.current_turn}`);
        
        // Clear highlights on turn change
        if (window.clearAllHighlights) {
            window.clearAllHighlights();
        }
        
        // Reset game state on turn change
        resetGameState();
        
        // Clear global selection
        setSelectedTile(null);
    }
    
    // Initialize scene if needed
    if (!state.sceneInitialized && window.initializeScene) {
        window.initializeScene();
    } else if (window.updateScene) {
        // Update only changed elements
        await window.updateScene();
    }
    
    // Render the scene
    if (window.two) {
        window.two.update();
    }
    
    // Update JSON display if visible
    if (window.updateJsonDisplay) {
        window.updateJsonDisplay(res);
    }
}

/**
 * Update game status display elements
 * @param {Object} gameData - Game data from server
 */
export function updateGameStatus(gameData) {
    if (!gameData) return;
    
    // Update current turn display
    const currentTurnElement = document.getElementById('current-turn');
    if (currentTurnElement) {
        currentTurnElement.textContent = gameData.current_turn || 'N/A';
        currentTurnElement.className = 'army-' + (gameData.current_turn ? gameData.current_turn.toLowerCase() : 'neutral');
    }
    
    // Update game status
    const gameStatusElement = document.getElementById('game-status');
    if (gameStatusElement) {
        if (gameData.game_active === false) {
            gameStatusElement.textContent = 'Game Over';
            gameStatusElement.className = 'status-ended';
            
            // Show winner if available
            if (gameData.winner) {
                const winnerElement = document.getElementById('winner-display');
                if (winnerElement) {
                    winnerElement.textContent = `Winner: ${gameData.winner}`;
                    winnerElement.style.display = 'block';
                }
            }
        } else {
            gameStatusElement.textContent = 'Active';
            gameStatusElement.className = 'status-active';
        }
    }
    
    // Update army resources if available
    if (gameData.army_resources) {
        updateArmyResources(gameData.army_resources);
    }
}

/**
 * Update army resources display
 * @param {Object} resources - Army resources data
 */
function updateArmyResources(resources) {
    Object.entries(resources).forEach(([army, data]) => {
        const fundsElement = document.getElementById(`${army.toLowerCase()}-funds`);
        if (fundsElement && data.funds !== undefined) {
            fundsElement.textContent = data.funds.toLocaleString();
        }
    });
}

// ===== SELECTION STATE =====

/**
 * Check if a unit is currently selected
 * @returns {boolean} True if a unit is selected
 */
export function hasSelectedUnit() {
    return state.selectedUnit !== null || state.board?.selected !== null;
}

/**
 * Get the currently selected unit
 * @returns {Object|null} Selected unit or null
 */
export function getSelectedUnit() {
    return state.selectedUnit || state.board?.selected || null;
}

/**
 * Set the selected unit
 * @param {Object|null} unit - Unit to select
 */
export function setSelectedUnit(unit) {
    state.selectedUnit = unit;
    updateGameState({ selectedUnit: unit });
}

// ===== OPERATION STATE =====

/**
 * Check if an operation is in progress
 * @returns {boolean} True if operation in progress
 */
export function isOperationInProgress() {
    return state.operationInProgress;
}

/**
 * Set operation in progress state
 * @param {boolean} inProgress - Whether operation is in progress
 */
export function setOperationInProgress(inProgress) {
    state.operationInProgress = inProgress;
    updateGameState({ operationInProgress: inProgress });
}

// ===== PERSISTENCE =====

/**
 * Save current game state to localStorage
 */
export function saveGameState() {
    try {
        const stateToSave = {
            board: state.board,
            selectedUnit: state.selectedUnit,
            timestamp: Date.now()
        };
        localStorage.setItem('awRpcGameState', JSON.stringify(stateToSave));
        logger.debug('Game state saved');
    } catch (error) {
        logger.error('Failed to save game state:', error);
    }
}

/**
 * Load game state from localStorage
 * @returns {boolean} True if state was loaded
 */
export function loadGameState() {
    try {
        const savedState = localStorage.getItem('awRpcGameState');
        if (savedState) {
            const parsed = JSON.parse(savedState);
            
            // Check if saved state is recent (within 5 minutes)
            if (Date.now() - parsed.timestamp < 5 * 60 * 1000) {
                setBoard(parsed.board);
                setSelectedUnit(parsed.selectedUnit);
                logger.debug('Game state loaded from storage');
                return true;
            }
        }
    } catch (error) {
        logger.error('Failed to load game state:', error);
    }
    return false;
}

/**
 * Clear saved game state
 */
export function clearSavedGameState() {
    try {
        localStorage.removeItem('awRpcGameState');
        logger.debug('Saved game state cleared');
    } catch (error) {
        logger.error('Failed to clear saved game state:', error);
    }
}

// ===== INITIALIZATION =====

/**
 * Initialize the game state module
 */
export function initializeGameStateModule() {
    logger.info('Initializing game state module...');
    
    // Set up global references for legacy compatibility
    if (window) {
        // Expose key functions globally
        window.getBoard = getBoard;
        window.setBoard = setBoard;
        window.getGameState = getGameState;
        window.updateGameState = updateGameState;
        window.forceSceneRefresh = forceSceneRefresh;
        window.update = update;
        window.updateGameStatus = updateGameStatus;
        
        // Initialize board reference
        window.board = state.board;
    }
    
    logger.info('Game state module initialized');
}

// Initialize on module load
initializeGameStateModule();