//
// Setup
//

// constants
const TILESIZE = 16;

// Transport visual constants
const TRANSPORT_HIGHLIGHT_OPACITY = 0.3;
const TRANSPORT_BORDER_WIDTH = 2;

// globals
var token = document.getElementById('draw').getAttribute('x-token');
var board = null;
var two = null;

// Transport rendering globals
var transportHighlightGroup = null;
var cargoIndicatorGroup = null;

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
    //const socket = io(document.location.scheme + document.location.host + '/');
    const socket = io('/');

    socket.on('connect', () => {
        console.log('socket connected');
        socket.emit('game', token);
    });
    socket.on('disconnect', () => {
        console.log('socket disconnected');
    });
    socket.on('update', (msg) => {
        console.log('update: ' + msg);
        update();
    });
    socket.on('message', (msg) => {
        console.log('message: ' + msg);
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
    if (!unit || !unit.status || !unit.status.cargo) return 0;
    
    // FIXED: Count non-null cargo slots properly
    let count = 0;
    if (Array.isArray(unit.status.cargo)) {
        for (let i = 0; i < unit.status.cargo.length; i++) {
            if (unit.status.cargo[i] !== null && unit.status.cargo[i] !== undefined) {
                count++;
            }
        }
    }
    return count;
}

function uuidv4() {
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
}

function rerender() {
    console.time('rerender');
    if (two) {
        two.clear();
        createScene();
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
    jsonrpc('game_board', {}, function(res) {
        // Preserve the current selection before updating board
        var previousSelection = board ? board.selected : null;
        
        // init globals
        board = res;
        
        // Restore selection if it existed
        if (previousSelection) {
            // Find the same tile in the new board data
            var restoredTile = board.grid.find(t => 
                t.x === previousSelection.x && t.y === previousSelection.y
            );
            if (restoredTile) {
                board.selected = restoredTile;
                console.log('🔄 Restored selection:', board.selected);
            }
        }
        
        // init globals
        board = res
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
                cargoIndicatorGroup = null;
                console.log('RENDER: Transport visual system initialized');
                console.log('Two.js initialized successfully');
                
                // canvas mouse handling
                var draw = document.getElementById('draw');
                var canvas = draw.children[0];
                if (canvas) {
                    canvas.onmousemove = canvasMove;
                    canvas.onclick = canvasClick;
                    canvas.ondblclick = canvasdblClick;
                }
            } catch (error) {
                console.error('Error initializing Two.js:', error);
                return;
            }
        }
        // render
        two.clear();
        createScene();
        // Add this before your existing two.update() call
        if (window.movementHighlights && window.movementHighlights.length > 0) {
            renderMovementHighlights();
        }
        two.update();
        // update info

        var gamebox = document.getElementById('gamebox');
        gamebox.innerText =
                           `Game info:
                             - Day: ${board.days}
                             - Current Turn: ${board.current_turn}
                             - Game Active: ${board.game_active}
                             Blue:
                             - Troops: ${board.total_blue_troops}
                             - Income: ${board.total_blue_properties}
                             - Funds: ${board.blue_funds}
                            Red:
                            - Troops: ${board.total_red_troops}
                            - Income: ${board.total_red_properties}
                            - Funds: ${board.red_funds}
                            `;

        var infobox = document.getElementById('infobox');
        infobox.innerText =
                        `Instructions:
                        - Single click: move, attack
                        -  + ctrl: load unit
                        -  + alt: unload unit
                        - Double click: capture, wait`;
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
    console.log('TRANSPORT_FIX: Cleaning up transport state for turn end');
    
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
                console.log('TRANSPORT_FIX: Could not remove transport highlight group:', e);
            }
        }
        transportHighlightGroup = null;
    }
    
    if (typeof cargoIndicatorGroup !== 'undefined' && cargoIndicatorGroup) {
        if (two && two.remove) {
            try {
                two.remove(cargoIndicatorGroup);
            } catch (e) {
                console.log('TRANSPORT_FIX: Could not remove cargo indicator group:', e);
            }
        }
        cargoIndicatorGroup = null;
    }
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
    jsonrpc('unit_move', {x: source.x, y: source.y, x2: target.x, y2: target.y});
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
                console.log('🚶 MOVING: Clicking on highlighted tile, attempting move');
                console.log(`Moving from (${board.selected.x}, ${board.selected.y}) to (${tile.x}, ${tile.y})`);
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
                    console.log('🔄 DESELECTING: Clicking same unit, deselecting');
                    
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
                    
                    console.log('✅ Unit deselected');
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
            console.log('🚶 MOVING: Using can_be_moved_to flag');
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
            console.log('🔄 DESELECTING: Clicking empty/enemy tile');
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
            
            console.log('✅ Deselected by clicking empty tile');
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
    console.log('SELECTION_FIX: Selecting unit with transport and range support');
    
    try {
        // Step 1: Basic unit selection (existing functionality)
        jsonrpc('unit_select', {x: tile.x, y: tile.y});
        
        // Step 2: Show attack range (existing functionality)  
        if (tile.unit && tile.unit.army === board.current_turn) {
            highlightAttackRange(tile.x, tile.y);
        } else {
            clearRangeHighlights();
        }
        
        // Step 3: Handle transport-specific functionality
        handleTransportSelectionLogic(tile);
        
    } catch (error) {
        console.error('SELECTION_FIX: Unit selection failed:', error);
        // Fallback to basic selection if transport logic fails
        jsonrpc('unit_select', {x: tile.x, y: tile.y});
    }
}

