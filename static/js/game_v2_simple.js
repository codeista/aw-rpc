/**
 * Minimal Game Renderer
 * No legacy code, no complexity, just essentials
 */

// Debug flag - set to false for production
const DEBUG = false;

// Game constants
const CONSTANTS = {
    // Display
    TILE_SIZE: 32,
    SPRITE_SCALE: 2,
    
    // UI
    MODAL_WIDTH: 300,
    CONTEXT_MENU_WIDTH: 180,
    HP_BAR_WIDTH: 30,
    HP_BAR_HEIGHT: 4,
    
    // Game rules
    MAX_CARGO: 2,
    CAPTURE_HP: 20,
    CAPTURE_PROGRESS_PER_HP: 1,
    
    // Production facilities
    PRODUCTION_FACILITIES: ['FACTORY', 'AIRPORT', 'PORT'],
    
    // Transport types
    TRANSPORT_TYPES: ['APC', 'LANDER', 'TCOPTER', 'CRUISER', 'CARRIER', 'BLACKBOAT'],
    
    // Colors
    COLORS: {
        MOVEMENT_HIGHLIGHT: 'rgba(255, 255, 0, 0.3)',
        ATTACK_HIGHLIGHT: 'rgba(255, 0, 0, 0.3)',
        SELECTION_BORDER: '#ffff00',
        HP_BAR_BG: 'rgba(0, 0, 0, 0.5)',
        HP_BAR_FG: '#00ff00'
    }
};

// Utility functions
const log = (...args) => {
    if (DEBUG) console.log(...args);
};

const error = (...args) => {
    console.error(...args);
};

// Parse RPC response consistently
const parseRpcResponse = (result) => {
    if (!result) return { success: false, error: 'No result' };
    if (result.error) return { success: false, error: result.error };
    if (result.success === false) return { success: false, error: result.message || 'Unknown error' };
    return { success: true, data: result };
};

// Show/hide element utility
const setElementDisplay = (element, display) => {
    if (element) element.style.display = display;
};

const showElement = (element) => setElementDisplay(element, 'block');
const hideElement = (element) => setElementDisplay(element, 'none');
const showFlexElement = (element) => setElementDisplay(element, 'flex');

class Game {
    constructor() {
        // Cache DOM elements
        this.ui = {
            canvas: document.getElementById('game-canvas'),
            modal: document.getElementById('modal'),
            unitSelect: document.getElementById('unit-select'),
            contextMenu: document.getElementById('context-menu'),
            actionPrompt: document.getElementById('action-prompt'),
            turnDisplay: document.getElementById('turn-display'),
            fundsDisplay: document.getElementById('funds-display'),
            unitInfo: document.getElementById('unit-info-panel'),
            tileInfo: document.getElementById('tile-info-panel'),
            movementInfo: document.getElementById('movement-info-panel'),
            combatPreview: document.getElementById('combat-preview-panel')
        };
        
        this.canvas = this.ui.canvas;
        this.ctx = this.canvas.getContext('2d');
        this.tileSize = CONSTANTS.TILE_SIZE;
        
        // Game state
        this.board = null;
        this.sprites = null;
        this.socket = null;
        this.combatPreviewCache = null;
        this.hasHighlights = false;
        this.canvasInitialized = false;
        this.lastActedUnit = null;
        
        this.init();
    }
    
    updateActionPrompt(message) {
        const promptElement = document.getElementById('action-prompt');
        if (promptElement) {
            promptElement.textContent = message;
        }
    }
    
