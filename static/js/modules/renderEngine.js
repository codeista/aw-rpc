/**
 * Render Engine Module - Handles all rendering operations with Two.js
 * Extracted from render.js as part of modularization effort
 */

import { getBoard } from './gameState.js';
import { TILESIZE } from './core.js';

// Ensure logger exists
if (typeof window.logger === 'undefined') {
    window.logger = console; // Fallback to console if logger.js isn't loaded
}
const logger = window.logger;

// ===== CONSTANTS =====
const SPRITESIZE = 16;
const HEALTHSIZE = 8;
const FUELSIZE = 8;
const AMMOSIZE = 8;
const FLAGSIZE = 8;
const LOADSIZE = 8;

// ===== RENDER STATE =====
const renderState = {
    sceneInitialized: false,
    sceneElements: {
        terrain: {},
        units: {},
        highlights: {}
    },
    textureLoadTimer: null,
    movementHighlightGroup: null,
    attackHighlightGroup: null,
    transportHighlightGroup: null
};

// ===== TILESET MANAGEMENT =====

/**
 * Get the selected terrain tileset
 * @returns {string} Path to terrain tileset
 */
export function getSelectedTerrainTileset() {
    const select = document.getElementById('terrainTilesetSelect');
    if (!select) return '/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png';
    
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

/**
 * Get the selected unit tileset
 * @returns {string} Path to unit tileset
 */
export function getSelectedUnitTileset() {
    const select = document.getElementById('unitTilesetSelect');
    if (!select) return '/static/img/aw2_blackhole_units_map_transparent.png';
    
    switch (select.value) {
        case 'blackhole_transparent':
            return '/static/img/aw2_blackhole_units_map_transparent.png';
        case 'blackhole_normal':
            return '/static/img/aw2_blackhole_units_map.png';
        default:
            return '/static/img/aw2_blackhole_units_map_transparent.png';
    }
}

// ===== TEXTURE LOADING =====

/**
 * Handle texture load completion
 * @param {string} src - Source URL of loaded texture
 */
export function onTextureLoad(src) {
    if (renderState.textureLoadTimer) {
        clearTimeout(renderState.textureLoadTimer);
        renderState.textureLoadTimer = null;
    }
    renderState.textureLoadTimer = setTimeout(() => {
        if (window.two) {
            window.two.update();
        }
    }, 100);
}

// ===== SCENE MANAGEMENT =====

/**
 * Initialize the rendering scene
 */
export async function initializeScene() {
    logger.info('🎨 Initializing scene...');
    
    const board = getBoard();
    if (!board || !board.grid || !window.two) return;
    
    // Clear existing scene
    window.two.clear();
    
    // Reset scene elements tracking
    renderState.sceneElements = {
        terrain: {},
        units: {},
        highlights: {}
    };
    
    // Render all tiles
    for (let i = 0; i < board.height; i++) {
        for (let j = 0; j < board.width; j++) {
            const tile = board.grid[j + i * board.width];
            const key = `${j},${i}`;
            
            // Create map tile
            makeMapTile(tile);
            renderState.sceneElements.terrain[key] = true;
            
            // Create unit sprite if present
            if (tile.unit !== null) {
                const sprite = await makeSprite(tile);
                renderState.sceneElements.units[key] = {
                    type: tile.unit.type,
                    hp: tile.unit.status?.hp || tile.unit.hp,
                    sprite: sprite
                };
            }
        }
    }
    
    // Render transport indicators
    renderTransportIndicators();
    
    renderState.sceneInitialized = true;
    window.sceneInitialized = true;
    
    logger.info('✅ Scene initialized');
}

/**
 * Update only changed elements in the scene
 */
export async function updateScene() {
    const board = getBoard();
    if (!board || !board.grid || !window.two) return;
    
    // Ensure sprite corrections are loaded
    if (window.loadSpriteCorrectorData) {
        await window.loadSpriteCorrectorData();
    }
    
    // Track which units we've seen this update
    const currentUnits = new Set();
    
    // Update tiles
    for (let i = 0; i < board.height; i++) {
        for (let j = 0; j < board.width; j++) {
            const tile = board.grid[j + i * board.width];
            const key = `${j},${i}`;
            
            // Update terrain only if changed (rarely happens)
            if (!renderState.sceneElements.terrain[key]) {
                makeMapTile(tile);
                renderState.sceneElements.terrain[key] = true;
            }
            
            // Update units
            if (tile.unit !== null) {
                currentUnits.add(key);
                
                // Check if unit exists and needs update
                const existingUnit = renderState.sceneElements.units[key];
                const unitHp = tile.unit.status?.hp || tile.unit.hp;
                
                if (!existingUnit || 
                    existingUnit.hp !== unitHp ||
                    existingUnit.type !== tile.unit.type) {
                    
                    // Remove old unit sprite if exists
                    if (existingUnit?.sprite) {
                        window.two.remove(existingUnit.sprite);
                    }
                    
                    // Create new unit sprite
                    const sprite = await makeSprite(tile);
                    renderState.sceneElements.units[key] = {
                        type: tile.unit.type,
                        hp: unitHp,
                        sprite: sprite
                    };
                }
            }
        }
    }
    
    // Remove units that no longer exist
    for (const key in renderState.sceneElements.units) {
        if (!currentUnits.has(key)) {
            const unit = renderState.sceneElements.units[key];
            if (unit.sprite) {
                window.two.remove(unit.sprite);
            }
            delete renderState.sceneElements.units[key];
        }
    }
    
    // Update transport indicators
    renderTransportIndicators();
}

/**
 * Force a complete re-render
 */
export async function rerender() {
    console.time('rerender');
    
    if (window.two) {
        // Update only what changed to prevent black flash
        await updateScene();
        window.two.update();
    } else {
        logger.error('Two.js not initialized');
    }
    
    console.timeEnd('rerender');
}

/**
 * Force a full scene refresh
 */
export function forceSceneRefresh() {
    renderState.sceneInitialized = false;
    renderState.sceneElements = {
        terrain: {},
        units: {},
        highlights: {}
    };
    window.sceneInitialized = false;
    window.sceneElements = renderState.sceneElements;
}

// ===== TILE RENDERING =====

/**
 * Render a base tile layer for structures
 * @param {Object} tile - Tile to render base for
 */
function renderBaseTile(tile) {
    const spriteSheetWidth = 445;
    const spriteSheetHeight = 1163;
    let x = spriteSheetWidth/2 - SPRITESIZE/2;
    let y = spriteSheetHeight/2 - SPRITESIZE/2;
    
    // PLAIN tile coordinates
    x = x - 8;
    y = y - 64;
    
    // Always use transparent tileset for base layer
    const baseTilesetSrc = '/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png';
    const baseTexture = new Two.Texture(baseTilesetSrc, () => onTextureLoad(baseTilesetSrc));
    baseTexture.offset = new Two.Vector(x, y);
    
    const baseRect = window.two.makeRectangle(
        tile.x * TILESIZE + TILESIZE/2, 
        tile.y * TILESIZE + TILESIZE/2, 
        SPRITESIZE, 
        SPRITESIZE
    );
    baseRect.fill = baseTexture;
    baseRect.stroke = 'transparent';
}

/**
 * Create map tile sprite
 * @param {Object} tile - Tile to render
 */
export function makeMapTile(tile) {
    const showMapTiles = document.getElementById('inputshowmap')?.checked;
    
    if (showMapTiles && tile.mapTile) {
        // Check if this terrain type needs a base layer
        const structureTypes = [
            'CITY', 'FACTORY', 'AIRPORT', 'PORT', 'COM_TOWER', 'LAB', 
            'MISSILE_SILO', 'EMPTY_SILO', 'BASE_TOWER_0', 'BASE_TOWER_1', 
            'BASE_TOWER_2', 'BASE_TOWER_3', 'BASE_TOWER_4', 'MOUNTAIN'
        ];
        
        if (structureTypes.includes(tile.mapTile.type)) {
            renderBaseTile(tile);
        }
        
        // Get sprite coordinates
        const coords = getTerrainSpriteCoords(tile.mapTile);
        if (!coords) return;
        
        const tilesetSrc = getSelectedTerrainTileset();
        const spriteTexture = new Two.Texture(tilesetSrc, () => onTextureLoad(tilesetSrc));
        spriteTexture.offset = new Two.Vector(coords.x, coords.y);
        
        let rect;
        if (coords.doubleHeight) {
            // Double-height tiles overlap the top border
            rect = window.two.makeRectangle(
                tile.x * TILESIZE + TILESIZE/2, 
                tile.y * TILESIZE, 
                SPRITESIZE, 
                SPRITESIZE * 2
            );
        } else {
            rect = window.two.makeRectangle(
                tile.x * TILESIZE + TILESIZE/2, 
                tile.y * TILESIZE + TILESIZE/2, 
                SPRITESIZE, 
                SPRITESIZE
            );
        }
        rect.fill = spriteTexture;
        rect.stroke = 'transparent';
    }
    
    // Tile overlay
    const rect = window.two.makeRectangle(
        tile.x * TILESIZE + TILESIZE/2, 
        tile.y * TILESIZE + TILESIZE/2, 
        TILESIZE, 
        TILESIZE
    );
    rect.stroke = 'black';
    rect.fill = 'transparent';
    rect.linewidth = 0.5;
}

/**
 * Get terrain sprite coordinates
 * @param {Object} mapTile - Map tile data
 * @returns {Object|null} Sprite coordinates and flags
 */
function getTerrainSpriteCoords(mapTile) {
    const spriteSheetWidth = 445;
    const spriteSheetHeight = 1163;
    let x = spriteSheetWidth/2 - SPRITESIZE/2;
    let y = spriteSheetHeight/2 - SPRITESIZE/2;
    let doubleHeight = false;
    
    // This is a simplified version - full implementation would include all terrain types
    switch (mapTile.type) {
        case 'PLAIN':
            x = x - 8;
            y = y - 64;
            break;
        case 'WOOD':
            x = x - 352;
            y = y - 56;
            doubleHeight = true;
            break;
        case 'MOUNTAIN':
            x = x - 25;
            y = y - 39;
            doubleHeight = true;
            break;
        case 'ROAD_HORT':
            x = x - 42;
            y = y - 64;
            break;
        case 'ROAD_VERT':
            x = x - 59;
            y = y - 64;
            break;
        case 'CITY':
            x = x - 87;
            // Additional logic for army colors would go here
            break;
        default:
            return null;
    }
    
    return { x, y, doubleHeight };
}

// ===== UNIT RENDERING =====

/**
 * Create unit sprite with HP indicator
 * @param {Object} tile - Tile containing unit
 * @returns {Object} Two.js sprite object
 */
export async function makeSprite(tile) {
    try {
        // Try to use advanced texture generation if available
        if (window.generateUnitTexture) {
            const uniqueTextureURL = await window.generateUnitTexture(tile);
            const spriteTexture = new Two.Texture(uniqueTextureURL);
            const rect = window.two.makeRectangle(
                tile.x * TILESIZE + TILESIZE/2, 
                tile.y * TILESIZE + TILESIZE/2, 
                SPRITESIZE, 
                SPRITESIZE
            );
            rect.fill = spriteTexture;
            rect.stroke = 'transparent';
            
            // Store sprite reference for compatibility
            tile.sprite = rect;
            
            // Force re-render
            if (window.two) {
                window.two.update();
            }
            
            return rect;
        }
    } catch (error) {
        logger.error('Error generating unit texture:', error);
    }
    
    // Fallback to legacy sprite creation
    return makeSpriteLegacy(tile);
}

/**
 * Legacy sprite creation method
 * @param {Object} tile - Tile containing unit
 * @returns {Object} Two.js sprite object
 */
function makeSpriteLegacy(tile) {
    const coords = getUnitSpriteCoords(tile.unit);
    const unitsSrc = getSelectedUnitTileset();
    
    // Create unique texture per unit to prevent sharing
    const spriteTexture = new Two.Texture(
        unitsSrc + '?unit=' + tile.x + '_' + tile.y, 
        () => onTextureLoad(unitsSrc)
    );
    spriteTexture.offset = new Two.Vector(coords.x, coords.y);
    
    const rect = window.two.makeRectangle(
        tile.x * TILESIZE + TILESIZE/2, 
        tile.y * TILESIZE + TILESIZE/2, 
        SPRITESIZE, 
        SPRITESIZE
    );
    rect.fill = spriteTexture;
    rect.stroke = 'transparent';
    
    // Add HP indicator if needed
    if (tile.unit.status?.hp <= 90) {
        addHPIndicator(tile, unitsSrc);
    }
    
    // Add fuel indicator if low
    if (tile.unit.status?.fuel <= 30) {
        addFuelIndicator(tile, unitsSrc);
    }
    
    // Add ammo indicator if low
    if (tile.unit.status?.ammo <= 3 && tile.unit.UnitType !== 0) {
        addAmmoIndicator(tile, unitsSrc);
    }
    
    // Add capture flag if capturing
    if (tile.capture_hp <= 19) {
        addCaptureFlag(tile, unitsSrc);
    }
    
    // Add cargo indicator for transports
    if (window.isTransportUnitForRender && window.isTransportUnitForRender(tile.unit)) {
        const cargoCount = window.getCargoCountForRender ? 
            window.getCargoCountForRender(tile.unit) : 0;
        if (cargoCount > 0) {
            addCargoIndicator(tile, unitsSrc);
        }
    }
    
    return rect;
}

/**
 * Get unit sprite coordinates based on army and type
 * @param {Object} unit - Unit data
 * @returns {Object} Sprite coordinates
 */
function getUnitSpriteCoords(unit) {
    const spriteSheetWidth = 781;
    const spriteSheetHeight = 1790;
    let x = spriteSheetWidth/2 - SPRITESIZE/2;
    let y = spriteSheetHeight/2 - SPRITESIZE/2;
    
    // Army offsets
    switch (unit.army) {
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
            y = y - 548;
            break;
        case 'YELLOW':
            x = x - 393;
            y = y - 548;
            break;
    }
    
    // Unit type offsets would go here
    // This is simplified - full implementation would include all unit types
    
    // Unavailable sprite offset
    if (!unit.can_move && !unit.can_attack) {
        x = x - 336;
    }
    
    return { x, y };
}

// ===== INDICATOR RENDERING =====

/**
 * Add HP indicator to unit
 * @param {Object} tile - Tile containing unit
 * @param {string} unitsSrc - Units texture source
 */
function addHPIndicator(tile, unitsSrc) {
    const hpDigit = Math.min(9, Math.max(1, Math.ceil(tile.unit.status.hp / 10)));
    const canMove = tile.unit.can_move;
    
    const spriteSheetWidth = 781;
    const spriteSheetHeight = 1790;
    let x = spriteSheetWidth/2 - HEALTHSIZE/2;
    let y = spriteSheetHeight/2 - HEALTHSIZE/2;
    
    if (canMove) {
        // Active HP coordinates
        x = x - 425 - ((hpDigit - 1) * 9);
        y = y - 1233;
    } else {
        // Inactive HP coordinates
        x = x - 297 - ((hpDigit - 1) * 9);
        y = y - 1233;
    }
    
    const healthTexture = new Two.Texture(
        unitsSrc + '?hp_' + (canMove ? 'active' : 'inactive') + '=' + tile.x + '_' + tile.y + '_' + hpDigit,
        () => onTextureLoad(unitsSrc)
    );
    healthTexture.offset = new Two.Vector(x, y);
    
    const health = window.two.makeRectangle(
        tile.x * TILESIZE + TILESIZE - HEALTHSIZE/2,
        tile.y * TILESIZE + TILESIZE - HEALTHSIZE/2,
        HEALTHSIZE,
        HEALTHSIZE
    );
    health.fill = healthTexture;
    health.stroke = 'transparent';
}

/**
 * Add fuel indicator
 */
function addFuelIndicator(tile, unitsSrc) {
    const spriteSheetWidth = 781;
    const spriteSheetHeight = 1790;
    let x = spriteSheetWidth/2 - FUELSIZE/2 - 651;
    let y = spriteSheetHeight/2 - FUELSIZE/2 - 1241;
    
    const fuelTexture = new Two.Texture(unitsSrc, () => onTextureLoad(unitsSrc));
    fuelTexture.offset = new Two.Vector(x, y);
    
    const fuel = window.two.makeRectangle(
        tile.x * TILESIZE + TILESIZE - FUELSIZE/2 - 8,
        tile.y * TILESIZE + TILESIZE - FUELSIZE/2 - 8,
        FUELSIZE,
        FUELSIZE
    );
    fuel.fill = fuelTexture;
    fuel.stroke = 'transparent';
}

/**
 * Add ammo indicator
 */
function addAmmoIndicator(tile, unitsSrc) {
    const spriteSheetWidth = 781;
    const spriteSheetHeight = 1790;
    let x = spriteSheetWidth/2 - AMMOSIZE/2 - 651;
    let y = spriteSheetHeight/2 - AMMOSIZE/2 - 1251;
    
    const ammoTexture = new Two.Texture(unitsSrc, () => onTextureLoad(unitsSrc));
    ammoTexture.offset = new Two.Vector(x, y);
    
    const ammo = window.two.makeRectangle(
        tile.x * TILESIZE + TILESIZE - AMMOSIZE/2,
        tile.y * TILESIZE + TILESIZE - AMMOSIZE/2 - 8,
        AMMOSIZE - 2,
        AMMOSIZE - 2
    );
    ammo.fill = ammoTexture;
    ammo.stroke = 'transparent';
}

/**
 * Add capture flag indicator
 */
function addCaptureFlag(tile, unitsSrc) {
    const spriteSheetWidth = 781;
    const spriteSheetHeight = 1790;
    let x = spriteSheetWidth/2 - FLAGSIZE/2 - 530;
    let y = spriteSheetHeight/2 - FLAGSIZE/2 - 1233;
    
    const flagTexture = new Two.Texture(unitsSrc, () => onTextureLoad(unitsSrc));
    flagTexture.offset = new Two.Vector(x, y);
    
    const flag = window.two.makeRectangle(
        tile.x * TILESIZE + TILESIZE - FLAGSIZE/2 - 8,
        tile.y * TILESIZE + TILESIZE - FLAGSIZE/2,
        FLAGSIZE,
        FLAGSIZE
    );
    flag.fill = flagTexture;
    flag.stroke = 'transparent';
}

/**
 * Add cargo indicator for transports
 */
function addCargoIndicator(tile, unitsSrc) {
    const spriteSheetWidth = 781;
    const spriteSheetHeight = 1790;
    let x = spriteSheetWidth/2 - LOADSIZE/2 - 520;
    let y = spriteSheetHeight/2 - LOADSIZE/2 - 1233;
    
    const loadTexture = new Two.Texture(unitsSrc, () => onTextureLoad(unitsSrc));
    loadTexture.offset = new Two.Vector(x, y);
    
    const load = window.two.makeRectangle(
        tile.x * TILESIZE + TILESIZE - LOADSIZE/2 - 8,
        tile.y * TILESIZE + TILESIZE - LOADSIZE/2,
        LOADSIZE,
        LOADSIZE
    );
    load.fill = loadTexture;
    load.stroke = 'transparent';
}

// ===== HIGHLIGHT RENDERING =====

/**
 * Render movement highlights
 */
export function renderMovementHighlights() {
    if (!window.movementHighlights || !window.two || window.movementHighlights.length === 0) {
        return;
    }
    
    // Clear existing visual highlights
    if (renderState.movementHighlightGroup) {
        window.two.remove(renderState.movementHighlightGroup);
    }
    
    // Create new highlight group
    renderState.movementHighlightGroup = window.two.makeGroup();
    
    window.movementHighlights.forEach(highlight => {
        const rect = createHighlightRect(highlight.x, highlight.y, '#4CAF50', 0.3);
        renderState.movementHighlightGroup.add(rect);
    });
    
    window.two.update();
}

/**
 * Render attack highlights
 */
export function renderAttackHighlights() {
    if (!window.gameState?.attackHighlights || !window.two || 
        window.gameState.attackHighlights.length === 0) {
        return;
    }
    
    // Clear existing visual highlights
    if (renderState.attackHighlightGroup) {
        window.two.remove(renderState.attackHighlightGroup);
    }
    
    // Create new highlight group
    renderState.attackHighlightGroup = window.two.makeGroup();
    
    window.gameState.attackHighlights.forEach(highlight => {
        const rect = createHighlightRect(highlight.x, highlight.y, '#F44336', 0.4);
        renderState.attackHighlightGroup.add(rect);
    });
    
    window.two.update();
}

/**
 * Render transport highlights
 */
export function renderTransportHighlights() {
    // Clear any existing highlight group
    if (renderState.transportHighlightGroup) {
        window.two.remove(renderState.transportHighlightGroup);
        renderState.transportHighlightGroup = null;
    }
    
    if (!window.transportHighlights || window.transportHighlights.length === 0) {
        return;
    }
    
    // Create new highlight group
    renderState.transportHighlightGroup = window.two.makeGroup();
    
    window.transportHighlights.forEach(highlight => {
        const color = highlight.type === 'load' ? '#2196F3' : '#9C27B0';
        const rect = createHighlightRect(highlight.x, highlight.y, color, 0.3);
        renderState.transportHighlightGroup.add(rect);
    });
    
    window.two.update();
}

/**
 * Render all transport indicators
 */
function renderTransportIndicators() {
    logger.debug('RENDER: Adding transport indicators');
    renderTransportHighlights();
}

/**
 * Create a highlight rectangle
 * @param {number} x - Tile X coordinate
 * @param {number} y - Tile Y coordinate
 * @param {string} color - Highlight color
 * @param {number} opacity - Highlight opacity
 * @returns {Object} Two.js rectangle
 */
function createHighlightRect(x, y, color, opacity) {
    const rect = window.two.makeRectangle(
        x * TILESIZE + TILESIZE/2,
        y * TILESIZE + TILESIZE/2,
        TILESIZE - 2,
        TILESIZE - 2
    );
    rect.fill = color;
    rect.opacity = opacity;
    rect.stroke = color;
    rect.linewidth = 2;
    return rect;
}

// ===== MODULE INITIALIZATION =====

/**
 * Initialize the render engine module
 */
export function initializeRenderEngineModule() {
    logger.info('Initializing render engine module...');
    
    // Set up global references for legacy compatibility
    if (window) {
        // Tileset functions
        window.getSelectedTerrainTileset = getSelectedTerrainTileset;
        window.getSelectedUnitTileset = getSelectedUnitTileset;
        
        // Scene management
        window.initializeScene = initializeScene;
        window.updateScene = updateScene;
        window.rerender = rerender;
        window.forceSceneRefresh = forceSceneRefresh;
        
        // Tile rendering
        window.makeMapTile = makeMapTile;
        window.makeSprite = makeSprite;
        
        // Highlight rendering
        window.renderMovementHighlights = renderMovementHighlights;
        window.renderAttackHighlights = renderAttackHighlights;
        window.renderTransportHighlights = renderTransportHighlights;
        
        // Texture loading
        window.ontextureLoad = window.ontextureLoad || onTextureLoad;
    }
    
    logger.info('Render engine module initialized');
}

// Initialize on module load
initializeRenderEngineModule();