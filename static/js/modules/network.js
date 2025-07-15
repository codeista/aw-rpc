/**
 * Network Module - JSON-RPC and Socket.io communication
 * Extracted from render.js as part of modularization effort
 */

import { uuidv4, getGameToken } from './core.js';

// ===== NETWORK STATE =====
let socketInstance = null;
let rpcRequestQueue = [];
let isOnline = navigator.onLine;

// ===== JSON-RPC IMPLEMENTATION =====

/**
 * Make a JSON-RPC call to the server
 * @param {string} method - RPC method name
 * @param {Object} params - RPC parameters
 * @param {Function} callback - Optional callback (if not provided, returns Promise)
 * @returns {Promise|undefined} Promise if no callback provided
 */
export function jsonrpc(method, params, callback) {
    if (!params) params = {};
    
    // Add token to all requests
    const token = getGameToken();
    if (token) {
        params.token = token;
    }
    
    logger.debug('rpc::', method, params);
    
    // If no callback provided, return a Promise (for async/await)
    if (!callback) {
        return new Promise((resolve, reject) => {
            makeRpcRequest(method, params, resolve, reject);
        });
    }
    
    // Original callback-based behavior (for existing code)
    makeRpcRequest(method, params, (result) => {
        if (callback) callback(result);
    }, (error) => {
        logger.error('error calling "' + method + '"');
    });
}

/**
 * Internal function to make the actual RPC request
 * @param {string} method - RPC method name
 * @param {Object} params - RPC parameters
 * @param {Function} resolve - Success callback
 * @param {Function} reject - Error callback
 */
function makeRpcRequest(method, params, resolve, reject) {
    const xhr = new XMLHttpRequest();
    
    xhr.onreadystatechange = function() {
        if (this.readyState === XMLHttpRequest.DONE) {
            if (this.status === 200) {
                try {
                    const response = JSON.parse(this.responseText);
                    logger.debug('RPC Response:', method, response);
                    
                    if (response.error) {
                        logger.error('RPC Error:', method, response.error);
                        reject(new Error(response.error.message || 'RPC Error'));
                    } else {
                        resolve(response.result);
                    }
                } catch (e) {
                    logger.error('JSON Parse Error:', this.responseText);
                    reject(new Error('Invalid JSON response'));
                }
            } else {
                reject(new Error(`HTTP ${this.status}: ${this.statusText}`));
            }
        }
    };
    
    xhr.open('POST', '/api');
    xhr.setRequestHeader('Content-Type', 'application/json');
    
    const data = {
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': uuidv4()
    };
    
    xhr.send(JSON.stringify(data));
}

// ===== SOCKET.IO MANAGEMENT =====

/**
 * Initialize Socket.io connection
 * @param {string} token - Game token
 * @param {Object} callbacks - Event callbacks
 * @returns {Object} Socket instance
 */
export function initializeSocket(token, callbacks = {}) {
    if (socketInstance) {
        logger.warn('Socket already initialized');
        return socketInstance;
    }
    
    // Default callbacks
    const defaultCallbacks = {
        onConnect: () => logger.info('socket connected'),
        onDisconnect: () => logger.info('socket disconnected'),
        onUpdate: () => {
            if (window.update && typeof window.update === 'function') {
                window.update();
            }
        },
        onMessage: (msg) => {
            const textareachat = document.getElementById('textareachat');
            if (textareachat) {
                textareachat.value = textareachat.value + msg + '\n';
                textareachat.scrollTop = textareachat.scrollHeight;
            }
        }
    };
    
    // Merge callbacks
    const socketCallbacks = { ...defaultCallbacks, ...callbacks };
    
    // Create socket connection after a brief delay
    setTimeout(() => {
        socketInstance = io('/');
        
        socketInstance.on('connect', () => {
            socketCallbacks.onConnect();
            if (token) {
                socketInstance.emit('game', token);
            }
        });
        
        socketInstance.on('disconnect', socketCallbacks.onDisconnect);
        socketInstance.on('update', socketCallbacks.onUpdate);
        socketInstance.on('message', socketCallbacks.onMessage);
        
        // Handle connection errors
        socketInstance.on('connect_error', (error) => {
            logger.error('Socket connection error:', error);
        });
        
        // Handle reconnection
        socketInstance.on('reconnect', (attemptNumber) => {
            logger.info('Socket reconnected after', attemptNumber, 'attempts');
        });
        
    }, 100);
    
    return socketInstance;
}