function handleTransportSelectionLogic(tile) {
    if (!tile.unit) {
        clearTransportHighlights();
        return;
    }
    
    // Get cargo/transport information
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
            } else {
                // Regular unit - clear any transport highlights
                clearTransportHighlights();
            }
            
            // Show cargo information to user
            showCargoInfo(tile.unit, cargoInfo);
        } else {
            // If cargo info fails, just clear highlights
            clearTransportHighlights();
        }
    });
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


function makeMapTile(tile) {
    var showMapTiles = document.getElementById('inputshowmap').checked;
    if (showMapTiles) {
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
                        break;
                        _2xHeight = true;
                    case 'BLUE':
                        y = y - 844;
                        _2xHeight = true;
                        break;
                    default:
                        y = y - 765;
                        break;
                }
                _2xHeight = true;
                break;
            case 'BASE_TOWER_0':
                x = x - 1;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 812;
                        break;
                        _2xHeight = true;
                    case 'BLUE':
                        y = y - 845;
                        _2xHeight = true;
                        break;
                    default:
                        y = y - 757;
                        break;
                }
                _2xHeight = true;
                break;
            case 'BASE_TOWER_1':
                x = x - 1;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 812;
                        break;
                        _2xHeight = true;
                    case 'BLUE':
                        y = y - 845;
                        _2xHeight = true;
                        break;
                    default:
                        y = y - 757;
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
                        break;
                        _2xHeight = true;
                    case 'BLUE':
                        y = y - 845;
                        _2xHeight = true;
                        break;
                    default:
                        y = y - 765;
                        break;
                }
                _2xHeight = true;
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
                x = x - 224;
                y = y - 146;
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
                console.log(tile.mapTile.type);
                return;
        }
        var tilesetSrc = '/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png';
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

