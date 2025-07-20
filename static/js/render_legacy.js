//
// Setup
//

// constants
if (!window.TILESIZE) {
    window.TILESIZE = 16;
}
// Use window.TILESIZE directly to avoid conflicts with other files

// Tileset management functions
function getSelectedTerrainTileset() {
    const select = document.getElementById('terrainTilesetSelect');
    // Default to AWDS tileset - known working
    if (!select) return '/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png';
    
    switch (select.value) {
        case 'aw2_rgb':
        case 'optimized':
            return '/static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png';
        case 'transparent':
            return '/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png';
        case 'normal':
            return '/static/img/Advance_Wars_Dual_Strike_Tileset_Normal.png';
        case 'blackhole_transparent':
            return '/static/img/aw2_blackhole_tileset_normal_transparent.png';
        case 'blackhole_normal':
            return '/static/img/aw2_blackhole_tileset_normal.png';
        default:
            return '/static/img/Game Boy Advance - Advance Wars 2 Black Hole Rising - Overworld Tileset Buildings.png';
    }
}

function getSelectedUnitTileset() {
    const select = document.getElementById('unitTilesetSelect');
    if (!select) return '/static/img/units_sprite_sheet_complete.png'; // Use complete optimized sheet as default
    
    switch (select.value) {
        case 'optimized':
        case 'complete':
            return '/static/img/units_sprite_sheet_complete.png';
        case 'blackhole_transparent':
            return '/static/img/aw2_blackhole_units_map_transparent.png';
        case 'blackhole_normal':
            return '/static/img/aw2_blackhole_units_map.png';
        default:
            return '/static/img/units_sprite_sheet_complete.png';
    }
}

// Load sprite map for optimized sprite sheet
let optimizedSpriteMap = null;
async function loadOptimizedSpriteMap() {
    if (optimizedSpriteMap) return optimizedSpriteMap;
    
    try {
        const response = await fetch('/static/img/units_sprite_map_complete.json');
        optimizedSpriteMap = await response.json();
        logger.debug('Loaded complete sprite map with', Object.keys(optimizedSpriteMap.sprites).length, 'sprites');
        return optimizedSpriteMap;
    } catch (error) {
        logger.error('Failed to load complete sprite map:', error);
        return null;
    }
}

// Load tileset map for AW2 RGB tileset
let aw2TilesetMap = null;
async function loadAW2TilesetMap() {
    if (aw2TilesetMap) return aw2TilesetMap;
    
    try {
        const response = await fetch('/static/img/aw2_tileset_labeled_mapping.json');
        aw2TilesetMap = await response.json();
        logger.debug('Loaded AW2 RGB tileset map with', Object.keys(aw2TilesetMap.tiles).length, 'tiles');
        return aw2TilesetMap;
    } catch (error) {
        logger.error('Failed to load AW2 tileset map:', error);
        return null;
    }
}

// Transport visual constants - use window to avoid conflicts
window.TRANSPORT_HIGHLIGHT_OPACITY = window.TRANSPORT_HIGHLIGHT_OPACITY || 0.3;
window.TRANSPORT_BORDER_WIDTH = window.TRANSPORT_BORDER_WIDTH || 2;

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
        attackHighlights: [],
        operationInProgress: false
    };
}

// Transport rendering globals
var transportHighlightGroup = null;

// Clear any stale highlights on page load
window.movementHighlights = [];
window.movementHighlightGroup = null;
window.attackHighlightGroup = null;
if (window.gameState) {
    window.gameState.attackHighlights = [];
}

// update board data
update();