/**
 * Get the current socket instance
 * @returns {Object|null} Socket instance or null
 */
export function getSocket() {
    return socketInstance;
}

/**
 * Emit a socket event
 * @param {string} event - Event name
 * @param {*} data - Event data
 */
export function emitSocketEvent(event, data) {
    if (socketInstance && socketInstance.connected) {
        socketInstance.emit(event, data);
    } else {
        logger.warn('Socket not connected, cannot emit event:', event);
    }
}

/**
 * Disconnect the socket
 */
export function disconnectSocket() {
    if (socketInstance) {
        socketInstance.disconnect();
        socketInstance = null;
    }
}

// ===== ERROR HANDLING =====

/**
 * Enhanced RPC call with error handling and retry logic
 * @param {string} method - RPC method name
 * @param {Object} params - RPC parameters
 * @param {Object} options - Additional options
 * @returns {Promise} Promise that resolves with the result
 */
export async function rpcWithRetry(method, params, options = {}) {
    const {
        retries = 3,
        retryDelay = 1000,
        timeout = 10000
    } = options;
    
    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            // Add timeout to the request
            const result = await Promise.race([
                jsonrpc(method, params),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Request timeout')), timeout)
                )
            ]);
            
            return result;
        } catch (error) {
            logger.error(`RPC attempt ${attempt + 1}/${retries + 1} failed:`, error.message);
            
            if (attempt === retries) {
                throw error;
            }
            
            // Wait before retrying
            await new Promise(resolve => setTimeout(resolve, retryDelay * (attempt + 1)));
        }
    }
}

/**
 * Batch multiple RPC calls
 * @param {Array} requests - Array of {method, params} objects
 * @returns {Promise} Promise that resolves with array of results
 */
export async function batchRpc(requests) {
    const promises = requests.map(req => jsonrpc(req.method, req.params));
    return Promise.allSettled(promises);
}

// ===== NETWORK STATUS MONITORING =====

/**
 * Check if the application is online
 * @returns {boolean} True if online
 */
export function isOnlineStatus() {
    return isOnline;
}

/**
 * Initialize network status monitoring
 */
export function initializeNetworkMonitoring() {
    window.addEventListener('online', () => {
        isOnline = true;
        logger.info('Network connection restored');
        
        // Attempt to reconnect socket if needed
        if (!socketInstance || !socketInstance.connected) {
            const token = getGameToken();
            if (token) {
                initializeSocket(token);
            }
        }
    });
    
    window.addEventListener('offline', () => {
        isOnline = false;
        logger.warn('Network connection lost');
    });
}

// ===== RPC QUEUE FOR OFFLINE SUPPORT =====

/**
 * Queue an RPC request for later execution
 * @param {string} method - RPC method name
 * @param {Object} params - RPC parameters
 */
export function queueRpcRequest(method, params) {
    rpcRequestQueue.push({ method, params, timestamp: Date.now() });
    logger.debug('Queued RPC request:', method);
}

/**
 * Process queued RPC requests
 * @returns {Promise} Promise that resolves when all queued requests are processed
 */
export async function processQueuedRequests() {
    if (!isOnline || rpcRequestQueue.length === 0) {
        return;
    }
    
    logger.info(`Processing ${rpcRequestQueue.length} queued RPC requests`);
    
    const requests = [...rpcRequestQueue];
    rpcRequestQueue = [];
    
    const results = await batchRpc(requests);
    
    // Log results
    results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
            logger.debug('Queued request processed:', requests[index].method);
        } else {
            logger.error('Queued request failed:', requests[index].method, result.reason);
        }
    });
    
    return results;
}

/**
 * Clear the RPC request queue
 */
export function clearRequestQueue() {
    const count = rpcRequestQueue.length;
    rpcRequestQueue = [];
    logger.info(`Cleared ${count} queued RPC requests`);
}

// Initialize network monitoring when module loads
initializeNetworkMonitoring();