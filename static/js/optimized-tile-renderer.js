// Optimized Tile Renderer for Advance Wars RPC
// Uses JSON-based tile mapping for better performance and maintainability

class OptimizedTileRenderer {
    constructor() {
        this.tileMap = null;
        this.tilesetImages = {};
        this.tileCache = new Map();
        this.loaded = false;
        this.selectedTileset = 'normal_transparent';
    }

    async initialize() {
        try {
            // Try to load optimized tile map first
            try {
                const optimizedMapResponse = await fetch('/static/img/optimized_tileset_map.json');
                this.tileMap = await optimizedMapResponse.json();
                this.useOptimized = true;
                console.log('✅ Using optimized tileset (92% smaller)');
            } catch (error) {
                // Fallback to legacy tile map
                const mapResponse = await fetch('/templates/tile_sprite_map.json');
                this.tileMap = await mapResponse.json();
                this.useOptimized = false;
                console.log('Using legacy tile map');
            }
            
            // Preload default tileset
            await this.loadTileset(this.selectedTileset);
            
            this.loaded = true;
            console.log('✅ Optimized tile renderer initialized');
            return true;
        } catch (error) {
            console.error('Failed to initialize optimized tile renderer:', error);
            throw error;
        }
    }

    async loadTileset(tilesetType) {
        if (this.tilesetImages[tilesetType]) {
            return; // Already loaded
        }

        const tilesetPath = this.getTilesetPath(tilesetType);
        
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => {
                this.tilesetImages[tilesetType] = img;
                console.log(`✅ Loaded tileset: ${tilesetType}`);
                resolve();
            };
            img.onerror = () => {
                console.error(`Failed to load tileset: ${tilesetType}`);
                reject(new Error(`Failed to load tileset: ${tilesetPath}`));
            };
            img.src = tilesetPath;
        });
    }

    getTilesetPath(tilesetType) {
        // Use optimized tilesets if available
        if (this.useOptimized) {
            switch (tilesetType) {
                case 'normal_transparent':
                    return '/static/img/optimized_tileset_transparent.png';
                case 'normal':
                    return '/static/img/optimized_tileset_normal.png';
                default:
                    // Fallback to legacy for blackhole tilesets (not optimized yet)
                    break;
            }
        }
        
        // Legacy paths
        switch (tilesetType) {
            case 'normal_transparent':
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

    async setTileset(tilesetType) {
        await this.loadTileset(tilesetType);
        this.selectedTileset = tilesetType;
        this.tileCache.clear(); // Clear cache when switching tilesets
        console.log(`Switched to tileset: ${tilesetType}`);
    }

    getTileConfig(tileType, army = null) {
        const tileData = this.tileMap.tiles[tileType];
        if (!tileData) {
            console.warn(`Unknown tile type: ${tileType}`);
            return null;
        }

        // Handle tiles with army variants
        if (tileData.variants) {
            const variant = army && tileData.variants[army] ? tileData.variants[army] : tileData.variants.neutral;
            return variant || tileData.variants[Object.keys(tileData.variants)[0]];
        }

        return tileData;
    }

    createTileTexture(tileType, army = null) {
        const cacheKey = `${this.selectedTileset}_${tileType}_${army || 'neutral'}`;
        
        // Check cache first
        if (this.tileCache.has(cacheKey)) {
            return this.tileCache.get(cacheKey);
        }

        const tileConfig = this.getTileConfig(tileType, army);
        if (!tileConfig) {
            return null;
        }

        const tilesetImage = this.tilesetImages[this.selectedTileset];
        if (!tilesetImage) {
            console.error('Tileset not loaded:', this.selectedTileset);
            return null;
        }

        // Create canvas for tile
        const canvas = document.createElement('canvas');
        canvas.width = tileConfig.width;
        canvas.height = tileConfig.height;
        const ctx = canvas.getContext('2d');

        // Calculate source position in sprite sheet
        let srcX, srcY;
        if (this.useOptimized) {
            // Optimized tileset uses direct coordinates
            srcX = tileConfig.x;
            srcY = tileConfig.y;
        } else {
            // Legacy tileset uses center-based offsets
            const centerX = this.tileMap.sprite_sheet.center_x;
            const centerY = this.tileMap.sprite_sheet.center_y;
            srcX = centerX + tileConfig.x;
            srcY = centerY + tileConfig.y;
        }

        // Draw tile from sprite sheet
        ctx.drawImage(
            tilesetImage,
            srcX, srcY, tileConfig.width, tileConfig.height,
            0, 0, tileConfig.width, tileConfig.height
        );

        // Cache the result
        this.tileCache.set(cacheKey, canvas);
        
        return canvas;
    }

    renderTile(two, tile, tileSize) {
        const tileType = tile.mapTile.type;
        const army = tile.mapTile.army;
        
        // Get tile configuration
        const tileConfig = this.getTileConfig(tileType, army);
        if (!tileConfig) {
            return null;
        }

        // Create tile texture
        const tileCanvas = this.createTileTexture(tileType, army);
        if (!tileCanvas) {
            return null;
        }

        // Create Two.js texture from canvas
        const dataUrl = tileCanvas.toDataURL();
        const texture = new Two.Texture(dataUrl, () => {
            // Texture loaded callback
            if (window.two && window.two.update) {
                window.two.update();
            }
        });
        
        // Calculate position
        const x = tile.x * tileSize + tileSize / 2;
        const y = tile.y * tileSize + tileSize / 2;

        // Adjust y position for double-height tiles
        let adjustedY = y;
        if (tileConfig.height > tileSize) {
            adjustedY = y - (tileConfig.height - tileSize) / 2;
        }

        // Create rectangle with texture
        const rect = two.makeRectangle(x, adjustedY, tileConfig.width, tileConfig.height);
        rect.fill = texture;
        rect.noStroke();
        
        // Add to scene (don't return, to match legacy behavior)
        two.add(rect);
        
        return rect;
    }

    // Render base PLAIN tile for structures (prevents transparency issues)
    renderBaseTile(two, tile, tileSize) {
        const plainCanvas = this.createTileTexture('PLAIN');
        if (!plainCanvas) {
            return null;
        }

        const dataUrl = plainCanvas.toDataURL();
        const texture = new Two.Texture(dataUrl, () => {
            // Texture loaded callback
            if (window.two && window.two.update) {
                window.two.update();
            }
        });
        const x = tile.x * tileSize + tileSize / 2;
        const y = tile.y * tileSize + tileSize / 2;

        const rect = two.makeRectangle(x, y, tileSize, tileSize);
        rect.fill = texture;
        rect.noStroke();
        
        // Add to scene (don't return, to match legacy behavior)
        two.add(rect);

        return rect;
    }

    // Check if a tile type needs a base layer
    needsBaseLayer(tileType) {
        const structureTiles = [
            'CITY', 'FACTORY', 'AIRPORT', 'PORT', 'LAB', 'COM_TOWER',
            'MISSILE_SILO', 'EMPTY_SILO', 'BASE_TOWER_0', 'BASE_TOWER_1',
            'BASE_TOWER_2', 'BASE_TOWER_3', 'BASE_TOWER_4'
        ];
        return structureTiles.includes(tileType);
    }

    // Get statistics about tile usage
    getStatistics() {
        return {
            loaded: this.loaded,
            currentTileset: this.selectedTileset,
            cachedTiles: this.tileCache.size,
            totalTileTypes: Object.keys(this.tileMap.tiles).length,
            tilesetsLoaded: Object.keys(this.tilesetImages).length
        };
    }

    // Clear cache (useful for memory management)
    clearCache() {
        this.tileCache.clear();
        console.log('Tile cache cleared');
    }
}

// Export as global for legacy compatibility
window.optimizedTileRenderer = new OptimizedTileRenderer();