// Comprehensive Click Detection Test Script
// Run this in the browser console while the game is loaded

async function runClickTests() {
    console.log('=== STARTING CLICK DETECTION TESTS ===\n');
    
    // Test 1: Check if click handler is properly initialized
    console.log('TEST 1: Click Handler Initialization');
    const canvas = document.querySelector('#draw canvas');
    if (!canvas) {
        console.error('❌ Canvas not found!');
        return;
    }
    console.log('✅ Canvas found');
    
    // Check if click handler is attached
    if (canvas.onclick && canvas.onclick.name === 'centralizedClickHandler') {
        console.log('✅ Centralized click handler is attached');
    } else {
        console.error('❌ Click handler not properly attached');
        console.log('Current onclick:', canvas.onclick);
    }
    
    // Test 2: Check if board and game state are loaded
    console.log('\nTEST 2: Game State Check');
    if (!window.board) {
        console.error('❌ Board not loaded');
        return;
    }
    console.log('✅ Board loaded');
    console.log(`   Current turn: ${window.board.current_turn}`);
    console.log(`   Board size: ${window.board.width}x${window.board.height}`);
    
    // Test 3: Find clickable elements
    console.log('\nTEST 3: Finding Clickable Elements');
    
    // Find factories
    const factories = window.board.grid.filter(t => 
        ['FACTORY', 'AIRPORT', 'PORT'].includes(t.mapTile?.type) &&
        t.mapTile.army === window.board.current_turn &&
        !t.unit
    );
    console.log(`Found ${factories.length} production buildings for ${window.board.current_turn}:`);
    factories.forEach(f => {
        console.log(`   ${f.mapTile.type} at (${f.x}, ${f.y})`);
    });
    
    // Find units
    const units = window.board.grid.filter(t => 
        t.unit && t.unit.army === window.board.current_turn
    );
    console.log(`\nFound ${units.length} units for ${window.board.current_turn}:`);
    units.slice(0, 5).forEach(u => {
        console.log(`   ${u.unit.type} at (${u.x}, ${u.y}) - can_move: ${u.unit.can_move}`);
    });
    
    // Test 4: Test tileAt function
    console.log('\nTEST 4: Testing tileAt Function');
    if (factories.length > 0) {
        const factory = factories[0];
        const pixelX = factory.x * window.TILESIZE + window.TILESIZE/2;
        const pixelY = factory.y * window.TILESIZE + window.TILESIZE/2;
        
        console.log(`Testing pixel coords (${pixelX}, ${pixelY}) for factory at (${factory.x}, ${factory.y})`);
        const tile = window.tileAt(pixelX, pixelY);
        
        if (tile) {
            console.log(`✅ tileAt returned tile at (${tile.x}, ${tile.y})`);
            if (tile.x === factory.x && tile.y === factory.y) {
                console.log('✅ Coordinates match!');
            } else {
                console.error('❌ Coordinate mismatch!');
            }
        } else {
            console.error('❌ tileAt returned null');
        }
    }
    
    // Test 5: Simulate a factory click
    console.log('\nTEST 5: Simulating Factory Click');
    if (factories.length > 0) {
        const factory = factories[0];
        console.log(`Simulating click on ${factory.mapTile.type} at (${factory.x}, ${factory.y})`);
        
        // Create click event
        const rect = canvas.getBoundingClientRect();
        const pixelX = factory.x * window.TILESIZE + window.TILESIZE/2;
        const pixelY = factory.y * window.TILESIZE + window.TILESIZE/2;
        
        const event = new MouseEvent('click', {
            view: window,
            bubbles: true,
            cancelable: true,
            clientX: rect.left + pixelX,
            clientY: rect.top + pixelY
        });
        
        // Add offset properties
        Object.defineProperty(event, 'offsetX', { value: pixelX });
        Object.defineProperty(event, 'offsetY', { value: pixelY });
        
        // Enable debug logging temporarily
        const originalLog = console.log;
        const logs = [];
        console.log = (...args) => {
            logs.push(args.join(' '));
            originalLog.apply(console, args);
        };
        
        canvas.dispatchEvent(event);
        
        console.log = originalLog;
        
        // Check if production menu appeared
        setTimeout(() => {
            const productionModal = document.querySelector('.production-modal, #production-menu, .unit-create-modal');
            if (productionModal) {
                console.log('✅ Production menu opened!');
            } else {
                console.error('❌ Production menu did not open');
                console.log('Debug logs:', logs);
            }
        }, 100);
    }
    
    // Test 6: Test processClick directly
    console.log('\nTEST 6: Testing processClick Directly');
    if (window.clickHandler && factories.length > 0) {
        const factory = factories[0];
        console.log(`Calling processClick directly on factory at (${factory.x}, ${factory.y})`);
        
        const mockEvent = { 
            offsetX: factory.x * window.TILESIZE, 
            offsetY: factory.y * window.TILESIZE,
            ctrlKey: false,
            altKey: false,
            shiftKey: false
        };
        
        const result = window.clickHandler.process(factory, mockEvent);
        console.log(`processClick returned: ${result}`);
    }
    
    console.log('\n=== TESTS COMPLETE ===');
}

// Run the tests
runClickTests();