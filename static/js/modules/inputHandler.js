/**
 * Input Handler Module - Manages all user input including clicks, keyboard, and touch
 * Extracted from render.js as part of modularization effort
 */

import { getBoard, getTile, getSelectedTile, setSelectedTile, getGameState } from './gameState.js';
import { showTransportFeedback, hideUnitContextMenu } from './uiSystems.js';

// Ensure logger exists
if (typeof window.logger === 'undefined') {
    window.logger = console; // Fallback to console if logger.js isn't loaded
}
const logger = window.logger;

// ===== INPUT STATE =====
const inputState = {
    longPressTimer: null,
    clickThrottleTimer: null,
    lastClickTime: 0,
    doubleClickThreshold: 300,
    contextMenuOpen: false,
    isDragging: false,
    dragStartPos: null
};

// ===== COORDINATE HELPERS =====

/**
 * Get tile at pixel coordinates
 * @param {number} px - Pixel X coordinate
 * @param {number} py - Pixel Y coordinate
 * @returns {Object|null} Tile object or null
 */
export function tileAt(px, py) {
    const board = getBoard();
    if (!board) return null;
    
    const TILESIZE = window.TILESIZE || 16;
    
    // Account for the extra height offset at the top
    const adjustedY = py - TILESIZE;
    const tileX = Math.floor(px / TILESIZE);
    const tileY = Math.floor(adjustedY / TILESIZE);
    
    // Bounds checking
    if (tileY < 0 || tileY >= board.height || tileX < 0 || tileX >= board.width) {
        return null;
    }
    
    // Find tile in board grid
    return board.grid[tileX + tileY * board.width];
}

// ===== MOUSE HANDLERS =====

/**
 * Handle mouse move events
 * @param {MouseEvent} ev - Mouse event
 */
export function canvasMove(ev) {
    const tile = tileAt(ev.offsetX, ev.offsetY);
    const board = getBoard();
    const draw = document.getElementById('draw');
    
    if (!draw) return;
    
    // Update cursor based on tile state
    draw.style.cursor = 'default';
    
    if (tile) {
        if (tile.can_be_moved_to) {
            draw.style.cursor = 'pointer';
        } else if (tile.can_be_attacked) {
            draw.style.cursor = 'crosshair';
        } else if (tile.unit && tile.unit.army === board?.current_turn) {
            draw.style.cursor = 'pointer';
        } else if (tile.mapTile?.army === board?.current_turn) {
            draw.style.cursor = 'pointer';
        }
    }
}

/**
 * Main click handler for canvas
 * @param {MouseEvent} ev - Mouse event
 */
export function canvasClick(ev) {
    const tile = tileAt(ev.offsetX, ev.offsetY);
    const board = getBoard();
    
    if (!tile || !board) return;
    
    logger.info(`🖱️ Canvas clicked at (${tile?.x}, ${tile?.y}), can_be_moved_to: ${tile?.can_be_moved_to}`);
    
    // Handle modifier keys
    if (ev.ctrlKey) {
        handleCtrlClick(tile, ev);
        return;
    }
    
    if (ev.altKey) {
        handleAltClick(tile, ev);
        return;
    }
    
    // Handle normal click
    handleNormalClick(tile, ev);
}

/**
 * Handle double click events
 * @param {MouseEvent} ev - Mouse event
 */
export function canvasdblClick(ev) {
    const tile = tileAt(ev.offsetX, ev.offsetY);
    const board = getBoard();
    
    if (!tile || !board) return;
    
    // Handle double click on capturable properties
    const capturableTypes = ['CITY', 'BASE_TOWER_1', 'FACTORY', 'PORT', 'AIRPORT'];
    
    if (capturableTypes.includes(tile.mapTile?.type)) {
        if (tile.unit?.can_capture && tile.unit.army === board.current_turn) {
            if (tile.unit.type === 'INFANTRY' || tile.unit.type === 'MECH') {
                if (window.unitCapture) {
                    window.unitCapture(tile);
                }
            }
        }
    } else if (tile.unit) {
        // Double click on unit to wait
        if (window.unitWait) {
            window.unitWait(tile);
        }
    }
}

