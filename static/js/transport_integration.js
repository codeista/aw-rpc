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
    selectedCargoIndex: 0,
    // SELECTION PRESERVATION
    preservedSelection: null,  // Store original selection during transport operations
    preserveSelection: false   // Flag to indicate if we should preserve selection
};

// =============================================================================
// MAIN TRANSPORT INTEGRATION
// =============================================================================

function handleTileClickWithTransport(tile, event) {

        // ========================================================================
    // PRIORITY 1: PRODUCTION BUILDINGS (CRITICAL FIX)
    // ========================================================================
    if ((tile.mapTile.type === 'FACTORY' || 
         tile.mapTile.type === 'AIRPORT' || 
         tile.mapTile.type === 'PORT') &&
        tile.mapTile.army === board.current_turn &&
        !tile.unit) {
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
            return false; // Let frontend handle unload
        }
        if (frontendTransportState.showingLoadOptions) {
            return false; // Let frontend handle load
        }
    }
    
    // CRITICAL: Don't interfere with alt-clicks
    if (event && event.altKey) {
        return false; // Let alt-click system handle
    }
    
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
            
            attemptToBoardTransport(selectedTile.x, selectedTile.y, tile.x, tile.y);
            return true; // We handled it
        }
        
        // Scenario 2: Enhanced movement (only if not conflicting)
        if (!tile.unit && tile.can_be_moved_to) {
            safelyPerformEnhancedMovement(selectedTile.x, selectedTile.y, tile.x, tile.y);
            return true; // We handled it
        }
        
        // Scenario 3: Selecting a different unit
        if (tile.unit && tile.unit.army === board.current_turn) {
            selectUnitWithTransportOptions(tile);
            return true; // We handled it
        }
    } else {
        // No unit selected - select this unit if it belongs to current player
        if (tile.unit && tile.unit.army === board.current_turn) {
            selectUnitWithTransportOptions(tile);
            return true; // We handled it
        }
    }
    
    return false; // We didn't handle it
}