// init controls
var buttonrerender = document.getElementsByClassName('buttonrerender');
buttonrerender.onclick = window.debounce(rerender, 300);
var inputshowmap = document.getElementById('inputshowmap');
inputshowmap.onchange = rerender;
var buttonendturn = document.getElementsByClassName('buttonendturn');
buttonendturn.onclick = window.debounce(armyEndTurn, 500);
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
        logger.info('socket connected');
        socket.emit('game', token);
    });
    socket.on('disconnect', () => {
        logger.info('socket disconnected');
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

// Update game status display elements
function updateGameStatus(gameData) {
    if (!gameData) return;
    
    // Update current turn
    const turnElement = document.getElementById('current-turn');
    if (turnElement && gameData.current_turn) {
        turnElement.textContent = gameData.current_turn;
        turnElement.style.color = gameData.current_turn === 'RED' ? '#e74c3c' : 
                                  gameData.current_turn === 'BLUE' ? '#3498db' : 
                                  gameData.current_turn === 'GREEN' ? '#27ae60' : 
                                  gameData.current_turn === 'YELLOW' ? '#f39c12' : '#95a5a6';
    }
    
    // Update day
    const dayElement = document.getElementById('current-day');
    if (dayElement && gameData.days !== undefined) {
        dayElement.textContent = gameData.days;
    }
    
    // Update RED funds
    const redFundsElement = document.getElementById('red-funds');
    if (redFundsElement && gameData.red_funds !== undefined) {
        redFundsElement.textContent = '$' + gameData.red_funds.toLocaleString();
    }
    
    // Update BLUE funds
    const blueFundsElement = document.getElementById('blue-funds');
    if (blueFundsElement && gameData.blue_funds !== undefined) {
        blueFundsElement.textContent = '$' + gameData.blue_funds.toLocaleString();
    }
    
    // Update any army funds if they exist
    if (gameData.army_funds) {
        for (const [army, funds] of Object.entries(gameData.army_funds)) {
            const element = document.getElementById(`${army.toLowerCase()}-funds`);
            if (element) {
                element.textContent = '$' + funds.toLocaleString();
            }
        }
    }
}

async function rerender() {
    console.time('rerender');
    if (two) {
        // Instead of clearing everything, just update what changed
        // This prevents the black flash
        await updateScene();
        two.update();
    } else {
        logger.error('Two.js not initialized - calling update()');
        update();
    }
    console.timeEnd('rerender');
}

//
// JSON-RPC methods
//

// Force a full scene refresh (useful after major changes)
function forceSceneRefresh() {
    window.sceneInitialized = false;
    window.sceneElements = {
        terrain: {},
        units: {},
        highlights: {}
    };
}

function jsonrpc(method, params, callback) {
    if (!params) params = {};
    params.token = token;
    logger.debug('rpc::', method, params);
    
    // If no callback provided, return a Promise (for async/await)
    if (!callback) {
        return new Promise((resolve, reject) => {
            var xhr = new XMLHttpRequest();
            xhr.onreadystatechange = function() {
                if (this.readyState === XMLHttpRequest.DONE) {
                    if (this.status === 200) {
                        try {
                            var response = JSON.parse(this.responseText);
                            logger.debug('RPC Response:', method, response);
                            if (response.error) {
                                logger.error('RPC Error:', method, response.error);
                                reject(new Error(response.error.message || 'RPC Error'));
                            } else {
                                resolve(response.result);
                            }
                        } catch (e) {
                            logger.error('JSON Parse Error:', this.responseText);
                            reject(new Error('Invalid JSON response'));
                        }
                    } else {
                        logger.error('RPC HTTP Error:', method, this.status, this.statusText);
                        logger.error('Response body:', this.responseText);
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
                logger.error('error calling "' + method + '"');
            }
        }
    };
    xhr.open('POST', '/api');
    xhr.setRequestHeader('Content-Type', 'application/json');
    var data = {'jsonrpc': '2.0', 'method': method, 'params': params, 'id': uuidv4()};
    xhr.send(JSON.stringify(data));
}

async function update() {
    // Use operation queue to prevent concurrent updates
    window.operationQueue.add(
        () => jsonrpc('game_board', {token: token}),
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
        // logger.debug('Game board response received:', res);
        // Preserve the current selection before updating board
        var previousSelection = board ? board.selected : null;
        var previousTurn = board ? board.current_turn : null;

        // Save movement highlights before updating board
        const savedMovementTiles = [];
        if (board && board.grid && window.movementHighlights) {
            board.grid.forEach(tile => {
                if (tile.can_be_moved_to) {
                    savedMovementTiles.push({x: tile.x, y: tile.y});
                }
            });
        }
        
        // Update board data
        board = res;
        window.board = res; // Also expose globally
        
        // Restore the previous selection if it still exists
        if (previousSelection && board.grid) {
            const selectedTile = board.grid.find(t => 
                t.x === previousSelection.x && t.y === previousSelection.y
            );
            if (selectedTile && selectedTile.unit && selectedTile.unit.army === board.current_turn) {
                board.selected = selectedTile;
                logger.debug('Restored selection:', selectedTile.x, selectedTile.y);
            } else {
                board.selected = null;
                logger.debug('Selection cleared - unit no longer valid');
            }
        }
        
        // Log board update for debugging
        logger.info('📋 Board updated:', {
            turn: res.current_turn,
            day: res.days,
            gridSize: res.grid?.length,
            units: res.grid?.filter(t => t.unit).length || 0
        });
        
        // Ensure rendering happens after board update
        if (two && two.scene) {
            logger.debug('Triggering render after board update');
            // Use the proper update function instead of non-existent clearScene/draw
            await updateScene();
            two.update();
        }
        
        // Restore movement highlights after update
        if (savedMovementTiles.length > 0 && board.grid) {
            savedMovementTiles.forEach(saved => {
                const tile = board.grid.find(t => t.x === saved.x && t.y === saved.y);
                if (tile) {
                    tile.can_be_moved_to = true;
                }
            });
            logger.debug(`Restored ${savedMovementTiles.length} movement highlight flags after update`);
        }
        
        // Initialize validators if not already done
        if (!window.gameValidators && board) {
            window.gameValidators = new GameValidators(board);
            logger.info('Game validators initialized');
        }
        
        // Restore selection if it existed
        if (previousSelection) {
            const restoredTile = board.grid.find(t => 
                t.x === previousSelection.x && t.y === previousSelection.y
            );
            if (restoredTile) {
                board.selected = restoredTile;
                logger.debug(`✅ Selection restored at (${restoredTile.x}, ${restoredTile.y})`);
            } else {
                logger.debug(`❌ Could not restore selection at (${previousSelection.x}, ${previousSelection.y})`);
            }
        }
        
        // If turn changed, clear all highlights
        if (previousTurn && previousTurn !== board.current_turn) {
            logger.debug(`🔄 Turn changed from ${previousTurn} to ${board.current_turn}`);
            clearAllHighlights();
        }
        
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
                    logger.error('Draw element not found');
                    return;
                }
                // Add extra height to accommodate double-height sprites at the top
                var extraHeight = window.TILESIZE; // One extra tile height for overlapping sprites
                var params = { 
                    type: Two.Types.canvas, 
                    width: board.width * window.TILESIZE, 
                    height: board.height * window.TILESIZE + extraHeight 
                };
                two = new Two(params).appendTo(elem);
                
                // Offset all rendering down by extraHeight to create top margin
                two.scene.translation.set(0, extraHeight);
                // Initialize transport visual system
                window.transportHighlights = [];
                transportHighlightGroup = null;
                logger.debug('RENDER: Transport visual system initialized');
                logger.debug('Two.js initialized successfully');
                
                // canvas mouse handling
                var draw = document.getElementById('draw');
                var canvas = draw.children[0];
                if (canvas) {
                    canvas.onmousemove = canvasMove;
                    canvas.onmouseleave = function() {
                        var infobox = document.getElementById('infobox');
                        if (infobox) {
                            infobox.dataset.hoverActive = 'false';
                            infobox.innerHTML = '<small style="color: #bdc3c7;">Hover over the map to see tile information</small>';
                        }
                    };
                    // Remove throttle - centralized handler will manage this
                    // Let centralized handler take over if it's loaded
                    if (!window.clickHandler) {
                        canvas.onclick = advanceWarsCanvasClick;
                        canvas.ondblclick = advanceWarsDoubleClick;
                    } else {
                        logger.info('Centralized click handler detected, deferring to it');
                        // Re-initialize the centralized handler to ensure it's attached
                        setTimeout(() => {
                            if (window.clickHandler && window.clickHandler.initialize) {
                                window.clickHandler.initialize();
                            }
                        }, 100);
                    }

                    // NEW: Prevent right-click context menu
                    canvas.addEventListener('contextmenu', function(event) {
                        logger.debug('🖱️ Right-click detected on canvas', event);
                        event.preventDefault();
                        event.stopPropagation();
                        
                        const tile = getTileFromCanvasClick(event);
                        logger.debug('🎯 Tile from right-click:', tile);
                        if (tile) {
                            handleTransportRightClick(tile, event);
                        } else {
                            logger.debug('❌ No tile found for right-click');
                        }
                        return false;
                    });

                    // ✅ NEW: Add this alt-click handler here
                    // Alt-click handling moved to main advanceWarsCanvasClick function to prevent conflicts
                    
                    // Add touch event support for mobile
                    addTouchSupport(canvas);
                }
            } catch (error) {
                logger.error('Error initializing Two.js:', error);
                return;
            }
        }
        // render - use differential rendering to prevent flashing
        if (!window.sceneInitialized) {
            // First time - create the full scene
            two.clear();
            await createScene();
            window.sceneInitialized = true;
        } else {
            // Subsequent updates - only update what changed
            await updateScene();
        }

        // Only render highlights if we have a selected unit that can act
        if (board.selected && board.selected.unit) {
            const unit = board.selected.unit;
            const canAct = unit.can_move || unit.can_attack;
            
            if (canAct) {
                // Render movement highlights
                if (window.movementHighlights && window.movementHighlights.length > 0) {
                    renderMovementHighlights();
                }
                // Render attack highlights
                if (window.gameState && window.gameState.attackHighlights && window.gameState.attackHighlights.length > 0) {
                    renderAttackHighlights();
                }
            } else {
                // Unit can't act - clear all highlights
                logger.debug('🚫 Selected unit cannot act - clearing highlights');
                clearAllHighlights();
            }
        }
        
        // Always render transport highlights if present
        if (window.transportHighlights && window.transportState && window.transportState.length > 0) {
            renderTransportHighlights();
        }

        two.update();
        // update info
        logger.debug('Updating game info...');
        var gamebox = document.getElementById('gamebox');
        logger.debug('Gamebox element found:', gamebox);
        
        // Update game statistics in the gamebox (not infobox)
        if (gamebox) {
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
            
            gamebox.innerText = gameStats;
            logger.info('Gamebox updated with:', gameStats);
        } else {
            logger.error('Gamebox element not found!');
        }
        
        // Keep infobox for tile information (updated on hover)
        var infobox = document.getElementById('infobox');
        if (infobox && !infobox.dataset.hoverActive) {
            infobox.innerHTML = '<small style="color: #bdc3c7;">Hover over the map to see tile information</small>';
        }

        // Gamebox already updated above with full statistics
        
        // update code (JSON display)
        var code = document.getElementById('code');
        if (code) {
            try {
                // Create a simplified board object without circular references
                var simplifiedBoard = {
                    width: board.width,
                    height: board.height,
                    current_turn: board.current_turn,
                    current_day: board.current_day,
                    game_active: board.game_active,
                    armies: board.armies,
                    // Don't include grid as it may have circular references
                };
                code.value = JSON.stringify(simplifiedBoard, null, 2);
            } catch (e) {
                code.value = "Error serializing board: " + e.message;
            }
        }
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
    logger.debug('🔄 Ending turn...');
    
    // Use operation queue with high priority
    window.operationQueue.add(async () => {
        // Clear ALL highlights before ending turn
        clearAllHighlights();
        
        // Clean up transport state
        cleanupTransportState();
        
        // Clear any selected units
        board.selected = null;
        if (window.gameState) {
            window.gameState.selectedUnit = null;
            window.gameState.selectedX = undefined;
            window.gameState.selectedY = undefined;
            window.gameState.movementPhase = false;
            window.gameState.showingAttackTargets = false;
        }
        
        // Call the original RPC method
        return await jsonrpc('army_end_turn', {token: token});
    }, {
        id: 'end-turn',
        description: 'Ending turn',
        priority: 10,
        showLoading: true
    }).then(result => {
        if (!result.skipped) {
            logger.info('✅ Turn ended');
            // Force update after turn ends
            update();
        }
    }).catch(error => {
        logger.error('❌ Failed to end turn:', error);
    });
}

function cleanupTransportState() {
    
    // Clear transport highlights if function exists
    if (typeof clearTransportHighlights === 'function') {
        clearTransportHighlights();
    }
    
    // Reset transport state
    if (window.transportState) {
        window.transportState.loadableUnits = [];
        window.transportState.unloadPositions = [];
        window.transportState.selectedTransport = null;
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
    modal.style.display = 'block';  // Show the modal
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
        
        // Use operation queue to prevent double-creation
        window.operationQueue.add(
            () => jsonrpc('unit_create', {token: token, army: army, unit_type: unitType, x: tile.x, y: tile.y}),
            {
                id: `create-${tile.x}-${tile.y}-${unitType}`,
                description: `Creating ${unitType}`,
                priority: 7
            }
        ).then(result => {
            if (!result.skipped) {
                // Close the modal
                modal.style.display = 'none';
                
                // Refresh the game display after creating unit
                logger.info('🔄 Updating board after unit creation');
                update();
            }
        });
    };
}

function airunitCreate(tile) {
    var modal = document.getElementById('modalcreate');
    modal.style.display = 'block';  // Show the modal
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
        var unitType = select.options[select.selectedIndex].value;;
        var army = tile.mapTile.army;
        
        // Use operation queue to prevent double-creation
        window.operationQueue.add(
            () => jsonrpc('unit_create', {token: token, army: army, unit_type: unitType, x: tile.x, y: tile.y}),
            {
                id: `create-${tile.x}-${tile.y}-${unitType}`,
                description: `Creating ${unitType}`,
                priority: 7
            }
        ).then(result => {
            if (!result.skipped) {
                // Close the modal
                modal.style.display = 'none';
                
                // Refresh the game display after creating unit
                logger.info('🔄 Updating board after air unit creation');
                update();
            }
        });
    };
}

function seaunitCreate(tile) {
    var modal = document.getElementById('modalcreate');
    modal.style.display = 'block';  // Show the modal
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
        var unitType = select.options[select.selectedIndex].value;;
        var army = tile.mapTile.army;
        
        // Use operation queue to prevent double-creation
        window.operationQueue.add(
            () => jsonrpc('unit_create', {token: token, army: army, unit_type: unitType, x: tile.x, y: tile.y}),
            {
                id: `create-${tile.x}-${tile.y}-${unitType}`,
                description: `Creating ${unitType}`,
                priority: 7
            }
        ).then(result => {
            if (!result.skipped) {
                // Close the modal
                modal.style.display = 'none';
                
                // Refresh the game display after creating unit
                logger.info('🔄 Updating board after sea unit creation');
                update();
            }
        });
    };
    modal.style.display = 'block';
}

function unitSelect(tile) {
    jsonrpc('unit_select', {x: tile.x, y: tile.y});
    // Update gameState for context menu
    if (tile.unit) {
        window.gameState.selectedUnit = tile.unit;
        window.gameState.selectedUnit.x = tile.x;
        window.gameState.selectedUnit.y = tile.y;
    }
}

function unitCapture(tile) {
    jsonrpc('capture_tile', {x: tile.x, y: tile.y}).then(result => {
        // Manually update unit flags after capture
        if (board && board.grid) {
            const unitTile = board.grid.find(t => t.x === tile.x && t.y === tile.y);
            if (unitTile && unitTile.unit) {
                logger.info('📝 Unit captured - marking as unavailable');
                unitTile.unit.can_move = false;
                unitTile.unit.can_attack = false;
                unitTile.unit.can_capture = false;
            }
        }
        // Force update to refresh sprite
        update();
    });
}

function unitWait(tile) {
    jsonrpc('unit_wait', {x: tile.x, y: tile.y}).then(result => {
        // Manually update unit flags after wait
        if (board && board.grid) {
            const unitTile = board.grid.find(t => t.x === tile.x && t.y === tile.y);
            if (unitTile && unitTile.unit) {
                logger.debug('📝 Unit waited - marking as unavailable');
                unitTile.unit.can_move = false;
                unitTile.unit.can_attack = false;
                unitTile.unit.can_capture = false;
            }
        }
        // Force update to refresh sprite
        update();
    });
}

function unitAttack(tile) {
    const source = board.selected;
    if (!source) {
        logger.error('No unit selected for attack');
        return;
    }
    
    // Use operation queue to prevent double-attacks
    window.operationQueue.add(
        () => jsonrpc('unit_attack', {x: source.x, y: source.y, x2: tile.x, y2: tile.y}),
        {
            id: `attack-${source.x}-${source.y}-${tile.x}-${tile.y}`,
            description: 'Attacking',
            priority: 9
        }
    ).then(result => {
        if (!result.skipped) {
            // Refresh the game display after attack
            update();
        }
    });
}

function unitLoad(tile) {
    // Use proper RPC method for loading cargo
    const source = board.selected || {x: window.gameState?.selectedX, y: window.gameState?.selectedY};
    if (!source || source.x === undefined) {
        logger.error('No unit selected for loading');
        return;
    }
    
    jsonrpc('cargo_board_transport', {cargo_x: source.x, cargo_y: source.y, transport_x: tile.x, transport_y: tile.y}, function(result) {
        if (result.error) {
            logger.error('Failed to load unit:', result.error);
        } else {
            // Refresh the game display after load
            update();
        }
    });
}

function unitUnload(tile) {
    // Use proper RPC method for unloading cargo
    const source = board.selected || {x: window.gameState?.selectedX, y: window.gameState?.selectedY};
    if (!source || source.x === undefined) {
        logger.error('No transport selected for unloading');
        return;
    }
    
    // First, get cargo info to see what units are in the transport
    jsonrpc('get_cargo_info', {x: source.x, y: source.y}, function(cargoResult) {
        if (!cargoResult || cargoResult.error) {
            logger.error('Failed to get cargo info:', cargoResult?.error);
            return;
        }
        
        const cargoUnits = cargoResult.cargo || [];
        if (cargoUnits.length === 0) {
            logger.warn('Transport has no cargo to unload');
            return;
        }
        
        // If only one unit, unload it directly
        if (cargoUnits.length === 1) {
            performUnload(source.x, source.y, tile.x, tile.y, 0);
        } else {
            // Show cargo selection UI for multiple units
            window.cargoSelection.show(cargoUnits, function(selectedIndex) {
                performUnload(source.x, source.y, tile.x, tile.y, selectedIndex);
            });
        }
    });
    
    // Helper function to perform the actual unload
    function performUnload(transportX, transportY, exitX, exitY, cargoIndex) {
        jsonrpc('cargo_exit_transport', {
            transport_x: transportX, 
            transport_y: transportY, 
            exit_x: exitX, 
            exit_y: exitY, 
            cargo_index: cargoIndex
        }, function(result) {
            if (result.error) {
                logger.error('Failed to unload unit:', result.error);
            } else {
                logger.info('Successfully unloaded unit at index', cargoIndex);
                // Refresh the game display after unload
                update();
            }
        });
    }
}

function unitJoin(tile) {
    jsonrpc('unit_join', {x: board.selected.x, y: board.selected.y, x2: tile.x, y2: tile.y}, function(result) {
        // Refresh the game display after join
        update();
    });
}

function unitMove(tile) {
    // Try to get source from board.selected first, then fall back to gameState
    var source = board.selected;
    if (!source && window.gameState && window.gameState.selectedX !== undefined) {
        // Reconstruct source from gameState
        source = {
            x: window.gameState.selectedX,
            y: window.gameState.selectedY
        };
        logger.debug(`📍 Using gameState selection at (${source.x},${source.y})`);
    }
    
    if (!source) {
        logger.error('❌ No unit selected for movement');
        return;
    }
    
    var target = tile;
    logger.info(`🚶 Attempting move from (${source.x},${source.y}) to (${target.x},${target.y})`);
    
    // Use operation queue to prevent double-moves
    window.operationQueue.add(
        () => jsonrpc('unit_move', {x: source.x, y: source.y, x2: target.x, y2: target.y}),
        {
            id: `move-${source.x}-${source.y}-${target.x}-${target.y}`,
            description: 'Moving unit',
            priority: 8
        }
    ).then(result => {
        if (result.skipped) {
            logger.debug('Move skipped:', result.reason);
            return;
        }
            logger.info('✅ Move successful:', result);
            
            // Clear the selection and highlights after successful move
            board.selected = null;
            if (window.gameState) {
                window.gameState.selectedUnit = null;
                window.gameState.selectedX = undefined;
                window.gameState.selectedY = undefined;
            }
            
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
            
            // Trigger board update
            update();
            
        })
        .catch(error => {
            logger.error('❌ Move failed:', error);
            alert(`Move failed: ${error.message || error}`);
            // Don't clear highlights if move failed
        });
}

//
// Unit context menu handling
//
function handleUnitRightClick(tile, event) {
    logger.debug('Right-click on tile:', tile);
    
    // Check if we have a selected unit and clicked on an adjacent unit
    if (window.gameState && window.gameState.selectedUnit && tile.unit) {
        const selectedUnit = window.gameState.selectedUnit;
        
        // Check if the selected unit is a Black Boat
        const isBlackBoat = selectedUnit.type === 'BLACKBOAT' || selectedUnit.type === 'BLACK_BOAT';
        
        // Check if clicked unit is adjacent to selected unit
        const distance = Math.abs(selectedUnit.x - tile.x) + Math.abs(selectedUnit.y - tile.y);
        const isAdjacent = distance === 1;
        
        // Check if both units are on the same team
        const sameTeam = selectedUnit.army === tile.unit.army;
        
        if (isBlackBoat && isAdjacent && sameTeam && tile.unit.hp < 100) {
            // Show context menu for repair
            if (typeof showUnitContextMenu === 'function') {
                showUnitContextMenu(event.pageX, event.pageY, selectedUnit, tile.unit);
            }
            return true;
        }
    }
    
    return false;
}

// Alias for legacy code
function handleTransportRightClick(tile, event) {
    return handleUnitRightClick(tile, event);
}

//
// two.js rendering methods
//

function tileAt(px, py) {
    // Account for scene translation offset (dynamic, not fixed)
    var sceneOffsetY = window.two?.scene?.translation?.y || window.TILESIZE;
    var adjustedY = py - sceneOffsetY;
    var tileX = Math.floor(px / window.TILESIZE);
    var tileY = Math.floor(adjustedY / window.TILESIZE);
    
    // Debug logging for coordinate issues
    if (window.logger && window.logger.debug) {
        window.logger.debug(`tileAt(${px}, ${py}) -> scene offset: ${sceneOffsetY}, adjusted: (${px}, ${adjustedY}) -> tile: (${tileX}, ${tileY})`);
    }
    
    // Bounds checking
    if (tileY < 0 || tileY >= board.height || tileX < 0 || tileX >= board.width) {
        return null;
    }
    
    var tile = board.grid[tileX + tileY * board.width];
    return tile;
}

function canvasMove(ev) {
    var x = ev.offsetX;
    var y = ev.offsetY;
    var tile = tileAt(x, y);
    
    // Update cursor
    draw.style.cursor = 'default';
    if (tile) {
        if (tile.can_be_moved_to)
            draw.style.cursor = 'pointer';
        else if (tile.can_be_attacked)
            draw.style.cursor = 'crosshair';
        else if (tile.unit != null && tile.unit.army == board.current_turn)
            draw.style.cursor = 'pointer';
        else if (tile.mapTile && tile.mapTile.army == board.current_turn)
            if (tile.mapTile.type == 'FACTORY' ||
                tile.mapTile.type == 'AIRPORT' ||
                tile.mapTile.type == 'PORT')
                draw.style.cursor = 'pointer';
    }
    
    // Update info panel with tile details on hover
    var infobox = document.getElementById('infobox');
    if (tile && infobox) {
        // Mark that we're hovering
        infobox.dataset.hoverActive = 'true';
        
        var info = `Tile (${tile.x}, ${tile.y})`;
        info += `\nTerrain: ${tile.mapTile.type}`;
        
        if (tile.mapTile.army) {
            info += ` (${tile.mapTile.army})`;
        }
        
        if (tile.unit) {
            info += `\n\nUnit: ${tile.unit.army} ${tile.unit.type}`;
            info += `\nHP: ${Math.ceil(tile.unit.status.hp / 10)}/10`;
            info += `\nFuel: ${tile.unit.status.fuel}`;
            if (tile.unit.status.ammo !== undefined) {
                info += `\nAmmo: ${tile.unit.status.ammo}`;
            }
        }
        
        infobox.innerText = info;
    }
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
        if ((board.selected || window.gameState?.selectedX !== undefined) && window.movementHighlights) {
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
        logger.error('SELECTION_FIX: Unit selection failed:', error);
        jsonrpc('unit_select', {x: tile.x, y: tile.y});
    }
}

function executeMovement(targetTile) {
    
    if (!board.selected || !board.selected.unit) {
        logger.error('❌ No unit selected for movement');
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
        // IMPORTANT: Set selectedUnit for transport units (needed for Black Boat repair)
        logger.debug('🚛 Transport unit clicked, setting selectedUnit:', tile);
        window.gameState.selectedUnit = tile;
        board.selected = tile;
        
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
    
    var baseRect = two.makeRectangle(tile.x * window.TILESIZE + window.TILESIZE/2, tile.y * window.TILESIZE + window.TILESIZE/2, SPRITESIZE, SPRITESIZE);
    baseRect.fill = baseTexture;
    baseRect.stroke = 'transparent';
}

function makeMapTile(tile) {
    var showMapTiles = document.getElementById('inputshowmap').checked;
    if (showMapTiles) {
        // Try to use optimized tile renderer first - DISABLED due to palette conversion issues
        if (false && window.optimizedTileRenderer && window.optimizedTileRenderer.loaded) {
            try {
                // Check if needs base layer
                if (window.optimizedTileRenderer.needsBaseLayer(tile.mapTile.type)) {
                    window.optimizedTileRenderer.renderBaseTile(two, tile, window.TILESIZE);
                }
                
                // Render the tile
                const tileElement = window.optimizedTileRenderer.renderTile(two, tile, window.TILESIZE);
                if (tileElement) {
                    return; // Successfully rendered with optimized renderer
                }
            } catch (error) {
                console.warn('Optimized tile render failed, falling back to legacy:', error);
            }
        }
        
        // Legacy rendering fallback
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
            // Double-height tiles (like missile silos) should overlap the top border
            rect = two.makeRectangle(tile.x * window.TILESIZE + window.TILESIZE/2, tile.y * window.TILESIZE, SPRITESIZE, SPRITESIZE * 2);
        } else {
            rect = two.makeRectangle(tile.x * window.TILESIZE + window.TILESIZE/2, tile.y * window.TILESIZE + window.TILESIZE/2, SPRITESIZE, SPRITESIZE);
        }
        rect.fill = spriteTexture;
        rect.stroke = 'transparent';
    }
    // tile overlay
    rect = two.makeRectangle(tile.x * window.TILESIZE + window.TILESIZE/2, tile.y * window.TILESIZE + window.TILESIZE/2, window.TILESIZE, window.TILESIZE);
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
    // Try to load optimized sprite renderer first
    if (window.optimizedSpriteRenderer && !window.optimizedSpriteRenderer.loaded) {
        try {
            await window.optimizedSpriteRenderer.initialize();
            logger.info('✅ Using optimized sprite sheet (93KB vs 370KB)');
        } catch (error) {
            logger.warn('Failed to load optimized sprites, falling back to legacy:', error);
        }
    }
    
    // Try to load optimized tile renderer - DISABLED due to palette conversion issues
    if (false && window.optimizedTileRenderer && !window.optimizedTileRenderer.loaded) {
        try {
            await window.optimizedTileRenderer.initialize();
            logger.info('✅ Using optimized tileset (6KB vs 76KB, 92% smaller)');
        } catch (error) {
            logger.warn('Failed to load optimized tiles, falling back to legacy:', error);
        }
    }
    
    // Fall back to legacy sprite corrections
    if (window.spriteCorrections) {
        return; // Already loaded
    }
    
    try {
        // Use the latest sprite corrections from templates directory
        const response = await fetch('/templates/sprite_corrections_config.json');
        const data = await response.json();
        
        window.spriteCorrections = data.corrections;
        window.spriteConfig = data.spriteConfig;
        
        logger.debug('Legacy sprite corrector data loaded');
        logger.debug('SpriteConfig:', window.spriteConfig);
        logger.debug('Total correction categories:', Object.keys(data.corrections).length);
        logger.debug('Sample blue unit coords:', data.corrections.idle?.INFANTRY_BLUE_idle_0);
    } catch (error) {
        logger.error('Failed to load sprite corrector data:', error);
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
    
    return new Promise(async (resolve, reject) => {
        spriteSheetImg.onload = async function() {
            // Use sprite corrector data to get accurate coordinates
            let spriteKey, x, y;
            
            // Determine sprite state - show as active/idle if unit can move OR attack
            // Note: can_capture alone doesn't make a unit available (it needs to be able to move to capture)
            const canAct = tile.unit.can_move || tile.unit.can_attack;
            const state = canAct ? 'idle' : 'unavailable';
            
            // Build sprite key using sprite corrector format
            spriteKey = `${tile.unit.type}_${tile.unit.army}_${state}_0`;
            
            // Debug logging for sprite state
            if (tile.unit.army === board.current_turn) {
                logger.info(`Unit ${tile.unit.type} at (${tile.x},${tile.y}): can_move=${tile.unit.can_move}, can_attack=${tile.unit.can_attack}, can_capture=${tile.unit.can_capture} -> state=${state}`);
                
                // Extra debug for invisible units
                if (state === 'unavailable' && tile.unit.type === 'INFANTRY') {
                    logger.debug(`DEBUG: Unavailable Infantry sprite key: ${spriteKey}`);
                }
            }
            
            // Check if using optimized sprite sheet
            const isOptimized = unitsSrc.includes('units_sprite_sheet_complete.png');
            
            if (isOptimized) {
                // Load and use optimized sprite map
                const spriteMap = await loadOptimizedSpriteMap();
                if (spriteMap && spriteMap.sprites[spriteKey]) {
                    const spriteData = spriteMap.sprites[spriteKey];
                    x = spriteData.x;
                    y = spriteData.y;
                } else {
                    logger.warn(`Sprite not found in optimized map: ${spriteKey}`);
                    // Default to center of sprite sheet
                    x = 0;
                    y = 0;
                }
            } else if (window.spriteCorrections && window.spriteCorrections[state] && window.spriteCorrections[state][spriteKey]) {
                // Use original sprite corrector data
                const coords = window.spriteCorrections[state][spriteKey];
                x = coords.x;
                y = coords.y;
                
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
                    
                    // logger.debug(`Using enhanced fallback for ${spriteKey} based on ${redSpriteKey}: x=${x}, y=${y}`);
                } else {
                    // Final fallback to original coordinate calculation
                    logger.warn(`Sprite corrector data not found for ${spriteKey}, using basic fallback coordinates`);
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
            
            // Debug for invisible units
            if (state === 'unavailable' && tile.unit.type === 'INFANTRY') {
                logger.debug(`Drawing unavailable Infantry from sprite sheet at (${x}, ${y}), size ${SPRITESIZE}x${SPRITESIZE}`);
            }
            
            // Draw the unit sprite onto canvas
            ctx.drawImage(
                spriteSheetImg,
                x, y, SPRITESIZE, SPRITESIZE,  // Source rect
                0, 0, SPRITESIZE, SPRITESIZE   // Dest rect
            );
            
            
            // Draw HP indicator if unit is damaged
            if (tile.unit.status.hp <= 90) {
                var hpDigit = Math.ceil(tile.unit.status.hp / 10);
                if (hpDigit > 9) hpDigit = 9;
                if (hpDigit < 1) hpDigit = 1;
                
                // Calculate HP sprite position using sprite corrector data
                var hpX, hpY;
                const hpCategory = (tile.unit.can_move || tile.unit.can_attack) ? 'hp_indicators' : 'hp_unavailable';
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
            logger.error('Failed to load sprite sheet:', unitsSrc, error);
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
        var rect = two.makeRectangle(tile.x * window.TILESIZE + window.TILESIZE/2, tile.y * window.TILESIZE + window.TILESIZE/2, SPRITESIZE, SPRITESIZE);
        rect.fill = spriteTexture;
        rect.stroke = 'transparent';
        
        // CRITICAL: Add the sprite to the scene!
        two.add(rect);
        
        // Store sprite reference on tile for legacy compatibility
        tile.sprite = rect;
        
        // Force re-render to show the new texture
        two.update();
        
        return rect;
    } catch (error) {
        logger.error('Error generating unit texture:', error);
        // Fallback to old sprite creation method
        return makeSpriteLegacy(tile);
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
    var rect = two.makeRectangle(tile.x * window.TILESIZE + window.TILESIZE/2, tile.y * window.TILESIZE + window.TILESIZE/2, SPRITESIZE, SPRITESIZE);
    rect.fill = spriteTexture;
    rect.stroke = 'transparent';
    var health = null;
    var fuel = null;
    var ammo = null;
    var flag = null;
    var load = null;
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
        health = two.makeRectangle(tile.x * window.TILESIZE + window.TILESIZE - HEALTHSIZE/2, tile.y * window.TILESIZE + window.TILESIZE - HEALTHSIZE/2, HEALTHSIZE, HEALTHSIZE);
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
        health = two.makeRectangle(tile.x * window.TILESIZE + window.TILESIZE - HEALTHSIZE/2, tile.y * window.TILESIZE + window.TILESIZE - HEALTHSIZE/2, HEALTHSIZE, HEALTHSIZE);
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
        fuel = two.makeRectangle(tile.x * window.TILESIZE + window.TILESIZE - FUELSIZE/2 - 8, tile.y * window.TILESIZE + window.TILESIZE - FUELSIZE/2 - 8, FUELSIZE, FUELSIZE);
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
        ammo = two.makeRectangle(tile.x * window.TILESIZE + window.TILESIZE - AMMOSIZE/2, tile.y * window.TILESIZE + window.TILESIZE - AMMOSIZE/2 - 8, AMMOSIZE -2, AMMOSIZE -2);
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
        flag = two.makeRectangle(tile.x * window.TILESIZE + window.TILESIZE - FLAGSIZE/2 - 8, tile.y * window.TILESIZE + window.TILESIZE - FLAGSIZE/2, FLAGSIZE, FLAGSIZE);
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
            load = two.makeRectangle(tile.x * window.TILESIZE + window.TILESIZE - LOADSIZE/2 - 8, tile.y * window.TILESIZE + window.TILESIZE - LOADSIZE/2, LOADSIZE, LOADSIZE);
            load.fill = loadTexture;
            load.stroke = 'transparent';
        }
    }
    
    // CRITICAL: Add all sprites to the scene!
    two.add(rect);
    if (health) two.add(health);
    if (fuel) two.add(fuel);
    if (ammo) two.add(ammo);
    if (flag) two.add(flag);
    if (load) two.add(load);
    
    // Store sprite reference on tile for legacy compatibility
    tile.sprite = rect;
    
    // Force re-render
    two.update();
    
    return rect;
}

function renderTransportIndicators() {
    logger.debug('RENDER: Adding transport indicators');
    
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
    
    if (!window.transportHighlights || !window.transportState || window.transportState.length === 0) {
        return; // No highlights to show
    }
    
    // Create new highlight group
    transportHighlightGroup = two.makeGroup();
    
    window.transportHighlights.forEach(highlight => {
        const x = (highlight.x * window.TILESIZE) + (window.TILESIZE / 2);
        const y = (highlight.y * window.TILESIZE) + (window.TILESIZE / 2);
        
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
        const highlightRect = two.makeRectangle(x, y, window.TILESIZE - 4, window.TILESIZE - 4);
        highlightRect.fill = color;
        highlightRect.stroke = strokeColor;
        highlightRect.linewidth = window.TRANSPORT_BORDER_WIDTH;
        
        // Add to highlight group
        transportHighlightGroup.add(highlightRect);
    });
    
    // Add the group to the scene
    two.add(transportHighlightGroup);
}

// Custom cargo indicator functions removed - using authentic AW load icon from tileset instead

// Global variables to track scene elements
window.sceneElements = window.sceneElements || {
    terrain: {},
    units: {},
    highlights: {}
};

// Update only changed elements instead of recreating everything
async function updateScene() {
    if (!board || !board.grid) return;
    
    // Ensure sprite corrections are loaded before rendering
    await loadSpriteCorrector();
    
    // Track which units we've seen this update
    const currentUnits = new Set();
    
    // Update tiles
    for (var i = 0; i < board.height; i++) {
        for (var j = 0; j < board.width; j++) {
            var tile = board.grid[j + i * board.width];
            var key = `${j},${i}`;
            
            // Update terrain only if changed (rarely happens)
            if (!window.sceneElements.terrain[key]) {
                makeMapTile(tile);
                window.sceneElements.terrain[key] = true;
            }
            
            // Update units
            if (tile.unit !== null) {
                currentUnits.add(key);
                
                // Check if unit exists and needs update
                if (!window.sceneElements.units[key] || 
                    window.sceneElements.units[key].hp !== tile.unit.hp ||
                    window.sceneElements.units[key].type !== tile.unit.type) {
                    
                    // Remove old unit sprite if exists
                    if (window.sceneElements.units[key] && window.sceneElements.units[key].sprite) {
                        two.remove(window.sceneElements.units[key].sprite);
                    }
                    
                    // Create new unit sprite
                    const sprite = await makeSprite(tile);
                    window.sceneElements.units[key] = {
                        type: tile.unit.type,
                        hp: tile.unit.hp,
                        sprite: sprite
                    };
                }
            }
        }
    }
    
    // Remove units that no longer exist
    for (const key in window.sceneElements.units) {
        if (!currentUnits.has(key)) {
            if (window.sceneElements.units[key].sprite) {
                two.remove(window.sceneElements.units[key].sprite);
            }
            delete window.sceneElements.units[key];
        }
    }
    
    // Update transport indicators
    renderTransportIndicators();
}

async function createScene() {
    // Clear tracking objects
    window.sceneElements.terrain = {};
    window.sceneElements.units = {};
    
    // create game tiles
    for (var i = 0; i < board.height; i++) {
        for (var j = 0; j < board.width; j++) {
            var tile = board.grid[j + i * board.width];
            var key = `${j},${i}`;
            
            // create map tile
            makeMapTile(tile);
            window.sceneElements.terrain[key] = true;
            
            // create sprite with proper await for canvas texture generation
            if (tile.unit !== null) {
                const sprite = await makeSprite(tile);
                window.sceneElements.units[key] = {
                    type: tile.unit.type,
                    hp: tile.unit.hp,
                    sprite: sprite
                };
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
        logger.error('Combat preview error:', error);
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
        logger.error('Enhanced attack error:', error);
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
        logger.error('❌ Enhanced attack failed:', error);
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
        logger.error('❌ No unit selected for attack');
        return;
    }
    
    var attacker = board.selected;
    
    jsonrpc('unit_attack', {
        x: attacker.x,
        y: attacker.y,
        x2: targetTile.x,
        y2: targetTile.y
    }, function(result) {
        logger.info('⚔️ Attack executed:', result);
        
        // Clear all state
        clearAllHighlights();
        board.selected = null;
        if (window.gameState) {
            window.gameState.selectedUnit = null;
            window.gameState.selectedX = undefined;
            window.gameState.selectedY = undefined;
            window.gameState.movementPhase = false;
            window.gameState.showingAttackTargets = false;
        }
        
        // Manually update unit flags since server doesn't do it properly
        if (board && board.grid) {
            const attackerTile = board.grid.find(t => t.x === attacker.x && t.y === attacker.y);
            if (attackerTile && attackerTile.unit) {
                logger.info('📝 Manually updating attacker flags to unavailable');
                attackerTile.unit.can_move = false;
                attackerTile.unit.can_attack = false;
                // Note: can_capture is not updated as it doesn't affect sprite state
            }
        }
        
        if (result && result.game_over) {
            alert(`Game Over! ${result.winner} wins!`);
        }
        
        // Force immediate update
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
        logger.error('Failed to get attack targets:', error);
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

// Initialize unified transport state
if (!window.transportState) {
    window.transportState = {
        loadableUnits: [],
        unloadPositions: [],
        selectedTransport: null
    };
}

// =============================================================================
// TRANSPORT HIGHLIGHT MANAGEMENT
// =============================================================================

function clearTransportHighlights() {
    // Remove all transport-related CSS classes
    const tiles = document.querySelectorAll('.tile');
    tiles.forEach(tile => {
        tile.classList.remove('loadable-unit', 'unload-position');
    });
    
    window.transportState.loadableUnits = [];
    window.transportState.unloadPositions = [];
    window.transportState.selectedTransport = null;
}

function showLoadableUnitsHighlight(transportX, transportY) {
    clearTransportHighlights();
    
    // Fix: Use jsonrpc instead of rpcCall and correct parameter format
    jsonrpc('get_loadable_units', {x: transportX, y: transportY}, function(result) {
        if (result.success && result.loadable_units) {
            window.transportState.loadableUnits = result.loadable_units;
            window.transportState.selectedTransport = {x: transportX, y: transportY};
            
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
            window.transportState.unloadPositions = result.valid_positions;
            window.transportState.selectedTransport = {x: transportX, y: transportY};
            
            showTransportFeedback(`${result.valid_positions.length} positions available. Alt+Click to unload.`);
        } else {
            showTransportFeedback("No valid unload positions.");
        }
    });
}

function attemptLoadUnit(transportX, transportY, cargoX, cargoY) {
    jsonrpc('cargo_board_transport', {
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
    jsonrpc('cargo_exit_transport', {
        transport_x: transportX, 
        transport_y: transportY, 
        exit_x: unloadX, 
        exit_y: unloadY, 
        cargo_index: cargoIndex
    }, function(result) {
        if (result.success) {
            showTransportFeedback(result.message);
            clearTransportHighlights();
            update(); // Refresh the board
        } else {
            showTransportFeedback(`Unload failed: ${result.error || result.message}`);
        }
    }).catch(function(error) {
        logger.error('Unload error:', error);
        showTransportFeedback(`Unload failed: ${error.message || 'Unknown error'}`);
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
        logger.error('TRANSPORT_FIX: Transport operation failed:', error);
        showTransportFeedback('Transport operation failed: ' + error.message, 'error');
        return false;
    }
}
function handleLoadingClick(tile) {
    // Check if this tile has a loadable unit highlighted
    const isLoadable = window.transportState.loadableUnits.some(unit => 
        unit.x === tile.x && unit.y === tile.y
    );
    
    if (isLoadable && window.transportState.selectedTransport) {
        attemptLoadUnit(
            window.transportState.selectedTransport.x,
            window.transportState.selectedTransport.y,
            tile.x,
            tile.y
        );
        return true; // Transport operation handled
    }
    
    return false;
}

function handleUnloadingClick(tile) {
    // Check if this tile is a valid unload position
    const isUnloadable = window.transportState.unloadPositions.some(pos => 
        pos.x === tile.x && pos.y === tile.y
    );
    
    if (isUnloadable && window.transportState.selectedTransport) {
        const transport = window.transportState.selectedTransport;
        
        // Get cargo info first
        jsonrpc('get_cargo_info', {x: transport.x, y: transport.y}, function(cargoResult) {
            if (!cargoResult || cargoResult.error) {
                logger.error('Failed to get cargo info:', cargoResult?.error);
                return;
            }
            
            const cargoUnits = cargoResult.cargo || [];
            if (cargoUnits.length === 0) {
                logger.warn('Transport has no cargo to unload');
                return;
            }
            
            // If only one unit, unload it directly
            if (cargoUnits.length === 1) {
                attemptUnloadUnit(transport.x, transport.y, tile.x, tile.y, 0);
            } else {
                // Show cargo selection UI for multiple units
                window.cargoSelection.show(cargoUnits, function(selectedIndex) {
                    attemptUnloadUnit(transport.x, transport.y, tile.x, tile.y, selectedIndex);
                });
            }
        });
        
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
    // TODO: This RPC method doesn't exist on the server
    // Need to implement proper transport status display
    logger.debug('Transport status display not yet implemented');
    
    // Could use get_cargo_info for selected transport instead:
    if (board.selected && board.selected.unit && isTransportUnitForRender(board.selected.unit)) {
        jsonrpc('get_cargo_info', {
            x: board.selected.x,
            y: board.selected.y
        }, function(result) {
            if (result.success) {
                logger.debug('Transport cargo:', result);
                showTransportFeedback(`Transport has ${result.cargo_count || 0} units loaded`);
            }
        });
    }
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
    logger.info(`[render_legacy] highlightMovementRange called for (${unitX}, ${unitY})`);
    
    // Get movement range data from backend
    jsonrpc('get_movement_highlights', {x: unitX, y: unitY})
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
            logger.error('[render_legacy] Movement range request failed:', error);
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
    
    var landUnits = ['INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 'NEOTANK', 'MEGATANK',
                     'APC', 'ARTILLERY', 'ROCKET', 'ANTIAIR', 'MISSILE', 'PIPERUNNER'];
    var seaUnits = ['BATTLESHIP', 'CRUISER', 'LANDER', 'SUB', 'BLACKBOAT', 'CARRIER'];
    var airUnits = ['FIGHTER', 'BOMBER', 'BCOPTER', 'TCOPTER', 'STEALTH'];
    
    // Sea units can only move on sea/reef/beach/port
    if (seaUnits.includes(unit.type)) {
        return ['SEA', 'REEF', 'BEACH_N', 'BEACH_S', 'BEACH_E', 'BEACH_W', 'PORT'].includes(terrainType);
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
                highlight.x * window.TILESIZE + window.TILESIZE/2, 
                highlight.y * window.TILESIZE + window.TILESIZE/2, 
                window.TILESIZE - 2, 
                window.TILESIZE - 2
            );
            
            // Subtle yellow highlighting
            rect.stroke = '#B8860B';
            rect.fill = 'rgba(255, 248, 220, 0.2)';
            rect.linewidth = 1;
            rect.noFill = false;
            
            window.movementHighlightGroup.add(rect);
            renderedCount++;
        } catch (error) {
            logger.error('Error creating highlight rect:', error);
        }
    });
    
    // Force Two.js update
    try {
        window.two.update();
    } catch (error) {
        logger.error('Error updating Two.js:', error);
    }
}

function clearMovementHighlightsData() {
    // Clear the data array
    if (window.movementHighlights) {
        window.movementHighlights = [];
    }
    
    // Clear can_be_moved_to flags from all tiles
    if (board && board.grid) {
        board.grid.forEach(tile => {
            tile.can_be_moved_to = false;
        });
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
                logger.error('Unit selection failed:', result);
            }
        });
        
    } catch (error) {
        logger.error('Selection error:', error);
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
window.tileAt = tileAt;
window.update = update;
window.unitMove = unitMove;
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
        logger.debug('🎯 advanceWarsUnitSelect called with tile:', tile);
        // Step 1: Backend unit selection
        jsonrpc('unit_select', {token: token, x: tile.x, y: tile.y}).then(result => {
            if (result && !result.error) {
                // Set selection state
                board.selected = tile;
                window.gameState.selectedUnit = tile;
                window.gameState.selectedX = tile.x;
                window.gameState.selectedY = tile.y;
                window.gameState.movementPhase = false;
                window.gameState.showingAttackTargets = false;
                logger.info('✅ Unit selected, gameState updated:', window.gameState.selectedUnit);
                logger.debug(`📍 Coordinates set to (${tile.x}, ${tile.y})`);
                // Show movement range
                if (tile.unit && tile.unit.army === board.current_turn) {
                    clearAllHighlights();
                    showMovementRange(tile.x, tile.y);
                    
                    // Auto-trigger attack highlights if unit can attack
                    if (tile.unit.can_attack) {
                        logger.debug('🎯 Auto-triggering attack highlights for unit');
                        showAttackTargets(tile.x, tile.y);
                    }
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
                logger.error('Unit selection failed:', result);
            }
        });
        
    } catch (error) {
        logger.error('Selection error:', error);
        // Don't make another RPC call here - it causes duplicates
    }
}

// =============================================================================
// MOVEMENT AND ATTACK LOGIC
// =============================================================================

function advanceWarsMove(targetTile) {
    // Use board.selected as fallback since gameState.selectedUnit may not be set due to timing issues
    const selectedUnit = window.gameState?.selectedUnit || board.selected;
    if (!selectedUnit) {
        logger.warn('No unit selected for movement');
        return false;
    }
    
    var source = selectedUnit;
    
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
            
            // Manually update unit's can_move flag after moving
            if (board && board.grid) {
                const movedUnitTile = board.grid.find(t => t.x === targetTile.x && t.y === targetTile.y);
                if (movedUnitTile && movedUnitTile.unit) {
                    logger.info('📝 Unit moved - updating can_move to false');
                    movedUnitTile.unit.can_move = false;
                    // Note: can_attack may still be true after moving
                }
            }
            
            // Enter movement phase
            window.gameState.movementPhase = true;
            // Clear movement highlights
            clearMovementHighlights();
            
            // Show attack targets after movement with longer delay
            setTimeout(async () => {
                // Get the updated tile data after move
                const updatedTile = board.grid.find(t => t.x === targetTile.x && t.y === targetTile.y);
                if (updatedTile) {
                    showAttackTargetsAfterMove(updatedTile.x, updatedTile.y);
                    // Also show action menu for capture/wait options
                    await showPostMoveActionMenu(updatedTile);
                } else {
                    logger.error('Could not find updated tile after move');
                }
            }, 800); // Increased delay to ensure board update completes
            
        } else {
            logger.error('❌ Move failed:', result);
        }
    }).catch(error => {
        logger.error('❌ Move error:', error);
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
        logger.error('Failed to get attack targets:', error);
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
            logger.info('⚔️ Attack result:', result);
            
            // Manually update unit flags since server doesn't do it properly
            if (board && board.grid) {
                const attackerTile = board.grid.find(t => t.x === source.x && t.y === source.y);
                if (attackerTile && attackerTile.unit) {
                    logger.info('📝 Manually updating attacker flags to unavailable');
                    attackerTile.unit.can_move = false;
                    attackerTile.unit.can_attack = false;
                    attackerTile.unit.can_capture = false;
                }
            }
            
            // IMPORTANT: End the unit's turn to clear all highlights
            endUnitTurn();
            // Force immediate update to refresh unit states
            setTimeout(() => {
                update();
            }, 100);
        }).catch(error => {
            logger.error('❌ Attack failed:', error);
            // Also end turn on attack failure
            endUnitTurn();
            update();
        });
    }
    
    return true;
}

function endUnitTurn() {
    
    // Manually update unit flags before clearing selection
    if (window.gameState && window.gameState.selectedUnit) {
        const unitX = window.gameState.selectedUnit.x;
        const unitY = window.gameState.selectedUnit.y;
        
        if (board && board.grid) {
            const unitTile = board.grid.find(t => t.x === unitX && t.y === unitY);
            if (unitTile && unitTile.unit) {
                logger.debug('📝 Ending unit turn - marking as unavailable');
                unitTile.unit.can_move = false;
                unitTile.unit.can_attack = false;
                unitTile.unit.can_capture = false;
            }
        }
        
        window.gameState.selectedUnit = null;
        window.gameState.selectedX = undefined;
        window.gameState.selectedY = undefined;
        logger.debug('📍 Coordinates cleared in endUnitTurn');
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
                highlight.x * window.TILESIZE + window.TILESIZE/2, 
                highlight.y * window.TILESIZE + window.TILESIZE/2, 
                window.TILESIZE - 2, 
                window.TILESIZE - 2
            );
            
            // Red highlighting for attack targets
            rect.stroke = '#DC143C'; // Crimson red
            rect.fill = 'rgba(220, 20, 60, 0.3)'; // Semi-transparent red
            rect.linewidth = 2;
            rect.noFill = false;
            
            window.attackHighlightGroup.add(rect);
            renderedCount++;
        } catch (error) {
            logger.error('Error creating attack highlight rect:', error);
        }
    });
    
    // Force Two.js update
    try {
        window.two.update();
    } catch (error) {
        logger.error('Error updating Two.js:', error);
    }
}

// =============================================================================
// MOVEMENT HIGHLIGHTING (Enhanced)
// =============================================================================

function showMovementRange(unitX, unitY) {
    
    // Use the correct backend movement RPC
    jsonrpc('unit_valid_moves', {token: token, x: unitX, y: unitY})
        .then(result => {
            logger.debug('unit_valid_moves result:', result);
            if (result && result.valid_moves) {
                // Transform to expected format - valid_moves is array of [x,y] tuples
                const highlightMoves = result.valid_moves.map(move => ({
                    x: move[0],
                    y: move[1],
                    cost: 1  // Default cost, actual cost not provided by this RPC
                }));
                applyMovementHighlights(highlightMoves);
            } else {
                calculateMovementRangeLocally(unitX, unitY);
            }
        })
        .catch(error => {
            logger.error('Failed to get valid moves:', error);
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
    
    // Update the board tiles to mark them as moveable
    if (board && board.grid) {
        moves.forEach(move => {
            const tile = board.grid.find(t => t.x === move.x && t.y === move.y);
            if (tile) {
                tile.can_be_moved_to = true;
            }
        });
    }
    
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
    logger.debug('🧹 Clearing all highlights...');
    
    // Clear movement highlights data and visuals
    if (window.movementHighlights) {
        window.movementHighlights = [];
    }
    if (window.movementHighlightGroup && window.two) {
        window.two.remove(window.movementHighlightGroup);
        window.movementHighlightGroup = null;
    }
    
    // Clear attack highlights data and visuals
    if (window.gameState && window.gameState.attackHighlights) {
        window.gameState.attackHighlights = [];
    }
    if (window.attackHighlightGroup && window.two) {
        window.two.remove(window.attackHighlightGroup);
        window.attackHighlightGroup = null;
    }
    
    // Clear transport highlights
    if (typeof clearTransportHighlights === 'function') {
        clearTransportHighlights();
    }
    if (typeof clearAllTransportHighlights === 'function') {
        clearAllTransportHighlights();
    }
    
    // Clear board visual state
    if (board && board.grid) {
        board.grid.forEach(tile => {
            tile.can_be_moved_to = false;
            tile.can_be_attacked = false;
        });
    }
    
    // Force complete re-render
    if (window.two) {
        window.two.update();
    }
    
    logger.debug('✅ All highlights cleared');
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
    // Prevent clicks during operations
    if (window.gameState?.operationInProgress || window.operationQueue?.processing) {
        logger.debug('Click ignored - operation in progress');
        return;
    }
    
    var x = ev.offsetX;
    var y = ev.offsetY;
    var tile = tileAt(x, y);
    
    logger.info(`🖱️ Canvas clicked at (${tile?.x}, ${tile?.y}), can_be_moved_to: ${tile?.can_be_moved_to}, has selected: ${board.selected != null}, board.selected: (${board.selected?.x}, ${board.selected?.y}), gameState selected: (${window.gameState?.selectedX}, ${window.gameState?.selectedY})`);
    
    // PRIORITY 0: New alt-click transport system (HIGHEST PRIORITY)
    if (ev.altKey && typeof handleTransportAltClick === 'function') {
        logger.debug('🔄 Processing alt-click through new transport system');
        const handled = handleTransportAltClick(tile, ev);
        if (handled) {
            logger.debug('✅ Alt-click handled by transport system, stopping propagation');
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
            // Need to get the transport coordinates from frontendTransportState
            if (typeof attemptUnloadUnit === 'function' && window.gameState?.selectedUnit) {
                const transport = window.gameState.selectedUnit;
                
                // Get cargo info and show selection UI if needed
                jsonrpc('get_cargo_info', {x: transport.x, y: transport.y}, function(cargoResult) {
                    if (!cargoResult || cargoResult.error) {
                        logger.error('Failed to get cargo info:', cargoResult?.error);
                        return;
                    }
                    
                    const cargoUnits = cargoResult.cargo || [];
                    if (cargoUnits.length === 0) {
                        logger.warn('Transport has no cargo to unload');
                        return;
                    }
                    
                    // If only one unit, unload it directly
                    if (cargoUnits.length === 1) {
                        attemptUnloadUnit(transport.x, transport.y, tile.x, tile.y, 0);
                    } else {
                        // Show cargo selection UI for multiple units
                        window.cargoSelection.show(cargoUnits, function(selectedIndex) {
                            attemptUnloadUnit(transport.x, transport.y, tile.x, tile.y, selectedIndex);
                        });
                    }
                });
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
                
                // Get cargo info first to show selection UI if needed
                const transport = window.gameState.selectedUnit;
                jsonrpc('get_cargo_info', {x: transport.x, y: transport.y}, function(cargoResult) {
                    if (!cargoResult || cargoResult.error) {
                        logger.error('Failed to get cargo info:', cargoResult?.error);
                        return;
                    }
                    
                    const cargoUnits = cargoResult.cargo || [];
                    if (cargoUnits.length === 0) {
                        logger.warn('Transport has no cargo to unload');
                        return;
                    }
                    
                    function performUnload(cargoIndex) {
                        jsonrpc('cargo_exit_transport', {
                            transport_x: transport.x,
                            transport_y: transport.y,
                            exit_x: tile.x,
                            exit_y: tile.y,
                            cargo_index: cargoIndex
                        }, function(result) {
                            if (result.success || !result.error) {
                                window.gameState.selectedUnit = null;
                                window.gameState.selectedX = undefined;
                                window.gameState.selectedY = undefined;
                                clearAllHighlights();
                                update();
                            } else {
                                logger.error('Failed to unload unit:', result.error);
                            }
                        });
                    }
                    
                    // If only one unit, unload it directly
                    if (cargoUnits.length === 1) {
                        performUnload(0);
                    } else {
                        // Show cargo selection UI for multiple units
                        window.cargoSelection.show(cargoUnits, performUnload);
                    }
                });
                return; // STOP - unload handled
            }
            // Check if selected unit is cargo and clicked tile has transport (LOAD)
            else if (tile.unit && isTransportUnitForRender(tile.unit)) {
                
                jsonrpc('cargo_board_transport', {
                    cargo_x: window.gameState.selectedUnit.x,
                    cargo_y: window.gameState.selectedUnit.y,
                    transport_x: tile.x,
                    transport_y: tile.y
                }, function(loadResult) {
                    if (loadResult.success) {
                        window.gameState.selectedUnit = null;
                        window.gameState.selectedX = undefined;
                        window.gameState.selectedY = undefined;
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
    
    // PRIORITY 4: Transport integration system - DISABLED
    // Centralized click handler manages transport features
    /*
    if (typeof handleTileClickWithTransport === 'function') {
        
        const transportHandled = handleTileClickWithTransport(tile, ev);
        if (transportHandled) {
            return; // STOP - transport integration handled it
        }
    }
    */
    
    // PRIORITY 5: New transport system
    if (typeof window.transportSystem !== 'undefined' && 
        typeof window.transportSystem.handleTransportClick === 'function') {
        
        const newTransportHandled = window.transportSystem.handleTransportClick(tile, ev);
        if (newTransportHandled) {
            return; // STOP - new transport system handled it
        }
    }
    
    // PRIORITY 6: Normal movement system
    // Use board.selected as fallback since gameState.selectedUnit may not be set due to timing issues
    const selectedUnit = window.gameState?.selectedUnit || board.selected;
    if (selectedUnit && tile.can_be_moved_to) {
        advanceWarsMove(tile);  // Fix: pass only target tile, not selectedUnit
        return;
    }
    
    // PRIORITY 7: Attack system
    if (window.gameState && window.gameState.selectedUnit && tile.can_be_attacked) {
        advanceWarsAttack(window.gameState.selectedUnit, tile);
        return;
    }
    
    // PRIORITY 8: Unit selection
    if (tile.unit && window.board && tile.unit.army === window.board.current_turn) {
        advanceWarsUnitSelect(tile);
        return;
    }
    
    // PRIORITY 9: Deselect when clicking empty tiles
    if (window.gameState && window.gameState.selectedUnit) {
        endUnitTurn();
    }
}
// =============================================================================
// ACTION MENU SYSTEM
// =============================================================================

async function showPostMoveActionMenu(tile) {
    logger.info('📋 Checking post-move actions for unit at', tile.x, tile.y);
    
    // Check if unit can capture
    const canCapture = tile.unit && tile.unit.can_capture && 
        (tile.unit.type === 'INFANTRY' || tile.unit.type === 'MECH') &&
        isCapturableProperty(tile.mapTile.type);
    
    // Check if there are attack targets
    const hasAttackTargets = window.gameState && window.gameState.attackHighlights && 
        window.gameState.attackHighlights.length > 0;
    
    // Check if unit can load into transport
    const canLoadTransport = await checkCanLoadTransport(tile);
    
    // Check if unit is a missile that can launch
    const canLaunchMissile = tile.unit && tile.unit.type === 'MISSILE' && 
        window.gameState && window.gameState.attackHighlights && 
        window.gameState.attackHighlights.length > 0;
    
    // Check for other special unit abilities
    const canJoin = tile.unit && checkCanJoinUnit(tile); // Units can join damaged units of same type
    const canSupply = tile.unit && (tile.unit.type === 'APC' || tile.unit.type === 'BLACKBOAT') && checkHasAdjacentUnitsToSupply(tile);
    const canRepair = tile.unit && tile.unit.type === 'BLACKBOAT' && checkHasAdjacentUnitsToRepair(tile);
    
    // If no actions available, auto-wait
    if (!hasAttackTargets && !canCapture && !canLoadTransport && !canLaunchMissile && !canJoin && !canSupply && !canRepair) {
        logger.debug('🤖 No actions available - auto-waiting unit');
        unitWait(tile);
        endUnitTurn();
        return;
    }
    
    logger.debug('📋 Showing action menu - actions available');
    
    // Create action menu
    const menu = document.createElement('div');
    menu.id = 'action-menu';
    menu.style.cssText = `
        position: fixed;
        background: rgba(0, 0, 0, 0.9);
        border: 2px solid #3498db;
        border-radius: 5px;
        padding: 10px;
        z-index: 10000;
        color: white;
        font-family: Arial, sans-serif;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    `;
    
    // Position menu near the unit
    const canvas = document.querySelector('#draw canvas');
    const rect = canvas.getBoundingClientRect();
    const menuX = rect.left + (tile.x * window.TILESIZE * (window.currentZoom || 1)) + 20;
    const menuY = rect.top + (tile.y * window.TILESIZE * (window.currentZoom || 1));
    
    menu.style.left = `${menuX}px`;
    menu.style.top = `${menuY}px`;
    
    // Add menu items
    const actions = [];
    
    if (hasAttackTargets) {
        actions.push({
            text: '⚔️ Attack',
            action: () => {
                logger.info('Attack selected - waiting for target selection');
                closeActionMenu();
                // Attack targets are already highlighted
            }
        });
    }
    
    if (canCapture) {
        actions.push({
            text: '🏴 Capture',
            action: () => {
                logger.debug('Capturing property');
                unitCapture(tile);
                endUnitTurn();
                closeActionMenu();
            }
        });
    }
    
    if (canLoadTransport) {
        actions.push({
            text: '🚛 Load',
            action: () => {
                logger.debug('Loading into transport - use Ctrl+Click on transport');
                closeActionMenu();
                // TODO: Could show transport selection UI here
            }
        });
    }
    
    if (canJoin) {
        actions.push({
            text: '🤝 Join',
            action: () => {
                logger.debug('Join units - not implemented yet');
                // TODO: Implement unit joining
                closeActionMenu();
            }
        });
    }
    
    if (canSupply) {
        actions.push({
            text: '⛽ Supply',
            action: () => {
                logger.debug('Supply units - use right-click menu');
                closeActionMenu();
            }
        });
    }
    
    if (canRepair) {
        actions.push({
            text: '🔧 Repair',
            action: () => {
                logger.debug('Repair units - use right-click menu');
                closeActionMenu();
            }
        });
    }
    
    actions.push({
        text: '⏸️ Wait',
        action: () => {
            logger.debug('Unit waiting');
            unitWait(tile);
            endUnitTurn();
            closeActionMenu();
        }
    });
    
    actions.push({
        text: '❌ Cancel',
        action: () => {
            logger.debug('Action cancelled');
            // Move unit back to original position if possible
            closeActionMenu();
            clearAllHighlights();
        }
    });
    
    // Create menu items
    actions.forEach((action, index) => {
        const item = document.createElement('div');
        item.style.cssText = `
            padding: 8px 12px;
            cursor: pointer;
            transition: background 0.2s;
            border-bottom: 1px solid #2c3e50;
        `;
        item.textContent = action.text;
        
        item.onmouseover = () => {
            item.style.background = 'rgba(52, 152, 219, 0.3)';
        };
        
        item.onmouseout = () => {
            item.style.background = 'transparent';
        };
        
        item.onclick = action.action;
        
        menu.appendChild(item);
    });
    
    // Add to document
    document.body.appendChild(menu);
    
    // Add click-outside handler
    setTimeout(() => {
        document.addEventListener('click', handleClickOutsideMenu);
    }, 100);
}

function closeActionMenu() {
    const menu = document.getElementById('action-menu');
    if (menu) {
        menu.remove();
        document.removeEventListener('click', handleClickOutsideMenu);
    }
}

function handleClickOutsideMenu(event) {
    const menu = document.getElementById('action-menu');
    if (menu && !menu.contains(event.target)) {
        closeActionMenu();
    }
}

function isCapturableProperty(tileType) {
    const capturableTypes = ['CITY', 'BASE_TOWER_1', 'FACTORY', 'PORT', 'AIRPORT'];
    return capturableTypes.includes(tileType);
}

async function checkCanLoadTransport(tile) {
    // Check if there are any adjacent friendly transports that can carry this unit
    if (!tile || !tile.unit) return false;
    
    try {
        // Use the RPC method to get loadable transports
        const result = await jsonrpc('transport_get_loadable_transports', {
            unit_x: tile.x,
            unit_y: tile.y
        });
        
        // Check if there are any transports available
        if (result && result.transports && result.transports.length > 0) {
            logger.debug(`Found ${result.transports.length} loadable transports for unit at (${tile.x},${tile.y})`);
            return true;
        }
        
        return false;
    } catch (error) {
        logger.error('Error checking loadable transports:', error);
        // Fallback to false if RPC fails
        return false;
    }
}

function checkCanJoinUnit(tile) {
    // Units can join with damaged units of the same type
    if (!tile || !tile.unit || tile.unit.status.hp >= 100) return false;
    
    // Check adjacent tiles for same unit type
    const adjacentPositions = [
        {x: tile.x + 1, y: tile.y},
        {x: tile.x - 1, y: tile.y},
        {x: tile.x, y: tile.y + 1},
        {x: tile.x, y: tile.y - 1}
    ];
    
    for (const pos of adjacentPositions) {
        const adjacentTile = board.grid.find(t => t.x === pos.x && t.y === pos.y);
        if (adjacentTile && adjacentTile.unit && 
            adjacentTile.unit.army === tile.unit.army &&
            adjacentTile.unit.type === tile.unit.type &&
            adjacentTile.unit.status.hp < 100) {
            return true;
        }
    }
    
    return false;
}

function checkHasAdjacentUnitsToSupply(tile) {
    // Check if APC/Black Boat has adjacent units that need supplies
    if (!tile || !tile.unit) return false;
    
    const adjacentPositions = [
        {x: tile.x + 1, y: tile.y},
        {x: tile.x - 1, y: tile.y},
        {x: tile.x, y: tile.y + 1},
        {x: tile.x, y: tile.y - 1}
    ];
    
    for (const pos of adjacentPositions) {
        const adjacentTile = board.grid.find(t => t.x === pos.x && t.y === pos.y);
        if (adjacentTile && adjacentTile.unit && adjacentTile.unit.army === tile.unit.army) {
            // Check if unit needs fuel or ammo
            const unit = adjacentTile.unit;
            const maxFuel = getMaxFuel(unit.type);
            const maxAmmo = getMaxAmmo(unit.type);
            
            if ((unit.status.fuel < maxFuel) || (unit.status.ammo < maxAmmo)) {
                return true;
            }
        }
    }
    
    return false;
}

function checkHasAdjacentUnitsToRepair(tile) {
    // Check if Black Boat has adjacent units that need repair
    if (!tile || !tile.unit || tile.unit.type !== 'BLACKBOAT') return false;
    
    const adjacentPositions = [
        {x: tile.x + 1, y: tile.y},
        {x: tile.x - 1, y: tile.y},
        {x: tile.x, y: tile.y + 1},
        {x: tile.x, y: tile.y - 1}
    ];
    
    for (const pos of adjacentPositions) {
        const adjacentTile = board.grid.find(t => t.x === pos.x && t.y === pos.y);
        if (adjacentTile && adjacentTile.unit && 
            adjacentTile.unit.army === tile.unit.army &&
            adjacentTile.unit.status.hp < 100) {
            return true;
        }
    }
    
    return false;
}

function getMaxFuel(unitType) {
    // Default max fuel values - could be loaded from config
    const fuelValues = {
        'INFANTRY': 99, 'MECH': 70, 'RECON': 80, 'TANK': 70,
        'MEDIUMTANK': 50, 'NEOTANK': 99, 'MEGATANK': 50,
        'APC': 70, 'ARTILLERY': 50, 'ROCKET': 50, 'ANTIAIR': 60,
        'MISSILE': 50, 'FIGHTER': 99, 'BOMBER': 99, 'BCOPTER': 99,
        'TCOPTER': 99, 'BATTLESHIP': 99, 'CRUISER': 99, 'LANDER': 99,
        'SUB': 60, 'CARRIER': 99, 'BLACKBOAT': 60, 'BLACKBOMB': 45,
        'STEALTH': 60, 'PIPERUNNER': 99
    };
    return fuelValues[unitType] || 99;
}

function getMaxAmmo(unitType) {
    // Default max ammo values - could be loaded from config
    const ammoValues = {
        'INFANTRY': 0, 'MECH': 3, 'RECON': 0, 'TANK': 9,
        'MEDIUMTANK': 8, 'NEOTANK': 9, 'MEGATANK': 3,
        'APC': 0, 'ARTILLERY': 9, 'ROCKET': 6, 'ANTIAIR': 9,
        'MISSILE': 6, 'FIGHTER': 9, 'BOMBER': 9, 'BCOPTER': 6,
        'TCOPTER': 0, 'BATTLESHIP': 9, 'CRUISER': 9, 'LANDER': 0,
        'SUB': 6, 'CARRIER': 9, 'BLACKBOAT': 0, 'BLACKBOMB': 0,
        'STEALTH': 6, 'PIPERUNNER': 9
    };
    return ammoValues[unitType] || 0;
}

// =============================================================================
// DOUBLE CLICK HANDLER
// =============================================================================

function advanceWarsDoubleClick(ev) {
    var x = ev.offsetX;
    var y = ev.offsetY;
    var tile = tileAt(x, y);
    
    // Check if tile exists
    if (!tile) {
        return;
    }
    
    // Double click on capturable properties
    if (tile.mapTile && (
        tile.mapTile.type === 'CITY' ||
        tile.mapTile.type === 'BASE_TOWER_1' ||
        tile.mapTile.type === 'FACTORY' ||
        tile.mapTile.type === 'PORT' ||
        tile.mapTile.type === 'AIRPORT')) {
        
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
    jsonrpc('unit_wait', {x: tile.x, y: tile.y}).then(result => {
        // Manually update unit flags after wait
        if (board && board.grid) {
            const unitTile = board.grid.find(t => t.x === tile.x && t.y === tile.y);
            if (unitTile && unitTile.unit) {
                logger.debug('📝 Unit waited - marking as unavailable');
                unitTile.unit.can_move = false;
                unitTile.unit.can_attack = false;
                unitTile.unit.can_capture = false;
            }
        }
        // Force update to refresh sprite
        update();
    });
}

function unitCapture(tile) {
    jsonrpc('capture_tile', {x: tile.x, y: tile.y}).then(result => {
        // Manually update unit flags after capture
        if (board && board.grid) {
            const unitTile = board.grid.find(t => t.x === tile.x && t.y === tile.y);
            if (unitTile && unitTile.unit) {
                logger.info('📝 Unit captured - marking as unavailable');
                unitTile.unit.can_move = false;
                unitTile.unit.can_attack = false;
                unitTile.unit.can_capture = false;
            }
        }
        // Force update to refresh sprite
        update();
    });
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
// SIMULATION SYSTEM - Debug tool to simulate user interactions
// =============================================================================

window.simulateGameFlow = async function() {
    logger.debug('🎮 STARTING GAME FLOW SIMULATION');
    logger.debug('=' + '='.repeat(60));
    
    // Find a unit that can move
    const tiles = board.grid.filter(tile => 
        tile.unit && 
        tile.unit.army === board.current_turn &&
        (tile.unit.can_move || tile.unit.can_attack)
    );
    
    if (tiles.length === 0) {
        logger.debug('❌ No units available to simulate');
        return;
    }
    
    const unitTile = tiles[0];
    logger.debug(`\n📍 Found ${unitTile.unit.army} ${unitTile.unit.type} at (${unitTile.x}, ${unitTile.y})`);
    logger.info(`   can_move: ${unitTile.unit.can_move}, can_attack: ${unitTile.unit.can_attack}, can_capture: ${unitTile.unit.can_capture}`);
    
    // Step 1: Select unit
    logger.debug('\n🖱️ STEP 1: Selecting unit...');
    await simulateClick(unitTile.x, unitTile.y);
    await delay(1000);
    
    // Step 2: Check for movement highlights
    logger.info('\n🖱️ STEP 2: Checking movement options...');
    if (window.movementHighlights && window.movementHighlights.length > 0) {
        logger.info(`✅ Movement highlights: ${window.movementHighlights.length} tiles`);
        
        // Find a valid move location
        const moveTarget = window.movementHighlights[0];
        logger.info(`\n🖱️ STEP 3: Moving to (${moveTarget.x}, ${moveTarget.y})...`);
        await simulateClick(moveTarget.x, moveTarget.y);
        await delay(1500);
        
        // Check unit state after move
        logger.info('\n📊 STEP 4: Checking unit state after move...');
        const movedTile = board.grid.find(t => t.x === moveTarget.x && t.y === moveTarget.y);
        if (movedTile && movedTile.unit) {
            logger.info(`   Unit at new position: ${movedTile.unit.type}`);
            logger.info(`   can_move: ${movedTile.unit.can_move}, can_attack: ${movedTile.unit.can_attack}`);
        }
        
        // Step 5: Check for attack options
        logger.info('\n🖱️ STEP 5: Checking attack options...');
        if (window.gameState && window.gameState.attackHighlights && window.gameState.attackHighlights.length > 0) {
            logger.info(`✅ Attack highlights: ${window.gameState.attackHighlights.length} targets`);
            
            const attackTarget = window.gameState.attackHighlights[0];
            logger.info(`\n🖱️ STEP 6: Attacking target at (${attackTarget.x}, ${attackTarget.y})...`);
            await simulateClick(attackTarget.x, attackTarget.y);
            await delay(1500);
        } else {
            logger.info('❌ No attack targets available');
        }
    } else {
        logger.info('❌ No movement options available');
    }
    
    // Final state check
    logger.debug('\n📊 FINAL STATE CHECK:');
    logger.info(`   Movement highlights: ${window.movementHighlights ? window.movementHighlights.length : 0}`);
    logger.info(`   Attack highlights: ${window.gameState?.attackHighlights ? window.gameState.attackHighlights.length : 0}`);
    logger.debug(`   Selected unit: ${board.selected ? 'Yes' : 'No'}`);
    
    logger.debug('\n✅ SIMULATION COMPLETE');
};

async function simulateClick(x, y) {
    const canvas = document.querySelector('#draw canvas');
    if (!canvas) {
        logger.error('Canvas not found');
        return;
    }
    
    // Calculate pixel coordinates
    const pixelX = x * window.TILESIZE + window.TILESIZE/2;
    const pixelY = y * window.TILESIZE + window.TILESIZE/2;
    
    logger.debug(`   🖱️ Simulating click at tile (${x}, ${y}) = pixel (${pixelX}, ${pixelY})`);
    
    // Create synthetic click event
    const event = new MouseEvent('click', {
        bubbles: true,
        cancelable: true,
        view: window,
        offsetX: pixelX,
        offsetY: pixelY,
        clientX: pixelX,
        clientY: pixelY
    });
    
    // Log what should happen
    const tile = board.grid.find(t => t.x === x && t.y === y);
    if (tile) {
        if (tile.unit) {
            logger.debug(`   → Clicking on ${tile.unit.army} ${tile.unit.type}`);
        } else {
            logger.debug(`   → Clicking on empty tile (terrain: ${tile.mapTile.type})`);
        }
    }
    
    // Dispatch the event
    canvas.dispatchEvent(event);
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Add console command
logger.info('💡 TIP: Run simulateGameFlow() to simulate a move/attack sequence');

// Force complete refresh function
window.forceRefresh = async function() {
    logger.debug('🔄 Forcing complete refresh...');
    
    // Clear all visual elements
    clearAllHighlights();
    
    // Clear cached unit sprites
    if (window.sceneElements && window.sceneElements.units) {
        Object.keys(window.sceneElements.units).forEach(key => {
            const unit = window.sceneElements.units[key];
            if (unit && window.two) {
                window.two.remove(unit);
            }
        });
        window.sceneElements.units = {};
    }
    
    // Force reload sprite corrections
    window.spriteCorrections = null;
    await loadSpriteCorrector();
    
    // Update the board
    update();
    
    logger.debug('✅ Refresh complete');
};

logger.info('💡 TIP: Run forceRefresh() for a complete update without F5');

// Test function to verify sprite state updates
window.testSpriteStates = function() {
    logger.info('🧪 TESTING SPRITE STATE UPDATES');
    logger.debug('=' + '='.repeat(60));
    
    // Find all units for current turn
    const currentTurnUnits = board.grid.filter(tile => 
        tile.unit && tile.unit.army === board.current_turn
    );
    
    logger.debug(`\n📊 Found ${currentTurnUnits.length} ${board.current_turn} units:`);
    
    currentTurnUnits.forEach(tile => {
        const unit = tile.unit;
        const canAct = unit.can_move || unit.can_attack;
        const spriteState = canAct ? 'idle' : 'unavailable';
        
        logger.debug(`   ${unit.type} at (${tile.x},${tile.y}):`);
        logger.info(`      can_move: ${unit.can_move}, can_attack: ${unit.can_attack}, can_capture: ${unit.can_capture}`);
        logger.debug(`      sprite state: ${spriteState} (${canAct ? '✅ Available' : '🚫 Unavailable'})`);
    });
    
    logger.info('\n💡 After moving/attacking, units should show as unavailable (grayed out)');
    logger.debug('💡 Run this function again after actions to verify state changes');
};

logger.debug('💡 TIP: Run testSpriteStates() to check unit availability states');

// Quick test for sprite state fix
window.testNewUnitSprite = function() {
    logger.debug('🧪 Testing new unit sprite state');
    logger.debug('A newly created unit should show as unavailable (grayed out)');
    logger.info('because can_move=false and can_attack=false on creation turn.');
    logger.debug('\nCreate a unit and run testSpriteStates() to verify!');
};

logger.debug('💡 TIP: Run testNewUnitSprite() to understand the sprite fix');

// Debug function to check sprite corrections
window.debugSpriteCorrections = function() {
    logger.debug('🔍 Checking sprite corrections...');
    
    if (!window.spriteCorrections) {
        logger.error('❌ Sprite corrections not loaded!');
        return;
    }
    
    logger.debug('✅ Sprite corrections loaded');
    logger.debug('Available states:', Object.keys(window.spriteCorrections));
    
    // Check for BLUE infantry
    const testKeys = [
        'INFANTRY_BLUE_idle_0',
        'INFANTRY_BLUE_unavailable_0',
        'INFANTRY_RED_idle_0'
    ];
    
    testKeys.forEach(key => {
        const idle = window.spriteCorrections.idle && window.spriteCorrections.idle[key];
        const unavailable = window.spriteCorrections.unavailable && window.spriteCorrections.unavailable[key];
        
        if (idle) {
            logger.debug(`✅ Found ${key} in idle: x=${idle.x}, y=${idle.y}`);
        }
        if (unavailable) {
            logger.debug(`✅ Found ${key} in unavailable: x=${unavailable.x}, y=${unavailable.y}`);
        }
        if (!idle && !unavailable) {
            logger.debug(`❌ Missing ${key}`);
        }
    });
};

logger.debug('💡 TIP: Run debugSpriteCorrections() to check sprite data');

// =============================================================================
// UNIT SPRITE TESTING SYSTEM
// =============================================================================

// Complete list of units from your config.ini
// Use window.ALL_UNIT_TYPES to avoid conflicts
window.ALL_UNIT_TYPES = window.ALL_UNIT_TYPES || [
    'INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 'ANTIAIR', 
    'ARTILLERY', 'BCOPTER', 'BATTLESHIP', 'BLACKBOAT', 'BLACKBOMB',
    'BOMBER', 'CARRIER', 'CRUISER', 'FIGHTER', 'LANDER', 'MEGATANK',
    'MISSILE', 'NEOTANK', 'PIPERUNNER', 'ROCKET', 'STEALTH', 'SUB',
    'TCOPTER', 'APC'
];

// Unit categories for organized testing
window.UNIT_CATEGORIES = window.UNIT_CATEGORIES || {
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
    
    window.ALL_UNIT_TYPES.forEach(unitType => {
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
    
    if (window.UNIT_CATEGORIES.LAND.includes(unitType)) {
        targetTile = board.grid.find(tile => 
            tile.mapTile.type === 'FACTORY' && 
            tile.mapTile.army === army &&
            tile.unit === null
        );
    } else if (window.UNIT_CATEGORIES.AIR.includes(unitType)) {
        targetTile = board.grid.find(tile => 
            tile.mapTile.type === 'AIRPORT' && 
            tile.mapTile.army === army &&
            tile.unit === null
        );
    } else if (window.UNIT_CATEGORIES.SEA.includes(unitType)) {
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
    
    window.UNIT_CATEGORIES.LAND.forEach((unit, index) => {
        setTimeout(() => {
            createTestUnit(unit);
        }, index * 1000); // 1 second delay between creations
    });
}

function testAirUnits() {
    
    window.UNIT_CATEGORIES.AIR.forEach((unit, index) => {
        setTimeout(() => {
            createTestUnit(unit);
        }, index * 1000);
    });
}

function testSeaUnits() {
    
    window.UNIT_CATEGORIES.SEA.forEach((unit, index) => {
        setTimeout(() => {
            createTestUnit(unit);
        }, index * 1000);
    });
}

function testAllUnits() {
    
    let delay = 0;
    window.ALL_UNIT_TYPES.forEach(unit => {
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
            logger.error('❌ Visual feedback error:', error);
        }
    }
    
    // ========================================================================
    // FIX 3: Production Building and Movement Click Handler
    // Handles factory clicks and movement execution properly
    // ========================================================================
    
    const originalTransportHandler = window.handleTileClickWithTransport;
    
    window.handleTileClickWithTransport = function(tile) {
        
        // PRIORITY 1: Unit selection (even on production buildings)
        if (tile.unit && tile.unit.army === board.current_turn) {
            // Select the unit first, even if it's on a factory/airport/port
            if (typeof advanceWarsUnitSelect === 'function') {
                advanceWarsUnitSelect(tile);
            } else if (board.selected?.x === tile.x && board.selected?.y === tile.y) {
                // If already selected, deselect
                board.selected = null;
                clearAllHighlights();
            } else {
                // Fallback selection
                board.selected = tile;
            }
            return true; // Return true to indicate we handled it
        }
        
        // PRIORITY 2: Movement execution (clicking on highlighted movement tiles)
        // This should come BEFORE production building checks!
        if (board.selected && !tile.unit && 
            window.movementHighlights && 
            window.movementHighlights.some(h => h.x === tile.x && h.y === tile.y)) {
            
            executeMovement(tile);
            return true; // Return true to indicate we handled it
        }
        
        // PRIORITY 3: Production buildings (factories, airports, ports) - only if no unit selected
        if ((tile.mapTile.type === 'FACTORY' || 
             tile.mapTile.type === 'AIRPORT' || 
             tile.mapTile.type === 'PORT') &&
            tile.mapTile.army === board.current_turn &&
            !tile.unit &&
            !board.selected) {  // Only open production if no unit is selected
            
            if (tile.mapTile.type === 'FACTORY') unitCreate(tile);
            else if (tile.mapTile.type === 'AIRPORT') airunitCreate(tile);
            else if (tile.mapTile.type === 'PORT') seaunitCreate(tile);
            return true; // Return true to indicate we handled it
        }
        
        // PRIORITY 3: Attack execution (clicking on highlighted attack targets)
        if (board.selected && tile.unit && 
            tile.unit.army !== board.current_turn &&
            window.gameState?.attackHighlights &&
            window.gameState.attackHighlights.some(h => h.x === tile.x && h.y === tile.y)) {
            
            executeAttack(tile);
            return true; // Return true to indicate we handled it
        }
        
        // PRIORITY 4: Fall back to original transport logic
        if (originalTransportHandler) {
            return originalTransportHandler(tile);
        }
        
        // Return false to indicate this handler didn't handle the click
        return false;
    };
    
    // ========================================================================
    // FIX 4: Movement Execution with Highlight Clearing
    // Executes unit movement and clears highlights afterwards
    // ========================================================================
    
    window.executeMovement = function(targetTile) {
        
        if (!board.selected) {
            logger.error('❌ No unit selected for movement');
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
                
                // Update the board to show new positions
                update();
                
            } else {
                logger.error('Movement failed:', result?.error);
            }
        }).catch(error => {
            logger.error('❌ Movement error:', error);
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
            window.gameState.selectedX = undefined;
            window.gameState.selectedY = undefined;
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
// MOBILE TOUCH SUPPORT
// ========================================================================

function addTouchSupport(canvas) {
    let touchStartTime = 0;
    let touchStartPos = { x: 0, y: 0 };
    let longPressTimer = null;
    let isDragging = false;
    
    // Convert touch coordinates to canvas coordinates
    function getTouchPos(touch) {
        const rect = canvas.getBoundingClientRect();
        return {
            x: touch.clientX - rect.left,
            y: touch.clientY - rect.top
        };
    }
    
    // Handle touch start (similar to mouse down)
    canvas.addEventListener('touchstart', function(e) {
        e.preventDefault();
        
        const touch = e.touches[0];
        const pos = getTouchPos(touch);
        touchStartTime = Date.now();
        touchStartPos = pos;
        isDragging = false;
        
        // Start long press timer for context menu (500ms)
        longPressTimer = setTimeout(() => {
            const tile = tileAt(pos.x, pos.y);
            if (tile) {
                // Simulate right-click for context menu
                const mockEvent = {
                    offsetX: pos.x,
                    offsetY: pos.y,
                    preventDefault: () => {},
                    stopPropagation: () => {}
                };
                handleTransportRightClick(tile, mockEvent);
            }
        }, 500);
    }, { passive: false });
    
    // Handle touch move (similar to mouse move)
    canvas.addEventListener('touchmove', function(e) {
        e.preventDefault();
        
        const touch = e.touches[0];
        const pos = getTouchPos(touch);
        
        // Check if user is dragging
        const distance = Math.sqrt(
            Math.pow(pos.x - touchStartPos.x, 2) + 
            Math.pow(pos.y - touchStartPos.y, 2)
        );
        
        if (distance > 10) {
            isDragging = true;
            // Cancel long press if dragging
            if (longPressTimer) {
                clearTimeout(longPressTimer);
                longPressTimer = null;
            }
        }
        
        // Update hover info
        const mockEvent = {
            offsetX: pos.x,
            offsetY: pos.y
        };
        canvasMove(mockEvent);
    }, { passive: false });
    
    // Handle touch end (similar to mouse click)
    canvas.addEventListener('touchend', function(e) {
        e.preventDefault();
        
        // Clear long press timer
        if (longPressTimer) {
            clearTimeout(longPressTimer);
            longPressTimer = null;
        }
        
        // If not dragging and quick tap, treat as click
        if (!isDragging) {
            const touchDuration = Date.now() - touchStartTime;
            const pos = touchStartPos;
            
            if (touchDuration < 200) {
                // Quick tap - treat as normal click
                const mockEvent = {
                    offsetX: pos.x,
                    offsetY: pos.y,
                    altKey: false,
                    ctrlKey: false,
                    metaKey: false
                };
                advanceWarsCanvasClick(mockEvent);
            } else if (touchDuration < 500) {
                // Medium tap - could add special handling here
                const mockEvent = {
                    offsetX: pos.x,
                    offsetY: pos.y,
                    altKey: false,
                    ctrlKey: false,
                    metaKey: false
                };
                advanceWarsCanvasClick(mockEvent);
            }
            // Long press is handled by the timer above
        }
    }, { passive: false });
    
    // Handle touch cancel
    canvas.addEventListener('touchcancel', function(e) {
        e.preventDefault();
        
        // Clear any timers
        if (longPressTimer) {
            clearTimeout(longPressTimer);
            longPressTimer = null;
        }
        isDragging = false;
    }, { passive: false });
    
    // Prevent default touch behavior on the canvas
    canvas.addEventListener('gesturestart', function(e) {
        e.preventDefault();
    });
    
    logger.debug('📱 Touch support added to canvas');
}

// Mobile-friendly notification system
function showMobileNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = 'mobile-notification';
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: ${type === 'error' ? '#e74c3c' : '#27ae60'};
        color: white;
        padding: 12px 24px;
        border-radius: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        font-size: 14px;
        font-weight: 500;
        animation: slideUp 0.3s ease;
        min-width: 200px;
        text-align: center;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideDown 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 2500);
}

// ========================================================================
// AUTO-APPLY THE FIXES WHEN PAGE LOADS
// ========================================================================

// Apply fixes when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(applyCompleteClickFix, 200);
    // Update game status if data is available
    if (window.lastGameData) {
        updateGameStatus(window.lastGameData);
    }
});

// Also apply immediately if DOM is already loaded
if (document.readyState !== 'loading') {
    setTimeout(applyCompleteClickFix, 200);
    // Update game status if data is available
    if (window.lastGameData) {
        updateGameStatus(window.lastGameData);
    }
}
// END OF CLICK SYSTEM FIXES

// ========================================================================
// CONTEXT MENU SYSTEM FOR UNIT ACTIONS
// ========================================================================

window.showUnitContextMenu = function(x, y, selectedUnit, targetUnit) {
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
    
    // Store context for when action is clicked
    window.contextMenuData = {
        selectedUnit: selectedUnit,
        targetUnit: targetUnit
    };
    
    // Hide menu when clicking elsewhere
    setTimeout(() => {
        document.addEventListener('click', hideContextMenu, { once: true });
    }, 100);
};

window.hideContextMenu = function() {
    const contextMenu = document.getElementById('unitContextMenu');
    if (contextMenu) {
        contextMenu.style.display = 'none';
    }
    window.contextMenuData = null;
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
        
        const repairParams = {
            token: window.currentGameToken || getGameTokenFromUrl(),
            blackboat_x: selectedUnit.x,
            blackboat_y: selectedUnit.y,
            target_x: targetUnit.x,
            target_y: targetUnit.y,
            hp_to_repair: 2  // Repair 2 HP (max for Black Boat)
        };
        
        rpc('repair_unit', repairParams, function(result) {
            if (result.error) {
                showNotification('Repair failed: ' + result.error, 'error');
            } else {
                const message = `Repaired ${result.hp_repaired || 2} HP for ${result.repair_cost || 0} funds`;
                showNotification(message, 'success');
                // Refresh the board to show updated HP
                updateGameBoard();
            }
        });
    }
    
    hideContextMenu();
};

// Utility function to get game token from URL
function getGameTokenFromUrl() {
    const path = window.location.pathname;
    const match = path.match(/\/game\/([^\/]+)/);
    return match ? match[1] : null;
}

// Notification system
window.showNotification = function(message, type = 'info') {
    // Create notification element if it doesn't exist
    let notification = document.getElementById('gameNotification');
    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'gameNotification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #2c3e50;
            color: #ecf0f1;
            padding: 12px 20px;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            z-index: 10000;
            font-size: 14px;
            max-width: 300px;
            display: none;
        `;
        document.body.appendChild(notification);
    }
    
    // Set color based on type
    const colors = {
        success: '#27ae60',
        error: '#e74c3c',
        warning: '#f39c12',
        info: '#3498db'
    };
    
    notification.style.background = colors[type] || colors.info;
    notification.textContent = message;
    notification.style.display = 'block';
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
};