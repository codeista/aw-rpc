// Debug script to identify mouse glitchiness

(function() {
    console.log('🐛 Mouse glitch debugger loaded');
    
    // Track all click events
    let clickCount = 0;
    let lastClickTime = 0;
    
    // Monitor canvas clicks
    const canvas = document.getElementById('draw');
    if (!canvas) {
        console.error('Canvas not found!');
        return;
    }
    
    // Log all click handlers
    console.log('Current onclick handler:', canvas.onclick ? canvas.onclick.name || 'anonymous' : 'none');
    console.log('Event listeners:', canvas._listeners || 'unknown');
    
    // Add debug overlay
    const overlay = document.createElement('div');
    overlay.id = 'mouse-debug-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background: rgba(0,0,0,0.8);
        color: white;
        padding: 10px;
        font-family: monospace;
        font-size: 12px;
        z-index: 10000;
        pointer-events: none;
    `;
    document.body.appendChild(overlay);
    
    function updateOverlay(info) {
        overlay.innerHTML = `
            <div>Click Count: ${clickCount}</div>
            <div>Last Click: ${info.x || '-'}, ${info.y || '-'}</div>
            <div>Tile: ${info.tileX || '-'}, ${info.tileY || '-'}</div>
            <div>Time Since Last: ${info.timeDiff || '-'}ms</div>
            <div>Handler: ${info.handler || '-'}</div>
            <div>Highlights: ${window.movementHighlights?.length || 0}</div>
            <div>Selected: ${window.board?.selected ? 'Yes' : 'No'}</div>
        `;
    }
    
    // Intercept clicks
    const originalOnclick = canvas.onclick;
    canvas.onclick = function(event) {
        clickCount++;
        const now = Date.now();
        const timeDiff = now - lastClickTime;
        lastClickTime = now;
        
        const tile = window.tileAt(event.offsetX, event.offsetY);
        
        const info = {
            x: event.offsetX,
            y: event.offsetY,
            tileX: tile?.x,
            tileY: tile?.y,
            timeDiff: timeDiff,
            handler: originalOnclick?.name || 'unknown'
        };
        
        updateOverlay(info);
        
        console.log('🖱️ Click intercepted:', info);
        
        // Call original handler
        if (originalOnclick) {
            return originalOnclick.call(this, event);
        }
    };
    
    // Monitor for handler changes
    let handlerCheckInterval = setInterval(() => {
        const currentHandler = canvas.onclick;
        if (currentHandler !== canvas.onclick) {
            console.warn('⚠️ Click handler changed!', currentHandler?.name);
        }
    }, 1000);
    
    // Add mouse move tracking
    canvas.addEventListener('mousemove', (event) => {
        const tile = window.tileAt(event.offsetX, event.offsetY);
        if (tile && tile.unit) {
            canvas.style.cursor = 'pointer';
        } else {
            canvas.style.cursor = 'default';
        }
    });
    
    // Cleanup function
    window.stopMouseDebug = function() {
        clearInterval(handlerCheckInterval);
        canvas.onclick = originalOnclick;
        overlay.remove();
        console.log('🐛 Mouse debugger stopped');
    };
    
    updateOverlay({});
    console.log('🐛 Mouse debugger active. Call stopMouseDebug() to stop.');
})();