/**
 * Handle right click (context menu)
 * @param {MouseEvent} ev - Mouse event
 */
export function handleContextMenu(ev) {
    ev.preventDefault();
    
    const tile = tileAt(ev.offsetX, ev.offsetY);
    if (!tile) return;
    
    logger.debug('🖱️ Right-click detected at', tile.x, tile.y);
    
    // Show context menu if available
    if (window.handleTransportRightClick) {
        window.handleTransportRightClick(tile, ev);
    }
}

// ===== CLICK TYPE HANDLERS =====

/**
 * Handle normal click
 * @param {Object} tile - Clicked tile
 * @param {MouseEvent} ev - Mouse event
 */
function handleNormalClick(tile, ev) {
    const board = getBoard();
    const gameState = getGameState();
    
    // Check if this is a transport operation
    if (window.handleTransportOperations && window.handleTransportOperations(tile, ev)) {
        return;
    }
    
    // Priority system for click handling
    
    // PRIORITY 1: Movement to highlighted tile
    if (tile.can_be_moved_to && board.selected) {
        if (window.executeMovement) {
            window.executeMovement(tile);
        }
        return;
    }
    
    // PRIORITY 2: Attack highlighted enemy
    if (tile.can_be_attacked && board.selected) {
        if (window.unitAttack) {
            window.unitAttack(tile);
        }
        return;
    }
    
    // PRIORITY 3: Select unit
    if (tile.unit && tile.unit.army === board.current_turn) {
        if (window.unitSelectWithTransportAndRange) {
            window.unitSelectWithTransportAndRange(tile);
        }
        return;
    }
    
    // PRIORITY 4: Capture property
    if (tile.mapTile && tile.mapTile.army !== board.current_turn && board.selected?.unit) {
        const capturableTypes = ['CITY', 'BASE_TOWER_1', 'FACTORY', 'PORT', 'AIRPORT'];
        if (capturableTypes.includes(tile.mapTile.type)) {
            if (window.unitCapture) {
                window.unitCapture(board.selected);
            }
            return;
        }
    }
    
    // PRIORITY 5: Create unit at factory
    if (tile.mapTile && tile.mapTile.army === board.current_turn && !tile.unit) {
        if (tile.mapTile.type === 'FACTORY') {
            if (window.unitCreate) {
                window.unitCreate(tile);
            }
            return;
        }
        if (tile.mapTile.type === 'AIRPORT') {
            if (window.airunitCreate) {
                window.airunitCreate(tile);
            }
            return;
        }
        if (tile.mapTile.type === 'PORT') {
            if (window.seaunitCreate) {
                window.seaunitCreate(tile);
            }
            return;
        }
    }
    
    // PRIORITY 6: Deselect
    if (board.selected) {
        setSelectedTile(null);
        
        // Clear all highlights
        const clearFunctions = [
            'clearMovementHighlights',
            'clearMovementHighlightsData',
            'clearTransportHighlights'
        ];
        
        clearFunctions.forEach(func => {
            if (window[func]) {
                window[func]();
            }
        });
        
        // Force visual update
        if (window.two) {
            window.two.update();
        }
    }
}

/**
 * Handle Ctrl+Click (loading units)
 * @param {Object} tile - Clicked tile
 * @param {MouseEvent} ev - Mouse event
 */
function handleCtrlClick(tile, ev) {
    logger.debug('🎮 Ctrl+Click detected');
    
    if (window.handleLoadingClick) {
        window.handleLoadingClick(tile);
    } else if (window.unitLoad) {
        window.unitLoad(tile);
    }
}

/**
 * Handle Alt+Click (unloading units)
 * @param {Object} tile - Clicked tile
 * @param {MouseEvent} ev - Mouse event
 */
function handleAltClick(tile, ev) {
    logger.debug('🎮 Alt+Click detected');
    
    if (window.handleTransportAltClick) {
        const handled = window.handleTransportAltClick(tile, ev);
        if (handled) return;
    }
    
    if (window.handleUnloadingClick) {
        window.handleUnloadingClick(tile);
    } else if (window.unitUnloadSelect) {
        window.unitUnloadSelect(tile);
    }
}

