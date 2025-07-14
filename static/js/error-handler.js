/**
 * Error Handler for AW-RPC game
 * Provides centralized error handling and user feedback
 */
class ErrorHandler {
    constructor() {
        this.errorQueue = [];
        this.isShowingError = false;
        this.maxRetries = 3;
        this.retryDelays = [1000, 2000, 4000]; // Exponential backoff
    }
    
    /**
     * Handle RPC errors with optional retry logic
     */
    async handleRpcError(error, method, params, options = {}) {
        const {
            retry = true,
            showUser = true,
            fallback = null,
            retryCount = 0
        } = options;
        
        logger.error(`RPC Error in ${method}:`, error);
        
        // Log to error tracking if available
        if (window.errorReporter) {
            window.errorReporter.log(error, { method, params });
        }
        
        // Determine error type and message
        const errorInfo = this.categorizeError(error);
        
        // Show user-friendly message
        if (showUser) {
            this.showUserError(errorInfo.userMessage, errorInfo.severity);
        }
        
        // Handle retry logic
        if (retry && retryCount < this.maxRetries && errorInfo.retryable) {
            const delay = this.retryDelays[retryCount] || 5000;
            logger.info(`Retrying ${method} in ${delay}ms (attempt ${retryCount + 1}/${this.maxRetries})`);
            
            await this.sleep(delay);
            
            // Retry the RPC call
            try {
                return await jsonrpc(method, params);
            } catch (retryError) {
                return this.handleRpcError(retryError, method, params, {
                    ...options,
                    retryCount: retryCount + 1
                });
            }
        }
        
        // Return fallback value if provided
        if (fallback !== null) {
            return fallback;
        }
        
        throw error;
    }
    
    /**
     * Categorize error and determine appropriate response
     */
    categorizeError(error) {
        const errorStr = error.toString().toLowerCase();
        const message = error.message || errorStr;
        
        // Network errors
        if (message.includes('network') || message.includes('fetch')) {
            return {
                type: 'network',
                userMessage: 'Connection lost. Please check your internet connection.',
                severity: 'error',
                retryable: true
            };
        }
        
        // Server errors
        if (message.includes('500') || message.includes('internal server')) {
            return {
                type: 'server',
                userMessage: 'Server error. Please try again later.',
                severity: 'error',
                retryable: true
            };
        }
        
        // Game state errors
        if (message.includes('invalid move') || message.includes('not your turn')) {
            return {
                type: 'game_state',
                userMessage: message,
                severity: 'warning',
                retryable: false
            };
        }
        
        // Validation errors
        if (message.includes('invalid') || message.includes('validation')) {
            return {
                type: 'validation',
                userMessage: message,
                severity: 'warning',
                retryable: false
            };
        }
        
        // Permission errors
        if (message.includes('permission') || message.includes('unauthorized')) {
            return {
                type: 'permission',
                userMessage: 'You do not have permission to perform this action.',
                severity: 'error',
                retryable: false
            };
        }
        
        // Default
        return {
            type: 'unknown',
            userMessage: 'An unexpected error occurred. Please try again.',
            severity: 'error',
            retryable: true
        };
    }
    
    /**
     * Show error message to user
     */
    showUserError(message, severity = 'error') {
        // Queue the error
        this.errorQueue.push({ message, severity, timestamp: Date.now() });
        
        // Process queue if not already showing an error
        if (!this.isShowingError) {
            this.processErrorQueue();
        }
    }
    
    /**
     * Process error queue
     */
    async processErrorQueue() {
        if (this.errorQueue.length === 0) {
            this.isShowingError = false;
            return;
        }
        
        this.isShowingError = true;
        const error = this.errorQueue.shift();
        
        // Create error element
        const errorEl = this.createErrorElement(error.message, error.severity);
        document.body.appendChild(errorEl);
        
        // Animate in
        requestAnimationFrame(() => {
            errorEl.style.opacity = '1';
            errorEl.style.transform = 'translateY(0)';
        });
        
        // Auto-hide after delay
        const delay = error.severity === 'error' ? 5000 : 3000;
        await this.sleep(delay);
        
        // Animate out
        errorEl.style.opacity = '0';
        errorEl.style.transform = 'translateY(-20px)';
        
        // Remove element
        await this.sleep(300);
        errorEl.remove();
        
        // Process next error
        this.processErrorQueue();
    }
    
    /**
     * Create error display element
     */
    createErrorElement(message, severity) {
        const el = document.createElement('div');
        el.className = `game-error-notification ${severity}`;
        el.innerHTML = `
            <div class="error-icon">${this.getIcon(severity)}</div>
            <div class="error-message">${this.escapeHtml(message)}</div>
            <button class="error-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        // Add styles
        el.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            min-width: 300px;
            max-width: 500px;
            padding: 16px 20px;
            background: ${severity === 'error' ? '#e74c3c' : '#f39c12'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            gap: 12px;
            opacity: 0;
            transform: translateY(-20px);
            transition: all 0.3s ease;
            z-index: 10000;
            font-size: 14px;
        `;
        
        return el;
    }
    
    /**
     * Get icon for severity
     */
    getIcon(severity) {
        switch (severity) {
            case 'error':
                return '❌';
            case 'warning':
                return '⚠️';
            case 'info':
                return 'ℹ️';
            default:
                return '📢';
        }
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Sleep utility
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Create error boundary for critical functions
     */
    wrapFunction(fn, options = {}) {
        return async (...args) => {
            try {
                return await fn(...args);
            } catch (error) {
                logger.error(`Error in wrapped function ${fn.name}:`, error);
                
                if (options.showUser !== false) {
                    const errorInfo = this.categorizeError(error);
                    this.showUserError(errorInfo.userMessage, errorInfo.severity);
                }
                
                if (options.fallback !== undefined) {
                    return options.fallback;
                }
                
                if (options.rethrow !== false) {
                    throw error;
                }
            }
        };
    }
}

// Create global error handler instance
window.errorHandler = new ErrorHandler();

// Wrap jsonrpc function to add automatic error handling
const originalJsonrpc = window.jsonrpc;
window.jsonrpc = function(method, params, callback) {
    const promise = originalJsonrpc.call(this, method, params, callback);
    
    // If no callback provided, add error handling to promise
    if (!callback && promise && promise.catch) {
        return promise.catch(error => {
            return window.errorHandler.handleRpcError(error, method, params, {
                retry: true,
                showUser: true
            });
        });
    }
    
    return promise;
};