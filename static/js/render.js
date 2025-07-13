//
// Setup
//

// constants
const TILESIZE = 16;

// Tileset management functions
function getSelectedTerrainTileset() {
    const select = document.getElementById('terrainTilesetSelect');
    if (!select) return '/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png'; // fallback
    
    switch (select.value) {
        case 'transparent':
            return '/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png';
        case 'normal':
            return '/static/img/Advance_Wars_Dual_Strike_Tileset_Normal.png';
        case 'blackhole_transparent':
            return '/static/img/aw2_blackhole_tileset_normal_transparent.png';
        case 'blackhole_normal':
            return '/static/img/aw2_blackhole_tileset_normal.png';
        default:
            return '/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png';
    }
}

function getSelectedUnitTileset() {
    const select = document.getElementById('unitTilesetSelect');
    if (!select) return '/static/img/aw2_blackhole_units_map_transparent.png'; // fallback
    
    switch (select.value) {
        case 'blackhole_transparent':
            return '/static/img/aw2_blackhole_units_map_transparent.png';
        case 'blackhole_normal':
            return '/static/img/aw2_blackhole_units_map.png';
        default:
            return '/static/img/aw2_blackhole_units_map_transparent.png';
    }
}

// Transport visual constants
const TRANSPORT_HIGHLIGHT_OPACITY = 0.3;
const TRANSPORT_BORDER_WIDTH = 2;

// globals
var token = document.getElementById('draw').getAttribute('x-token');
var board = null;
var two = null;

// Initialize game state for combat system
if (!window.gameState) {
    window.gameState = {
        selectedUnit: null,
        movementPhase: false,
        showingAttackTargets: false,
        attackHighlights: []
    };
}

// Transport rendering globals
var transportHighlightGroup = null;

// update board data
update();

// init controls
var buttonrerender = document.getElementsByClassName('buttonrerender');
buttonrerender.onclick = rerender;
var inputshowmap = document.getElementById('inputshowmap');
inputshowmap.onchange = rerender;
var buttonendturn = document.getElementsByClassName('buttonendturn');
buttonendturn.onclick = armyEndTurn;
var buttonendgame = document.getElementsByClassName('buttonendgame');
buttonendgame.onclick = endGame;
var buttonchat = document.getElementById('buttonchat');
buttonchat.onclick = chat;
var inputchat = document.getElementById('inputchat');
inputchat.onkeypress = chat;
var inputshowchat = document.getElementById('inputshowchat');
inputshowchat.onchange = showChat;
var inputshowjson = document.getElementById('inputshowjson');
inputshowjson.onchange = showJson;

// init socket.io
setTimeout(function() {
    const socket = io('/');

    socket.on('connect', () => {
        console.log('socket connected');
        socket.emit('game', token);
    });
    socket.on('disconnect', () => {
        console.log('socket disconnected');
    });
    socket.on('update', (msg) => {
        update();
    });
    socket.on('message', (msg) => {
        var textareachat = document.getElementById('textareachat');
        textareachat.value = textareachat.value + msg + '\n';
        textareachat.scrollTop = textareachat.scrollHeight;
    });
}, 100);

//
// Helper methods
//

function isTransportUnitForRender(unit) {
    if (!unit || !unit.type) return false;
    const transportTypes = ['APC', 'LANDER', 'TCOPTER', 'CRUISER', 'CARRIER', 'BLACKBOAT'];
    return transportTypes.includes(unit.type);
}

function getCargoCountForRender(unit) {
    if (!unit) return 0;
    // Method 1: Check unit.cargo array
    if (unit.cargo && Array.isArray(unit.cargo)) {
        // Count non-null cargo slots
        const actualCargoCount = unit.cargo.filter(cargo => 
            cargo !== null && 
            cargo !== undefined && 
            typeof cargo === 'object'
        ).length;
        
        return actualCargoCount;
    }
    
    // Method 2: Check unit.status.cargo array  
    if (unit.status && unit.status.cargo && Array.isArray(unit.status.cargo)) {
        const actualCargoCount = unit.status.cargo.filter(cargo => 
            cargo !== null && 
            cargo !== undefined && 
            typeof cargo === 'object'
        ).length;
        
        return actualCargoCount;
    }
    
    // Method 3: Check for explicit cargo count property
    if (typeof unit.cargo_count === 'number') {
        return unit.cargo_count;
    }
    
    // Method 4: Check status cargo count
    if (unit.status && typeof unit.status.cargo_count === 'number') {
        return unit.status.cargo_count;
    }
    
    return 0;
}

function uuidv4() {
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
}

async function rerender() {
    console.time('rerender');
    if (two) {
        two.clear();
        await createScene();
        two.update();
    } else {
        console.error('Two.js not initialized - calling update()');
        update();
    }
    console.timeEnd('rerender');
}

//
// JSON-RPC methods
//

function jsonrpc(method, params, callback) {
    if (!params) params = {};
    params.token = token;
    console.log('rpc::', method, params);
    
    // If no callback provided, return a Promise (for async/await)
    if (!callback) {
        return new Promise((resolve, reject) => {
            var xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function() {
                if (this.readyState === XMLHttpRequest.DONE) {
                    if (this.status === 200) {
                        try {
                            var response = JSON.parse(this.responseText);
                            if (response.error) {
                                reject(new Error(response.error.message || 'RPC Error'));
                            } else {
                                resolve(response.result);
                            }
                        } catch (e) {
                            reject(new Error('Invalid JSON response'));
                        }
                    } else {
                        reject(new Error(`HTTP ${this.status}: ${this.statusText}`));
                    }
                }
            };
            xhr.open('POST', '/api');
            xhr.setRequestHeader('Content-Type', 'application/json');
            var data = {'jsonrpc': '2.0', 'method': method, 'params': params, 'id': uuidv4()};
            xhr.send(JSON.stringify(data));
        });
    }
    
    // Original callback-based behavior (for existing code)
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (this.readyState === XMLHttpRequest.DONE) {
            if (this.status === 200) {
                if (callback) {
                    callback(JSON.parse(this.responseText).result);
                }
            } else {
                console.error('error calling "' + method + '"');
            }
        }
    };
    xhr.open('POST', '/api');
    xhr.setRequestHeader('Content-Type', 'application/json');
    var data = {'jsonrpc': '2.0', 'method': method, 'params': params, 'id': uuidv4()};
    xhr.send(JSON.stringify(data));
}

function update() {
    console.log('Update function called');
    jsonrpc('game_board', {}, async function(res) {
        console.log('Game board response received:', res);
        // Preserve the current selection before updating board
        var previousSelection = board ? board.selected : null;

                // Update board data
        board = res;
        
        // Update status bar if function exists
        if (typeof updateGameStatus === 'function') {
            updateGameStatus(board);
        }
        
        // Store last game data globally for status updates
        window.lastGameData = board;
        
        // CRITICAL: Restore selection if it existed
        if (previousSelection) {
            // Find the same tile in the new board data
            var restoredTile = board.grid.find(t => 
                t.x === previousSelection.x && t.y === previousSelection.y
            );
            if (restoredTile) {
                board.selected = restoredTile;
            } else {
            }
        }
        
        // Continue with initialization
        if (two === null) {
            try {
                // make an instance of two and place it on the page.
                var elem = document.getElementById('draw');
                if (!elem) {
                    console.error('Draw element not found');
                    return;
                }
                var params = { type: Two.Types.canvas, width: board.width * TILESIZE, height: board.height * TILESIZE };
                two = new Two(params).appendTo(elem);
                // Initialize transport visual system
                window.transportHighlights = [];
                transportHighlightGroup = null;
                console.log('RENDER: Transport visual system initialized');
                console.log('Two.js initialized successfully');
                
                // canvas mouse handling
                var draw = document.getElementById('draw');
                var canvas = draw.children[0];
                if (canvas) {
                    canvas.onmousemove = canvasMove;
                    canvas.onclick = advanceWarsCanvasClick;
                    canvas.ondblclick = advanceWarsDoubleClick;

                    // NEW: Prevent right-click context menu
                    canvas.addEventListener('contextmenu', function(event) {
                        event.preventDefault();
                        event.stopPropagation();
                        
                        const tile = getTileFromCanvasClick(event);
                        if (tile) {
                            handleTransportRightClick(tile, event);
                        }
                        return false;
                    });

                    // ✅ NEW: Add this alt-click handler here
                    // Alt-click handling moved to main advanceWarsCanvasClick function to prevent conflicts
                }
            } catch (error) {
                console.error('Error initializing Two.js:', error);
                return;
            }
        }
        // render
        two.clear();
        await createScene();

        // Render both movement and attack highlights
        if (window.movementHighlights && window.movementHighlights.length > 0) {
            renderMovementHighlights();
        }
        // Render transport highlights
        if (window.transportHighlights && window.transportHighlights.length > 0) {
            renderTransportHighlights();
        }
        if (window.gameState && window.gameState.attackHighlights && window.gameState.attackHighlights.length > 0) {
            renderAttackHighlights();
        }

        two.update();
        // update info
        console.log('Updating game info...');
        var gamebox = document.getElementById('gamebox');
        console.log('Gamebox element found:', gamebox);
        // Main info panel gets the detailed game stats
        var infobox = document.getElementById('infobox');
        console.log('Infobox element found:', infobox);
        if (infobox) {
            // Build army stats dynamically for all active armies
            let armyStats = '';
            const armies = ['RED', 'BLUE', 'GREEN', 'YELLOW', 'GREY'];
            armies.forEach(army => {
                if (board.army_troops && board.army_troops[army] !== undefined) {
                    const troops = board.army_troops[army] || 0;
                    const properties = board.army_properties[army] || 0;
                    const funds = board.army_funds ? board.army_funds[army] || 0 : 
                                 (army === 'RED' ? board.red_funds : army === 'BLUE' ? board.blue_funds : 0);
                    armyStats += `${army} Army: ${troops} troops, ${properties} income, ${funds} funds\n`;
                }
            });
            
            const gameStats = `Game Statistics:
Day: ${board.days} | Turn: ${board.current_turn} | Active: ${board.game_active}

${armyStats}
Controls: Click=move/attack, Ctrl+Click=load, Alt+Click=unload, Double-click=capture/wait`;
            
            infobox.innerText = gameStats;
            console.log('Infobox updated with:', gameStats);
        } else {
            console.error('Infobox element not found!');
        }

        // Small control panel box gets brief status
        if (gamebox) {
            gamebox.innerText = `Day ${board.days} | ${board.current_turn}'s Turn | Active: ${board.game_active}`;
            console.log('Game info updated successfully');
        } else {
            console.error('Gamebox element not found!');
        }
        // update code
        var code = document.getElementById('code');
        code.value = JSON.stringify(board, null, 2);
    });
}

function chat(ev) {
    if ('key' in ev && ev.key != 'Enter')
        return;
    var inputchat = document.getElementById('inputchat');
    var msg = inputchat.value;
    inputchat.value = '';
    if (msg == '')
        return;
    jsonrpc('message', {msg: msg});
}

function armyEndTurn() {
    // Clean up transport state before ending turn
    cleanupTransportState();
    
    // Call the original RPC method
    jsonrpc('army_end_turn', {});
}

function cleanupTransportState() {
    
    // Clear transport highlights if function exists
    if (typeof clearTransportHighlights === 'function') {
        clearTransportHighlights();
    }
    
    // Reset transport state
    if (typeof transportHighlights !== 'undefined') {
        transportHighlights = {
            loadableUnits: [],
            unloadPositions: [],
            selectedTransport: null
        };
    }
    
    // Clear visual highlights
    if (typeof transportHighlightGroup !== 'undefined' && transportHighlightGroup) {
        if (two && two.remove) {
            try {
                two.remove(transportHighlightGroup);
            } catch (e) {
            }
        }
        transportHighlightGroup = null;
    }
    
    // Cargo indicators now handled by authentic AW system
}

function endGame() {
    jsonrpc('end_game', {});
}

function unitCreate(tile) {
    var modal = document.getElementById('modalcreate');
    var span = document.getElementsByClassName('close')[0];
    span.onclick = function() {
        modal.style.display = 'none';
    };
    window.onclick = function(ev) {
        if (ev.target == modal) {
            modal.style.display = 'none';
        }
    };
    var select = document.getElementById('selectcreate');
    select.innerHTML = '<option>INFANTRY</option><option>MECH</option><option>RECON</option><option>TANK</option><option>MEDIUMTANK</option><option>ANTIAIR</option><option>ARTILLERY</option><option>MISSILE</option><option>ROCKET</option><option>NEOTANK</option><option>MEGATANK</option><option>PIPERUNNER</option><option>APC</option>';

    var btn = document.getElementById('buttoncreate');
    btn.onclick = function() {
        modal.style.display = 'none';
        var unitType = select.options[select.selectedIndex].value;;
        var army = tile.mapTile.army;
        jsonrpc('unit_create', {army: army, unit_type: unitType, x: tile.x, y: tile.y});
    };
    modal.style.display = 'block';
}

function airunitCreate(tile) {
    var modal = document.getElementById('modalcreate');
    var span = document.getElementsByClassName('close')[0];
    span.onclick = function() {
        modal.style.display = 'none';
    };
    window.onclick = function(ev) {
        if (ev.target == modal) {
            modal.style.display = 'none';
        }
    };
    var select = document.getElementById('selectcreate');
    select.innerHTML = '<option>BCOPTER</option><option>TCOPTER</option><option>FIGHTER</option><option>BOMBER</option>';

    var btn = document.getElementById('buttoncreate');
    btn.onclick = function() {
        modal.style.display = 'none';
        var unitType = select.options[select.selectedIndex].value;;
        var army = tile.mapTile.army;
        jsonrpc('unit_create', {army: army, unit_type: unitType, x: tile.x, y: tile.y});
    };
    modal.style.display = 'block';
}

function seaunitCreate(tile) {
    var modal = document.getElementById('modalcreate');
    var span = document.getElementsByClassName('close')[0];
    span.onclick = function() {
        modal.style.display = 'none';
    };
    window.onclick = function(ev) {
        if (ev.target == modal) {
            modal.style.display = 'none';
        }
    };
    var select = document.getElementById('selectcreate');
    select.innerHTML = '<option>LANDER</option><option>BATTLESHIP</option><option>CRUISER</option><option>SUB</option><option>CARRIER</option><option>BLACKBOAT</option>';

    var btn = document.getElementById('buttoncreate');
    btn.onclick = function() {
        modal.style.display = 'none';
        var unitType = select.options[select.selectedIndex].value;;
        var army = tile.mapTile.army;
        jsonrpc('unit_create', {army: army, unit_type: unitType, x: tile.x, y: tile.y});
    };
    modal.style.display = 'block';
}