function makeSprite(tile) {
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
            x = x - 17
            break;
        case 'MEGATANK':
            y = y - 512;
            x = x - 33
            break;
        case 'PIPERUNNER':
            y = y - 538;
            break;
    }
    if (!tile.unit.can_move && !tile.unit.can_attack)
        x = x - 336; // unavailable sprite
    var unitsSrc = '/static/img/aw2_blackhole_units_map_transparent.png';
    var spriteTexture = new Two.Texture(unitsSrc, () => ontextureLoad(unitsSrc));
    spriteTexture.offset = new Two.Vector(x, y);
    var rect = two.makeRectangle(tile.x * TILESIZE + TILESIZE/2, tile.y * TILESIZE + TILESIZE/2, SPRITESIZE, SPRITESIZE);
    rect.fill = spriteTexture;
    rect.stroke = 'transparent';
    var health = null;
    var fuel = null;
    var ammo = null;
    if (tile.unit.status.hp <= 90 && tile.unit.can_move ) {
        const HEALTHSIZE = SPRITESIZE/2;
        x = spriteSheetWidth/2 - HEALTHSIZE/2;
        y = spriteSheetHeight/2 - HEALTHSIZE/2;
        x = x - 557;
        y = y - 1234;
        var xMult = Math.ceil(tile.unit.status.hp / 10) - 1;
        x = x - xMult - xMult * HEALTHSIZE;
        var healthTexture = new Two.Texture(unitsSrc, () => ontextureLoad(unitsSrc));
        healthTexture.offset = new Two.Vector(x, y);
        health = two.makeRectangle(tile.x * TILESIZE + TILESIZE - HEALTHSIZE/2, tile.y * TILESIZE + TILESIZE - HEALTHSIZE/2, HEALTHSIZE, HEALTHSIZE);
        health.fill = healthTexture;
        health.stroke = 'transparent';
    }
    if (tile.unit.status.hp <= 90 && !tile.unit.can_move ) {
        const HEALTHSIZE = SPRITESIZE/2;
        x = spriteSheetWidth/2 - HEALTHSIZE/2;
        y = spriteSheetHeight/2 - HEALTHSIZE/2;
        x = x - 428;
        y = y - 1234;
        var xMult = Math.ceil(tile.unit.status.hp / 10) - 1;
        x = x - xMult - xMult * HEALTHSIZE;
        var healthTexture = new Two.Texture(unitsSrc, () => ontextureLoad(unitsSrc));
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
    
    // Render cargo indicators on transport units
    renderCargoIndicators();
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

function renderCargoIndicators() {
    // Clear existing cargo indicators
    if (cargoIndicatorGroup) {
        two.remove(cargoIndicatorGroup);
        cargoIndicatorGroup = null;
    }
    
    // Create new cargo indicator group
    cargoIndicatorGroup = two.makeGroup();
    
    // Check all tiles for transport units (using your existing board structure)
    if (!board || !board.grid) return;
    
    for (var i = 0; i < board.height; i++) {
        for (var j = 0; j < board.width; j++) {
            var tile = board.grid[j + i * board.width];
            
            if (tile.unit && isTransportUnitForRender(tile.unit)) {
                const cargoCount = getCargoCountForRender(tile.unit);
                if (cargoCount > 0) {
                    renderCargoCountBadge(tile.x, tile.y, cargoCount);
                    renderTransportBorder(tile.x, tile.y);
                }
            }
        }
    }
    
    // Add the group to the scene
    two.add(cargoIndicatorGroup);
}

function renderCargoCountBadge(tileX, tileY, count) {
    const x = (tileX * TILESIZE) + TILESIZE - 6;
    const y = (tileY * TILESIZE) + 6;
    
    // Create background circle
    const badgeBackground = two.makeCircle(x, y, 6);
    badgeBackground.fill = '#FFD700'; // Gold background
    badgeBackground.stroke = '#000000';
    badgeBackground.linewidth = 1;
    
    // Create text (Two.js text)
    const badgeText = two.makeText(count.toString(), x, y);
    badgeText.fill = '#000000';
    badgeText.size = 8;
    badgeText.weight = 'bold';
    badgeText.family = 'Arial, sans-serif';
    
    // Add to cargo indicator group
    cargoIndicatorGroup.add(badgeBackground);
    cargoIndicatorGroup.add(badgeText);
}

function renderTransportBorder(tileX, tileY) {
    const x = (tileX * TILESIZE) + (TILESIZE / 2);
    const y = (tileY * TILESIZE) + (TILESIZE / 2);
    
    // Create yellow border to indicate transport has cargo
    const border = two.makeRectangle(x, y, TILESIZE - 2, TILESIZE - 2);
    border.fill = 'transparent';
    border.stroke = '#FFD700'; // Gold border
    border.linewidth = 2;
    
    // Add to cargo indicator group
    cargoIndicatorGroup.add(border);
}

function createScene() {
    // create game tiles
    for (var i = 0; i < board.height; i++) {
        for (var j = 0; j < board.width; j++) {
            var tile = board.grid[j + i * board.width];
            // create map file
            makeMapTile(tile);
            // create sprite
            if (tile.unit !== null) {
                makeSprite(tile);
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
            console.log('Enhanced combat result:', result.combat_result);
            showCombatResult(result.combat_result);
            
            // Check if game ended
            if (result.game_ended && result.winner) {
                setTimeout(() => {
                    alert(`🎉 GAME OVER! ${result.winner} WINS! 🎉`);
                }, 1000); // Delay so they can see the combat result first
            }
            
            // Board will update automatically via websocket
        } else {
            alert('Attack failed: ' + result.error);
        }
    } catch (error) {
        console.error('Enhanced attack error:', error);
        alert('Attack failed: ' + error.message);
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
    enhancedAttack(attackerX, attackerY, defenderX, defenderY);
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
    console.log('Combat Result:');
    console.log(`- Attacker dealt ${combatResult.attacker_damage} damage`);
    console.log(`- Defender dealt ${combatResult.defender_damage} damage`);
    console.log(`- Counter attack: ${combatResult.counter_attack_occurred ? 'Yes' : 'No'}`);
    console.log(`- Attacker destroyed: ${combatResult.attacker_destroyed ? 'Yes' : 'No'}`);
    console.log(`- Defender destroyed: ${combatResult.defender_destroyed ? 'Yes' : 'No'}`);
    
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
            
            console.log(`Highlighted ${result.targets.length} attack targets for unit at (${unitX}, ${unitY})`);
        }
    }).catch(error => {
        console.error('Failed to get attack targets:', error);
    });
}

