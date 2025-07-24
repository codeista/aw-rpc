# Minimal Renderer Design Philosophy

## Core Principle
The renderer is just a view layer - it displays what the server tells it and forwards user input to the server. No game rules or logic in the client.

## Current Implementation (Option 4)

### What We Consider "Minimal"
- **No game rules**: The client doesn't know movement ranges, damage calculations, or validity checks
- **No game state**: Only server state is truth, no local predictions or caching
- **Simple routing**: Client has minimal logic to route clicks to appropriate RPC methods

### Why Some Client Logic is Necessary
With the current server API, the client needs to know which RPC endpoint to call:
- `unit_select` - When clicking on a unit
- `unit_move` - When moving a selected unit  
- `unit_attack_enhanced` - When attacking with a selected unit
- `unit_create` - When producing units
- etc.

This routing logic is **UI logic, not game logic**. It's similar to how a web form knows to POST to different endpoints based on which button you click.

### The Click Handler Flow
```javascript
if (board.selected) {
    try move
    if failed, try attack  
    if failed, try select
} else {
    try select
}
```

This is the minimal decision tree needed to work with current RPC methods.

## Future Enhancement: Server-Side Click Handler

A more pure approach would be adding a server RPC method:

```python
@jsonrpc.method('handle_click')
def handle_click(token: str, x: int, y: int, modifiers: dict = None) -> dict:
    # Server determines intent and executes appropriate action
    # Returns updated board state
```

Benefits:
- Zero client logic
- Server has full context for decisions
- Easier to add complex interactions

Tradeoffs:
- Requires server changes
- Less granular control
- Harder to implement different input modes

## Current Status
We're using Option 4 (minimal client routing) because:
1. It works with existing server
2. Still maintains clean separation
3. Common pattern in game clients
4. Easy to migrate to server-side handler later

The TODO comment in the code marks where we could replace client routing with a server-side handler if needed.