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
    showingBoardingOptions: false,
    selectedCargoIndex: 0
};

// =============================================================================
// MAIN TRANSPORT INTEGRATION
// =============================================================================

function handleTileClickWithTransport(tile, event) {
    console.log(`AW_TRANSPORT: Tile clicked at (${tile.x}, ${tile.y})`);

        // ========================================================================
    // PRIORITY 1: PRODUCTION BUILDINGS (CRITICAL FIX)
    // ========================================================================
    if ((tile.mapTile.type === 'FACTORY' || 
         tile.mapTile.type === 'AIRPORT' || 
         tile.mapTile.type === 'PORT') &&
        tile.mapTile.army === board.current_turn &&
        !tile.unit) {
        
        console.log(`🏭 PRODUCTION: ${tile.mapTile.type} click at (${tile.x}, ${tile.y})`);
        
        // Call the appropriate creation function
        if (tile.mapTile.type === 'FACTORY') {
            unitCreate(tile);
        } else if (tile.mapTile.type === 'AIRPORT') {
            airunitCreate(tile);
        } else if (tile.mapTile.type === 'PORT') {
            seaunitCreate(tile);
        }
        return; // Exit early, don't process as transport
    }
    
    // CRITICAL: Don't interfere with frontend transport operations
    if (typeof frontendTransportState !== 'undefined') {
        if (frontendTransportState.showingUnloadOptions) {
            console.log('AW_TRANSPORT: Frontend unload mode active - not handling');
            return false; // Let frontend handle unload
        }
        if (frontendTransportState.showingLoadOptions) {
            console.log('AW_TRANSPORT: Frontend load mode active - not handling');
            return false; // Let frontend handle load
        }
    }
    
    // CRITICAL: Don't interfere with alt-clicks
    if (event && event.altKey) {
        console.log('AW_TRANSPORT: Alt-click detected - not handling');
        return false; // Let alt-click system handle
    }
    
    // Clear previous highlights
    clearAllTransportHighlights();
    
    // Handle transport integration logic only if no other system is active
    if (board.selected) {
        const selectedTile = board.selected;
        const selectedUnit = selectedTile.unit;
        
        // Scenario 1: Clicking on a friendly transport with a cargo unit selected
        if (tile.unit && 
            tile.unit.army === selectedUnit.army && 
            isTransportUnit(tile.unit) && 
            canUnitBoardTransports(selectedUnit) &&
            !(tile.x === selectedTile.x && tile.y === selectedTile.y)) {
            
            console.log(`AW_TRANSPORT: Attempting to board transport`);
            attemptToBoardTransport(selectedTile.x, selectedTile.y, tile.x, tile.y);
            return true; // We handled it
        }
        
        // Scenario 2: Enhanced movement (only if not conflicting)
        if (!tile.unit && tile.can_be_moved_to) {
            console.log(`AW_TRANSPORT: Enhanced movement`);
            safelyPerformEnhancedMovement(selectedTile.x, selectedTile.y, tile.x, tile.y);
            return true; // We handled it
        }
        
        // Scenario 3: Selecting a different unit
        if (tile.unit && tile.unit.army === board.current_turn) {
            console.log(`AW_TRANSPORT: Selecting unit with transport options`);
            selectUnitWithTransportOptions(tile);
            return true; // We handled it
        }
    } else {
        // No unit selected - select this unit if it belongs to current player
        if (tile.unit && tile.unit.army === board.current_turn) {
            console.log(`AW_TRANSPORT: Selecting unit with transport options`);
            selectUnitWithTransportOptions(tile);
            return true; // We handled it
        }
    }
    
    return false; // We didn't handle it
}

