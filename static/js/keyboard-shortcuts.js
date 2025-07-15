/**
 * Keyboard Shortcuts Module - Comprehensive keyboard controls for AW-RPC
 * 
 * Keyboard Map:
 * - Space: End turn
 * - Escape: Cancel current action / Deselect
 * - Enter: Confirm action / Wait unit
 * - W: Wait selected unit
 * - A: Attack mode
 * - M: Move mode
 * - C: Capture with Infantry/Mech
 * - L: Load unit into transport
 * - U: Unload unit from transport
 * - T: Show transport status
 * - +/=: Zoom in
 * - -: Zoom out
 * - 0: Reset zoom
 * - Arrow keys: Pan map (future)
 * - Tab: Cycle through available units
 * - Shift+Tab: Cycle backwards
 * - H: Show/hide help
 * - D: Toggle debug info
 * - R: Refresh/rerender
 * - E: End turn (alternative to Space)
 * - Number keys 1-9: Quick actions in menus
 */

class KeyboardShortcuts {
    constructor() {
        this.enabled = true;
        this.helpVisible = false;
        this.debugMode = false;
        this.currentUnitIndex = 0;
        
        // Create help overlay
        this.createHelpOverlay();
        
        // Bind event handlers
        this.handleKeyDown = this.handleKeyDown.bind(this);
        this.handleKeyUp = this.handleKeyUp.bind(this);
    }
    
    /**
     * Initialize keyboard shortcuts
     */
    initialize() {
        document.addEventListener('keydown', this.handleKeyDown);
        document.addEventListener('keyup', this.handleKeyUp);
        
        logger.info('Keyboard shortcuts initialized');
    }
    
