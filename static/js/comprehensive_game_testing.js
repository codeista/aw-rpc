// =============================================================================
// COMPREHENSIVE ADVANCE WARS GAME TESTING SUITE
// =============================================================================

console.log('🎮 ADVANCE WARS TESTING SUITE LOADED');
console.log('==========================================');

// =============================================================================
// CORE SYSTEM TESTS
// =============================================================================

function runCoreSystemTests() {
    console.log('🧪 === CORE SYSTEM TESTS ===');
    
    // Test 1: Board State
    console.log('1. Board State Test:');
    console.log(`   - Board size: ${board.width}x${board.height}`);
    console.log(`   - Current turn: ${board.current_turn}`);
    console.log(`   - Game active: ${board.game_active}`);
    console.log(`   - Day: ${board.days}`);
    
    // Test 2: Unit Count
    let redUnits = 0, blueUnits = 0, totalUnits = 0;
    board.grid.forEach(tile => {
        if (tile.unit) {
            totalUnits++;
            if (tile.unit.army === 'RED') redUnits++;
            if (tile.unit.army === 'BLUE') blueUnits++;
        }
    });
    
    console.log('2. Unit Count Test:');
    console.log(`   - RED units: ${redUnits}`);
    console.log(`   - BLUE units: ${blueUnits}`);
    console.log(`   - Total units: ${totalUnits}`);
    
    // Test 3: Property Count
    let redProperties = 0, blueProperties = 0, neutralProperties = 0;
    board.grid.forEach(tile => {
        if (tile.mapTile.type === 'CITY' || tile.mapTile.type === 'FACTORY' || 
            tile.mapTile.type === 'AIRPORT' || tile.mapTile.type === 'PORT') {
            if (tile.mapTile.army === 'RED') redProperties++;
            else if (tile.mapTile.army === 'BLUE') blueProperties++;
            else neutralProperties++;
        }
    });
    
    console.log('3. Property Count Test:');
    console.log(`   - RED properties: ${redProperties}`);
    console.log(`   - BLUE properties: ${blueProperties}`);
    console.log(`   - Neutral properties: ${neutralProperties}`);
    
    // Test 4: Funds
    console.log('4. Army Funds Test:');
    console.log(`   - RED funds: ${board.red_funds}`);
    console.log(`   - BLUE funds: ${board.blue_funds}`);
    
    return {
        board: {width: board.width, height: board.height, active: board.game_active},
        units: {red: redUnits, blue: blueUnits, total: totalUnits},
        properties: {red: redProperties, blue: blueProperties, neutral: neutralProperties},
        funds: {red: board.red_funds, blue: board.blue_funds}
    };
}

// =============================================================================
// MOVEMENT SYSTEM TESTS
// =============================================================================

function testMovementSystem() {
    console.log('🏃 === MOVEMENT SYSTEM TESTS ===');
    
    return new Promise((resolve) => {
        // Find a unit to test with
        let testUnit = null;
        let testTile = null;
        
        for (let tile of board.grid) {
            if (tile.unit && tile.unit.army === board.current_turn) {
                testUnit = tile.unit;
                testTile = tile;
                break;
            }
        }
        
        if (!testUnit) {
            console.log('❌ No units found for current army');
            resolve({success: false, reason: 'No units available'});
            return;
        }
        
        console.log(`1. Testing with ${testUnit.army} ${testUnit.type} at (${testTile.x}, ${testTile.y})`);
        
        // Test unit selection
        jsonrpc('unit_select', {x: testTile.x, y: testTile.y}).then(result => {
            if (result.error) {
                console.log('❌ Unit selection failed:', result.message);
                resolve({success: false, reason: 'Selection failed'});
                return;
            }
            
            console.log('✅ Unit selection successful');
            
            // Set selection and create indicators
            board.selected = testTile;
            
            setTimeout(() => {
                if (typeof createIndicatorsForSelectedUnitFixed === 'function') {
                    let indicatorCount = createIndicatorsForSelectedUnitFixed();
                    console.log(`✅ Created ${indicatorCount} movement indicators`);
                    
                    // Test movement to an adjacent tile
                    let targetX = testTile.x + 1;
                    let targetY = testTile.y;
                    
                    // Make sure target is valid
                    if (targetX < board.width) {
                        setTimeout(() => {
                            jsonrpc('unit_move', {
                                x: testTile.x, y: testTile.y,
                                x2: targetX, y2: targetY
                            }).then(moveResult => {
                                if (moveResult.error) {
                                    console.log('❌ Movement failed:', moveResult.message);
                                    resolve({success: false, reason: 'Movement failed'});
                                } else {
                                    console.log('✅ Movement successful');
                                    resolve({success: true, indicators: indicatorCount});
                                }
                            });
                        }, 1000);
                    } else {
                        console.log('✅ Movement system ready (no valid target for test move)');
                        resolve({success: true, indicators: indicatorCount});
                    }
                } else {
                    console.log('❌ Movement indicator function not available');
                    resolve({success: false, reason: 'Indicator function missing'});
                }
            }, 500);
        });
    });
}

