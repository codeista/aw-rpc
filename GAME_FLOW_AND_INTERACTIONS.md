# Advance Wars RPC - Game Flow and User Interactions

## Game Flow Overview

### 1. Game Start
- Player creates new game via `/test` or `/game/new`
- Game initializes with starting funds and units
- RED army always goes first

### 2. Turn Structure
1. **Turn Start**
   - Income added (1000 per property)
   - Units activated (can_move, can_attack, can_capture = true)
   - Fuel consumed for air/sea units
   - Auto-resupply from APCs/Carriers/Cruisers
   - Units on repair facilities heal +20 HP

2. **Player Actions** (any order)
   - Move units
   - Attack enemies
   - Capture properties
   - Load/unload transports
   - Create new units
   - Repair/resupply (Black Boat)
   - **Auto-Wait**: Units automatically wait if no actions available after moving

3. **Turn End**
   - Click "End Turn" button
   - All unit flags reset
   - Control passes to next player

### 3. Victory Conditions
- **HQ Capture**: Capture enemy headquarters
- **Elimination**: Destroy all enemy units
- **Property Control**: Control 80% of properties

---

## User Interactions by Type

### 🖱️ Mouse Controls

#### Left Click
- **On empty tile**: Deselect current unit
- **On friendly unit**: 
  - Select unit (priority: unit > production building)
  - Show movement range (yellow highlights)
  - Show attack range (red highlights)
- **On highlighted tile**:
  - Move selected unit to tile
  - Opens action menu if enemies in range
- **On enemy unit** (when unit selected):
  - Attack if in range
  - Shows combat preview first

#### Right Click
- **On Black Boat/APC**: Opens context menu
  - 🔧 Repair Unit (Black Boat only)
  - ⛽ Resupply Unit
- **On transport with cargo**: 
  - Shows unload options
  - Click position to unload

#### Double Click
- **On transport**: Quick-load adjacent units
- **On facility**: Open production menu

#### Hover
- Shows tile coordinates
- Displays unit info
- Highlights valid movement tiles

### ⌨️ Keyboard Controls

#### Navigation
- **Arrow Keys**: Pan map (if implemented)
- **WASD**: Alternative pan controls

#### Zoom
- **+/=**: Zoom in
- **-**: Zoom out
- **0**: Reset zoom to 100%
- **Note**: Zoom level persists across sessions (saved to localStorage)

#### Actions
- **Space**: End turn
- **Escape**: Cancel current action
- **Enter**: Confirm action

### 📱 Mobile Touch Controls

#### Touch Gestures
- **Tap**: Same as left click
  - Select units
  - Move to highlighted tiles
  - Interact with UI elements
- **Long Press**: Same as right click
  - Opens context menus
  - Shows unit options
- **Drag**: Pan the map
- **Pinch**: Zoom in/out

#### Mobile UI Elements
- **Action Buttons** (40x40px):
  - Move
  - Attack
  - Capture
  - Wait
  - Load/Unload
- **End Turn Button**: Prominent position
- **Zoom Controls**: +/- buttons on screen

---

## RPC Calls Reference

### Game Management
```javascript
// Create new game
RPC: game_create
Params: {token: "gameId"}
Returns: "ok"

// Create test game (50k funds)
RPC: game_create_test
Params: {token: "gameId"}
Returns: "ok"

// Get game state
RPC: game_board
Params: {token: "gameId"}
Returns: {
  width, height, grid: [...tiles],
  current_turn: "RED",
  red_funds: 5000,
  blue_funds: 5000,
  days: 1,
  game_active: true
}

// End turn
RPC: army_end_turn
Params: {token: "gameId"}
Returns: {success: true}
```

