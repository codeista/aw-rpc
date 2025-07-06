// static/js/transport_integration.js - Advance Wars Style Frontend

/**
 * ADVANCE WARS STYLE TRANSPORT CONTROLS
 * 
 * Controls:
 * - Normal Click: Select unit / Move to empty tile
 * - Click on friendly transport: Board transport (if selected unit can board)
 * - Right Click on transport: Show exit options
 * - Click on exit highlight: Exit transport to that position
 * 
 * Visual Indicators:
 * - Green highlights: Transports the selected cargo can board
 * - Blue highlights: Positions where cargo can exit from selected transport
 * - Yellow border: Transport units with cargo
 * - Cargo count indicator: Shows number of units in transport
 */

// =============================================================================
// GLOBAL TRANSPORT STATE
// =============================================================================

let transportState = {
    selectedUnit: null,
    selectedTransport: null,
    loadableTransports: [],
    exitPositions: [],
    showingExitOptions: false,
    showingBoardingOptions: false
};

// =============================================================================
// MAIN TRANSPORT INTEGRATION
// =============================================================================

// Override the main tile click handler to include transport logic
function handleTileClickWithTransport(tile) {
    console.log(`AW_TRANSPORT: Tile clicked at (${tile.x}, ${tile.y})`);
    
    // Clear previous highlights
    clearAllTransportHighlights();
    
    // Handle different click scenarios
    if (board.selected) {
        const selectedTile = board.selected;
        const selectedUnit = selectedTile.unit;
        
        // Scenario 1: Clicking on a friendly transport with a cargo unit selected
        if (tile.unit && 
            tile.unit.army === selectedUnit.army && 
            isTransportUnit(tile.unit) && 
            canUnitBoardTransports(selectedUnit)) {
            
            console.log(`AW_TRANSPORT: Attempting to board transport`);
            attemptToBoardTransport(selectedTile.x, selectedTile.y, tile.x, tile.y);
            return;
        }
        
        // Scenario 2: Normal movement (including auto-boarding)
        if (!tile.unit) {
            console.log(`AW_TRANSPORT: Normal movement`);
            attemptEnhancedMovement(selectedTile.x, selectedTile.y, tile.x, tile.y);
            return;
        }
        
        // Scenario 3: Selecting a different unit
        if (tile.unit && tile.unit.army === board.current_turn) {
            selectUnitWithTransportOptions(tile);
            return;
        }
        
        // Scenario 4: Attack (existing logic)
        if (tile.unit && tile.unit.army !== board.current_turn) {
            // Handle attack (existing attack logic)
            unitAttack(tile.x, tile.y);
            return;
        }
    } else {
        // No unit selected - select this unit if it belongs to current player
        if (tile.unit && tile.unit.army === board.current_turn) {
            selectUnitWithTransportOptions(tile);
            return;
        }
    }
    
    // Fallback to default behavior
    unitSelect(tile);
}

// =============================================================================
// UNIT SELECTION WITH TRANSPORT OPTIONS
// =============================================================================

function selectUnitWithTransportOptions(tile) {
    console.log(`AW_TRANSPORT: Selecting unit with transport options`);
    
    // Select the unit normally first
    unitSelect(tile);
    
    // If it's a cargo unit, show nearby transports
    if (canUnitBoardTransports(tile.unit)) {
        showLoadableTransports(tile.x, tile.y);
    }
    
    // If it's a transport with cargo, prepare for exit options
    if (isTransportUnit(tile.unit)) {
        transportState.selectedTransport = tile;
        // Don't show exit options immediately - wait for right-click or special input
    }
}

// =============================================================================
// TRANSPORT BOARDING
// =============================================================================

function attemptToBoardTransport(cargoX, cargoY, transportX, transportY) {
    console.log(`AW_TRANSPORT: ${cargoX},${cargoY} boarding ${transportX},${transportY}`);
    
    jsonrpc('cargo_board_transport', {
        cargo_x: cargoX,
        cargo_y: cargoY,
        transport_x: transportX,
        transport_y: transportY
    }).then(result => {
        if (result.success) {
            console.log(`AW_TRANSPORT: Boarding successful - ${result.message}`);
            
            // Show success message
            showTransportMessage(result.message, 'success');
            
            // Clear selection and highlights
            clearAllTransportHighlights();
            board.selected = null;
            
            // Update board display
            updateBoardDisplay();
        } else {
            console.error(`AW_TRANSPORT: Boarding failed - ${result.error}`);
            showTransportMessage(result.error, 'error');
        }
    }).catch(error => {
        console.error('AW_TRANSPORT: Boarding request failed:', error);
        showTransportMessage('Failed to board transport', 'error');
    });
}