function unitSelect(tile) {
    jsonrpc('unit_select', {x: tile.x, y: tile.y});
}

function unitCapture(tile) {
    jsonrpc('capture_tile', {x: tile.x, y: tile.y});
}

function unitWait(tile) {
    jsonrpc('unit_wait', {x: tile.x, y: tile.y});
}

function unitAttack(tile) {
    jsonrpc('unit_attack', {x: board.selected.x, y: board.selected.y, x2: tile.x, y2: tile.y});
}

function unitLoad(tile) {
    jsonrpc('unit_load', {x: board.selected.x, y: board.selected.y, x2: tile.x, y2: tile.y});
}

function unitUnload(tile) {
    idx = 0
    jsonrpc('unit_unload', {x: board.selected.x, y: board.selected.y, x2: tile.x, y2: tile.y , index: idx});
}

function unitJoin(tile) {
    jsonrpc('unit_join', {x: board.selected.x, y: board.selected.y, x2: tile.x, y2: tile.y});
}

function unitMove(tile) {
    var source = board.selected;
    var target = tile;
    jsonrpc('unit_move', {x: source.x, y: source.y, x2: target.x, y2: target.y})
        .then(result => {
            
            // Clear the selection and highlights after successful move
            board.selected = null;
            
            // Clear movement highlights
            if (typeof clearMovementHighlights === 'function') {
                clearMovementHighlights();
            }
            if (typeof clearMovementHighlightsData === 'function') {
                clearMovementHighlightsData();
            }
            
            // Clear transport highlights if they exist
            if (typeof clearTransportHighlights === 'function') {
                clearTransportHighlights();
            }
            
            // Force visual update
            if (window.two) {
                window.two.update();
            }
            
        })
        .catch(error => {
            console.error('❌ Move failed:', error);
            // Don't clear highlights if move failed
        });
}

//
// two.js rendering methods
//

function tileAt(px, py) {
    var tileX = Math.floor(px / TILESIZE);
    var tileY = Math.floor(py / TILESIZE);
    var tile = board.grid[tileX + tileY * board.width];
    return tile;
}

function canvasMove(ev) {
    var x = ev.offsetX;
    var y = ev.offsetY;
    var tile = tileAt(x, y);
    draw.style.cursor = 'default';
    if (tile && tile.can_be_moved_to)
        draw.style.cursor = 'pointer';
    else if (tile.can_be_attacked)
             draw.style.cursor = 'crosshair';
    else if (tile.unit != null && tile.unit.army == board.current_turn)
             draw.style.cursor = 'pointer';
    else if (tile.mapTile.army == board.current_turn)
             if (tile.mapTile.type == 'FACTORY' ||
                 tile.mapTile.type == 'AIRPORT' ||
                 tile.mapTile.type == 'PORT')
                 draw.style.cursor = 'pointer';
}

function canvasClick(ev) {
    var x = ev.offsetX;
    var y = ev.offsetY;
    var tile = tileAt(x, y);
    
    if (ev.detail == 1) {
        // Handle Ctrl+Click for loading
        if (ev.ctrlKey) {
            unitLoad(tile);
            return;
        }
        
        // Handle Alt+Click for unloading
        if (ev.altKey) {
            unitUnload(tile);
            return;
        }
        
        // PRIORITY 1: Check for movement on highlighted tiles FIRST
        if (board.selected && window.movementHighlights) {
            var isHighlightedMove = window.movementHighlights.some(h => 
                h.x === tile.x && h.y === tile.y
            );
            
            if (isHighlightedMove) {
                unitMove(tile);
                return; // Exit immediately after movement
            }
        }
        
        // PRIORITY 2: Regular game actions (attacks)
        if (tile.can_be_attacked) {
            // Use enhanced attack if available, otherwise fallback
            if (typeof unitAttackWithPreview === 'function') {
                unitAttackWithPreview(tile);
            } else {
                unitAttack(tile);
            }
            return;
        }
        
        // PRIORITY 3: Unit selection/deselection
        if (tile.unit != null && tile.unit.army == board.current_turn) {
            if (tile.unit.can_attack || tile.unit.can_move || tile.unit.can_capture) {
                // Check if clicking on the same unit (deselect)
                if (board.selected && 
                    board.selected.x === tile.x && 
                    board.selected.y === tile.y) {
                    
                    // Deselect the unit
                    board.selected = null;
                    
                    // Clear movement highlights
                    if (typeof clearMovementHighlights === 'function') {
                        clearMovementHighlights();
                    }
                    if (typeof clearMovementHighlightsData === 'function') {
                        clearMovementHighlightsData();
                    }
                    
                    // Clear transport highlights if they exist
                    if (typeof clearTransportHighlights === 'function') {
                        clearTransportHighlights();
                    }
                    
                    // Force a visual update
                    if (window.two) {
                        window.two.update();
                    }
                    
                    return;
                }
                
                // Different unit selected - proceed with normal selection
                if (typeof unitSelectWithMovementHighlighting === 'function') {
                    unitSelectWithMovementHighlighting(tile);
                } else if (typeof unitSelectWithTransportAndRange === 'function') {
                    unitSelectWithTransportAndRange(tile);
                } else {
                    unitSelect(tile);
                }
                return;
            }
        }
        
        // PRIORITY 4: Fallback movement check
        if (tile.can_be_moved_to) {
            unitMove(tile);
            return;
        }
        
        // PRIORITY 5: Building interactions
        if (tile.mapTile.type == 'FACTORY' &&
                tile.mapTile.army == board.current_turn &&
                tile.unit == null) {
            unitCreate(tile);
            return;
        }
        if (tile.mapTile.type == 'AIRPORT' &&
                tile.mapTile.army == board.current_turn &&
                tile.unit == null) {
            airunitCreate(tile);
            return;
        }
        if (tile.mapTile.type == 'PORT' &&
                tile.mapTile.army == board.current_turn &&
                tile.unit == null) {
            seaunitCreate(tile);
            return;
        }
        
        // PRIORITY 6: Deselect when clicking empty tiles (LAST)
        if (board.selected) {
            board.selected = null;
            
            // Clear all highlights
            if (typeof clearMovementHighlights === 'function') {
                clearMovementHighlights();
            }
            if (typeof clearMovementHighlightsData === 'function') {
                clearMovementHighlightsData();
            }
            if (typeof clearTransportHighlights === 'function') {
                clearTransportHighlights();
            }
            
            // Force visual update
            if (window.two) {
                window.two.update();
            }
            
        }
    }
}

function canvasdblClick(ev) {
    var x = ev.offsetX;
    var y = ev.offsetY;
    var tile = tileAt(x, y);
    if (tile.mapTile.type === 'CITY' ||
               tile.mapTile.type === 'BASE_TOWER_1' ||
               tile.mapTile.type === 'FACTORY' ||
               tile.mapTile.type === 'PORT' ||
               tile.mapTile.type ==='AIRPORT') {
               if (tile.unit &&
                   tile.unit.can_capture) {
                   if (tile.unit.type == 'INFANTRY' ||
                       tile.unit.type == 'MECH') {
                       unitCapture(tile);
                       }
                   }
    } else if (tile.unit) {
            unitWait(tile);
            }
}

function unitSelectWithTransportAndRange(tile) {
    
    try {
        // Step 1: Basic unit selection
        jsonrpc('unit_select', {x: tile.x, y: tile.y});
        
        // Step 2: Show movement range AND attack targets
        if (tile.unit && tile.unit.army === board.current_turn) {
            // Show movement range
            showMovementRange(tile.x, tile.y);
            
            // Show attack targets after a short delay
            setTimeout(() => {
                showAttackTargets(tile.x, tile.y);
            }, 200);
        } else {
            clearAllHighlights();
        }
        
        // Step 3: Handle transport functionality
        handleTransportSelectionLogic(tile);
        
    } catch (error) {
        console.error('SELECTION_FIX: Unit selection failed:', error);
        jsonrpc('unit_select', {x: tile.x, y: tile.y});
    }
}

function executeMovement(targetTile) {
    
    if (!board.selected || !board.selected.unit) {
        console.error('❌ No unit selected for movement');
        return;
    }
    
    var mover = board.selected;
    
    jsonrpc('unit_move', {
        x: mover.x,
        y: mover.y,
        x2: targetTile.x,
        y2: targetTile.y
    }, function(result) {
        
        // Update the selected tile position
        board.selected = targetTile;
        
        // Clear movement highlights but keep unit selected for potential attack
        clearMovementHighlights();
        
        // Show attack options from new position
        setTimeout(() => {
            showAttackTargets(targetTile.x, targetTile.y);
        }, 300);
        
        // Update the board
        update();
    });
}

function handleTransportSelectionLogic(tile) {
    if (!tile.unit) {
        clearTransportHighlights();
        return;
    }
    // Get cargo/transport information (ONLY for transport units)
    if (tile.unit && isTransportUnit(tile.unit)) {
        jsonrpc('get_cargo_info', {x: tile.x, y: tile.y}, function(result) {
            if (result && result.success && result.cargo_info) {
                const cargoInfo = result.cargo_info;
                
                // Show transport-specific highlights
                if (cargoInfo.is_transport) {
                    if (cargoInfo.current_cargo > 0) {
                        // Transport has cargo - show unload positions
                        showUnloadPositionsHighlight(tile.x, tile.y);
                    } else {
                        // Empty transport - show loadable units nearby
                        showLoadableUnitsHighlight(tile.x, tile.y);
                    }
                }
                
                // Show cargo information to user (only for transports now)
                showCargoInfo(tile.unit, cargoInfo);
            } else {
                // If cargo info fails, just clear highlights
                clearTransportHighlights();
            }
        });
    } else {
        // For non-transport units, just clear any existing transport highlights
        clearTransportHighlights();
        // No popup, no RPC call needed
    }
}

var textureLoadId = null;
function ontextureLoad(src) {
    if (textureLoadId != null) {
        clearTimeout(textureLoadId);
        textureLoadId = null;
    }
    textureLoadId = setTimeout(() => two.update(), 100);
}

function showJson() {
  var showJsonArea = document.getElementById('inputshowjson').checked;
  if (showJsonArea) {
    code.hidden = "";
  } else {
    code.hidden = "true";
  }
}

function showChat() {
  var showChatArea = document.getElementById('inputshowchat').checked;
  if (showChatArea) {
    textareachat.hidden = "";
    inputchat.hidden = "";
    buttonchat.hidden = "";
  } else {
    textareachat.hidden = "true";
    inputchat.hidden = "true";
    buttonchat.hidden = "true";
  }
}

function renderBaseTile(tile) {
    // Render a PLAIN tile as base layer for structures
    // ALWAYS use transparent tileset for base layer to prevent black backgrounds
    var spriteSheetWidth = 445;
    var spriteSheetHeight = 1163;
    const SPRITESIZE = 16;
    var x = spriteSheetWidth/2 - SPRITESIZE/2;
    var y = spriteSheetHeight/2 - SPRITESIZE/2;
    
    // PLAIN tile coordinates
    x = x - 8;
    y = y - 64;
    
    // Always use AW:DS transparent tileset for base layer, regardless of user selection
    var baseTilesetSrc = '/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png';
    var baseTexture = new Two.Texture(baseTilesetSrc, () => ontextureLoad(baseTilesetSrc));
    baseTexture.offset = new Two.Vector(x, y);
    
    var baseRect = two.makeRectangle(tile.x * TILESIZE + TILESIZE/2, tile.y * TILESIZE + TILESIZE/2, SPRITESIZE, SPRITESIZE);
    baseRect.fill = baseTexture;
    baseRect.stroke = 'transparent';
}

