# Advance Wars RPC - UI Review

## Current UI State

### 1. Main Menu (index.html)
- Modern gradient background design
- Form-based game creation
- Player name inputs
- Map selection
- Starting funds option

### 2. Game View (render_v2.html)
- **Title**: Shows game token ID in browser tab
- **Layout**: 
  - Top controls bar with turn info and End Turn button
  - Canvas for game rendering
  - Tile info at bottom
- **Info Display**:
  - Current turn (RED/BLUE)
  - Day counter
  - RED funds
  - BLUE funds

### 3. Controls
- **Mouse**:
  - Left click: Select/move units
  - Right click: Context menu (attack, capture, etc.)
  - Hover: Show tile info
- **Keyboard**: Currently no keyboard shortcuts

## Potential Improvements

### Browser Window Updates
1. **Better Title**: Instead of showing token, show:
   - "Advance Wars RPC - Day X - [Current Player]'s Turn"
   - Or custom game names

2. **Favicon**: Add a game icon for browser tabs

3. **Responsive Design**: Better scaling for different screen sizes

### UI Enhancements
1. **Player Info Panel**: 
   - Show all players (not just RED/BLUE)
   - Army colors
   - Unit count
   - Property count

2. **Controls Help**:
   - Show keyboard shortcuts
   - Mouse control hints
   - Tutorial overlay

3. **Visual Feedback**:
   - Turn change animations
   - Victory/defeat screens
   - Battle animations

4. **Game List Page**:
   - Show active games
   - Game preview thumbnails
   - Quick join links

5. **Additional Controls**:
   - Zoom in/out
   - Fullscreen mode
   - Settings menu
   - Sound toggle (if audio added)

Would you like me to implement any of these improvements?