function safelyPerformEnhancedMovement(fromX, fromY, toX, toY) {
    
    // ✅ FIX: Find unit using the flat array structure
    const fromTile = board.grid.find(t => t.x === fromX && t.y === fromY);
    if (!fromTile || !fromTile.unit) {
        return;
    }
    
    if (!fromTile.unit.can_move) {
        showTransportMessage('Unit has already moved this turn', 'warning');
        return;
    }
    
    // ✅ FIX: Use regular movement for transports (much more reliable)
    if (isTransportUnit(fromTile.unit)) {
        jsonrpc('unit_move', {
            x: fromX,
            y: fromY,
            x2: toX,
            y2: toY
        }).then(result => {
            if (result.success || !result.error) {
                
                // ✅ FIX: Update selection to new position using flat array
                const newTile = board.grid.find(t => t.x === toX && t.y === toY);
                if (newTile) {
                    board.selected = newTile;
                    // Update preserved selection if we're preserving
                    if (transportState.preserveSelection) {
                        transportState.preservedSelection.x = toX;
                        transportState.preservedSelection.y = toY;
                    }
                    // CRITICAL: Update transport state if this was the selected transport
                    if (transportState.selectedTransport && 
                        transportState.selectedTransport.x === fromX && 
                        transportState.selectedTransport.y === fromY) {
                        transportState.selectedTransport = newTile;
                        console.log('🚛 Updated selected transport position:', fromX, fromY, '->', toX, toY);
                    }
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
            showTransportMessage(result.message || 'Unit moved successfully', 'success');
            clearAllTransportHighlights();
            updateBoardDisplay();
        } else {
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
    
    jsonrpc('cargo_board_transport', {
        cargo_x: cargoX,
        cargo_y: cargoY,
        transport_x: transportX,
        transport_y: transportY
    }).then(result => {
            
    if (result.success) {

        // Show success message
        showTransportMessage(result.message, 'success');
        
        // Clear transport highlights
        clearAllTransportHighlights();
        
        // ✅ FIX: Find transport tile using flat array structure
        const transportTile = board.grid.find(t => t.x === transportX && t.y === transportY);
        if (transportTile && transportTile.unit) {
            board.selected = transportTile;
            
            // Show movement range for the transport
            if (typeof showMovementRange === 'function') {
                showMovementRange(transportX, transportY);
            }
        } else {
            board.selected = null;
        }
        
        // Update board display - force fresh data from server
        updateBoardDisplay();
        
        // Also force a complete rerender to ensure cargo icons update
        setTimeout(() => {
            if (typeof update === 'function') {
                update();
            }
        }, 100);
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
            
        }
    }).catch(error => {
        console.error('AW_TRANSPORT: Failed to get loadable transports:', error);
    });
}

// =============================================================================
// TRANSPORT EXITING
// =============================================================================

function showTransportExitOptions(transportX, transportY) {
    console.log('🔍 Getting cargo info for transport at:', transportX, transportY);
    
    // ✅ NEW: First check if transport has cargo
    console.log('🔄 Calling get_cargo_info RPC for transport at:', transportX, transportY);
    jsonrpc('get_cargo_info', {x: transportX, y: transportY}).then(cargoResult => {
        console.log('📦 Cargo info result:', cargoResult);
        if (!cargoResult.success) {
            console.error('❌ get_cargo_info failed:', cargoResult.error);
            showTransportMessage(`Could not get transport info: ${cargoResult.error || 'Unknown error'}`, 'error');
            return;
        }
        
        const cargoInfo = cargoResult.cargo_info;
        console.log('📋 Cargo info details:', cargoInfo);
        
        // ✅ NEW: Only show exit options if transport has cargo
        if (!cargoInfo.is_transport) {
            console.log('❌ Unit is not a transport');
            showTransportMessage('Unit is not a transport', 'warning');
            return;
        }
        
        if (cargoInfo.current_cargo === 0) {
            console.log('❌ Transport is empty, current_cargo:', cargoInfo.current_cargo);
            showTransportMessage('Transport is empty - no units to deploy', 'warning');
            return;
        }
        
        console.log('✅ Transport has cargo:', cargoInfo.current_cargo, 'units');
        
        // Transport has cargo, proceed with getting exit positions
        console.log('🔍 Getting exit positions for transport...');
        jsonrpc('get_exit_positions', {
            transport_x: transportX,
            transport_y: transportY
        }).then(result => {
            console.log('📍 Exit positions result:', result);
            if (result.success && result.valid_positions.length > 0) {
                console.log('✅ Found', result.valid_positions.length, 'exit positions:', result.valid_positions);
                transportState.exitPositions = result.valid_positions;
                transportState.showingExitOptions = true;
                
                // Highlight exit positions in blue
                console.log('🎯 Highlighting exit positions...');
                result.valid_positions.forEach(pos => {
                    console.log('  Highlighting position:', pos.x, pos.y);
                    highlightTile(pos.x, pos.y, 'exit-position');
                });
                
                // Show cargo selection UI if multiple cargo units
                if (result.transport_info && result.transport_info.cargo_units && result.transport_info.cargo_units.length > 1) {
                    console.log('🎮 Multiple cargo units, showing selection menu');
                    showCargoSelectionMenu(result.transport_info.cargo_units, transportX, transportY);
                }
                
                showTransportMessage(`${cargoInfo.current_cargo} unit(s) ready to deploy. Alt-click blue tiles to deploy.`, 'info');
            } else {
                console.log('❌ No valid exit positions found');
                showTransportMessage('No valid positions to deploy units', 'info');
            }
        }).catch(error => {
            console.error('❌ Error getting exit positions:', error);
            showTransportMessage('Failed to get exit positions', 'error');
        });
        
    }).catch(error => {
        console.error('❌ get_cargo_info RPC call failed:', error);
        console.error('❌ Error details:', error.message, error.stack);
        showTransportMessage(`RPC call failed: ${error.message || 'Unknown error'}`, 'error');
    });
}

function attemptToExitTransport(transportX, transportY, exitX, exitY, cargoIndex = 0) {
    
    jsonrpc('cargo_exit_transport', {
        transport_x: transportX,
        transport_y: transportY,
        exit_x: exitX,
        exit_y: exitY,
        cargo_index: cargoIndex
    }).then(result => {
        console.log('🚛 Unload result:', result);
        if (result.success) {
            
            // Show success message
            showTransportMessage(result.message, 'success');
            
            // Store transport position before clearing state
            const originalTransportX = transportX;
            const originalTransportY = transportY;
            
            // CRITICAL: Force clear all highlights after successful unload
            transportState.showingExitOptions = false; // Clear the flag first
            transportState.showingBoardingOptions = false;
            window.transportHighlights = []; // Force clear highlights array
            transportState.loadableTransports = [];
            transportState.exitPositions = [];
            transportState.selectedTransport = null;
            
            // Restore preserved selection instead of clearing
            restorePreservedSelection();
            
            console.log('🧹 Cleared all transport highlights and state after successful unload');
            
            // Update board display - force fresh data from server
            updateBoardDisplay();
            
            // Force multiple board updates to ensure cargo icons disappear
            setTimeout(() => {
                console.log('🔄 Forcing first board update after unload...');
                if (typeof update === 'function') {
                    update();
                }
                
                // Force a second update after a short delay
                setTimeout(() => {
                    console.log('🔄 Forcing second board update...');
                    if (typeof update === 'function') {
                        update();
                    }
                    
                    // Additional debug and manual cargo clearing
                    setTimeout(() => {
                        const updatedTile = board.grid.find(t => t.x === originalTransportX && t.y === originalTransportY);
                        if (updatedTile && updatedTile.unit) {
                            // MANUAL CARGO CLEARING: Force the client unit to have empty cargo
                            if (updatedTile.unit.cargo) {
                                updatedTile.unit.cargo = [];
                            }
                            if (updatedTile.unit.status && updatedTile.unit.status.cargo) {
                                updatedTile.unit.status.cargo = [];
                            }
                            
                            const cargoCount = getCargoCountForRender(updatedTile.unit);
                            console.log('🚛 Post-unload cargo count check:', {
                                position: `${originalTransportX},${originalTransportY}`,
                                cargoCount: cargoCount,
                                manuallyCleared: true
                            });
                            
                            // Force one final render
                            if (typeof rerender === 'function') {
                                rerender();
                            }
                        }
                    }, 300);
                }, 200);
            }, 100);
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
    
}

function clearAllTransportHighlights(force = false) {
    // Don't clear if we're currently showing exit options (preserve blue highlights)
    // unless force is true
    if (transportState.showingExitOptions && !force) {
        console.log('🚧 Prevented clearing highlights - exit options are showing');
        return;
    }
    
    window.transportHighlights = [];
    transportState.loadableTransports = [];
    transportState.exitPositions = [];
    transportState.showingExitOptions = false;
    transportState.showingBoardingOptions = false;
    
    // CRITICAL FIX: Force re-render to actually remove visual highlights
    if (typeof rerender === 'function') {
        rerender();
    } else if (typeof two !== 'undefined') {
        // Force Two.js update to clear visual highlights
        two.update();
    }
    
    console.log('🧹 Cleared all transport highlights and forced re-render');
}

// =============================================================================
// SELECTION PRESERVATION SYSTEM
// =============================================================================

function preserveCurrentSelection() {
    if (board.selected) {
        transportState.preservedSelection = {
            x: board.selected.x,
            y: board.selected.y,
            unit: board.selected.unit
        };
        transportState.preserveSelection = true;
        console.log('💾 Preserved selection:', transportState.preservedSelection);
    }
}

function restorePreservedSelection() {
    if (transportState.preserveSelection && transportState.preservedSelection) {
        // Find the tile at the preserved coordinates
        const restoredTile = board.grid.find(t => 
            t.x === transportState.preservedSelection.x && 
            t.y === transportState.preservedSelection.y
        );
        
        if (restoredTile) {
            board.selected = restoredTile;
            console.log('🔄 Restored selection to:', restoredTile.x, restoredTile.y);
        } else {
            console.log('⚠️ Could not restore selection - tile not found');
            board.selected = null;
        }
        
        // Clear preservation state
        transportState.preservedSelection = null;
        transportState.preserveSelection = false;
    }
}

function clearOnlyHighlights() {
    // Clear just the visual highlights without affecting state
    window.transportHighlights = [];
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
        cargoButton.textContent = `${cargo.type} (HP: ${cargo.hp})`;
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
        
        showTransportExitOptions(tile.x, tile.y);
    }
}

// Handle exit position clicks
function handleExitPositionClick(tile) {
    if (transportState.showingExitOptions && 
        transportState.exitPositions.some(pos => pos.x === tile.x && pos.y === tile.y)) {
        
        const transport = transportState.selectedTransport;
        const cargoIndex = transportState.selectedCargoIndex || 0;
        
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
            clearAllTransportHighlights(true); // Force clear everything
            showTransportMessage('Transport actions cancelled', 'info');
            break;
    }
}

// =============================================================================
// INTEGRATION WITH EXISTING GAME SYSTEMS
// =============================================================================

function getTileFromCanvasClick(event) {
    
    const canvas = event.target;
    if (!canvas) {
        return null;
    }
    
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Your game uses TILESIZE (should be 32 based on typical setup)
    const TILE_SIZE = TILESIZE;
    
    const tileX = Math.floor(x / TILE_SIZE);
    const tileY = Math.floor(y / TILE_SIZE);
    // Find the actual tile from the board using your flat array structure
    if (board && board.grid) {
        const tile = board.grid.find(t => t.x === tileX && t.y === tileY);
        if (tile) {
            return tile;
        } else {
        }
    } else {
    }
    
    return null;
}

function handleTransportRightClick(tile, event) {
    
    console.log('🔧 Right-click debug:', {
        hasGameState: !!window.gameState,
        hasSelectedUnit: !!(window.gameState && window.gameState.selectedUnit),
        selectedUnit: window.gameState?.selectedUnit,
        clickedTile: tile,
        clickedUnit: tile.unit
    });
    
    // FIRST: Check for Black Boat repair scenario
    if (window.gameState && window.gameState.selectedUnit && tile.unit) {
        const selectedTile = window.gameState.selectedUnit;
        const selectedUnit = selectedTile.unit || selectedTile; // Handle both tile and unit objects
        
        // Get position - might be on tile or unit
        const selectedX = selectedTile.x || selectedUnit.x;
        const selectedY = selectedTile.y || selectedUnit.y;
        
        // Check if the selected unit is a Black Boat
        const isBlackBoat = selectedUnit.type === 'BLACKBOAT' || selectedUnit.type === 'BLACK_BOAT';
        
        // Check if clicked unit is adjacent to selected unit
        const distance = Math.abs(selectedX - tile.x) + Math.abs(selectedY - tile.y);
        const isAdjacent = distance === 1;
        
        // Check if both units are on the same team
        const sameTeam = selectedUnit.army === tile.unit.army;
        
        // Get HP from the correct location (might be in status.hp)
        const targetHP = tile.unit.hp || tile.unit.status?.hp || 100;
        const selectedHP = selectedUnit.hp || selectedUnit.status?.hp || 100;
        
        console.log('🔧 Repair check:', {
            selectedTile,
            selectedUnit,
            selectedX,
            selectedY,
            isBlackBoat,
            distance,
            isAdjacent,
            sameTeam,
            selectedHP,
            targetUnit: tile.unit,
            targetHP,
            targetStatus: tile.unit.status,
            targetHPLow: targetHP < 100,
            willShowMenu: isBlackBoat && isAdjacent && sameTeam && (targetHP <= 90 || true)  // Show for repair or resupply
        });
        
        // Check if we should show context menu for repair or resupply
        const canRepair = isBlackBoat && targetHP <= 90;  // Can only repair up to 10 visual HP (91-100 actual)
        const isAPC = selectedUnit.type === 'APC';
        const canResupply = (isBlackBoat || isAPC);  // Can always resupply regardless of HP
        
        if (isAdjacent && sameTeam && (canRepair || canResupply)) {
            console.log('🔧 Showing repair/resupply context menu', {
                canRepair,
                canResupply,
                isBlackBoat,
                isAPC,
                targetHP
            });
            // Show context menu for repair and/or resupply
            if (typeof showUnitContextMenu === 'function') {
                showUnitContextMenu(event.pageX, event.pageY, selectedUnit, tile.unit);
                return true;
            } else {
                console.error('showUnitContextMenu function not found');
            }
        }
    }
    
    // SECOND: Check if this tile has a transport unit for cargo operations
    if (tile.unit && isTransportUnit(tile.unit) && tile.unit.army === board.current_turn) {
        
        // Show transport exit options
        showTransportExitOptions(tile.x, tile.y);
        
        // Show visual feedback
        showTransportMessage('Right-clicked on transport - showing exit options', 'info');
        
        return true; // We handled it
    } else if (tile.unit) {
        showTransportMessage('Right-click only works on transport units or for Black Boat repair', 'warning');
    } else {
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
    console.log('🔄 Alt-click detected on tile:', tile.x, tile.y, tile.unit ? tile.unit.type : 'no unit');
    
    // Check if we're showing exit options and this is a valid exit position
    if (transportState.showingExitOptions && 
        transportState.exitPositions.some(pos => pos.x === tile.x && pos.y === tile.y)) {
        
        console.log('📍 Clicking on exit position');
        // Find the selected transport
        const transport = transportState.selectedTransport;
        if (transport) {
            
            const cargoIndex = transportState.selectedCargoIndex || 0;
            attemptToExitTransport(transport.x, transport.y, tile.x, tile.y, cargoIndex);
            return true;
        }
    }
    
    // Check if this is a transport with cargo (select it and show options)
    if (tile.unit && isTransportUnit(tile.unit) && tile.unit.army === board.current_turn) {
        console.log('🚛 Alt-clicked on transport unit:', tile.unit.type);
        console.log('🔍 Transport details:', { x: tile.x, y: tile.y, army: tile.unit.army, currentTurn: board.current_turn });
        
        // Preserve current selection before changing it
        preserveCurrentSelection();
        
        // Select the transport
        board.selected = tile;
        transportState.selectedTransport = tile;
        
        // Show exit options immediately
        showTransportExitOptions(tile.x, tile.y);
        
        showTransportMessage('Alt-clicked transport - showing exit options. Alt-click blue tiles to deploy.', 'info');
        return true;
    }
    
    // Alternative: Check if we're alt-clicking near a transport that was just moved
    // Look for nearby transports that might have cargo
    if (!tile.unit) {
        const nearbyTransports = board.grid.filter(t => 
            t.unit && 
            isTransportUnit(t.unit) && 
            t.unit.army === board.current_turn &&
            Math.abs(t.x - tile.x) <= 1 && Math.abs(t.y - tile.y) <= 1
        );
        
        if (nearbyTransports.length === 1) {
            const transport = nearbyTransports[0];
            console.log('🚛 Found nearby transport at:', transport.x, transport.y, '- checking for cargo');
            
            // Check if this transport has cargo and can unload here
            jsonrpc('get_cargo_info', {x: transport.x, y: transport.y}).then(cargoResult => {
                if (cargoResult.success && cargoResult.cargo_info.current_cargo > 0) {
                    console.log('🚛 Nearby transport has cargo - showing exit options');
                    board.selected = transport;
                    transportState.selectedTransport = transport;
                    showTransportExitOptions(transport.x, transport.y);
                    showTransportMessage('Found nearby loaded transport - showing exit options.', 'info');
                }
            });
            return true;
        }
    }
    
    console.log('❌ Alt-click not handled - no valid transport or exit position');
    return false;
    
    // Regular alt-click on empty tile or non-transport
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

// =============================================================================
// INTEGRATION WITH NEW CLICK HANDLER SYSTEM
// =============================================================================

// Register transport handlers with the new centralized system
function registerTransportHandlers() {
    if (!window.clickHandler) {
        console.warn('Click handler system not available yet, retrying...');
        setTimeout(registerTransportHandlers, 500);
        return;
    }
    
    // Transport exit position click handler
    window.clickHandler.register('contextual', {
        name: 'transport-exit-position',
        priority: 1,
        condition: (tile, event) => {
            return transportState.showingExitOptions &&
                   transportState.exitPositions.some(pos => pos.x === tile.x && pos.y === tile.y);
        },
        handle: (tile, event) => {
            handleExitPositionClick(tile);
            return true;
        }
    });
    
    // Transport boarding handler
    window.clickHandler.register('contextual', {
        name: 'transport-boarding',
        priority: 2,
        condition: (tile, event) => {
            return board.selected?.unit &&
                   canUnitBoardTransports(board.selected.unit) &&
                   tile.unit &&
                   isTransportUnit(tile.unit) &&
                   tile.unit.army === board.selected.unit.army &&
                   tile.x !== board.selected.x && tile.y !== board.selected.y;
        },
        handle: (tile, event) => {
            attemptToBoardTransport(board.selected.x, board.selected.y, tile.x, tile.y);
            return true;
        }
    });
    
    // Transport selection with cargo handler
    window.clickHandler.register('selection', {
        name: 'transport-with-cargo',
        priority: 1,
        condition: (tile, event) => {
            return tile.unit &&
                   tile.unit.army === board.current_turn &&
                   isTransportUnit(tile.unit) &&
                   tile.unit.cargo?.length > 0;
        },
        handle: (tile, event) => {
            selectUnitWithTransportOptions(tile);
            return true;
        }
    });
    
    console.log('✅ Transport handlers registered with centralized click system');
}

// Start registration process
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', registerTransportHandlers);
} else {
    registerTransportHandlers();
} 

