/**
 * Mobile Support Module - Handles touch events and mobile-specific features
 * Extracted from render.js as part of modularization effort
 */

import { tileAt } from './inputHandler.js';

// Ensure logger exists
if (typeof window.logger === 'undefined') {
    window.logger = console; // Fallback to console if logger.js isn't loaded
}
const logger = window.logger;

// ===== MOBILE STATE =====
const mobileState = {
    touchStartTime: 0,
    touchStartPos: { x: 0, y: 0 },
    longPressTimer: null,
    isDragging: false,
    notificationTimer: null
};

// ===== TOUCH SUPPORT =====

/**
 * Add touch support to canvas element
 * @param {HTMLElement} canvas - Canvas element
 */
export function addTouchSupport(canvas) {
    logger.debug('📱 Adding touch support to canvas...');
    
    // Convert touch coordinates to canvas coordinates
    function getTouchPos(touch) {
        const rect = canvas.getBoundingClientRect();
        return {
            x: touch.clientX - rect.left,
            y: touch.clientY - rect.top
        };
    }
    
    // Handle touch start (similar to mouse down)
    canvas.addEventListener('touchstart', function(e) {
        e.preventDefault();
        
        const touch = e.touches[0];
        const pos = getTouchPos(touch);
        mobileState.touchStartTime = Date.now();
        mobileState.touchStartPos = pos;
        mobileState.isDragging = false;
        
        // Start long press timer for context menu (500ms)
        mobileState.longPressTimer = setTimeout(() => {
            const tile = tileAt(pos.x, pos.y);
            if (tile) {
                // Simulate right-click for context menu
                const mockEvent = {
                    offsetX: pos.x,
                    offsetY: pos.y,
                    pageX: touch.pageX,
                    pageY: touch.pageY,
                    preventDefault: () => {},
                    stopPropagation: () => {}
                };
                
                if (window.handleTransportRightClick) {
                    window.handleTransportRightClick(tile, mockEvent);
                }
            }
        }, 500);
        
    }, { passive: false });
    
    // Handle touch move (similar to mouse move)
    canvas.addEventListener('touchmove', function(e) {
        e.preventDefault();
        
        const touch = e.touches[0];
        const pos = getTouchPos(touch);
        
        // Check if user is dragging
        const distance = Math.sqrt(
            Math.pow(pos.x - mobileState.touchStartPos.x, 2) + 
            Math.pow(pos.y - mobileState.touchStartPos.y, 2)
        );
        
        if (distance > 10) {
            mobileState.isDragging = true;
            // Cancel long press if dragging
            if (mobileState.longPressTimer) {
                clearTimeout(mobileState.longPressTimer);
                mobileState.longPressTimer = null;
            }
        }
        
        // Update cursor position for hover effects
        const mockEvent = {
            offsetX: pos.x,
            offsetY: pos.y
        };
        
        if (window.canvasMove) {
            window.canvasMove(mockEvent);
        }
        
    }, { passive: false });
    
    // Handle touch end (similar to mouse click)
    canvas.addEventListener('touchend', function(e) {
        e.preventDefault();
        
        // Clear long press timer
        if (mobileState.longPressTimer) {
            clearTimeout(mobileState.longPressTimer);
            mobileState.longPressTimer = null;
        }
        
        // If not dragging and quick tap, treat as click
        if (!mobileState.isDragging) {
            const touchDuration = Date.now() - mobileState.touchStartTime;
            const pos = mobileState.touchStartPos;
            
            if (touchDuration < 200) {
                // Quick tap - treat as normal click
                const mockEvent = {
                    offsetX: pos.x,
                    offsetY: pos.y,
                    altKey: false,
                    ctrlKey: false,
                    metaKey: false,
                    detail: 1
                };
                
                if (window.advanceWarsCanvasClick) {
                    window.advanceWarsCanvasClick(mockEvent);
                } else if (window.canvasClick) {
                    window.canvasClick(mockEvent);
                }
            } else if (touchDuration < 500) {
                // Medium tap - could add special handling here
                const mockEvent = {
                    offsetX: pos.x,
                    offsetY: pos.y,
                    altKey: false,
                    ctrlKey: false,
                    metaKey: false,
                    detail: 1
                };
                
                if (window.advanceWarsCanvasClick) {
                    window.advanceWarsCanvasClick(mockEvent);
                } else if (window.canvasClick) {
                    window.canvasClick(mockEvent);
                }
            }
            // Long press is handled by the timer
        }
        
        mobileState.isDragging = false;
        
    }, { passive: false });
    
    // Handle touch cancel
    canvas.addEventListener('touchcancel', function(e) {
        e.preventDefault();
        
        // Clear any timers
        if (mobileState.longPressTimer) {
            clearTimeout(mobileState.longPressTimer);
            mobileState.longPressTimer = null;
        }
        mobileState.isDragging = false;
    }, { passive: false });
    
    // Prevent default touch behavior on the canvas
    canvas.addEventListener('gesturestart', function(e) {
        e.preventDefault();
    });
    
    logger.debug('📱 Touch support added to canvas');
}

// ===== MOBILE NOTIFICATIONS =====

/**
 * Show mobile-friendly notification
 * @param {string} message - Notification message
 * @param {string} type - Notification type (info/error/success)
 */
