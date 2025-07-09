// transport_frontend.js - Frontend integration for transport system

// =============================================================================
// TRANSPORT STATE MANAGEMENT
// =============================================================================

let frontendTransportState = {
    selectedTransport: null,
    selectedCargo: null,
    showingLoadOptions: false,
    showingUnloadOptions: false,
    validUnloadPositions: [],
    transportInfo: null
};

// =============================================================================
// TRANSPORT SELECTION AND INFO
// =============================================================================

function selectTransportUnit(tile) {
    console.log('🚛 Selecting transport unit:', tile.unit.type);
    
    // Get detailed transport information
    jsonrpc('get_transport_info', {x: tile.x, y: tile.y}).then(result => {
        if (result.success) {
            frontendTransportState.selectedTransport = tile;
            frontendTransportState.transportInfo = result;
            
            console.log('📊 Transport info:', result);
            showTransportActionMenu(tile, result);
        } else {
            showMessage(`Failed to get transport info: ${result.error}`, 'error');
        }
    }).catch(error => {
        console.error('❌ Transport info request failed:', error);
        showMessage('Failed to get transport information', 'error');
    });
}

function showTransportActionMenu(tile, transportInfo) {
    const menu = document.createElement('div');
    menu.className = 'transport-action-menu';
    menu.style.cssText = `
        position: fixed;
        background: white;
        border: 2px solid #333;
        border-radius: 8px;
        padding: 15px;
        z-index: 1000;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        min-width: 300px;
    `;
    
    let menuHTML = `<h3>${transportInfo.unit_type} Actions</h3>`;
    
    // Movement status
    const movementStatus = transportInfo.movement_status;
    if (movementStatus.has_moved_this_turn) {
        menuHTML += '<p style="color: orange;">⚠️ Already moved this turn</p>';
    } else if (movementStatus.can_move) {
        menuHTML += '<button onclick="initiateTransportMovement()">Move Transport</button><br>';
    }
    
    // Load/Unload options
    if (movementStatus.can_load_unload) {
        const cargoInfo = transportInfo.cargo_info;
        
        if (cargoInfo.current_cargo < cargoInfo.max_capacity) {
            menuHTML += '<button onclick="showLoadOptions()">Load Unit</button><br>';
        }
        
        if (cargoInfo.current_cargo > 0) {
            menuHTML += '<button onclick="showUnloadOptions()">Unload Unit</button><br>';
        }
        
        // Show cargo status
        if (cargoInfo.current_cargo > 0) {
            menuHTML += `<p><strong>Cargo (${cargoInfo.current_cargo}/${cargoInfo.max_capacity}):</strong></p>`;
            cargoInfo.cargo_units.forEach(cargo => {
                menuHTML += `<p>• ${cargo.type} (${Math.ceil(cargo.hp/10)} HP)</p>`;
            });
        } else {
            menuHTML += `<p>Empty (0/${cargoInfo.max_capacity})</p>`;
        }
        
        // Show compatible units
        menuHTML += `<p><small>Can carry: ${transportInfo.compatible_units.join(', ')}</small></p>`;
    } else {
        menuHTML += '<p style="color: red;">Cannot load/unload (not your turn)</p>';
    }
    
    menuHTML += '<button onclick="closeTransportMenu()">Close</button>';
    menu.innerHTML = menuHTML;
    
    // Remove existing menu
    closeTransportMenu();
    
    document.body.appendChild(menu);
}

function closeTransportMenu() {
    const existingMenu = document.querySelector('.transport-action-menu');
    if (existingMenu) {
        existingMenu.remove();
    }
    
    // Clear highlights
    clearTransportHighlights();
}

// =============================================================================
// MOVEMENT INTEGRATION
// =============================================================================