function makeMapTile(tile) {
    var showMapTiles = document.getElementById('inputshowmap').checked;
    if (showMapTiles) {
        // Check if this terrain type needs a base layer (structures)
        const structureTypes = ['CITY', 'FACTORY', 'AIRPORT', 'PORT', 'COM_TOWER', 'LAB', 'MISSILE_SILO', 'EMPTY_SILO', 
                              'BASE_TOWER_0', 'BASE_TOWER_1', 'BASE_TOWER_2', 'BASE_TOWER_3', 'BASE_TOWER_4', 'MOUNTAIN'];
        
        if (structureTypes.includes(tile.mapTile.type)) {
            // First render a PLAIN tile as base layer
            renderBaseTile(tile);
        }
        
        // tile sprite
        var spriteSheetWidth = 445;
        var spriteSheetHeight = 1163;
        const SPRITESIZE = 16;
        var x = spriteSheetWidth/2 - SPRITESIZE/2;
        var y = spriteSheetHeight/2 - SPRITESIZE/2;
        var _2xHeight = false;
        switch (tile.mapTile.type) {
            case 'PLAIN':
                x = x - 8;
                y = y - 64;
                break;
            case 'WOOD':
                x = x - 352;
                y = y - 56;
                _2xHeight = true;
                break;
            case 'MOUNTAIN':
                x = x - 25;
                y = y - 39;
                _2xHeight = true;
                break;
            case 'ROAD_HORT':
                x = x - 42;
                y = y - 64;
                break;
            case 'ROAD_VERT':
                x = x - 59;
                y = y - 64;
                break;
            case 'ROAD_NW':
                x = x - 42;
                y = y - 13;
                break;
            case 'ROAD_NE':
                x = x - 76;
                y = y - 13;
                break;
            case 'ROAD_SE':
                x = x - 76;
                y = y - 47;
                break;
            case 'ROAD_SW':
                x = x - 42;
                y = y - 47;
                break;
            case 'SWNRoad':
                x = x - 156;
                y = y - 31;
                break;
            case 'ESWRoad':
                x = x - 59;
                y = y - 13;
                break;
            case 'WNERoad':
                x = x - 110;
                y = y - 47;
                break;
            case 'NESRoad':
                x = x - 110;
                y = y - 47;
                break;
            case 'CRoad':
                x = x - 59;
                y = y - 30;
                break;
            case 'CITY':
                x = x - 87;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 812;
                        break;
                    case 'BLUE':
                        y = y - 847;
                        break;
                    case 'GREEN':
                        y = y - 882;
                        break;
                    case 'YELLOW':
                        y = y - 917;
                        break;
                    case 'GREY':
                        y = y - 952;
                        break;
                    default:
                        y = y - 766;
                        break;
                }
                _2xHeight = true;
                break;
            case 'FACTORY':
                x = x - 102;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 818;
                        break;
                    case 'BLUE':
                        y = y - 851;
                        break;
                    case 'GREEN':
                        y = y - 884;
                        break;
                    case 'YELLOW':
                        y = y - 917;
                        break;
                    case 'GREY':
                        y = y - 950;
                        break;
                    default:
                        y = y - 772;
                        break;
                }
                break;
            case 'AIRPORT':
                x = x - 120;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 818;
                        break;
                    case 'BLUE':
                        y = y - 851;
                        break;
                    case 'GREEN':
                        y = y - 884;
                        break;
                    case 'YELLOW':
                        y = y - 917;
                        break;
                    case 'GREY':
                        y = y - 950;
                        break;
                    default:
                        y = y - 773;
                        break;
                }
                break;
            case 'PORT':
                x = x - 137;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 811;
                        _2xHeight = true;
                        break;
                    case 'BLUE':
                        y = y - 844;
                        _2xHeight = true;
                        break;
                    case 'GREEN':
                        y = y - 877;
                        _2xHeight = true;
                        break;
                    case 'YELLOW':
                        y = y - 910;
                        _2xHeight = true;
                        break;
                    case 'GREY':
                        y = y - 943;
                        _2xHeight = true;
                        break;
                    default:
                        y = y - 765;
                        _2xHeight = true;
                        break;
                }
                break;
            case 'COM_TOWER':
                x = x - 154;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 811;
                        _2xHeight = true;
                        break;
                    case 'BLUE':
                        y = y - 844;
                        _2xHeight = true;
                        break;
                    case 'GREEN':
                        y = y - 877;
                        _2xHeight = true;
                        break;
                    case 'YELLOW':
                        y = y - 910;
                        _2xHeight = true;
                        break;
                    case 'GREY':
                        y = y - 943;
                        _2xHeight = true;
                        break;
                    default:
                        y = y - 765;
                        _2xHeight = true;
                        break;
                }
                break;
            case 'BASE_TOWER_0':
                x = x - 1;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 812;
                        _2xHeight = true;
                        break;
                    case 'BLUE':
                        y = y - 845;
                        _2xHeight = true;
                        break;
                    case 'GREEN':
                        y = y - 878;
                        _2xHeight = true;
                        break;
                    case 'YELLOW':
                        y = y - 911;
                        _2xHeight = true;
                        break;
                    case 'GREY':
                        y = y - 944;
                        _2xHeight = true;
                        break;
                    default:
                        y = y - 757;
                        _2xHeight = true;
                        break;
                }
                break;
            case 'BASE_TOWER_1':
                x = x - 1;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 812;
                        _2xHeight = true;
                        break;
                    case 'BLUE':
                        y = y - 845;
                        _2xHeight = true;
                        break;
                    case 'GREEN':
                        y = y - 878;
                        _2xHeight = true;
                        break;
                    case 'YELLOW':
                        y = y - 911;
                        _2xHeight = true;
                        break;
                    case 'GREY':
                        y = y - 944;
                        _2xHeight = true;
                        break;
                    default:
                        y = y - 757;
                        _2xHeight = true;
                        break;
                }
                _2xHeight = true;
                break;
            case 'BASE_TOWER_2':
                x = x - 38;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 1040;
                        break;
                    case 'BLUE':
                        y = y - 1073;
                        break;
                    default:
                        y = y - 1218;
                        break;
                }
                _2xHeight = true;
                break;
            case 'LAB':
                x = x - 171;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 812;
                        _2xHeight = true;
                        break;
                    case 'BLUE':
                        y = y - 845;
                        _2xHeight = true;
                        break;
                    case 'GREEN':
                        y = y - 878;
                        _2xHeight = true;
                        break;
                    case 'YELLOW':
                        y = y - 911;
                        _2xHeight = true;
                        break;
                    case 'GREY':
                        y = y - 944;
                        _2xHeight = true;
                        break;
                    default:
                        y = y - 765;
                        _2xHeight = true;
                        break;
                }
                break;
            case 'RIVER_HORT':
                x = x - 386;
                y = y - 145;
                break;
            case 'RIVER_VERT':
                x = x - 420;
                y = y - 111;
                break;
            case 'RIVER_NE':
                x = x - 369;
                y = y - 94;
                break;
            case 'RIVER_NW':
                x = x - 403;
                y = y - 94;
                break;
            case 'RIVER_SE':
                x = x - 403;
                y = y - 128;
                break;
            case 'RIVER_SW':
                x = x - 369;
                y = y - 128;
                break;
            case 'ESWRiver':
                x = x - 161;
                y = y - 338;
                break;
            case 'NESRiver':
                x = x - 110;
                y = y - 251;
                break;
            case 'WNERiver':
                x = x - 160;
                y = y - 285;
                break;
            case 'SWNRiver':
                x = x - 160;
                y = y - 285;
                break;
            case 'BEACH_NE':
                x = x - 333;
                y = y - 198;
                break;
            case 'BEACH_NW':
                x = x - 282;
                y = y - 355;
                break;
            case 'BEACH_SW':
                x = x - 350;
                y = y - 355;
                break;
            case 'BEACH_SE':
                x = x - 333;
                y = y - 145;
                break;
            case 'BEACH_N':
                x = x - 265;
                y = y - 111;
                break;
            case 'BEACH_E':
                x = x - 214;
                y = y - 321;
                break;
            case 'BEACH_S':
                x = x - 265;
                y = y - 304;
                break;
            case 'BEACH_W':
                x = x - 231;
                y = y - 321;
                break;
            case 'BEACH_END_N':
                x = x - 248;
                y = y - 145;
                break;
            case 'BEACH_END_E':
                x = x - 316;
                y = y - 111;
                break;
            case 'BEACH_END_S':
                x = x - 248;
                y = y - 128;
                break;
            case 'BEACH_END_W':
                x = x - 316;
                y = y - 94;
                break;
            case 'PIPE_VERT':
                x = x - 212;
                y = y - 30;
                break;
            case 'PIPE_END_N':
                x = x - 178;
                y = y - 30;
                break;
            case 'PIPE_END_S':
                x = x - 178;
                y = y - 47;
                break;
            case 'PIPE_END_W':
                x = x - 144;
                y = y - 64;
                break;
            case 'PIPE_END_E':
                x = x - 161;
                y = y - 64;
                break;
            case 'PIPE_END_NE':
                x = x - 161;
                y = y - 30;
                break;
            case 'PIPE_END_NW':
                x = x - 144;
                y = y - 30;
                break;
            case 'PIPE_END_SW':
                x = x - 144;
                y = y - 47;
                break;
            case 'PIPE_END_SE':
                x = x - 161;
                y = y - 47;
                break;
            case 'PIPE_HORT':
                x = x - 195;
                y = y - 30;
                break;
            case 'SEA':
                x = x - 76;
                y = y - 94;
                break;
            case 'HBridge':
                x = x - 76;
                y = y - 64;
                break;
            case 'VBridge':
                x = x - 94;
                y = y - 64;
                break;
            case 'REEF':
                x = x - 195;
                y = y - 145;
                break;
            case 'MISSILE_SILO':
                x = x - 188;
                y = y - 766;
                _2xHeight = true;
                break;
            case 'EMPTY_SILO':
                x = x - 205;
                y = y - 767;
                _2xHeight = true;
                break;
            default:
                return;
        }
        var tilesetSrc = getSelectedTerrainTileset();
        var spriteTexture = new Two.Texture(tilesetSrc, () => ontextureLoad(tilesetSrc));
        spriteTexture.offset = new Two.Vector(x, y);
        var rect = null;
        if (_2xHeight) {
            rect = two.makeRectangle(tile.x * TILESIZE + TILESIZE/2, tile.y * TILESIZE , SPRITESIZE, SPRITESIZE * 2);
        } else {
            rect = two.makeRectangle(tile.x * TILESIZE + TILESIZE/2, tile.y * TILESIZE + TILESIZE/2, SPRITESIZE, SPRITESIZE);
        }
        rect.fill = spriteTexture;
        rect.stroke = 'transparent';
    }
    // tile overlay
    rect = two.makeRectangle(tile.x * TILESIZE + TILESIZE/2, tile.y * TILESIZE + TILESIZE/2, TILESIZE, TILESIZE);
    rect.stroke = 'black';
    rect.fill = 'transparent';
    rect.opacity = 0.50;
    if (tile.can_be_moved_to) {
        rect.fill = 'lightyellow';
    }
    if (tile.can_be_attacked) {
        rect.fill = 'red';
    }
    if (board.selected && board.selected.unit && tile.unit && tile.unit.id == board.selected.unit.id) {
        rect.fill = 'lightsalmon';
    }
}

/**
 * Load sprite corrector data from JSON file
 */
async function loadSpriteCorrector() {
    if (window.spriteCorrections) {
        return; // Already loaded
    }
    
    try {
        // Use the latest sprite corrections from templates directory
        const response = await fetch('/templates/sprite_corrections_config.json');
        const data = await response.json();
        
        window.spriteCorrections = data.corrections;
        window.spriteConfig = data.spriteConfig;
        
        console.log('Sprite corrector data loaded successfully');
        console.log('SpriteConfig:', window.spriteConfig);
        console.log('Total correction categories:', Object.keys(data.corrections).length);
        console.log('Sample blue unit coords:', data.corrections.idle?.INFANTRY_BLUE_idle_0);
    } catch (error) {
        console.error('Failed to load sprite corrector data:', error);
        // Set fallback values
        window.spriteCorrections = {};
        window.spriteConfig = { width: 16, height: 16 };
    }
}

/**
 * Generate a unique texture for a unit with its HP indicator baked in
 * This prevents HP display sharing between units of the same type
 */
async function generateUnitTexture(tile) {
    // Ensure sprite corrector data is loaded
    await loadSpriteCorrector();
    
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    // Sprite dimensions: 16x16 for unit sprites, 8x8 for HP indicators
    const SPRITESIZE = 16;  // Unit sprites are 16x16 (except HQ and MOUNTAIN)
    const HEALTHSIZE = 8;   // HP indicators are 8x8
    
    // Set canvas size to accommodate unit sprite
    canvas.width = SPRITESIZE;
    canvas.height = SPRITESIZE;
    
    // Load the sprite sheet image
    const spriteSheetImg = new Image();
    const unitsSrc = getSelectedUnitTileset();
    
    return new Promise((resolve, reject) => {
        spriteSheetImg.onload = function() {
            console.log(`Sprite sheet loaded: ${unitsSrc}, dimensions: ${spriteSheetImg.width}x${spriteSheetImg.height}`);
            // Use sprite corrector data to get accurate coordinates
            let spriteKey, x, y;
            
            // Determine sprite state
            const state = (!tile.unit.can_move && !tile.unit.can_attack) ? 'unavailable' : 'idle';
            
            // Build sprite key using sprite corrector format
            spriteKey = `${tile.unit.type}_${tile.unit.army}_${state}_0`;
            
            // Get coordinates from sprite corrector data
            if (window.spriteCorrections && window.spriteCorrections[state] && window.spriteCorrections[state][spriteKey]) {
                const coords = window.spriteCorrections[state][spriteKey];
                x = coords.x;
                y = coords.y;
                console.log(`Using sprite corrector for ${spriteKey}: x=${x}, y=${y}`);
            } else {
                // Enhanced fallback: Try to find coordinates based on RED army equivalent
                const redSpriteKey = spriteKey.replace('_BLUE_', '_RED_').replace('_GREEN_', '_RED_').replace('_YELLOW_', '_RED_').replace('_GREY_', '_RED_');
                
                if (window.spriteCorrections && window.spriteCorrections[state] && window.spriteCorrections[state][redSpriteKey]) {
                    // Use RED army coordinates as base and apply army offset
                    const redCoords = window.spriteCorrections[state][redSpriteKey];
                    x = redCoords.x;
                    y = redCoords.y;
                    
                    // Apply army-specific offset based on sprite sheet layout analysis:
                    // RED: x=3, y=104 | BLUE: x=392, y=104 | GREEN: x=3, y=672 | YELLOW: x=392, y=672 | GREY: x=339, y=1240
                    switch (tile.unit.army) {
                        case 'RED': 
                            // no offset, already using RED coordinates
                            break;
                        case 'BLUE': 
                            x += 389; // BLUE units are 389px to the right of RED
                            break;
                        case 'GREEN': 
                            y += 568; // GREEN units are 568px below RED 
                            break;
                        case 'YELLOW': 
                            x += 389; // 389px right
                            y += 568; // 568px down
                            break;
                        case 'GREY': 
                            x += 336; // 336px right 
                            y += 1136; // 1136px down
                            break;
                        default: 
                            x += 336; 
                            y += 1136; 
                            break;
                    }
                    
                    console.log(`Using enhanced fallback for ${spriteKey} based on ${redSpriteKey}: x=${x}, y=${y}`);
                } else {
                    // Final fallback to original coordinate calculation
                    console.warn(`Sprite corrector data not found for ${spriteKey}, using basic fallback coordinates`);
                    var spriteSheetWidth = 781;
                    var spriteSheetHeight = 1790;
                    x = spriteSheetWidth/2 - SPRITESIZE/2;
                    y = spriteSheetHeight/2 - SPRITESIZE/2;
                    
                    // Apply basic army offsets as fallback
                    switch (tile.unit.army) {
                        case 'RED': x -= 4; y -= 105; break;
                        case 'BLUE': x -= 25; y -= 105; break;
                        case 'GREEN': x -= 46; y -= 105; break;
                        case 'YELLOW': x -= 67; y -= 105; break;
                        default: x -= 88; y -= 105; break;
                    }
                    
                    // Apply basic unit type offsets as fallback
                    switch(tile.unit.type) {
                        case 'MECH': x -= 21; break;
                        case 'TANK': x -= 105; break;
                        case 'BATTLESHIP': x -= 357; y -= 42; break;
                    }
                    
                    if (!tile.unit.can_move && !tile.unit.can_attack) {
                        x -= 336; // unavailable sprite
                    }
                }
            }
            
            // Draw the unit sprite onto canvas
            ctx.drawImage(
                spriteSheetImg,
                x, y, SPRITESIZE, SPRITESIZE,  // Source rect
                0, 0, SPRITESIZE, SPRITESIZE   // Dest rect
            );
            
            // Debug: Log what we're drawing for blue units
            if (tile.unit.army === 'BLUE') {
                console.log(`Drawing BLUE unit: ${spriteKey} from (${x}, ${y}) size ${SPRITESIZE}x${SPRITESIZE}`);
            }
            
            // Draw HP indicator if unit is damaged
            if (tile.unit.status.hp <= 90) {
                var hpDigit = Math.ceil(tile.unit.status.hp / 10);
                if (hpDigit > 9) hpDigit = 9;
                if (hpDigit < 1) hpDigit = 1;
                
                // Calculate HP sprite position using sprite corrector data
                var hpX, hpY;
                const hpCategory = tile.unit.can_move ? 'hp_indicators' : 'hp_unavailable';
                const hpKey = `${hpCategory}_${hpDigit - 1}`;
                
                if (window.spriteCorrections && window.spriteCorrections[hpCategory] && window.spriteCorrections[hpCategory][hpKey]) {
                    const hpCoords = window.spriteCorrections[hpCategory][hpKey];
                    hpX = hpCoords.x;
                    hpY = hpCoords.y;
                } else {
                    // Fallback to hardcoded positions
                    if (tile.unit.can_move) {
                        // Active HP indicators
                        hpX = 556 + (hpDigit - 1) * 9;
                        hpY = 1233;
                    } else {
                        // Inactive HP indicators  
                        hpX = 428 + (hpDigit - 1) * 9;
                        hpY = 1233;
                    }
                }
                
                // Draw HP indicator in bottom-right corner
                ctx.drawImage(
                    spriteSheetImg,
                    hpX, hpY, HEALTHSIZE, HEALTHSIZE,           // Source rect
                    SPRITESIZE - HEALTHSIZE, SPRITESIZE - HEALTHSIZE, HEALTHSIZE, HEALTHSIZE  // Dest rect (bottom-right)
                );
            }
            
            // Convert canvas to data URL - this creates a unique texture
            const dataURL = canvas.toDataURL();
            resolve(dataURL);
        };
        
        spriteSheetImg.onerror = function(error) {
            console.error('Failed to load sprite sheet:', unitsSrc, error);
            reject(error);
        };
        
        spriteSheetImg.src = unitsSrc;
    });
}

