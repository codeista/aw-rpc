/**
 * Testing & Debug Module - Development utilities and testing functions
 * Extracted from render.js as part of modularization effort
 */

import { jsonrpc } from './network.js';
import { getGameState } from './core.js';

// ===== SPRITE TESTING UTILITIES =====

/**
 * Debug sprite corrections data
 */
export function debugSpriteCorrections() {
    logger.debug('🔍 Checking sprite corrections...');
    
    if (!window.spriteCorrections) {
        logger.error('❌ No sprite corrections loaded!');
        logger.debug('Make sure to call loadSpriteCorrections() first');
        return;
    }
    
    logger.debug('✅ Sprite corrections loaded');
    logger.debug('Available states:', Object.keys(window.spriteCorrections));
    
    // Test specific unit types
    const testUnits = [
        'INFANTRY_RED_idle_0',
        'INFANTRY_BLUE_idle_0', 
        'TANK_RED_idle_0',
        'INFANTRY_RED_unavailable_0',
        'INFANTRY_BLUE_unavailable_0'
    ];
    
    testUnits.forEach(key => {
        const idle = window.spriteCorrections.idle?.[key];
        const unavailable = window.spriteCorrections.unavailable?.[key];
        
        if (idle) {
            logger.debug(`✅ Found ${key} in idle: x=${idle.x}, y=${idle.y}`);
        }
        if (unavailable) {
            logger.debug(`✅ Found ${key} in unavailable: x=${unavailable.x}, y=${unavailable.y}`);
        }
        if (!idle && !unavailable) {
            logger.debug(`❌ Missing ${key}`);
        }
    });
}

/**
 * Test sprite states for all units on the board
 */
export function testSpriteStates() {
    if (!window.board) {
        logger.debug('❌ No board available');
        return;
    }
    
    logger.debug('=' + '='.repeat(60));
    logger.debug('🧪 TESTING SPRITE STATES');
    logger.debug('=' + '='.repeat(60));
    
    const currentTurnUnits = [];
    
    // Find units for current turn
    window.board.grid.forEach(tile => {
        if (tile.unit && tile.unit.army === window.board.current_turn) {
            currentTurnUnits.push({tile, unit: tile.unit});
        }
    });
    
    logger.debug(`\n📊 Found ${currentTurnUnits.length} ${window.board.current_turn} units:`);
    
    currentTurnUnits.forEach(({tile, unit}) => {
        const canAct = unit.can_attack || unit.can_move || unit.can_capture;
        const spriteState = canAct ? 'idle' : 'unavailable';
        
        logger.debug(`   ${unit.type} at (${tile.x},${tile.y}):`);
        logger.debug(`      can_move: ${unit.can_move}, can_attack: ${unit.can_attack}`);
        logger.debug(`      sprite state: ${spriteState} (${canAct ? '✅ Available' : '🚫 Unavailable'})`);
    });
    
    logger.debug('\n💡 Run this function again after actions to verify state changes');
}

/**
 * Test sprite state for newly created units
 */
export function testNewUnitSprite() {
    logger.debug('🧪 Testing new unit sprite state');
    logger.debug('A newly created unit should show as unavailable (grayed out)');
    logger.debug('\nCreate a unit and run testSpriteStates() to verify!');
}

// ===== UNIT CREATION TESTING =====

/**
 * Test all unit sprite rendering
 */
export function testAllUnitSprites() {
    const unitTypes = [
        'INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 'NEOTANK', 'MEGATANK',
        'APC', 'ARTILLERY', 'ROCKET', 'ANTIAIR', 'MISSILE', 'PIPERUNNER',
        'FIGHTER', 'BOMBER', 'BCOPTER', 'TCOPTER', 'STEALTH', 'BLACKBOMB',
        'BATTLESHIP', 'CRUISER', 'LANDER', 'SUB', 'CARRIER', 'BLACKBOAT'
    ];
    
    logger.debug('🎨 Testing all unit sprites...');
    
    unitTypes.forEach(unitType => {
        const spriteKey = `${unitType}_RED_idle_0`;
        const hasSprite = window.spriteCorrections?.idle?.[spriteKey];
        logger.debug(`${unitType}: ${hasSprite ? '✅' : '❌'}`);
    });
}

/**
 * Test unit creation for specific army and type
 */
export function testUnitCreation(army = 'RED', unitType = 'INFANTRY', x = 5, y = 5) {
    logger.debug(`🏭 Testing ${army} ${unitType} creation at (${x}, ${y})`);
    
    jsonrpc('unit_create', {
        army: army,
        unit_type: unitType,
        x: x,
        y: y
    }).then(result => {
        logger.debug('✅ Unit creation result:', result);
        
        // Test sprite state after creation
        setTimeout(() => {
            testSpriteStates();
        }, 500);
    }).catch(error => {
        logger.error('❌ Unit creation failed:', error);
    });
}