function showLoadableTransports(cargoX, cargoY) {
    jsonrpc('get_loadable_transports', {
        cargo_x: cargoX,
        cargo_y: cargoY
    }).then(result => {
        if (result.success && result.loadable_transports.length > 0) {
            transportState.loadableTransports = result.loadable_transports;
            transportState.showingBoardingOptions = true;
            
            // Highlight loadable transports in green
            result.loadable_transports.forEach(transport => {
                highlightTile(transport.x, transport.y, 'loadable-transport');
            });
            
            console.log(`AW_TRANSPORT: Showing ${result.loadable_transports.length} loadable transports`);
        }
    }).catch(error => {
        console.error('AW_TRANSPORT: Failed to get loadable transports:', error);
    });
}

// =============================================================================
// TRANSPORT EXITING
// =============================================================================

function showTransportExitOptions(transportX, transportY) {
    console.log(`AW_TRANSPORT: Showing exit options for transport at (${transportX}, ${transportY})`);
    
    jsonrpc('get_exit_positions', {
        transport_x: transportX,
        transport_y: transportY
    }).then(result => {
        if (result.success && result.valid_positions.length > 0) {
            transportState.exitPositions = result.valid_positions;
            transportState.showingExitOptions = true;
            
            // Highlight exit positions in blue
            result.valid_positions.forEach(pos => {
                highlightTile(pos.x, pos.y, 'exit-position');
            });
            
            // Show cargo selection UI if multiple cargo units
            if (result.transport_info.cargo_units.length > 1) {
                showCargoSelectionMenu(result.transport_info.cargo_units, transportX, transportY);
            }
            
            console.log(`AW_TRANSPORT: Showing ${result.valid_positions.length} exit positions`);
        } else {
            showTransportMessage('No units can be deployed from this transport', 'info');
        }
    }).catch(error => {
        console.error('AW_TRANSPORT: Failed to get exit positions:', error);
    });
}

function attemptToExitTransport(transportX, transportY, exitX, exitY, cargoIndex = 0) {
    console.log(`AW_TRANSPORT: Exiting cargo ${cargoIndex} from (${transportX},${transportY}) to (${exitX},${exitY})`);
    
    jsonrpc('cargo_exit_transport', {
        transport_x: transportX,
        transport_y: transportY,
        exit_x: exitX,
        exit_y: exitY,
        cargo_index: cargoIndex
    }).then(result => {
        if (result.success) {
            console.log(`AW_TRANSPORT: Exit successful - ${result.message}`);
            
            // Show success message
            showTransportMessage(result.message, 'success');
            
            // Clear highlights and selection
            clearAllTransportHighlights();
            transportState.showingExitOptions = false;
            
            // Update board display
            updateBoardDisplay();
        } else {
            console.error(`AW_TRANSPORT: Exit failed - ${result.error}`);
            showTransportMessage(result.error, 'error');
        }
    }).catch(error => {
        console.error('AW_TRANSPORT: Exit request failed:', error);
        showTransportMessage('Failed to exit transport', 'error');
    });
}

// =============================================================================
// ENHANCED MOVEMENT WITH AUTO-BOARDING
// =============================================================================

