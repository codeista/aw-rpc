/**
 * Module Loader - Manages loading and initialization of modular render system
 * Replaces the monolithic render.js with a modular architecture
 */

class ModuleLoader {
    constructor() {
        this.modules = new Map();
        this.loadedModules = new Set();
        this.initializationOrder = [
            'core',
            'network', 
            'testing',
            // Phase 2 modules (to be added later)
            // 'gameState',
            // 'uiSystems',
            // Phase 3 modules 
            // 'inputHandler',
            // 'gameActions',
            // Phase 4 modules
            // 'renderEngine',
            // 'movementSystem',
            // 'combatSystem',
            // 'transportSystem',
            // Phase 5 modules
            // 'mobileSupport'
        ];
        this.loadStartTime = performance.now();
    }

    /**
     * Load a specific module
     * @param {string} moduleName - Name of the module to load
     * @returns {Promise} Promise that resolves when module is loaded
     */
    async loadModule(moduleName) {
        if (this.loadedModules.has(moduleName)) {
            return this.modules.get(moduleName);
        }

        logger.info(`📦 Loading module: ${moduleName}`);
        
        try {
            const module = await import(`./modules/${moduleName}.js`);
            this.modules.set(moduleName, module);
            this.loadedModules.add(moduleName);
            
            logger.info(`✅ Module loaded: ${moduleName}`);
            return module;
        } catch (error) {
            logger.error(`❌ Failed to load module ${moduleName}:`, error);
            throw error;
        }
    }

    /**
     * Load all modules in the correct order
     * @returns {Promise} Promise that resolves when all modules are loaded
     */
    async loadAllModules() {
        logger.info('🚀 Starting modular render system...');
        
        try {
            // Load modules in dependency order
            for (const moduleName of this.initializationOrder) {
                await this.loadModule(moduleName);
            }
            
            const loadTime = performance.now() - this.loadStartTime;
            logger.info(`✅ All modules loaded successfully in ${loadTime.toFixed(2)}ms`);
            
            // Initialize the application
            await this.initializeApplication();
            
        } catch (error) {
            logger.error('❌ Failed to load modules:', error);
            this.handleLoadError(error);
        }
    }

    /**
     * Initialize the application after all modules are loaded
     */
    async initializeApplication() {
        logger.info('🎮 Initializing application...');
        
        try {
            // Get core module
            const core = this.modules.get('core');
            const network = this.modules.get('network');
            
            // Initialize game state
            core.initializeGameState();
            
            // Initialize network with token
            const token = core.getGameToken();
            if (token) {
                network.initializeSocket(token);
                logger.info(`🔗 Socket initialized for game: ${token}`);
            }
            
            // Initialize global references for compatibility
            this.setupGlobalCompatibility();
            
            // Start the main update cycle (temporarily using original function)
            if (window.update && typeof window.update === 'function') {
                window.update();
            }
            
            // Initialize controls (temporarily using original functions)
            this.initializeControls();
            
            logger.info('✅ Application initialized successfully');
            
        } catch (error) {
            logger.error('❌ Application initialization failed:', error);
            throw error;
        }
    }

    /**
     * Set up global compatibility for existing code
     */
    setupGlobalCompatibility() {
        const core = this.modules.get('core');
        const network = this.modules.get('network');
        
        // Export core constants globally
        window.TILESIZE = core.TILESIZE;
        window.TRANSPORT_HIGHLIGHT_OPACITY = core.TRANSPORT_HIGHLIGHT_OPACITY;
        window.TRANSPORT_BORDER_WIDTH = core.TRANSPORT_BORDER_WIDTH;
        
        // Export utility functions globally
        window.uuidv4 = core.uuidv4;
        window.isTransportUnitForRender = core.isTransportUnitForRender;
        window.getCargoCountForRender = core.getCargoCountForRender;
        window.getSelectedTerrainTileset = core.getSelectedTerrainTileset;
        window.getSelectedUnitTileset = core.getSelectedUnitTileset;
        
        // Export network functions globally
        window.jsonrpc = network.jsonrpc;
        
        // Initialize globals
        const globals = core.initializeGlobals();
        window.token = globals.token;
        window.board = globals.board;
        window.two = globals.two;
        window.transportHighlightGroup = globals.transportHighlightGroup;
        
        logger.debug('🔗 Global compatibility layer established');
    }