### Unit Actions
```javascript
// Select unit
RPC: unit_select
Params: {token: "gameId", x: 5, y: 5}
Returns: {unit_data...}

// Get movement options
RPC: get_valid_moves
Params: {token: "gameId", x: 5, y: 5}
Returns: {moves: [[x,y], ...]}

// Move unit
RPC: unit_move
Params: {token: "gameId", x: 5, y: 5, x2: 7, y2: 5}
Returns: {success: true}

// Get attack targets
RPC: get_attack_targets
Params: {token: "gameId", unit_x: 5, unit_y: 5}
Returns: {targets: [{x, y, unit_type}...]}

// Preview damage
RPC: damage_preview
Params: {token: "gameId", x: 5, y: 5, x2: 7, y2: 5}
Returns: {
  preview: {
    attacker_hp_after: 100,
    defender_hp_after: 40,
    can_counter: true
  }
}

// Attack
RPC: unit_attack
Params: {token: "gameId", x: 5, y: 5, x2: 7, y2: 5}
Returns: {success: true, combat_result...}

// Capture property
RPC: capture_tile
Params: {token: "gameId", x: 5, y: 5}
Returns: {success: true, captured: true/false}

// Wait (end unit's turn)
RPC: unit_wait
Params: {token: "gameId", x: 5, y: 5}
Returns: {success: true}
```

### Transport Operations
```javascript
// Get loadable transports
RPC: transport_get_loadable_transports
Params: {token: "gameId", unit_x: 5, unit_y: 5}
Returns: {transports: [{x, y, type, space}...]}

// Load unit
RPC: cargo_board_transport
Params: {token: "gameId", cargo_x: 5, cargo_y: 5, transport_x: 6, transport_y: 5}
Returns: {success: true}

// Get unload positions
RPC: transport_get_exit_positions
Params: {token: "gameId", transport_x: 5, transport_y: 5}
Returns: {positions: [[x,y], ...]}

// Unload unit
RPC: cargo_exit_transport
Params: {token: "gameId", transport_x: 5, transport_y: 5, exit_x: 6, exit_y: 5, cargo_idx: 0}
Returns: {success: true}
```

### Production
```javascript
// Get production options
RPC: get_production_options
Params: {token: "gameId", x: 0, y: 3}
Returns: {
  options: [
    {type: "INFANTRY", cost: 1000},
    {type: "TANK", cost: 7000}...
  ]
}

// Create unit
RPC: unit_create
Params: {token: "gameId", army: "RED", unit_type: "TANK", x: 0, y: 3}
Returns: {success: true}
```

### Repair/Resupply
```javascript
// Black Boat repair
RPC: repair_unit
Params: {token: "gameId", blackboat_x: 0, blackboat_y: 0, target_x: 1, target_y: 0, hp_to_repair: 2}
Returns: {success: true}

// Manual resupply
RPC: resupply_unit
Params: {token: "gameId", resupply_x: 0, resupply_y: 0, target_x: 1, target_y: 0, fuel_amount: 99, ammo_amount: 10}
Returns: {success: true}
```

---

## Interaction Flow Examples

### Moving and Attacking
1. **Mouse**: Click unit → Click green tile → Click "Attack" → Click red target
2. **Touch**: Tap unit → Tap green tile → Tap "Attack" button → Tap enemy
3. **RPC Sequence**:
   ```
   unit_select → get_valid_moves → unit_move → get_attack_targets → damage_preview → unit_attack
   ```
4. **Auto-Wait**: If no attack targets, capture options, or transports available after moving, unit automatically waits

### Creating Units
1. **Mouse**: Double-click factory → Select unit type → Click "Create"
2. **Touch**: Tap factory → Tap "Create Unit" → Select type
3. **RPC Sequence**:
   ```
   get_production_options → unit_create
   ```

### Transport Operations
1. **Load**: Select infantry → Click adjacent APC
2. **Unload**: Right-click loaded transport → Click unload position
3. **RPC Sequence**:
   ```
   transport_get_loadable_transports → cargo_board_transport
   transport_get_exit_positions → cargo_exit_transport
   ```

### Black Boat Repair
1. **Mouse**: Right-click Black Boat → Click "Repair Unit"
2. **Touch**: Long-press Black Boat → Tap "Repair Unit"
3. **RPC Sequence**:
   ```
   repair_unit (max 2 HP, up to 90 total HP)
   ```

---

## Visual Effects and Highlights

### Unit Selection Effects
When selecting a unit:
1. **Immediate Effects**:
   - Yellow border around selected unit
   - Unit info panel updates
   - Movement highlights appear (green tiles)
   - Attack highlights appear (red tiles)
   
2. **RPC Calls Triggered**:
   - `unit_select` - Gets unit data
   - `get_valid_moves` - Calculates movement range
   - `get_attack_targets` - Finds attackable enemies