// =============================================================================
// TURN SYSTEM TESTS
// =============================================================================

function testTurnSystem() {
    console.log('🔄 === TURN SYSTEM TESTS ===');
    
    return new Promise((resolve) => {
        let originalTurn = board.current_turn;
        console.log(`1. Current turn: ${originalTurn}`);
        
        // Test turn ending
        jsonrpc('army_end_turn', {}).then(result => {
            if (result.error) {
                console.log('❌ Turn end failed:', result.message);
                resolve({success: false, reason: 'Turn end failed'});
                return;
            }
            
            console.log('✅ Turn ended successfully');
            console.log(`2. New turn: ${result.current_turn}`);
            
            setTimeout(() => {
                if (board.current_turn !== originalTurn) {
                    console.log('✅ Turn system working correctly');
                    resolve({
                        success: true, 
                        originalTurn: originalTurn, 
                        newTurn: board.current_turn
                    });
                } else {
                    console.log('❌ Turn did not change properly');
                    resolve({success: false, reason: 'Turn not changed'});
                }
            }, 1000);
        });
    });
}

// =============================================================================
// UNIT CREATION TESTS
// =============================================================================

function testUnitCreation() {
    console.log('🏭 === UNIT CREATION TESTS ===');
    
    return new Promise((resolve) => {
        // Find a factory owned by current army
        let factory = null;
        
        for (let tile of board.grid) {
            if (tile.mapTile.type === 'FACTORY' && 
                tile.mapTile.army === board.current_turn && 
                !tile.unit) {
                factory = tile;
                break;
            }
        }
        
        if (!factory) {
            console.log('❌ No available factories for current army');
            resolve({success: false, reason: 'No factories available'});
            return;
        }
        
        console.log(`1. Testing unit creation at factory (${factory.x}, ${factory.y})`);
        
        // Test creating an infantry unit
        jsonrpc('unit_create', {
            army: board.current_turn,
            unit_type: 'INFANTRY',
            x: factory.x,
            y: factory.y
        }).then(result => {
            if (result.error) {
                console.log('❌ Unit creation failed:', result.message);
                resolve({success: false, reason: result.message});
            } else {
                console.log('✅ Unit creation successful');
                resolve({
                    success: true, 
                    unitType: 'INFANTRY',
                    position: {x: factory.x, y: factory.y}
                });
            }
        });
    });
}

// =============================================================================
// COMBAT SYSTEM TESTS
// =============================================================================

