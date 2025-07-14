/**
 * Operation Queue for AW-RPC
 * Prevents race conditions by queuing operations and preventing double-clicks
 */
class OperationQueue {
    constructor() {
        this.queue = [];
        this.processing = false;
        this.operationInProgress = {};
        this.clickCooldown = 300; // ms between clicks on same element
        this.lastClicks = new Map();
        this.loadingOverlay = null;
        this.createLoadingUI();
    }
    
    /**
     * Create loading UI overlay
     */
    createLoadingUI() {
        // Create a subtle loading indicator
        const indicator = document.createElement('div');
        indicator.id = 'operation-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(52, 152, 219, 0.9);
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 14px;
            display: none;
            z-index: 9999;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        `;
        indicator.innerHTML = '<span class="spinner">⚙️</span> Processing...';
        document.body.appendChild(indicator);
        this.loadingOverlay = indicator;
        
        // Add spinning animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            #operation-indicator .spinner {
                display: inline-block;
                animation: spin 1s linear infinite;
            }
        `;
        document.head.appendChild(style);
    }
    
    /**
     * Check if click should be prevented (too soon after last click)
     */
    isDoubleClick(identifier) {
        const now = Date.now();
        const lastClick = this.lastClicks.get(identifier);
        
        if (lastClick && (now - lastClick) < this.clickCooldown) {
            logger.debug(`Double-click prevented for ${identifier}`);
            return true;
        }
        
        this.lastClicks.set(identifier, now);
        // Clean up old entries
        if (this.lastClicks.size > 100) {
            const oldestTime = now - 5000;
            for (const [key, time] of this.lastClicks) {
                if (time < oldestTime) {
                    this.lastClicks.delete(key);
                }
            }
        }
        
        return false;
    }
    
    /**
     * Add an operation to the queue
     */
    async add(operation, options = {}) {
        const {
            id = null,
            priority = 5,
            showLoading = true,
            preventDuplicate = true,
            description = 'Operation'
        } = options;
        
        // Check for double-click if ID provided
        if (id && this.isDoubleClick(id)) {
            logger.debug(`Skipping duplicate operation: ${id}`);
            return Promise.resolve({ skipped: true, reason: 'double-click' });
        }
        
        // Check if same operation is already in progress
        if (preventDuplicate && id && this.operationInProgress[id]) {
            logger.debug(`Operation already in progress: ${id}`);
            return Promise.resolve({ skipped: true, reason: 'in-progress' });
        }
        
        // Create operation object
        const op = {
            id,
            priority,
            showLoading,
            description,
            execute: operation,
            promise: null,
            resolve: null,
            reject: null
        };
        
        // Create promise for this operation
        op.promise = new Promise((resolve, reject) => {
            op.resolve = resolve;
            op.reject = reject;
        });
        
        // Add to queue (priority queue - higher priority first)
        this.queue.push(op);
        this.queue.sort((a, b) => b.priority - a.priority);
        
        logger.debug(`Added operation to queue: ${description} (${this.queue.length} in queue)`);
        
        // Start processing if not already
        if (!this.processing) {
            this.process();
        }
        
        return op.promise;
    }
    
    /**
     * Process the queue
     */
    async process() {
        if (this.processing) return;
        this.processing = true;
        
        while (this.queue.length > 0) {
            const op = this.queue.shift();
            
            // Mark as in progress
            if (op.id) {
                this.operationInProgress[op.id] = true;
            }
            
            // Show loading if requested
            if (op.showLoading && this.loadingOverlay) {
                this.showLoading(op.description);
            }
            
            try {
                logger.debug(`Executing operation: ${op.description}`);
                const result = await op.execute();
                op.resolve(result);
            } catch (error) {
                logger.error(`Operation failed: ${op.description}`, error);
                op.reject(error);
            } finally {
                // Clear in progress flag
                if (op.id) {
                    delete this.operationInProgress[op.id];
                }
                
                // Hide loading
                if (op.showLoading) {
                    this.hideLoading();
                }
            }
            
            // Small delay between operations to prevent overwhelming the server
            await this.sleep(50);
        }
        
        this.processing = false;
    }
    
    /**
     * Show loading indicator
     */
    showLoading(text = 'Processing...') {
        if (this.loadingOverlay) {
            this.loadingOverlay.innerHTML = `<span class="spinner">⚙️</span> ${text}`;
            this.loadingOverlay.style.display = 'block';
        }
    }
    
    /**
     * Hide loading indicator
     */
    hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.style.display = 'none';
        }
    }
    
    /**
     * Clear the queue
     */
    clear() {
        // Reject all pending operations
        for (const op of this.queue) {
            op.reject(new Error('Queue cleared'));
        }
        this.queue = [];
        this.operationInProgress = {};
    }
    
    /**
     * Get queue status
     */
    getStatus() {
        return {
            queueLength: this.queue.length,
            processing: this.processing,
            inProgress: Object.keys(this.operationInProgress)
        };
    }
    
    /**
     * Sleep utility
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Create global operation queue
window.operationQueue = new OperationQueue();

/**
 * Debounce function for UI events
 */
window.debounce = function(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
};

/**
 * Throttle function for continuous events
 */
window.throttle = function(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
};