// ===== KEYBOARD HANDLERS =====

/**
 * Handle keyboard input
 * @param {KeyboardEvent} event - Keyboard event
 */
export function handleKeyDown(event) {
    const key = event.key.toLowerCase();
    
    switch (key) {
        case 't':
            // Show transport status
            if (window.getTransportStatus) {
                window.getTransportStatus();
            }
            break;
            
        case 'c':
            // Clear transport highlights
            if (window.clearTransportHighlights) {
                window.clearTransportHighlights();
            }
            break;
            
        case 'escape':
            // Cancel current action
            handleEscape();
            break;
            
        case 'enter':
            // Confirm current action
            handleEnter();
            break;
            
        case 'w':
            // Unit wait
            handleWaitKey();
            break;
            
        case 'a':
            // Attack mode
            handleAttackKey();
            break;
            
        case 'm':
            // Move mode
            handleMoveKey();
            break;
    }
}

/**
 * Handle Escape key
 */
function handleEscape() {
    // Hide context menu
    hideUnitContextMenu();
    
    // Clear selection
    const board = getBoard();
    if (board?.selected) {
        setSelectedTile(null);
        
        // Clear highlights
        if (window.clearAllHighlights) {
            window.clearAllHighlights();
        }
    }
}

/**
 * Handle Enter key
 */
function handleEnter() {
    const board = getBoard();
    const selected = board?.selected;
    
    if (selected?.unit && selected.unit.army === board.current_turn) {
        // If unit is selected, wait
        if (window.unitWait) {
            window.unitWait(selected);
        }
    }
}

/**
 * Handle Wait key
 */
function handleWaitKey() {
    const board = getBoard();
    const selected = board?.selected;
    
    if (selected?.unit && selected.unit.army === board.current_turn) {
        if (window.unitWait) {
            window.unitWait(selected);
        }
    }
}

/**
 * Handle Attack key
 */
function handleAttackKey() {
    const board = getBoard();
    const selected = board?.selected;
    
    if (selected?.unit && selected.unit.can_attack) {
        if (window.showAttackTargets) {
            window.showAttackTargets(selected.x, selected.y);
        }
    }
}

/**
 * Handle Move key
 */
function handleMoveKey() {
    const board = getBoard();
    const selected = board?.selected;
    
    if (selected?.unit && selected.unit.can_move) {
        if (window.showMovementRange) {
            window.showMovementRange(selected.x, selected.y);
        }
    }
}

// ===== TOUCH HANDLERS =====

/**
 * Handle touch start
 * @param {TouchEvent} ev - Touch event
 */
export function handleTouchStart(ev) {
    if (ev.touches.length !== 1) return;
    
    const touch = ev.touches[0];
    const rect = ev.target.getBoundingClientRect();
    const x = touch.clientX - rect.left;
    const y = touch.clientY - rect.top;
    
    inputState.dragStartPos = { x, y };
    
    // Start long press timer
    inputState.longPressTimer = setTimeout(() => {
        const tile = tileAt(x, y);
        if (tile) {
            // Simulate right click
            const mockEvent = {
                offsetX: x,
                offsetY: y,
                pageX: touch.pageX,
                pageY: touch.pageY,
                preventDefault: () => {},
                stopPropagation: () => {}
            };
            
            if (window.handleTransportRightClick) {
                window.handleTransportRightClick(tile, mockEvent);
            }
        }
    }, 500);
}

/**
 * Handle touch move
 * @param {TouchEvent} ev - Touch event
 */
export function handleTouchMove(ev) {
    // Cancel long press if moving
    if (inputState.longPressTimer) {
        clearTimeout(inputState.longPressTimer);
        inputState.longPressTimer = null;
    }
    
    inputState.isDragging = true;
}

/**
 * Handle touch end
 * @param {TouchEvent} ev - Touch event
 */
