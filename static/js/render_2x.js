/**
 * Canvas-based 2x Renderer for Advance Wars RPC
 * Direct canvas rendering without Two.js
 */

// Constants
const TILESIZE = 32; // 2x upscaled from 16
const SPRITESIZE = 32;
const HEALTHSIZE = 16; // HP indicators are 16x16

// Sprite map globals
let terrainMap = null;
let unitsMap = null;
let uiMap = null;

// Canvas globals
let canvas = null;
let ctx = null;
let board = null;

// Sprite sheet images
const spriteSheets = {
    terrain: null,
    units: null,
    ui: null
};

// Get token from page
const token = document.getElementById('draw').getAttribute('x-token');

// Game state
const gameState = {
    selectedUnit: null,
    hoveredTile: null,
    operationInProgress: false
};

// Socket.IO connection
const socket = io();

// Set up Socket.IO handlers
socket.on('connect', () => {
    console.log('✅ Socket connected');
    socket.emit('game', token);
});

socket.on('disconnect', () => {
    console.log('❌ Socket disconnected');
});

socket.on('update', (msg) => {
    console.log('📡 Board update received');
    if (msg && msg.board) {
        board = msg.board;
        window.board = board; // Expose globally
        render();
    }
});

/**
 * Load sprite maps from JSON files
 */
async function loadSpriteMaps() {
    try {
        const [terrainResponse, unitsResponse, uiResponse] = await Promise.all([
            fetch('/static/img/sprites_2x/combined/terrain_tileset_2x_map.json'),
            fetch('/static/img/sprites_2x/combined/units_spritesheet_2x_map.json'),
            fetch('/static/img/sprites_2x/combined/ui_spritesheet_2x_map.json')
        ]);
        
        terrainMap = await terrainResponse.json();
        unitsMap = await unitsResponse.json();
        uiMap = await uiResponse.json();
        
        // Expose globally for debugging
        window.terrainMap = terrainMap;
        window.unitsMap = unitsMap;
        window.uiMap = uiMap;
        
        console.log('✅ Loaded 2x sprite maps:', {
            terrain: Object.keys(terrainMap).length,
            units: Object.keys(unitsMap).length,
            ui: Object.keys(uiMap).length
        });
        
        // Load sprite sheet images
        await loadSpriteSheets();
        
    } catch (error) {
        console.error('❌ Failed to load sprite maps:', error);
    }
}

/**
 * Load sprite sheet images
 */
async function loadSpriteSheets() {
    const loadImage = (src) => {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = (e) => reject(new Error(`Failed to load ${src}`));
            img.src = src;
        });
    };
    
    try {
        const [terrain, units, ui] = await Promise.all([
            loadImage('/static/img/sprites_2x/combined/terrain_tileset_2x.png'),
            loadImage('/static/img/sprites_2x/combined/units_spritesheet_2x.png'),
            loadImage('/static/img/sprites_2x/combined/ui_spritesheet_2x.png')
        ]);
        
        spriteSheets.terrain = terrain;
        spriteSheets.units = units;
        spriteSheets.ui = ui;
        
        // Expose globally for debugging
        window.spriteSheets = spriteSheets;
        
        console.log('✅ Loaded sprite sheet images');
        
        // Initialize canvas after sprites are loaded
        initCanvas();
        
    } catch (error) {
        console.error('❌ Failed to load sprite sheets:', error);
    }
}

/**
 * Initialize canvas
 */
function initCanvas() {
    const container = document.getElementById('draw');
    if (!container) {
        console.error('❌ Draw container not found');
        return;
    }
    
    // Create canvas element
    canvas = document.createElement('canvas');
    ctx = canvas.getContext('2d');
    
    // Disable image smoothing for pixel art
    ctx.imageSmoothingEnabled = false;
    ctx.msImageSmoothingEnabled = false;
    ctx.webkitImageSmoothingEnabled = false;
    
    // Add to container
    container.appendChild(canvas);
    
    // Expose globally for debugging
    window.canvas = canvas;
    window.ctx = ctx;
    
    // Set up event listeners
    canvas.addEventListener('click', handleClick);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('contextmenu', handleRightClick);
    canvas.addEventListener('mouseleave', handleMouseLeave);
    
    // Start update loop
    update();
}