function attemptEnhancedMovement(fromX, fromY, toX, toY) {
    console.log(`AW_TRANSPORT: Enhanced movement from (${fromX},${fromY}) to (${toX},${toY})`);
    
    jsonrpc('unit_move_enhanced', {
        from_x: fromX,
        from_y: fromY,
        to_x: toX,
        to_y: toY
    }).then(result => {
        if (result.success) {
            if (result.action === 'boarded_transport') {
                console.log(`AW_TRANSPORT: Auto-boarded transport - ${result.message}`);
                showTransportMessage(result.message, 'success');
            } else {
                console.log(`AW_TRANSPORT: Normal movement - ${result.message}`);
            }
            
            // Clear selection and update board
            clearAllTransportHighlights();
            board.selected = null;
            updateBoardDisplay();
        } else {
            console.error(`AW_TRANSPORT: Movement failed - ${result.error}`);
            showTransportMessage(result.error, 'error');
        }
    }).catch(error => {
        console.error('AW_TRANSPORT: Enhanced movement failed:', error);
        showTransportMessage('Movement failed', 'error');
    });
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

function isTransportUnit(unit) {
    if (!unit || !unit.type) return false;
    const transportTypes = ['APC', 'LANDER', 'TCOPTER', 'CRUISER', 'CARRIER', 'BLACKBOAT'];
    const unitType = unit.type.name || unit.type;
    return transportTypes.includes(unitType);
}

function canUnitBoardTransports(unit) {
    if (!unit || !unit.type) return false;
    const cargoTypes = ['INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 
                       'ANTIAIR', 'ARTILLERY', 'ROCKET', 'MISSILE', 'APC',
                       'BCOPTER', 'TCOPTER', 'FIGHTER', 'BOMBER'];
    const unitType = unit.type.name || unit.type;
    return cargoTypes.includes(unitType);
}

function highlightTile(x, y, className) {
    // Store highlights for next render cycle
    if (!window.transportHighlights) {
        window.transportHighlights = [];
    }
    
    window.transportHighlights.push({
        x: x,
        y: y,
        type: className
    });
    
    console.log(`AW_TRANSPORT: Highlighting tile (${x}, ${y}) as ${className}`);
}

function clearAllTransportHighlights() {
    window.transportHighlights = [];
    transportState.loadableTransports = [];
    transportState.exitPositions = [];
    transportState.showingExitOptions = false;
    transportState.showingBoardingOptions = false;
    
    console.log('AW_TRANSPORT: Cleared all transport highlights');
}

// =============================================================================
// USER INTERFACE ELEMENTS
// =============================================================================

function showTransportMessage(message, type = 'info') {
    // Create or update transport message display
    let messageDiv = document.getElementById('transport-message');
    if (!messageDiv) {
        messageDiv = document.createElement('div');
        messageDiv.id = 'transport-message';
        messageDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            max-width: 300px;
        `;
        document.body.appendChild(messageDiv);
    }
    
    // Set color based on type
    const colors = {
        success: '#4CAF50',
        error: '#f44336',
        info: '#2196F3',
        warning: '#ff9800'
    };
    
    messageDiv.style.backgroundColor = colors[type] || colors.info;
    messageDiv.textContent = message;
    messageDiv.style.display = 'block';
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        if (messageDiv) {
            messageDiv.style.display = 'none';
        }
    }, 3000);
}

function showCargoSelectionMenu(cargoUnits, transportX, transportY) {
    // Create cargo selection overlay
    const overlay = document.createElement('div');
    overlay.id = 'cargo-selection-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 2000;
        display: flex;
        align-items: center;
        justify-content: center;
    `;
    
    const menu = document.createElement('div');
    menu.style.cssText = `
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    `;
    
    menu.innerHTML = `
        <h3>Select Unit to Deploy</h3>
        <div id="cargo-list"></div>
        <button onclick="closeCarg oSelectionMenu()">Cancel</button>
    `;
    
    const cargoList = menu.querySelector('#cargo-list');
    cargoUnits.forEach((cargo, index) => {
        const cargoButton = document.createElement('button');
        cargoButton.textContent = `${cargo.unit_type} (HP: ${cargo.hp})`;
        cargoButton.style.cssText = `
            display: block;
            width: 100%;
            margin: 5px 0;
            padding: 10px;
            border: 1px solid #ccc;
            background: #f9f9f9;
            cursor: pointer;
        `;
        cargoButton.onclick = () => {
            transportState.selectedCargoIndex = index;
            closeCargoSelectionMenu();
        };
        cargoList.appendChild(cargoButton);
    });
    
    overlay.appendChild(menu);
    document.body.appendChild(overlay);
}

function closeCargoSelectionMenu() {
    const overlay = document.getElementById('cargo-selection-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// =============================================================================
// EVENT HANDLERS
// =============================================================================

// Handle right-click for transport exit options
function handleRightClick(tile) {
    if (tile.unit && 
        tile.unit.army === board.current_turn && 
        isTransportUnit(tile.unit)) {
        
        console.log(`AW_TRANSPORT: Right-click on transport at (${tile.x}, ${tile.y})`);
        showTransportExitOptions(tile.x, tile.y);
    }
}

// Handle exit position clicks
function handleExitPositionClick(tile) {
    if (transportState.showingExitOptions && 
        transportState.exitPositions.some(pos => pos.x === tile.x && pos.y === tile.y)) {
        
        const transport = transportState.selectedTransport;
        const cargoIndex = transportState.selectedCargoIndex || 0;
        
        console.log(`AW_TRANSPORT: Exit position clicked at (${tile.x}, ${tile.y})`);
        attemptToExitTransport(transport.x, transport.y, tile.x, tile.y, cargoIndex);
    }
}

// Override keyboard controls for transport actions
function handleKeyboardControls(event) {
    if (!board.selected) return;
    
    const selectedTile = board.selected;
    const selectedUnit = selectedTile.unit;
    
    switch(event.key.toLowerCase()) {
        case 'b': // Board transport
            if (canUnitBoardTransports(selectedUnit)) {
                showLoadableTransports(selectedTile.x, selectedTile.y);
            }
            break;
            
        case 'e': // Exit transport
            if (isTransportUnit(selectedUnit)) {
                showTransportExitOptions(selectedTile.x, selectedTile.y);
            }
            break;
            
        case 'escape': // Cancel transport actions
            clearAllTransportHighlights();
            break;
    }
}

// =============================================================================
// INTEGRATION WITH EXISTING GAME SYSTEMS
// =============================================================================

// Enhanced board update to show transport indicators
function updateBoardDisplayWithTransports() {
    // Call existing board update
    updateBoardDisplay();
    
    // Add transport-specific visual indicators
    addTransportIndicators();
}

function addTransportIndicators() {
    // Get all transport units for visual indicators
    jsonrpc('get_transport_summary', {}).then(result => {
        if (result.success) {
            result.transports.forEach(transport => {
                addTransportVisualIndicator(transport);
            });
        }
    }).catch(error => {
        console.error('AW_TRANSPORT: Failed to get transport summary:', error);
    });
}

function addTransportVisualIndicator(transportInfo) {
    // Find the tile element for this transport
    const tileElement = getTileElement(transportInfo.x, transportInfo.y);
    if (!tileElement) return;
    
    // Add visual indicator for transports with cargo
    if (transportInfo.current_cargo > 0) {
        // Add yellow border to indicate transport has cargo
        tileElement.style.border = '3px solid #FFD700';
        
        // Add cargo count indicator
        let cargoIndicator = tileElement.querySelector('.cargo-indicator');
        if (!cargoIndicator) {
            cargoIndicator = document.createElement('div');
            cargoIndicator.className = 'cargo-indicator';
            cargoIndicator.style.cssText = `
                position: absolute;
                top: 2px;
                right: 2px;
                background: #FFD700;
                color: black;
                border-radius: 50%;
                width: 16px;
                height: 16px;
                font-size: 10px;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10;
            `;
            tileElement.appendChild(cargoIndicator);
        }
        cargoIndicator.textContent = transportInfo.current_cargo;
    } else {
        // Remove indicators if no cargo
        tileElement.style.border = '';
        const cargoIndicator = tileElement.querySelector('.cargo-indicator');
        if (cargoIndicator) {
            cargoIndicator.remove();
        }
    }
}

function getTileElement(x, y) {
    // This depends on your specific tile rendering implementation
    // Adjust according to your actual tile element structure
    return document.querySelector(`[data-tile-x="${x}"][data-tile-y="${y}"]`);
}

// =============================================================================
// RENDER INTEGRATION FOR TWO.JS
// =============================================================================

// Enhanced rendering for Two.js with transport highlights
function renderTransportHighlights(two) {
    if (!window.transportHighlights) return;
    
    window.transportHighlights.forEach(highlight => {
        const tileSize = 32; // Adjust to your tile size
        const x = highlight.x * tileSize;
        const y = highlight.y * tileSize;
        
        let color;
        switch(highlight.type) {
            case 'loadable-transport':
                color = '#4CAF50'; // Green for loadable transports
                break;
            case 'exit-position':
                color = '#2196F3'; // Blue for exit positions
                break;
            default:
                color = '#FFC107'; // Yellow for other highlights
        }
        
        // Create highlight rectangle
        const highlightRect = two.makeRectangle(x + tileSize/2, y + tileSize/2, tileSize-2, tileSize-2);
        highlightRect.fill = color;
        highlightRect.opacity = 0.3;
        highlightRect.stroke = color;
        highlightRect.linewidth = 2;
        
        // Add to Two.js scene
        two.add(highlightRect);
    });
    
    // Update Two.js display
    two.update();
}

// =============================================================================
// INITIALIZATION AND CLEANUP
// =============================================================================

// Initialize transport system integration
function initializeTransportSystem() {
    console.log('AW_TRANSPORT: Initializing Advance Wars transport system');
    
    // Add keyboard event listeners
    document.addEventListener('keydown', handleKeyboardControls);
    
    // Add right-click context menu prevention and custom handler
    document.addEventListener('contextmenu', function(event) {
        event.preventDefault();
        
        // Get tile from click position (adjust according to your tile detection logic)
        const tile = getTileFromMousePosition(event.clientX, event.clientY);
        if (tile) {
            handleRightClick(tile);
        }
    });
    
    // Override existing tile click handler
    const originalTileClick = window.handleTileClick || function() {};
    window.handleTileClick = function(tile) {
        // Check if this is an exit position click
        if (transportState.showingExitOptions) {
            handleExitPositionClick(tile);
            return;
        }
        
        // Otherwise use transport-aware click handler
        handleTileClickWithTransport(tile);
    };
    
    console.log('AW_TRANSPORT: Transport system initialized successfully');
}

function getTileFromMousePosition(clientX, clientY) {
    // This needs to be implemented based on your specific rendering system
    // For Two.js, you'd convert screen coordinates to tile coordinates
    // This is a placeholder implementation
    const canvas = document.querySelector('canvas');
    if (!canvas) return null;
    
    const rect = canvas.getBoundingClientRect();
    const x = clientX - rect.left;
    const y = clientY - rect.top;
    
    const tileSize = 32; // Adjust to your tile size
    const tileX = Math.floor(x / tileSize);
    const tileY = Math.floor(y / tileSize);
    
    // Return tile object (adjust to match your tile structure)
    return {
        x: tileX,
        y: tileY,
        unit: getUnitAtPosition(tileX, tileY) // Implement this based on your game state
    };
}

function getUnitAtPosition(x, y) {
    // Get unit from current board state
    if (!board || !board.grid) return null;
    
    const tile = board.grid.find(tile => tile.x === x && tile.y === y);
    return tile ? tile.unit : null;
}

// =============================================================================
// HELP AND TUTORIAL SYSTEM
// =============================================================================

function showTransportHelp() {
    const helpText = `
    ADVANCE WARS TRANSPORT CONTROLS:
    
    BOARDING TRANSPORTS:
    • Select cargo unit (Infantry, Mech, Tank, etc.)
    • Click on friendly transport to board
    • Or move normally - will auto-board if destination is friendly transport
    • Press 'B' to highlight nearby transports
    
    EXITING TRANSPORTS:
    • Right-click on transport to see exit options
    • Click on blue highlighted tiles to deploy units
    • Press 'E' when transport is selected to show exit options
    
    VISUAL INDICATORS:
    • Green highlights = Transports you can board
    • Blue highlights = Positions where you can deploy
    • Yellow border = Transport carrying units
    • Number badge = Number of units in transport
    
    ADVANCED WARS RULES:
    • Cargo units can act immediately after being deployed
    • Transports cannot move after deploying units
    • Units automatically board when moving onto friendly transport
    `;
    
    showTransportMessage(helpText, 'info');
}

// =============================================================================
// EXPORT FUNCTIONS FOR GLOBAL ACCESS
// =============================================================================

// Make functions available globally
window.AW_Transport = {
    initializeTransportSystem,
    showTransportHelp,
    clearAllTransportHighlights,
    isTransportUnit,
    canUnitBoardTransports,
    showLoadableTransports,
    showTransportExitOptions,
    handleTileClickWithTransport,
    renderTransportHighlights
};

// Auto-initialize when script loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('AW_TRANSPORT: DOM loaded, initializing transport system...');
    initializeTransportSystem();
});

// =============================================================================
// DEBUG AND TESTING FUNCTIONS
// =============================================================================

function debugTransportState() {
    console.log('=== TRANSPORT DEBUG STATE ===');
    console.log('Selected Unit:', transportState.selectedUnit);
    console.log('Selected Transport:', transportState.selectedTransport);
    console.log('Loadable Transports:', transportState.loadableTransports);
    console.log('Exit Positions:', transportState.exitPositions);
    console.log('Showing Exit Options:', transportState.showingExitOptions);
    console.log('Showing Boarding Options:', transportState.showingBoardingOptions);
    console.log('Transport Highlights:', window.transportHighlights);
    console.log('=============================');
}

// Make debug function available globally
window.debugTransportState = debugTransportState;