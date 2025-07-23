/**
 * Sprite Mapping System
 * Maps player IDs to sprite colors for dynamic color assignment
 */

class SpriteMapper {
    constructor() {
        // Default sprite color assignments
        this.defaultMapping = {
            0: 'RED',
            1: 'BLUE',
            2: 'GREEN',
            3: 'YELLOW',
            4: 'GREY'
        };
        
        // Current mapping (can be overridden)
        this.playerSpriteMap = { ...this.defaultMapping };
        
        // Player configuration
        this.players = {};
    }
    
    /**
     * Initialize from game state
     * @param {Object} gameState - Game state with player configuration
     */
    initFromGameState(gameState) {
        // Clear existing mappings
        this.playerSpriteMap = {};
        this.players = {};
        
        // Check for player configuration in game state
        if (gameState.players) {
            // New format with player configuration
            for (const [playerId, playerData] of Object.entries(gameState.players)) {
                const id = parseInt(playerId);
                this.players[id] = playerData;
                this.playerSpriteMap[id] = playerData.sprite_color || this.defaultMapping[id] || 'GREY';
            }
        } else if (gameState.sprite_mapping) {
            // Sprite mapping provided directly
            for (const [playerId, spriteColor] of Object.entries(gameState.sprite_mapping)) {
                this.playerSpriteMap[parseInt(playerId)] = spriteColor;
            }
        } else {
            // Legacy format - detect based on turn order
            if (gameState.turn_order) {
                gameState.turn_order.forEach((army, index) => {
                    // Map army names to sprite colors
                    const armyToSprite = {
                        'RED': 'RED',
                        'BLUE': 'BLUE',
                        'GREEN': 'GREEN',
                        'YELLOW': 'YELLOW',
                        'GREY': 'GREY',
                        'BLACK': 'GREY',  // Fallback
                        'ORANGE': 'YELLOW'  // Fallback
                    };
                    this.playerSpriteMap[index] = armyToSprite[army] || this.defaultMapping[index] || 'GREY';
                });
            } else {
                // Default 2-player setup
                this.playerSpriteMap = {
                    0: 'RED',
                    1: 'BLUE'
                };
            }
        }
    }
    
    /**
     * Get sprite color for a player
     * @param {number} playerId - Player ID
     * @returns {string} Sprite color (e.g., 'RED', 'BLUE')
     */
    getSpriteColor(playerId) {
        return this.playerSpriteMap[playerId] || 'GREY';
    }
    
    /**
     * Get sprite color from army name (backward compatibility)
     * @param {string} army - Army name (e.g., 'RED', 'BLUE')
     * @returns {string} Sprite color
     */
    getSpriteColorFromArmy(army) {
        // For backward compatibility when army names are used directly
        const validColors = ['RED', 'BLUE', 'GREEN', 'YELLOW', 'GREY'];
        if (validColors.includes(army)) {
            return army;
        }
        
        // Try to find player with this army
        for (const [playerId, spriteColor] of Object.entries(this.playerSpriteMap)) {
            if (spriteColor === army) {
                return spriteColor;
            }
        }
        
        return 'GREY';  // Default fallback
    }
    
    /**
     * Build unit sprite name
     * @param {Object} unit - Unit object
     * @returns {string} Sprite name (e.g., 'INFANTRY_RED_idle_0')
     */
    buildUnitSprite(unit) {
        let spriteColor;
        
        // Check if unit has player_id (new format)
        if (unit.player_id !== undefined) {
            spriteColor = this.getSpriteColor(unit.player_id);
        } else if (unit.army) {
            // Legacy format with army name
            spriteColor = this.getSpriteColorFromArmy(unit.army);
        } else {
            spriteColor = 'GREY';
        }
        
        // Determine state
        const state = (unit.has_moved || unit.done) ? 'unavailable' : 'idle';
        
        // Build sprite name
        return `${unit.type}_${spriteColor}_${state}_0`;
    }
    
    /**
     * Build building sprite name
     * @param {Object} mapTile - Map tile object
     * @returns {string} Sprite name (e.g., 'RED_FACTORY', 'CITY')
     */
    buildBuildingSprite(mapTile) {
        // Check if building is owned
        if (mapTile.player_id !== undefined && mapTile.player_id !== null) {
            // New format with player ID
            const spriteColor = this.getSpriteColor(mapTile.player_id);
            return `${spriteColor}_${mapTile.type}`;
        } else if (mapTile.army && mapTile.army !== 'NEUTRAL') {
            // Legacy format with army name
            const spriteColor = this.getSpriteColorFromArmy(mapTile.army);
            return `${spriteColor}_${mapTile.type}`;
        } else {
            // Neutral building
            return mapTile.type;
        }
    }
    
    /**
     * Get player display information
     * @param {number} playerId - Player ID
     * @returns {Object} Player info with name and color
     */
    getPlayerInfo(playerId) {
        const player = this.players[playerId];
        if (player) {
            return {
                name: player.name || `Player ${playerId + 1}`,
                color: player.color || this.getSpriteColor(playerId),
                spriteColor: this.getSpriteColor(playerId)
            };
        }
        
        // Fallback for legacy format
        const spriteColor = this.getSpriteColor(playerId);
        return {
            name: `${spriteColor} Army`,
            color: spriteColor.charAt(0) + spriteColor.slice(1).toLowerCase(),
            spriteColor: spriteColor
        };
    }
}

// Create global instance
window.spriteMapper = new SpriteMapper();