async function makeSprite(tile) {
    try {
        // Generate unique texture for this specific unit with HP baked in
        const uniqueTextureURL = await generateUnitTexture(tile);
        const SPRITESIZE = 16;
        
        // Create sprite using the unique texture with HP baked in
        var spriteTexture = new Two.Texture(uniqueTextureURL);
        var rect = two.makeRectangle(tile.x * TILESIZE + TILESIZE/2, tile.y * TILESIZE + TILESIZE/2, SPRITESIZE, SPRITESIZE);
        rect.fill = spriteTexture;
        rect.stroke = 'transparent';
        
        // Force re-render to show the new texture
        two.update();
        
        return rect;
    } catch (error) {
        console.error('Error generating unit texture:', error);
        // Fallback to old sprite creation method
        makeSpriteLegacy(tile);
    }
}

function makeSpriteLegacy(tile) {
    var spriteSheetWidth = 781;
    var spriteSheetHeight = 1790;
    const SPRITESIZE = 16;
    var x = spriteSheetWidth/2 - SPRITESIZE/2;
    var y = spriteSheetHeight/2 - SPRITESIZE/2;
    switch (tile.unit.army) {
        case 'RED':
            x = x - 4;
            y = y - 105;
            break;
        case 'BLUE':
            x = x - 393;
            y = y - 105;
            break;
        case 'GREEN':
            x = x - 4;
            y = y - 672;
            break;
        case 'YELLOW':
            x = x - 393;
            y = y - 672;
            break;
        case 'GREY':
            x = x - 4;
            y = y - 1240;
            break;
    }
    switch (tile.unit.type) {
        case 'MECH':
            y = y - 95;
            break;
        case 'RECON':
            y = y - 190;
            break;
        case 'TANK':
            y = y - 209;
            break;
        case 'MEDIUMTANK':
            y = y - 228;
            break;
        case 'ANTIAIR':
            y = y - 285;
            break;
        case 'ARTILLERY':
            y = y - 303;
            break;
        case 'MISSILE':
            y = y - 342;
            break;
        case 'ROCKET':
            y = y - 322;
            break;
        case 'APC':
            y = y - 265;
            break;
        case 'NEOTANK':
            y = y - 247;
            break;
        case 'FIGHTER':
            y = y - 361;
            break;
        case 'BCOPTER':
            y = y - 400;
            break;
        case 'TCOPTER':
            y = y - 418;
            break;
        case 'BATTLESHIP':
            y = y - 437;
            break;
        case 'LANDER':
            y = y - 475;
            break;
        case 'CRUISER':
            y = y - 455;
            break;
        case 'SUB':
            y = y - 495;
            break;
        case 'BOMBER':
            y = y - 380;
            break;
        case 'CARRIER':
            y = y - 512;
            break;
        case 'BLACKBOAT':
            y = y - 512;
            x = x - 17;
            break;
        case 'MEGATANK':
            y = y - 512;
            x = x - 33;
            break;
        case 'PIPERUNNER':
            y = y - 538;
            break;
        case 'BLACKBOMB':
            y = y - 380;  // Same as bomber initially, adjust if needed
            x = x - 50;   // Offset if different sprite position
            break;
        case 'STEALTH':
            y = y - 361;  // Same as fighter initially, adjust if needed  
            x = x - 67;   // Offset if different sprite position
            break;
    }
    if (!tile.unit.can_move && !tile.unit.can_attack)
        x = x - 336; // unavailable sprite
    var unitsSrc = getSelectedUnitTileset();
    // Create unique texture per unit to prevent sharing between units
    var spriteTexture = new Two.Texture(unitsSrc + '?unit=' + tile.x + '_' + tile.y, () => ontextureLoad(unitsSrc));
    spriteTexture.offset = new Two.Vector(x, y);
    var rect = two.makeRectangle(tile.x * TILESIZE + TILESIZE/2, tile.y * TILESIZE + TILESIZE/2, SPRITESIZE, SPRITESIZE);
    rect.fill = spriteTexture;
    rect.stroke = 'transparent';
    var health = null;
    var fuel = null;
    var ammo = null;
    if (tile.unit.status.hp <= 90 && tile.unit.can_move ) {
        const HEALTHSIZE = SPRITESIZE/2; // Unit sprites are 16x16, HP display area is 16x16
        var hpDigit = Math.ceil(tile.unit.status.hp / 10); // 1-10 HP -> 1, 11-20 HP -> 2, etc.
        if (hpDigit > 9) hpDigit = 9; // Cap at 9
        if (hpDigit < 1) hpDigit = 1; // Minimum 1
        
        // HP Available coordinates from sprite corrector: hp_indicators_0 to hp_indicators_8 (digits 1-9)
        // hp_indicators_0 = digit "1" at x=556, hp_indicators_1 = digit "2" at x=565, etc.
        x = spriteSheetWidth/2 - HEALTHSIZE/2;
        y = spriteSheetHeight/2 - HEALTHSIZE/2;
        var hpSpriteX = 556 + (hpDigit - 1) * 9;
        x = x - hpSpriteX;
        y = y - 1233;
        // Create unique health texture per unit to prevent sharing (can_move=true)
        var healthTexture = new Two.Texture(unitsSrc + '?hp_active=' + tile.x + '_' + tile.y + '_' + hpDigit, () => ontextureLoad(unitsSrc));
        healthTexture.offset = new Two.Vector(x, y);
        health = two.makeRectangle(tile.x * TILESIZE + TILESIZE - HEALTHSIZE/2, tile.y * TILESIZE + TILESIZE - HEALTHSIZE/2, HEALTHSIZE, HEALTHSIZE);
        health.fill = healthTexture;
        health.stroke = 'transparent';
    }
    if (tile.unit.status.hp <= 90 && !tile.unit.can_move ) {
        const HEALTHSIZE = SPRITESIZE/2; // Unit sprites are 16x16, HP display area is 16x16
        var hpDigit = Math.ceil(tile.unit.status.hp / 10); // 1-10 HP -> 1, 11-20 HP -> 2, etc.
        if (hpDigit > 9) hpDigit = 9; // Cap at 9
        if (hpDigit < 1) hpDigit = 1; // Minimum 1
        
        // HP Unavailable coordinates from sprite corrector: hp_unavailable_0 to hp_unavailable_8 (digits 1-9)
        // hp_unavailable_0 = digit "1" at x=428, hp_unavailable_1 = digit "2" at x=437, etc.
        x = spriteSheetWidth/2 - HEALTHSIZE/2;
        y = spriteSheetHeight/2 - HEALTHSIZE/2;
        var hpSpriteX = 428 + (hpDigit - 1) * 9;
        x = x - hpSpriteX;
        y = y - 1233;
        // Create unique health texture per unit to prevent sharing (can_move=false)
        var healthTexture = new Two.Texture(unitsSrc + '?hp_inactive=' + tile.x + '_' + tile.y + '_' + hpDigit, () => ontextureLoad(unitsSrc));
        healthTexture.offset = new Two.Vector(x, y);
        health = two.makeRectangle(tile.x * TILESIZE + TILESIZE - HEALTHSIZE/2, tile.y * TILESIZE + TILESIZE - HEALTHSIZE/2, HEALTHSIZE, HEALTHSIZE);
        health.fill = healthTexture;
        health.stroke = 'transparent';
    }
    if (tile.unit.status.fuel <= 30) {
        const FUELSIZE = SPRITESIZE/2;
        x = spriteSheetWidth/2 - FUELSIZE/2;
        y = spriteSheetHeight/2 - FUELSIZE/2;
        x = x - 651;
        y = y - 1241;
        var fuelTexture = new Two.Texture(unitsSrc, () => ontextureLoad(unitsSrc));
        fuelTexture.offset = new Two.Vector(x, y);
        fuel = two.makeRectangle(tile.x * TILESIZE + TILESIZE - FUELSIZE/2 - 8, tile.y * TILESIZE + TILESIZE - FUELSIZE/2 - 8, FUELSIZE, FUELSIZE);
        fuel.fill = fuelTexture;
        fuel.stroke = 'transparent';
    }
    if (!tile.unit.UnitType == 0 && tile.unit.status.ammo <= 3) {
        const AMMOSIZE = SPRITESIZE/2;
        x = spriteSheetWidth/2 - AMMOSIZE/2;
        y = spriteSheetHeight/2 - AMMOSIZE/2;
        x = x - 651;
        y = y - 1251;
        var ammoTexture = new Two.Texture(unitsSrc, () => ontextureLoad(unitsSrc));
        ammoTexture.offset = new Two.Vector(x, y);
        ammo = two.makeRectangle(tile.x * TILESIZE + TILESIZE - AMMOSIZE/2, tile.y * TILESIZE + TILESIZE - AMMOSIZE/2 - 8, AMMOSIZE -2, AMMOSIZE -2);
        ammo.fill = ammoTexture;
        ammo.stroke = 'transparent';
    }
    if (tile.capture_hp <= 19) {
        const FLAGSIZE = SPRITESIZE/2;
        x = spriteSheetWidth/2 - FLAGSIZE/2;
        y = spriteSheetHeight/2 - FLAGSIZE/2;
        x = x - 530;
        y = y - 1233;
        var flagTexture = new Two.Texture(unitsSrc, () => ontextureLoad(unitsSrc));
        flagTexture.offset = new Two.Vector(x, y);
        flag = two.makeRectangle(tile.x * TILESIZE + TILESIZE - FLAGSIZE/2 - 8, tile.y * TILESIZE + TILESIZE - FLAGSIZE/2, FLAGSIZE, FLAGSIZE);
        flag.fill = flagTexture;
        flag.stroke = 'transparent';
    }
    
    // FIXED CARGO INDICATOR CODE:
    if (isTransportUnitForRender(tile.unit)) {
        const cargoCount = getCargoCountForRender(tile.unit);
        
        if (cargoCount > 0) {
            const LOADSIZE = SPRITESIZE/2;
            x = spriteSheetWidth/2 - LOADSIZE/2;
            y = spriteSheetHeight/2 - LOADSIZE/2;
            x = x - 520;
            y = y - 1233;
            var loadTexture = new Two.Texture(unitsSrc, () => ontextureLoad(unitsSrc));
            loadTexture.offset = new Two.Vector(x, y);
            load = two.makeRectangle(tile.x * TILESIZE + TILESIZE - LOADSIZE/2 - 8, tile.y * TILESIZE + TILESIZE - LOADSIZE/2, LOADSIZE, LOADSIZE);
            load.fill = loadTexture;
            load.stroke = 'transparent';
        }
    }
    
    return rect;
}

function renderTransportIndicators() {
    console.log('RENDER: Adding transport indicators');
    
    // Render transport highlights (green for boarding, blue for exits)
    renderTransportHighlights();
    
    // Transport cargo indicators are now handled by authentic AW load icon in makeUnitTile()
}

function renderTransportHighlights() {
    // Clear any existing highlight group
    if (transportHighlightGroup) {
        two.remove(transportHighlightGroup);
        transportHighlightGroup = null;
    }
    
    if (!window.transportHighlights || window.transportHighlights.length === 0) {
        return; // No highlights to show
    }
    
    // Create new highlight group
    transportHighlightGroup = two.makeGroup();
    
    window.transportHighlights.forEach(highlight => {
        const x = (highlight.x * TILESIZE) + (TILESIZE / 2);
        const y = (highlight.y * TILESIZE) + (TILESIZE / 2);
        
        let color, strokeColor;
        switch(highlight.type) {
            case 'loadable-transport':
                color = 'rgba(76, 175, 80, 0.3)'; // Green with transparency
                strokeColor = '#4CAF50';
                break;
            case 'exit-position':
                color = 'rgba(33, 150, 243, 0.3)'; // Blue with transparency  
                strokeColor = '#2196F3';
                break;
            default:
                color = 'rgba(255, 193, 7, 0.3)'; // Yellow with transparency
                strokeColor = '#FFC107';
        }
        
        // Create highlight rectangle
        const highlightRect = two.makeRectangle(x, y, TILESIZE - 4, TILESIZE - 4);
        highlightRect.fill = color;
        highlightRect.stroke = strokeColor;
        highlightRect.linewidth = TRANSPORT_BORDER_WIDTH;
        
        // Add to highlight group
        transportHighlightGroup.add(highlightRect);
    });
    
    // Add the group to the scene
    two.add(transportHighlightGroup);
}

// Custom cargo indicator functions removed - using authentic AW load icon from tileset instead

async function createScene() {
    // create game tiles
    for (var i = 0; i < board.height; i++) {
        for (var j = 0; j < board.width; j++) {
            var tile = board.grid[j + i * board.width];
            // create map file
            makeMapTile(tile);
            // create sprite with proper await for canvas texture generation
            if (tile.unit !== null) {
                await makeSprite(tile);
            }
        }
    }
    renderTransportIndicators();
}