export function handleTouchEnd(ev) {
    // Cancel long press timer
    if (inputState.longPressTimer) {
        clearTimeout(inputState.longPressTimer);
        inputState.longPressTimer = null;
    }
    
    // If not dragging, treat as click
    if (!inputState.isDragging && inputState.dragStartPos) {
        const mockEvent = {
            offsetX: inputState.dragStartPos.x,
            offsetY: inputState.dragStartPos.y,
            detail: 1,
            ctrlKey: false,
            altKey: false
        };
        
        canvasClick(mockEvent);
    }
    
    inputState.isDragging = false;
    inputState.dragStartPos = null;
}

// ===== THROTTLE/DEBOUNCE UTILITIES =====

/**
 * Throttle function calls
 * @param {Function} func - Function to throttle
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Throttled function
 */
export function throttle(func, delay) {
    let lastCall = 0;
    return function (...args) {
        const now = Date.now();
        if (now - lastCall >= delay) {
            lastCall = now;
            return func.apply(this, args);
        }
    };
}

/**
 * Debounce function calls
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

// ===== INITIALIZATION =====

/**
 * Initialize input handlers
 */
export function initializeInputHandlers() {
    logger.info('Initializing input handlers...');
    
    const canvas = document.getElementById('draw');
    if (!canvas) {
        logger.error('Canvas element not found');
        return;
    }
    
    // Mouse handlers
    canvas.addEventListener('mousemove', canvasMove);
    canvas.addEventListener('click', throttle(canvasClick, 200));
    canvas.addEventListener('dblclick', canvasdblClick);
    canvas.addEventListener('contextmenu', handleContextMenu);
    
    // Touch handlers
    canvas.addEventListener('touchstart', handleTouchStart, { passive: false });
    canvas.addEventListener('touchmove', handleTouchMove, { passive: false });
    canvas.addEventListener('touchend', handleTouchEnd, { passive: false });
    
    // Keyboard handler
    document.addEventListener('keydown', handleKeyDown);
    
    // Control button handlers
    initializeControlButtons();
    
    logger.info('Input handlers initialized');
}

/**
 * Initialize control button handlers
 */
function initializeControlButtons() {
    // Rerender button
    const buttonrerender = document.getElementsByClassName('buttonrerender')[0];
    if (buttonrerender && window.rerender) {
        buttonrerender.onclick = debounce(window.rerender, 300);
    }
    
    // Show map checkbox
    const inputshowmap = document.getElementById('inputshowmap');
    if (inputshowmap && window.rerender) {
        inputshowmap.onchange = window.rerender;
    }
    
    // End turn button
    const buttonendturn = document.getElementsByClassName('buttonendturn')[0];
    if (buttonendturn && window.armyEndTurn) {
        buttonendturn.onclick = debounce(window.armyEndTurn, 500);
    }
    
    // End game button
    const buttonendgame = document.getElementsByClassName('buttonendgame')[0];
    if (buttonendgame && window.endGame) {
        buttonendgame.onclick = window.endGame;
    }
    
    // Chat button
    const buttonchat = document.getElementById('buttonchat');
    if (buttonchat && window.chat) {
        buttonchat.onclick = window.chat;
    }
    
    // Chat input
    const inputchat = document.getElementById('inputchat');
    if (inputchat && window.chat) {
        inputchat.onkeypress = window.chat;
    }
    
    // Show chat checkbox
    const inputshowchat = document.getElementById('inputshowchat');
    if (inputshowchat && window.showChat) {
        inputshowchat.onchange = window.showChat;
    }
    
    // Show JSON checkbox
    const inputshowjson = document.getElementById('inputshowjson');
    if (inputshowjson && window.showJson) {
        inputshowjson.onchange = window.showJson;
    }
}

/**
 * Initialize the input handler module
 */
export function initializeInputHandlerModule() {
    logger.info('Initializing input handler module...');
    
    // Set up global references for legacy compatibility
    if (window) {
        window.tileAt = tileAt;
        window.canvasMove = canvasMove;
        window.canvasClick = canvasClick;
        window.canvasdblClick = canvasdblClick;
        window.throttle = throttle;
        window.debounce = debounce;
    }
    
    // Note: Actual handler initialization happens after render.js loads
    // This prevents conflicts with existing handlers
    
    logger.info('Input handler module initialized');
}

// Initialize on module load
initializeInputHandlerModule();