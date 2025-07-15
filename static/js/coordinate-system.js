/**
 * Unified Coordinate System for Advance Wars RPC
 * 
 * This module handles all coordinate conversions between:
 * - Page coordinates (mouse events)
 * - Canvas coordinates (drawing context)
 * - Tile coordinates (game logic)
 * 
 * Automatically adapts to:
 * - Different map sizes
 * - Canvas scaling/zooming
 * - Container resizing
 * - Board updates
 */

class CoordinateSystem {
    constructor() {
        // Map dimensions
        this.mapWidth = 0;
        this.mapHeight = 0;
        
        // Canvas properties
        this.tileSize = 16; // Base tile size in pixels
        this.canvasScale = 1;
        this.canvas = null;
        this.canvasRect = null;
        
        // Container properties
        this.container = null;
        this.containerRect = null;
        
        // Offsets for centered canvas
        this.canvasOffset = { x: 0, y: 0 };
        
        // Extra height for sprite overlap (units can extend above their tile)
        this.extraTopHeight = this.tileSize;
        
        // Debug mode
        this.debug = false;
        
        // Initialize
        this.init();
    }
    
    init() {
        // Set up board update listener
        this.setupBoardListener();
        
        // Set up resize observer for container
        this.setupResizeObserver();
        
        // Initial update if board exists
        if (window.board) {
            this.updateFromBoard(window.board);
        }
    }
    
    setupBoardListener() {
        // Hook into the global update function to detect board changes
        if (window.update) {
            const originalUpdate = window.update;
            window.update = () => {
                originalUpdate();
                // After update completes, check if board changed
                if (window.board) {
                    this.updateFromBoard(window.board);
                }
            };
        }
    }
    
    setupResizeObserver() {
        // Watch for container size changes
        const resizeObserver = new ResizeObserver(() => {
            this.updateCanvasProperties();
        });
        
        // Start observing when container is available
        const checkContainer = setInterval(() => {
            const container = document.querySelector('.board-container') || document.getElementById('draw');
            if (container) {
                this.container = container;
                resizeObserver.observe(container);
                clearInterval(checkContainer);
                this.updateCanvasProperties();
            }
        }, 100);
    }
    
    updateFromBoard(board) {
        // Check if map dimensions changed
        if (board.width !== this.mapWidth || board.height !== this.mapHeight) {
            this.mapWidth = board.width;
            this.mapHeight = board.height;
            
            if (this.debug) {
                console.log(`📐 Map size updated: ${this.mapWidth}x${this.mapHeight}`);
            }
            
            // Recalculate canvas properties
            this.updateCanvasProperties();
        }
    }
    
    updateCanvasProperties() {
        // Find canvas element
        this.canvas = document.querySelector('#draw canvas');
        if (!this.canvas) return;
        
        // Get canvas dimensions and position
        this.canvasRect = this.canvas.getBoundingClientRect();
        
        // Get container dimensions
        if (this.container) {
            this.containerRect = this.container.getBoundingClientRect();
        }
        
        // Calculate scale from canvas transform or style
        const transform = window.getComputedStyle(this.canvas).transform;
        if (transform && transform !== 'none') {
            const matrix = new DOMMatrix(transform);
            this.canvasScale = matrix.a; // X scale factor
        } else {
            // Fallback: calculate from rendered vs actual size
            if (this.canvas.width > 0) {
                this.canvasScale = this.canvasRect.width / this.canvas.width;
            }
        }
        
        // Calculate centering offset
        if (this.containerRect && this.canvasRect) {
            this.canvasOffset.x = this.canvasRect.left - this.containerRect.left;
            this.canvasOffset.y = this.canvasRect.top - this.containerRect.top;
        }
        
        if (this.debug) {
            console.log('📐 Canvas properties updated:', {
                scale: this.canvasScale,
                offset: this.canvasOffset,
                canvasSize: { w: this.canvas.width, h: this.canvas.height },
                renderedSize: { w: this.canvasRect.width, h: this.canvasRect.height }
            });
        }
    }
    
    /**
     * Convert page coordinates (from mouse event) to tile coordinates
     */
    pageToTile(pageX, pageY) {
        if (!this.canvas || !this.canvasRect) {
            this.updateCanvasProperties();
            if (!this.canvas) return null;
        }
        
        // Convert page coords to canvas-relative coords
        const canvasX = pageX - this.canvasRect.left;
        const canvasY = pageY - this.canvasRect.top;
        
        // Account for scale
        const unscaledX = canvasX / this.canvasScale;
        const unscaledY = canvasY / this.canvasScale;
        
        // Convert to tile coordinates
        return this.canvasToTile(unscaledX, unscaledY);
    }
    
    /**
     * Convert canvas coordinates to tile coordinates
     */
    canvasToTile(canvasX, canvasY) {
        // Account for the extra height at the top for sprite overlap
        const adjustedY = canvasY - this.extraTopHeight;
        
        // Calculate tile coordinates
        const tileX = Math.floor(canvasX / this.tileSize);
        const tileY = Math.floor(adjustedY / this.tileSize);
        
        // Bounds checking
        if (tileX < 0 || tileX >= this.mapWidth || tileY < 0 || tileY >= this.mapHeight) {
            return null;
        }
        
        // Find the tile in the board grid
        if (window.board && window.board.grid) {
            const tile = window.board.grid.find(t => t.x === tileX && t.y === tileY);
            return tile || null;
        }
        
        return null;
    }
    
    /**
     * Convert offset coordinates (from click event) to tile coordinates
     */
    offsetToTile(offsetX, offsetY) {
        // offsetX/offsetY are relative to the target element (canvas)
        // They should already account for any scaling applied via CSS
        return this.canvasToTile(offsetX, offsetY);
    }
    
    /**
     * Get the current scale factor
     */
    getScale() {
        return this.canvasScale;
    }
    
    /**
     * Enable/disable debug mode
     */
    setDebug(enabled) {
        this.debug = enabled;
        if (enabled) {
            console.log('📐 Coordinate System Debug Mode Enabled');
            this.updateCanvasProperties();
        }
    }
    
    /**
     * Force a recalculation of all properties
     */
    recalculate() {
        if (window.board) {
            this.updateFromBoard(window.board);
        }
        this.updateCanvasProperties();
    }
}

// Create global instance
window.coordinateSystem = new CoordinateSystem();

// Also expose for debugging
window.CoordinateSystem = CoordinateSystem;

console.log('✅ Unified Coordinate System initialized');