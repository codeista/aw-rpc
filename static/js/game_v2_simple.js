/**
 * Minimal Game Renderer
 * No legacy code, no complexity, just essentials
 */

class Game {
    constructor() {
        this.canvas = document.getElementById('game-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.tileSize = 32;
        this.board = null;
        this.sprites = null;
        this.socket = null;
        
        this.init();
    }
    
    async init() {
        // Load sprites first
        await this.loadSprites();
        
        // Setup socket connection
        this.setupSocket();
        
        // Setup input handlers
        this.setupInput();
        
        // Get initial board state
        await this.rpc('game_board');
    }
    
    async loadSprites() {
        try {
            // Load sprite data
            const [terrain, units, ui] = await Promise.all([
                fetch('/static/img/sprites_2x/combined/terrain_tileset_2x_map.json').then(r => r.json()),
                fetch('/static/img/sprites_2x/combined/units_spritesheet_2x_map.json').then(r => r.json()),
                fetch('/static/img/sprites_2x/combined/ui_spritesheet_2x_map.json').then(r => r.json())
            ]);
            
            // Load images
            const terrainImg = new Image();
            const unitsImg = new Image();
            const uiImg = new Image();
            
            await Promise.all([
                new Promise(r => { terrainImg.onload = r; terrainImg.src = '/static/img/sprites_2x/combined/terrain_tileset_2x.png'; }),
                new Promise(r => { unitsImg.onload = r; unitsImg.src = '/static/img/sprites_2x/combined/units_spritesheet_2x.png'; }),
                new Promise(r => { uiImg.onload = r; uiImg.src = '/static/img/sprites_2x/combined/ui_spritesheet_2x.png'; })
            ]);
            
            this.sprites = {
                terrain: { data: terrain, img: terrainImg },
                units: { data: units, img: unitsImg },
                ui: { data: ui, img: uiImg }
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
            this.socket.emit('game', TOKEN);
        });
        
        this.socket.on('update', (msg) => {
            if (msg && msg.board) {
                this.board = msg.board;
                this.render();
            }
        });
    }
    
    setupInput() {
        // Canvas click
        this.canvas.addEventListener('click', async (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = Math.floor((e.clientX - rect.left) / this.tileSize);
            const y = Math.floor((e.clientY - rect.top) / this.tileSize);
            
            console.log(`Click at (${x},${y}), selected:`, this.board?.selected);
            
            // Simple click handling based on board state
            if (this.board && this.board.selected) {
                // Check if clicking on same tile as selected - deselect
                if (this.board.selected.x === x && this.board.selected.y === y) {
                    await this.rpc('unit_select', { x, y });
                    return;
                }
                
                const clickedTile = this.getTile(x, y);
                
                // PRIORITY 1: Check if this tile is highlighted for movement
                if (clickedTile && clickedTile.can_be_moved_to) {
                    // This is a valid move target - always try movement
                    console.log('Tile is highlighted for movement, attempting move');
                    try {
                        const moveResult = await this.rpc('unit_move', {
                            x: this.board.selected.x,
                            y: this.board.selected.y,
                            x2: x,
                            y2: y
                        });
                        console.log('Move result:', moveResult);
                        return; // Movement handled
                    } catch (moveError) {
                        console.log('Move failed:', moveError);
                        // Fall through to other options
                    }
                }
                
                // PRIORITY 2: Check if clicking on empty production building (not a move target)
                if (clickedTile && !clickedTile.unit && clickedTile.mapTile && 
                    ['FACTORY', 'AIRPORT', 'PORT'].includes(clickedTile.mapTile.type)) {
                    // Check ownership
                    let isOwner = false;
                    if (this.board.current_player !== undefined) {
                        isOwner = clickedTile.mapTile.player_id === this.board.current_player;
                    } else {
                        isOwner = clickedTile.mapTile.army === this.board.current_turn;
                    }
                    
                    if (isOwner) {
                        console.log('Showing production for empty factory at', x, y);
                        this.showProduction(x, y);
                        return;
                    }
                }
                
                // PRIORITY 3: Check if unit has already moved/acted
                const selectedTile = this.getTile(this.board.selected.x, this.board.selected.y);
                if (selectedTile?.unit) {
                    console.log('Selected unit state:', {
                        type: selectedTile.unit.type,
                        has_moved: selectedTile.unit.has_moved,
                        done: selectedTile.unit.done,
                        canAct: !selectedTile.unit.has_moved && !selectedTile.unit.done
                    });
                    
                    // Check various ways the unit might be marked as done
                    if (selectedTile.unit.has_moved === true || 
                        selectedTile.unit.done === true ||
                        selectedTile.unit.has_moved === 1 ||
                        selectedTile.unit.done === 1) {
                        console.log('Selected unit has already acted, handling as new click');
                        await this.handleFreshClick(x, y);
                        return;
                    }
                }
                
                // PRIORITY 4: Try attack if not a movement target
                if (clickedTile && clickedTile.can_be_attacked) {
                    console.log('Tile is highlighted for attack, attempting attack');
                    try {
                        const attackResult = await this.rpc('unit_attack_enhanced', {
                            attacker_x: this.board.selected.x,
                            attacker_y: this.board.selected.y,
                            defender_x: x,
                            defender_y: y
                        });
                        console.log('Attack result:', attackResult);
                        return;
                    } catch (attackError) {
                        console.log('Attack failed:', attackError);
                    }
                }
                
                // If nothing else worked, handle as fresh click
                console.log('No valid action for click, handling as fresh click');
                await this.handleFreshClick(x, y);
            } else {
                await this.handleFreshClick(x, y);
            }
        });
        
        // Right click for production
        this.canvas.addEventListener('contextmenu', async (e) => {
            e.preventDefault();
            const rect = this.canvas.getBoundingClientRect();
            const x = Math.floor((e.clientX - rect.left) / this.tileSize);
            const y = Math.floor((e.clientY - rect.top) / this.tileSize);
            
            // Check if it's a production building
            const tile = this.getTile(x, y);
            if (tile && tile.mapTile && ['FACTORY', 'AIRPORT', 'PORT'].includes(tile.mapTile.type)) {
                console.log('Production building clicked:', {
                    type: tile.mapTile.type,
                    army: tile.mapTile.army,
                    player_id: tile.mapTile.player_id,
                    current_player: this.board.current_player,
                    current_turn: this.board.current_turn,
                    has_unit: !!tile.unit
                });
                
                // For v2 games, check player ownership differently
                let isOwner = false;
                
                if (this.board.current_player !== undefined) {
                    // V2 game - check if building's player_id matches current player
                    isOwner = tile.mapTile.player_id === this.board.current_player;
                    console.log('V2 ownership check:', isOwner);
                } else {
                    // Legacy game - check army
                    isOwner = tile.mapTile.army === this.board.current_turn;
                    console.log('Legacy ownership check:', isOwner);
                }
                
                if (isOwner && !tile.unit) {
                    this.showProduction(x, y);
                } else {
                    console.log('Cannot produce:', isOwner ? 'Unit present' : 'Not owner');
                }
            }
        });
        
        // Mouse move for tile info
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = Math.floor((e.clientX - rect.left) / this.tileSize);
            const y = Math.floor((e.clientY - rect.top) / this.tileSize);
            
            const tile = this.getTile(x, y);
            const info = document.getElementById('tile-info');
            
            if (tile) {
                let text = `(${x},${y}) ${tile.mapTile?.type || ''}`;
                if (tile.unit) {
                    // HP is in status object
                    const hp = tile.unit.status ? tile.unit.status.hp : 100;
                    text += ` | ${tile.unit.type} HP:${hp}`;
                    // Add fuel and ammo status
                    if (tile.unit.status) {
                        const fuel = tile.unit.status.fuel;
                        const ammo = tile.unit.status.ammo;
                        text += ` F:${fuel}`;
                        if (ammo !== null && ammo !== undefined) {
                            text += ` A:${ammo}`;
                        }
                        // Add warnings
                        if (fuel < 20) text += ' ⚠️LOW FUEL';
                        if (ammo !== null && ammo <= 1) text += ' ⚠️LOW AMMO';
                    }
                }
                info.textContent = text;
            } else {
                info.textContent = '';
            }
        });
        
