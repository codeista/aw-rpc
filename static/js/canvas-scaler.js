/**
 * Canvas Scaler - Simplified scaling that works with coordinate system
 * This now only handles visual scaling, coordinate conversion is done by coordinate-system.js
 */

(function() {
    const logger = window.logger || console;
    
    // Configuration
    const BASE_TILE_SIZE = 16; // Original tile size in pixels
    const MIN_TILE_SIZE = 24; // Minimum visual tile size for playability
    const MAX_TILE_SIZE = 64; // Maximum visual tile size
    const CONTAINER_PADDING = 40; // Padding around the canvas in the container
    
    let currentScale = 1;
    let containerSize = { width: 0, height: 0 };
    let mapSize = { width: 0, height: 0 };
    
    /**
     * Calculate the optimal scale for the canvas based on container and map size
     */
    function calculateOptimalScale() {
        const container = document.querySelector('.board-container');
        if (!container || !window.board) return 1;
        
        // Get container dimensions
        const containerRect = container.getBoundingClientRect();
        containerSize.width = containerRect.width - CONTAINER_PADDING * 2;
        containerSize.height = containerRect.height - CONTAINER_PADDING * 2;
        
        // Get map dimensions
        mapSize.width = window.board.width;
        mapSize.height = window.board.height;
        
        // Calculate canvas size at base scale
        const baseCanvasWidth = mapSize.width * BASE_TILE_SIZE;
        const baseCanvasHeight = mapSize.height * BASE_TILE_SIZE;
        
        // Calculate scale to fit container
        const scaleX = containerSize.width / baseCanvasWidth;
        const scaleY = containerSize.height / baseCanvasHeight;
        const fitScale = Math.min(scaleX, scaleY);
        
        // Calculate scale to achieve desired tile size
        const desiredTileSize = Math.max(MIN_TILE_SIZE, Math.min(MAX_TILE_SIZE, 
            Math.min(containerSize.width / mapSize.width, containerSize.height / mapSize.height)));
        const tileScale = desiredTileSize / BASE_TILE_SIZE;
        
        // Use the smaller of the two scales to ensure it fits
        const optimalScale = Math.min(fitScale, tileScale);
        
        logger.info('📐 Calculated optimal scale:', {
            containerSize,
            mapSize,
            baseCanvas: { width: baseCanvasWidth, height: baseCanvasHeight },
            fitScale: fitScale.toFixed(3),
            tileScale: tileScale.toFixed(3),
            optimalScale: optimalScale.toFixed(3),
            resultingTileSize: (optimalScale * BASE_TILE_SIZE).toFixed(1)
        });
        
        return optimalScale;
    }
    
    /**
     * Apply scale to the canvas element
     */
    function applyScale(scale) {
        const canvas = document.querySelector('#draw canvas');
        if (!canvas) return;
        
        currentScale = scale;
        
        // Remove CSS constraints that interfere with scaling
        canvas.style.maxWidth = 'none';
        canvas.style.maxHeight = 'none';
        canvas.style.width = 'auto';
        canvas.style.height = 'auto';
        canvas.style.minWidth = '0';
        canvas.style.minHeight = '0';
        
        // Apply CSS transform for scaling
        canvas.style.transform = `scale(${scale})`;
        canvas.style.transformOrigin = 'center center';
        
        // Update visual calibration if it exists
        if (window.visualCalibration) {
            // Visual calibration needs to account for the scale
            window.visualCalibration.setScale(scale);
        }
        
        logger.info('🔍 Applied canvas scale:', scale.toFixed(3));
    }
    
    /**
     * Convert page coordinates to canvas coordinates accounting for scale
     */
    function pageToCanvas(pageX, pageY) {
        const canvas = document.querySelector('#draw canvas');
        if (!canvas) return { x: 0, y: 0 };
        
        const rect = canvas.getBoundingClientRect();
        
        // Get the actual canvas dimensions (unscaled)
        const canvasWidth = canvas.width;
        const canvasHeight = canvas.height;
        
        // When transform scale is applied with transform-origin center,
        // the canvas grows/shrinks from its center point
        // getBoundingClientRect() returns the scaled dimensions
        
        // Calculate the actual scaled dimensions
        const scaledWidth = canvasWidth * currentScale;
        const scaledHeight = canvasHeight * currentScale;
        
        // The scaled canvas is centered in the bounding rect
        // Calculate the offset to the actual canvas content
        const offsetX = (rect.width - scaledWidth) / 2;
        const offsetY = (rect.height - scaledHeight) / 2;
        
        // Convert page coordinates to scaled canvas coordinates
        const relativeX = pageX - rect.left - offsetX;
        const relativeY = pageY - rect.top - offsetY;
        
        // Convert to unscaled canvas coordinates
        const canvasX = relativeX / currentScale;
        const canvasY = relativeY / currentScale;
        
        // Debug logging
        if (window.DEBUG_CANVAS_SCALER) {
            logger.debug('pageToCanvas:', {
                page: { x: pageX, y: pageY },
                rect: { left: rect.left, top: rect.top, width: rect.width, height: rect.height },
                canvas: { width: canvasWidth, height: canvasHeight },
                scale: currentScale,
                scaled: { width: scaledWidth, height: scaledHeight },
                offset: { x: offsetX, y: offsetY },
                relative: { x: relativeX, y: relativeY },
                result: { x: canvasX, y: canvasY }
            });
        }
        
        return { x: canvasX, y: canvasY };
    }
    
    /**
     * Convert canvas coordinates to tile coordinates
     */
    function canvasToTile(canvasX, canvasY) {
        // Account for the extra tile height offset (from render_legacy.js)
        const adjustedY = canvasY - BASE_TILE_SIZE;
        
        const tileX = Math.floor(canvasX / BASE_TILE_SIZE);
        const tileY = Math.floor(adjustedY / BASE_TILE_SIZE);
        
        // Bounds checking
        if (!window.board || tileY < 0 || tileY >= window.board.height || tileX < 0 || tileX >= window.board.width) {
            return { x: -1, y: -1 };
        }
        
        return { x: tileX, y: tileY };
    }
    
    /**
     * Initialize the scaler when the board is ready
     */
    function initialize() {
        if (!window.board || !window.two) {
            setTimeout(initialize, 100);
            return;
        }
        
        // Calculate and apply initial scale
        const scale = calculateOptimalScale();
        applyScale(scale);
        
        // Monitor for window resize
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                const newScale = calculateOptimalScale();
                applyScale(newScale);
            }, 250);
        });
        
        // Override the zoom functions to work with our scaling
        const originalZoomIn = window.zoomIn;
        const originalZoomOut = window.zoomOut;
        const originalZoomReset = window.zoomReset;
        const originalZoomFit = window.zoomFit;
        
        window.zoomIn = function() {
            const newScale = Math.min(currentScale * 1.2, MAX_TILE_SIZE / BASE_TILE_SIZE);
            applyScale(newScale);
            logger.info('🔍 Zoom in to scale:', newScale.toFixed(3));
        };
        
        window.zoomOut = function() {
            const newScale = Math.max(currentScale / 1.2, MIN_TILE_SIZE / BASE_TILE_SIZE);
            applyScale(newScale);
            logger.info('🔍 Zoom out to scale:', newScale.toFixed(3));
        };
        
        window.zoomReset = function() {
            applyScale(1);
            logger.info('🔍 Zoom reset to scale: 1.000');
        };
        
        window.zoomFit = function() {
            const optimalScale = calculateOptimalScale();
            applyScale(optimalScale);
            logger.info('🔍 Zoom fit to scale:', optimalScale.toFixed(3));
        };
        
        logger.info('✅ Canvas scaler initialized');
    }
    
    // Start initialization
    setTimeout(initialize, 500);
    
    // Export API
    window.canvasScaler = {
        getScale: () => currentScale,
        setScale: applyScale,
        pageToCanvas: pageToCanvas,
        canvasToTile: canvasToTile,
        pageToTile: (pageX, pageY) => {
            const canvasCoords = pageToCanvas(pageX, pageY);
            return canvasToTile(canvasCoords.x, canvasCoords.y);
        },
        recalculate: () => {
            const scale = calculateOptimalScale();
            applyScale(scale);
        }
    };
    
})();