3. **Highlight Rendering**:
   ```javascript
   // Yellow movement tiles
   renderMovementHighlights()
   - Semi-transparent yellow overlay
   - Shows all reachable tiles
   - Considers terrain movement costs
   
   // Red attack tiles  
   renderAttackHighlights()
   - Semi-transparent red overlay
   - Shows attackable positions
   - Updates after movement
   ```

### Movement Effects
When moving a unit:
1. **Preview State**:
   - Hover shows path preview
   - Movement cost indicator
   
2. **During Movement**:
   - Unit sprite moves to new position
   - Old position cleared
   - Movement highlights disappear
   
3. **After Movement**:
   - Attack highlights update for new position
   - Action menu appears if enemies in range
   - Unit remains selected

### Combat Effects
When attacking:
1. **Combat Preview**:
   - Damage preview modal appears
   - Shows estimated damage both ways
   - HP bars with predicted outcomes
   
2. **During Combat**:
   - Attack animation (if implemented)
   - HP updates on both units
   - Destroyed units removed
   
3. **After Combat**:
   - All highlights cleared via clearAllHighlights()
   - Unit marked as unavailable (grayed out)
   - Auto-deselect attacker
   - Client-side flags updated: can_move = false, can_attack = false

### Transport Highlighting
When selecting cargo unit near transports:
1. **Load Highlights**:
   - Green border on compatible transports
   - Shows available space indicator
   - Transport type compatibility check
   
2. **Visual Indicators**:
   ```javascript
   renderTransportHighlights()
   - Green circle for loadable transports
   - Cargo count badges (e.g., "1/2")
   - Different colors for different transport types
   ```

When right-clicking loaded transport:
1. **Unload Highlights**:
   - Green tiles show valid unload positions
   - Adjacent empty tiles only
   - Terrain compatibility checked
   
2. **Cargo Display**:
   - Shows cargo list in context menu
   - Unit type and HP for each

### Property Capture Effects
When infantry/mech on capturable property:
1. **Capture Progress**:
   - Flag indicator appears
   - Shows capture HP (20 → 0)
   - Property color shifts toward capturing army
   
2. **Capture Complete**:
   - Property changes color
   - Income updates next turn
   - Victory condition check

### Production Effects
When selecting production facility:
1. **Factory/Airport/Port**:
   - Production menu modal appears
   - Shows available units with costs
   - Grays out unaffordable units
   
