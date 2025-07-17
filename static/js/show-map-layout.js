/**
 * Show the map layout and clickable buildings
 */

window.showMapLayout = function() {
    console.log('=== MAP LAYOUT ===');
    
    if (!window.board || !window.board.grid) {
        console.error('Board not loaded!');
        return;
    }
    
    // Get map dimensions
    const width = window.board.width;
    const height = window.board.height;
    console.log(`Map size: ${width}x${height}`);
    console.log(`Current turn: ${window.board.current_turn}`);
    console.log(`Funds: RED=${window.board.red_funds}, BLUE=${window.board.blue_funds}`);
    
    // Find all production buildings
    const productionBuildings = window.board.grid.filter(tile => 
        tile.mapTile && (
            tile.mapTile.type === 'FACTORY' || 
            tile.mapTile.type === 'AIRPORT' || 
            tile.mapTile.type === 'PORT'
        )
    );
    
    console.log(`\n🏭 PRODUCTION BUILDINGS (${productionBuildings.length} total):`);
    
    // Group by type
    const byType = {
        FACTORY: [],
        AIRPORT: [],
        PORT: []
    };
    
    productionBuildings.forEach(tile => {
        byType[tile.mapTile.type].push(tile);
    });
    
    // Show each type
    Object.entries(byType).forEach(([type, buildings]) => {
        if (buildings.length > 0) {
            console.log(`\n${type}S (${buildings.length}):`);
            buildings.forEach(b => {
                const owner = b.mapTile.army || 'NEUTRAL';
                const occupied = b.unit ? `has ${b.unit.type}` : 'empty';
                const canUse = b.mapTile.army === window.board.current_turn && !b.unit;
                console.log(`- (${b.x},${b.y}) ${owner} ${occupied} ${canUse ? '✅ CLICK HERE' : ''}`);
            });
        }
    });
    
    // Show clickable options for current player
    const myBuildings = productionBuildings.filter(b => 
        b.mapTile.army === window.board.current_turn && !b.unit
    );
    
    if (myBuildings.length > 0) {
        console.log(`\n✅ YOU CAN CLICK THESE ${window.board.current_turn} BUILDINGS:`);
        myBuildings.forEach(b => {
            console.log(`- ${b.mapTile.type} at (${b.x}, ${b.y})`);
            
            // Calculate pixel position for clicking
            const pixelX = b.x * 16 + 8;
            const pixelY = b.y * 16 + 16 + 8; // +16 for header offset
            console.log(`  Canvas click position: (${pixelX}, ${pixelY})`);
        });
        
        // Offer to test click
        if (myBuildings.length > 0) {
            const first = myBuildings[0];
            window.testProductionClick = function() {
                console.log(`Testing click on ${first.mapTile.type} at (${first.x}, ${first.y})...`);
                const canvas = document.querySelector('#draw canvas');
                if (canvas) {
                    const event = new MouseEvent('click', {
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        offsetX: first.x * 16 + 8,
                        offsetY: first.y * 16 + 16 + 8
                    });
                    canvas.dispatchEvent(event);
                }
            };
            console.log('\n💡 Run testProductionClick() to test clicking the first available building');
        }
    } else {
        console.log(`\n❌ No ${window.board.current_turn} production buildings available to click`);
        console.log('Either all are occupied or none belong to you');
    }
    
    // Show what's at (0,4) since we were looking there
    console.log('\n📍 What\'s at (0,4)?');
    const tile04 = window.board.grid.find(t => t.x === 0 && t.y === 4);
    if (tile04) {
        console.log(`- Terrain: ${tile04.mapTile?.type}`);
        console.log(`- Army: ${tile04.mapTile?.army || 'none'}`);
        console.log(`- Unit: ${tile04.unit?.type || 'none'}`);
    }
};

// Auto-run
setTimeout(() => {
    window.showMapLayout();
}, 1000);