function initiateTransportMovement() {
    console.log('🚶 Initiating transport movement');
    
    if (!frontendTransportState.selectedTransport) {
        showMessage('No transport selected', 'error');
        return;
    }
    
    // Check if transport can move
    const tile = frontendTransportState.selectedTransport;
    jsonrpc('can_transport_move', {x: tile.x, y: tile.y}).then(result => {
        if (result.success && result.can_move) {
            // Close menu and show movement options
            closeTransportMenu();
            showMessage('Click destination to move transport', 'info');
            
            // Enable movement mode (integrate with your existing movement system)
            if (typeof showMovementRange === 'function') {
                showMovementRange(tile.x, tile.y);
            }
            
            // Set global state for movement handling
            window.gameState = window.gameState || {};
            window.gameState.transportMovementMode = true;
            
        } else {
            showMessage(result.can_move ? 'Transport cannot move' : 'Transport already moved this turn', 'warning');
        }
    }).catch(error => {
        console.error('❌ Movement check failed:', error);
        showMessage('Failed to check movement capability', 'error');
    });
}

function executeTransportMovement(fromTile, toTile) {
    console.log(`🚛 Moving transport from (${fromTile.x},${fromTile.y}) to (${toTile.x},${toTile.y})`);
    
    jsonrpc('unit_move_enhanced', {
        from_x: fromTile.x,
        from_y: fromTile.y,
        to_x: toTile.x,
        to_y: toTile.y
    }).then(result => {
        if (result.success) {
            showMessage(result.message, 'success');
            update(); // Refresh board
            
            // Keep transport selected and show actions
            setTimeout(() => {
                const newTile = {x: toTile.x, y: toTile.y, unit: fromTile.unit};
                selectTransportUnit(newTile);
            }, 500);
            
        } else {
            showMessage(`Movement failed: ${result.error}`, 'error');
        }
        
        // Clear movement mode
        window.gameState.transportMovementMode = false;
        
    }).catch(error => {
        console.error('❌ Transport movement failed:', error);
        showMessage('Transport movement failed', 'error');
        window.gameState.transportMovementMode = false;
    });
}

// =============================================================================
// LOADING SYSTEM
// =============================================================================

function showLoadOptions() {
    console.log('📦 Showing load options');
    
    closeTransportMenu();
    frontendTransportState.showingLoadOptions = true;
    
    // Highlight adjacent units that can be loaded
    if (frontendTransportState.selectedTransport && frontendTransportState.transportInfo) {
        const transport = frontendTransportState.selectedTransport;
        const compatibleUnits = frontendTransportState.transportInfo.compatible_units;
        
        highlightLoadableUnits(transport, compatibleUnits);
        showMessage('Click adjacent unit to load into transport', 'info');
    }
}

function highlightLoadableUnits(transportTile, compatibleUnits) {
    clearTransportHighlights();
    
    const directions = [[0,1], [0,-1], [1,0], [-1,0]];
    
    directions.forEach(([dx, dy]) => {
        const x = transportTile.x + dx;
        const y = transportTile.y + dy;
        
        if (isValidPosition(x, y)) {
            const tile = getTileAt(x, y);
            if (tile && tile.unit && compatibleUnits.includes(tile.unit.type)) {
                highlightTile(x, y, 'loadable-unit');
            }
        }
    });
}

function attemptLoadUnit(cargoTile) {
    console.log(`📦 Attempting to load ${cargoTile.unit.type} into transport`);
    
    if (!frontendTransportState.selectedTransport) {
        showMessage('No transport selected', 'error');
        return;
    }
    
    const transport = frontendTransportState.selectedTransport;
    
    jsonrpc('load_transport_unit', {
        transport_x: transport.x,
        transport_y: transport.y,
        cargo_x: cargoTile.x,
        cargo_y: cargoTile.y
    }).then(result => {
        if (result.success) {
            showMessage(result.message, 'success');
            update(); // Refresh board
            
            // Clear state
            frontendTransportState.showingLoadOptions = false;
            clearTransportHighlights();
            
        } else {
            showMessage(`Loading failed: ${result.error}`, 'error');
        }
    }).catch(error => {
        console.error('❌ Load unit failed:', error);
        showMessage('Failed to load unit', 'error');
    });
}

// =============================================================================
// UNLOADING SYSTEM
// =============================================================================

