# Advance Wars RPC - Complete Game Flow Review

## 🎮 GAME INITIALIZATION & SETUP

### **Game Creation**
```
1. Navigate to: http://localhost:5000/
2. Options:
   - Regular game: game_create (5000 starting funds)
   - Test game: game_create_test (50000 starting funds)
3. Game board loads with:
   - 12x10 map with strategic unit placement
   - RED and BLUE armies
   - Production facilities (Factory, Airport, Port)
```

### **Turn Structure**
```
Turn Start → Income → Unit Actions → Turn End
```

---

## 🖱️ USER INTERACTION FLOW

### **PRIMARY ACTIONS**

#### **Left-Click Flow**
```
LEFT-CLICK TARGET → ACTION
├── Empty Tile
│   ├── No unit selected → Nothing
│   └── Unit selected → Move unit (if highlighted yellow)
├── Own Unit
│   ├── First click → Select unit + show movement range
│   ├── Same unit → Deselect unit
│   └── Different unit → Select new unit
├── Enemy Unit
│   ├── No unit selected → Nothing  
│   └── Unit selected → Attack (if highlighted red)
└── Production Facility
    ├── Factory → Ground unit menu
    ├── Airport → Air unit menu
    └── Port → Naval unit menu
```

#### **Right-Click Flow**
```
RIGHT-CLICK TARGET → ACTION
├── Transport with Cargo → Show blue exit positions
├── Black Boat Selected + Adjacent Damaged Unit → Repair context menu
└── Other → Warning message
```

#### **Double-Click Flow**
```
DOUBLE-CLICK TARGET → ACTION
├── Capturable Property + Infantry/Mech → Start capture
└── Any Own Unit → Wait/End turn
```

---

## 🚛 TRANSPORT SYSTEM FLOW

### **Loading Cargo**
```
METHOD 1 (Auto-Board):
Select Cargo → Move onto Transport → Auto-loads

METHOD 2 (Manual Board):
Select Cargo → Ctrl+Click Transport → Manual load

METHOD 3 (Show Options):
Select Cargo → Press 'B' → Click Green Transport
```

### **Unloading Cargo**
```
METHOD 1 (Right-Click):
Right-Click Transport → Click Blue Exit Position

METHOD 2 (Alt-Click):
Alt-Click Transport → Alt-Click Blue Exit Position

METHOD 3 (Auto-Unload):
Move Transport to Beach → Auto-unloads at beaches
```

### **Transport Capacity & Rules**
| Transport | Capacity | Can Carry | Special Rules |
|-----------|----------|-----------|---------------|
| APC | 1 | Infantry, Mech | Auto-resupply adjacent units |
| Lander | 2 | Ground units | Beach/port loading only |
| T-Copter | 1 | Infantry, Mech | Air transport |
| Cruiser | 2 | Air units | Auto-resupply carried units |
| Carrier | 2 | Planes | Auto-resupply carried units |
| Black Boat | 2 | Infantry, Mech | Manual repair (2 HP max) |

---

## ⚔️ COMBAT SYSTEM FLOW

### **Attack Execution**
```
1. Select Attacking Unit
2. See red highlighted enemy targets
3. Click enemy unit
4. Combat dialog appears:
   - Shows attacker vs defender HP
   - Damage preview with luck factor
   - Confirm/Cancel options
5. Confirm → Combat resolves → HP updated
```

### **Damage Calculation**
```
Base Damage (from table) × 
Attacker HP% × 
Terrain Defense Modifier × 
Luck Factor (±9%)
```

---

## 🔧 BLACK BOAT REPAIR FLOW

### **Current Implementation**
```
1. Select Black Boat (left-click)
   └── Sets window.gameState.selectedUnit
2. Right-click Adjacent Damaged Friendly Unit
   └── Triggers handleTransportRightClick()
3. System Checks:
   ├── Black Boat selected? ✓
   ├── Adjacent (1 tile)? ✓
   ├── Same army? ✓
   └── Target HP < 100? ✓
4. Show Context Menu: "🔧 Repair Unit (2 HP)"
5. Click Repair → RPC call → Update HP & Funds
```

### **Expected Flow Test**
```
TEST SCENARIO:
1. Create Black Boat at port (0,0)
2. Create Infantry adjacent (1,0)
3. Create enemy Tank nearby
4. Have Tank attack Infantry (damage it)
5. Select Black Boat
6. Right-click damaged Infantry
7. Should see repair context menu
```

