/**
 * Error Notification System for Advance Wars RPC
 * Provides user-friendly error messages for RPC failures
 */

class ErrorNotificationSystem {
    constructor() {
        this.container = null;
        this.activeNotifications = new Set();
        this.init();
    }

    init() {
        // Create notification container
        this.container = document.createElement('div');
        this.container.id = 'error-notification-container';
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            pointer-events: none;
        `;
        document.body.appendChild(this.container);
    }

    /**
     * Show error notification
     * @param {string} message - Error message to display
     * @param {string} detail - Additional detail (optional)
     * @param {number} duration - Duration in ms (default 5000)
     */
    show(message, detail = '', duration = 5000) {
        const notification = document.createElement('div');
        const id = Date.now() + Math.random();
        
        notification.className = 'error-notification';
        notification.style.cssText = `
            background: #dc3545;
            color: white;
            padding: 12px 20px;
            margin-bottom: 10px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            pointer-events: auto;
            cursor: pointer;
            animation: slideIn 0.3s ease-out;
            max-width: 350px;
            word-wrap: break-word;
        `;

        // Create message content
        let content = `<strong>⚠️ Error</strong><br>${this.escapeHtml(message)}`;
        if (detail) {
            content += `<br><small style="opacity: 0.8">${this.escapeHtml(detail)}</small>`;
        }
        
        notification.innerHTML = content;
        notification.dataset.id = id;
        
        // Click to dismiss
        notification.addEventListener('click', () => {
            this.dismiss(id);
        });
        
        this.container.appendChild(notification);
        this.activeNotifications.add(id);
        
        // Auto dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                this.dismiss(id);
            }, duration);
        }
        
        return id;
    }

    /**
     * Show success notification
     */
    showSuccess(message, duration = 3000) {
        const notification = document.createElement('div');
        const id = Date.now() + Math.random();
        
        notification.className = 'success-notification';
        notification.style.cssText = `
            background: #28a745;
            color: white;
            padding: 12px 20px;
            margin-bottom: 10px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            pointer-events: auto;
            cursor: pointer;
            animation: slideIn 0.3s ease-out;
            max-width: 350px;
        `;
        
        notification.innerHTML = `<strong>✅ Success</strong><br>${this.escapeHtml(message)}`;
        notification.dataset.id = id;
        
        notification.addEventListener('click', () => {
            this.dismiss(id);
        });
        
        this.container.appendChild(notification);
        this.activeNotifications.add(id);
        
        if (duration > 0) {
            setTimeout(() => {
                this.dismiss(id);
            }, duration);
        }
    }

    /**
     * Dismiss notification
     */
    dismiss(id) {
        const notification = this.container.querySelector(`[data-id="${id}"]`);
        if (notification && this.activeNotifications.has(id)) {
            notification.style.animation = 'slideOut 0.3s ease-in';
            notification.addEventListener('animationend', () => {
                notification.remove();
                this.activeNotifications.delete(id);
            });
        }
    }

    /**
     * Clear all notifications
     */
    clearAll() {
        this.activeNotifications.forEach(id => this.dismiss(id));
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
     * Parse RPC error and show appropriate message
     */
    showRpcError(error, method) {
        let message = `Failed to execute: ${method}`;
        let detail = '';

        if (error.error) {
            if (error.error.message) {
                message = error.error.message;
            }
            if (error.error.data && error.error.data.message) {
                detail = error.error.data.message;
            }
        } else if (typeof error === 'string') {
            message = error;
        } else if (error.message) {
            message = error.message;
        }

        // Special handling for common errors
        if (message.includes('missing a required argument')) {
            message = 'Invalid request parameters';
        } else if (message.includes('not supported between')) {
            message = 'Server data format error';
            detail = 'Please refresh the page';
        } else if (message.includes('Game not found')) {
            message = 'Game session expired';
            detail = 'Please create a new game';
        }

        this.show(message, detail);
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .error-notification:hover,
    .success-notification:hover {
        transform: scale(1.02);
        transition: transform 0.2s;
    }
`;
document.head.appendChild(style);

// Create global instance
window.errorNotification = new ErrorNotificationSystem();