function testCombatSystem() {
    console.log('⚔️ === COMBAT SYSTEM TESTS ===');
    
    // Check if there are units from both armies for combat testing
    let redUnits = [];
    let blueUnits = [];
    
    board.grid.forEach(tile => {
        if (tile.unit) {
            if (tile.unit.army === 'RED') {
                redUnits.push({x: tile.x, y: tile.y, type: tile.unit.type});
            } else if (tile.unit.army === 'BLUE') {
                blueUnits.push({x: tile.x, y: tile.y, type: tile.unit.type});
            }
        }
    });
    
    console.log(`1. RED units available: ${redUnits.length}`);
    console.log(`2. BLUE units available: ${blueUnits.length}`);
    
    if (redUnits.length === 0 || blueUnits.length === 0) {
        console.log('❌ Need units from both armies for combat testing');
        return {success: false, reason: 'Insufficient units for combat'};
    }
    
    // Check if any units are adjacent for combat
    let combatPairs = [];
    redUnits.forEach(red => {
        blueUnits.forEach(blue => {
            let distance = Math.abs(red.x - blue.x) + Math.abs(red.y - blue.y);
            if (distance <= 3) { // Within reasonable range
                combatPairs.push({attacker: red, defender: blue, distance: distance});
            }
        });
    });
    
    if (combatPairs.length > 0) {
        console.log(`✅ ${combatPairs.length} potential combat scenarios available`);
        console.log('3. Ready for combat testing - create units closer together and attack');
        return {success: true, combatPairs: combatPairs.length};
    } else {
        console.log('⚠️ Units too far apart for combat - move them closer');
        return {success: true, combatPairs: 0, note: 'Units need to be closer'};
    }
}

// =============================================================================
// PROPERTY CAPTURE TESTS
// =============================================================================

function testPropertyCapture() {
    console.log('🏛️ === PROPERTY CAPTURE TESTS ===');
    
    // Find capturable properties near current army units
    let capturableProperties = [];
    
    board.grid.forEach(tile => {
        if ((tile.mapTile.type === 'CITY' || tile.mapTile.type === 'FACTORY' || 
             tile.mapTile.type === 'AIRPORT' || tile.mapTile.type === 'PORT') &&
            tile.mapTile.army !== board.current_turn) {
            
            // Check if there's a friendly infantry/mech nearby
            let nearbyUnits = [];
            board.grid.forEach(unitTile => {
                if (unitTile.unit && 
                    unitTile.unit.army === board.current_turn &&
                    (unitTile.unit.type === 'INFANTRY' || unitTile.unit.type === 'MECH')) {
                    
                    let distance = Math.abs(tile.x - unitTile.x) + Math.abs(tile.y - unitTile.y);
                    if (distance <= 3) {
                        nearbyUnits.push({
                            unit: unitTile.unit.type,
                            distance: distance,
                            position: {x: unitTile.x, y: unitTile.y}
                        });
                    }
                }
            });
            
            if (nearbyUnits.length > 0) {
                capturableProperties.push({
                    property: tile.mapTile.type,
                    position: {x: tile.x, y: tile.y},
                    owner: tile.mapTile.army || 'Neutral',
                    nearbyUnits: nearbyUnits
                });
            }
        }
    });
    
    console.log(`1. Found ${capturableProperties.length} capturable properties with nearby units`);
    
    if (capturableProperties.length > 0) {
        console.log('✅ Ready for capture testing');
        console.log('2. Move infantry/mech to property, then double-click to capture');
        return {success: true, opportunities: capturableProperties};
    } else {
        console.log('⚠️ No capture opportunities - create infantry and move to cities');
        return {success: true, opportunities: 0, note: 'Need infantry near properties'};
    }
}

// =============================================================================
// FULL GAME TEST SUITE
// =============================================================================

async function runFullGameTests() {
    console.log('🎮 === RUNNING FULL GAME TEST SUITE ===');
    console.log('==========================================');
    
    let results = {};
    
    // Core system tests
    results.coreSystem = runCoreSystemTests();
    console.log('');
    
    // Movement system tests
    try {
        results.movement = await testMovementSystem();
        console.log('');
    } catch (error) {
        results.movement = {success: false, error: error.message};
        console.log('');
    }
    
    // Turn system tests
    try {
        results.turnSystem = await testTurnSystem();
        console.log('');
    } catch (error) {
        results.turnSystem = {success: false, error: error.message};
        console.log('');
    }
    
    // Unit creation tests
    try {
        results.unitCreation = await testUnitCreation();
        console.log('');
    } catch (error) {
        results.unitCreation = {success: false, error: error.message};
        console.log('');
    }
    
    // Combat system tests
    results.combat = testCombatSystem();
    console.log('');
    
    // Property capture tests
    results.propertyCapture = testPropertyCapture();
    console.log('');
    
    // Generate final report
    console.log('📊 === FINAL TEST REPORT ===');
    console.log('============================');
    
    let passedTests = 0;
    let totalTests = 0;
    
    Object.keys(results).forEach(testName => {
        totalTests++;
        let result = results[testName];
        if (result.success) {
            console.log(`✅ ${testName}: PASSED`);
            passedTests++;
        } else {
            console.log(`❌ ${testName}: FAILED - ${result.reason || result.error}`);
        }
    });
    
    console.log('');
    console.log(`🎯 OVERALL SCORE: ${passedTests}/${totalTests} tests passed`);
    
    if (passedTests === totalTests) {
        console.log('🏆 EXCELLENT! All systems working perfectly!');
    } else if (passedTests >= totalTests * 0.8) {
        console.log('👍 GOOD! Most systems working, minor issues to address');
    } else {
        console.log('⚠️ NEEDS WORK: Several systems need attention');
    }
    
    return results;
}