/**
 * Test creating land units
 */
export function testLandUnits() {
    const landUnits = ['INFANTRY', 'MECH', 'RECON', 'TANK', 'APC'];
    landUnits.forEach((unit, index) => {
        setTimeout(() => testUnitCreation('RED', unit, 2 + index, 3), index * 200);
    });
}

/**
 * Test creating air units
 */
export function testAirUnits() {
    const airUnits = ['BCOPTER', 'TCOPTER', 'FIGHTER', 'BOMBER'];
    airUnits.forEach((unit, index) => {
        setTimeout(() => testUnitCreation('BLUE', unit, 6 + index, 3), index * 200);
    });
}

/**
 * Test creating sea units
 */
export function testSeaUnits() {
    const seaUnits = ['BATTLESHIP', 'CRUISER', 'LANDER', 'SUB'];
    seaUnits.forEach((unit, index) => {
        setTimeout(() => testUnitCreation('RED', unit, 2 + index, 7), index * 200);
    });
}

/**
 * Test creating all unit types
 */
export function testAllUnits() {
    logger.debug('🏭 Testing all unit types...');
    testLandUnits();
    setTimeout(testAirUnits, 1500);
    setTimeout(testSeaUnits, 3000);
}

// ===== GAME FLOW TESTING =====

/**
 * Simulate game flow for testing
 */
export function simulateGameFlow() {
    logger.debug('🎮 STARTING GAME FLOW SIMULATION');
    logger.debug('=' + '='.repeat(60));
    
    if (!window.board || !window.board.grid) {
        logger.debug('❌ No board available for simulation');
        return;
    }
    
    // Find a unit to simulate with
    const unitTile = window.board.grid.find(tile => 
        tile.unit && 
        tile.unit.army === window.board.current_turn &&
        (tile.unit.can_move || tile.unit.can_attack)
    );
    
    if (!unitTile) {
        logger.debug('❌ No units available to simulate');
        return;
    }
    
    logger.debug(`\n📍 Found ${unitTile.unit.army} ${unitTile.unit.type} at (${unitTile.x}, ${unitTile.y})`);
    logger.debug(`   can_move: ${unitTile.unit.can_move}`);
    logger.debug(`   can_attack: ${unitTile.unit.can_attack}`);
    
    logger.debug('\n🖱️ STEP 1: Selecting unit...');
    
    // Simulate unit selection
    if (window.advanceWarsUnitSelect) {
        window.advanceWarsUnitSelect(unitTile);
        
        setTimeout(() => {
            const gameState = getGameState();
            logger.debug(`   Selected unit: ${gameState.selectedUnit ? 'Yes' : 'No'}`);
            
            if (gameState.selectedUnit) {
                logger.debug(`   Coordinates: (${gameState.selectedUnit.x}, ${gameState.selectedUnit.y})`);
                
                // Test movement if possible
                if (unitTile.unit.can_move) {
                    logger.debug('\n🚶 STEP 2: Testing movement...');
                    // Find valid move position
                    const validMoves = window.board.grid.filter(tile => tile.can_be_moved_to);
                    if (validMoves.length > 0) {
                        const targetTile = validMoves[0];
                        logger.debug(`   Moving to (${targetTile.x}, ${targetTile.y})`);
                        simulateClick(targetTile.x, targetTile.y);
                    }
                }
            }
            
            // Final state check
            setTimeout(() => {
                logger.debug('\n📊 FINAL STATE CHECK:');
                logger.debug(`   Board selected: ${window.board.selected ? 'Yes' : 'No'}`);
                logger.debug(`   Game state selected: ${getGameState().selectedUnit ? 'Yes' : 'No'}`);
                logger.debug(`   Selected unit: ${getGameState().selectedUnit ? 'Yes' : 'No'}`);
                logger.debug('\n✅ SIMULATION COMPLETE');
            }, 1000);
            
        }, 500);
    }
}

/**
 * Simulate a click at specific coordinates
 */
export function simulateClick(x, y) {
    logger.debug(`   🖱️ Simulating click at tile (${x}, ${y})`);
    
    if (!window.board || !window.board.grid) {
        logger.debug('   ❌ No board available');
        return;
    }
    
    const tile = window.board.grid.find(t => t.x === x && t.y === y);
    
    if (!tile) {
        logger.debug(`   ❌ No tile found at (${x}, ${y})`);
        return;
    }
    
    if (tile.unit) {
        logger.debug(`   → Clicking on ${tile.unit.army} ${tile.unit.type}`);
    } else {
        logger.debug(`   → Clicking on empty tile (terrain: ${tile.mapTile?.type || 'unknown'})`);
    }
    
    // Simulate the click through the canvas system
    if (window.canvasClick) {
        const fakeEvent = {
            offsetX: (x * window.TILESIZE) + (window.TILESIZE / 2),
            offsetY: (y * window.TILESIZE) + (window.TILESIZE / 2),
            preventDefault: () => {},
            stopPropagation: () => {}
        };
        
        window.canvasClick(fakeEvent);
    }
}

