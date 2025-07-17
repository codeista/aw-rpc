# GREY Army Sprite Layout

## Unique Characteristics
The GREY army has a distinctive sprite layout on the sprite sheet:

### Special Spacing Pattern:
1. **INFANTRY** at Y=1240 (base position)
2. **MECH** at Y=1335 (+95 pixels - large gap)
3. **RECON** at Y=1430 (+95 pixels - large gap)
4. **TANK** at Y=1449 (+19 pixels - standard spacing resumes)
5. All subsequent units follow standard 19-pixel spacing

### Missing Units:
The following units have NO sprites for GREY army:
- CARRIER
- MEGATANK
- BLACKBOAT
- STEALTH
- BLACKBOMB

### Complete GREY Army Layout:
| Unit | Y Position | X (idle) | X (unavailable) |
|------|------------|----------|-----------------|
| INFANTRY | 1240 | 3, 20, 37 | 339, 356, 373 |
| MECH | 1335 | 3, 20, 37 | 339, 356, 373 |
| RECON | 1430 | 3, 20, 37 | 339, 356, 373 |
| TANK | 1449 | 3, 20, 37 | 339, 356, 373 |
| MEDIUMTANK | 1468 | 3, 20, 37 | 339, 356, 373 |
| NEOTANK | 1487 | 3, 20, 37 | 339, 356, 373 |
| APC | 1506 | 3, 20, 37 | 339, 356, 373 |
| ANTIAIR | 1525 | 3, 20, 37 | 339, 356, 373 |
| ARTILLERY | 1544 | 3, 20, 37 | 339, 356, 373 |
| ROCKET | 1563 | 3, 20, 37 | 339, 356, 373 |
| MISSILE | 1582 | 3, 20, 37 | 339, 356, 373 |
| FIGHTER | 1601 | 3, 20, 37 | 339, 356, 373 |
| BOMBER | 1620 | 3, 20, 37 | 339, 356, 373 |
| BCOPTER | 1639 | 3, 20, 37 | 339, 356, 373 |
| TCOPTER | 1658 | 3, 20, 37 | 339, 356, 373 |
| ~~STEALTH~~ | (missing) | - | - |
| ~~BLACKBOMB~~ | (missing) | - | - |
| BATTLESHIP | 1677 | 3, 20, 37 | 339, 356, 373 |
| CRUISER | 1696 | 3, 20, 37 | 339, 356, 373 |
| LANDER | 1715 | 3, 20, 37 | 339, 356, 373 |
| SUB | 1734 | 3, 20, 37 | 339, 356, 373 |
| ~~CARRIER~~ | (missing) | - | - |
| ~~BLACKBOAT~~ | (missing) | - | - |
| PIPERUNNER | 1753 | 3, 20, 37 | 339, 356, 373 |

### Notes:
- All idle sprites are at X positions: 3, 20, 37 (frames 0, 1, 2)
- All unavailable sprites are at X positions: 339, 356, 373 (frames 0, 1, 2)
- The 95-pixel gaps for MECH and RECON are unique to GREY army
- Missing units cause the remaining units to shift up in position