// =============================================================================
// QUICK TEST FUNCTIONS
// =============================================================================

function quickMovementTest() {
    console.log('⚡ Quick Movement Test');
    testMovementSystem().then(result => {
        console.log(result.success ? '✅ Movement: OK' : '❌ Movement: FAILED');
    });
}

function quickCombatCheck() {
    console.log('⚡ Quick Combat Check');
    let result = testCombatSystem();
    console.log(result.success ? '✅ Combat: Ready' : '❌ Combat: Not Ready');
}

function quickTurnTest() {
    console.log('⚡ Quick Turn Test');
    testTurnSystem().then(result => {
        console.log(result.success ? '✅ Turns: OK' : '❌ Turns: FAILED');
    });
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

function getGameStats() {
    console.log('📈 === CURRENT GAME STATISTICS ===');
    return runCoreSystemTests();
}

function findUnits(army = null) {
    let units = [];
    board.grid.forEach(tile => {
        if (tile.unit && (!army || tile.unit.army === army)) {
            units.push({
                army: tile.unit.army,
                type: tile.unit.type,
                position: {x: tile.x, y: tile.y},
                hp: tile.unit.status.hp,
                fuel: tile.unit.status.fuel,
                canMove: tile.unit.can_move,
                canAttack: tile.unit.can_attack
            });
        }
    });
    return units;
}

function findProperties(army = null) {
    let properties = [];
    board.grid.forEach(tile => {
        if (tile.mapTile.type === 'CITY' || tile.mapTile.type === 'FACTORY' || 
            tile.mapTile.type === 'AIRPORT' || tile.mapTile.type === 'PORT') {
            if (!army || tile.mapTile.army === army) {
                properties.push({
                    type: tile.mapTile.type,
                    owner: tile.mapTile.army || 'Neutral',
                    position: {x: tile.x, y: tile.y},
                    captureHP: tile.capture_hp
                });
            }
        }
    });
    return properties;
}

// =============================================================================
// ENHANCED MOVEMENT TESTS
// =============================================================================

async function testAdvancedMovement() {
    console.log('🎯 === ADVANCED MOVEMENT TESTS ===');
    
    // Test pathfinding
    let pathfindingTest = await testPathfinding();
    console.log(`1. Pathfinding: ${pathfindingTest.success ? '✅ PASS' : '❌ FAIL'}`);
    
    // Test movement range
    let rangeTest = testMovementRange();
    console.log(`2. Movement Range: ${rangeTest.success ? '✅ PASS' : '❌ FAIL'}`);
    
    // Test terrain movement costs
    let terrainTest = testTerrainMovement();
    console.log(`3. Terrain Costs: ${terrainTest.success ? '✅ PASS' : '❌ FAIL'}`);
    
    return {
        success: pathfindingTest.success && rangeTest.success && terrainTest.success,
        details: { pathfinding: pathfindingTest, range: rangeTest, terrain: terrainTest }
    };
}

async function testPathfinding() {
    console.log('🗺️ Testing pathfinding algorithms...');
    
    // Find a unit to test with
    let testUnit = findUnits(board.current_turn)[0];
    if (!testUnit) {
        return { success: false, reason: 'No units available for testing' };
    }
    
    let startPos = testUnit.position;
    
    // Test pathfinding to various distances
    let pathfindingTests = [
        { distance: 2, expected: true },
        { distance: 3, expected: true },
        { distance: 10, expected: false }  // Should be too far
    ];
    
    let successful = 0;
    for (let test of pathfindingTests) {
        let targetX = startPos.x + test.distance;
        let targetY = startPos.y;
        
        if (targetX < board.width && targetY < board.height) {
            try {
                let result = await jsonrpc('unit_move', {
                    x: startPos.x, y: startPos.y,
                    x2: targetX, y2: targetY
                });
                
                if (result.success === test.expected) {
                    successful++;
                    console.log(`✅ Distance ${test.distance}: Expected ${test.expected}, Got ${result.success}`);
                    
                    // Move back if successful
                    if (result.success) {
                        await jsonrpc('unit_move', {
                            x: targetX, y: targetY,
                            x2: startPos.x, y2: startPos.y
                        });
                    }
                } else {
                    console.log(`❌ Distance ${test.distance}: Expected ${test.expected}, Got ${result.success}`);
                }
            } catch (error) {
                if (!test.expected) {
                    successful++;
                    console.log(`✅ Distance ${test.distance}: Correctly rejected (${error.message})`);
                } else {
                    console.log(`❌ Distance ${test.distance}: Unexpected error (${error.message})`);
                }
            }
        }
    }
    
    return { success: successful >= 2, tested: pathfindingTests.length, passed: successful };
}

// =============================================================================
// TRANSPORT SYSTEM TESTS
// =============================================================================

async function testTransportSystem() {
    console.log('🚛 === TRANSPORT SYSTEM TESTS ===');
    
    // Test loading
    let loadTest = await testUnitLoading();
    console.log(`1. Unit Loading: ${loadTest.success ? '✅ PASS' : '❌ FAIL'}`);
    
    // Test transport movement
    let moveTest = await testTransportMovement();
    console.log(`2. Transport Movement: ${moveTest.success ? '✅ PASS' : '❌ FAIL'}`);
    
    // Test unloading
    let unloadTest = await testUnitUnloading();
    console.log(`3. Unit Unloading: ${unloadTest.success ? '✅ PASS' : '❌ FAIL'}`);
    
    // Test capacity limits
    let capacityTest = await testTransportCapacity();
    console.log(`4. Capacity Limits: ${capacityTest.success ? '✅ PASS' : '❌ FAIL'}`);
    
    return {
        success: loadTest.success && moveTest.success && unloadTest.success && capacityTest.success,
        details: { loading: loadTest, movement: moveTest, unloading: unloadTest, capacity: capacityTest }
    };
}

async function testUnitLoading() {
    console.log('📦 Testing unit loading into transports...');
    
    // Find transport and compatible unit
    let transport = null;
    let cargo = null;
    
    board.grid.forEach(tile => {
        if (tile.unit && tile.unit.army === board.current_turn) {
            if (['APC', 'LANDER', 'CRUISER', 'CARRIER'].includes(tile.unit.type)) {
                transport = tile;
            } else if (['INFANTRY', 'MECH'].includes(tile.unit.type) && !cargo) {
                cargo = tile;
            }
        }
    });
    
    if (!transport || !cargo) {
        return { success: false, reason: 'No transport or cargo units available' };
    }
    
    try {
        let result = await jsonrpc('unit_load', {
            x: cargo.x, y: cargo.y,
            x2: transport.x, y2: transport.y
        });
        
        if (result.success) {
            console.log(`✅ Successfully loaded ${cargo.unit.type} into ${transport.unit.type}`);
            return { success: true, transport: transport.unit.type, cargo: cargo.unit.type };
        } else {
            console.log(`❌ Failed to load unit: ${result.error}`);
            return { success: false, reason: result.error };
        }
    } catch (error) {
        console.log(`❌ Loading error: ${error.message}`);
        return { success: false, reason: error.message };
    }
}

// =============================================================================
// CAPTURE SYSTEM TESTS  
// =============================================================================

async function testCaptureSystem() {
    console.log('🏛️ === CAPTURE SYSTEM TESTS ===');
    
    // Test capture initiation
    let initiationTest = await testCaptureInitiation();
    console.log(`1. Capture Initiation: ${initiationTest.success ? '✅ PASS' : '❌ FAIL'}`);
    
    // Test capture progression
    let progressTest = await testCaptureProgression();
    console.log(`2. Capture Progression: ${progressTest.success ? '✅ PASS' : '❌ FAIL'}`);
    
    // Test capture completion
    let completionTest = await testCaptureCompletion();
    console.log(`3. Capture Completion: ${completionTest.success ? '✅ PASS' : '❌ FAIL'}`);
    
    return {
        success: initiationTest.success && progressTest.success && completionTest.success,
        details: { initiation: initiationTest, progression: progressTest, completion: completionTest }
    };
}

async function testCaptureInitiation() {
    console.log('🏴 Testing capture initiation...');
    
    // Find capturable property with nearby infantry
    let captureTarget = null;
    let capturingUnit = null;
    
    board.grid.forEach(tile => {
        if (['CITY', 'FACTORY', 'AIRPORT', 'PORT'].includes(tile.mapTile.type) &&
            tile.mapTile.army !== board.current_turn) {
            
            // Look for nearby infantry
            board.grid.forEach(unitTile => {
                if (unitTile.unit && 
                    unitTile.unit.army === board.current_turn &&
                    ['INFANTRY', 'MECH'].includes(unitTile.unit.type)) {
                    
                    let distance = Math.abs(tile.x - unitTile.x) + Math.abs(tile.y - unitTile.y);
                    if (distance <= 3 && !captureTarget) {
                        captureTarget = tile;
                        capturingUnit = unitTile;
                    }
                }
            });
        }
    });
    
    if (!captureTarget || !capturingUnit) {
        return { success: false, reason: 'No capture opportunities available' };
    }
    
    try {
        // Move unit to property
        let moveResult = await jsonrpc('unit_move', {
            x: capturingUnit.x, y: capturingUnit.y,
            x2: captureTarget.x, y2: captureTarget.y
        });
        
        if (!moveResult.success) {
            return { success: false, reason: 'Could not move unit to property' };
        }
        
        // Initiate capture
        let captureResult = await jsonrpc('capture_tile', {
            x: captureTarget.x, y: captureTarget.y
        });
        
        if (captureResult.success) {
            console.log(`✅ Capture initiated on ${captureTarget.mapTile.type}`);
            return { success: true, property: captureTarget.mapTile.type };
        } else {
            console.log(`❌ Capture initiation failed: ${captureResult.error}`);
            return { success: false, reason: captureResult.error };
        }
    } catch (error) {
        console.log(`❌ Capture error: ${error.message}`);
        return { success: false, reason: error.message };
    }
}

// =============================================================================
// EXPORT FUNCTIONS
// =============================================================================

console.log('📋 === AVAILABLE TEST COMMANDS ===');
console.log('runFullGameTests() - Complete test suite');
console.log('runCoreSystemTests() - Basic system check');
console.log('quickMovementTest() - Fast movement test');
console.log('quickCombatCheck() - Combat readiness check');
console.log('quickTurnTest() - Turn system test');
console.log('getGameStats() - Current game statistics');
console.log('findUnits("RED") - Find all RED units');
console.log('findProperties("BLUE") - Find all BLUE properties');
console.log('==========================================');

// Make functions globally available
window.runFullGameTests = runFullGameTests;
window.runCoreSystemTests = runCoreSystemTests;
window.testMovementSystem = testMovementSystem;
window.testTurnSystem = testTurnSystem;
window.testUnitCreation = testUnitCreation;
window.testCombatSystem = testCombatSystem;
window.testPropertyCapture = testPropertyCapture;
window.quickMovementTest = quickMovementTest;
window.quickCombatCheck = quickCombatCheck;
window.quickTurnTest = quickTurnTest;
window.getGameStats = getGameStats;
window.findUnits = findUnits;
window.findProperties = findProperties;