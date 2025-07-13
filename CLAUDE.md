## ADVANCE WARS RPC - GAME ENGINE

This is a complete implementation of Advance Wars as a web-based RPC game. Key systems:

### Core Game Rules
- **Turn-based strategy**: Players take turns moving units and capturing properties
- **Unit creation**: Units cannot move on the turn they are created (standard AW rule)
- **One action per turn**: Units can move OR attack, not both in same turn
- **Income**: 1000 funds per property owned, distributed at turn start
- **Victory**: HQ capture, elimination, or property control

### Important Game Mechanics
1. **Transport System**
   - Units move INTO transports to board (not picked up)
   - Unloaded units cannot act same turn
   - APCs auto-resupply adjacent units
   - Black Boats can repair (manual command, 2HP max)

2. **Combat System**
   - Damage based on unit matchups + terrain defense
   - Counter-attacks if defender survives and in range
   - HP affects damage output

3. **Testing**
   - Use `game_create_test` RPC for high starting funds (50k)
   - Regular `game_create` only gives 5k funds
   - Check GAME_MECHANICS.md for detailed rules

### Code Architecture
- `manager.py` - Core game logic
- `transport_system.py` - All transport mechanics
- `app.py` - RPC endpoints and server
- `render.js` - Frontend game rendering

## STANDARD WORKFLOW
1. First think through the problem, read the codebase for relevant files and write a plan to tasks/todo.md. 
2. the plan should have a list of todo items that can be checked off as we go.
3. before you begin working check in with me and I will verify the plan.
4. then begin working on the todo items checking them off as we go.
5. every step of the way give me a high level explanation of the changes made.
6. make every task and code change as simple as possible reusing current methods, system files and configs if relevant.
7. add a review section to the todo.md file with a summary of changes and relevant info.

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.