---

## 🎯 UNIT CREATION FLOW

### **Production Requirements**
```
GROUND UNITS (Factory):
- Must own factory
- Sufficient funds
- Factory not occupied

AIR UNITS (Airport):
- Must own airport  
- Sufficient funds
- Airport not occupied

NAVAL UNITS (Port):
- Must own port
- Sufficient funds
- Port not occupied
```

### **Creation Rules**
```
1. New units CANNOT move on creation turn
2. New units CAN attack on creation turn
3. Funds deducted immediately
4. Unit appears on facility tile
```

---

## 🔄 TURN MANAGEMENT FLOW

### **Turn Start Events**
```
1. Income Distribution (1000 per property)
2. Unit State Reset (can_move, can_attack, can_capture = true)
3. Fuel Consumption (air/sea units)
4. Auto-Resupply Triggers:
   ├── APCs resupply adjacent units
   ├── Cruisers resupply carried units
   └── Carriers resupply carried units
5. Facility Repairs (20 HP at friendly facilities)
```

### **Turn End Events**
```
1. Unit flags reset
2. Control passes to next army
3. Game state saved
```

---

## 🐛 COMMON ISSUES & FIXES

### **Selection Issues**
```
PROBLEM: Unit not staying selected
FIX: Check window.gameState.selectedUnit is set correctly
```

### **Right-Click Not Working**
```
PROBLEM: Context menu not appearing
CHECKLIST:
├── Black Boat selected? (check console debug)
├── Target unit damaged? (HP < 100)
├── Units adjacent? (distance = 1)
├── Same army? (both RED or both BLUE)
└── showUnitContextMenu function exists?
```

### **Transport Issues**
```
PROBLEM: Can't load/unload
CHECKLIST:
├── Cargo compatible with transport?
├── Transport has capacity?
├── Valid terrain for loading?
└── Units can act this turn?
```

---

## 🧪 COMPREHENSIVE TEST SEQUENCE

### **Phase 1: Basic Movement**
```
1. Select Infantry → See yellow movement highlights
2. Click yellow tile → Unit moves
3. Select Tank → See red attack highlights  
4. Click red enemy → Combat dialog appears
```

### **Phase 2: Transport Operations**
```
1. Create APC at factory
2. Create Infantry at factory
3. Move Infantry onto APC → Auto-boards
4. Move APC elsewhere
5. Right-click APC → Blue exit positions appear
6. Click blue tile → Infantry unloads
```

### **Phase 3: Black Boat Repair**
```
1. Create Black Boat at port
2. Create Infantry nearby
3. Damage Infantry with enemy attack
4. Select Black Boat
5. Right-click damaged Infantry → Context menu
6. Click repair → HP increases, funds decrease
```

### **Phase 4: Production & Economy**
```
1. Click factory → Unit creation menu
2. Create unit → Funds decrease
3. End turn → Income received
4. Verify property count affects income
```

---

## ✅ SUCCESS CRITERIA

### **Core Systems Working**
- [x] Unit selection & movement
- [x] Combat with damage calculation
- [x] Transport loading/unloading
- [x] Unit creation at facilities
- [x] Turn-based income system

### **Advanced Features Working**
- [x] Black Boat movement on sea/beach/port
- [⚠️] Black Boat repair context menu (testing)
- [x] Auto-resupply systems (APC, Cruiser, Carrier)
- [x] Visual highlights and feedback
- [x] Multiple army support

### **Quality of Life Features**
- [x] Keyboard shortcuts (B, E, Escape)
- [x] Modifier keys (Ctrl+Click, Alt+Click)
- [x] Visual unit states (HP, availability)
- [x] Comprehensive testing tools

---

## 🔧 DEBUGGING TOOLS

### **Browser Console Commands**
```javascript
// Check game state
console.log(window.gameState);

// Check selected unit
console.log(window.gameState.selectedUnit);

// Check board state
console.log(board);

// Test repair function directly
showUnitContextMenu(100, 100, blackBoat, damagedUnit);
```

### **RPC Debug**
- All RPC calls logged in console
- Performance timing included
- Error handling with detailed messages

This comprehensive flow ensures every aspect of the game works correctly from unit creation through complex transport and repair operations.