/**
 * Generate UUID for JSON-RPC
 */
function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

/**
 * JSON-RPC call function
 */
async function jsonrpc(method, params = {}) {
    params.token = token;
    
    const response = await fetch('/api', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': uuidv4()
        })
    });
    
    const data = await response.json();
    
    if (data.error) {
        throw new Error(data.error.message || 'RPC Error');
    }
    
    return data.result;
}

/**
 * Update board data from server
 */
async function update() {
    try {
        board = await jsonrpc('game_board', {});
        window.board = board; // Expose globally
        
        // Set canvas size based on grid
        if (board && board.grid && board.grid.length > 0) {
            const newWidth = (board.width || 12) * TILESIZE;
            const newHeight = (board.height || 10) * TILESIZE;
            
            console.log(`🎯 Canvas sizing: ${board.width}x${board.height} tiles @ ${TILESIZE}px = ${newWidth}x${newHeight}px`);
            
            if (canvas.width !== newWidth || canvas.height !== newHeight) {
                canvas.width = newWidth;
                canvas.height = newHeight;
                console.log(`✅ Canvas resized to ${canvas.width}x${canvas.height}`);
            }
        }
        
        // Update UI elements
        updateUI();
        
        // Render the board
        render();
    } catch (error) {
        console.error('❌ Failed to update board:', error);
    }
}

/**
 * Main render function
 */
function render() {
    if (!board || !ctx || !spriteSheets.terrain) return;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Render in layers
    renderTerrain();
    renderUnits();
    renderOverlay();
    renderHoverInfo();
}

/**
 * Render terrain tiles
 */
function renderTerrain() {
    if (!board.grid || !terrainMap) return;
    
    const width = board.width || 12;
    const height = board.height || 10;
    
    // First pass: render base tiles
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const index = y * width + x;
            const tile = board.grid[index];
            if (!tile || !tile.mapTile || !tile.mapTile.type) continue;
            
            // For structures and tall sprites, render a plain tile underneath
            const structureTypes = ['CITY', 'FACTORY', 'AIRPORT', 'PORT', 'COM_TOWER', 'LAB', 
                                  'MISSILE_SILO', 'EMPTY_SILO', 'BASE_TOWER_0', 'BASE_TOWER_1', 
                                  'BASE_TOWER_2', 'BASE_TOWER_3', 'BASE_TOWER_4', 'MOUNTAIN', 'WOOD'];
            
            if (structureTypes.includes(tile.mapTile.type)) {
                const plainSprite = terrainMap['PLAIN'];
                if (plainSprite) {
                    ctx.drawImage(
                        spriteSheets.terrain,
                        plainSprite.x, plainSprite.y, plainSprite.w, plainSprite.h,
                        x * TILESIZE, y * TILESIZE, TILESIZE, TILESIZE
                    );
                }
            }
        }
    }
    
    // Second pass: render actual terrain (allows tall sprites to overlap)
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const index = y * width + x;
            const tile = board.grid[index];
            if (!tile || !tile.mapTile || !tile.mapTile.type) continue;
            
            // Get sprite name
            let spriteName = tile.mapTile.type;
            if (tile.mapTile.army && tile.mapTile.army !== 'NEUTRAL') {
                // Check if we need army-specific sprite
                const armySpriteName = `${tile.mapTile.army}_${tile.mapTile.type}`;
                if (terrainMap[armySpriteName]) {
                    spriteName = armySpriteName;
                }
            }
            
            // Draw sprite
            const sprite = terrainMap[spriteName];
            if (sprite) {
                // Handle tall sprites (buildings)
                const fullHeight = sprite.full_height || sprite.h;
                const drawY = fullHeight > TILESIZE ? 
                    y * TILESIZE - (fullHeight - TILESIZE) : 
                    y * TILESIZE;
                
                ctx.drawImage(
                    spriteSheets.terrain,
                    sprite.x, sprite.y - (fullHeight - sprite.h), sprite.w, fullHeight,
                    x * TILESIZE, drawY, sprite.w, fullHeight
                );
            } else {
                // Fallback - draw colored rectangle
                ctx.fillStyle = getTerrainColor(tile.mapTile.type);
                ctx.fillRect(x * TILESIZE, y * TILESIZE, TILESIZE, TILESIZE);
            }
        }
    }
}