// =============================================================================
// PHASE 2A: ENHANCED COMBAT FUNCTIONS
// =============================================================================

// Enhanced attack with preview (replaces your partial function)
function unitAttackWithPreview(tile) {
    // First show combat preview
    showCombatPreview(board.selected.x, board.selected.y, tile.x, tile.y);
}

// Combat preview function (corrected version)
async function showCombatPreview(attackerX, attackerY, defenderX, defenderY) {
    try {
        const result = await jsonrpc('combat_preview', {
            attacker_x: attackerX,
            attacker_y: attackerY,
            defender_x: defenderX,
            defender_y: defenderY
        });
        
        if (result.success) {
            showCombatPreviewModal(result, attackerX, attackerY, defenderX, defenderY);
        } else {
            alert('Cannot preview combat: ' + result.error);
            // Fallback to regular attack
            unitAttackRegular(defenderX, defenderY);
        }
    } catch (error) {
        console.error('Combat preview error:', error);
        // Fallback to regular attack
        unitAttackRegular(defenderX, defenderY);
    }
}

// Enhanced attack execution 
async function enhancedAttack(attackerX, attackerY, defenderX, defenderY) {
    try {
        const result = await jsonrpc('unit_attack_enhanced', {
            attacker_x: attackerX,
            attacker_y: attackerY,
            defender_x: defenderX,
            defender_y: defenderY
        });
        
        if (result.success) {
            showCombatResult(result.combat_result);
            
            // Check if game ended
            if (result.game_ended && result.winner) {
                setTimeout(() => {
                    alert(`🎉 GAME OVER! ${result.winner} WINS! 🎉`);
                }, 1000);
            }
            
            // ADDED: Return success so we can chain endUnitTurn()
            return result;
        } else {
            alert('Attack failed: ' + result.error);
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('Enhanced attack error:', error);
        alert('Attack failed: ' + error.message);
        throw error;
    }
}

// Show combat preview modal (integrates with your existing modal system)
function showCombatPreviewModal(previewData, attackerX, attackerY, defenderX, defenderY) {
    const modalContent = `
        <span class="close">&times;</span>
        <h3>Combat Preview</h3>
        <div style="display: flex; justify-content: space-between; margin: 15px 0;">
            <div style="flex: 1; margin: 0 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px;">
                <h4>Your Attack</h4>
                <p><strong>Damage:</strong> ${previewData.attacker_damage}</p>
                <p><strong>Range:</strong> ${previewData.damage_range}</p>
                ${previewData.terrain_bonus > 0 ? `<p><em>Enemy has +${previewData.terrain_bonus} terrain defense</em></p>` : ''}
                ${previewData.ammo_warning ? '<p style="color: red;"><em>⚠ Low ammo!</em></p>' : ''}
            </div>
            <div style="flex: 1; margin: 0 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px;">
                <h4>Counter Attack</h4>
                ${previewData.can_counter ? 
                    `<p><strong>Damage:</strong> ${previewData.counter_damage}</p>
                     <p style="color: orange;"><em>Enemy can counter!</em></p>` :
                    '<p style="color: green;"><em>No counter attack</em></p>'
                }
            </div>
            <div style="flex: 1; margin: 0 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px;">
                <h4>Result</h4>
                <p><strong>Your HP:</strong> ${previewData.attacker_hp_after}</p>
                <p><strong>Enemy HP:</strong> ${previewData.defender_hp_after}</p>
                ${previewData.defender_destroyed ? '<p style="color: green;"><strong>Enemy destroyed!</strong></p>' : ''}
                ${previewData.attacker_destroyed ? '<p style="color: red;"><strong>You will be destroyed!</strong></p>' : ''}
            </div>
        </div>
        <div style="text-align: center; margin-top: 20px;">
            <button onclick="confirmCombat(${attackerX}, ${attackerY}, ${defenderX}, ${defenderY})" 
                    style="margin: 0 10px; padding: 10px 20px; font-size: 16px; background: #d9534f; color: white; border: none; border-radius: 5px; cursor: pointer;">
                Attack!
            </button>
            <button onclick="cancelCombat()" 
                    style="margin: 0 10px; padding: 10px 20px; font-size: 16px; background: #6c757d; color: white; border: none; border-radius: 5px; cursor: pointer;">
                Cancel
            </button>
        </div>
    `;
    
    // Use your existing modal system
    const modal = document.getElementById('modalcreate');
    const modalContentDiv = modal.querySelector('.modal-content');
    
    // Store original content to restore later
    window.originalModalContent = modalContentDiv.innerHTML;
    
    // Replace with combat preview
    modalContentDiv.innerHTML = modalContent;
    modal.style.display = 'block';
    
    // Add close button functionality
    const closeBtn = modal.querySelector('.close');
    closeBtn.onclick = cancelCombat;
}

// Confirm combat attack
function confirmCombat(attackerX, attackerY, defenderX, defenderY) {
    // Close modal
    cancelCombat();
    
    // Execute enhanced attack
    enhancedAttack(attackerX, attackerY, defenderX, defenderY).then(() => {
        // ADDED: End unit turn after enhanced attack
        endUnitTurn();
    }).catch((error) => {
        console.error('❌ Enhanced attack failed:', error);
        endUnitTurn();
    });
}

// Cancel combat preview
function cancelCombat() {
    const modal = document.getElementById('modalcreate');
    const modalContentDiv = modal.querySelector('.modal-content');
    
    // Restore original modal content
    if (window.originalModalContent) {
        modalContentDiv.innerHTML = window.originalModalContent;
    }
    
    modal.style.display = 'none';
}

// Show combat result briefly
function showCombatResult(combatResult) {
    
    // You could add a visual notification here later
}

// Regular attack fallback
function unitAttackRegular(defenderX, defenderY) {
    jsonrpc('unit_attack', {
        x: board.selected.x, 
        y: board.selected.y, 
        x2: defenderX, 
        y2: defenderY
    });
}

function executeAttack(targetTile) {
    
    if (!board.selected || !board.selected.unit) {
        console.error('❌ No unit selected for attack');
        return;
    }
    
    var attacker = board.selected;
    
    jsonrpc('unit_attack', {
        x: attacker.x,
        y: attacker.y,
        x2: targetTile.x,
        y2: targetTile.y
    }, function(result) {
        clearAllHighlights();
        board.selected = null;
        
        if (result && result.game_over) {
            alert(`Game Over! ${result.winner} wins!`);
        }
        
        update();
    });
}

// =============================================================================
// ATTACK RANGE HIGHLIGHTING
// =============================================================================

//highlightAttackRange function
function highlightAttackRange(unitX, unitY) {
    jsonrpc('get_attack_targets', {
        unit_x: unitX,
        unit_y: unitY
    }).then(result => {
        if (result && result.success) {
            clearRangeHighlights();
            
            result.targets.forEach(target => {
                highlightTile(target.x, target.y, 'attack-range');
            });
            
        }
    }).catch(error => {
        console.error('Failed to get attack targets:', error);
    });
}

// Clear range highlights
function clearRangeHighlights() {
    // Since we're using Two.js canvas, we'll need to re-render
    // For now, just log that we're clearing highlights
    // The next board update will clear the highlights automatically
}

// Highlight a specific tile (Two.js version)
function highlightTile(x, y, className) {
    // For Two.js, we'll add visual indicators during rendering
    // Store the highlighted tiles for the next render cycle
    if (!window.highlightedTiles) {
        window.highlightedTiles = [];
    }
    
    window.highlightedTiles.push({
        x: x,
        y: y,
        type: className
    });
    
}

// Enhanced unit selection with range display
function unitSelectWithRange(tile) {
    jsonrpc('unit_select', {x: tile.x, y: tile.y});
    
    // Show attack range for selected unit
    if (tile.unit && tile.unit.army === board.current_turn) {
        highlightAttackRange(tile.x, tile.y);
    } else {
        clearRangeHighlights();
    }
}

// =============================================================================
// TRANSPORT SYSTEM FRONTEND INTEGRATION - Add to your render.js
// =============================================================================

// Global variables for transport state
let transportHighlights = {
    loadableUnits: [],
    unloadPositions: [],
    selectedTransport: null
};

// =============================================================================
// TRANSPORT HIGHLIGHT MANAGEMENT
// =============================================================================

function clearTransportHighlights() {
    // Remove all transport-related CSS classes
    const tiles = document.querySelectorAll('.tile');
    tiles.forEach(tile => {
        tile.classList.remove('loadable-unit', 'unload-position');
    });
    
    transportHighlights = {
        loadableUnits: [],
        unloadPositions: [],
        selectedTransport: null
    };
}

function showLoadableUnitsHighlight(transportX, transportY) {
    clearTransportHighlights();
    
    // Fix: Use jsonrpc instead of rpcCall and correct parameter format
    jsonrpc('get_loadable_units', {x: transportX, y: transportY}, function(result) {
        if (result.success && result.loadable_units) {
            transportHighlights.loadableUnits = result.loadable_units;
            transportHighlights.selectedTransport = {x: transportX, y: transportY};
            
            // Note: Since you're using Two.js canvas, highlighting will be different
            // For now, just store the highlights and show feedback
            showTransportFeedback(`${result.loadable_units.length} units can be loaded. Ctrl+Click to load.`);
        } else {
            showTransportFeedback("No units available to load.");
        }
    });
}

function showUnloadPositionsHighlight(transportX, transportY) {
    clearTransportHighlights();
    
    // Fix: Use jsonrpc instead of rpcCall and correct parameter format
    jsonrpc('get_unload_positions', {x: transportX, y: transportY}, function(result) {
        if (result.success && result.valid_positions) {
            transportHighlights.unloadPositions = result.valid_positions;
            transportHighlights.selectedTransport = {x: transportX, y: transportY};
            
            showTransportFeedback(`${result.valid_positions.length} positions available. Alt+Click to unload.`);
        } else {
            showTransportFeedback("No valid unload positions.");
        }
    });
}

function attemptLoadUnit(transportX, transportY, cargoX, cargoY) {
    jsonrpc('load_unit', {
        transport_x: transportX, 
        transport_y: transportY, 
        cargo_x: cargoX, 
        cargo_y: cargoY
    }, function(result) {
        if (result.success) {
            showTransportFeedback(result.message);
            clearTransportHighlights();
            update(); // Refresh the board
        } else {
            showTransportFeedback(`Load failed: ${result.error || result.message}`);
        }
    });
}

function attemptUnloadUnit(transportX, transportY, unloadX, unloadY, cargoIndex = 0) {
    jsonrpc('unload_unit', {
        transport_x: transportX, 
        transport_y: transportY, 
        unload_x: unloadX, 
        unload_y: unloadY, 
        cargo_index: cargoIndex
    }, function(result) {
        if (result.success) {
            showTransportFeedback(result.message);
            clearTransportHighlights();
            update(); // Refresh the board
        } else {
            showTransportFeedback(`Unload failed: ${result.error || result.message}`);
        }
    });
}

function showTransportFeedback(message) {
    // Remove existing feedback
    const existingFeedback = document.getElementById('transport-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    
    // Create new feedback element
    const feedback = document.createElement('div');
    feedback.id = 'transport-feedback';
    feedback.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #2c3e50;
        color: white;
        padding: 10px 15px;
        border-radius: 5px;
        z-index: 1000;
        font-family: sans-serif;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    `;
    feedback.textContent = message;
    
    document.body.appendChild(feedback);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (feedback && feedback.parentNode) {
            feedback.remove();
        }
    }, 3000);
}

function showCargoInfo(unit, cargoInfo) {
    let message = `${unit.type}: `;
    
    if (!cargoInfo.is_transport) {
        message += "Not a transport unit";
    } else {
        message += `${cargoInfo.current_cargo}/${cargoInfo.max_capacity} cargo`;
        
        const cargoList = cargoInfo.cargo_list || cargoInfo.cargo_units || [];
        if (cargoList.length > 0) {
            const cargoTypes = cargoInfo.cargo_list.map(c => c.unit_type).join(', ');
            message += ` (${cargoTypes})`;
        }
    }
    
    showTransportFeedback(message);
}

// =============================================================================
// TRANSPORT CLICK HANDLING
// =============================================================================

function handleTransportOperations(tile, event) {
    // Only handle if we have the required functions
    if (!handleLoadingClick || !handleUnloadingClick) {
        return false;
    }
    
    try {
        // Handle Ctrl+Click for loading
        if (event.ctrlKey) {
            return handleLoadingClick(tile);
        }
        
        // Handle Alt+Click for unloading  
        if (event.altKey) {
            return handleUnloadingClick(tile);
        }
        
        return false; // No transport operation
    } catch (error) {
        console.error('TRANSPORT_FIX: Transport operation failed:', error);
        showTransportFeedback('Transport operation failed: ' + error.message, 'error');
        return false;
    }
}
function handleLoadingClick(tile) {
    // Check if this tile has a loadable unit highlighted
    const isLoadable = transportHighlights.loadableUnits.some(unit => 
        unit.x === tile.x && unit.y === tile.y
    );
    
    if (isLoadable && transportHighlights.selectedTransport) {
        attemptLoadUnit(
            transportHighlights.selectedTransport.x,
            transportHighlights.selectedTransport.y,
            tile.x,
            tile.y
        );
        return true; // Transport operation handled
    }
    
    return false;
}

function handleUnloadingClick(tile) {
    // Check if this tile is a valid unload position
    const isUnloadable = transportHighlights.unloadPositions.some(pos => 
        pos.x === tile.x && pos.y === tile.y
    );
    
    if (isUnloadable && transportHighlights.selectedTransport) {
        // For now, always unload first cargo unit (index 0)
        attemptUnloadUnit(
            transportHighlights.selectedTransport.x,
            transportHighlights.selectedTransport.y,
            tile.x,
            tile.y,
            0
        );
        return true; // Transport operation handled
    }
    
    return false;
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

function getTileElement(x, y) {
    // This function should return the DOM element for the tile at (x, y)
    // You'll need to implement this based on your existing tile rendering system
    // For example:
    const tiles = document.querySelectorAll('.tile');
    for (let tileElement of tiles) {
        const tileData = tileElement.tileData; // Assuming you store tile data here
        if (tileData && tileData.x === x && tileData.y === y) {
            return tileElement;
        }
    }
    return null;
}

function getTransportStatus() {
    jsonrpc('get_transport_units', {}, function(result) {
        if (result.success) {
            result.transport_units.forEach(transport => {
            });
        }
    });
}

// =============================================================================
// KEYBOARD SHORTCUTS (Optional)
// =============================================================================

document.addEventListener('keydown', function(event) {
    // 'T' key to show transport status
    if (event.key === 't' || event.key === 'T') {
        getTransportStatus();
    }
    
    // 'C' key to clear transport highlights
    if (event.key === 'c' || event.key === 'C') {
        clearTransportHighlights();
    }
});

// =============================================================================
// INITIALIZATION
// =============================================================================

function initializeTransportSystem() {
    
    // Add CSS for transport highlights if not already added
    if (!document.getElementById('transport-styles')) {
        const style = document.createElement('style');
        style.id = 'transport-styles';
        style.textContent = `
            .loadable-unit {
                outline: 2px solid #00ff00 !important;
                background-color: rgba(0, 255, 0, 0.2) !important;
            }
            
            .unload-position {
                outline: 2px solid #0080ff !important;
                background-color: rgba(0, 128, 255, 0.2) !important;
            }
        `;
        document.head.appendChild(style);
    }
}

function rpcCall(method, params, callback) {
    return jsonrpc(method, params[0], callback);
}

function updateBoard() {
    update();
}

function clearIndicators() {
    // Clear any existing indicators
    // Since you're using Two.js, this might be handled by the next render
}

function gameToken() {
    return token;
}

// =============================================================================
// MOVEMENT HIGHLIGHTING SYSTEM FIX
// Add this to your render.js file
// =============================================================================

// Global variables for movement highlighting
window.movementHighlights = [];
window.movementHighlightGroup = null;

// =============================================================================
// MOVEMENT RANGE CALCULATION AND HIGHLIGHTING
// =============================================================================

function highlightMovementRange(unitX, unitY) {
    
    // Get movement range data from backend
    jsonrpc('get_unit_valid_moves', {x: unitX, y: unitY})
        .then(result => {
            if (result && result.success && result.moves) {
                clearMovementHighlights();
                
                result.moves.forEach(move => {
                    highlightMovementTile(move.x, move.y, 'movement-range');
                });
                
            } else {
                // Fallback: calculate movement range locally
                calculateMovementRangeLocally(unitX, unitY);
            }
        })
        .catch(error => {
            console.error('Movement range request failed:', error);
            // Fallback: calculate movement range locally
            calculateMovementRangeLocally(unitX, unitY);
        });
}

function calculateMovementRangeLocally(unitX, unitY) {
    
    // Don't clear if we already have highlights from a previous source
    if (window.movementHighlights && window.movementHighlights.length > 0) {
        return;
    }
    
    // Get the selected unit
    var selectedUnit = null;
    var selectedTile = board.grid.find(t => t.x === unitX && t.y === unitY);
    if (selectedTile && selectedTile.unit) {
        selectedUnit = selectedTile.unit;
    }
    
    if (!selectedUnit) {
        return;
    }
    
    // Basic movement range calculation (adjust based on your game rules)
    var movementRange = getUnitMovementRange(selectedUnit);
    
    // Check all tiles within movement range
    for (var x = 0; x < board.width; x++) {
        for (var y = 0; y < board.height; y++) {
            if (x === unitX && y === unitY) continue; // Skip current position
            
            var distance = Math.abs(x - unitX) + Math.abs(y - unitY); // Manhattan distance
            if (distance <= movementRange) {
                var targetTile = board.grid.find(t => t.x === x && t.y === y);
                if (targetTile && canUnitMoveToTile(selectedUnit, targetTile)) {
                    highlightMovementTile(x, y, 'movement-range');
                }
            }
        }
    }
    
    // Render the highlights after calculation
    renderMovementHighlights();
}

function calculateMovementWithCosts(startX, startY, maxMovement, unit) {
    var validMoves = [];
    var visited = new Set();
    var queue = [{x: startX, y: startY, cost: 0}];
    
    while (queue.length > 0) {
        var current = queue.shift();
        var key = `${current.x},${current.y}`;
        
        if (visited.has(key)) continue;
        visited.add(key);
        
        // Add this position as a valid move (except starting position)
        if (current.cost > 0 && current.cost <= maxMovement) {
            var targetTile = board.grid.find(t => t.x === current.x && t.y === current.y);
            if (targetTile && canUnitMoveToTile(unit, targetTile)) {
                validMoves.push({x: current.x, y: current.y, cost: current.cost});
            }
        }
        
        // Explore adjacent tiles if we haven't used all movement
        if (current.cost < maxMovement) {
            var directions = [
                {dx: 0, dy: 1},  // Down
                {dx: 0, dy: -1}, // Up
                {dx: 1, dy: 0},  // Right
                {dx: -1, dy: 0}  // Left
            ];
            
            directions.forEach(dir => {
                var newX = current.x + dir.dx;
                var newY = current.y + dir.dy;
                var newKey = `${newX},${newY}`;
                
                // Check bounds
                if (newX >= 0 && newX < board.width && newY >= 0 && newY < board.height && !visited.has(newKey)) {
                    var targetTile = board.grid.find(t => t.x === newX && t.y === newY);
                    if (targetTile) {
                        var moveCost = getTerrainMovementCost(unit, targetTile.mapTile.type);
                        var newCost = current.cost + moveCost;
                        
                        // Only add to queue if we can afford the movement cost
                        if (newCost <= maxMovement && canUnitTraverseTerrain(unit, targetTile.mapTile.type)) {
                            queue.push({x: newX, y: newY, cost: newCost});
                        }
                    }
                }
            });
        }
    }
    
    return validMoves;
}
function getUnitMovementRange(unit) {
    // Use actual Advance Wars movement values from config.ini
    var movementRanges = {
        'INFANTRY': 3,      // From config: move = 3
        'MECH': 2,          // From config: move = 2  
        'RECON': 8,         // From config: move = 8
        'TANK': 6,          // From config: move = 6
        'MEDIUMTANK': 5,    // From config: move = 5
        'ANTIAIR': 6,       // From config: move = 6
        'ARTILLERY': 5,     // From config: move = 5
        'BCOPTER': 6,       // From config: move = 6
        'BATTLESHIP': 5,    // From config: move = 5
        'BLACKBOAT': 7,     // From config: move = 7
        'BOMBER': 7,        // From config: move = 7
        'CARRIER': 5,       // From config: move = 5
        'CRUISER': 6,       // From config: move = 6
        'FIGHTER': 9,       // From config: move = 9
        'LANDER': 6,        // From config: move = 6
        'MEGATANK': 4,      // From config: move = 4
        'MISSILE': 4,       // From config: move = 4
        'NEOTANK': 6,       // From config: move = 6
        'PIPERUNNER': 9,    // From config: move = 9
        'ROCKET': 5,        // From config: move = 5
        'STEALTH': 6,       // From config: move = 6
        'SUB': 5,           // From config: move = 5
        'TCOPTER': 6,       // From config: move = 6
        'APC': 6            // From config: move = 6
    };
    
    return movementRanges[unit.type] || 3;
}

function canUnitMoveToTile(unit, tile) {
    // Basic movement validation
    // You can expand this based on your game's terrain rules
    
    // Can't move to occupied tiles (except for transports)
    if (tile.unit) {
        // Allow moving to friendly transports for loading
        if (tile.unit.army === unit.army && isTransportUnit(tile.unit)) {
            return true;
        }
        return false;
    }
    
    // Can't move to enemy properties (usually)
    if (tile.mapTile && tile.mapTile.army && tile.mapTile.army !== unit.army) {
        // Some properties like cities can be moved to for capture
        var capturableTypes = ['CITY', 'FACTORY', 'AIRPORT', 'PORT'];
        if (capturableTypes.includes(tile.mapTile.type)) {
            return unit.can_capture; // Only if unit can capture
        }
        return false;
    }
    
    // Check terrain restrictions
    if (tile.mapTile && tile.mapTile.type) {
        return canUnitTraverseTerrain(unit, tile.mapTile.type);
    }
    
    return true; // Default: can move
}

function canUnitTraverseTerrain(unit, terrainType) {
    // Define terrain movement rules
    // This is a simplified version - expand based on your game rules
    
    var landUnits = ['INFANTRY', 'MECH', 'RECON', 'TANK', 'MD_TANK', 'NEOTANK', 
                     'APC', 'ARTILLERY', 'ROCKET', 'ANTI_AIR', 'MISSILE'];
    var seaUnits = ['BATTLESHIP', 'CRUISER', 'LANDER', 'SUB'];
    var airUnits = ['FIGHTER', 'BOMBER', 'B_COPTER', 'T_COPTER'];
    
    // Sea units can only move on sea/reef
    if (seaUnits.includes(unit.type)) {
        return ['SEA', 'REEF'].includes(terrainType);
    }
    
    // Air units can move anywhere
    if (airUnits.includes(unit.type)) {
        return true;
    }
    
    // Land units can't move on sea
    if (landUnits.includes(unit.type)) {
        return !['SEA', 'REEF'].includes(terrainType);
    }
    
    return true; // Default
}

// =============================================================================
// MOVEMENT HIGHLIGHTING VISUAL FUNCTIONS
// =============================================================================

function highlightMovementTile(x, y, className) {
    // Add to movement highlights array
    if (!window.movementHighlights) {
        window.movementHighlights = [];
    }
    
    window.movementHighlights.push({
        x: x,
        y: y,
        type: className
    });
    
}

function clearMovementHighlights() {
    // Clear visual highlights in Two.js ONLY
    if (window.movementHighlightGroup && window.two) {
        window.two.remove(window.movementHighlightGroup);
        window.movementHighlightGroup = null;
    }
    
}

function renderMovementHighlights() {
    if (!window.movementHighlights || !window.two || window.movementHighlights.length === 0) {
        return;
    }
    
    // Clear existing visual highlights only
    if (window.movementHighlightGroup) {
        window.two.remove(window.movementHighlightGroup);
    }
    
    // Create new highlight group
    window.movementHighlightGroup = window.two.makeGroup();
    
    var renderedCount = 0;
    window.movementHighlights.forEach(highlight => {
        try {
            var rect = window.two.makeRectangle(
                highlight.x * TILESIZE + TILESIZE/2, 
                highlight.y * TILESIZE + TILESIZE/2, 
                TILESIZE - 2, 
                TILESIZE - 2
            );
            
            // Subtle yellow highlighting
            rect.stroke = '#B8860B';
            rect.fill = 'rgba(255, 248, 220, 0.2)';
            rect.linewidth = 1;
            rect.noFill = false;
            
            window.movementHighlightGroup.add(rect);
            renderedCount++;
        } catch (error) {
            console.error('Error creating highlight rect:', error);
        }
    });
    
    // Force Two.js update
    try {
        window.two.update();
    } catch (error) {
        console.error('Error updating Two.js:', error);
    }
}

function clearMovementHighlightsData() {
    // Clear the data array
    if (window.movementHighlights) {
        window.movementHighlights = [];
    }
}

// =============================================================================
// ENHANCED UNIT SELECTION WITH MOVEMENT HIGHLIGHTING
// =============================================================================

function unitSelectWithMovementHighlighting(tile) {
    
    try {
        // Step 1: Basic unit selection
        jsonrpc('unit_select', {x: tile.x, y: tile.y}).then(result => {
            if (result && !result.error) {
                // Set board selection
                board.selected = tile;
                
                // Step 2: Show movement range for selected unit
                if (tile.unit && tile.unit.army === board.current_turn) {
                    highlightMovementRange(tile.x, tile.y);
                    
                    // Step 3: Also show attack range if desired
                    if (typeof highlightAttackRange === 'function') {
                        setTimeout(() => {
                            highlightAttackRange(tile.x, tile.y);
                        }, 100);
                    }
                } else {
                    clearMovementHighlights();
                }
                
                // Step 4: Handle transport functionality if available
                if (typeof handleTransportSelectionLogic === 'function') {
                    handleTransportSelectionLogic(tile);
                }
            } else {
                console.error('Unit selection failed:', result);
            }
        });
        
    } catch (error) {
        console.error('Selection error:', error);
        // Fallback to basic selection
        jsonrpc('unit_select', {x: tile.x, y: tile.y});
    }
}

// =============================================================================
// INTEGRATION WITH EXISTING RENDERING SYSTEM
// =============================================================================

// Override or add to your existing createScene function
function addMovementHighlightsToScene() {
    if (window.movementHighlights && window.movementHighlights.length > 0) {
        renderMovementHighlights();
    }
}

// Call this in your main render/update loop
function updateMovementHighlights() {
    if (window.movementHighlights && window.movementHighlights.length > 0) {
        renderMovementHighlights();
    }
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

// =============================================================================
// INITIALIZATION AND EXPORTS
// =============================================================================

// Make functions available globally
window.highlightMovementRange = highlightMovementRange;
window.clearMovementHighlights = clearMovementHighlights;
window.unitSelectWithMovementHighlighting = unitSelectWithMovementHighlighting;
window.addMovementHighlightsToScene = addMovementHighlightsToScene;
window.updateMovementHighlights = updateMovementHighlights;
// =============================================================================
// ADVANCE WARS MOVEMENT SYSTEM - Complete Implementation
// Replace your existing movement and selection functions with these
// =============================================================================

// Enhanced selection state management
window.gameState = {
    selectedUnit: null,
    movementPhase: false, // true when unit has moved but not acted
    showingAttackTargets: false,
    movementHighlights: [],
    attackHighlights: []
};

// =============================================================================
// ENHANCED UNIT SELECTION WITH ADVANCE WARS LOGIC
// =============================================================================

function advanceWarsUnitSelect(tile) {
    
    try {
        // Step 1: Backend unit selection
        jsonrpc('unit_select', {x: tile.x, y: tile.y}).then(result => {
            if (result && !result.error) {
                // Set selection state
                board.selected = tile;
                window.gameState.selectedUnit = tile;
                window.gameState.movementPhase = false;
                window.gameState.showingAttackTargets = false;
                // Show movement range
                if (tile.unit && tile.unit.army === board.current_turn) {
                    clearAllHighlights();
                    showMovementRange(tile.x, tile.y);
                } else {
                    clearAllHighlights();
                }
                
                // Handle transport functionality if available
                if (typeof handleTransportSelectionLogic === 'function') {
                    setTimeout(() => {
                        handleTransportSelectionLogic(tile);
                    }, 100);
                }
            } else {
                console.error('Unit selection failed:', result);
            }
        });
        
    } catch (error) {
        console.error('Selection error:', error);
        jsonrpc('unit_select', {x: tile.x, y: tile.y});
    }
}

// =============================================================================
// MOVEMENT AND ATTACK LOGIC
// =============================================================================

function advanceWarsMove(targetTile) {
    if (!window.gameState.selectedUnit) {
        return false;
    }
    
    var source = window.gameState.selectedUnit;
    
    jsonrpc('unit_move', {
        x: source.x, 
        y: source.y, 
        x2: targetTile.x, 
        y2: targetTile.y
    }).then(result => {
        if (result && !result.error) {
            
            // CRITICAL FIX: Update position immediately
            window.gameState.selectedUnit = {
                x: targetTile.x,
                y: targetTile.y
            };
            
            // Enter movement phase
            window.gameState.movementPhase = true;
            // Clear movement highlights
            clearMovementHighlights();
            
            // Show attack targets after movement with longer delay
            setTimeout(() => {
                showAttackTargetsAfterMove(targetTile.x, targetTile.y);
            }, 800); // Increased delay to ensure board update completes
            
        } else {
            console.error('❌ Move failed:', result);
        }
    }).catch(error => {
        console.error('❌ Move error:', error);
    });
    
    return true;
}

function showAttackTargetsAfterMove(unitX, unitY) {
    
    jsonrpc('get_attack_targets', {
        unit_x: unitX,
        unit_y: unitY
    }).then(result => {
        if (result && result.success && result.targets && result.targets.length > 0) {
            window.gameState.showingAttackTargets = true;
            clearAttackHighlights();
            
            result.targets.forEach(target => {
                highlightAttackTile(target.x, target.y);
            });
            
            renderAttackHighlights();
        } else {
            // No attack targets - unit is done
            endUnitTurn();
        }
    }).catch(error => {
        console.error('Failed to get attack targets:', error);
        endUnitTurn();
    });
}

function advanceWarsAttack(targetTile) {
    if (!window.gameState.selectedUnit || !window.gameState.showingAttackTargets) {
        return false;
    }
    
    var source = window.gameState.selectedUnit;
    
    // Use the updated coordinates from gameState
    if (typeof unitAttackWithPreview === 'function') {
        // For preview attacks, we need to modify the combat functions
        showCombatPreview(source.x, source.y, targetTile.x, targetTile.y);
    } else {
        // Direct attack with correct coordinates
        jsonrpc('unit_attack', {
            x: source.x,
            y: source.y, 
            x2: targetTile.x, 
            y2: targetTile.y
        }).then(result => {
            // IMPORTANT: End the unit's turn to clear all highlights
            endUnitTurn();
        }).catch(error => {
            console.error('❌ Attack failed:', error);
            // Also end turn on attack failure
            endUnitTurn();
        });
    }
    
    return true;
}

function endUnitTurn() {
    
    if (window.gameState && window.gameState.selectedUnit) {
        window.gameState.selectedUnit = null;
    }
    
    clearAllHighlights();
    
    // Clear transport state
    if (typeof frontendTransportState !== 'undefined') {
        frontendTransportState.showingLoadOptions = false;
        frontendTransportState.showingUnloadOptions = false;
        frontendTransportState.validUnloadPositions = [];
        frontendTransportState.selectedTransport = null;
    }
}

// =============================================================================
// INDIRECT UNIT MOVEMENT RESTRICTIONS (Advance Wars Rules)
// =============================================================================

function isIndirectUnit(unit) {
    if (!unit || !unit.type) return false;
    const indirectTypes = ['ARTILLERY', 'ROCKET', 'MISSILE'];
    return indirectTypes.includes(unit.type);
}

function hasMoved(unit) {
    // Indirect units cannot attack after moving
    // We detect movement by checking if can_move is false
    return !unit.can_move;
}

function checkIndirectUnitRestrictions(unitX, unitY) {
    const tile = board.grid.find(t => t.x === unitX && t.y === unitY);
    const unit = tile?.unit;
    
    if (unit && isIndirectUnit(unit) && hasMoved(unit)) {
        return true; // Restricted
    }
    
    return false; // Not restricted
}

// =============================================================================
// ATTACK HIGHLIGHTING SYSTEM
// =============================================================================

function highlightAttackTile(x, y) {
    if (!window.gameState.attackHighlights) {
        window.gameState.attackHighlights = [];
    }
    
    window.gameState.attackHighlights.push({
        x: x,
        y: y,
        type: 'attack-target'
    });
    
}

function clearAttackHighlights() {
    // Clear visual highlights
    if (window.attackHighlightGroup && window.two) {
        window.two.remove(window.attackHighlightGroup);
        window.attackHighlightGroup = null;
    }
    
    // Clear data
    if (window.gameState.attackHighlights) {
        window.gameState.attackHighlights = [];
    }
    
}

function renderAttackHighlights() {
    if (!window.gameState.attackHighlights || !window.two || window.gameState.attackHighlights.length === 0) {
        return;
    }
    
    // Clear existing visual highlights
    if (window.attackHighlightGroup) {
        window.two.remove(window.attackHighlightGroup);
    }
    
    // Create new highlight group
    window.attackHighlightGroup = window.two.makeGroup();
    
    var renderedCount = 0;
    window.gameState.attackHighlights.forEach(highlight => {
        try {
            var rect = window.two.makeRectangle(
                highlight.x * TILESIZE + TILESIZE/2, 
                highlight.y * TILESIZE + TILESIZE/2, 
                TILESIZE - 2, 
                TILESIZE - 2
            );
            
            // Red highlighting for attack targets
            rect.stroke = '#DC143C'; // Crimson red
            rect.fill = 'rgba(220, 20, 60, 0.3)'; // Semi-transparent red
            rect.linewidth = 2;
            rect.noFill = false;
            
            window.attackHighlightGroup.add(rect);
            renderedCount++;
        } catch (error) {
            console.error('Error creating attack highlight rect:', error);
        }
    });
    
    // Force Two.js update
    try {
        window.two.update();
    } catch (error) {
        console.error('Error updating Two.js:', error);
    }
}

// =============================================================================
// MOVEMENT HIGHLIGHTING (Enhanced)
// =============================================================================

function showMovementRange(unitX, unitY) {
    
    // Use the backend movement highlights RPC
    jsonrpc('get_movement_highlights', {x: unitX, y: unitY})
        .then(result => {
            if (result && result.success && result.moves) {
                applyMovementHighlights(result.moves);
            } else {
                calculateMovementRangeLocally(unitX, unitY);
            }
        })
        .catch(error => {
            calculateMovementRangeLocally(unitX, unitY);
        });
}

function applyMovementHighlights(moves) {
    // Clear existing highlights
    clearMovementHighlightsData();
    
    // Store new highlights
    window.movementHighlights = moves.map(move => ({
        x: move.x,
        y: move.y,
        type: 'movement-range'
    }));
    // Force immediate rendering
    renderMovementHighlights();
}

// =============================================================================
// ATTACK HIGHLIGHTING SYSTEM - ADD THESE FUNCTIONS
// =============================================================================

function showAttackTargets(unitX, unitY) {
    
    // Get the unit to check if it's indirect and has moved
    const tile = board.grid.find(t => t.x === unitX && t.y === unitY);
    const unit = tile?.unit;
    
    // CHECK: If indirect unit has moved, don't show attack targets
    if (unit && isIndirectUnit(unit) && hasMoved(unit)) {
        clearAttackHighlights();
        return;
    }
    
    jsonrpc('get_attack_targets', {
        unit_x: unitX,
        unit_y: unitY
    }, function(result) {
        if (result && result.success && result.targets && result.targets.length > 0) {
            
            // Clear existing attack highlights
            clearAttackHighlights();
            
            // Add new attack highlights
            result.targets.forEach(target => {
                highlightAttackTile(target.x, target.y);
            });
            
            // Render the highlights
            renderAttackHighlights();
            
        } else {
        }
    });
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

function clearAllHighlights() {
    
    // Clear movement highlights
    if (typeof clearMovementHighlights === 'function') {
        clearMovementHighlights();
    }
    
    // Clear transport highlights
    if (typeof clearTransportHighlights === 'function') {
        clearTransportHighlights();
    }
    
    // Clear any other highlights
    if (typeof clearAttackHighlights === 'function') {
        clearAttackHighlights();
    }
}

function isMovementHighlighted(x, y) {
    return window.movementHighlights && 
           window.movementHighlights.some(h => h.x === x && h.y === y);
}

function isAttackHighlighted(x, y) {
    return window.gameState.attackHighlights && 
           window.gameState.attackHighlights.some(h => h.x === x && h.y === y);
}

// =============================================================================
// ENHANCED CANVAS CLICK HANDLER
// =============================================================================

function advanceWarsCanvasClick(ev) {
    var x = ev.offsetX;
    var y = ev.offsetY;
    var tile = tileAt(x, y);
    
    // PRIORITY 0: New alt-click transport system (HIGHEST PRIORITY)
    if (ev.altKey && typeof handleTransportAltClick === 'function') {
        console.log('🔄 Processing alt-click through new transport system');
        const handled = handleTransportAltClick(tile, ev);
        if (handled) {
            console.log('✅ Alt-click handled by transport system, stopping propagation');
            return false; // Stop all further processing
        }
    }
    // PRIORITY 1: Frontend transport unload system (HIGHEST PRIORITY)
    if (typeof frontendTransportState !== 'undefined' && 
        frontendTransportState.showingUnloadOptions) {
        
        // Check if clicked position is valid for unload
        const isValidUnload = frontendTransportState.validUnloadPositions.some(pos => 
            pos.x === tile.x && pos.y === tile.y
        );
        
        if (isValidUnload) {
            if (typeof attemptUnloadUnit === 'function') {
                attemptUnloadUnit(tile);
            }
            return; // STOP - unload handled
        } else {
            // Close unload mode if clicking elsewhere
            if (typeof closeTransportMenu === 'function') {
                closeTransportMenu();
            }
            return; // STOP - don't continue processing
        }
    }
    
    // PRIORITY 2: Frontend transport load system
    if (typeof frontendTransportState !== 'undefined' && 
        frontendTransportState.showingLoadOptions) {
        
        if (tile.unit && frontendTransportState.transportInfo && 
            frontendTransportState.transportInfo.compatible_units.includes(tile.unit.type)) {
            if (typeof attemptLoadUnit === 'function') {
                attemptLoadUnit(tile);
            }
            return; // STOP - load handled
        } else {
            if (typeof closeTransportMenu === 'function') {
                closeTransportMenu();
            }
            return; // STOP - don't continue processing
        }
    }
    
    // PRIORITY 3: Alt-click system for legacy unload/load
    if (ev.altKey && window.gameState && window.gameState.selectedUnit) {
        
        const selectedTile = board.grid.find(t => 
            t.x === window.gameState.selectedUnit.x && t.y === window.gameState.selectedUnit.y
        );
        
        if (selectedTile && selectedTile.unit) {
            // Check if selected unit is a transport with cargo (UNLOAD)
            if (isTransportUnitForRender(selectedTile.unit) && getCargoCountForRender(selectedTile.unit) > 0) {
                
                jsonrpc('unit_unload', {
                    x: window.gameState.selectedUnit.x,
                    y: window.gameState.selectedUnit.y,
                    x2: tile.x,
                    y2: tile.y,
                    index: 0
                }, function(result) {
                    if (result.success) {
                        window.gameState.selectedUnit = null;
                        clearAllHighlights();
                        update();
                    } else {
                    }
                });
                return; // STOP - unload handled
            }
            // Check if selected unit is cargo and clicked tile has transport (LOAD)
            else if (tile.unit && isTransportUnitForRender(tile.unit)) {
                
                jsonrpc('unit_load', {
                    x: window.gameState.selectedUnit.x,
                    y: window.gameState.selectedUnit.y,
                    x2: tile.x,
                    y2: tile.y
                }, function(loadResult) {
                    if (loadResult.success) {
                        window.gameState.selectedUnit = null;
                        clearAllHighlights();
                        update();
                    } else {
                    }
                });
                return; // STOP - load handled
            }
        }
        
        return; // STOP - always stop after alt-click
    }
    
    // PRIORITY 4: Transport integration system (CONTROLLED)
    if (typeof handleTileClickWithTransport === 'function') {
        
        const transportHandled = handleTileClickWithTransport(tile, ev);
        if (transportHandled) {
            return; // STOP - transport integration handled it
        }
    }
    
    // PRIORITY 5: New transport system
    if (typeof window.transportSystem !== 'undefined' && 
        typeof window.transportSystem.handleTransportClick === 'function') {
        
        const newTransportHandled = window.transportSystem.handleTransportClick(tile, ev);
        if (newTransportHandled) {
            return; // STOP - new transport system handled it
        }
    }
    
    // PRIORITY 6: Normal movement system
    if (window.gameState && window.gameState.selectedUnit && tile.can_be_moved_to) {
        advanceWarsMove(window.gameState.selectedUnit, tile);
        return;
    }
    
    // PRIORITY 7: Attack system
    if (window.gameState && window.gameState.selectedUnit && tile.can_be_attacked) {
        advanceWarsAttack(window.gameState.selectedUnit, tile);
        return;
    }
    
    // PRIORITY 8: Unit selection
    if (tile.unit && tile.unit.army === board.current_turn) {
        advanceWarsUnitSelect(tile);
        return;
    }
    
    // PRIORITY 9: Deselect when clicking empty tiles
    if (window.gameState && window.gameState.selectedUnit) {
        endUnitTurn();
    }
}
// =============================================================================
// DOUBLE CLICK HANDLER
// =============================================================================

function advanceWarsDoubleClick(ev) {
    var x = ev.offsetX;
    var y = ev.offsetY;
    var tile = tileAt(x, y);
    // Double click on capturable properties
    if (tile.mapTile.type === 'CITY' ||
        tile.mapTile.type === 'BASE_TOWER_1' ||
        tile.mapTile.type === 'FACTORY' ||
        tile.mapTile.type === 'PORT' ||
        tile.mapTile.type === 'AIRPORT') {
        
        if (tile.unit &&
            tile.unit.can_capture &&
            tile.unit.army === board.current_turn) {
            if (tile.unit.type == 'INFANTRY' || tile.unit.type == 'MECH') {
                unitCapture(tile);
                endUnitTurn();
                return;
            }
        }
    }
    
    // Double click on any unit to wait
    if (tile.unit && tile.unit.army === board.current_turn) {
        unitWait(tile);
        endUnitTurn();
    }
}

// =============================================================================
// INITIALIZATION AND INTEGRATION
// =============================================================================

// Replace your existing canvasClick and canvasdblClick functions with these:
window.canvasClick = advanceWarsCanvasClick;
window.canvasdblClick = advanceWarsDoubleClick;

// Enhanced unit functions for end-of-turn cleanup
function unitWait(tile) {
    jsonrpc('unit_wait', {x: tile.x, y: tile.y});
}

function unitCapture(tile) {
    jsonrpc('capture_tile', {x: tile.x, y: tile.y});
}

// Make functions globally available
window.advanceWarsUnitSelect = advanceWarsUnitSelect;
window.advanceWarsMove = advanceWarsMove;
window.advanceWarsAttack = advanceWarsAttack;
window.endUnitTurn = endUnitTurn;
window.clearAllHighlights = clearAllHighlights;
window.showMovementRange = showMovementRange;
window.renderAttackHighlights = renderAttackHighlights;
// =============================================================================
// UNIT SPRITE TESTING SYSTEM
// =============================================================================

// Complete list of units from your config.ini
const ALL_UNIT_TYPES = [
    'INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 'ANTIAIR', 
    'ARTILLERY', 'BCOPTER', 'BATTLESHIP', 'BLACKBOAT', 'BLACKBOMB',
    'BOMBER', 'CARRIER', 'CRUISER', 'FIGHTER', 'LANDER', 'MEGATANK',
    'MISSILE', 'NEOTANK', 'PIPERUNNER', 'ROCKET', 'STEALTH', 'SUB',
    'TCOPTER', 'APC'
];

// Unit categories for organized testing
const UNIT_CATEGORIES = {
    LAND: ['INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 'ANTIAIR', 
           'ARTILLERY', 'MISSILE', 'NEOTANK', 'ROCKET', 'APC', 'MEGATANK', 'PIPERUNNER'],
    AIR: ['BCOPTER', 'BOMBER', 'FIGHTER', 'TCOPTER', 'BLACKBOMB', 'STEALTH'],
    SEA: ['BATTLESHIP', 'BLACKBOAT', 'CARRIER', 'CRUISER', 'LANDER', 'SUB']
};

// =============================================================================
// SPRITE TESTING FUNCTIONS
// =============================================================================

function testAllUnitSprites() {
    
    const results = {
        working: [],
        missing: [],
        errors: []
    };
    
    ALL_UNIT_TYPES.forEach(unitType => {
        try {
            const spriteInfo = getUnitSpriteInfo(unitType);
            if (spriteInfo.exists) {
                results.working.push(unitType);
            } else {
                results.missing.push(unitType);
            }
        } catch (error) {
            results.errors.push({unit: unitType, error: error.message});
        }
    });
    if (results.missing.length > 0) {
    }
    
    if (results.errors.length > 0) {
    }
    
    return results;
}

function getUnitSpriteInfo(unitType) {
    // Check if unit type has a case in the makeSprite function
    const spriteMapping = {
        'INFANTRY': true,     // Default case (no specific case needed)
        'MECH': true,
        'RECON': true,
        'TANK': true,
        'MEDIUMTANK': true,
        'ANTIAIR': true,
        'ARTILLERY': true,
        'MISSILE': true,
        'ROCKET': true,
        'APC': true,
        'NEOTANK': true,
        'FIGHTER': true,
        'BCOPTER': true,
        'TCOPTER': true,
        'BATTLESHIP': true,
        'LANDER': true,
        'CRUISER': true,
        'SUB': true,
        'BOMBER': true,
        'CARRIER': true,
        'BLACKBOAT': true,
        'MEGATANK': true,
        'PIPERUNNER': true,
        'BLACKBOMB': false,   // Need to check if implemented
        'STEALTH': false      // Need to check if implemented
    };
    
    return {
        exists: spriteMapping[unitType] !== false,
        implemented: spriteMapping[unitType] === true
    };
}

// =============================================================================
// UNIT CREATION TESTING
// =============================================================================

function testUnitCreation() {
    
    // Find factory tiles for each type
    const factories = board.grid.filter(tile => 
        tile.mapTile.type === 'FACTORY' && 
        tile.mapTile.army === board.current_turn &&
        tile.unit === null
    );
    
    const airports = board.grid.filter(tile => 
        tile.mapTile.type === 'AIRPORT' && 
        tile.mapTile.army === board.current_turn &&
        tile.unit === null
    );
    
    const ports = board.grid.filter(tile => 
        tile.mapTile.type === 'PORT' && 
        tile.mapTile.army === board.current_turn &&
        tile.unit === null
    );
    return {
        factories: factories,
        airports: airports,
        ports: ports,
        canTestLand: factories.length > 0,
        canTestAir: airports.length > 0,
        canTestSea: ports.length > 0
    };
}

function createTestUnit(unitType, army = 'RED') {
    
    // Find appropriate production facility
    let targetTile = null;
    
    if (UNIT_CATEGORIES.LAND.includes(unitType)) {
        targetTile = board.grid.find(tile => 
            tile.mapTile.type === 'FACTORY' && 
            tile.mapTile.army === army &&
            tile.unit === null
        );
    } else if (UNIT_CATEGORIES.AIR.includes(unitType)) {
        targetTile = board.grid.find(tile => 
            tile.mapTile.type === 'AIRPORT' && 
            tile.mapTile.army === army &&
            tile.unit === null
        );
    } else if (UNIT_CATEGORIES.SEA.includes(unitType)) {
        targetTile = board.grid.find(tile => 
            tile.mapTile.type === 'PORT' && 
            tile.mapTile.army === army &&
            tile.unit === null
        );
    }
    
    if (!targetTile) {
        return false;
    }
    
    // Create the unit via RPC
    jsonrpc('unit_create', {
        army: army,
        unit_type: unitType,
        x: targetTile.x,
        y: targetTile.y
    }).then(result => {
        if (result && !result.error) {
        } else {
        }
    }).catch(error => {
    });
    
    return true;
}

// =============================================================================
// SYSTEMATIC TESTING COMMANDS
// =============================================================================

function testLandUnits() {
    
    UNIT_CATEGORIES.LAND.forEach((unit, index) => {
        setTimeout(() => {
            createTestUnit(unit);
        }, index * 1000); // 1 second delay between creations
    });
}

function testAirUnits() {
    
    UNIT_CATEGORIES.AIR.forEach((unit, index) => {
        setTimeout(() => {
            createTestUnit(unit);
        }, index * 1000);
    });
}

function testSeaUnits() {
    
    UNIT_CATEGORIES.SEA.forEach((unit, index) => {
        setTimeout(() => {
            createTestUnit(unit);
        }, index * 1000);
    });
}

function testAllUnits() {
    
    let delay = 0;
    ALL_UNIT_TYPES.forEach(unit => {
        setTimeout(() => {
            createTestUnit(unit);
        }, delay * 1000);
        delay++;
    });
}

// =============================================================================
// SPRITE ANALYSIS
// =============================================================================

function analyzeBoardUnits() {
    
    const unitsOnBoard = board.grid.filter(tile => tile.unit !== null);
    const unitCounts = {};
    unitsOnBoard.forEach(tile => {
        const unitType = tile.unit.type;
        unitCounts[unitType] = (unitCounts[unitType] || 0) + 1;
        
    });
    
    Object.entries(unitCounts).forEach(([type, count]) => {
    });
    
    return {
        units: unitsOnBoard,
        counts: unitCounts,
        totalUnits: unitsOnBoard.length
    };
}

function checkMissingSprites() {
    
    // Units that might not have sprite cases
    const potentiallyMissing = ['BLACKBOMB', 'STEALTH'];
    
    potentiallyMissing.forEach(unit => {
        // Try to find this unit type in existing sprite switch statement
        const hasSprite = getUnitSpriteInfo(unit);
    });
}

// =============================================================================
// EXPORT TESTING FUNCTIONS
// =============================================================================

// Make functions globally available
window.testAllUnitSprites = testAllUnitSprites;
window.testUnitCreation = testUnitCreation;
window.createTestUnit = createTestUnit;
window.testLandUnits = testLandUnits;
window.testAirUnits = testAirUnits;
window.testSeaUnits = testSeaUnits;
window.testAllUnits = testAllUnits;
window.analyzeBoardUnits = analyzeBoardUnits;
window.checkMissingSprites = checkMissingSprites;
// =============================================================================
// PERMANENT CLICK SYSTEM FIXES - Added to fix factory clicks and unit selection
// =============================================================================

function applyCompleteClickFix() {
    
    // ========================================================================
    // FIX 1: Selection State Management
    // Prevents board.selected from being cleared during board updates
    // ========================================================================
    
    const originalUpdate = window.update;
    
    window.update = function() {
        // Store current selection info BEFORE update
        const currentSelection = board?.selected ? {
            x: board.selected.x,
            y: board.selected.y,
            unit: board.selected.unit
        } : null;
        
        // Call the original update
        originalUpdate();
        
        // Restore selection AFTER board is updated
        if (currentSelection) {
            setTimeout(() => {
                const restoredTile = board.grid.find(tile => 
                    tile.x === currentSelection.x && 
                    tile.y === currentSelection.y
                );
                
                if (restoredTile && restoredTile.unit) {
                    board.selected = restoredTile;
                    
                    // Show visual feedback
                    showSelectionVisuals(restoredTile);
                } else {
                }
            }, 50);
        }
    };
    
    // ========================================================================
    // FIX 2: Visual Feedback System
    // Shows movement highlights and attack targets when unit is selected
    // ========================================================================
    
    function showSelectionVisuals(tile) {
        
        try {
            // Show movement highlights
            if (typeof highlightMovementRange === 'function') {
                highlightMovementRange(tile.x, tile.y);
            } else if (typeof showMovementRange === 'function') {
                showMovementRange(tile.x, tile.y);
            }
            
            // Show attack targets
            if (typeof showAttackTargets === 'function') {
                setTimeout(() => {
                    showAttackTargets(tile.x, tile.y);
                }, 100);
            }
            
            // Force visual update
            if (window.two && window.two.update) {
                window.two.update();
            }
        } catch (error) {
            console.error('❌ Visual feedback error:', error);
        }
    }
    
    // ========================================================================
    // FIX 3: Production Building and Movement Click Handler
    // Handles factory clicks and movement execution properly
    // ========================================================================
    
    const originalTransportHandler = window.handleTileClickWithTransport;
    
    window.handleTileClickWithTransport = function(tile) {
        
        // PRIORITY 1: Production buildings (factories, airports, ports)
        if ((tile.mapTile.type === 'FACTORY' || 
             tile.mapTile.type === 'AIRPORT' || 
             tile.mapTile.type === 'PORT') &&
            tile.mapTile.army === board.current_turn &&
            !tile.unit) {
            
            if (tile.mapTile.type === 'FACTORY') unitCreate(tile);
            else if (tile.mapTile.type === 'AIRPORT') airunitCreate(tile);
            else if (tile.mapTile.type === 'PORT') seaunitCreate(tile);
            return;
        }
        
        // PRIORITY 2: Movement execution (clicking on highlighted movement tiles)
        if (board.selected && !tile.unit && 
            window.movementHighlights && 
            window.movementHighlights.some(h => h.x === tile.x && h.y === tile.y)) {
            
            executeMovement(tile);
            return;
        }
        
        // PRIORITY 3: Attack execution (clicking on highlighted attack targets)
        if (board.selected && tile.unit && 
            tile.unit.army !== board.current_turn &&
            window.gameState?.attackHighlights &&
            window.gameState.attackHighlights.some(h => h.x === tile.x && h.y === tile.y)) {
            
            executeAttack(tile);
            return;
        }
        
        // PRIORITY 4: Fall back to original transport logic
        if (originalTransportHandler) {
            originalTransportHandler(tile);
        }
    };
    
    // ========================================================================
    // FIX 4: Movement Execution with Highlight Clearing
    // Executes unit movement and clears highlights afterwards
    // ========================================================================
    
    window.executeMovement = function(targetTile) {
        
        if (!board.selected) {
            console.error('❌ No unit selected for movement');
            return;
        }
        
        const fromTile = board.selected;
        
        jsonrpc('unit_move', {
            x: fromTile.x,
            y: fromTile.y,
            x2: targetTile.x,
            y2: targetTile.y
        }).then(result => {
            if (result && !result.error) {
                
                // Clear all highlights and selection
                board.selected = null;
                if (window.movementHighlights) window.movementHighlights = [];
                if (window.gameState?.attackHighlights) window.gameState.attackHighlights = [];
                
                // Call clear functions
                ['clearMovementHighlights', 'clearAttackHighlights', 'clearTransportHighlights'].forEach(func => {
                    if (typeof window[func] === 'function') window[func]();
                });
                
                // Force visual update
                if (window.two?.update) window.two.update();
                
            } else {
            }
        }).catch(error => {
            console.error('❌ Movement error:', error);
        });
    };
    
    // ========================================================================
    // FIX 5: Enhanced Unit Selection
    // Ensures board.selected is set immediately when unit is clicked
    // ========================================================================
    
    const originalSelectWithTransport = window.selectUnitWithTransportOptions;
    
    window.selectUnitWithTransportOptions = function(tile) {
        
        // Set selection IMMEDIATELY
        board.selected = tile;
        
        // Show visual feedback
        showSelectionVisuals(tile);
        
        // Call original function
        if (originalSelectWithTransport) {
            originalSelectWithTransport(tile);
        }
    };
    
    // ========================================================================
    // UTILITY: Manual Clear Function for Debugging
    // ========================================================================
    
    window.clearAllHighlights = function() {
        
        // Clear all highlight arrays
        if (window.movementHighlights) window.movementHighlights = [];
        if (window.gameState && window.gameState.attackHighlights) window.gameState.attackHighlights = [];
        
        // Clear selection
        board.selected = null;
        if (window.gameState) {
            window.gameState.selectedUnit = null;
            window.gameState.movementPhase = false;
            window.gameState.showingAttackTargets = false;
        }
        
        // Call all clear functions
        const clearFunctions = [
            'clearMovementHighlights',
            'clearMovementHighlightsData', 
            'clearAttackHighlights',
            'clearTransportHighlights',
            'clearAllTransportHighlights'
        ];
        
        clearFunctions.forEach(funcName => {
            if (typeof window[funcName] === 'function') {
                try {
                    window[funcName]();
                } catch (e) {
                }
            }
        });
        
        // Force visual update
        if (window.two && window.two.update) {
            window.two.update();
        }
        
    };
    
}

// ========================================================================
// AUTO-APPLY THE FIXES WHEN PAGE LOADS
// ========================================================================

// Apply fixes when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(applyCompleteClickFix, 200);
});

// Also apply immediately if DOM is already loaded
if (document.readyState !== 'loading') {
    setTimeout(applyCompleteClickFix, 200);
}
// END OF CLICK SYSTEM FIXES