        // End turn button
        document.getElementById('end-turn').addEventListener('click', async () => {
            await this.rpc('army_end_turn');
        });
        
        // Modal buttons
        document.getElementById('create').addEventListener('click', async () => {
            const select = document.getElementById('unit-select');
            const modal = document.getElementById('modal');
            
            if (this.productionCoords && select.value) {
                await this.rpc('produce_unit', {
                    x: this.productionCoords.x,
                    y: this.productionCoords.y,
                    unit_type: select.value
                });
                modal.style.display = 'none';
            }
        });
        
        document.getElementById('cancel').addEventListener('click', () => {
            document.getElementById('modal').style.display = 'none';
        });
    }
    
    async rpc(method, params = {}) {
        try {
            const response = await fetch('/api', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: method,
                    params: { token: TOKEN, ...params },
                    id: Date.now().toString()
                })
            });
            
            const data = await response.json();
            if (data.error) {
                throw new Error(data.error.message);
            }
            
            // Always update board after RPC call
            await this.updateBoard();
            
            // Check if we should deselect after certain actions
            if (method === 'unit_move' && this.board?.selected) {
                await this.checkPostActionSelection();
            }
            
            return data.result;
        } catch (e) {
            console.error('RPC error:', e);
            throw e;
        }
    }
    
    async updateBoard() {
        const response = await fetch('/api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'game_board',
                params: { token: TOKEN },
                id: Date.now().toString()
            })
        });
        
        const data = await response.json();
        if (data.result) {
            this.board = data.result;
            
            // Handle v2 games with player data
            if (this.board.players && this.board.sprite_mapping) {
                console.log('V2 game detected with players:', this.board.players);
                
                // Create sprite mapper if available
                if (typeof SpriteMapper !== 'undefined') {
                    this.spriteMapper = new SpriteMapper(this.board.players, this.board.sprite_mapping);
                }
            }
            
            this.render();
        }
    }
    
    getTile(x, y) {
        if (!this.board || x < 0 || y < 0 || x >= this.board.width || y >= this.board.height) {
            return null;
        }
        return this.board.grid[y * this.board.width + x];
    }
    
    async handleFreshClick(x, y) {
        const tile = this.getTile(x, y);
        
        // First check if there's a unit to select
        if (tile && tile.unit) {
            await this.rpc('unit_select', { x, y });
        }
        // Then check if it's an empty production building
        else if (tile && tile.mapTile && ['FACTORY', 'AIRPORT', 'PORT'].includes(tile.mapTile.type)) {
            // Check ownership
            let isOwner = false;
            if (this.board.current_player !== undefined) {
                isOwner = tile.mapTile.player_id === this.board.current_player;
            } else {
                isOwner = tile.mapTile.army === this.board.current_turn;
            }
            
            if (isOwner && !tile.unit) {
                // Left click on own empty factory - show production
                console.log('Showing production for empty factory at', x, y);
                this.showProduction(x, y);
                return;
            } else {
                // Not owner or has unit, clear selection
                console.log('Factory not available for production:', {owner: isOwner, hasUnit: !!tile.unit});
                await this.rpc('unit_select', { x, y });
            }
        }
        // Otherwise clear selection
        else {
            await this.rpc('unit_select', { x, y });
        }
    }
    
    async checkPostActionSelection() {
        if (!this.board || !this.board.selected) return;
        
        // Count available actions
        const moveCount = this.board.grid.filter(t => t.can_be_moved_to).length;
        const attackCount = this.board.grid.filter(t => t.can_be_attacked).length;
        
        console.log(`Post-action check: ${moveCount} moves, ${attackCount} attacks available`);
        
        // If no actions available, deselect
        if (moveCount === 0 && attackCount === 0) {
            console.log('No actions available, deselecting unit');
            await this.rpc('unit_select', { 
                x: this.board.selected.x, 
                y: this.board.selected.y 
            });
        }
    }
    
    async showProduction(x, y) {
        try {
            const result = await this.rpc('get_production_options', { x, y });
            console.log('Production options result:', result);
            
            if (result && result.success && result.production_options && result.production_options.available_units) {
                const select = document.getElementById('unit-select');
                select.innerHTML = '';
                
                result.production_options.available_units.forEach(opt => {
                    const option = document.createElement('option');
                    option.value = opt.unit_type;
                    option.textContent = `${opt.unit_type} - ${opt.cost}G`;
                    if (!opt.can_afford) {
                        option.disabled = true;
                        option.textContent += ' (Not enough funds)';
                    }
                    select.appendChild(option);
                });
                
                this.productionCoords = { x, y };
                document.getElementById('modal').style.display = 'flex';
                console.log('Production modal should now be visible');
            } else {
                console.error('No production options available:', result);
            }
        } catch (e) {
            console.error('Failed to get production options:', e);
        }
    }
    
    render() {
        if (!this.board || !this.sprites) {
            return;
        }
        
        // Count units in different passes
        let unitsInPass3 = 0;
        
        // Set canvas size once
        const width = this.board.width * this.tileSize;
        const height = this.board.height * this.tileSize;
        
        if (this.canvas.width !== width || this.canvas.height !== height) {
            this.canvas.width = width;
            this.canvas.height = height;
            this.ctx.imageSmoothingEnabled = false;
        }
        
        // Clear and fill with plains color (more efficient than drawing tiles)
        // Using a more muted green that matches the actual plains tiles
        this.ctx.fillStyle = '#7CB068'; // Softer plains green
        this.ctx.fillRect(0, 0, width, height);
        
        // First pass: Draw non-tall terrain only
        for (let y = 0; y < this.board.height; y++) {
            for (let x = 0; x < this.board.width; x++) {
                const tile = this.board.grid[y * this.board.width + x];
                const px = x * this.tileSize;
                const py = y * this.tileSize;
                
                if (tile.mapTile) {
                    const tallTypes = ['CITY', 'FACTORY', 'AIRPORT', 'PORT', 'HQ', 'BASE_TOWER_0', 'BASE_TOWER_1', 'BASE_TOWER_2', 'BASE_TOWER_3', 'BASE_TOWER_4', 'MOUNTAIN', 'WOOD'];
                    
                    // Only draw non-tall terrain (including PLAIN and SEA)
                    if (!tallTypes.includes(tile.mapTile.type)) {
                        let spriteName = tile.mapTile.type;
                        
                        // Beach tiles are now correctly mapped
                        
                        if (tile.mapTile.army && tile.mapTile.army !== 'NEUTRAL') {
                            let army = tile.mapTile.army;
                            
                            // For v2 games, convert player ID to sprite color
                            if (this.spriteMapper && tile.mapTile.player_id !== undefined) {
                                army = this.spriteMapper.getSpriteColor(tile.mapTile.player_id);
                            }
                            
                            const armySprite = `${army}_${tile.mapTile.type}`;
                            if (this.sprites.terrain.data[armySprite]) {
                                spriteName = armySprite;
                            }
                        }
                        this.drawSprite('terrain', spriteName, px, py);
                    }
                }
            }
        }
        
        // Second pass: Draw tall terrain objects from top to bottom  
        // This allows lower tiles to properly overlap upper tiles
        for (let y = 0; y < this.board.height; y++) {
            for (let x = 0; x < this.board.width; x++) {
                const tile = this.board.grid[y * this.board.width + x];
                const px = x * this.tileSize;
                const py = y * this.tileSize;
                
                // Draw tall terrain objects
                if (tile.mapTile) {
                    const tallTypes = ['CITY', 'FACTORY', 'AIRPORT', 'PORT', 'HQ', 'BASE_TOWER_0', 'BASE_TOWER_1', 'BASE_TOWER_2', 'BASE_TOWER_3', 'BASE_TOWER_4', 'MOUNTAIN', 'WOOD'];
                    if (tallTypes.includes(tile.mapTile.type)) {
                        let spriteName = tile.mapTile.type;
                        
                        // Handle army buildings
                        if (tile.mapTile.army && tile.mapTile.army !== 'NEUTRAL') {
                            let army = tile.mapTile.army;
                            
                            // For v2 games, convert player ID to sprite color
                            if (this.spriteMapper && tile.mapTile.player_id !== undefined) {
                                army = this.spriteMapper.getSpriteColor(tile.mapTile.player_id);
                            }
                            
                            const armySprite = `${army}_${tile.mapTile.type}`;
                            if (this.sprites.terrain.data[armySprite]) {
                                spriteName = armySprite;
                            }
                        }
                        this.drawSprite('terrain', spriteName, px, py);
                    }
                }
            }
        }
        
        // Third pass: Draw highlights, units, and UI elements
        for (let y = 0; y < this.board.height; y++) {
            for (let x = 0; x < this.board.width; x++) {
                const tile = this.board.grid[y * this.board.width + x];
                const px = x * this.tileSize;
                const py = y * this.tileSize;
                
                // Draw highlights
                if (tile.can_be_moved_to) {
                    this.ctx.fillStyle = 'rgba(255, 255, 0, 0.3)';
                    this.ctx.fillRect(px, py, this.tileSize, this.tileSize);
                }
                
                if (tile.can_be_attacked) {
                    this.ctx.fillStyle = 'rgba(255, 0, 0, 0.3)';
                    this.ctx.fillRect(px, py, this.tileSize, this.tileSize);
                }
                
                // Draw unit
                if (tile.unit) {
                    unitsInPass3++;
                    
                    // Build sprite name - format is TYPE_ARMY_idle/unavailable_frame
                    let unitSprite;
                    
                    // For v2 games, use sprite mapper
                    if (this.spriteMapper && tile.unit.player_id !== undefined) {
                        const state = (tile.unit.has_moved || tile.unit.done) ? 'unavailable' : 'idle';
                        unitSprite = this.spriteMapper.buildUnitSprite(tile.unit, state);
                    } else {
                        // Legacy path for non-v2 games
                        unitSprite = `${tile.unit.type}_${tile.unit.army}`;
                        if (tile.unit.has_moved || tile.unit.done) {
                            unitSprite += '_unavailable';
                        } else {
                            unitSprite += '_idle';
                        }
                        unitSprite += '_0';
                    }
                    
                    this.drawSprite('units', unitSprite, px, py);
                    
                    // Draw HP - HP is in status object
                    if (tile.unit.status && tile.unit.status.hp < 100) {
                        const hp = Math.ceil(tile.unit.status.hp / 10);
                        const hpNum = hp === 10 ? 9 : hp; // Max is 9 in sprite sheet
                        
                        let army = tile.unit.army;
                        // For v2 games, get army from sprite mapping
                        if (this.spriteMapper && tile.unit.player_id !== undefined) {
                            const spriteColor = this.spriteMapper.getSpriteColor(tile.unit.player_id);
                            army = spriteColor; // Use sprite color as army name
                        }
                        
                        // Available units (can act) use neutral HP, unavailable use colored
                        const unitIsAvailable = !tile.unit.has_moved && !tile.unit.done && tile.unit.can_move;
                        const hpSprite = unitIsAvailable ? 
                            `hp_${hpNum}` :                              // Available: neutral HP
                            `hp_${army.toLowerCase()}_${hpNum}`;        // Unavailable: colored HP
                        this.drawSprite('ui', hpSprite, px + 16, py + 2);
                    }
                    
                    // Draw fuel/ammo warnings from spritesheet
                    if (tile.unit.status) {
                        const fuel = tile.unit.status.fuel;
                        const ammo = tile.unit.status.ammo;
                        
                        // Low fuel warning (bottom left)
                        if (fuel < 20) {
                            this.drawSprite('ui', 'fuel_warning', px + 2, py + 14);
                        }
                        
                        // Low ammo warning (bottom right)
                        if (ammo !== null && ammo !== undefined && ammo <= 1) {
                            this.drawSprite('ui', 'ammo_warning', px + 14, py + 14);
                        }
                    }
                }
            }
        }
        
        // Draw selection
        if (this.board.selected) {
            const px = this.board.selected.x * this.tileSize;
            const py = this.board.selected.y * this.tileSize;
            this.ctx.strokeStyle = '#FFD700';
            this.ctx.lineWidth = 3;
            this.ctx.strokeRect(px + 1.5, py + 1.5, this.tileSize - 3, this.tileSize - 3);
        }
        
        // Update UI
        document.getElementById('current-turn').textContent = this.board.current_turn || '-';
        document.getElementById('day').textContent = this.board.days || '-';
        
        // For v2 games with player funds
        if (this.board.player_funds) {
            // Assuming player 0 is RED, player 1 is BLUE for now
            document.getElementById('red-funds').textContent = this.board.player_funds['0'] || '-';
            document.getElementById('blue-funds').textContent = this.board.player_funds['1'] || '-';
        } else {
            // Legacy
            document.getElementById('red-funds').textContent = this.board.red_funds || '-';
            document.getElementById('blue-funds').textContent = this.board.blue_funds || '-';
        }
    }
    
    drawSprite(type, name, x, y) {
        const sprite = this.sprites[type].data[name];
        if (!sprite) {
            console.warn(`Sprite not found: ${type}/${name}`);
            return;
        }
        
        // For units and UI, don't adjust for tall sprites
        if (type === 'units' || type === 'ui') {
            this.ctx.drawImage(
                this.sprites[type].img,
                sprite.x, sprite.y, sprite.w, sprite.h,
                x, y, sprite.w, sprite.h
            );
        } else {
            // Handle tall sprites for terrain only
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
}

// Start game when page loads
window.addEventListener('DOMContentLoaded', () => {
    window.game = new Game();
});