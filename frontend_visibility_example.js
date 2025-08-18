/**
 * Frontend example: How to use visibility filtering
 * 
 * The frontend needs to be updated to pass the viewing player's ID
 * when requesting the game board to ensure hidden units are properly filtered.
 */

// Example: Update the game board request to include player_id
async function updateGameBoard(gameToken, currentPlayerId) {
    // OLD WAY (shows all units to everyone):
    // const board = await jsonrpc('game_board', { token: gameToken });
    
    // NEW WAY (filters hidden units based on visibility):
    const board = await jsonrpc('game_board', { 
        token: gameToken,
        viewing_player_id: currentPlayerId  // Pass the current player's ID
    });
    
    // The returned board will only contain units visible to currentPlayerId:
    // - All of their own units (including hidden ones)
    // - All non-hidden enemy units
    // - Hidden enemy units ONLY if adjacent to a friendly unit
    
    return board;
}

// Example: Rendering units with hidden state
function renderUnit(ctx, unit, isCurrentPlayer) {
    // Check if unit belongs to current player
    if (unit.player_id === currentPlayerId) {
        // Own unit - always render
        if (unit.is_hidden) {
            // Show semi-transparent to indicate hidden state
            ctx.globalAlpha = 0.5;
            drawUnitSprite(ctx, unit);
            ctx.globalAlpha = 1.0;
            
            // Maybe add a "hidden" indicator
            ctx.fillStyle = 'white';
            ctx.font = '8px Arial';
            ctx.fillText('H', unit.x * 16 + 2, unit.y * 16 + 14);
        } else {
            // Normal rendering
            drawUnitSprite(ctx, unit);
        }
    } else {
        // Enemy unit - will only be in the data if visible
        // The backend has already filtered out invisible units
        drawUnitSprite(ctx, unit);
        
        // If it's hidden but visible (adjacent), maybe show differently
        if (unit.is_hidden) {
            // Add some indicator that this is a detected hidden unit
            ctx.strokeStyle = 'red';
            ctx.lineWidth = 2;
            ctx.strokeRect(unit.x * 16, unit.y * 16, 16, 16);
        }
    }
}

// Example: Update context menu for hide/unhide actions
function updateUnitContextMenu(unit) {
    const menu = document.getElementById('unitContextMenu');
    
    // Add hide/unhide options for stealth and sub units
    if (unit.type === 'STEALTH' || unit.type === 'SUB') {
        if (unit.is_hidden) {
            // Show unhide option
            addMenuItem(menu, 'Unhide', () => {
                jsonrpc('unit_unhide', { 
                    token: gameToken, 
                    x: unit.x, 
                    y: unit.y 
                }).then(result => {
                    if (result.success) {
                        updateGameBoard(gameToken, currentPlayerId);
                    }
                });
            });
        } else if (unit.can_move && !unit.has_moved) {
            // Show hide option (only if unit hasn't moved)
            addMenuItem(menu, 'Hide', () => {
                jsonrpc('unit_hide', { 
                    token: gameToken, 
                    x: unit.x, 
                    y: unit.y 
                }).then(result => {
                    if (result.success) {
                        updateGameBoard(gameToken, currentPlayerId);
                    }
                });
            });
        }
    }
}

// SECURITY NOTE: 
// With this implementation, Player 2 CANNOT see Player 1's hidden units
// by inspecting the JavaScript or network responses. The backend only
// sends units that should be visible to the requesting player.