    async init() {
        // Load sprites first
        await this.loadSprites();
        
        // Setup socket connection
        this.setupSocket();
        
        // Setup input handlers
        this.setupInput();
        
        // Initialize context menu with all options
        this.restoreOriginalContextMenu();
        
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
            
            log('Sprites loaded');
        } catch (e) {
            console.error('Failed to load sprites:', e);
        }
    }
    
    setupSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            log('Connected');
            this.socket.emit('game', TOKEN);
        });
        
        this.socket.on('update', (msg) => {
            if (msg && msg.board) {
                this.board = msg.board;
                // Clear combat preview cache when board updates
                this.combatPreviewCache = null;
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
            
            log(`Click at (${x},${y}), selected:`, this.board?.selected);
            
            // Simple click handling based on board state
            if (this.board && this.board.selected) {
                // Check if clicking on same tile as selected - deselect
                if (this.board.selected.x === x && this.board.selected.y === y) {
                    await this.rpc('unit_select', { x, y });
                    return;
                }
                
                const clickedTile = this.getTile(x, y);
                
                // PRIORITY 1: Check if this is a valid movement destination
                // First check if highlights are set, otherwise try movement anyway for empty tiles
                const selectedUnit = this.getTile(this.board.selected.x, this.board.selected.y)?.unit;
                const canTryMove = selectedUnit && !selectedUnit.done && selectedUnit.can_move;
                const isEmptyTile = clickedTile && !clickedTile.unit;
                
                if (canTryMove && (clickedTile?.can_be_moved_to || isEmptyTile)) {
                    // This might be a valid move target - try movement
                    log('Attempting move to', x, y);
                    try {
                        const moveResult = await this.rpc('unit_move', {
                            x: this.board.selected.x,
                            y: this.board.selected.y,
                            x2: x,
                            y2: y
                        });
                        log('Move result:', moveResult);
                        
                        // After moving, check if unit can still attack
                        const movedTile = this.getTile(x, y);
                        if (movedTile && movedTile.unit && movedTile.unit.can_attack && !movedTile.unit.done) {
                            // For direct fire units that can attack after moving
                            if (!movedTile.unit.is_indirect || movedTile.unit.is_indirect === false) {
                                log('Unit can attack after move, showing attack range');
                                await this.showAttackRange(x, y);
                                this.updateActionPrompt('Select target to attack');
                            } else {
                                this.updateActionPrompt('Select action from menu');
                            }
                        } else {
                            this.updateActionPrompt('Unit moved');
                        }
                        
                        // Check if we need to show automatic context menu for multi-action scenarios
                        await this.checkForAutoContextMenu(x, y);
                        return; // Movement handled
                    } catch (moveError) {
                        log('Move failed:', moveError);
                        // Fall through to other options
                    }
                }
                
                // PRIORITY 2: Check if unit has already moved/acted
                const selectedTile = this.getTile(this.board.selected.x, this.board.selected.y);
                if (selectedTile?.unit) {
                    log('Selected unit state:', {
                        type: selectedTile.unit.type,
                        has_moved: selectedTile.unit.has_moved,
                        done: selectedTile.unit.done,
                        canAct: !selectedTile.unit.has_moved && !selectedTile.unit.done
                    });
                    
                    // Check various ways the unit might be marked as done
                    const hasMoved = selectedTile.unit.status?.has_moved_this_turn || selectedTile.unit.has_moved || false;
                    if (hasMoved === true || 
                        selectedTile.unit.done === true ||
                        selectedTile.unit.has_moved === 1 ||
                        selectedTile.unit.done === 1) {
                        log('Selected unit has already acted, handling as new click');
                        await this.handleFreshClick(x, y);
                        return;
                    }
                }
                
                // PRIORITY 3: Check if clicking on empty production building (ONLY if not a move target)
                if (clickedTile && !clickedTile.unit && clickedTile.mapTile && 
                    ['FACTORY', 'AIRPORT', 'PORT'].includes(clickedTile.mapTile.type) &&
                    !clickedTile.can_be_moved_to) {  // Only show production if NOT a valid move destination
                    // Check ownership
                    let isOwner = false;
                    if (this.board.current_player !== undefined) {
                        isOwner = clickedTile.mapTile.player_id === this.board.current_player;
                    } else {
                        isOwner = clickedTile.mapTile.army === this.board.current_turn;
                    }
                    
                    if (isOwner) {
                        log('Showing production for empty factory at', x, y);
                        this.showProduction(x, y);
                        return;
                    }
                }
                
                // PRIORITY 4: Try attack if clicking on enemy unit
                if (clickedTile && clickedTile.unit) {
                    // Check if it's an enemy unit
                    let isEnemy = false;
                    if (this.board.current_player !== undefined) {
                        isEnemy = clickedTile.unit.player_id !== this.board.current_player;
                    } else {
                        isEnemy = clickedTile.unit.army !== this.board.current_turn;
                    }
                    
                    if (isEnemy) {
                        log('Clicked on enemy unit, attempting direct attack');
                        try {
                            // First check if this is a valid target
                            const targetsResult = await this.rpc('combat_targets', { 
                                unit_x: this.board.selected.x, 
                                unit_y: this.board.selected.y 
                            });
                            
                            if (targetsResult.success && targetsResult.targets) {
                                const isValidTarget = targetsResult.targets.some(
                                    t => t.x === x && t.y === y
                                );
                                
                                if (isValidTarget) {
                                    log('Valid target confirmed, executing attack');
                                    const attackResult = await this.rpc('unit_attack_enhanced', {
                                        attacker_x: this.board.selected.x,
                                        attacker_y: this.board.selected.y,
                                        defender_x: x,
                                        defender_y: y
                                    });
                                    log('Attack result:', attackResult);
                                    return;
                                } else {
                                    log('Enemy is out of range');
                                    this.updateActionPrompt('Target out of range');
                                }
                            }
                        } catch (attackError) {
                            log('Attack failed:', attackError);
                        }
                    }
                }
                
                // If nothing else worked, handle as fresh click
                log('No valid action for click, handling as fresh click');
                await this.handleFreshClick(x, y);
            } else {
                await this.handleFreshClick(x, y);
            }
        });
        
        // Canvas double-click for capture
        this.canvas.addEventListener('dblclick', async (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = Math.floor((e.clientX - rect.left) / this.tileSize);
            const y = Math.floor((e.clientY - rect.top) / this.tileSize);
            
            const tile = this.getTile(x, y);
            
            // Check if there's a unit that can capture
            if (tile && tile.unit) {
                // Check if unit can capture (infantry/mech on capturable building)
                if ((tile.unit.type === 'INFANTRY' || tile.unit.type === 'MECH') &&
                    tile.mapTile && ['CITY', 'FACTORY', 'AIRPORT', 'PORT', 'HQ'].includes(tile.mapTile.type)) {
                    
                    // Check if building is enemy or neutral (not owned by current player)
                    let canCapture = false;
                    if (this.board.current_player !== undefined) {
                        canCapture = tile.mapTile.player_id !== this.board.current_player;
                    } else {
                        canCapture = tile.mapTile.army !== this.board.current_turn;
                    }
                    
                    if (canCapture) {
                        try {
                            log(`Double-click capture at (${x},${y})`);
                            await this.rpc('unit_capture', { x, y });
                        } catch (error) {
                            console.error('Capture failed:', error);
                        }
                    }
                }
            }
        });
        
        // Right click for context menu
        this.canvas.addEventListener('contextmenu', async (e) => {
            e.preventDefault();
            const rect = this.canvas.getBoundingClientRect();
            const x = Math.floor((e.clientX - rect.left) / this.tileSize);
            const y = Math.floor((e.clientY - rect.top) / this.tileSize);
            
            this.showContextMenu(e.clientX, e.clientY, x, y);
        });
        
        // Mouse move for tile info and combat preview
        let lastHoverTile = null;
        
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
                        // Only show ammo warning for units that can attack (have range > 0)
                        const canAttack = tile.unit.rangemax > 0 || (tile.unit.status.rangemax && tile.unit.status.rangemax > 0);
                        if (canAttack && ammo !== null && ammo <= 1) text += ' ⚠️LOW AMMO';
                    }
                    
                    // Check if this is a new tile to avoid repeated calls
                    const currentTileKey = `${x},${y}`;
                    if (lastHoverTile !== currentTileKey) {
                        lastHoverTile = currentTileKey;
                        
                        // Show combat preview if hovering over enemy unit with selected unit
                        if (tile.unit) {
                            log('Hover over unit, board.selected:', this.board?.selected);
                        }
                        
                        if (this.board?.selected && tile.unit) {
                            log(`Hover check: selected=(${this.board.selected.x},${this.board.selected.y}), hover=(${x},${y}), has unit:`, !!tile.unit);
                            
                            const selectedTile = this.getTile(this.board.selected.x, this.board.selected.y);
                            if (selectedTile?.unit) {
                                // Check if this is an enemy unit
                                let isEnemy = false;
                                if (this.board.current_player !== undefined) {
                                    isEnemy = tile.unit.player_id !== this.board.current_player;
                                    log(`Enemy check (v2): unit.player_id=${tile.unit.player_id}, current_player=${this.board.current_player}, isEnemy=${isEnemy}`);
                                } else {
                                    isEnemy = tile.unit.army !== this.board.current_turn;
                                    log(`Enemy check (v1): unit.army=${tile.unit.army}, current_turn=${this.board.current_turn}, isEnemy=${isEnemy}`);
                                }
                                
                                if (isEnemy) {
                                    // Check if we should show combat preview
                                    const selectedUnit = selectedTile.unit;
                                    const distance = Math.abs(x - this.board.selected.x) + Math.abs(y - this.board.selected.y);
                                    
                                    // For direct units, check if they could move into attack range
                                    if (selectedUnit.status && !this.isIndirectUnit(selectedUnit.type)) {
                                        // Direct unit - check if within movement + attack range
                                        // Direct units have attack range of 1
                                        const moveRange = selectedUnit.status.move || selectedUnit.move || 3;
                                        
                                        // Can attack if:
                                        // 1. Already adjacent (distance = 1)
                                        // 2. Can move to be adjacent (distance <= moveRange + 1)
                                        if (distance === 1 || (distance <= moveRange + 1 && !selectedUnit.has_moved)) {
                                            log(`Direct unit can reach target: distance=${distance}, moveRange=${moveRange}`);
                                            this.showCombatPreview(this.board.selected.x, this.board.selected.y, x, y);
                                        } else {
                                            log(`Direct unit cannot reach target: distance=${distance}, moveRange=${moveRange}`);
                                            this.hideCombatPreview();
                                        }
                                    } else if (selectedUnit.status && this.isIndirectUnit(selectedUnit.type)) {
                                        // Indirect unit - show preview if in range
                                        log('Indirect unit, showing preview if in range');
                                        this.showCombatPreview(this.board.selected.x, this.board.selected.y, x, y);
                                    } else {
                                        log('Unit type not recognized or no status');
                                        this.hideCombatPreview();
                                    }
                                } else {
                                    log('Not enemy, hiding preview');
                                    this.hideCombatPreview();
                                }
                            } else {
                                this.hideCombatPreview();
                            }
                        } else {
                            this.hideCombatPreview();
                        }
                    }
                } else {
                    lastHoverTile = null;
                    // Hide combat preview when not hovering over units
                    this.hideCombatPreview();
                }
                info.textContent = text;
            } else {
                lastHoverTile = null;
                info.textContent = '';
                this.hideCombatPreview();
            }
        });
        
        // End turn button
        document.getElementById('end-turn').addEventListener('click', async () => {
            await this.rpc('army_end_turn');
        });
        
        // Modal buttons
        const createBtn = document.getElementById('create');
        const cancelBtn = document.getElementById('cancel');
        
        if (createBtn && cancelBtn) {
            log('Attaching modal event handlers');
            
            createBtn.addEventListener('click', async () => {
                const select = document.getElementById('unit-select');
                const modal = document.getElementById('modal');
                
                if (this.productionCoords && select.value) {
                    log('Creating unit:', select.value, 'at', this.productionCoords);
                    const result = await this.rpc('unit_create', {
                        army: this.board.current_turn,
                        unit_type: select.value,
                        x: this.productionCoords.x,
                        y: this.productionCoords.y
                    });
                    log('Unit creation result:', result);
                    hideElement(modal);
                }
            });
            
            cancelBtn.addEventListener('click', () => {
                hideElement(this.ui.modal);
            });
        } else {
            console.error('Modal buttons not found! Create:', createBtn, 'Cancel:', cancelBtn);
        }
        
        // Help panel toggle
        const helpToggle = document.getElementById('help-toggle');
        const helpPanel = document.getElementById('help-panel');
        
        helpToggle.addEventListener('click', () => {
            helpPanel.classList.toggle('hidden');
            helpToggle.textContent = helpPanel.classList.contains('hidden') ? '? Help' : '✕ Close';
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', async (e) => {
            // Ignore if typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') {
                return;
            }
            
            switch(e.key) {
                case ' ':  // Space - End turn
                    e.preventDefault();
                    await this.rpc('army_end_turn');
                    break;
                    
                case 'Escape':  // Escape - Cancel action/close modal
                    e.preventDefault();
                    // Close production modal if open
                    if (this.ui.modal.style.display === 'flex') {
                        hideElement(this.ui.modal);
                    }
                    // Deselect unit if selected
                    else if (this.board && this.board.selected) {
                        await this.rpc('unit_select', { 
                            x: this.board.selected.x, 
                            y: this.board.selected.y 
                        });
                    }
                    break;
                    
                case 'Tab':  // Tab - Cycle through units
                    e.preventDefault();
                    await this.cycleUnits();
                    break;
                    
                case 'h':  // H - Toggle help
                case 'H':
                    e.preventDefault();
                    helpPanel.classList.toggle('hidden');
                    helpToggle.textContent = helpPanel.classList.contains('hidden') ? '? Help' : '✕ Close';
                    break;
            }
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
            
            // Track unit actions for turn mechanics
            const actionMethods = ['unit_move', 'unit_wait', 'unit_capture', 'unit_attack', 
                                 'unit_load', 'unit_unload', 'unit_resupply', 'unit_delete'];
            if (actionMethods.includes(method) && params.x !== undefined && params.y !== undefined) {
                this.lockPreviousUnit(params.x, params.y);
            }
            
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
    
    // Enhanced RPC with consistent error handling and response parsing
    async safeRpc(method, params = {}) {
        try {
            const result = await this.rpc(method, params);
            return parseRpcResponse(result);
        } catch (error) {
            this.showError(`${method} failed: ${error.message}`);
            return { success: false, error };
        }
    }
    
    showError(message) {
        // Show error in action prompt
        this.updateActionPrompt(`Error: ${message}`);
        error('Error:', message);
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
            // Check for turn change
            const previousTurn = this.board?.current_turn;
            this.board = data.result;
            
            // Reset last acted unit on turn change
            if (previousTurn && previousTurn !== this.board.current_turn) {
                this.lastActedUnit = null;
                log(`Turn changed from ${previousTurn} to ${this.board.current_turn}`);
            }
            
            // Debug log for selected unit
            if (this.board.selected) {
                log('Board updated with selected unit:', this.board.selected);
            }
            
            // Handle v2 games with player data
            if (this.board.players && this.board.sprite_mapping) {
                log('V2 game detected with players:', this.board.players);
                
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
        
        log(`handleFreshClick at (${x},${y}):`, {
            hasTile: !!tile,
            hasUnit: !!tile?.unit,
            unitType: tile?.unit?.type,
            hasMoved: tile?.unit?.has_moved,
            isDone: tile?.unit?.done
        });
        
        // First check if there's a unit to select
        if (tile && tile.unit) {
            log(`Selecting unit: ${tile.unit.type} at (${x},${y})`);
            await this.rpc('unit_select', { x, y });
            
            // Check if selection was successful
            log('After unit_select, board.selected:', this.board?.selected);
            
            // Show unit info and movement range for selected unit
            this.updateUnitInfoPanel(tile.unit);
            
            // Update action prompt based on unit state
            if (tile.unit.done) {
                this.updateActionPrompt('Unit has completed action');
            } else if (!tile.unit.has_moved) {
                this.updateActionPrompt('Select destination or action');
            } else if (tile.unit.can_attack && (!tile.unit.is_indirect || tile.unit.is_indirect === false)) {
                this.updateActionPrompt('Select target or action');
            } else {
                this.updateActionPrompt('Select action from menu');
            }
            
            // Show movement range if unit can move
            if (!tile.unit.has_moved && !tile.unit.done) {
                log(`Unit can move, showing movement range...`);
                await this.showMovementRange(x, y);
            } else {
                log(`Unit cannot move: has_moved=${tile.unit.has_moved}, done=${tile.unit.done}`);
            }
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
                log('Showing production for empty factory at', x, y);
                this.showProduction(x, y);
                return;
            } else {
                // Not owner or has unit, clear selection and panels
                log('Factory not available for production:', {owner: isOwner, hasUnit: !!tile.unit});
                this.clearUIPanels();
                await this.rpc('unit_select', { x, y });
            }
        }
        // Otherwise clear selection and panels
        else {
            this.clearUIPanels();
            await this.rpc('unit_select', { x, y });
        }
    }
    
    async checkPostActionSelection() {
        if (!this.board || !this.board.selected) return;
        
        // Count available actions
        const moveCount = this.board.grid.filter(t => t.can_be_moved_to).length;
        const attackCount = this.board.grid.filter(t => t.can_be_attacked).length;
        
        log(`Post-action check: ${moveCount} moves, ${attackCount} attacks available`);
        
        // If no actions available, deselect
        if (moveCount === 0 && attackCount === 0) {
            log('No actions available, deselecting unit');
            await this.rpc('unit_select', { 
                x: this.board.selected.x, 
                y: this.board.selected.y 
            });
        }
    }
    
    async showProduction(x, y) {
        try {
            const result = await this.rpc('get_production_options', { x, y });
            log('Production options result:', result);
            
            if (result && result.success && result.production_options && result.production_options.units) {
                const select = document.getElementById('unit-select');
                const modal = document.getElementById('modal');
                
                if (!select || !modal) {
                    console.error('Modal elements missing! Select:', select, 'Modal:', modal);
                    return;
                }
                
                select.innerHTML = '';
                
                log(`Loading ${result.production_options.units.length} units into production menu`);
                
                result.production_options.units.forEach(opt => {
                    const option = document.createElement('option');
                    option.value = opt.type;
                    option.textContent = `${opt.type} - ${opt.cost}G`;
                    if (!opt.can_afford) {
                        option.disabled = true;
                        option.textContent += ' (Not enough funds)';
                    }
                    select.appendChild(option);
                });
                
                this.productionCoords = { x, y };
                showFlexElement(modal);
                log('Production modal displayed');
            } else {
                console.error('No production options available:', result);
            }
        } catch (e) {
            console.error('Failed to get production options:', e);
        }
    }
    
    async cycleUnits() {
        if (!this.board) return;
        
        // Find all units that belong to current player and can still act
        const availableUnits = [];
        for (let y = 0; y < this.board.height; y++) {
            for (let x = 0; x < this.board.width; x++) {
                const tile = this.getTile(x, y);
                if (tile?.unit) {
                    // Check if unit belongs to current player
                    let isCurrentPlayer = false;
                    if (this.board.current_player !== undefined) {
                        isCurrentPlayer = tile.unit.player_id === this.board.current_player;
                    } else {
                        isCurrentPlayer = tile.unit.army === this.board.current_turn;
                    }
                    
                    // Check if unit can still act
                    if (isCurrentPlayer && !tile.unit.has_moved && !tile.unit.done) {
                        availableUnits.push({ x, y, unit: tile.unit });
                    }
                }
            }
        }
        
        if (availableUnits.length === 0) {
            log('No available units to cycle through');
            return;
        }
        
        // Find current selection index
        let currentIndex = -1;
        if (this.board.selected) {
            currentIndex = availableUnits.findIndex(
                u => u.x === this.board.selected.x && u.y === this.board.selected.y
            );
        }
        
        // Select next unit
        const nextIndex = (currentIndex + 1) % availableUnits.length;
        const nextUnit = availableUnits[nextIndex];
        
        log(`Cycling to unit at (${nextUnit.x}, ${nextUnit.y})`);
        await this.rpc('unit_select', { x: nextUnit.x, y: nextUnit.y });
    }
    
    showContextMenu(screenX, screenY, tileX, tileY) {
        const menu = document.getElementById('context-menu');
        const tile = this.getTile(tileX, tileY);
        
        // First ensure menu has content
        if (menu.innerHTML === '') {
            this.restoreOriginalContextMenu();
        }
        
        // Hide menu if clicking on empty tile
        if (!tile || !tile.unit) {
            // Check if it's a production building
            if (tile && tile.mapTile && ['FACTORY', 'AIRPORT', 'PORT'].includes(tile.mapTile.type)) {
                // Check ownership
                let isOwner = false;
                if (this.board.current_player !== undefined) {
                    isOwner = tile.mapTile.player_id === this.board.current_player;
                } else {
                    isOwner = tile.mapTile.army === this.board.current_turn;
                }
                
                if (isOwner && !tile.unit) {
                    this.showProduction(tileX, tileY);
                }
            }
            hideElement(menu);
            return;
        }
        
        // Store context menu target
        this.contextMenuTarget = { x: tileX, y: tileY };
        
        // Check if unit belongs to current player
        let isOwnUnit = false;
        if (this.board.current_player !== undefined) {
            isOwnUnit = tile.unit.player_id === this.board.current_player;
        } else {
            isOwnUnit = tile.unit.army === this.board.current_turn;
        }
        
        if (!isOwnUnit) {
            hideElement(menu);
            return;
        }
        
        // Configure menu items based on unit state and context
        const menuItems = menu.querySelectorAll('.menu-item');
        menuItems.forEach(item => {
            const action = item.dataset.action;
            item.disabled = false;
            showElement(item);
            
            switch(action) {
                case 'move':
                    // Move is available if unit hasn't moved yet
                    item.disabled = tile.unit.has_moved || tile.unit.done;
                    break;
                    
                case 'wait':
                    // Wait is always available if unit hasn't moved
                    item.disabled = tile.unit.has_moved || tile.unit.done;
                    break;
                    
                case 'capture':
                    // Only for infantry/mech on capturable buildings
                    if (!['INFANTRY', 'MECH'].includes(tile.unit.type)) {
                        hideElement(item);
                    } else if (!tile.mapTile || !['CITY', 'FACTORY', 'AIRPORT', 'PORT', 'HQ', 'BASE_TOWER_0', 'BASE_TOWER_1', 'BASE_TOWER_2', 'BASE_TOWER_3', 'BASE_TOWER_4'].includes(tile.mapTile.type)) {
                        item.disabled = true;
                    } else {
                        // Check if building belongs to enemy
                        let canCapture = false;
                        if (this.board.current_player !== undefined) {
                            canCapture = tile.mapTile.player_id !== this.board.current_player;
                        } else {
                            canCapture = tile.mapTile.army !== this.board.current_turn;
                        }
                        item.disabled = !canCapture || tile.unit.has_moved || tile.unit.done;
                    }
                    break;
                    
                case 'attack':
                    // Check if unit can attack and has valid targets
                    if (!tile.unit.can_attack || tile.unit.done) {
                        hideElement(item);
                        break;
                    }
                    
                    let hasAttackTargets = false;
                    
                    // For direct fire units, check adjacent tiles
                    if (!tile.unit.is_indirect || tile.unit.is_indirect === false) {
                        const offsets = [[0,-1], [1,0], [0,1], [-1,0]];
                        for (const [dx, dy] of offsets) {
                            const adjTile = this.getTile(tileX + dx, tileY + dy);
                            if (adjTile && adjTile.unit) {
                                // Check if it's an enemy
                                let isEnemy = false;
                                if (this.board.current_player !== undefined) {
                                    isEnemy = adjTile.unit.player_id !== this.board.current_player;
                                } else {
                                    isEnemy = adjTile.unit.army !== this.board.current_turn;
                                }
                                if (isEnemy) {
                                    hasAttackTargets = true;
                                    break;
                                }
                            }
                        }
                    } else {
                        // For indirect units, they can only attack if they haven't moved
                        if (!tile.unit.has_moved) {
                            // Quick check - just see if there are any enemies on the board
                            // The actual range check will be done when attack is selected
                            for (let gridTile of this.board.grid) {
                                if (gridTile.unit) {
                                    let isEnemy = false;
                                    if (this.board.current_player !== undefined) {
                                        isEnemy = gridTile.unit.player_id !== this.board.current_player;
                                    } else {
                                        isEnemy = gridTile.unit.army !== this.board.current_turn;
                                    }
                                    if (isEnemy) {
                                        hasAttackTargets = true;
                                        break;
                                    }
                                }
                            }
                        }
                    }
                    
                    if (!hasAttackTargets) {
                        hideElement(item);
                    }
                    break;
                    
                case 'load':
                    // Check if there's a transport adjacent
                    const hasAdjacentTransport = this.checkAdjacentTransport(tileX, tileY);
                    item.disabled = !hasAdjacentTransport || tile.unit.has_moved || tile.unit.done;
                    // Hide for transports themselves
                    if (['APC', 'LANDER', 'CRUISER', 'T_COPTER', 'BLACK_BOAT'].includes(tile.unit.type)) {
                        hideElement(item);
                    }
                    break;
                    
                case 'unload':
                    // Only for transports with units
                    const transportTypes = ['APC', 'LANDER', 'CRUISER', 'T_COPTER', 'BLACK_BOAT'];
                    if (!transportTypes.includes(tile.unit.type)) {
                        hideElement(item);
                    } else {
                        // Check if transport has units (would need API call to verify)
                        item.disabled = tile.unit.has_moved || tile.unit.done;
                    }
                    break;
                    
                case 'repair':
                    // Only for APC/Black Boat
                    if (!['APC', 'BLACK_BOAT'].includes(tile.unit.type)) {
                        hideElement(item);
                    } else {
                        item.disabled = tile.unit.has_moved || tile.unit.done;
                    }
                    break;
                    
                case 'delete':
                    // Always available for own units
                    item.disabled = false;
                    break;
            }
        });
        
        // Position menu
        menu.style.left = `${screenX}px`;
        menu.style.top = `${screenY}px`;
        showElement(menu);
        
        // Add click handlers
        this.setupContextMenuHandlers();
    }
    
    checkAdjacentTransport(x, y) {
        const offsets = [[0,-1], [1,0], [0,1], [-1,0]];
        for (const [dx, dy] of offsets) {
            const nx = x + dx;
            const ny = y + dy;
            const tile = this.getTile(nx, ny);
            if (tile?.unit) {
                // Check if it's a friendly transport
                let isFriendly = false;
                if (this.board.current_player !== undefined) {
                    isFriendly = tile.unit.player_id === this.board.current_player;
                } else {
                    isFriendly = tile.unit.army === this.board.current_turn;
                }
                
                if (isFriendly && ['APC', 'LANDER', 'CRUISER', 'T_COPTER', 'BLACK_BOAT'].includes(tile.unit.type)) {
                    return true;
                }
            }
        }
        return false;
    }
    
    setupContextMenuHandlers() {
        const menu = document.getElementById('context-menu');
        const menuItems = menu.querySelectorAll('.menu-item');
        
        // Remove old handlers
        menuItems.forEach(item => {
            item.replaceWith(item.cloneNode(true));
        });
        
        // Add new handlers
        menu.querySelectorAll('.menu-item').forEach(item => {
            item.addEventListener('click', async () => {
                const action = item.dataset.action;
                hideElement(menu);
                
                if (!this.contextMenuTarget) return;
                
                const x = this.contextMenuTarget.x;
                const y = this.contextMenuTarget.y;
                
                switch(action) {
                    case 'move':
                        // Select unit and show movement highlights (same as left-click)
                        await this.handleTileClick(x, y);
                        break;
                        
                    case 'wait':
                        await this.rpc('unit_wait', { x, y });
                        this.hideContextMenu();  // Close menu after wait
                        break;
                        
                    case 'capture':
                        await this.rpc('unit_capture', { x, y });
                        break;
                        
                    case 'attack':
                        await this.handleAttackFromContextMenu(x, y);
                        break;
                        
                    case 'load':
                        // Show available transports to load into
                        this.showLoadOptions(x, y);
                        break;
                        
                    case 'unload':
                        // For now, just mark unit as done
                        // Full unload UI would need direction selection
                        await this.rpc('unit_wait', { x, y });
                        break;
                        
                    case 'repair':
                        await this.rpc('unit_resupply', { x, y });
                        break;
                        
                    case 'delete':
                        await this.handleDeleteUnit(x, y);
                        break;
                        
                    case 'cancel':
                        // Clear selection and highlights
                        this.board.selected = null;
                        this.clearHighlights();
                        this.render();
                        break;
                }
            });
        });
        
        // Hide menu when clicking elsewhere
        document.addEventListener('click', (e) => {
            if (!menu.contains(e.target) && e.target !== menu) {
                hideElement(menu);
            }
        }, { once: true });
    }
    
    render() {
        if (!this.board || !this.sprites) {
            return;
        }
        
        this.setupCanvas();
        this.clearCanvas();
        
        // Three-pass rendering for proper layering
        this.renderTerrainBase();      // Pass 1: Non-tall terrain
        this.renderTerrainTall();      // Pass 2: Tall terrain (buildings, forests)
        this.renderUnitsAndUI();       // Pass 3: Units, highlights, UI
        this.renderSelection();        // Selection box
        
        // Update panels
        this.updateGameStatusPanel();
        this.updatePlayerStatsPanel();
    }
    
    setupCanvas() {
        const width = this.board.width * this.tileSize;
        const height = this.board.height * this.tileSize;
        
        // Only resize canvas if dimensions actually changed
        if (!this.canvasInitialized || this.canvas.width !== width || this.canvas.height !== height) {
            this.canvas.width = width;
            this.canvas.height = height;
            this.ctx.imageSmoothingEnabled = false;
            this.canvasInitialized = true;
            log(`Canvas resized to ${width}x${height}`);
        }
    }
    
    clearCanvas() {
        const width = this.board.width * this.tileSize;
        const height = this.board.height * this.tileSize;
        
        // Clear and fill with plains color (more efficient than drawing tiles)
        this.ctx.fillStyle = '#7CB068'; // Softer plains green
        this.ctx.fillRect(0, 0, width, height);
    }
    
    renderTerrainBase() {
        const tallTypes = ['CITY', 'FACTORY', 'AIRPORT', 'PORT', 'HQ', 'BASE_TOWER_0', 'BASE_TOWER_1', 'BASE_TOWER_2', 'BASE_TOWER_3', 'BASE_TOWER_4', 'MOUNTAIN', 'WOOD'];
        
        // First pass: Draw non-tall terrain only
        for (let y = 0; y < this.board.height; y++) {
            for (let x = 0; x < this.board.width; x++) {
                const tile = this.board.grid[y * this.board.width + x];
                const px = x * this.tileSize;
                const py = y * this.tileSize;
                
                if (tile.mapTile && !tallTypes.includes(tile.mapTile.type)) {
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
    
    renderTerrainTall() {
        const tallTypes = ['CITY', 'FACTORY', 'AIRPORT', 'PORT', 'HQ', 'BASE_TOWER_0', 'BASE_TOWER_1', 'BASE_TOWER_2', 'BASE_TOWER_3', 'BASE_TOWER_4', 'MOUNTAIN', 'WOOD'];
        
        // Second pass: Draw tall terrain objects from top to bottom  
        // This allows lower tiles to properly overlap upper tiles
        for (let y = 0; y < this.board.height; y++) {
            for (let x = 0; x < this.board.width; x++) {
                const tile = this.board.grid[y * this.board.width + x];
                const px = x * this.tileSize;
                const py = y * this.tileSize;
                
                // Draw tall terrain objects
                if (tile.mapTile && tallTypes.includes(tile.mapTile.type)) {
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
    
    renderUnitsAndUI() {
        // Third pass: Draw highlights, units, and UI elements
        for (let y = 0; y < this.board.height; y++) {
            for (let x = 0; x < this.board.width; x++) {
                const tile = this.board.grid[y * this.board.width + x];
                const px = x * this.tileSize;
                const py = y * this.tileSize;
                
                // Draw highlights
                this.renderTileHighlight(tile, px, py);
                
                // Draw unit
                if (tile.unit) {
                    this.renderUnit(tile, px, py);
                }
            }
        }
    }
    
    renderTileHighlight(tile, px, py) {
        if (tile.can_be_moved_to) {
            this.ctx.fillStyle = CONSTANTS.COLORS.MOVEMENT_HIGHLIGHT;
            this.ctx.fillRect(px, py, this.tileSize, this.tileSize);
        }
        
        if (tile.can_be_attacked) {
            this.ctx.fillStyle = CONSTANTS.COLORS.ATTACK_HIGHLIGHT;
            this.ctx.fillRect(px, py, this.tileSize, this.tileSize);
        }
    }
    
    renderUnit(tile, px, py) {
        // Build sprite name - format is TYPE_ARMY_idle/unavailable_frame
        let unitSprite;
        
        // A unit is unavailable if:
        // 1. It belongs to another player (enemy)
        // 2. It has no actions left (can't move, attack, or capture)
        // 3. It's explicitly marked as done
        const isEnemy = this.board.current_player !== undefined ? 
            tile.unit.player_id !== this.board.current_player :
            tile.unit.army !== this.board.current_turn;
        
        // A unit has no actions if it can't move, attack, or capture
        const hasNoActions = !tile.unit.can_move && !tile.unit.can_attack && !tile.unit.can_capture;
        const isDone = tile.unit.done || false;
        const isUnavailable = isEnemy || hasNoActions || isDone;
        
        // Debug newly created units
        if (tile.x === 0 && tile.y === 4 && tile.unit) {
            log('Unit state debug at factory:', {
                type: tile.unit.type,
                can_move: tile.unit.can_move,
                can_attack: tile.unit.can_attack,
                can_capture: tile.unit.can_capture,
                done: tile.unit.done,
                hasNoActions,
                isUnavailable,
                sprite: isUnavailable ? 'unavailable' : 'idle'
            });
        }
        
        // For v2 games, use sprite mapper
        if (this.spriteMapper && tile.unit.player_id !== undefined) {
            const state = isUnavailable ? 'unavailable' : 'idle';
            unitSprite = this.spriteMapper.buildUnitSprite(tile.unit, state);
        } else {
            // Legacy path for non-v2 games
            unitSprite = `${tile.unit.type}_${tile.unit.army}`;
            if (isUnavailable) {
                unitSprite += '_unavailable';
            } else {
                unitSprite += '_idle';
            }
            unitSprite += '_0';
        }
        
        this.drawSprite('units', unitSprite, px, py);
        
        // Draw HP or status icon
        if (tile.unit.status) {
            let army = tile.unit.army;
            // For v2 games, get army from sprite mapping
            if (this.spriteMapper && tile.unit.player_id !== undefined) {
                const spriteColor = this.spriteMapper.getSpriteColor(tile.unit.player_id);
                army = spriteColor; // Use sprite color as army name
            }
            
            const armyLower = army.toLowerCase();
            // Unit is available if it belongs to current player and has actions left
            const isOwnUnit = this.board.current_player !== undefined ? 
                tile.unit.player_id === this.board.current_player :
                tile.unit.army === this.board.current_turn;
            const hasActions = tile.unit.can_move || tile.unit.can_attack || tile.unit.can_capture;
            const isDone = tile.unit.done || false;
            const unitIsAvailable = isOwnUnit && hasActions && !isDone;
            let statusSprite = null;
            
            // Check for special status conditions
            // 1. Check if unit is capturing (tile has capture_hp < 20)
            if (tile.capture_hp !== undefined && tile.capture_hp < 20) {
                // Show capturing icon - use available or unavailable version
                statusSprite = unitIsAvailable ? 
                    `status_${armyLower}_capturing` :
                    `hp_${armyLower}_capturing`;
            }
            // 2. TODO: Check for submerged submarines
            // else if (tile.unit.type === 'SUB' && tile.unit.is_submerged) {
            //     statusSprite = unitIsAvailable ?
            //         `status_${armyLower}_submerged` :
            //         `hp_${armyLower}_submerged`;
            // }
            // 3. TODO: Check for loaded units (though they're usually off-map)
            
            // If unit has special status, show status icon
            if (statusSprite && this.sprites.ui.data[statusSprite]) {
                this.drawSprite('ui', statusSprite, px + 16, py + 2);
            } 
            // Otherwise show HP if damaged
            else if (tile.unit.status.hp < 100) {
                const hp = Math.ceil(tile.unit.status.hp / 10);
                const hpNum = hp === 10 ? 9 : hp; // Max is 9 in sprite sheet
                
                // Available units use white HP numbers, unavailable use colored
                const hpSprite = unitIsAvailable ? 
                    `hp_${hpNum}` :
                    `hp_${armyLower}_${hpNum}`;
                this.drawSprite('ui', hpSprite, px + 16, py + 2);
            }
            
            // Draw fuel/ammo warnings from spritesheet
            const fuel = tile.unit.status.fuel;
            const ammo = tile.unit.status.ammo;
            
            // Low fuel warning (bottom left)
            if (fuel < 20) {
                this.drawSprite('ui', 'fuel_warning', px + 2, py + 14);
            }
            
            // Low ammo warning (bottom right) - only for units that can attack
            const canAttack = tile.unit.rangemax > 0 || (tile.unit.status.rangemax && tile.unit.status.rangemax > 0);
            if (canAttack && ammo !== null && ammo !== undefined && ammo <= 1) {
                this.drawSprite('ui', 'ammo_warning', px + 14, py + 14);
            }
        }
    }
    
    renderSelection() {
        if (!this.board.selected) return;
        
        const px = this.board.selected.x * this.tileSize;
        const py = this.board.selected.y * this.tileSize;
        this.ctx.strokeStyle = CONSTANTS.COLORS.SELECTION_BORDER;
        this.ctx.lineWidth = 3;
        this.ctx.strokeRect(px + 1.5, py + 1.5, this.tileSize - 3, this.tileSize - 3);
        
        // Update UI displays
        this.updateUIDisplays();
    }
    
    updateUIDisplays() {
        document.getElementById('current-turn').textContent = this.board.current_turn || '-';
        
        // Days can be 0 at game start, display as 1
        const displayDay = this.board.days === 0 ? 1 : (this.board.days || 1);
        document.getElementById('day').textContent = `Day ${displayDay}`;
        
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
        
        // Update map name if available
        if (this.board.map_name) {
            const mapNameElement = document.getElementById('map-name');
            if (mapNameElement) {
                mapNameElement.textContent = this.board.map_name;
            }
        }
        
        // Update game status panel
        this.updateGameStatusPanel();
        
        // Update player statistics
        this.updatePlayerStatsPanel();
        
        // Update browser title
        const turn = this.board.current_turn || 'Loading';
        const titleDay = this.board.days === 0 ? 1 : (this.board.days || 1);
        if (this.board.game_active) {
            document.title = `Advance Wars RPC - Day ${titleDay} - ${turn}'s Turn`;
        } else {
            // Check for winner
            if (this.board.winner) {
                document.title = `Advance Wars RPC - ${this.board.winner} Victory!`;
            } else {
                document.title = 'Advance Wars RPC - Game Over';
            }
        }
    }
    
    async showMovementRange(x, y) {
        try {
            const result = await this.rpc('movement_range', { unit_x: x, unit_y: y });
            if (result.success) {
                // Clear previous highlights
                this.clearHighlights();
                
                // Highlight movement range
                result.moves.forEach(move => {
                    const tile = this.getTile(move.x, move.y);
                    if (tile) {
                        tile.can_be_moved_to = true;
                        this.hasHighlights = true;
                    }
                });
                
                // Update movement info panel
                this.updateMovementInfoPanel(result);
                
                // Get attack targets for this unit
                this.showAttackRange(x, y);
                
                this.render();
            }
        } catch (e) {
            console.error('Failed to get movement range:', e);
        }
    }
    
    async showAttackRange(x, y) {
        try {
            log(`showAttackRange called for unit at (${x},${y})`);
            const result = await this.rpc('combat_targets', { unit_x: x, unit_y: y });
            log(`combat_targets result:`, result);
            
            if (result.success) {
                // Clear previous attack highlights first
                if (this.board && this.board.grid) {
                    this.board.grid.forEach(tile => {
                        tile.can_be_attacked = false;
                    });
                }
                
                // Highlight attack targets
                log(`Setting ${result.targets.length} attack targets:`);
                result.targets.forEach(target => {
                    const tile = this.getTile(target.x, target.y);
                    if (tile) {
                        log(`  - Target at (${target.x},${target.y}): ${tile.unit?.type || 'no unit'}`);
                        tile.can_be_attacked = true;
                        this.hasHighlights = true;
                    }
                });
                this.render();
            }
        } catch (e) {
            console.error('Failed to get attack range:', e);
        }
    }
    
    clearHighlights() {
        if (!this.board) return;
        
        let hadHighlights = false;
        for (let tile of this.board.grid) {
            if (tile.can_be_moved_to || tile.can_be_attacked) {
                hadHighlights = true;
            }
            tile.can_be_moved_to = false;
            tile.can_be_attacked = false;
        }
        
        // Update action prompt when clearing highlights
        this.updateActionPrompt('Select a unit');
        this.hasHighlights = hadHighlights;
    }
    
    updateUnitInfoPanel(unit) {
        const panel = document.getElementById('unit-info-panel');
        if (!unit) {
            panel.style.display = 'none';
            return;
        }
        
        panel.style.display = 'block';
        
        document.getElementById('unit-type').textContent = unit.type;
        document.getElementById('unit-hp').textContent = unit.status?.hp || '100';
        document.getElementById('unit-fuel').textContent = unit.status?.fuel || '0';
        document.getElementById('unit-ammo').textContent = unit.status?.ammo || 'N/A';
        document.getElementById('unit-move').textContent = unit.status?.move || '0';
        
        const rangeMin = unit.status?.rangemin || 1;
        const rangeMax = unit.status?.rangemax || 1;
        const rangeText = rangeMin === rangeMax ? rangeMin : `${rangeMin}-${rangeMax}`;
        document.getElementById('unit-range').textContent = rangeText;
        
        document.getElementById('unit-vision').textContent = unit.status?.vision || '0';
    }
    
    updateMovementInfoPanel(movementData) {
        const panel = document.getElementById('movement-info-panel');
        if (!movementData) {
            panel.style.display = 'none';
            return;
        }
        
        panel.style.display = 'block';
        
        document.getElementById('movement-count').textContent = movementData.moves?.length || 0;
        document.getElementById('movement-can-attack').textContent = movementData.can_attack ? 'Yes' : 'No';
        
        let status = 'Ready';
        if (movementData.has_moved) status = 'Moved';
        if (movementData.done) status = 'Done';
        document.getElementById('movement-status').textContent = status;
    }
    
    async showCombatPreview(attackerX, attackerY, defenderX, defenderY) {
        // Determine if we need to skip range check
        const selectedTile = this.getTile(attackerX, attackerY);
        const distance = Math.abs(defenderX - attackerX) + Math.abs(defenderY - attackerY);
        const isDirectUnit = selectedTile?.unit && !this.isIndirectUnit(selectedTile.unit.type);
        const skipRangeCheck = isDirectUnit && distance > 1;
        
        // Create cache key including skip_range_check
        const cacheKey = `${attackerX},${attackerY}->${defenderX},${defenderY}:${skipRangeCheck}`;
        
        log(`Combat preview requested: ${cacheKey}`);
        
        // Check if we already have this preview cached
        if (this.combatPreviewCache && this.combatPreviewCache.key === cacheKey) {
            log('Using cached preview');
            this.updateCombatPreviewPanel(this.combatPreviewCache.data);
            return;
        }
        
        try {
            const result = await this.rpc('combat_preview', {
                attacker_x: attackerX,
                attacker_y: attackerY,
                defender_x: defenderX,
                defender_y: defenderY,
                skip_range_check: skipRangeCheck
            });
            
            log('Combat preview result:', result);
            
            if (result.success) {
                // Cache the result
                this.combatPreviewCache = { key: cacheKey, data: result };
                this.updateCombatPreviewPanel(result);
            } else if (result.error === "Target is out of range") {
                // Show a simplified preview for out-of-range targets
                log('Target out of range, showing info preview');
                this.showOutOfRangePreview(defenderX, defenderY);
            } else {
                log('Combat preview failed:', result);
                this.hideCombatPreview();
            }
        } catch (e) {
            console.error('Combat preview error:', e);
            this.hideCombatPreview();
        }
    }
    
    updateCombatPreviewPanel(preview) {
        const panel = document.getElementById('combat-preview-panel');
        log('updateCombatPreviewPanel called, panel exists:', !!panel);
        
        if (!preview || !preview.success) {
            log('Preview invalid or unsuccessful:', preview);
            if (panel) panel.style.display = 'none';
            return;
        }
        
        if (!panel) {
            console.error('Combat preview panel element not found!');
            return;
        }
        
        log('Setting panel to visible');
        panel.style.display = 'block';
        
        const targetUnit = preview.defender?.type || 'Unknown';
        document.getElementById('combat-target').textContent = targetUnit;
        
        const damage = preview.damage?.attacker_damage || 0;
        const damageRange = preview.damage?.attacker_damage_range;
        let damageText = `${damage}%`;
        if (damageRange) {
            damageText = `${damageRange.min}-${damageRange.max}%`;
        }
        document.getElementById('combat-damage').textContent = damageText;
        
        const counterDamage = preview.damage?.counter_damage || 0;
        const counterRange = preview.damage?.counter_damage_range;
        let counterText = preview.damage?.can_counter ? `${counterDamage}%` : 'None';
        if (counterRange && preview.damage?.can_counter) {
            counterText = `${counterRange.min}-${counterRange.max}%`;
        }
        document.getElementById('combat-counter').textContent = counterText;
        
        const terrainDefense = preview.defender?.terrain_defense || 0;
        document.getElementById('combat-terrain').textContent = `${terrainDefense} stars`;
        
        let result = 'Even';
        if (damage > counterDamage + 10) result = 'Favorable';
        if (counterDamage > damage + 10) result = 'Unfavorable';
        if (!preview.damage?.can_counter) result = 'Safe';
        document.getElementById('combat-result').textContent = result;
    }
    
    hideCombatPreview() {
        document.getElementById('combat-preview-panel').style.display = 'none';
    }
    
    showOutOfRangePreview(targetX, targetY) {
        const panel = document.getElementById('combat-preview-panel');
        if (!panel) return;
        
        const tile = this.getTile(targetX, targetY);
        if (!tile || !tile.unit) return;
        
        panel.style.display = 'block';
        
        // Show target info
        document.getElementById('combat-target').textContent = tile.unit.type;
        document.getElementById('combat-damage').textContent = 'Out of range';
        document.getElementById('combat-counter').textContent = 'N/A';
        
        // Show terrain defense
        const terrainDefense = tile.mapTile?.defense || 0;
        document.getElementById('combat-terrain').textContent = `${terrainDefense} stars`;
        
        document.getElementById('combat-result').textContent = 'Cannot attack';
    }
    
    async checkForAutoContextMenu(x, y) {
        const tile = this.getTile(x, y);
        if (!tile || !tile.unit) return;
        
        // Check if unit belongs to current player
        let isOwnUnit = false;
        if (this.board.current_player !== undefined) {
            isOwnUnit = tile.unit.player_id === this.board.current_player;
        } else {
            isOwnUnit = tile.unit.army === this.board.current_turn;
        }
        
        if (!isOwnUnit) return;
        
        // Count available high-priority actions
        let availableActions = [];
        
        // Check if can capture
        if (['INFANTRY', 'MECH'].includes(tile.unit.type) &&
            tile.mapTile && ['CITY', 'FACTORY', 'AIRPORT', 'PORT', 'HQ', 'BASE_TOWER_0', 'BASE_TOWER_1', 'BASE_TOWER_2', 'BASE_TOWER_3', 'BASE_TOWER_4'].includes(tile.mapTile.type)) {
            
            // Check if building belongs to enemy or neutral
            let canCapture = false;
            if (this.board.current_player !== undefined) {
                canCapture = tile.mapTile.player_id !== this.board.current_player;
            } else {
                canCapture = tile.mapTile.army !== this.board.current_turn;
            }
            
            if (canCapture && !tile.unit.has_moved && !tile.unit.done) {
                availableActions.push('capture');
            }
        }
        
        // Check if can attack - dynamically check for enemies in range
        let hasAttackTargets = false;
        if (tile.unit.can_attack && !tile.unit.done) {
            // For direct fire units, check adjacent tiles
            if (!tile.unit.is_indirect || tile.unit.is_indirect === false) {
                const offsets = [[0,-1], [1,0], [0,1], [-1,0]];
                for (const [dx, dy] of offsets) {
                    const adjTile = this.getTile(x + dx, y + dy);
                    if (adjTile && adjTile.unit) {
                        // Check if it's an enemy
                        let isEnemy = false;
                        if (this.board.current_player !== undefined) {
                            isEnemy = adjTile.unit.player_id !== this.board.current_player;
                        } else {
                            isEnemy = adjTile.unit.army !== this.board.current_turn;
                        }
                        if (isEnemy) {
                            hasAttackTargets = true;
                            break;
                        }
                    }
                }
            } else {
                // For indirect units, they can only attack if they haven't moved
                if (!tile.unit.has_moved) {
                    // Check for enemies within range
                    const rangeMin = tile.unit.status?.rangemin || 2;
                    const rangeMax = tile.unit.status?.rangemax || 3;
                    
                    for (let dy = -rangeMax; dy <= rangeMax; dy++) {
                        for (let dx = -rangeMax; dx <= rangeMax; dx++) {
                            const dist = Math.abs(dx) + Math.abs(dy);
                            if (dist >= rangeMin && dist <= rangeMax) {
                                const targetTile = this.getTile(x + dx, y + dy);
                                if (targetTile && targetTile.unit) {
                                    let isEnemy = false;
                                    if (this.board.current_player !== undefined) {
                                        isEnemy = targetTile.unit.player_id !== this.board.current_player;
                                    } else {
                                        isEnemy = targetTile.unit.army !== this.board.current_turn;
                                    }
                                    if (isEnemy) {
                                        hasAttackTargets = true;
                                        break;
                                    }
                                }
                            }
                        }
                        if (hasAttackTargets) break;
                    }
                }
            }
        }
        if (hasAttackTargets) {
            availableActions.push('attack');
        }
        
        // Check if can load into transport
        const hasAdjacentTransport = this.checkAdjacentTransport(x, y);
        if (hasAdjacentTransport && !tile.unit.has_moved && !tile.unit.done &&
            !['APC', 'LANDER', 'CRUISER', 'T_COPTER', 'BLACK_BOAT'].includes(tile.unit.type)) {
            availableActions.push('load');
        }
        
        // Show automatic context menu if multiple high-priority actions available
        if (availableActions.length >= 2) {
            log(`Auto-showing context menu for actions: ${availableActions.join(', ')}`);
            
            // Calculate screen position for context menu (center of tile)
            const rect = this.canvas.getBoundingClientRect();
            const screenX = rect.left + (x * this.tileSize) + (this.tileSize / 2);
            const screenY = rect.top + (y * this.tileSize) + (this.tileSize / 2);
            
            // Small delay to ensure board state is updated
            setTimeout(() => {
                this.showContextMenu(screenX, screenY, x, y);
            }, 100);
        }
    }
    
    async handleAttackFromContextMenu(x, y) {
        // Fetch valid attack targets from server to ensure we have fresh data
        log(`Fetching attack targets for unit at (${x},${y})`);
        
        try {
            const result = await this.rpc('combat_targets', { unit_x: x, unit_y: y });
            
            if (!result.success || !result.targets || result.targets.length === 0) {
                log('No valid attack targets found');
                return;
            }
            
            // Convert server response to our attack target format
            const attackTargets = result.targets.map(target => ({
                x: target.x,
                y: target.y,
                unit: target.unit
            }));
            
            log(`Found ${attackTargets.length} attack targets from server`);
            
            if (attackTargets.length === 1) {
                // Only one target, attack it directly
                const target = attackTargets[0];
                log(`Attacking ${target.unit.type} at (${target.x},${target.y})`);
                try {
                    await this.rpc('unit_attack_enhanced', {
                        attacker_x: x,
                        attacker_y: y,
                        defender_x: target.x,
                        defender_y: target.y
                    });
                } catch (error) {
                    console.error('Attack failed:', error);
                }
            } else {
                // Multiple targets - show selection
                log(`Multiple attack targets available: ${attackTargets.length}`);
                this.updateActionPrompt('Select target to attack');
                this.showAttackTargetSelection(x, y, attackTargets);
            }
        } catch (error) {
            console.error('Failed to fetch attack targets:', error);
            return;
        }
    }
    
    showAttackTargetSelection(attackerX, attackerY, targets) {
        // Store attack data for event delegation
        this.pendingAttackData = {
            attackerX: attackerX,
            attackerY: attackerY,
            targets: targets
        };
        
        // Create a dynamic submenu showing all attack targets
        const menu = document.getElementById('context-menu');
        
        // Clear existing menu items
        menu.innerHTML = '';
        
        // Add header
        const header = document.createElement('div');
        header.className = 'menu-header';
        header.textContent = 'Select Target:';
        header.style.padding = '8px 20px';
        header.style.color = '#3498db';
        header.style.fontWeight = 'bold';
        header.style.borderBottom = '1px solid rgba(255,255,255,0.1)';
        header.style.marginBottom = '4px';
        menu.appendChild(header);
        
        // Add target options with data attributes
        targets.forEach((target, index) => {
            const button = document.createElement('button');
            button.className = 'menu-item attack-target';
            button.textContent = `${target.unit.type} (${target.x},${target.y})`;
            button.style.display = 'block';
            button.style.width = '100%';
            button.disabled = false;
            
            // Store target data in data attributes
            button.dataset.targetIndex = index;
            button.dataset.targetX = target.x;
            button.dataset.targetY = target.y;
            button.dataset.unitType = target.unit.type;
            
            menu.appendChild(button);
        });
        
        // Add divider and cancel option
        const divider = document.createElement('div');
        divider.className = 'menu-divider';
        menu.appendChild(divider);
        
        const cancelButton = document.createElement('button');
        cancelButton.className = 'menu-item menu-cancel';
        cancelButton.textContent = 'Cancel';
        menu.appendChild(cancelButton);
        
        // Set up single event delegation handler for the menu
        this.setupAttackTargetHandler();
        
        log(`Showing target selection for ${targets.length} targets`);
    }
    
    setupAttackTargetHandler() {
        const menu = document.getElementById('context-menu');
        
        // Remove any existing handlers
        menu.removeEventListener('click', this.attackTargetClickHandler);
        
        // Create new handler
        this.attackTargetClickHandler = async (e) => {
            const target = e.target;
            
            if (target.classList.contains('attack-target')) {
                log('Attack target clicked!', target.textContent);
                
                // Get target data
                const targetX = parseInt(target.dataset.targetX);
                const targetY = parseInt(target.dataset.targetY);
                const unitType = target.dataset.unitType;
                
                // Hide menu
                menu.style.display = 'none';
                
                log(`Selected target: ${unitType} at (${targetX},${targetY})`);
                log(`Attack parameters:`, {
                    attacker_x: this.pendingAttackData.attackerX,
                    attacker_y: this.pendingAttackData.attackerY,
                    defender_x: targetX,
                    defender_y: targetY
                });
                
                try {
                    const result = await this.rpc('unit_attack_enhanced', {
                        attacker_x: this.pendingAttackData.attackerX,
                        attacker_y: this.pendingAttackData.attackerY,
                        defender_x: targetX,
                        defender_y: targetY
                    });
                    log('Attack result:', result);
                } catch (error) {
                    console.error('Attack failed:', error);
                    console.error('Error details:', error.message);
                }
                
                // Clean up
                this.pendingAttackData = null;
            } else if (target.classList.contains('menu-cancel')) {
                log('Attack cancelled');
                menu.style.display = 'none';
                this.restoreOriginalContextMenu();
                this.pendingAttackData = null;
            }
        };
        
        // Add handler
        menu.addEventListener('click', this.attackTargetClickHandler);
    }
    
    lockPreviousUnit(currentX, currentY) {
        // If acting with a different unit, mark the previous unit as done
        if (this.lastActedUnit && 
            (this.lastActedUnit.x !== currentX || this.lastActedUnit.y !== currentY)) {
            
            const lastTile = this.getTile(this.lastActedUnit.x, this.lastActedUnit.y);
            if (lastTile && lastTile.unit) {
                // Exception: Transports can continue loading/unloading
                const transportTypes = ['APC', 'LANDER', 'CRUISER', 'T_COPTER', 'BLACK_BOAT'];
                if (!transportTypes.includes(lastTile.unit.type)) {
                    // Mark non-transport units as done
                    lastTile.unit.done = true;
                    log(`Locked previous unit ${lastTile.unit.type} at (${this.lastActedUnit.x}, ${this.lastActedUnit.y})`);
                }
            }
        }
        
        // Update last acted unit
        this.lastActedUnit = { x: currentX, y: currentY };
    }
    
    async handleDeleteUnit(x, y) {
        // Show confirmation dialog
        const tile = this.getTile(x, y);
        if (!tile || !tile.unit) return;
        
        const unitType = tile.unit.type;
        const confirmed = confirm(`Are you sure you want to delete this ${unitType}?`);
        
        if (confirmed) {
            // Call RPC to delete unit
            const result = await this.rpc('unit_delete', { x, y });
            if (result.success) {
                log(`Deleted ${unitType} at (${x}, ${y})`);
            }
        }
    }
    
    showLoadOptions(x, y) {
        // Find adjacent transports
        const offsets = [[0,-1], [1,0], [0,1], [-1,0]];
        const transports = [];
        
        for (const [dx, dy] of offsets) {
            const nx = x + dx;
            const ny = y + dy;
            const tile = this.getTile(nx, ny);
            
            if (tile?.unit && ['APC', 'LANDER', 'CRUISER', 'T_COPTER', 'BLACK_BOAT'].includes(tile.unit.type)) {
                // Check if it's a friendly transport
                let isFriendly = false;
                if (this.board.current_player !== undefined) {
                    isFriendly = tile.unit.player_id === this.board.current_player;
                } else {
                    isFriendly = tile.unit.army === this.board.current_turn;
                }
                
                if (isFriendly) {
                    transports.push({ x: nx, y: ny, type: tile.unit.type });
                }
            }
        }
        
        if (transports.length === 0) {
            log('No adjacent transports found');
            return;
        }
        
        if (transports.length === 1) {
            // Only one transport, load directly
            this.rpc('unit_load', {
                x: x,      // unit position
                y: y,      // unit position  
                x2: transports[0].x,    // transport position
                y2: transports[0].y     // transport position
            });
        } else {
            // Multiple transports - highlight them and let user choose
            this.clearHighlights();
            transports.forEach(t => {
                const tile = this.getTile(t.x, t.y);
                if (tile) {
                    tile.can_be_loaded_to = true;
                    this.hasHighlights = true;
                }
            });
            this.pendingLoadData = { unitX: x, unitY: y };
            this.render();
        }
    }
    
    restoreOriginalContextMenu() {
        // Restore the original context menu HTML structure
        const menu = document.getElementById('context-menu');
        menu.innerHTML = `
            <button class="menu-item" data-action="move">Move</button>
            <button class="menu-item" data-action="wait">Wait</button>
            <button class="menu-item" data-action="capture">Capture</button>
            <button class="menu-item" data-action="attack">Attack</button>
            <button class="menu-item" data-action="load">Load</button>
            <button class="menu-item" data-action="unload">Unload</button>
            <button class="menu-item" data-action="repair">Supply/Repair</button>
            <button class="menu-item" data-action="delete">Delete Unit</button>
            <div class="menu-divider"></div>
            <button class="menu-item" data-action="cancel">Cancel</button>
        `;
        // Re-setup handlers for the restored menu
        this.setupContextMenuHandlers();
    }
    
    clearUIPanels() {
        document.getElementById('unit-info-panel').style.display = 'none';
        document.getElementById('movement-info-panel').style.display = 'none';
        document.getElementById('combat-preview-panel').style.display = 'none';
        this.clearHighlights();
        // Only render if highlights were actually cleared to avoid unnecessary renders
        if (this.board && this.hasHighlights) {
            this.hasHighlights = false;
            this.render();
        }
    }
    
    isIndirectUnit(unitType) {
        // Check if unit is an indirect attacker
        return ['ARTILLERY', 'ROCKET', 'BATTLESHIP', 'MISSILE', 'CARRIER', 'PIPERUNNER'].includes(unitType);
    }
    
    drawSprite(type, name, x, y) {
        const sprite = this.sprites[type].data[name];
        if (!sprite) {
            console.warn(`Sprite not found: ${type}/${name}`);
            return;
        }
        
        // Debug HP sprites
        if (type === 'ui' && name.startsWith('hp_')) {
            log(`Drawing UI sprite: ${name} at image coords (${sprite.x}, ${sprite.y})`);
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
    
    updateGameStatusPanel() {
        const panel = document.getElementById('game-status-panel');
        if (!panel || !this.board) return;
        
        // Check if game is active or ended
        const isActive = this.board.game_active !== false;
        
        if (!isActive) {
            // Game has ended, show the panel
            panel.style.display = 'block';
            
            // Update status
            document.getElementById('game-status').textContent = 'Ended';
            document.getElementById('game-status').style.color = '#e74c3c';
            
            // Show winner info if available
            if (this.board.winner) {
                document.getElementById('winner-row').style.display = 'flex';
                document.getElementById('game-winner').textContent = this.board.winner;
                
                // Show victory type if available
                if (this.board.victory_type) {
                    document.getElementById('victory-type-row').style.display = 'flex';
                    document.getElementById('victory-type').textContent = this.board.victory_type;
                }
            }
        } else {
            // Game is active, hide the panel
            panel.style.display = 'none';
        }
    }
    
    updatePlayerStatsPanel() {
        const content = document.getElementById('player-stats-content');
        if (!content || !this.board) return;
        
        // Clear existing content
        content.innerHTML = '';
        
        // Calculate player statistics
        const playerStats = {};
        
        // Initialize player data
        if (this.board.players) {
            // V2 game with player data
            this.board.players.forEach(player => {
                playerStats[player.id] = {
                    name: player.name,
                    color: player.color,
                    units: 0,
                    unitValue: 0,
                    properties: 0,
                    funds: this.board.player_funds ? (this.board.player_funds[player.id] || 0) : 0
                };
            });
        } else {
            // Legacy game
            playerStats[0] = {
                name: 'Red Army',
                color: '#e74c3c',
                units: 0,
                unitValue: 0,
                properties: 0,
                funds: this.board.red_funds || 0
            };
            playerStats[1] = {
                name: 'Blue Army',
                color: '#3498db',
                units: 0,
                unitValue: 0,
                properties: 0,
                funds: this.board.blue_funds || 0
            };
        }
        
        // Count units and properties
        this.board.grid.forEach(tile => {
            // Count units
            if (tile.unit) {
                let playerId;
                if (tile.unit.player_id !== undefined) {
                    playerId = tile.unit.player_id;
                } else {
                    // Legacy: map army to player ID
                    playerId = tile.unit.army === 'RED' ? 0 : 1;
                }
                
                if (playerStats[playerId]) {
                    playerStats[playerId].units++;
                    // Estimate unit value (simplified - should use actual costs)
                    const unitCosts = {
                        'INFANTRY': 1000, 'MECH': 3000, 'RECON': 4000, 'TANK': 7000,
                        'MD_TANK': 16000, 'NEOTANK': 22000, 'APC': 5000, 'ARTILLERY': 6000,
                        'ROCKET': 15000, 'ANTI_AIR': 8000, 'MISSILE': 12000, 'B_COPTER': 9000,
                        'T_COPTER': 5000, 'FIGHTER': 20000, 'BOMBER': 22000, 'BATTLESHIP': 28000,
                        'CRUISER': 18000, 'LANDER': 12000, 'SUB': 20000, 'BLACK_BOAT': 7500
                    };
                    playerStats[playerId].unitValue += unitCosts[tile.unit.type] || 10000;
                }
            }
            
            // Count properties
            if (tile.mapTile && ['CITY', 'FACTORY', 'AIRPORT', 'PORT', 'HQ', 'BASE_TOWER_0', 'BASE_TOWER_1', 'BASE_TOWER_2', 'BASE_TOWER_3', 'BASE_TOWER_4'].includes(tile.mapTile.type)) {
                let playerId;
                if (tile.mapTile.player_id !== undefined) {
                    playerId = tile.mapTile.player_id;
                } else if (tile.mapTile.army) {
                    // Legacy: map army to player ID
                    playerId = tile.mapTile.army === 'RED' ? 0 : 1;
                } else {
                    return; // Neutral property
                }
                
                if (playerStats[playerId]) {
                    playerStats[playerId].properties++;
                }
            }
        });
        
        // Create stat rows for each player
        Object.entries(playerStats).forEach(([playerId, stats]) => {
            const playerDiv = document.createElement('div');
            playerDiv.style.marginBottom = '15px';
            playerDiv.style.borderBottom = '1px solid rgba(255,255,255,0.1)';
            playerDiv.style.paddingBottom = '10px';
            
            // Player name header
            const nameDiv = document.createElement('div');
            nameDiv.style.fontSize = '14px';
            nameDiv.style.fontWeight = '600';
            nameDiv.style.color = stats.color;
            nameDiv.style.marginBottom = '8px';
            nameDiv.textContent = stats.name;
            playerDiv.appendChild(nameDiv);
            
            // Stats
            const statsData = [
                { label: 'Units:', value: stats.units },
                { label: 'Unit Value:', value: stats.unitValue.toLocaleString() },
                { label: 'Properties:', value: stats.properties },
                { label: 'Funds:', value: stats.funds.toLocaleString() }
            ];
            
            statsData.forEach(stat => {
                const row = document.createElement('div');
                row.className = 'stat-row';
                row.innerHTML = `
                    <span class="stat-label">${stat.label}</span>
                    <span class="stat-value">${stat.value}</span>
                `;
                playerDiv.appendChild(row);
            });
            
            content.appendChild(playerDiv);
        });
        
        // Remove last border
        if (content.lastChild) {
            content.lastChild.style.borderBottom = 'none';
            content.lastChild.style.paddingBottom = '0';
            content.lastChild.style.marginBottom = '0';
        }
    }
}

// Start game when page loads
window.addEventListener('DOMContentLoaded', () => {
    window.game = new Game();
});