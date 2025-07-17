/**
 * Handler for individual sprite files (not part of main sprite sheet)
 */

console.log('🖼️ Individual Sprite Handler Loading...');

// Map of individual sprite files
window.individualSprites = {
    // GREEN STEALTH uses stealth.png for all frames
    'STEALTH_GREEN_idle_0': '/static/img/stealth.png',
    'STEALTH_GREEN_idle_1': '/static/img/stealth.png', 
    'STEALTH_GREEN_idle_2': '/static/img/stealth.png',
    'STEALTH_GREEN_unavailable_0': '/static/img/stealth.png',
    'STEALTH_GREEN_unavailable_1': '/static/img/stealth.png',
    'STEALTH_GREEN_unavailable_2': '/static/img/stealth.png'
};

// Preload individual sprites
window.individualSpriteImages = {};

function preloadIndividualSprites() {
    const uniqueImages = [...new Set(Object.values(window.individualSprites))];
    
    uniqueImages.forEach(src => {
        const img = new Image();
        img.onload = () => {
            console.log(`✅ Loaded individual sprite: ${src}`);
            window.individualSpriteImages[src] = img;
        };
        img.onerror = () => {
            console.error(`❌ Failed to load sprite: ${src}`);
        };
        img.src = src;
    });
}

// Override sprite drawing for individual sprites
const originalDrawSprite = window.drawUnitSprite;
if (originalDrawSprite) {
    window.drawUnitSprite = function(ctx, tile, x, y) {
        if (!tile.unit) return originalDrawSprite.apply(this, arguments);
        
        const unit = tile.unit;
        const state = (unit.can_move || unit.can_attack) ? 'idle' : 'unavailable';
        const spriteKey = `${unit.type}_${unit.army}_${state}_0`;
        
        // Check if this is an individual sprite
        if (window.individualSprites[spriteKey]) {
            const imgSrc = window.individualSprites[spriteKey];
            const img = window.individualSpriteImages[imgSrc];
            
            if (img && img.complete) {
                // Draw the individual sprite
                ctx.drawImage(img, x, y, 16, 16);
                return;
            }
        }
        
        // Fall back to original sprite sheet method
        return originalDrawSprite.apply(this, arguments);
    };
}

// Initialize on load
setTimeout(() => {
    preloadIndividualSprites();
    console.log('✅ Individual sprite handler ready');
}, 100);

// Helper to add more individual sprites
window.addIndividualSprite = function(unitType, army, state, frame, imagePath) {
    const key = `${unitType}_${army}_${state}_${frame}`;
    window.individualSprites[key] = imagePath;
    
    // Preload if not already loaded
    if (!window.individualSpriteImages[imagePath]) {
        const img = new Image();
        img.onload = () => {
            window.individualSpriteImages[imagePath] = img;
            console.log(`✅ Added sprite: ${key} -> ${imagePath}`);
        };
        img.src = imagePath;
    }
};

// Helper to add unavailable state with grayscale
window.addGrayscaleUnavailable = function(unitType, army, imagePath) {
    // For now, just use the same image
    // TODO: Apply grayscale filter
    for (let i = 0; i < 3; i++) {
        window.addIndividualSprite(unitType, army, 'unavailable', i, imagePath);
    }
};