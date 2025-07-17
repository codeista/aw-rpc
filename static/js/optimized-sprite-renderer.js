/**
 * Optimized Sprite Renderer
 * Uses pre-rendered sprite sheet with all color variants
 */

class OptimizedSpriteRenderer {
    constructor() {
        this.spriteSheet = null;
        this.spriteMap = null;
        this.loaded = false;
    }

    async initialize() {
        try {
            // Load sprite map
            const mapResponse = await fetch('/static/img/units_sprite_map_v2.json');
            this.spriteMap = await mapResponse.json();
            
            // Load sprite sheet
            return new Promise((resolve, reject) => {
                this.spriteSheet = new Image();
                this.spriteSheet.onload = () => {
                    this.loaded = true;
                    console.log('✅ Optimized sprite sheet v2 loaded');
                    resolve();
                };
                this.spriteSheet.onerror = reject;
                this.spriteSheet.src = '/static/img/units_sprite_sheet_v2.png';
            });
        } catch (error) {
            console.error('Failed to load optimized sprites:', error);
            throw error;
        }
    }

    getSpriteInfo(unitType, army, state = 'idle', frame = 0) {
        if (!this.loaded || !this.spriteMap) return null;
        
        const spriteKey = `${unitType}_${army}_${state}_${frame}`;
        const spriteInfo = this.spriteMap.sprites[spriteKey];
        
        // Check if sprite actually exists (not just mapped)
        if (spriteInfo && spriteInfo.exists === false) {
            return null;
        }
        
        return spriteInfo || null;
    }

    drawSprite(ctx, unitType, army, state, frame, destX, destY, destSize) {
        const spriteInfo = this.getSpriteInfo(unitType, army, state, frame);
        if (!spriteInfo) return false;

        // Draw from sprite sheet
        ctx.drawImage(
            this.spriteSheet,
            spriteInfo.x,
            spriteInfo.y,
            spriteInfo.width,
            spriteInfo.height,
            destX,
            destY,
            destSize,
            destSize
        );
        
        return true;
    }

    // Helper to get sprite coordinates for Two.js Sprite
    getSpriteCoordinates(unitType, army, state = 'idle', frame = 0) {
        const spriteInfo = this.getSpriteInfo(unitType, army, state, frame);
        if (!spriteInfo) return null;

        return {
            x: spriteInfo.x,
            y: spriteInfo.y,
            width: spriteInfo.width,
            height: spriteInfo.height,
            columns: this.spriteMap.metadata.sprites_per_row,
            rows: Math.ceil(Object.keys(this.spriteMap.sprites).length / this.spriteMap.metadata.sprites_per_row)
        };
    }
}

// Create global instance
window.optimizedSpriteRenderer = new OptimizedSpriteRenderer();