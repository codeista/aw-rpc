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
                // Save current highlights
                const savedHighlights = {};
                if (this.board) {
                    this.board.grid.forEach((tile, idx) => {
                        if (tile.can_be_moved_to || tile.can_be_attacked) {
                            savedHighlights[idx] = {
                                can_be_moved_to: tile.can_be_moved_to,
                                can_be_attacked: tile.can_be_attacked
                            };
                        }
                    });
                }
                
                this.board = msg.board;
                
                // Restore highlights
                Object.entries(savedHighlights).forEach(([idx, highlights]) => {
                    const tile = this.board.grid[parseInt(idx)];
                    if (tile) {
                        tile.can_be_moved_to = highlights.can_be_moved_to;
                        tile.can_be_attacked = highlights.can_be_attacked;
                    }
                });
                
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
            
            // Simple click handling based on board state
            if (this.board && this.board.selected) {
                // Try move, then attack, then new selection
                try {
                    await this.rpc('movement_execute', {
                        from_x: this.board.selected.x,
                        from_y: this.board.selected.y,
                        to_x: x,
                        to_y: y
                    });
                } catch (e) {
                    try {
                        await this.rpc('combat_attack', {
                            attacker_x: this.board.selected.x,
                            attacker_y: this.board.selected.y,
                            defender_x: x,
                            defender_y: y
                        });
                    } catch (e) {
                        await this.rpc('unit_select', { x, y });
                    }
                }
            } else {
                await this.rpc('unit_select', { x, y });
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
                if (tile.mapTile.army === this.board.current_turn && !tile.unit) {
                    this.showProduction(x, y);
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
                    text += ` | ${tile.unit.type} HP:${tile.unit.hp}`;
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
                await this.rpc('unit_create', {
                    x: this.productionCoords.x,
                    y: this.productionCoords.y,
                    unit_type: select.value,
                    army: this.board.current_turn
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
            
            // Update board after RPC call UNLESS it's a query method
            const queryMethods = ['movement_range', 'combat_targets', 'get_production_options'];
            if (!queryMethods.includes(method)) {
                await this.updateBoard();
            }
            
            return data.result;
        } catch (e) {
            console.error('RPC error:', e);
            throw e;
        }
    }
    
    async updateBoard(preserveHighlights = false) {
        // Save current highlights if requested
        const savedHighlights = {};
        if (preserveHighlights && this.board) {
            this.board.grid.forEach((tile, idx) => {
                if (tile.can_be_moved_to || tile.can_be_attacked) {
                    savedHighlights[idx] = {
                        can_be_moved_to: tile.can_be_moved_to,
                        can_be_attacked: tile.can_be_attacked
                    };
                }
            });
        }
        
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
            
            // Restore highlights if requested
            if (preserveHighlights) {
                Object.entries(savedHighlights).forEach(([idx, highlights]) => {
                    const tile = this.board.grid[parseInt(idx)];
                    if (tile) {
                        tile.can_be_moved_to = highlights.can_be_moved_to;
                        tile.can_be_attacked = highlights.can_be_attacked;
                    }
                });
            }
            
            this.render();
            
            // If there's a selected unit, update movement highlights
            if (this.board.selected && this.board.selected.unit) {
                await this.updateMovementHighlights();
            }
        }
    }
    
    async updateMovementHighlights() {
        console.log('updateMovementHighlights called');
        
        // Only update highlights if a unit is selected
        if (!this.board || !this.board.selected || !this.board.selected.unit) {
            console.log('No unit selected, returning');
            return;
        }
        
        const unit = this.board.selected.unit;
        const x = this.board.selected.x;
        const y = this.board.selected.y;
        
        console.log(`Selected unit: ${unit.type} at (${x}, ${y})`);
        
        // Only get movement highlights for the current player's units
        if (unit.army !== this.board.current_turn) {
            console.log(`Unit army ${unit.army} != current turn ${this.board.current_turn}`);
            return;
        }
        
        try {
            // Get movement range from server
            const moveResult = await this.rpc('movement_range', { 
                unit_x: x, 
                unit_y: y 
            });
            
            console.log('Movement range result:', moveResult);
            
            if (moveResult.success && moveResult.positions) {
                console.log(`Setting ${moveResult.positions.length} movement highlights`);
                // Update can_be_moved_to flags
                moveResult.positions.forEach(pos => {
                    const tile = this.getTile(pos.x, pos.y);
                    if (tile) {
                        tile.can_be_moved_to = true;
                    }
                });
            }
            
            // Get attack targets
            const attackResult = await this.rpc('combat_targets', {
                unit_x: x,
                unit_y: y
            });
            
            console.log('Combat targets result:', attackResult);
            
            if (attackResult.success && attackResult.targets) {
                console.log(`Setting ${attackResult.targets.length} attack highlights`);
                // Update can_be_attacked flags
                attackResult.targets.forEach(target => {
                    const tile = this.getTile(target.x, target.y);
                    if (tile) {
                        tile.can_be_attacked = true;
                    }
                });
            }
            
            // Re-render to show highlights
            this.render();
        } catch (error) {
            console.error('Failed to update movement highlights:', error);
        }
    }
    
    getTile(x, y) {
        if (!this.board || x < 0 || y < 0 || x >= this.board.width || y >= this.board.height) {
            return null;
        }
        return this.board.grid[y * this.board.width + x];
    }
    
    async showProduction(x, y) {
        try {
            const options = await this.rpc('get_production_options', { x, y });
            if (options && options.length > 0) {
                const select = document.getElementById('unit-select');
                select.innerHTML = '';
                
                options.forEach(opt => {
                    const option = document.createElement('option');
                    option.value = opt.type;
                    option.textContent = `${opt.type} - ${opt.cost}G`;
                    select.appendChild(option);
                });
                
                this.productionCoords = { x, y };
                document.getElementById('modal').style.display = 'flex';
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
                            const armySprite = `${tile.mapTile.army}_${tile.mapTile.type}`;
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
                        if (tile.mapTile.army && tile.mapTile.army !== 'NEUTRAL') {
                            const armySprite = `${tile.mapTile.army}_${tile.mapTile.type}`;
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
                    // Note: 2x sprites use uppercase army names and 'idle' state
                    let unitSprite = `${tile.unit.type}_${tile.unit.army}`;
                    if (tile.unit.has_moved || tile.unit.done) {
                        unitSprite += '_unavailable';
                    } else {
                        unitSprite += '_idle';
                    }
                    unitSprite += '_0';
                    
                    this.drawSprite('units', unitSprite, px, py);
                    
                    // Draw HP
                    if (tile.unit.hp < 100) {
                        const hp = Math.ceil(tile.unit.hp / 10);
                        const hpNum = hp === 10 ? 9 : hp; // Max is 9 in sprite sheet
                        const hpSprite = tile.unit.has_moved || tile.unit.done ? 
                            `hp_${tile.unit.army.toLowerCase()}_${hpNum}` : 
                            `hp_${hpNum}`;
                        this.drawSprite('ui', hpSprite, px + 16, py + 2);
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
        document.getElementById('red-funds').textContent = this.board.red_funds || '-';
        document.getElementById('blue-funds').textContent = this.board.blue_funds || '-';
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