/**
 * Render units
 */
function renderUnits() {
    if (!board.grid || !unitsMap) return;
    
    const width = board.width || 12;
    const height = board.height || 10;
    
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const index = y * width + x;
            const tile = board.grid[index];
            if (!tile || !tile.unit) continue;
            
            const unit = tile.unit;
            
            // Build sprite key
            let spriteKey = `${unit.type}_${unit.army}`;
            if (unit.has_moved || unit.done) {
                spriteKey += '_unavailable';
            }
            spriteKey += '_0'; // Animation frame
            
            // Special cases
            if (unit.is_submerged) {
                spriteKey = `${unit.type}_${unit.army}_submerged_0`;
            }
            
            const sprite = unitsMap[spriteKey];
            if (sprite) {
                ctx.drawImage(
                    spriteSheets.units,
                    sprite.x, sprite.y, sprite.w, sprite.h,
                    x * TILESIZE, y * TILESIZE, SPRITESIZE, SPRITESIZE
                );
                
                // Draw HP indicator
                if (unit.hp < 100) {
                    drawHPIndicator(x * TILESIZE, y * TILESIZE, unit.hp, unit.army, unit.has_moved || unit.done);
                }
                
                // Draw status icons
                drawStatusIcons(x * TILESIZE, y * TILESIZE, unit);
            }
        }
    }
}

/**
 * Draw HP indicator
 */
function drawHPIndicator(x, y, hp, army, unavailable) {
    const hpNumber = Math.ceil(hp / 10);
    const hpStr = hpNumber === 10 ? '?' : hpNumber.toString();
    
    let spriteKey;
    if (unavailable) {
        spriteKey = `HP_${army}_${hpStr}`;
    } else {
        spriteKey = `HP_WHITE_${hpStr}`;
    }
    
    const sprite = uiMap[spriteKey];
    if (sprite && spriteSheets.ui) {
        ctx.drawImage(
            spriteSheets.ui,
            sprite.x, sprite.y, sprite.w, sprite.h,
            x + SPRITESIZE - HEALTHSIZE - 2, y + 2, HEALTHSIZE, HEALTHSIZE
        );
    }
}

/**
 * Draw status icons (loaded, capturing, etc)
 */
function drawStatusIcons(x, y, unit) {
    if (!unit || !uiMap) return;
    
    let statusKey = null;
    
    // Check for various status conditions
    if (unit.cargo && unit.cargo.length > 0) {
        statusKey = unit.has_moved ? 'STATUS_UNAVAILABLE_' : 'STATUS_AVAILABLE_';
        statusKey += unit.army + '_LOAD';
    } else if (unit.is_capturing) {
        statusKey = unit.has_moved ? 'STATUS_UNAVAILABLE_' : 'STATUS_AVAILABLE_';
        statusKey += unit.army + '_CAPTURE';
    } else if (unit.is_submerged) {
        statusKey = unit.has_moved ? 'STATUS_UNAVAILABLE_' : 'STATUS_AVAILABLE_';
        statusKey += unit.army + '_SUBMERGED';
    }
    
    // Draw status icon if applicable
    if (statusKey && uiMap[statusKey]) {
        const sprite = uiMap[statusKey];
        ctx.drawImage(
            spriteSheets.ui,
            sprite.x, sprite.y, sprite.w, sprite.h,
            x + 2, y + SPRITESIZE - HEALTHSIZE - 2, HEALTHSIZE, HEALTHSIZE
        );
    }
    
    // Check for low fuel/ammo warnings
    if (unit.fuel && unit.fuel <= 20) {
        const fuelSprite = uiMap['WARNING_FUEL'];
        if (fuelSprite) {
            ctx.drawImage(
                spriteSheets.ui,
                fuelSprite.x, fuelSprite.y, fuelSprite.w, fuelSprite.h,
                x + 2, y + 2, HEALTHSIZE, HEALTHSIZE
            );
        }
    } else if (unit.ammo !== undefined && unit.ammo === 0) {
        const ammoSprite = uiMap['WARNING_AMMO'];
        if (ammoSprite) {
            ctx.drawImage(
                spriteSheets.ui,
                ammoSprite.x, ammoSprite.y, ammoSprite.w, ammoSprite.h,
                x + 2, y + 2, HEALTHSIZE, HEALTHSIZE
            );
        }
    }
}

