/**
 * UI Systems Module - Manages all UI elements, displays, and user feedback
 * Extracted from render.js as part of modularization effort
 */

// Ensure logger exists
if (typeof window.logger === 'undefined') {
    window.logger = console; // Fallback to console if logger.js isn't loaded
}
const logger = window.logger;

// ===== UI STATE =====
const uiState = {
    contextMenuVisible: false,
    transportFeedbackTimer: null,
    jsonVisible: false,
    chatVisible: false
};

// ===== GAME STATUS DISPLAY =====

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
    
    // Update day counter
    const dayElement = document.getElementById('current-day');
    if (dayElement && gameData.days !== undefined) {
        dayElement.textContent = `Day ${gameData.days}`;
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
    
    // Store last game data globally for status updates
    window.lastGameData = gameData;
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
        
        // Update other resource displays if they exist
        const incomeElement = document.getElementById(`${army.toLowerCase()}-income`);
        if (incomeElement && data.income !== undefined) {
            incomeElement.textContent = `+${data.income.toLocaleString()}`;
        }
        
        const propertiesElement = document.getElementById(`${army.toLowerCase()}-properties`);
        if (propertiesElement && data.properties !== undefined) {
            propertiesElement.textContent = data.properties;
        }
    });
}

// ===== JSON DISPLAY =====

/**
 * Toggle JSON display area
 */
export function showJson() {
    const showJsonArea = document.getElementById('inputshowjson');
    const codeElement = document.getElementById('code');
    
    if (!showJsonArea || !codeElement) return;
    
    uiState.jsonVisible = showJsonArea.checked;
    
    if (uiState.jsonVisible) {
        codeElement.hidden = "";
    } else {
        codeElement.hidden = "true";
    }
}

/**
 * Update JSON display with board data
 * @param {Object} data - Data to display
 */
export function updateJsonDisplay(data) {
    const codeElement = document.getElementById('code');
    if (codeElement && uiState.jsonVisible) {
        codeElement.textContent = JSON.stringify(data, null, 2);
    }
}

// ===== CHAT DISPLAY =====

/**
 * Toggle chat display area
 */
export function showChat() {
    const showChatArea = document.getElementById('inputshowchat');
    const textareachat = document.getElementById('textareachat');
    const inputchat = document.getElementById('inputchat');
    const buttonchat = document.getElementById('buttonchat');
    
    if (!showChatArea) return;
    
    uiState.chatVisible = showChatArea.checked;
    
    const elements = [textareachat, inputchat, buttonchat];
    elements.forEach(elem => {
        if (elem) {
            elem.hidden = uiState.chatVisible ? "" : "true";
        }
    });
}

// ===== TRANSPORT FEEDBACK =====

/**
 * Show transport operation feedback to user
 * @param {string} message - Message to display
 * @param {string} type - Message type (info, success, error)
 */
