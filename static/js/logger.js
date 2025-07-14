/**
 * Logger class for AW-RPC game
 * Provides configurable logging with different levels and buffering
 */
class Logger {
    constructor(level = 'INFO', maxBufferSize = 1000) {
        this.levels = {
            DEBUG: 0,
            INFO: 1,
            WARN: 2,
            ERROR: 3,
            NONE: 4
        };
        
        // Get log level from localStorage or default
        const savedLevel = localStorage.getItem('awrpc_log_level');
        this.currentLevel = this.levels[savedLevel || level];
        
        this.buffer = [];
        this.maxBufferSize = maxBufferSize;
        
        // Check if we're in debug mode
        this.debugMode = window.location.hostname === 'localhost' || 
                        window.location.search.includes('debug=true');
    }
    
    setLevel(level) {
        if (this.levels[level] !== undefined) {
            this.currentLevel = this.levels[level];
            localStorage.setItem('awrpc_log_level', level);
        }
    }
    
    log(level, ...args) {
        const levelValue = this.levels[level];
        if (levelValue === undefined || levelValue < this.currentLevel) {
            return;
        }
        
        const entry = {
            level,
            timestamp: Date.now(),
            message: args.map(arg => {
                if (typeof arg === 'object') {
                    try {
                        return JSON.stringify(arg);
                    } catch (e) {
                        return String(arg);
                    }
                }
                return String(arg);
            }).join(' ')
        };
        
        // Add to buffer
        this.buffer.push(entry);
        if (this.buffer.length > this.maxBufferSize) {
            this.buffer.shift();
        }
        
        // Console output in debug mode
        if (this.debugMode || levelValue >= this.levels.WARN) {
            const prefix = `[${level}] ${new Date(entry.timestamp).toISOString().substr(11, 8)}`;
            switch (level) {
                case 'ERROR':
                    console.error(prefix, ...args);
                    break;
                case 'WARN':
                    console.warn(prefix, ...args);
                    break;
                case 'INFO':
                    console.info(prefix, ...args);
                    break;
                default:
                    console.log(prefix, ...args);
            }
        }
    }
    
    debug(...args) {
        this.log('DEBUG', ...args);
    }
    
    info(...args) {
        this.log('INFO', ...args);
    }
    
    warn(...args) {
        this.log('WARN', ...args);
    }
    
    error(...args) {
        this.log('ERROR', ...args);
    }
    
    // Get recent logs for debugging
    getBuffer(level = null, limit = 100) {
        let logs = this.buffer;
        if (level && this.levels[level] !== undefined) {
            logs = logs.filter(entry => this.levels[entry.level] >= this.levels[level]);
        }
        return logs.slice(-limit);
    }
    
    // Clear the buffer
    clearBuffer() {
        this.buffer = [];
    }
    
    // Export logs as text
    exportLogs(level = null) {
        const logs = this.getBuffer(level);
        return logs.map(entry => {
            const time = new Date(entry.timestamp).toISOString();
            return `${time} [${entry.level}] ${entry.message}`;
        }).join('\n');
    }
}

// Create global logger instance
window.logger = new Logger(window.LOG_LEVEL || 'INFO');

// Add console command for easy access
window.setLogLevel = (level) => window.logger.setLevel(level);
window.getLogs = (level, limit) => window.logger.getBuffer(level, limit);
window.exportLogs = (level) => {
    const logs = window.logger.exportLogs(level);
    console.log(logs);
    return logs;
};