function safelyPerformEnhancedMovement(fromX, fromY, toX, toY) {
    console.log(`AW_TRANSPORT: Enhanced movement from (${fromX},${fromY}) to (${toX},${toY})`);
    
    // ✅ FIX: Find unit using the flat array structure
    const fromTile = board.grid.find(t => t.x === fromX && t.y === fromY);
    if (!fromTile || !fromTile.unit) {
        console.log('AW_TRANSPORT: No unit at source position');
        return;
    }
    
    if (!fromTile.unit.can_move) {
        console.log('AW_TRANSPORT: Unit cannot move this turn');
        showTransportMessage('Unit has already moved this turn', 'warning');
        return;
    }
    
    // ✅ FIX: Use regular movement for transports (much more reliable)
    if (isTransportUnit(fromTile.unit)) {
        console.log(`AW_TRANSPORT: Using regular movement for transport`);
        jsonrpc('unit_move', {
            x: fromX,
            y: fromY,
            x2: toX,
            y2: toY
        }).then(result => {
            if (result.success || !result.error) {
                console.log(`AW_TRANSPORT: Transport movement successful`);
                
                // ✅ FIX: Update selection to new position using flat array
                const newTile = board.grid.find(t => t.x === toX && t.y === toY);
                if (newTile) {
                    board.selected = newTile;
                    console.log(`🔄 Selection updated to new position (${toX}, ${toY})`);
                }
                
                clearAllTransportHighlights();
                updateBoardDisplay();
            } else {
                console.error(`AW_TRANSPORT: Transport movement failed - ${result.error}`);
                showTransportMessage(result.error || 'Movement failed', 'error');
            }
        }).catch(error => {
            console.error('AW_TRANSPORT: Transport movement failed:', error);
            showTransportMessage('Movement failed', 'error');
        });
        return;
    }
    
    // Regular enhanced movement for non-transport units
    jsonrpc('unit_move_enhanced', {
        from_x: fromX,
        from_y: fromY,
        to_x: toX,
        to_y: toY
    }).then(result => {
        if (result.success) {
            console.log('AW_TRANSPORT: Movement successful');
            showTransportMessage(result.message || 'Unit moved successfully', 'success');
            clearAllTransportHighlights();
            updateBoardDisplay();
        } else {
            console.log('AW_TRANSPORT: Movement failed -', result.error);
            showTransportMessage(result.error, 'error');
        }
    }).catch(error => {
        console.error('AW_TRANSPORT: Movement error:', error);
        showTransportMessage('Movement failed', 'error');
    });
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
        
        // Clear transport highlights
        clearAllTransportHighlights();
        
        // ✅ FIX: Find transport tile using flat array structure
        const transportTile = board.grid.find(t => t.x === transportX && t.y === transportY);
        if (transportTile && transportTile.unit) {
            board.selected = transportTile;
            console.log(`🔄 Selection updated to transport at (${transportX}, ${transportY})`);
            
            // Show movement range for the transport
            if (typeof showMovementRange === 'function') {
                showMovementRange(transportX, transportY);
            }
        } else {
            console.log(`❌ Could not find transport tile at (${transportX}, ${transportY})`);
            board.selected = null;
        }
        
        // Update board display
        updateBoardDisplay();
    }else {
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
    
    // ✅ NEW: First check if transport has cargo
    jsonrpc('get_cargo_info', {x: transportX, y: transportY}).then(cargoResult => {
        if (!cargoResult.success) {
            showTransportMessage('Could not get transport information', 'error');
            return;
        }
        
        const cargoInfo = cargoResult.cargo_info;
        
        // ✅ NEW: Only show exit options if transport has cargo
        if (!cargoInfo.is_transport) {
            showTransportMessage('Unit is not a transport', 'warning');
            return;
        }
        
        if (cargoInfo.current_cargo === 0) {
            showTransportMessage('Transport is empty - no units to deploy', 'warning');
            return;
        }
        
        // Transport has cargo, proceed with getting exit positions
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
                if (result.transport_info && result.transport_info.cargo_units && result.transport_info.cargo_units.length > 1) {
                    showCargoSelectionMenu(result.transport_info.cargo_units, transportX, transportY);
                }
                
                console.log(`AW_TRANSPORT: Showing ${result.valid_positions.length} exit positions for ${cargoInfo.current_cargo} cargo units`);
                showTransportMessage(`${cargoInfo.current_cargo} unit(s) ready to deploy. Alt-click blue tiles to deploy.`, 'info');
            } else {
                showTransportMessage('No valid positions to deploy units', 'info');
            }
        }).catch(error => {
            console.error('AW_TRANSPORT: Failed to get exit positions:', error);
            showTransportMessage('Failed to get exit positions', 'error');
        });
        
    }).catch(error => {
        console.error('AW_TRANSPORT: Failed to get cargo info:', error);
        showTransportMessage('Failed to get transport information', 'error');
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
    // Just call the new safe function
    safelyPerformEnhancedMovement(fromX, fromY, toX, toY);
}

// function attemptEnhancedMovement(fromX, fromY, toX, toY) {
    
//     console.log(`AW_TRANSPORT: Enhanced movement from (${fromX},${fromY}) to (${toX},${toY})`);
    
//     jsonrpc('unit_move_enhanced', {
//         from_x: fromX,
//         from_y: fromY,
//         to_x: toX,
//         to_y: toY
//     }).then(result => {
//         if (result.success) {
//             if (result.action === 'boarded_transport') {
//                 console.log(`AW_TRANSPORT: Auto-boarded transport - ${result.message}`);
//                 showTransportMessage(result.message, 'success');
//             } else {
//                 console.log(`AW_TRANSPORT: Normal movement - ${result.message}`);
//             }
            
//             // Clear selection and update board
//             clearAllTransportHighlights();
//             board.selected = null;
//             updateBoardDisplay();
//         } else {
//             console.error(`AW_TRANSPORT: Movement failed - ${result.error}`);
//             showTransportMessage(result.error, 'error');
//         }
//     }).catch(error => {
//         console.error('AW_TRANSPORT: Enhanced movement failed:', error);
//         showTransportMessage('Movement failed', 'error');
//     });
// }

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
        <button onclick="closeCargoSelectionMenu()">Cancel</button>
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

function getTileFromCanvasClick(event) {
    console.log('🎯 Getting tile from canvas click');
    
    const canvas = event.target;
    if (!canvas) {
        console.log('❌ No canvas target');
        return null;
    }
    
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Your game uses TILESIZE (should be 32 based on typical setup)
    const TILE_SIZE = TILESIZE;
    
    const tileX = Math.floor(x / TILE_SIZE);
    const tileY = Math.floor(y / TILE_SIZE);
    
    console.log(`🎯 Click position: (${x}, ${y}) -> Tile: (${tileX}, ${tileY})`);
    
    // Find the actual tile from the board using your flat array structure
    if (board && board.grid) {
        const tile = board.grid.find(t => t.x === tileX && t.y === tileY);
        if (tile) {
            console.log('✅ Found tile:', tile);
            return tile;
        } else {
            console.log(`❌ No tile found at coordinates (${tileX}, ${tileY})`);
            console.log('Available tiles:', board.grid.map(t => `(${t.x},${t.y})`).slice(0, 10)); // Show first 10 for debug
        }
    } else {
        console.log('❌ No board or board.grid available');
    }
    
    return null;
}

function handleTransportRightClick(tile, event) {
    console.log(`🖱️ RIGHT-CLICK: Tile (${tile.x}, ${tile.y})`);
    
    // Check if this tile has a transport unit
    if (tile.unit && isTransportUnit(tile.unit) && tile.unit.army === board.current_turn) {
        console.log(`🚛 RIGHT-CLICK: Transport unit found - showing exit options`);
        
        // Show transport exit options
        showTransportExitOptions(tile.x, tile.y);
        
        // Show visual feedback
        showTransportMessage('Right-clicked on transport - showing exit options', 'info');
        
        return true; // We handled it
    } else if (tile.unit) {
        console.log(`👤 RIGHT-CLICK: Non-transport unit (${tile.unit.type || 'unknown'})`);
        showTransportMessage('Right-click only works on transport units', 'warning');
    } else {
        console.log(`🔳 RIGHT-CLICK: Empty tile`);
        showTransportMessage('No unit here to deploy from', 'info');
    }
    
    return false;
}

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
    // For Two.js canvas implementation, this is handled in the rendering system
    console.log(`AW_TRANSPORT: Transport at (${transportInfo.x}, ${transportInfo.y}) has ${transportInfo.current_cargo} cargo`);
}

