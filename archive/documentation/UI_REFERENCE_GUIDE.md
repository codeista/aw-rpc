# Advance Wars RPC - Complete UI Reference Guide

## 🎮 Current Movement & Interaction System

### **CLICK INTERACTIONS**

#### **Left-Click Actions**
| Target | Action | Visual Feedback |
|--------|--------|-----------------|
| **Own Unit** | Select unit | Unit selected, movement highlights appear |
| **Yellow Highlighted Tile** | Move unit | Unit moves, highlights clear |
| **Red Highlighted Enemy** | Attack enemy | Combat dialog, damage preview |
| **Factory/Airport/Port** | Create unit | Unit creation menu opens |
| **Green Transport** | Board transport | Cargo loads, highlights clear |

#### **Right-Click Actions**
| Target | Requirement | Action | Visual Result |
|--------|-------------|--------|---------------|
| **Transport with Cargo** | Any transport | Show unload options | Blue exit positions appear |
| **Damaged Friendly Unit** | Black Boat selected + adjacent | Repair context menu | Menu with "🔧 Repair Unit (2 HP)" |

#### **Double-Click Actions**
| Target | Action | Result |
|--------|--------|--------|
| **Capturable Property** | Capture (Infantry/Mech only) | Unit begins capture process |
| **Any Own Unit** | End turn/Wait | Unit becomes inactive |

#### **Modifier + Click**
| Combination | Target | Action |
|-------------|--------|--------|
| **Ctrl+Click** | Transport | Legacy boarding method |
| **Alt+Click** | Transport | Show exit options |
| **Alt+Click** | Blue highlighted tile | Deploy/unload unit |

---

## 🎨 VISUAL HIGHLIGHT SYSTEM

### **Movement Highlights**
- **Color**: Light yellow (`rgba(255, 248, 220, 0.2)`) with gold border (`#B8860B`)
- **Shape**: Rectangle covering tile with 2px border
- **Trigger**: Select any movable unit
- **Cleared**: When unit moves or different unit selected

### **Attack Highlights**
- **Color**: Red (`red` fill)
- **Shape**: Rectangle covering tile
- **Trigger**: Select unit with attack capability
- **Shows**: All enemy units within attack range

### **Transport Highlights**

#### **Loadable Transports (Green)**
- **Color**: Green
- **Trigger**: Select cargo unit + press 'B' key OR move onto transport
- **Shows**: All compatible transports within range

#### **Exit Positions (Blue)**
- **Color**: Blue  
- **Trigger**: Right-click transport OR Alt+click transport
- **Shows**: Valid unload positions around transport

#### **Transport with Cargo (Yellow Border)**
- **Visual**: Yellow border around transport sprite
- **Shows**: Transport is carrying units
- **Persistent**: Remains until cargo is unloaded

---

## 📱 POPUP MENUS & DIALOGS

### **Unit Creation Menus**

#### **Factory Menu** (Ground Units)
```
Infantry (1000)     Mech (3000)        Recon (4000)
Tank (7000)         Medium Tank (16000) Anti-Air (8000)
Artillery (6000)    Missile (12000)     Rocket (15000)
Neo Tank (22000)    Mega Tank (28000)   APC (5000)
Piperunner (20000)
```

#### **Airport Menu** (Air Units)
```
B-Copter (9000)     T-Copter (5000)
Fighter (20000)     Bomber (22000)
```

#### **Port Menu** (Naval Units)
```
Lander (12000)      Battleship (28000)  Cruiser (18000)
Sub (20000)         Carrier (30000)     Black Boat (7500)
```

### **Context Menus**

#### **Black Boat Repair Menu**
- **Trigger**: Right-click damaged adjacent unit with Black Boat selected
- **Options**: "🔧 Repair Unit (2 HP)"
- **Requirements**: Adjacent friendly unit with <100 HP
- **Cost**: 10% of unit cost per HP repaired

#### **Combat Confirmation Dialog**
- **Shows**: Attacker vs Defender HP
- **Damage Preview**: Estimated damage with luck factor
- **Options**: Confirm Attack / Cancel

---

## ⌨️ KEYBOARD SHORTCUTS

| Key | Action | Context |
|-----|--------|---------|
| **B** | Show loadable transports | Cargo unit selected |
| **E** | Show exit options | Transport selected |
| **Escape** | Cancel all actions | Clear highlights and selections |

---

## 🚢 TRANSPORT SYSTEM WORKFLOW

### **Loading Cargo**
1. **Method 1**: Select cargo → move onto transport (auto-boards)
2. **Method 2**: Select cargo → press 'B' → click green transport
3. **Method 3**: Select cargo → Ctrl+click transport

### **Unloading Cargo**
1. **Method 1**: Right-click transport → click blue exit position
2. **Method 2**: Alt-click transport → Alt-click blue exit position
3. **Auto-exit**: Some transports auto-unload when moving to beaches

### **Transport Types & Capacity**

| Transport | Capacity | Can Carry | Special |
|-----------|----------|-----------|---------|
| **APC** | 1 | Infantry, Mech | Auto-resupply adjacent units |
| **Lander** | 2 | Most ground units | Beach/port loading only |
| **T-Copter** | 1 | Infantry, Mech | Air transport |
| **Cruiser** | 2 | Air units | Auto-resupply carried units |
| **Carrier** | 2 | Planes | Auto-resupply carried units |
| **Black Boat** | 2 | Infantry, Mech | Manual repair (2 HP max) |

---

## 🎯 UNIT STATUS INDICATORS

### **Health Display**
- **Green bar**: Full/high health units
- **Yellow bar**: Damaged units  
- **Red bar**: Heavily damaged units
- **Size**: 8x8 pixels below unit sprite

### **Unit State Visual Cues**
- **Bright sprites**: Can act this turn
- **Dimmed sprites**: Already acted this turn
- **Gray overlay**: Out of fuel or cannot act

### **Army Colors**
- **RED Army**: Red-tinted unit sprites
- **BLUE Army**: Blue-tinted unit sprites
- **Additional armies**: Green, Yellow support

---

## 🔧 SPECIAL FEATURES

### **Black Boat Repair System**
1. Select Black Boat
2. Right-click adjacent damaged friendly unit
3. Choose "🔧 Repair Unit (2 HP)" from context menu
4. Pays 10% of unit cost per HP repaired
5. Maximum 2 HP repair per action

### **Auto-Resupply Systems**
- **APC**: Auto-resupplies ALL adjacent units at turn start
- **Cruiser/Carrier**: Auto-resupplies carried air units each turn

### **Capture System**
- **Units**: Infantry, Mech only
- **Method**: Double-click on enemy/neutral property
- **Progress**: Based on unit HP (HP/10 capture points per turn)
- **Victory**: Capturing enemy HQ wins instantly

---

## 🎮 CONTROL SUMMARY

**Primary Controls**: 
- Click=select/move/attack
- Right-click=transport/repair options  
- Double-click=capture/wait

**Transport Controls**:
- Ctrl+Click=load
- Alt+Click=unload  
- B key=show transports
- E key=show exits

**Visual Feedback**:
- Yellow=movement range
- Red=attack targets
- Green=loadable transports
- Blue=exit positions

This system provides comprehensive Advance Wars gameplay with enhanced transport mechanics and modern UI conveniences while maintaining the classic feel of the original game.