# Advance Wars Unit Types Documentation

## Complete List of Unit Types

Based on the codebase analysis, here are all the unit types defined in the game with their exact names as used in the `UnitType` enum:

### Land Units
1. **INFANTRY** - Basic foot soldier unit
2. **MECH** - Mechanized infantry with bazooka
3. **RECON** - Fast reconnaissance vehicle
4. **TANK** - Standard tank unit
5. **MEDIUMTANK** - Medium tank (also referred to as "Md Tank" in the game)
6. **NEOTANK** - Advanced tank unit
7. **MEGATANK** - Super heavy tank
8. **APC** - Armored Personnel Carrier (transport/supply unit)
9. **ARTILLERY** - Indirect fire artillery unit
10. **ROCKET** - Long-range rocket launcher
11. **ANTIAIR** - Anti-aircraft vehicle
12. **MISSILE** - Surface-to-air missile launcher
13. **PIPERUNNER** - Special unit that moves on pipes

### Air Units
14. **FIGHTER** - Air superiority fighter
15. **BOMBER** - Heavy bomber aircraft
16. **BCOPTER** - Battle Copter (attack helicopter)
17. **TCOPTER** - Transport Copter
18. **STEALTH** - Stealth fighter/bomber
19. **BLACKBOMB** - Special explosive air unit

### Naval Units
20. **BATTLESHIP** - Heavy naval artillery ship
21. **CRUISER** - Multi-role naval vessel
22. **LANDER** - Landing craft for transporting land units
23. **SUB** - Submarine
24. **CARRIER** - Aircraft carrier
25. **BLACKBOAT** - Transport/repair boat for infantry

## Usage Examples

When creating units programmatically, use the UnitType enum:
```python
from unit import UnitType
from map_system import Army

# Example unit creation
unit_type = UnitType.INFANTRY
army = Army.RED
```

When using string-based unit types (e.g., in JSON or API calls), use the exact uppercase names:
```json
{
  "unit_type": "INFANTRY",
  "army": "RED"
}
```

## Valid String Names for API/JSON
The following are the valid string names that can be used:
- INFANTRY
- MECH
- RECON
- TANK
- MEDIUMTANK
- NEOTANK
- MEGATANK
- APC
- ARTILLERY
- ROCKET
- ANTIAIR
- MISSILE
- PIPERUNNER
- FIGHTER
- BOMBER
- BCOPTER
- TCOPTER
- STEALTH
- BLACKBOMB
- BATTLESHIP
- CRUISER
- LANDER
- SUB
- CARRIER
- BLACKBOAT

## Unit Classes
Units are also categorized by movement type:
- **BOOTS/FOOT**: Infantry, Mech
- **TREADS**: Tanks (Tank, Medium Tank, Neo Tank, Mega Tank)
- **TYRES**: Recon, APC, Artillery, Rocket, Anti-Air, Missile
- **AIR**: Fighter, Bomber, B-Copter, T-Copter, Stealth, Black Bomb
- **SEA**: Battleship, Cruiser, Lander, Sub, Carrier, Black Boat
- **PIPE**: Piperunner

## Special Notes
- Unit type names are case-sensitive when used as strings
- The enum values (e.g., UnitType.INFANTRY) are the preferred method in Python code
- Some units have abbreviated display names in the UI but use full names in the code (e.g., "Md Tank" displays as MEDIUMTANK in code)