    /**
     * Create help overlay for keyboard shortcuts
     */
    createHelpOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'keyboard-help-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #3498db;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            z-index: 10000;
            display: none;
            font-family: monospace;
        `;
        
        overlay.innerHTML = `
            <h2 style="color: #3498db; margin-bottom: 15px;">⌨️ Keyboard Shortcuts</h2>
            <div style="display: grid; grid-template-columns: auto 1fr; gap: 10px;">
                <kbd>Space / E</kbd><span>End turn</span>
                <kbd>Escape</kbd><span>Cancel action / Deselect</span>
                <kbd>Enter</kbd><span>Confirm / Wait unit</span>
                <kbd>W</kbd><span>Wait selected unit</span>
                <kbd>A</kbd><span>Attack mode</span>
                <kbd>M</kbd><span>Move mode</span>
                <kbd>C</kbd><span>Capture property</span>
                <kbd>L</kbd><span>Load unit</span>
                <kbd>U</kbd><span>Unload unit</span>
                <kbd>T</kbd><span>Transport status</span>
                <kbd>Tab</kbd><span>Next unit</span>
                <kbd>Shift+Tab</kbd><span>Previous unit</span>
                <kbd>+/-</kbd><span>Zoom in/out</span>
                <kbd>0</kbd><span>Reset zoom</span>
                <kbd>R</kbd><span>Refresh board</span>
                <kbd>D</kbd><span>Debug mode</span>
                <kbd>H</kbd><span>Toggle this help</span>
                <kbd>1-9</kbd><span>Quick menu actions</span>
            </div>
            <p style="margin-top: 15px; color: #7f8c8d;">Press H or Escape to close</p>
        `;
        
        document.body.appendChild(overlay);
        this.helpOverlay = overlay;
    }
    
    /**
     * Handle keydown events
     */
    handleKeyDown(event) {
        // Don't handle if typing in input/textarea
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
            return;
        }
        
        // Don't handle if disabled
        if (!this.enabled) {
            return;
        }
        
        const key = event.key.toLowerCase();
        const shift = event.shiftKey;
        const ctrl = event.ctrlKey;
        const alt = event.altKey;
        
        // Prevent default for our shortcuts
        switch (key) {
            case ' ':
            case 'escape':
            case 'enter':
            case 'tab':
            case '+':
            case '=':
            case '-':
            case '0':
                event.preventDefault();
                break;
        }
        
        // Handle shortcuts
        switch (key) {
            // Game actions
            case ' ':
            case 'e':
                this.endTurn();
                break;
                
            case 'escape':
                this.cancelAction();
                break;
                
            case 'enter':
                this.confirmAction();
                break;
                
            // Unit actions
            case 'w':
                this.waitUnit();
                break;
                
            case 'a':
                this.attackMode();
                break;
                
            case 'm':
                this.moveMode();
                break;
                
            case 'c':
                this.captureProperty();
                break;
                
            // Transport actions
            case 'l':
                this.loadUnit();
                break;
                
            case 'u':
                this.unloadUnit();
                break;
                
            case 't':
                this.transportStatus();
                break;
                
            // Navigation
            case 'tab':
                event.preventDefault();
                if (shift) {
                    this.previousUnit();
                } else {
                    this.nextUnit();
                }
                break;
                
            // Zoom
            case '+':
            case '=':
                this.zoomIn();
                break;
                
            case '-':
                this.zoomOut();
                break;
                
            case '0':
                this.zoomReset();
                break;
                
            // UI
            case 'h':
                this.toggleHelp();
                break;
                
            case 'd':
                this.toggleDebug();
                break;
                
            case 'r':
                this.refresh();
                break;
                
            // Number keys for quick actions
            case '1':
            case '2':
            case '3':
            case '4':
            case '5':
            case '6':
            case '7':
            case '8':
            case '9':
                this.quickAction(parseInt(key));
                break;
                
            // Arrow keys for future map panning
            case 'arrowup':
            case 'arrowdown':
            case 'arrowleft':
            case 'arrowright':
                // TODO: Implement map panning
                break;
        }
    }
    
    /**
     * Handle keyup events
     */
    handleKeyUp(event) {
        // Future: Handle key releases if needed
    }
    
    // ===== ACTION IMPLEMENTATIONS =====
    
    endTurn() {
        logger.debug('Keyboard: End turn');
        if (window.armyEndTurn) {
            window.armyEndTurn();
        }
    }
    
    cancelAction() {
        logger.debug('Keyboard: Cancel action');
        
        // Hide any open menus
        if (window.hideUnitContextMenu) {
            window.hideUnitContextMenu();
        }
        
        if (window.hideActionMenu) {
            window.hideActionMenu();
        }
        
        // Clear selection
        if (window.board?.selected) {
            window.board.selected = null;
            if (window.clearAllHighlights) {
                window.clearAllHighlights();
            }
            if (window.rerender) {
                window.rerender();
            }
        }
        
        // Hide help if open
        if (this.helpVisible) {
            this.toggleHelp();
        }
    }
    
    confirmAction() {
        logger.debug('Keyboard: Confirm action');
        
        const selected = window.board?.selected;
        if (selected?.unit && selected.unit.army === window.board.current_turn) {
            this.waitUnit();
        }
    }
    
    waitUnit() {
        logger.debug('Keyboard: Wait unit');
        
        const selected = window.board?.selected;
        if (selected?.unit && selected.unit.army === window.board.current_turn) {
            if (window.unitWait) {
                window.unitWait(selected);
            }
        }
    }
    
    attackMode() {
        logger.debug('Keyboard: Attack mode');
        
        const selected = window.board?.selected;
        if (selected?.unit && selected.unit.army === window.board.current_turn) {
            // Show attack targets
            if (window.showAttackTargets) {
                window.showAttackTargets(selected);
            }
        }
    }
    
    moveMode() {
        logger.debug('Keyboard: Move mode');
        
        const selected = window.board?.selected;
        if (selected?.unit && selected.unit.army === window.board.current_turn) {
            // Show movement range
            if (window.showMovementRange) {
                window.showMovementRange(selected);
            }
        }
    }
    
    captureProperty() {
        logger.debug('Keyboard: Capture property');
        
        const selected = window.board?.selected;
        if (selected?.unit) {
            const unitType = selected.unit.type;
            if (unitType === 'INFANTRY' || unitType === 'MECH') {
                if (window.unitCapture) {
                    window.unitCapture(selected);
                }
            }
        }
    }
    
    loadUnit() {
        logger.debug('Keyboard: Load unit');
        
        const selected = window.board?.selected;
        if (selected) {
            // Simulate Ctrl+Click on selected tile
            const event = new MouseEvent('click', {
                ctrlKey: true,
                offsetX: selected.x * window.TILESIZE,
                offsetY: selected.y * window.TILESIZE
            });
            
            if (window.handleTransportOperations) {
                const tile = { x: selected.x, y: selected.y, unit: selected.unit };
                window.handleTransportOperations(tile, event);
            }
        }
    }
    
    unloadUnit() {
        logger.debug('Keyboard: Unload unit');
        
        const selected = window.board?.selected;
        if (selected) {
            // Simulate Alt+Click on selected tile
            const event = new MouseEvent('click', {
                altKey: true,
                offsetX: selected.x * window.TILESIZE,
                offsetY: selected.y * window.TILESIZE
            });
            
            if (window.handleTransportOperations) {
                const tile = { x: selected.x, y: selected.y, unit: selected.unit };
                window.handleTransportOperations(tile, event);
            }
        }
    }
    
    transportStatus() {
        logger.debug('Keyboard: Transport status');
        
        if (window.getTransportStatus) {
            window.getTransportStatus();
        }
    }
    
    nextUnit() {
        logger.debug('Keyboard: Next unit');
        this.cycleUnits(1);
    }
    
    previousUnit() {
        logger.debug('Keyboard: Previous unit');
        this.cycleUnits(-1);
    }
    
    cycleUnits(direction) {
        if (!window.board) return;
        
        // Get all available units for current player
        const currentArmy = window.board.current_turn;
        const availableUnits = [];
        
        window.board.grid.forEach(tile => {
            if (tile.unit && tile.unit.army === currentArmy && !tile.unit.moved) {
                availableUnits.push(tile);
            }
        });
        
        if (availableUnits.length === 0) return;
        
        // Update index
        this.currentUnitIndex += direction;
        if (this.currentUnitIndex >= availableUnits.length) {
            this.currentUnitIndex = 0;
        } else if (this.currentUnitIndex < 0) {
            this.currentUnitIndex = availableUnits.length - 1;
        }
        
        // Select the unit
        const unitTile = availableUnits[this.currentUnitIndex];
        if (window.unitSelect) {
            window.unitSelect(unitTile);
        }
        
        // Center camera on unit (future feature)
        // if (window.centerCameraOn) {
        //     window.centerCameraOn(unitTile.x, unitTile.y);
        // }
    }
    
    zoomIn() {
        logger.debug('Keyboard: Zoom in');
        if (window.zoomIn) {
            window.zoomIn();
        }
    }
    
    zoomOut() {
        logger.debug('Keyboard: Zoom out');
        if (window.zoomOut) {
            window.zoomOut();
        }
    }
    
    zoomReset() {
        logger.debug('Keyboard: Zoom reset');
        if (window.zoomReset) {
            window.zoomReset();
        }
    }
    
    toggleHelp() {
        logger.debug('Keyboard: Toggle help');
        this.helpVisible = !this.helpVisible;
        this.helpOverlay.style.display = this.helpVisible ? 'block' : 'none';
    }
    
    toggleDebug() {
        logger.debug('Keyboard: Toggle debug');
        this.debugMode = !this.debugMode;
        
        if (window.logger) {
            window.logger.setLevel(this.debugMode ? 'DEBUG' : 'INFO');
        }
        
        // Show notification
        if (window.showNotification) {
            window.showNotification(`Debug mode: ${this.debugMode ? 'ON' : 'OFF'}`, 'info');
        }
    }
    
    refresh() {
        logger.debug('Keyboard: Refresh');
        if (window.rerender) {
            window.rerender();
        }
    }
    
    quickAction(number) {
        logger.debug(`Keyboard: Quick action ${number}`);
        
        // Check if action menu is open
        const actionMenu = document.querySelector('.action-menu:not([style*="display: none"])');
        if (actionMenu) {
            const buttons = actionMenu.querySelectorAll('button');
            if (buttons[number - 1]) {
                buttons[number - 1].click();
            }
        }
        
        // Check if modal is open
        const modal = document.querySelector('.modal[style*="display: block"]');
        if (modal) {
            const options = modal.querySelectorAll('option, button');
            if (options[number - 1]) {
                if (options[number - 1].tagName === 'OPTION') {
                    options[number - 1].selected = true;
                } else {
                    options[number - 1].click();
                }
            }
        }
    }
    
    /**
     * Enable/disable keyboard shortcuts
     */
    setEnabled(enabled) {
        this.enabled = enabled;
        logger.info(`Keyboard shortcuts ${enabled ? 'enabled' : 'disabled'}`);
    }
}

// Create and initialize global keyboard shortcuts
window.keyboardShortcuts = new KeyboardShortcuts();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.keyboardShortcuts.initialize();
    });
} else {
    window.keyboardShortcuts.initialize();
}

// Export for debugging
window.KeyboardShortcuts = KeyboardShortcuts;