function showUnloadOptions() {
    console.log('📤 Showing unload options');
    
    if (!frontendTransportState.selectedTransport) {
        showMessage('No transport selected', 'error');
        return;
    }
    
    closeTransportMenu();
    frontendTransportState.showingUnloadOptions = true;
    
    const transport = frontendTransportState.selectedTransport;
    
    jsonrpc('get_valid_unload_positions', {x: transport.x, y: transport.y}).then(result => {
        if (result.success) {
            frontendTransportState.validUnloadPositions = result.valid_positions;
            
            // Highlight valid unload positions
            result.valid_positions.forEach(pos => {
                highlightTile(pos.x, pos.y, 'unload-position');
            });
            
            showMessage(`${result.valid_positions.length} positions available. Click to unload.`, 'info');
            
        } else {
            showMessage(`Failed to get unload positions: ${result.error}`, 'error');
        }
    }).catch(error => {
        console.error('❌ Get unload positions failed:', error);
        showMessage('Failed to get unload positions', 'error');
    });
}

function attemptUnloadUnit(unloadTile, cargoIndex = 0) {
    console.log(`📤 Attempting to unload to (${unloadTile.x},${unloadTile.y})`);
    
    if (!frontendTransportState.selectedTransport) {
        showMessage('No transport selected', 'error');
        return;
    }
    
    const transport = frontendTransportState.selectedTransport;
    
    jsonrpc('unload_transport_unit', {
        transport_x: transport.x,
        transport_y: transport.y,
        unload_x: unloadTile.x,
        unload_y: unloadTile.y,
        cargo_index: cargoIndex
    }).then(result => {
        if (result.success) {
            showMessage(result.message, 'success');
            update(); // Refresh board
            
            // Clear state
            frontendTransportState.showingUnloadOptions = false;
            frontendTransportState.validUnloadPositions = [];
            clearTransportHighlights();
            
        } else {
            showMessage(`Unloading failed: ${result.error}`, 'error');
        }
    }).catch(error => {
        console.error('❌ Unload unit failed:', error);
        showMessage('Failed to unload unit', 'error');
    });
}

// =============================================================================
// HIGHLIGHTING SYSTEM
// =============================================================================

function highlightTile(x, y, className) {
    // Store highlights for rendering system
    if (!window.transportHighlights) {
        window.transportHighlights = [];
    }
    
    window.transportHighlights.push({
        x: x,
        y: y,
        type: className
    });
    
    console.log(`🎯 Highlighting tile (${x}, ${y}) as ${className}`);
}

function clearTransportHighlights() {
    window.transportHighlights = [];
    frontendTransportState.showingLoadOptions = false;
    frontendTransportState.showingUnloadOptions = false;
    frontendTransportState.validUnloadPositions = [];
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

function isValidPosition(x, y) {
    return x >= 0 && y >= 0 && x < board.width && y < board.height;
}

function getTileAt(x, y) {
    // Adapt this to your board structure
    if (board && board.grid) {
        const index = y * board.width + x;
        return board.grid[index];
    }
    return null;
}

function isTransportUnit(unit) {
    if (!unit || !unit.type) return false;
    const transportTypes = ['APC', 'TCOPTER', 'LANDER', 'BLACKBOAT', 'CRUISER', 'CARRIER'];
    return transportTypes.includes(unit.type);
}

function showMessage(message, type = 'info') {
    // Create or update message display
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
        if (messageDiv.style.display !== 'none') {
            messageDiv.style.display = 'none';
        }
    }, 3000);
}

// =============================================================================
// CLICK HANDLER INTEGRATION
// =============================================================================