    /**
     * Initialize controls (temporary - will be moved to inputHandler module)
     */
    initializeControls() {
        // Button handlers
        const buttonrerender = document.getElementsByClassName('buttonrerender')[0];
        if (buttonrerender && window.debounce && window.rerender) {
            buttonrerender.onclick = window.debounce(window.rerender, 300);
        }

        const inputshowmap = document.getElementById('inputshowmap');
        if (inputshowmap && window.rerender) {
            inputshowmap.onchange = window.rerender;
        }

        const buttonendturn = document.getElementsByClassName('buttonendturn')[0];
        if (buttonendturn && window.debounce && window.armyEndTurn) {
            buttonendturn.onclick = window.debounce(window.armyEndTurn, 500);
        }

        const buttonendgame = document.getElementsByClassName('buttonendgame')[0];
        if (buttonendgame && window.endGame) {
            buttonendgame.onclick = window.endGame;
        }

        const buttonchat = document.getElementById('buttonchat');
        if (buttonchat && window.chat) {
            buttonchat.onclick = window.chat;
        }

        const inputchat = document.getElementById('inputchat');
        if (inputchat && window.chat) {
            inputchat.onkeypress = window.chat;
        }

        const inputshowchat = document.getElementById('inputshowchat');
        if (inputshowchat && window.showChat) {
            inputshowchat.onchange = window.showChat;
        }

        const inputshowjson = document.getElementById('inputshowjson');
        if (inputshowjson && window.showJson) {
            inputshowjson.onchange = window.showJson;
        }

        logger.debug('🎛️ Controls initialized');
    }

    /**
     * Handle load errors gracefully
     */
    handleLoadError(error) {
        logger.error('🚨 Critical loading error - falling back to legacy render.js');
        
        // Show user-friendly error message
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #e74c3c;
            color: white;
            padding: 15px 25px;
            border-radius: 5px;
            z-index: 10000;
            font-family: Arial, sans-serif;
        `;
        errorDiv.innerHTML = `
            ⚠️ Modular loading failed. Using legacy mode.<br>
            <small>Check console for details.</small>
        `;
        document.body.appendChild(errorDiv);
        
        // Remove error message after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
        
        // Try to load legacy render.js if modular loading fails
        this.loadLegacyFallback();
    }

    /**
     * Load legacy render.js as fallback
     */
    loadLegacyFallback() {
        logger.warn('🔄 Attempting to load legacy render.js...');
        
        const script = document.createElement('script');
        script.src = '/static/js/render_legacy.js'; // We'll create this as backup
        script.onerror = () => {
            logger.error('❌ Legacy fallback also failed');
        };
        script.onload = () => {
            logger.info('✅ Legacy render.js loaded successfully');
        };
        
        document.head.appendChild(script);
    }

    /**
     * Get loaded module
     * @param {string} moduleName - Name of the module
     * @returns {Object|null} Module or null if not loaded
     */
    getModule(moduleName) {
        return this.modules.get(moduleName) || null;
    }

    /**
     * Check if module is loaded
     * @param {string} moduleName - Name of the module
     * @returns {boolean} True if module is loaded
     */
    isModuleLoaded(moduleName) {
        return this.loadedModules.has(moduleName);
    }

    /**
     * Get loading statistics
     * @returns {Object} Loading statistics
     */
    getLoadingStats() {
        return {
            totalModules: this.initializationOrder.length,
            loadedModules: this.loadedModules.size,
            loadTime: performance.now() - this.loadStartTime,
            modules: Array.from(this.loadedModules)
        };
    }
}

// Create global module loader instance
window.moduleLoader = new ModuleLoader();

// Export for use in other modules
export default window.moduleLoader;