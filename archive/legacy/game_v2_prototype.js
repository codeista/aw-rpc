/**
 * Minimal Game Renderer v2 - Uses clean API with 8 methods
 * Player-based system, no hardcoded colors
 */

class GameV2 {
    constructor() {
        this.canvas = document.getElementById('game-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.tileSize = 32;
        this.gameId = null;
        this.gameState = null;
        this.sprites = null;
        this.socket = null;
        this.playerColors = {}; // player_id -> color mapping
        
        this.init();
    }
    
    async init() {
        // Load sprites first
        await this.loadSprites();
        
        // Setup socket connection
        this.setupSocket();
        
        // Setup input handlers
        this.setupInput();
        
        // Create or join game
        await this.initGame();
    }
    
    async initGame() {
        // Use TOKEN from template
        if (typeof TOKEN !== 'undefined' && TOKEN) {
            this.gameId = TOKEN;
            await this.updateGameState();
        } else {
            console.error('No game token provided');
        }
    }
    
    async updateGameState() {
        console.log('Updating game state for gameId:', this.gameId);
        const state = await this.rpc('game_board', { token: this.gameId });
        this.gameState = state;
        
        // Update player color mapping
        this.playerColors = {};
        for (const [playerId, playerData] of Object.entries(state.players)) {
            this.playerColors[playerId] = playerData.color;
        }
        
        this.render();
    }
    
    async loadSprites() {
        try {
            // Load sprite data using existing sprite system
            const [terrainData, unitData] = await Promise.all([
                fetch('/static/img/optimized_tileset_map.json').then(r => r.json()),
                fetch('/static/img/units_sprite_map_complete.json').then(r => r.json())
            ]);
            
            // Load images
            const terrainImg = new Image();
            const unitsImg = new Image();
            
            await Promise.all([
                new Promise(r => { terrainImg.onload = r; terrainImg.src = '/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png'; }),
                new Promise(r => { unitsImg.onload = r; unitsImg.src = '/static/img/units_sprite_sheet_complete.png'; })
            ]);
            
            this.sprites = {
                terrain: { data: terrainData, img: terrainImg },
                units: { data: unitData, img: unitsImg }
            };
            
            console.log('Sprites loaded');
        } catch (e) {
            console.error('Failed to load sprites:', e);
        }
    }
    
    setupSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected');
            if (this.gameId) {
                this.socket.emit('game', this.gameId);
            }
        });
        
        this.socket.on('update', (msg) => {
            // Update game state when server sends updates
            this.updateGameState();
        });
    }
    
    setupInput() {
        // Canvas click
        this.canvas.addEventListener('click', async (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = Math.floor((e.clientX - rect.left) / this.tileSize);
            const y = Math.floor((e.clientY - rect.top) / this.tileSize);
            
            await this.handleClick(x, y);
        });
        
        // Right click for production
        this.canvas.addEventListener('contextmenu', async (e) => {
            e.preventDefault();
            const rect = this.canvas.getBoundingClientRect();
            const x = Math.floor((e.clientX - rect.left) / this.tileSize);
            const y = Math.floor((e.clientY - rect.top) / this.tileSize);
            
            await this.handleRightClick(x, y);
        });
        
        // Mouse move for tile info
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = Math.floor((e.clientX - rect.left) / this.tileSize);
            const y = Math.floor((e.clientY - rect.top) / this.tileSize);
            
            this.showTileInfo(x, y);
        });
        
        // End turn button
        document.getElementById('end-turn').addEventListener('click', async () => {
            await this.rpc('v2.end_turn', { game_id: this.gameId });
        });
        
        // Modal buttons
        document.getElementById('create').addEventListener('click', async () => {
            const select = document.getElementById('unit-select');
            const modal = document.getElementById('modal');
            
            if (this.productionCoords && select.value) {
                await this.rpc('v2.create_unit', {
                    game_id: this.gameId,
                    facility_x: this.productionCoords.x,
                    facility_y: this.productionCoords.y,
                    unit_type: select.value
                });
                modal.style.display = 'none';
            }
        });
        
        document.getElementById('cancel').addEventListener('click', () => {
            document.getElementById('modal').style.display = 'none';
        });
    }
    
    async handleClick(x, y) {
        if (!this.gameState) return;
        
        // Check if we have an active unit
        if (this.gameState.active_unit) {
            const [ax, ay] = this.gameState.active_unit;
            
            // Find if clicked tile is a valid action
            if (this.selection && this.selection.selection) {
                const validMoves = this.selection.selection.valid_moves || [];
                const validAttacks = this.selection.selection.valid_attacks || [];
                
                // Check if it's a valid move
                const moveTarget = validMoves.find(m => m.x === x && m.y === y);
                if (moveTarget) {
                    await this.rpc('v2.move_unit', {
                        game_id: this.gameId,
                        from_x: ax,
                        from_y: ay,
                        to_x: x,
                        to_y: y
                    });
                    return;
                }
                
                // Check if it's a valid attack
                const attackTarget = validAttacks.find(a => a.x === x && a.y === y);
                if (attackTarget) {
                    await this.rpc('v2.attack', {
                        game_id: this.gameId,
                        target_x: x,
                        target_y: y
                    });
                    return;
                }
            }
        }
        
        // Otherwise, select the tile
        this.selection = await this.rpc('v2.select_tile', {
            game_id: this.gameId,
            x,
            y
        });
    }
    
    async handleRightClick(x, y) {
        // Get production options for this tile
        try {
            const options = await this.rpc('v2.get_production_options', {
                game_id: this.gameId,
                x,
                y
            });
            
            if (options && options.available_units && options.available_units.length > 0) {
                this.showProduction(x, y, options);
            }
        } catch (e) {
            // Not a production building
        }
    }
    
    showProduction(x, y, options) {
        const select = document.getElementById('unit-select');
        select.innerHTML = '';
        
        options.available_units.forEach(unit => {
            const option = document.createElement('option');
            option.value = unit.type;
            option.textContent = `${unit.type.toUpperCase()} - ${unit.cost}G`;
            if (!unit.can_afford) {
                option.disabled = true;
                option.textContent += ' (Can\'t afford)';
            }
            select.appendChild(option);
        });
        
        this.productionCoords = { x, y };
        document.getElementById('modal').style.display = 'flex';
    }
    
    showTileInfo(x, y) {
        if (!this.gameState) return;
        
        const tile = this.gameState.board.tiles.find(t => t.x === x && t.y === y);
        const info = document.getElementById('tile-info');
        
        if (tile) {
            let text = `(${x},${y}) ${tile.terrain.type}`;
            if (tile.building) {
                text += ` | ${tile.building.type.toUpperCase()}`;
                if (tile.building.owner) {
                    const player = this.gameState.players[tile.building.owner];
                    text += ` (${player.name})`;
                }
            }
            if (tile.unit) {
                text += ` | ${tile.unit.type.toUpperCase()} HP:${tile.unit.hp}`;
            }
            info.textContent = text;
        } else {
            info.textContent = '';
        }
    }
    
    render() {
        if (!this.gameState || !this.sprites) {
            return;
        }
        
        const board = this.gameState.board;
        
        // Set canvas size
        const width = board.width * this.tileSize;
        const height = board.height * this.tileSize;
        
        if (this.canvas.width !== width || this.canvas.height !== height) {
            this.canvas.width = width;
            this.canvas.height = height;
            this.ctx.imageSmoothingEnabled = false;
        }
        
        // Clear canvas
        this.ctx.fillStyle = '#7CB068';
        this.ctx.fillRect(0, 0, width, height);
        
        // Render in three passes
        this.renderTerrain();
        this.renderTallObjects();
        this.renderUnitsAndUI();
        
        // Update UI
        this.updateUI();
    }
    
    renderTerrain() {
        // First pass: non-tall terrain
        for (const tile of this.gameState.board.tiles) {
            const px = tile.x * this.tileSize;
            const py = tile.y * this.tileSize;
            
            // Skip tall objects for now
            const tallTypes = ['city', 'factory', 'airport', 'port', 'hq', 'base_tower_0', 'base_tower_1', 'base_tower_2', 'base_tower_3', 'base_tower_4', 'mountain', 'wood'];
            if (tile.building && tallTypes.includes(tile.building.type)) continue;
            if (tallTypes.includes(tile.terrain.type)) continue;
            
            // Draw terrain
            this.drawTerrainSprite(tile, px, py);
        }
    }
    
    renderTallObjects() {
        // Second pass: tall objects from top to bottom
        // This allows lower tiles to properly overlap upper tiles
        const sortedTiles = [...this.gameState.board.tiles].sort((a, b) => a.y - b.y);
        
        for (const tile of sortedTiles) {
            const px = tile.x * this.tileSize;
            const py = tile.y * this.tileSize;
            
            const tallTypes = ['city', 'factory', 'airport', 'port', 'hq', 'base_tower_0', 'base_tower_1', 'base_tower_2', 'base_tower_3', 'base_tower_4', 'mountain', 'wood'];
            
            // Draw tall terrain
            if (tallTypes.includes(tile.terrain.type)) {
                this.drawTerrainSprite(tile, px, py);
            }
            
            // Draw buildings
            if (tile.building && tallTypes.includes(tile.building.type)) {
                this.drawBuildingSprite(tile, px, py);
            }
        }
    }
    
    renderUnitsAndUI() {
        // Third pass: highlights, units, UI
        for (const tile of this.gameState.board.tiles) {
            const px = tile.x * this.tileSize;
            const py = tile.y * this.tileSize;
            
            // Draw movement highlights
            if (this.selection && this.selection.selection) {
                const validMoves = this.selection.selection.valid_moves || [];
                if (validMoves.some(m => m.x === tile.x && m.y === tile.y)) {
                    this.ctx.fillStyle = 'rgba(255, 255, 0, 0.3)';
                    this.ctx.fillRect(px, py, this.tileSize, this.tileSize);
                }
                
                const validAttacks = this.selection.selection.valid_attacks || [];
                if (validAttacks.some(a => a.x === tile.x && a.y === tile.y)) {
                    this.ctx.fillStyle = 'rgba(255, 0, 0, 0.3)';
                    this.ctx.fillRect(px, py, this.tileSize, this.tileSize);
                }
            }
            
            // Draw unit
            if (tile.unit) {
                this.drawUnitSprite(tile.unit, px, py);
            }
        }
        
        // Draw selection box
        if (this.gameState.selected) {
            const [sx, sy] = this.gameState.selected;
            const px = sx * this.tileSize;
            const py = sy * this.tileSize;
            this.ctx.strokeStyle = '#FFD700';
            this.ctx.lineWidth = 3;
            this.ctx.strokeRect(px + 1.5, py + 1.5, this.tileSize - 3, this.tileSize - 3);
        }
        
        // Draw active unit indicator
        if (this.gameState.active_unit) {
            const [ax, ay] = this.gameState.active_unit;
            const px = ax * this.tileSize;
            const py = ay * this.tileSize;
            this.ctx.strokeStyle = '#00FF00';
            this.ctx.lineWidth = 2;
            this.ctx.strokeRect(px + 0.5, py + 0.5, this.tileSize - 1, this.tileSize - 1);
        }
    }
    
    drawTerrainSprite(tile, x, y) {
        let spriteName = tile.terrain.type.toUpperCase();
        
        // Fix beach tile names
        if (spriteName === 'BEACH_N') {
            spriteName = 'BEACH_W';
        } else if (spriteName === 'BEACH_W') {
            spriteName = 'BEACH_N';
        }
        
        this.drawSprite('terrain', spriteName, x, y);
    }
    
    drawBuildingSprite(tile, x, y) {
        let spriteName = tile.building.type.toUpperCase();
        
        // Map HQ to BASE_TOWER_0
        if (spriteName === 'HQ') {
            spriteName = 'BASE_TOWER_0';
        }
        
        // Add owner color prefix if owned
        if (tile.building.owner) {
            // Get sprite color from mapping, fallback to player color or owner
            let color;
            if (this.gameState.sprite_mapping && tile.building.player_id !== undefined) {
                // V2 game with sprite mapping
                color = this.gameState.sprite_mapping[tile.building.player_id] || 'RED';
            } else if (tile.building.owner !== undefined && this.playerColors[tile.building.owner]) {
                // Legacy with owner field
                color = this.playerColors[tile.building.owner].toUpperCase();
            } else if (tile.building.army !== undefined) {
                // Fallback to army field
                color = tile.building.army;
            } else {
                color = 'NEUTRAL';
            }
            spriteName = `${color}_${spriteName}`;
        }
        
        this.drawSprite('terrain', spriteName, x, y);
    }
    
    drawUnitSprite(unit, x, y) {
        // Get sprite color from mapping, fallback to player color or unit army
        let color;
        if (this.gameState.sprite_mapping && unit.player_id !== undefined) {
            // V2 game with sprite mapping
            color = this.gameState.sprite_mapping[unit.player_id] || 'RED';
        } else if (unit.owner !== undefined && this.playerColors[unit.owner]) {
            // Legacy with owner field
            color = this.playerColors[unit.owner].toUpperCase();
        } else if (unit.army !== undefined) {
            // Fallback to army field
            color = unit.army;
        } else {
            // Ultimate fallback
            color = 'RED';
        }
        
        const state = unit.has_acted ? 'unavailable' : 'idle';
        const spriteName = `${unit.type.toUpperCase()}_${color}_${state}_0`;
        
        this.drawSprite('units', spriteName, x, y);
        
        // Draw HP if damaged
        if (unit.hp < 100) {
            const hp = Math.ceil(unit.hp / 10);
            const hpNum = hp === 10 ? 9 : hp;
            const hpSprite = unit.has_acted ? 
                `hp_${color.toLowerCase()}_${hpNum}` : 
                `hp_${hpNum}`;
            this.drawSprite('ui', hpSprite, x + 16, y + 2);
        }
    }
    
    drawSprite(type, name, x, y) {
        const sprite = this.sprites[type].data[name];
        if (!sprite) {
            console.warn(`Sprite not found: ${type}/${name}`);
            return;
        }
        
        if (type === 'units' || type === 'ui') {
            this.ctx.drawImage(
                this.sprites[type].img,
                sprite.x, sprite.y, sprite.w, sprite.h,
                x, y, sprite.w, sprite.h
            );
        } else {
            // Handle tall sprites for terrain
            const fullHeight = sprite.full_height || sprite.h;
            
            // For tall sprites, sprite.y marks the bottom of the sprite
            // We need to read from (sprite.y - fullHeight) to get the full sprite
            const sourceY = sprite.y - fullHeight;
            
            // Draw the sprite so its bottom aligns with the tile bottom
            // For a 64px sprite on a 32px tile, start drawing 32px higher
            const drawY = y - (fullHeight - this.tileSize);
            
            this.ctx.drawImage(
                this.sprites[type].img,
                sprite.x, sourceY, sprite.w, fullHeight,
                x, drawY, sprite.w, fullHeight
            );
        }
    }
    
    updateUI() {
        const state = this.gameState;
        const currentPlayer = state.players[state.current_player];
        
        document.getElementById('current-turn').textContent = currentPlayer.name;
        document.getElementById('current-turn').style.color = currentPlayer.color;
        document.getElementById('day').textContent = state.day;
        
        // Update all player funds
        const fundsDiv = document.getElementById('player-funds');
        fundsDiv.innerHTML = '';
        for (const [playerId, player] of Object.entries(state.players)) {
            const span = document.createElement('span');
            span.textContent = `${player.name}: ${player.funds}G`;
            span.style.color = player.color;
            span.style.marginRight = '20px';
            fundsDiv.appendChild(span);
        }
    }
    
    async rpc(method, params = {}) {
        try {
            const requestBody = {
                jsonrpc: '2.0',
                method: method,
                params: params,
                id: Date.now().toString()
            };
            console.log('RPC Request:', method, params);
            
            const response = await fetch('/api', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });
            
            const data = await response.json();
            if (data.error) {
                console.error('RPC Error Response:', data.error);
                throw new Error(data.error.message);
            }
            
            // Auto-update state after most operations
            if (!['v2.game_state', 'v2.get_production_options', 'v2.create_game'].includes(method)) {
                await this.updateGameState();
            }
            
            console.log('RPC Success:', method, data.result);
            return data.result;
        } catch (e) {
            console.error('RPC error:', e);
            throw e;
        }
    }
}

// Start game when page loads
window.addEventListener('DOMContentLoaded', () => {
    window.game = new GameV2();
});