export function showTransportFeedback(message, type = 'info') {
    // Remove existing feedback
    const existingFeedback = document.getElementById('transport-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    
    // Clear any existing timer
    if (uiState.transportFeedbackTimer) {
        clearTimeout(uiState.transportFeedbackTimer);
    }
    
    // Create new feedback element
    const feedback = document.createElement('div');
    feedback.id = 'transport-feedback';
    
    const bgColor = type === 'error' ? '#e74c3c' : 
                   type === 'success' ? '#27ae60' : '#3498db';
    
    feedback.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: ${bgColor};
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        font-size: 14px;
        z-index: 1000;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        animation: slideUp 0.3s ease-out;
    `;
    
    feedback.textContent = message;
    document.body.appendChild(feedback);
    
    // Auto-remove after 3 seconds
    uiState.transportFeedbackTimer = setTimeout(() => {
        if (feedback.parentNode) {
            feedback.style.animation = 'slideDown 0.3s ease-out';
            setTimeout(() => feedback.remove(), 300);
        }
    }, 3000);
}

// ===== CARGO INFO DISPLAY =====

/**
 * Show cargo information for a unit
 * @param {Object} unit - Unit object
 * @param {Object} cargoInfo - Cargo information
 */
export function showCargoInfo(unit, cargoInfo) {
    let message = `${unit.type}: `;
    
    if (!cargoInfo.is_transport) {
        message += "Not a transport unit";
    } else {
        message += `${cargoInfo.current_cargo}/${cargoInfo.max_capacity} cargo`;
        
        const cargoList = cargoInfo.cargo_list || cargoInfo.cargo_units || [];
        if (cargoList.length > 0) {
            const cargoTypes = cargoList.map(c => c.unit_type || c.type).join(', ');
            message += ` (${cargoTypes})`;
        }
    }
    
    showTransportFeedback(message);
}

// ===== CONTEXT MENU =====

/**
 * Show unit context menu at specified position
 * @param {number} x - X position
 * @param {number} y - Y position
 * @param {Object} selectedUnit - Selected unit
 * @param {Object} targetUnit - Target unit
 */
export function showUnitContextMenu(x, y, selectedUnit, targetUnit) {
    logger.debug('Showing context menu', {selectedUnit, targetUnit});
    
    const contextMenu = document.getElementById('unitContextMenu');
    if (!contextMenu) {
        logger.error('Context menu element not found');
        return;
    }
    
    // Position the menu at mouse coordinates
    contextMenu.style.left = x + 'px';
    contextMenu.style.top = y + 'px';
    contextMenu.style.display = 'block';
    
    // Store context data
    contextMenu.dataset.selectedX = selectedUnit.x;
    contextMenu.dataset.selectedY = selectedUnit.y;
    contextMenu.dataset.targetX = targetUnit.x;
    contextMenu.dataset.targetY = targetUnit.y;
    
    // Show/hide menu items based on unit capabilities
    const repairItem = contextMenu.querySelector('[data-action="repair"]');
    if (repairItem) {
        repairItem.style.display = targetUnit.hp < 100 ? 'block' : 'none';
    }
    
    uiState.contextMenuVisible = true;
}

/**
 * Hide unit context menu
 */
export function hideUnitContextMenu() {
    const contextMenu = document.getElementById('unitContextMenu');
    if (contextMenu) {
        contextMenu.style.display = 'none';
    }
    uiState.contextMenuVisible = false;
}

// ===== UI INITIALIZATION =====

/**
 * Apply complete click fix for UI responsiveness
 */
export function applyCompleteClickFix() {
    logger.info('Applying UI click fixes...');
    
    // Update game status if data is available
    if (window.lastGameData) {
        updateGameStatus(window.lastGameData);
    }
    
    // Set up context menu close on click outside
    document.addEventListener('click', (e) => {
        if (uiState.contextMenuVisible && !e.target.closest('#unitContextMenu')) {
            hideUnitContextMenu();
        }
    });
}

/**
 * Create a menu button element
 * @param {string} text - Button text
 * @param {Function} onClick - Click handler
 * @param {string} className - CSS class name
 * @returns {HTMLElement} Button element
 */
export function createMenuButton(text, onClick, className = '') {
    const button = document.createElement('button');
    button.textContent = text;
    button.className = `menu-button ${className}`;
    button.onclick = onClick;
    
    button.style.cssText = `
        padding: 8px 16px;
        margin: 4px;
        border: none;
        border-radius: 4px;
        background: #3498db;
        color: white;
        cursor: pointer;
        font-size: 14px;
        transition: background 0.2s;
    `;
    
    button.onmouseover = () => {
        button.style.background = '#2980b9';
    };
    
    button.onmouseout = () => {
        button.style.background = '#3498db';
    };
    
    return button;
}

// ===== ANIMATION STYLES =====

/**
 * Initialize UI animations
 */
export function initializeUIAnimations() {
    if (!document.getElementById('ui-animations')) {
        const style = document.createElement('style');
        style.id = 'ui-animations';
        style.textContent = `
            @keyframes slideUp {
                from {
                    transform: translateX(-50%) translateY(20px);
                    opacity: 0;
                }
                to {
                    transform: translateX(-50%) translateY(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideDown {
                from {
                    transform: translateX(-50%) translateY(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(-50%) translateY(20px);
                    opacity: 0;
                }
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
            
            .menu-button:active {
                transform: scale(0.95);
            }
        `;
        document.head.appendChild(style);
    }
}

// ===== LOADING INDICATORS =====

/**
 * Show loading indicator
 * @param {string} message - Loading message
 * @returns {HTMLElement} Loading element
 */
export function showLoadingIndicator(message = 'Loading...') {
    const existing = document.getElementById('loading-indicator');
    if (existing) {
        existing.remove();
    }
    
    const loader = document.createElement('div');
    loader.id = 'loading-indicator';
    loader.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 20px 40px;
        border-radius: 10px;
        font-size: 16px;
        z-index: 10000;
        animation: fadeIn 0.3s ease-out;
    `;
    
    loader.innerHTML = `
        <div style="text-align: center;">
            <div class="spinner" style="
                border: 3px solid rgba(255,255,255,0.3);
                border-radius: 50%;
                border-top: 3px solid white;
                width: 30px;
                height: 30px;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px;
            "></div>
            <div>${message}</div>
        </div>
    `;
    
    document.body.appendChild(loader);
    return loader;
}

/**
 * Hide loading indicator
 */
export function hideLoadingIndicator() {
    const loader = document.getElementById('loading-indicator');
    if (loader) {
        loader.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => loader.remove(), 300);
    }
}

// ===== MODULE INITIALIZATION =====

/**
 * Initialize the UI systems module
 */
export function initializeUISystemsModule() {
    logger.info('Initializing UI systems module...');
    
    // Initialize animations
    initializeUIAnimations();
    
    // Set up global references for legacy compatibility
    if (window) {
        window.updateGameStatus = updateGameStatus;
        window.showJson = showJson;
        window.showChat = showChat;
        window.showTransportFeedback = showTransportFeedback;
        window.showCargoInfo = showCargoInfo;
        window.showUnitContextMenu = showUnitContextMenu;
        window.hideUnitContextMenu = hideUnitContextMenu;
        window.applyCompleteClickFix = applyCompleteClickFix;
        window.createMenuButton = createMenuButton;
        window.showLoadingIndicator = showLoadingIndicator;
        window.hideLoadingIndicator = hideLoadingIndicator;
        window.updateJsonDisplay = updateJsonDisplay;
    }
    
    // Apply click fixes when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(applyCompleteClickFix, 200);
        });
    } else {
        setTimeout(applyCompleteClickFix, 200);
    }
    
    logger.info('UI systems module initialized');
}

// Initialize on module load
initializeUISystemsModule();