export function showMobileNotification(message, type = 'info') {
    // Remove existing notification if any
    const existing = document.getElementById('mobile-notification');
    if (existing) {
        existing.remove();
    }
    
    // Clear existing timer
    if (mobileState.notificationTimer) {
        clearTimeout(mobileState.notificationTimer);
    }
    
    const notification = document.createElement('div');
    notification.id = 'mobile-notification';
    notification.className = 'mobile-notification';
    
    const bgColor = type === 'error' ? '#e74c3c' : 
                   type === 'success' ? '#27ae60' : '#3498db';
    
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: ${bgColor};
        color: white;
        padding: 12px 24px;
        border-radius: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        font-size: 14px;
        z-index: 10000;
        animation: slideUp 0.3s ease-out;
        max-width: 80%;
        text-align: center;
    `;
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    mobileState.notificationTimer = setTimeout(() => {
        notification.style.animation = 'slideDown 0.3s ease-out';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 3000);
}

// ===== MOBILE UI ADJUSTMENTS =====

/**
 * Apply mobile-specific UI adjustments
 */
export function applyMobileUIAdjustments() {
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (!isMobile) {
        return;
    }
    
    logger.info('📱 Applying mobile UI adjustments...');
    
    // Add mobile class to body
    document.body.classList.add('mobile-device');
    
    // Adjust button sizes for mobile
    const style = document.createElement('style');
    style.id = 'mobile-styles';
    style.textContent = `
        .mobile-device button {
            min-height: 44px;
            min-width: 44px;
            font-size: 16px;
        }
        
        .mobile-device .control-button {
            padding: 12px 20px;
            margin: 8px;
        }
        
        .mobile-device #gamebox {
            font-size: 14px;
        }
        
        .mobile-device .modal-content {
            width: 90%;
            max-width: 500px;
            margin: 10% auto;
        }
        
        @keyframes slideUp {
            from {
                transform: translateX(-50%) translateY(100%);
                opacity: 0;
            }
            to {
                transform: translateX(-50%) translateY(0);
                opacity: 1;
            }
        }
        
        @keyframes slideDown {
            from {
                transform: translateX(-50%) translateY(0);
                opacity: 1;
            }
            to {
                transform: translateX(-50%) translateY(100%);
                opacity: 0;
            }
        }
        
        /* Prevent text selection on mobile */
        .mobile-device {
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            -khtml-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
        }
        
        /* Larger touch targets for game tiles */
        .mobile-device .tile-highlight {
            min-width: 32px;
            min-height: 32px;
        }
    `;
    
    document.head.appendChild(style);
    
    // Disable pinch zoom on game canvas
    document.addEventListener('gesturestart', function(e) {
        e.preventDefault();
    });
    
    document.addEventListener('gesturechange', function(e) {
        e.preventDefault();
    });
    
    document.addEventListener('gestureend', function(e) {
        e.preventDefault();
    });
    
    // Add viewport meta tag if not present
    let viewport = document.querySelector('meta[name="viewport"]');
    if (!viewport) {
        viewport = document.createElement('meta');
        viewport.name = 'viewport';
        viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
        document.head.appendChild(viewport);
    }
    
    logger.info('✅ Mobile UI adjustments applied');
}

// ===== GESTURE SUPPORT =====

/**
 * Add gesture support for mobile devices
 * @param {HTMLElement} element - Element to add gestures to
 */
export function addGestureSupport(element) {
    let gestureStartDistance = 0;
    let gestureStartScale = 1;
    
    element.addEventListener('gesturestart', function(e) {
        e.preventDefault();
        gestureStartDistance = e.scale;
        gestureStartScale = window.currentScale || 1;
    });
    
    element.addEventListener('gesturechange', function(e) {
        e.preventDefault();
        
        // Calculate new scale
        const scale = gestureStartScale * (e.scale / gestureStartDistance);
        
        // Limit scale between 0.5 and 2.0
        const limitedScale = Math.max(0.5, Math.min(2.0, scale));
        
        // Apply scale if we have a scaling function
        if (window.setGameScale) {
            window.setGameScale(limitedScale);
        }
    });
    
    element.addEventListener('gestureend', function(e) {
        e.preventDefault();
        window.currentScale = window.currentScale || 1;
    });
}

// ===== MOBILE DETECTION =====

/**
 * Check if device is mobile
 * @returns {boolean} True if mobile device
 */
export function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
           (window.innerWidth <= 768);
}

/**
 * Check if device supports touch
 * @returns {boolean} True if touch is supported
 */
export function isTouchDevice() {
    return 'ontouchstart' in window || 
           navigator.maxTouchPoints > 0 || 
           navigator.msMaxTouchPoints > 0;
}

// ===== MODULE INITIALIZATION =====

/**
 * Initialize the mobile support module
 */
export function initializeMobileSupportModule() {
    logger.info('Initializing mobile support module...');
    
    // Apply mobile UI adjustments
    applyMobileUIAdjustments();
    
    // Set up global references for legacy compatibility
    if (window) {
        // Touch support
        window.addTouchSupport = addTouchSupport;
        
        // Notifications
        window.showMobileNotification = showMobileNotification;
        
        // Gestures
        window.addGestureSupport = addGestureSupport;
        
        // Detection
        window.isMobileDevice = isMobileDevice;
        window.isTouchDevice = isTouchDevice;
    }
    
    // Add touch support to canvas if it exists
    const canvas = document.querySelector('#draw canvas');
    if (canvas && isTouchDevice()) {
        addTouchSupport(canvas);
    }
    
    logger.info('Mobile support module initialized');
}

// Initialize on module load
initializeMobileSupportModule();