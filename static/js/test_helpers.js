/**
 * Helper functions for creating test games
 */

// Create a test game with high starting funds (50k)
async function createTestGame(token) {
    if (!token) {
        token = 'test_' + Math.random().toString(36).substr(2, 9);
    }
    
    try {
        const result = await rpc('game_create_test', { token: token });
        if (result && !result.error) {
            console.log(`✅ Test game created: ${token}`);
            console.log(`   URL: ${window.location.origin}/${token}`);
            console.log(`   Starting funds: 50,000 each`);
            return token;
        } else {
            console.error('❌ Failed to create test game:', result?.error || 'Unknown error');
            return null;
        }
    } catch (error) {
        console.error('❌ Error creating test game:', error);
        return null;
    }
}

// Quick setup for Black Boat testing
async function setupBlackBoatTest(token) {
    if (!token) {
        token = await createTestGame();
    }
    
    if (!token) return null;
    
    console.log('\n🚢 Setting up Black Boat test...');
    
    // Create Black Boat at port (0,0)
    const blackboatResult = await rpc('unit_create', {
        token: token,
        army: 'RED',
        unit_type: 'BLACKBOAT',
        x: 0,
        y: 0
    });
    
    if (blackboatResult && !blackboatResult.error) {
        console.log('✅ Black Boat created at port (0,0)');
        
        // Create infantry nearby for repair testing
        const infResult = await rpc('unit_create', {
            token: token,
            army: 'RED', 
            unit_type: 'INFANTRY',
            x: 1,
            y: 0
        });
        
        if (infResult && !infResult.error) {
            console.log('✅ Infantry created at (1,0)');
            console.log('\n📝 Instructions:');
            console.log('1. End turn to enable Black Boat movement');
            console.log('2. Create enemy unit to damage infantry');
            console.log('3. Select Black Boat and right-click damaged infantry to repair');
        }
    }
    
    return token;
}

// Export for use in console
window.testHelpers = {
    createTestGame,
    setupBlackBoatTest
};

console.log('Test helpers loaded. Available functions:');
console.log('- testHelpers.createTestGame() - Create game with 50k funds');
console.log('- testHelpers.setupBlackBoatTest() - Set up Black Boat repair test');