2. **After Production**:
   - New unit appears on facility
   - Funds deducted
   - Unit starts grayed out (can't move first turn)

### Repair/Resupply Effects
Black Boat repair:
1. **Repair Range**:
   - Shows repairable units in range
   - HP indicators on damaged units
   - Max 10 HP (90 actual) limit shown
   
2. **During Repair**:
   - HP animation (+1 or +2)
   - Fuel/ammo topped off
   - Cost deducted (10% per HP)

APC auto-resupply:
1. **Turn Start**:
   - Automatic fuel/ammo restoration
   - Visual indicator flash
   - No cost, happens silently

### Special Visual States

#### Unit States
- **Available** (can act): Full color sprite - determined by (can_move || can_attack)
- **Unavailable** (acted): Grayed out sprite - when both can_move and can_attack are false
- **Loaded** (in transport): Hidden from map
- **Capturing**: Flag indicator visible
- **Note**: can_capture flag does not affect sprite state

#### Tile Overlays
- **Movement Range**: Yellow semi-transparent
- **Attack Range**: Red semi-transparent  
- **Transport Load**: Green circle outline
- **Unload Positions**: Green tile highlights
- **Capture Progress**: Flag + HP number

#### UI Indicators
- **Selected Unit**: Yellow border (2px)
- **HP Display**: Number in corner (1-10)
- **Fuel Warning**: Fuel can icon (<30 fuel)
- **Ammo Warning**: Ammo icon (<3 ammo)
- **Cargo Count**: "X/Y" badge on transports

### Zoom Effects
When zooming:
1. **Canvas Scaling**:
   - All sprites scale proportionally
   - Highlights maintain relative size
   - Text remains readable
   
2. **Persistence**:
   - Zoom level saved to localStorage as 'canvas-zoom'
   - Restored on page refresh via loadZoomFromStorage()
   - Mobile pinch gesture support
   - Default: 100% zoom if no saved value
   
3. **Sprite Loading**:
   - Sprite corrections loaded before rendering to prevent black sprites
   - Handles timing issues with async sprite data loading
   - BLUE unit sprites: Fixed "grayed out" issue by adding proper sprite state mapping

---

## Context Menus and Action Dialogs

### Unit Action Menu
Appears after moving to a tile:
```
┌─────────────────┐
│ ⚔️ Attack       │ → Shows if enemies in range
│ 🏴 Capture      │ → Shows if on capturable property
│ 🚛 Load         │ → Shows if transport adjacent
│ ⏸️ Wait         │ → Always available
│ ❌ Cancel       │ → Returns unit to original position
└─────────────────┘
```
**Note**: If no actions are available except Wait, the unit automatically waits without showing menu

### Transport Context Menu (Right-Click)
For Black Boat:
```
┌────────────────────────────────────┐
│ 🔧 Repair Unit (2 HP, max 10 HP)  │
│ ⛽ Resupply Unit (Fuel+Ammo)       │
│ 📦 Show Cargo                      │ → If carrying units
│ ❌ Cancel                          │
└────────────────────────────────────┘
```

For APC/Lander/T-Copter:
```
┌─────────────────────┐
│ ⛽ Resupply Unit    │ → APC only
│ 📦 Unload Cargo     │ → If carrying units
│ ❌ Cancel           │
└─────────────────────┘
```

### Unload Position Menu
After selecting unload:
```
┌─────────────────────┐
│ Select Position:    │
│ ⬆️ North (5,4)      │ → Only shows valid tiles
│ ➡️ East (6,5)       │ → Checks terrain compatibility
│ ⬇️ South (5,6)      │ → Adjacent tiles only
│ ❌ Cancel           │
└─────────────────────┘
```

### Production Menu
When clicking on factory/airport/port:
```
┌─────────────────────────────┐
│ 🏭 Factory Production       │
├─────────────────────────────┤
│ 👤 Infantry    💰 1000     │
│ 🤖 Mech        💰 3000     │
│ 🚗 Recon       💰 4000     │
│ 🚢 Tank        💰 7000     │ → Grayed if insufficient funds
│ 🚛 APC         💰 5000     │
│ 💥 Artillery   💰 6000     │
├─────────────────────────────┤
│ Current Funds: 💰 15000     │
│ ❌ Cancel                   │
└─────────────────────────────┘
```

### Combat Preview Dialog
Before attacking:
```
┌──────────────────────────────┐
│      Combat Preview          │
├──────────────────────────────┤
│ Attacker: Tank (10 HP)       │
│ ▓▓▓▓▓▓▓▓▓▓ → ▓▓▓▓▓▓▓▓▓▓    │
│ Damage: 55%                  │
├──────────────────────────────┤
│ Defender: Infantry (10 HP)   │
│ ▓▓▓▓▓▓▓▓▓▓ → ▓▓▓▓░░░░░░    │
│ Counter: 10%                 │
├──────────────────────────────┤
│ ✅ Confirm   ❌ Cancel       │
└──────────────────────────────┘
```

### Victory Dialog
When game ends:
```
┌──────────────────────────────┐
│        🏆 Victory! 🏆        │
├──────────────────────────────┤
│ RED Army Wins!               │
│                              │
│ Victory Type: HQ Capture     │
│ Turns: 15                    │
│ Units Destroyed: 8           │
├──────────────────────────────┤
│ 🔄 New Game   📊 Stats       │
└──────────────────────────────┘
```

### Mobile Action Buttons
Floating buttons for touch interface:
```
┌────┬────┬────┬────┐
│ 🚶 │ ⚔️ │ 🏴 │ ⏸️ │  40x40px each
└────┴────┴────┴────┘
  Move Attack Cap Wait
```

### Property Info Popup
When hovering over property:
```
┌─────────────────────┐
│ 🏭 Factory          │
│ Owner: RED          │
│ Income: +1000/turn  │
│ HP: 20/20           │
└─────────────────────┘
```

### Unit Info Panel
When selecting unit:
```
┌─────────────────────────┐
│ RED Tank                │
│ HP: ▓▓▓▓▓▓▓▓▓▓ 10/10  │
│ Fuel: 70/70            │
│ Ammo: 9/9              │
│ Move: 6                │
│ Status: Ready          │
└─────────────────────────┘
```

### Error/Warning Dialogs
For invalid actions:
```
┌──────────────────────────────┐
│ ⚠️ Invalid Action           │
├──────────────────────────────┤
│ Cannot move through enemy    │
│ units!                       │
├──────────────────────────────┤
│        OK                    │
└──────────────────────────────┘
```

### Repair Cost Confirmation
For Black Boat repairs:
```
┌──────────────────────────────┐
│ 💰 Repair Cost              │
├──────────────────────────────┤
│ Unit: Infantry (3 HP)        │
│ Repair: +2 HP                │
│ Cost: 200 funds             │
│ New HP: 5/10                │
├──────────────────────────────┤
│ ✅ Confirm   ❌ Cancel       │
└──────────────────────────────┘
```

---

## UI State Management

### Canvas Rendering Pipeline
1. **Base Layer**: Terrain tiles
2. **Unit Layer**: Unit sprites with HP
3. **Highlight Layer**: Movement/attack overlays
4. **UI Layer**: Selection borders, indicators
5. **Modal Layer**: Menus and dialogs (z-index: 10000)

### Differential Updates
- Only redraws changed elements
- Tracks units by position key
- Prevents flickering with double buffering
- Updates triggered by RPC responses

### Mobile Optimizations
- **Touch Events**: Prevents default browser behaviors
- **Modal Positioning**: Fixed center positioning
- **Button Size**: 40x40px minimum touch target
- **Viewport**: Responsive scaling with device-width

---

## Development Tools

### Sprite Showcase
- **Route**: `/sprites`
- **Purpose**: View all unit sprites for all armies in different states
- **Features**:
  - Shows available, unavailable, and damaged states
  - All 25 unit types for all 5 armies (RED, BLUE, GREEN, YELLOW, BLACK)
  - Interactive tileset switching
  - Uses actual game sprite correction data
  - Demonstrates sprite state rendering pipeline
  - Useful for debugging sprite display issues

### Debug Functions (Console)
Available in browser console for testing:

1. **simulateGameFlow()**
   - Simulates complete game flow programmatically
   - Tests unit selection, movement, and combat
   - Executes: select unit → move → attack → end turn sequence
   - Useful for automated testing and QA validation
   - Returns: Boolean success status and detailed logs

2. **testSpriteStates()**
   - Logs current sprite state for all units on the board
   - Shows can_move, can_attack, can_capture flags for each unit
   - Displays unit position, type, army, and HP
   - Helps debug sprite graying/availability display issues
   - Format: "[x,y] TYPE(army) HP: can_move/can_attack/can_capture"

3. **clearAllHighlights()**
   - Manually clears all movement and attack highlights
   - Useful when highlights get stuck after errors
   - Called automatically after combat and major actions

### Client-Side Workarounds
Due to server-side state management limitations, the following client-side updates are implemented:

1. **After Movement**:
   - If auto-wait triggered: can_move = false, can_attack = false
   
2. **After Attack**:
   - Attacker: can_move = false, can_attack = false
   
3. **After Capture**:
   - Unit: can_move = false, can_attack = false, can_capture = false
   
4. **After Wait**:
   - Unit: can_move = false, can_attack = false

These ensure sprite states update immediately without waiting for server sync.

### Async Action Menu Handling
The `showPostMoveActionMenu()` function handles async action selection after unit movement:

1. **Menu Display Logic**:
   ```javascript
   async function showPostMoveActionMenu(actions) {
     // Filter available actions based on unit state
     // Show modal with action buttons
     // Return selected action as Promise
   }
   ```

2. **Auto-Wait Integration**:
   - If only "Wait" action available, auto-executes without showing menu
   - Prevents unnecessary modal popups for routine moves
   - Improves game flow and user experience

3. **Action Priority**:
   - Attack actions shown first (red button)
   - Capture actions for properties (flag button)
   - Transport load/unload options
   - Wait action always available (gray button)