// Clear range highlights
function clearRangeHighlights() {
    // Since we're using Two.js canvas, we'll need to re-render
    // For now, just log that we're clearing highlights
    console.log('Clearing attack range highlights');
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
    
    console.log(`Highlighting tile (${x}, ${y}) as ${className}`);
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
        
        if (cargoInfo.cargo_list.length > 0) {
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

// function showTransportFeedback(message, type = 'info') {
//     // Remove existing feedback
//     const existingFeedback = document.getElementById('transport-feedback');
//     if (existingFeedback) {
//         existingFeedback.remove();
//     }
    
//     // Create new feedback element
//     const feedback = document.createElement('div');
//     feedback.id = 'transport-feedback';
//     feedback.style.cssText = `
//         position: fixed;
//         top: 20px;
//         right: 20px;
//         background: ${type === 'error' ? '#e74c3c' : '#2c3e50'};
//         color: white;
//         padding: 10px 15px;
//         border-radius: 5px;
//         z-index: 1000;
//         font-family: sans-serif;
//         box-shadow: 0 2px 10px rgba(0,0,0,0.2);
//         max-width: 300px;
//     `;
//     feedback.textContent = message;
    
//     document.body.appendChild(feedback);
    
//     // Auto-remove after 3 seconds
//     setTimeout(() => {
//         if (feedback && feedback.parentNode) {
//             feedback.remove();
//         }
//     }, 3000);
// }

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
        // TODO: Add UI for selecting which cargo unit to unload
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
            console.log(`Transport Status: ${result.count} transport units found`);
            result.transport_units.forEach(transport => {
                console.log(`${transport.unit_type} at (${transport.x}, ${transport.y}): ${transport.cargo_info.current_cargo}/${transport.cargo_info.max_capacity} cargo`);
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
    console.log("Transport system initialized");
    
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
    console.log("Clearing indicators");
}

function gameToken() {
    return token;
}

function handleLoadingClick(tile) {
    if (!transportHighlights || !transportHighlights.loadableUnits) {
        return false;
    }
    
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
        return true;
    }
    
    return false;
}

function handleUnloadingClick(tile) {
    if (!transportHighlights || !transportHighlights.unloadPositions) {
        return false;
    }
    
    const isUnloadable = transportHighlights.unloadPositions.some(pos => 
        pos.x === tile.x && pos.y === tile.y
    );
    
    if (isUnloadable && transportHighlights.selectedTransport) {
        attemptUnloadUnit(
            transportHighlights.selectedTransport.x,
            transportHighlights.selectedTransport.y,
            tile.x,
            tile.y,
            0
        );
        return true;
    }
    
    return false;
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
    console.log(`🚶 MOVEMENT: Highlighting movement range for unit at (${unitX}, ${unitY})`);
    
    // Get movement range data from backend
    jsonrpc('get_unit_valid_moves', {x: unitX, y: unitY})
        .then(result => {
            if (result && result.success && result.moves) {
                clearMovementHighlights();
                
                result.moves.forEach(move => {
                    highlightMovementTile(move.x, move.y, 'movement-range');
                });
                
                console.log(`✅ Highlighted ${result.moves.length} movement options`);
            } else {
                console.log('❌ No movement data received, trying fallback calculation');
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
    console.log('🔧 FALLBACK: Calculating movement range locally');
    
    // Don't clear if we already have highlights from a previous source
    if (window.movementHighlights && window.movementHighlights.length > 0) {
        console.log('✅ Highlights already exist, skipping fallback');
        return;
    }
    
    // Get the selected unit
    var selectedUnit = null;
    var selectedTile = board.grid.find(t => t.x === unitX && t.y === unitY);
    if (selectedTile && selectedTile.unit) {
        selectedUnit = selectedTile.unit;
    }
    
    if (!selectedUnit) {
        console.log('❌ No unit found for movement calculation');
        return;
    }
    
    // Basic movement range calculation (adjust based on your game rules)
    var movementRange = getUnitMovementRange(selectedUnit);
    console.log(`Unit ${selectedUnit.type} has movement range: ${movementRange}`);
    
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

function getUnitMovementRange(unit) {
    // Define movement ranges for different unit types
    // Adjust these values based on your game's rules
    var movementRanges = {
        'INFANTRY': 2,
        'MECH': 2,
        'RECON': 8,
        'TANK': 6,
        'MD_TANK': 5,
        'NEOTANK': 6,
        'APC': 6,
        'ARTILLERY': 5,
        'ROCKET': 5,
        'ANTI_AIR': 6,
        'MISSILE': 4,
        'FIGHTER': 9,
        'BOMBER': 7,
        'B_COPTER': 6,
        'T_COPTER': 6,
        'BATTLESHIP': 5,
        'CRUISER': 6,
        'LANDER': 6,
        'SUB': 5
    };
    
    return movementRanges[unit.type] || 3; // Default to 3 if unit type not found
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
    
    console.log(`🎯 Highlighting movement tile (${x}, ${y})`);
}

function clearMovementHighlights() {
    // Clear visual highlights in Two.js ONLY
    if (window.movementHighlightGroup && window.two) {
        window.two.remove(window.movementHighlightGroup);
        window.movementHighlightGroup = null;
    }
    
    console.log('🧹 Cleared movement highlight visuals');
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
        console.log(`✅ Rendered ${renderedCount} movement highlights successfully`);
    } catch (error) {
        console.error('Error updating Two.js:', error);
    }
}

function clearMovementHighlightsData() {
    // Clear the data array
    if (window.movementHighlights) {
        window.movementHighlights = [];
    }
    console.log('🧹 Cleared movement highlights data');
}

// =============================================================================
// ENHANCED UNIT SELECTION WITH MOVEMENT HIGHLIGHTING
// =============================================================================

function unitSelectWithMovementHighlighting(tile) {
    console.log('🎯 SELECTION: Enhanced unit selection with movement highlighting');
    
    try {
        // Step 1: Basic unit selection
        jsonrpc('unit_select', {x: tile.x, y: tile.y}).then(result => {
            if (result && !result.error) {
                // Set board selection
                board.selected = tile;
                console.log('✅ Unit selected successfully');
                
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
    var transportTypes = ['APC', 'LANDER', 'BLACKBOAT', 'T_COPTER'];
    return transportTypes.includes(unit.type);
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

console.log('✅ Movement highlighting system loaded successfully');