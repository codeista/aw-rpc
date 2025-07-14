/**
 * Cargo Selection UI for AW-RPC
 * Allows players to select which unit to unload from transports
 */
class CargoSelectionUI {
    constructor() {
        this.modal = null;
        this.selectedIndex = null;
        this.onSelectCallback = null;
        this.createModal();
    }
    
    /**
     * Create the modal HTML structure
     */
    createModal() {
        // Create modal container
        this.modal = document.createElement('div');
        this.modal.id = 'cargo-selection-modal';
        this.modal.className = 'modal';
        this.modal.style.display = 'none';
        
        // Modal content
        this.modal.innerHTML = `
            <div class="modal-content cargo-modal">
                <div class="cargo-modal-header">
                    <h3>Select Unit to Unload</h3>
                    <span class="close" onclick="window.cargoSelection.hide()">&times;</span>
                </div>
                <div class="cargo-modal-body">
                    <div id="cargo-units-list" class="cargo-units-list">
                        <!-- Units will be dynamically added here -->
                    </div>
                </div>
                <div class="cargo-modal-footer">
                    <button class="btn btn-secondary" onclick="window.cargoSelection.hide()">Cancel</button>
                    <button id="cargo-unload-btn" class="btn btn-primary" onclick="window.cargoSelection.confirmSelection()" disabled>
                        Unload Selected
                    </button>
                </div>
            </div>
        `;
        
        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .cargo-modal {
                background: linear-gradient(135deg, #2c3e50, #34495e);
                margin: 10% auto;
                padding: 0;
                border: 2px solid #3498db;
                border-radius: 10px;
                width: 90%;
                max-width: 500px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                animation: modalFadeIn 0.3s ease;
                overflow: hidden;
            }
            
            .cargo-modal-header {
                background: linear-gradient(90deg, #2c3e50 0%, #34495e 100%);
                padding: 20px;
                border-bottom: 1px solid #3498db;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .cargo-modal-header h3 {
                margin: 0;
                color: #ecf0f1;
                font-size: 20px;
            }
            
            .cargo-modal-body {
                padding: 20px;
                max-height: 400px;
                overflow-y: auto;
            }
            
            .cargo-units-list {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .cargo-unit-item {
                background: rgba(52, 152, 219, 0.1);
                border: 2px solid rgba(52, 152, 219, 0.3);
                border-radius: 8px;
                padding: 16px;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 16px;
            }
            
            .cargo-unit-item:hover {
                background: rgba(52, 152, 219, 0.2);
                border-color: #3498db;
                transform: translateX(4px);
            }
            
            .cargo-unit-item.selected {
                background: rgba(52, 152, 219, 0.3);
                border-color: #3498db;
                box-shadow: 0 0 10px rgba(52, 152, 219, 0.5);
            }
            
            .cargo-unit-icon {
                width: 48px;
                height: 48px;
                background: rgba(0,0,0,0.3);
                border-radius: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
            }
            
            .cargo-unit-info {
                flex: 1;
            }
            
            .cargo-unit-name {
                font-size: 18px;
                color: #ecf0f1;
                font-weight: bold;
                margin-bottom: 4px;
            }
            
            .cargo-unit-stats {
                display: flex;
                gap: 20px;
                font-size: 14px;
                color: #bdc3c7;
            }
            
            .cargo-unit-stat {
                display: flex;
                align-items: center;
                gap: 4px;
            }
            
            .cargo-unit-index {
                background: rgba(52, 152, 219, 0.3);
                color: #3498db;
                padding: 8px 12px;
                border-radius: 50%;
                font-weight: bold;
                font-size: 16px;
            }
            
            .cargo-modal-footer {
                background: rgba(0,0,0,0.2);
                padding: 16px 20px;
                border-top: 1px solid rgba(255,255,255,0.1);
                display: flex;
                justify-content: flex-end;
                gap: 12px;
            }
            
            .btn-secondary {
                background: rgba(255,255,255,0.1);
                color: #ecf0f1;
                border: 1px solid rgba(255,255,255,0.2);
            }
            
            .btn-secondary:hover {
                background: rgba(255,255,255,0.2);
            }
            
            .empty-cargo {
                text-align: center;
                padding: 40px;
                color: #7f8c8d;
                font-size: 16px;
            }
            
            @keyframes modalFadeIn {
                from {
                    opacity: 0;
                    transform: translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(this.modal);
        
        // Click outside to close
        this.modal.onclick = (event) => {
            if (event.target === this.modal) {
                this.hide();
            }
        };
        
        // Keyboard support
        document.addEventListener('keydown', (event) => {
            if (this.modal.style.display === 'block') {
                if (event.key === 'Escape') {
                    this.hide();
                } else if (event.key >= '1' && event.key <= '9') {
                    const index = parseInt(event.key) - 1;
                    this.selectUnit(index);
                } else if (event.key === 'Enter' && this.selectedIndex !== null) {
                    this.confirmSelection();
                }
            }
        });
    }
    
    /**
     * Show the cargo selection modal
     * @param {Array} cargoUnits - Array of units in the transport
     * @param {Function} onSelect - Callback when a unit is selected
     */
    show(cargoUnits, onSelect) {
        if (!cargoUnits || cargoUnits.length === 0) {
            logger.warn('No cargo units to display');
            return;
        }
        
        this.selectedIndex = null;
        this.onSelectCallback = onSelect;
        
        // Populate units list
        const listElement = document.getElementById('cargo-units-list');
        listElement.innerHTML = '';
        
        cargoUnits.forEach((unit, index) => {
            const unitElement = this.createUnitElement(unit, index);
            listElement.appendChild(unitElement);
        });
        
        // Reset button state
        document.getElementById('cargo-unload-btn').disabled = true;
        
        // Show modal
        this.modal.style.display = 'block';
        logger.info('Cargo selection modal shown with', cargoUnits.length, 'units');
    }
    
    /**
     * Create a unit element for the list
     */
    createUnitElement(unit, index) {
        const div = document.createElement('div');
        div.className = 'cargo-unit-item';
        div.dataset.index = index;
        
        // Get unit icon (you can customize this based on unit type)
        const unitIcon = this.getUnitIcon(unit.unit_type);
        
        div.innerHTML = `
            <div class="cargo-unit-index">${index + 1}</div>
            <div class="cargo-unit-icon">${unitIcon}</div>
            <div class="cargo-unit-info">
                <div class="cargo-unit-name">${this.formatUnitName(unit.unit_type)}</div>
                <div class="cargo-unit-stats">
                    <div class="cargo-unit-stat">
                        <span style="color: #e74c3c;">❤️</span>
                        <span>${unit.health || unit.hp || 10}/10 HP</span>
                    </div>
                    <div class="cargo-unit-stat">
                        <span style="color: #f39c12;">⛽</span>
                        <span>${unit.fuel || 99} Fuel</span>
                    </div>
                    <div class="cargo-unit-stat">
                        <span style="color: #95a5a6;">🎯</span>
                        <span>${unit.ammo || 'N/A'} Ammo</span>
                    </div>
                </div>
            </div>
        `;
        
        div.onclick = () => this.selectUnit(index);
        
        return div;
    }
    
    /**
     * Get icon for unit type
     */
    getUnitIcon(unitType) {
        const icons = {
            'INFANTRY': '🚶',
            'MECH': '🤖',
            'RECON': '🚗',
            'TANK': '🚙',
            'MEDIUMTANK': '🚜',
            'NEOTANK': '🛡️',
            'MEGATANK': '🦾',
            'APC': '🚐',
            'ARTILLERY': '🎯',
            'ROCKET': '🚀',
            'ANTIAIR': '🔫',
            'MISSILE': '🎪',
            'FIGHTER': '✈️',
            'BOMBER': '💣',
            'BCOPTER': '🚁',
            'TCOPTER': '🚁',
            'STEALTH': '👻',
            'BLACKBOMB': '💣',
            'BATTLESHIP': '🚢',
            'CRUISER': '⛵',
            'LANDER': '🛥️',
            'SUB': '🚤',
            'CARRIER': '🛳️',
            'BLACKBOAT': '⚫'
        };
        
        return icons[unitType] || '🎮';
    }
    
    /**
     * Format unit name for display
     */
    formatUnitName(unitType) {
        const names = {
            'INFANTRY': 'Infantry',
            'MECH': 'Mech',
            'RECON': 'Recon',
            'TANK': 'Tank',
            'MEDIUMTANK': 'Medium Tank',
            'NEOTANK': 'Neo Tank',
            'MEGATANK': 'Mega Tank',
            'APC': 'APC',
            'ARTILLERY': 'Artillery',
            'ROCKET': 'Rocket',
            'ANTIAIR': 'Anti-Air',
            'MISSILE': 'Missile',
            'FIGHTER': 'Fighter',
            'BOMBER': 'Bomber',
            'BCOPTER': 'Battle Copter',
            'TCOPTER': 'Transport Copter',
            'STEALTH': 'Stealth',
            'BLACKBOMB': 'Black Bomb',
            'BATTLESHIP': 'Battleship',
            'CRUISER': 'Cruiser',
            'LANDER': 'Lander',
            'SUB': 'Submarine',
            'CARRIER': 'Carrier',
            'BLACKBOAT': 'Black Boat'
        };
        
        return names[unitType] || unitType;
    }
    
    /**
     * Select a unit
     */
    selectUnit(index) {
        // Remove previous selection
        document.querySelectorAll('.cargo-unit-item').forEach((el, i) => {
            if (i === index) {
                el.classList.add('selected');
            } else {
                el.classList.remove('selected');
            }
        });
        
        this.selectedIndex = index;
        document.getElementById('cargo-unload-btn').disabled = false;
        logger.debug('Selected cargo unit at index', index);
    }
    
    /**
     * Confirm selection and trigger callback
     */
    confirmSelection() {
        if (this.selectedIndex !== null && this.onSelectCallback) {
            logger.info('Confirmed cargo selection:', this.selectedIndex);
            this.onSelectCallback(this.selectedIndex);
            this.hide();
        }
    }
    
    /**
     * Hide the modal
     */
    hide() {
        this.modal.style.display = 'none';
        this.selectedIndex = null;
        this.onSelectCallback = null;
        logger.debug('Cargo selection modal hidden');
    }
}

// Create global instance
window.cargoSelection = new CargoSelectionUI();