/**
 * Input validators for AW-RPC game
 * Validates user inputs before sending to server
 */
class GameValidators {
    constructor(gameBoard) {
        this.board = gameBoard;
        this.validUnitTypes = [
            'INFANTRY', 'MECH', 'RECON', 'TANK', 'MEDIUMTANK', 'NEOTANK', 
            'MEGATANK', 'APC', 'ARTILLERY', 'ROCKET', 'ANTIAIR', 'MISSILE', 
            'PIPERUNNER', 'FIGHTER', 'BOMBER', 'BCOPTER', 'TCOPTER', 'STEALTH', 
            'BLACKBOMB', 'BATTLESHIP', 'CRUISER', 'LANDER', 'SUB', 'CARRIER', 
            'BLACKBOAT'
        ];
    }
    
    /**
     * Validate coordinates
     */
    validateCoordinates(x, y, checkBounds = true) {
        // Type check
        if (!Number.isInteger(x) || !Number.isInteger(y)) {
            throw new ValidationError('Coordinates must be integers');
        }
        
        // Negative check
        if (x < 0 || y < 0) {
            throw new ValidationError('Coordinates cannot be negative');
        }
        
        // Bounds check
        if (checkBounds && this.board) {
            if (x >= this.board.width || y >= this.board.height) {
                throw new ValidationError(`Coordinates out of bounds (${x},${y})`);
            }
        }
        
        return true;
    }
    
    /**
     * Validate unit type
     */
    validateUnitType(unitType) {
        if (!unitType || typeof unitType !== 'string') {
            throw new ValidationError('Unit type must be a string');
        }
        
        if (!this.validUnitTypes.includes(unitType)) {
            throw new ValidationError(`Invalid unit type: ${unitType}`);
        }
        
        return true;
    }
    
    /**
     * Validate funds amount
     */
    validateFunds(amount) {
        if (!Number.isInteger(amount)) {
            throw new ValidationError('Funds must be an integer');
        }
        
        if (amount < 0) {
            throw new ValidationError('Funds cannot be negative');
        }
        
        if (amount > 999999) {
            throw new ValidationError('Funds amount too large');
        }
        
        return true;
    }
    
    /**
     * Validate army color
     */
    validateArmy(army) {
        const validArmies = ['RED', 'BLUE', 'GREEN', 'YELLOW', 'BLACK'];
        
        if (!army || typeof army !== 'string') {
            throw new ValidationError('Army must be a string');
        }
        
        if (!validArmies.includes(army.toUpperCase())) {
            throw new ValidationError(`Invalid army: ${army}`);
        }
        
        return true;
    }
    
    /**
     * Validate cargo index
     */
    validateCargoIndex(index) {
        if (!Number.isInteger(index)) {
            throw new ValidationError('Cargo index must be an integer');
        }
        
        if (index < 0 || index > 1) {
            throw new ValidationError('Cargo index must be 0 or 1');
        }
        
        return true;
    }
    
    /**
     * Validate movement path
     */
    validateMovementPath(fromX, fromY, toX, toY) {
        this.validateCoordinates(fromX, fromY);
        this.validateCoordinates(toX, toY);
        
        // Check if same position
        if (fromX === toX && fromY === toY) {
            throw new ValidationError('Cannot move to same position');
        }
        
        // Check distance (optional - could be game rule based)
        const distance = Math.abs(fromX - toX) + Math.abs(fromY - toY);
        if (distance > 10) {
            throw new ValidationError('Movement distance too far');
        }
        
        return true;
    }
    
    /**
     * Validate RPC parameters based on method name
     */
    validateRpcParams(method, params) {
        try {
            switch (method) {
                case 'unit_create':
                    this.validateArmy(params.army);
                    this.validateUnitType(params.unit_type);
                    this.validateCoordinates(params.x, params.y);
                    break;
                    
                case 'unit_move':
                    this.validateMovementPath(params.x1, params.y1, params.x2, params.y2);
                    break;
                    
                case 'unit_attack':
                    this.validateCoordinates(params.x1, params.y1);
                    this.validateCoordinates(params.x2, params.y2);
                    break;
                    
                case 'cargo_board_transport':
                    this.validateCoordinates(params.cargo_x, params.cargo_y);
                    this.validateCoordinates(params.transport_x, params.transport_y);
                    break;
                    
                case 'cargo_exit_transport':
                    this.validateCoordinates(params.transport_x, params.transport_y);
                    this.validateCoordinates(params.exit_x, params.exit_y);
                    this.validateCargoIndex(params.cargo_index);
                    break;
                    
                case 'unit_capture':
                    this.validateCoordinates(params.x, params.y);
                    break;
                    
                case 'unit_join':
                    this.validateCoordinates(params.x, params.y);
                    this.validateCoordinates(params.x2, params.y2);
                    break;
                    
                // Add more method validations as needed
            }
            
            return true;
        } catch (error) {
            logger.warn(`Validation failed for ${method}:`, error.message);
            throw error;
        }
    }
    
    /**
     * Sanitize string input
     */
    sanitizeString(input, maxLength = 100) {
        if (typeof input !== 'string') {
            return '';
        }
        
        // Remove any HTML/script tags
        input = input.replace(/<[^>]*>/g, '');
        
        // Limit length
        if (input.length > maxLength) {
            input = input.substring(0, maxLength);
        }
        
        // Escape special characters
        return input
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#x27;');
    }
    
    /**
     * Validate and sanitize chat message
     */
    validateChatMessage(message) {
        if (!message || typeof message !== 'string') {
            throw new ValidationError('Message must be a non-empty string');
        }
        
        message = message.trim();
        
        if (message.length === 0) {
            throw new ValidationError('Message cannot be empty');
        }
        
        if (message.length > 500) {
            throw new ValidationError('Message too long (max 500 characters)');
        }
        
        return this.sanitizeString(message, 500);
    }
}

/**
 * Custom validation error class
 */
class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ValidationError';
    }
}

// Create global validator instance (will be initialized when board is ready)
window.gameValidators = null;

// Wrap jsonrpc to add validation
const originalJsonrpcWithValidation = window.jsonrpc;
window.jsonrpc = function(method, params, callback) {
    // Validate parameters if validator is available
    if (window.gameValidators) {
        try {
            window.gameValidators.validateRpcParams(method, params);
        } catch (error) {
            if (error instanceof ValidationError) {
                logger.error(`Validation error for ${method}:`, error.message);
                
                // Show user-friendly error
                if (window.errorHandler) {
                    window.errorHandler.showUserError(error.message, 'warning');
                }
                
                // Return rejected promise or call callback with error
                if (callback) {
                    callback({ error: error.message });
                    return;
                } else {
                    return Promise.reject(error);
                }
            }
            throw error;
        }
    }
    
    // Call original function
    return originalJsonrpcWithValidation.call(this, method, params, callback);
};