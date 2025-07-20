/**
 * Click Handler Test Suite
 * Tests all click handling functionality
 */

class ClickHandlerTests {
    constructor() {
        this.results = [];
        this.currentTest = null;
    }

    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️';
        console.log(`${prefix} [${timestamp}] ${message}`);
        
        if (this.currentTest) {
            this.currentTest.logs.push({ message, type, timestamp });
        }
    }

    async runAllTests() {
        console.log('🧪 Starting Click Handler Tests...\n');
        
        const tests = [
            this.testClickHandlerInitialization,
            this.testEmptyTileClick,
            this.testUnitSelection,
            this.testMovementClick,
            this.testProductionBuildingClick,
            this.testAttackClick,
            this.testAltClickHandler,
            this.testClickPriorities
        ];

        for (const test of tests) {
            await this.runTest(test.bind(this));
        }

        this.printResults();
    }

    async runTest(testFn) {
        const testName = testFn.name;
        this.currentTest = {
            name: testName,
            logs: [],
            passed: false,
            error: null
        };

        try {
            this.log(`Running test: ${testName}`);
            await testFn();
            this.currentTest.passed = true;
            this.log(`Test passed: ${testName}`, 'success');
        } catch (error) {
            this.currentTest.error = error;
            this.log(`Test failed: ${testName} - ${error.message}`, 'error');
        }

        this.results.push(this.currentTest);
        this.currentTest = null;
        console.log(''); // Add spacing between tests
    }

    // Helper to simulate a click event
    simulateClick(x, y, options = {}) {
        const canvas = document.querySelector('#draw canvas');
        if (!canvas) {
            throw new Error('Canvas not found');
        }

        const event = new MouseEvent('click', {
            bubbles: true,
            cancelable: true,
            view: window,
            clientX: x,
            clientY: y,
            offsetX: x,
            offsetY: y,
            ...options
        });

        canvas.dispatchEvent(event);
        return event;
    }

    // Test 1: Click handler initialization
    async testClickHandlerInitialization() {
        // Check if click handler is loaded
        if (!window.clickHandler) {
            throw new Error('Click handler not loaded');
        }

        // Check if required functions exist
        const requiredFunctions = ['register', 'process', 'initialize', 'clearHighlights'];
        for (const fn of requiredFunctions) {
            if (typeof window.clickHandler[fn] !== 'function') {
                throw new Error(`Missing function: clickHandler.${fn}`);
            }
        }

        // Check if canvas has click handler attached
        const canvas = document.querySelector('#draw canvas');
        if (!canvas) {
            throw new Error('Canvas not found');
        }

        if (!canvas.onclick) {
            throw new Error('Canvas onclick not set');
        }

        this.log('Click handler properly initialized');
    }

    // Test 2: Empty tile click
    async testEmptyTileClick() {
        // Mock an empty tile
        const originalTileAt = window.tileAt;
        window.tileAt = (x, y) => ({
            x: Math.floor(x / 16),
            y: Math.floor(y / 16),
            mapTile: { type: 'PLAIN', army: null },
            unit: null
        });

        // Clear any existing selection
        if (window.board) {
            window.board.selected = { x: 5, y: 5, unit: { army: 'RED' } };
        }

        // Click on empty tile
        this.simulateClick(100, 100);

        // Check that selection was cleared
        if (window.board && window.board.selected !== null) {
            throw new Error('Selection not cleared on empty tile click');
        }

        this.log('Empty tile click handled correctly');
        window.tileAt = originalTileAt;
    }

    // Test 3: Unit selection
    async testUnitSelection() {
        const originalTileAt = window.tileAt;
        
        // Mock a tile with a unit
        window.tileAt = (x, y) => ({
            x: 3,
            y: 3,
            mapTile: { type: 'PLAIN', army: null },
            unit: {
                type: 'INFANTRY',
                army: 'RED',
                hp: 10,
                can_move: true,
                can_attack: true
            }
        });

        // Set current turn
        if (window.board) {
            window.board.current_turn = 'RED';
            window.board.selected = null;
        }

        // Click on unit
        this.simulateClick(48, 48); // 3 * 16

        // Check that unit was selected
        if (!window.board || !window.board.selected) {
            throw new Error('Unit not selected');
        }

        if (window.board.selected.x !== 3 || window.board.selected.y !== 3) {
            throw new Error('Wrong unit selected');
        }

        this.log('Unit selection handled correctly');
        window.tileAt = originalTileAt;
    }

    // Test 4: Movement click
    async testMovementClick() {
        const originalTileAt = window.tileAt;
        
        // Set up a selected unit
        if (window.board) {
            window.board.selected = {
                x: 2,
                y: 2,
                unit: { type: 'INFANTRY', army: 'RED', can_move: true }
            };
            window.board.current_turn = 'RED';
        }

        // Mock movement highlights
        window.movementHighlights = [
            { x: 3, y: 2 },
            { x: 2, y: 3 },
            { x: 1, y: 2 },
            { x: 2, y: 1 }
        ];

        // Mock a movement destination tile
        window.tileAt = (x, y) => ({
            x: 3,
            y: 2,
            mapTile: { type: 'PLAIN', army: null },
            unit: null,
            can_be_moved_to: true
        });

        // Mock unitMove function
        let moveExecuted = false;
        window.unitMove = (tile) => {
            moveExecuted = true;
            this.log(`Unit move executed to (${tile.x}, ${tile.y})`);
        };

        // Click on movement highlight
        this.simulateClick(48, 32); // 3 * 16, 2 * 16

        if (!moveExecuted) {
            throw new Error('Movement not executed');
        }

        this.log('Movement click handled correctly');
        window.tileAt = originalTileAt;
    }

    // Test 5: Production building click
    async testProductionBuildingClick() {
        const originalTileAt = window.tileAt;
        
        // Mock a factory tile
        window.tileAt = (x, y) => ({
            x: 5,
            y: 5,
            mapTile: { 
                type: 'FACTORY', 
                army: 'RED'
            },
            unit: null
        });

        // Set current turn and clear selection
        if (window.board) {
            window.board.current_turn = 'RED';
            window.board.selected = null;
        }

        // Mock unitCreate function
        let createCalled = false;
        window.unitCreate = (tile) => {
            createCalled = true;
            this.log(`Unit create called for ${tile.mapTile.type}`);
        };

        // Click on factory
        this.simulateClick(80, 80); // 5 * 16

        if (!createCalled) {
            throw new Error('Unit create not called for factory');
        }

        this.log('Production building click handled correctly');
        window.tileAt = originalTileAt;
    }

    // Test 6: Attack click
    async testAttackClick() {
        const originalTileAt = window.tileAt;
        
        // Set up attacking unit
        if (window.board) {
            window.board.selected = {
                x: 4,
                y: 4,
                unit: { type: 'INFANTRY', army: 'RED', can_attack: true }
            };
            window.board.current_turn = 'RED';
        }

        // Set up attack highlights
        if (!window.gameState) window.gameState = {};
        window.gameState.attackHighlights = [
            { x: 5, y: 4 },
            { x: 4, y: 5 }
        ];

        // Mock enemy unit tile
        window.tileAt = (x, y) => ({
            x: 5,
            y: 4,
            mapTile: { type: 'PLAIN', army: null },
            unit: {
                type: 'INFANTRY',
                army: 'BLUE',
                hp: 10
            }
        });

        // Mock executeAttack
        let attackExecuted = false;
        window.executeAttack = (tile) => {
            attackExecuted = true;
            this.log(`Attack executed on unit at (${tile.x}, ${tile.y})`);
        };

        // Click on enemy unit
        this.simulateClick(80, 64); // 5 * 16, 4 * 16

        if (!attackExecuted) {
            throw new Error('Attack not executed');
        }

        this.log('Attack click handled correctly');
        window.tileAt = originalTileAt;
    }

    // Test 7: Alt-click handler
    async testAltClickHandler() {
        const originalTileAt = window.tileAt;
        
        // Mock a transport unit with cargo
        window.tileAt = (x, y) => ({
            x: 6,
            y: 6,
            mapTile: { type: 'PLAIN', army: null },
            unit: {
                type: 'APC',
                army: 'RED',
                cargo: [{ type: 'INFANTRY', hp: 10 }]
            }
        });

        // Mock transport functions
        window.isTransportUnit = (unit) => unit.type === 'APC';
        
        let altClickHandled = false;
        window.handleTransportAltClick = (tile, event) => {
            altClickHandled = true;
            this.log('Transport alt-click handled');
            return true;
        };

        // Alt-click on transport
        this.simulateClick(96, 96, { altKey: true });

        if (!altClickHandled) {
            throw new Error('Alt-click not handled for transport');
        }

        this.log('Alt-click handler working correctly');
        window.tileAt = originalTileAt;
    }

    // Test 8: Click priority system
    async testClickPriorities() {
        // Register test handlers
        const handlersTriggered = [];

        // High priority modal handler
        window.clickHandler.register('modals', {
            name: 'test-modal',
            priority: 0,
            condition: () => true,
            handle: () => {
                handlersTriggered.push('modal');
                return false; // Don't consume
            }
        });

        // Lower priority selection handler
        window.clickHandler.register('selection', {
            name: 'test-selection',
            priority: 10,
            condition: () => true,
            handle: () => {
                handlersTriggered.push('selection');
                return true; // Consume
            }
        });

        // Simulate a click
        this.simulateClick(50, 50);

        // Check order
        if (handlersTriggered[0] !== 'modal') {
            throw new Error('Modal handler not triggered first');
        }

        if (handlersTriggered.length !== 2 || handlersTriggered[1] !== 'selection') {
            throw new Error('Selection handler not triggered or click not consumed properly');
        }

        this.log('Click priority system working correctly');
    }

    // Print test results
    printResults() {
        console.log('\n📊 Test Results Summary:');
        console.log('========================');
        
        const passed = this.results.filter(r => r.passed).length;
        const failed = this.results.filter(r => !r.passed).length;
        const total = this.results.length;
        
        console.log(`Total Tests: ${total}`);
        console.log(`✅ Passed: ${passed}`);
        console.log(`❌ Failed: ${failed}`);
        console.log(`Success Rate: ${((passed / total) * 100).toFixed(1)}%`);
        
        if (failed > 0) {
            console.log('\n❌ Failed Tests:');
            this.results.filter(r => !r.passed).forEach(result => {
                console.log(`\n- ${result.name}`);
                console.log(`  Error: ${result.error.message}`);
            });
        }
        
        console.log('\n✅ All tests completed!');
    }
}

// Export for use
window.ClickHandlerTests = ClickHandlerTests;

// Auto-run tests if requested
if (window.location.search.includes('runClickTests=true')) {
    console.log('Auto-running click handler tests...');
    setTimeout(() => {
        const tester = new ClickHandlerTests();
        tester.runAllTests();
    }, 4000); // Wait for everything to load
}