// Simple board update function (fallback)
function updateBoardDisplay() {
    // Call the main update function
    if (typeof update === 'function') {
        update();
    } else if (typeof rerender === 'function') {
        rerender();
    }
}

// Add this function to transport_integration.js (before the exports)
function handleTransportAltClick(tile, event) {
    console.log(`🖱️ ALT-CLICK: Tile (${tile.x}, ${tile.y})`);
    
    // Check if we're showing exit options and this is a valid exit position
    if (transportState.showingExitOptions && 
        transportState.exitPositions.some(pos => pos.x === tile.x && pos.y === tile.y)) {
        
        // Find the selected transport
        const transport = transportState.selectedTransport;
        if (transport) {
            console.log(`🚛 ALT-CLICK: Exiting cargo from transport at (${transport.x}, ${transport.y}) to (${tile.x}, ${tile.y})`);
            
            const cargoIndex = transportState.selectedCargoIndex || 0;
            attemptToExitTransport(transport.x, transport.y, tile.x, tile.y, cargoIndex);
            return true;
        }
    }
    
    // Check if this is a transport with cargo (select it and show options)
    if (tile.unit && isTransportUnit(tile.unit) && tile.unit.army === board.current_turn) {
        console.log(`🚛 ALT-CLICK: Selecting transport and showing exit options`);
        
        // Select the transport
        board.selected = tile;
        transportState.selectedTransport = tile;
        
        // Show exit options immediately
        showTransportExitOptions(tile.x, tile.y);
        
        showTransportMessage('Alt-clicked transport - showing exit options. Alt-click blue tiles to deploy.', 'info');
        return true;
    }
    
    // Regular alt-click on empty tile or non-transport
    console.log(`🔳 ALT-CLICK: Not a transport exit action`);
    showTransportMessage('Alt-click on transport to show exit options, then alt-click blue tiles to deploy', 'info');
    return false;
}