function handleTransportClick(tile, event) {
    console.log('🖱️ Transport click handler:', tile);
    
    // IMPORTANT: Don't intercept alt-clicks or ctrl-clicks
    if (event && (event.altKey || event.ctrlKey)) {
        console.log('🔄 Alt/Ctrl-click detected - using existing transport system');
        return false; // Let existing system handle cargo loading
    }
    
    // IMPORTANT: Only handle clicks on TRANSPORT units, not cargo units
    if (!tile.unit || !isTransportUnit(tile.unit)) {
        console.log('🔄 Not a transport unit - letting existing system handle');
        return false; // Let existing system handle non-transport units
    }
    
    // Handle different click modes (only for transport units)
    if (frontendTransportState.showingLoadOptions) {
        // Loading mode - check if clicked unit can be loaded
        if (tile.unit && frontendTransportState.transportInfo && 
            frontendTransportState.transportInfo.compatible_units.includes(tile.unit.type)) {
            attemptLoadUnit(tile);
        } else {
            showMessage('Cannot load this unit type', 'warning');
        }
        return true;
    }
    
    if (frontendTransportState.showingUnloadOptions) {
        // Unloading mode - check if clicked position is valid
        const isValidUnload = frontendTransportState.validUnloadPositions.some(pos => 
            pos.x === tile.x && pos.y === tile.y
        );
        
        if (isValidUnload) {
            attemptUnloadUnit(tile);
        } else {
            showMessage('Cannot unload at this position', 'warning');
        }
        return true;
    }
    
    if (window.gameState && window.gameState.transportMovementMode) {
        // Movement mode - execute transport movement
        if (frontendTransportState.selectedTransport) {
            executeTransportMovement(frontendTransportState.selectedTransport, tile);
        }
        return true;
    }
    
    // Normal transport selection (only for transport units)
    console.log('🚛 Selecting transport unit:', tile.unit.type);
    selectTransportUnit(tile);
    return true;
}

// =============================================================================
// INTEGRATION WITH EXISTING TRANSPORT SYSTEM
// =============================================================================

// Bridge with existing transport integration
function integrateWithExistingSystem() {
    console.log('🔗 Integrating new transport system with existing handlers');
    
    // Override or extend existing functions if they exist
    if (typeof handleTileClickWithTransport === 'function') {
        // Store reference to old function
        window.originalHandleTileClickWithTransport = handleTileClickWithTransport;
        
        // Create new integrated function that preserves alt-click behavior
        window.handleTileClickWithTransport = function(tile, event) {
            // PRIORITY: For alt-clicks and ctrl-clicks, ALWAYS use original system
            if (event && (event.altKey || event.ctrlKey)) {
                console.log('🔄 Alt/Ctrl-click: Using original transport system');
                return window.originalHandleTileClickWithTransport(tile, event);
            }
            
            // For regular clicks on transports, try new system first
            if (tile.unit && isTransportUnit(tile.unit)) {
                if (window.transportSystem && window.transportSystem.handleTransportClick(tile, event)) {
                    return true;
                }
            }
            
            // Fall back to original system for other cases
            return window.originalHandleTileClickWithTransport(tile, event);
        };
        
        console.log('✅ Integrated with existing handleTileClickWithTransport (preserving alt/ctrl-click)');
    }
    
    // Keep the rest of the integration unchanged
    if (typeof selectUnitWithTransportOptions === 'function') {
        window.originalSelectUnitWithTransportOptions = selectUnitWithTransportOptions;
        
        window.selectUnitWithTransportOptions = function(tile) {
            // Use new transport selection for transport units
            if (tile.unit && isTransportUnit(tile.unit)) {
                selectTransportUnit(tile);
                return;
            }
            
            // Fall back to original for non-transport units
            window.originalSelectUnitWithTransportOptions(tile);
        };
        
        console.log('✅ Integrated with existing selectUnitWithTransportOptions');
    }
}

// Auto-integrate when this script loads
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(integrateWithExistingSystem, 100); // Small delay to ensure other scripts load
});

// Also integrate immediately if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', integrateWithExistingSystem);
} else {
    integrateWithExistingSystem();
}

// =============================================================================
// INITIALIZATION
// =============================================================================

console.log('🚛 Transport frontend system loaded');

// Export functions for global use
window.transportSystem = {
    selectTransportUnit,
    handleTransportClick: (tile, event) => handleTransportClick(tile, event),
    closeTransportMenu,
    clearTransportHighlights,
    isTransportUnit
};