// ===== BOARD ANALYSIS =====

/**
 * Force a complete refresh of the game state
 */
export function forceRefresh() {
    logger.debug('🔄 Forcing complete refresh...');
    
    if (window.update) {
        window.update();
    }
    
    if (window.rerender) {
        window.rerender();
    }
    
    // Clear and reinitialize state
    const gameState = getGameState();
    gameState.selectedUnit = null;
    gameState.movementPhase = false;
    gameState.showingAttackTargets = false;
    gameState.attackHighlights = [];
    
    logger.debug('✅ Refresh complete');
}

/**
 * Analyze current board state
 */
export function analyzeBoardState() {
    if (!window.board) {
        logger.debug('❌ No board available');
        return;
    }
    
    logger.debug('=' + '='.repeat(60));
    logger.debug('📊 BOARD STATE ANALYSIS');
    logger.debug('=' + '='.repeat(60));
    
    const stats = {
        total_tiles: window.board.grid.length,
        units_by_army: {},
        terrain_types: {},
        properties_by_army: {},
        current_turn: window.board.current_turn,
        game_active: window.board.game_active
    };
    
    // Analyze tiles
    window.board.grid.forEach(tile => {
        // Count units by army
        if (tile.unit) {
            const army = tile.unit.army;
            stats.units_by_army[army] = (stats.units_by_army[army] || 0) + 1;
        }
        
        // Count terrain types
        if (tile.mapTile) {
            const terrain = tile.mapTile.type;
            stats.terrain_types[terrain] = (stats.terrain_types[terrain] || 0) + 1;
        }
        
        // Count properties by army
        if (tile.mapTile && tile.mapTile.army) {
            const army = tile.mapTile.army;
            stats.properties_by_army[army] = (stats.properties_by_army[army] || 0) + 1;
        }
    });
    
    logger.debug('📈 Statistics:');
    logger.debug('  Total tiles:', stats.total_tiles);
    logger.debug('  Current turn:', stats.current_turn);
    logger.debug('  Game active:', stats.game_active);
    logger.debug('  Units by army:', stats.units_by_army);
    logger.debug('  Properties by army:', stats.properties_by_army);
    logger.debug('  Terrain distribution:', stats.terrain_types);
    
    return stats;
}

// ===== PERFORMANCE TESTING =====

/**
 * Test rendering performance
 */
export function testRenderingPerformance() {
    logger.debug('⚡ Testing rendering performance...');
    
    const startTime = performance.now();
    let frameCount = 0;
    
    function measureFrame() {
        frameCount++;
        
        if (frameCount < 60) {
            requestAnimationFrame(measureFrame);
        } else {
            const endTime = performance.now();
            const totalTime = endTime - startTime;
            const fps = (frameCount / totalTime) * 1000;
            
            logger.debug(`📊 Performance Results:`);
            logger.debug(`  Frames: ${frameCount}`);
            logger.debug(`  Total time: ${totalTime.toFixed(2)}ms`);
            logger.debug(`  Average FPS: ${fps.toFixed(2)}`);
        }
    }
    
    requestAnimationFrame(measureFrame);
}

// ===== EXPORT TESTING UTILITIES TO GLOBAL SCOPE =====

// Make testing functions available globally for console use
window.debugSpriteCorrections = debugSpriteCorrections;
window.testSpriteStates = testSpriteStates;
window.testNewUnitSprite = testNewUnitSprite;
window.testAllUnitSprites = testAllUnitSprites;
window.testUnitCreation = testUnitCreation;
window.testLandUnits = testLandUnits;
window.testAirUnits = testAirUnits;
window.testSeaUnits = testSeaUnits;
window.testAllUnits = testAllUnits;
window.simulateGameFlow = simulateGameFlow;
window.simulateClick = simulateClick;
window.forceRefresh = forceRefresh;
window.analyzeBoardState = analyzeBoardState;
window.testRenderingPerformance = testRenderingPerformance;

// Add helpful tips to console
logger.debug('💡 Testing utilities loaded. Available functions:');
logger.debug('   debugSpriteCorrections() - Check sprite data');
logger.debug('   testSpriteStates() - Check unit availability states');
logger.debug('   testAllUnits() - Create test units of all types');
logger.debug('   simulateGameFlow() - Test game interaction flow');
logger.debug('   analyzeBoardState() - Get board statistics');
logger.debug('   testRenderingPerformance() - Measure FPS');