/**
 * Render overlay (selection, movement highlights, etc)
 */
function renderOverlay() {
    if (!board.grid) return;
    
    const width = board.width || 12;
    const height = board.height || 10;
    
    // Draw movement highlights
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const index = y * width + x;
            const tile = board.grid[index];
            
            if (tile.can_be_moved_to) {
                ctx.fillStyle = 'rgba(255, 255, 0, 0.3)';
                ctx.fillRect(x * TILESIZE, y * TILESIZE, TILESIZE, TILESIZE);
                
                // Draw border
                ctx.strokeStyle = 'rgba(255, 255, 0, 0.8)';
                ctx.lineWidth = 1;
                ctx.strokeRect(x * TILESIZE + 0.5, y * TILESIZE + 0.5, TILESIZE - 1, TILESIZE - 1);
            }
            
            if (tile.can_be_attacked) {
                ctx.fillStyle = 'rgba(255, 0, 0, 0.3)';
                ctx.fillRect(x * TILESIZE, y * TILESIZE, TILESIZE, TILESIZE);
                
                // Draw border
                ctx.strokeStyle = 'rgba(255, 0, 0, 0.8)';
                ctx.lineWidth = 1;
                ctx.strokeRect(x * TILESIZE + 0.5, y * TILESIZE + 0.5, TILESIZE - 1, TILESIZE - 1);
            }
        }
    }
    
    // Draw selection
    if (board.selected) {
        ctx.strokeStyle = '#FFD700';
        ctx.lineWidth = 3;
        ctx.strokeRect(
            board.selected.x * TILESIZE + 1.5, 
            board.selected.y * TILESIZE + 1.5, 
            TILESIZE - 3, 
            TILESIZE - 3
        );
    }
}

/**
 * Render hover info
 */
function renderHoverInfo() {
    if (!gameState.hoveredTile || !board.grid) return;
    
    const { x, y } = gameState.hoveredTile;
    const width = board.width || 12;
    const height = board.height || 10;
    
    if (x < 0 || y < 0 || y >= height || x >= width) return;
    
    // Draw hover outline
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.lineWidth = 1;
    ctx.strokeRect(x * TILESIZE + 0.5, y * TILESIZE + 0.5, TILESIZE - 1, TILESIZE - 1);
}

/**
 * Get fallback color for terrain type
 */
function getTerrainColor(type) {
    const colors = {
        'SEA': '#4080FF',
        'REEF': '#6090FF',
        'PLAIN': '#90C030',
        'WOOD': '#508030',
        'MOUNTAIN': '#806040',
        'ROAD': '#A0A0A0',
        'CITY': '#808080',
        'FACTORY': '#606060',
        'AIRPORT': '#707070',
        'PORT': '#5050A0'
    };
    
    // Check if type contains any key
    for (let key in colors) {
        if (type.includes(key)) {
            return colors[key];
        }
    }
    
    return '#808080'; // Default grey
}

/**
 * Handle click events
 */
function handleClick(event) {
    const rect = canvas.getBoundingClientRect();
    const x = Math.floor((event.clientX - rect.left) / TILESIZE);
    const y = Math.floor((event.clientY - rect.top) / TILESIZE);
    
    console.log(`Click at tile (${x}, ${y})`);
    
    // Emit click event for centralized handler
    const clickEvent = new CustomEvent('tileclick', {
        detail: { x, y, shiftKey: event.shiftKey, altKey: event.altKey }
    });
    document.dispatchEvent(clickEvent);
}