// =============================================================================
// INITIALIZATION AND EXPORTS
// =============================================================================

// Add keyboard event listener
document.addEventListener('keydown', handleKeyboardControls);

// Initialize transport state if not already defined
if (typeof window.transportState === 'undefined') {
    window.transportState = transportState;
}

// Export functions for use in other files
window.isTransportUnit = isTransportUnit;
window.canUnitBoardTransports = canUnitBoardTransports;
window.showLoadableTransports = showLoadableTransports;
window.showTransportExitOptions = showTransportExitOptions;
window.attemptToBoardTransport = attemptToBoardTransport;
window.attemptToExitTransport = attemptToExitTransport;
window.clearAllTransportHighlights = clearAllTransportHighlights;
window.showTransportMessage = showTransportMessage;
window.updateBoardDisplayWithTransports = updateBoardDisplayWithTransports;
window.handleTileClickWithTransport = handleTileClickWithTransport;
window.selectUnitWithTransportOptions = selectUnitWithTransportOptions;
window.handleRightClick = handleRightClick;
window.handleExitPositionClick = handleExitPositionClick;
window.getTileFromCanvasClick = getTileFromCanvasClick;
window.handleTransportRightClick = handleTransportRightClick;
window.handleTransportAltClick = handleTransportAltClick; 

console.log('AW_TRANSPORT: Complete transport integration system loaded successfully');