/**
 * Handle mouse move events
 */
function handleMouseMove(event) {
    const rect = canvas.getBoundingClientRect();
    const x = Math.floor((event.clientX - rect.left) / TILESIZE);
    const y = Math.floor((event.clientY - rect.top) / TILESIZE);
    
    // Update hover state
    if (!gameState.hoveredTile || gameState.hoveredTile.x !== x || gameState.hoveredTile.y !== y) {
        gameState.hoveredTile = { x, y };
        
        // Update tile info display
        updateTileInfo(x, y);
        
        // Re-render to show hover
        render();
    }
}

/**
 * Handle mouse leave
 */
function handleMouseLeave() {
    gameState.hoveredTile = null;
    updateTileInfo(-1, -1);
    render();
}

/**
 * Handle right click events
 */
function handleRightClick(event) {
    event.preventDefault();
    
    const rect = canvas.getBoundingClientRect();
    const x = Math.floor((event.clientX - rect.left) / TILESIZE);
    const y = Math.floor((event.clientY - rect.top) / TILESIZE);
    
    // Emit right click event
    const clickEvent = new CustomEvent('tilerightclick', {
        detail: { x, y, clientX: event.clientX, clientY: event.clientY }
    });
    document.dispatchEvent(clickEvent);
}

/**
 * Update tile info display
 */
function updateTileInfo(x, y) {
    const tileInfo = document.getElementById('tile-info');
    if (!tileInfo || !board || !board.grid) return;
    
    const width = board.width || 12;
    const height = board.height || 10;
    
    if (x < 0 || y < 0 || y >= height || x >= width) {
        tileInfo.textContent = '';
        return;
    }
    
    const index = y * width + x;
    const tile = board.grid[index];
    if (!tile) return;
    
    let info = `Tile (${x}, ${y}): ${tile.mapTile?.type || 'unknown'}`;
    
    if (tile.mapTile?.army && tile.mapTile.army !== 'NEUTRAL') {
        info += ` (${tile.mapTile.army})`;
    }
    
    if (tile.unit) {
        info += ` | Unit: ${tile.unit.type} (${tile.unit.army}) HP: ${tile.unit.hp}`;
    }
    
    tileInfo.textContent = info;
}

/**
 * Update UI elements
 */
function updateUI() {
    if (!board) return;
    
    // Update turn info
    const currentTurn = document.getElementById('current-turn');
    if (currentTurn) currentTurn.textContent = board.current_turn || 'RED';
    
    const dayNumber = document.getElementById('day-number');
    if (dayNumber) dayNumber.textContent = board.days || '0';
    
    // Update funds
    const redFunds = document.getElementById('red-funds');
    if (redFunds) redFunds.textContent = (board.red_funds || 0).toLocaleString();
    
    const blueFunds = document.getElementById('blue-funds');
    if (blueFunds) blueFunds.textContent = (board.blue_funds || 0).toLocaleString();
}

// Initialize on load
window.addEventListener('load', () => {
    console.log('🎮 Initializing Canvas 2x Renderer');
    
    // Check if draw container exists
    if (!document.getElementById('draw')) {
        console.error('❌ Draw container not found - waiting for DOM');
        return;
    }
    
    loadSpriteMaps();
});

// Also try DOMContentLoaded as backup
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 DOMContentLoaded - checking if already initialized');
    if (!window.terrainMap && document.getElementById('draw')) {
        console.log('🔄 Initializing from DOMContentLoaded');
        loadSpriteMaps();
    }
});

// Expose functions for external use
window.updateBoard = update;
window.render2x = render;
window.gameState2x = gameState;

// Set refresh interval
setInterval(update, 5000);

// Try immediate initialization if DOM is ready
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    if (document.getElementById('draw')) {
        console.log('🚀 Immediate initialization attempt');
        loadSpriteMaps();
    }
}