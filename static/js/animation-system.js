/**
 * Animation System for AW-RPC
 * Provides visual feedback animations for game actions
 * 
 * Features:
 * - Movement animations (unit sliding)
 * - Attack animations (explosions, projectiles)
 * - Capture animations (flag raising)
 * - UI feedback animations (selection pulse, hover effects)
 * - Damage number popups
 * - Turn transition effects
 */

class AnimationSystem {
    constructor() {
        this.animations = new Map();
        this.animationId = 0;
        this.enabled = true;
        this.frameCallbacks = [];
        this.isRunning = false;
        
        // Animation settings
        this.settings = {
            movementSpeed: 300, // ms per tile
            attackDuration: 600, // ms
            captureDuration: 400, // ms
            damageDuration: 1000, // ms
            pulseSpeed: 1000, // ms
            fadeSpeed: 300, // ms
            explosionFrames: 8,
            projectileSpeed: 500 // pixels per second
        };
        
        // Preload animation assets
        this.assets = {
            explosion: null,
            projectile: null,
            capture: null
        };
        
        this.initialize();
    }
    
    /**
     * Initialize the animation system
     */
    initialize() {
        // Start animation loop
        this.startAnimationLoop();
        
        logger.info('Animation system initialized');
    }
    
    /**
     * Start the animation loop
     */
    startAnimationLoop() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.lastTime = performance.now();
        
        const animate = (currentTime) => {
            if (!this.isRunning) return;
            
            const deltaTime = currentTime - this.lastTime;
            this.lastTime = currentTime;
            
            // Update all active animations
            this.updateAnimations(deltaTime);
            
            // Execute frame callbacks
            this.frameCallbacks.forEach(callback => callback(deltaTime));
            
            requestAnimationFrame(animate);
        };
        
        requestAnimationFrame(animate);
    }
    
    /**
     * Update all active animations
     * @param {number} deltaTime - Time since last frame in ms
     */
    updateAnimations(deltaTime) {
        for (const [id, animation] of this.animations) {
            animation.elapsed += deltaTime;
            
            // Calculate progress (0 to 1)
            const progress = Math.min(animation.elapsed / animation.duration, 1);
            
            // Apply easing
            const easedProgress = this.applyEasing(progress, animation.easing);
            
            // Update animation
            animation.update(easedProgress, deltaTime);
            
            // Remove completed animations
            if (progress >= 1) {
                if (animation.onComplete) {
                    animation.onComplete();
                }
                this.animations.delete(id);
            }
        }
    }
    
    /**
     * Apply easing function to progress
     * @param {number} t - Progress (0 to 1)
     * @param {string} easing - Easing type
     * @returns {number} Eased progress
     */
    applyEasing(t, easing = 'linear') {
        switch (easing) {
            case 'linear':
                return t;
            case 'easeIn':
                return t * t;
            case 'easeOut':
                return t * (2 - t);
            case 'easeInOut':
                return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
            case 'bounce':
                if (t < 0.5) {
                    return 8 * t * t * t * t;
                } else {
                    const f = (t - 1);
                    return 1 + 8 * f * f * f * f;
                }
            default:
                return t;
        }
    }
    
    /**
     * Create a movement animation
     * @param {Object} unit - Unit sprite/element
     * @param {number} fromX - Starting X position
     * @param {number} fromY - Starting Y position
     * @param {number} toX - Target X position
     * @param {number} toY - Target Y position
     * @param {Function} onComplete - Callback when complete
     * @returns {number} Animation ID
     */
    animateMovement(unit, fromX, fromY, toX, toY, onComplete) {
        if (!this.enabled || !unit) return -1;
        
        const distance = Math.sqrt(Math.pow(toX - fromX, 2) + Math.pow(toY - fromY, 2));
        const duration = distance * this.settings.movementSpeed;
        
        const id = this.animationId++;
        const animation = {
            type: 'movement',
            element: unit,
            fromX,
            fromY,
            toX,
            toY,
            duration,
            elapsed: 0,
            easing: 'easeInOut',
            onComplete,
            update: (progress) => {
                const x = fromX + (toX - fromX) * progress;
                const y = fromY + (toY - fromY) * progress;
                
                if (unit.position) {
                    unit.position.x = x;
                    unit.position.y = y;
                } else if (unit.translation) {
                    unit.translation.x = x;
                    unit.translation.y = y;
                }
                
                // Update Two.js if available
                if (window.two) {
                    window.two.update();
                }
            }
        };
        
        this.animations.set(id, animation);
        logger.debug(`Started movement animation ${id}`);
        return id;
    }
    
    /**
     * Create an attack animation
     * @param {number} fromX - Attacker X position
     * @param {number} fromY - Attacker Y position
     * @param {number} toX - Target X position
     * @param {number} toY - Target Y position
     * @param {string} type - Attack type (direct, indirect, etc)
     * @param {Function} onComplete - Callback when complete
     * @returns {number} Animation ID
     */
    animateAttack(fromX, fromY, toX, toY, type = 'direct', onComplete) {
        if (!this.enabled) return -1;
        
        const id = this.animationId++;
        
        if (type === 'indirect') {
            // Create projectile animation
            this.createProjectileAnimation(id, fromX, fromY, toX, toY, () => {
                // Follow with explosion
                this.createExplosionAnimation(toX, toY, onComplete);
            });
        } else {
            // Direct attack - just explosion at target
            this.createExplosionAnimation(toX, toY, onComplete);
        }
        
        logger.debug(`Started attack animation ${id}`);
        return id;
    }
    
    /**
     * Create a projectile animation
     * @param {number} id - Animation ID
     * @param {number} fromX - Start X
     * @param {number} fromY - Start Y
     * @param {number} toX - End X
     * @param {number} toY - End Y
     * @param {Function} onComplete - Callback
     */
    createProjectileAnimation(id, fromX, fromY, toX, toY, onComplete) {
        if (!window.two) return;
        
        // Create projectile sprite
        const projectile = window.two.makeCircle(fromX, fromY, 4);
        projectile.fill = '#ffff00';
        projectile.stroke = '#ff0000';
        projectile.linewidth = 2;
        
        const distance = Math.sqrt(Math.pow(toX - fromX, 2) + Math.pow(toY - fromY, 2));
        const duration = (distance / this.settings.projectileSpeed) * 1000;
        
        const animation = {
            type: 'projectile',
            element: projectile,
            fromX,
            fromY,
            toX,
            toY,
            duration,
            elapsed: 0,
            easing: 'linear',
            onComplete: () => {
                projectile.remove();
                if (onComplete) onComplete();
            },
            update: (progress) => {
                projectile.translation.x = fromX + (toX - fromX) * progress;
                projectile.translation.y = fromY + (toY - fromY) * progress;
                
                // Add trail effect
                projectile.opacity = 1 - (progress * 0.3);
                projectile.scale = 1 - (progress * 0.2);
            }
        };
        
        this.animations.set(id, animation);
    }
    
    /**
     * Create an explosion animation
     * @param {number} x - X position
     * @param {number} y - Y position
     * @param {Function} onComplete - Callback
     */
    createExplosionAnimation(x, y, onComplete) {
        if (!window.two) return;
        
        // Create explosion effect with multiple circles
        const explosionGroup = window.two.makeGroup();
        const circles = [];
        
        for (let i = 0; i < 3; i++) {
            const circle = window.two.makeCircle(x, y, 8 + i * 4);
            circle.fill = i === 0 ? '#ffffff' : (i === 1 ? '#ffff00' : '#ff0000');
            circle.opacity = 0.8 - i * 0.2;
            circle.noStroke();
            explosionGroup.add(circle);
            circles.push(circle);
        }
        
        const id = this.animationId++;
        const animation = {
            type: 'explosion',
            element: explosionGroup,
            duration: this.settings.attackDuration,
            elapsed: 0,
            easing: 'easeOut',
            onComplete: () => {
                explosionGroup.remove();
                if (onComplete) onComplete();
            },
            update: (progress) => {
                circles.forEach((circle, i) => {
                    circle.scale = 0.5 + progress * (2 + i);
                    circle.opacity = (0.8 - i * 0.2) * (1 - progress);
                });
            }
        };
        
        this.animations.set(id, animation);
    }
    
    /**
     * Animate capture progress
     * @param {Object} tile - Tile being captured
     * @param {number} progress - Capture progress (0-100)
     * @returns {number} Animation ID
     */
    animateCapture(tile, progress) {
        if (!this.enabled || !window.two) return -1;
        
        const TILESIZE = window.TILESIZE || 16;
        const x = tile.x * TILESIZE + TILESIZE / 2;
        const y = tile.y * TILESIZE + TILESIZE / 2;
        
        // Create or update capture indicator
        let indicator = tile._captureIndicator;
        if (!indicator) {
            indicator = window.two.makeRectangle(x, y - 8, 20, 4);
            indicator.fill = '#00ff00';
            indicator.stroke = '#000000';
            indicator.linewidth = 1;
            tile._captureIndicator = indicator;
        }
        
        // Update progress bar
        const fillWidth = (progress / 100) * 20;
        indicator.width = fillWidth;
        
        // Pulse effect
        const id = this.animationId++;
        const animation = {
            type: 'capture',
            element: indicator,
            duration: this.settings.captureDuration,
            elapsed: 0,
            easing: 'easeInOut',
            onComplete: () => {
                if (progress >= 100) {
                    // Flash on complete capture
                    this.flashElement(indicator, '#ffffff', 2);
                }
            },
            update: (animProgress) => {
                indicator.scale = 1 + Math.sin(animProgress * Math.PI) * 0.2;
            }
        };
        
        this.animations.set(id, animation);
        return id;
    }
    
    /**
     * Show damage numbers
     * @param {number} x - X position
     * @param {number} y - Y position
     * @param {number} damage - Damage amount
     * @param {string} color - Text color
     */
    showDamageNumber(x, y, damage, color = '#ff0000') {
        if (!this.enabled || !window.two) return;
        
        // Create damage text
        const text = window.two.makeText(damage.toString(), x, y);
        text.size = 20;
        text.weight = 700;
        text.fill = color;
        text.stroke = '#000000';
        text.linewidth = 3;
        text.opacity = 1;
        
        const id = this.animationId++;
        const animation = {
            type: 'damage',
            element: text,
            duration: this.settings.damageDuration,
            elapsed: 0,
            startY: y,
            easing: 'easeOut',
            onComplete: () => {
                text.remove();
            },
            update: (progress) => {
                // Float upward and fade
                text.translation.y = y - (progress * 30);
                text.opacity = 1 - (progress * 0.8);
                text.scale = 1 + (progress * 0.3);
            }
        };
        
        this.animations.set(id, animation);
    }
    
    /**
     * Pulse animation for selected units
     * @param {Object} element - Element to pulse
     * @param {Function} onCancel - Called when animation is cancelled
     * @returns {number} Animation ID
     */
    pulseElement(element, onCancel) {
        if (!this.enabled || !element) return -1;
        
        const id = this.animationId++;
        let pulseCount = 0;
        
        const animation = {
            type: 'pulse',
            element,
            duration: Infinity, // Continuous
            elapsed: 0,
            originalScale: element.scale || 1,
            onCancel,
            update: (progress, deltaTime) => {
                // Use elapsed time for continuous animation
                const cycleProgress = (animation.elapsed % this.settings.pulseSpeed) / this.settings.pulseSpeed;
                const scale = animation.originalScale + Math.sin(cycleProgress * Math.PI * 2) * 0.1;
                
                if (element.scale !== undefined) {
                    element.scale = scale;
                }
            }
        };
        
        this.animations.set(id, animation);
        return id;
    }
    
    /**
     * Flash an element with a color
     * @param {Object} element - Element to flash
     * @param {string} color - Flash color
     * @param {number} times - Number of flashes
     */
    flashElement(element, color = '#ffffff', times = 1) {
        if (!this.enabled || !element) return;
        
        const originalFill = element.fill;
        let flashCount = 0;
        
        const id = this.animationId++;
        const animation = {
            type: 'flash',
            element,
            duration: this.settings.fadeSpeed * times * 2,
            elapsed: 0,
            easing: 'linear',
            onComplete: () => {
                element.fill = originalFill;
            },
            update: (progress) => {
                const cycle = Math.floor(progress * times * 2);
                element.fill = (cycle % 2 === 0) ? color : originalFill;
            }
        };
        
        this.animations.set(id, animation);
    }
    
    /**
     * Animate turn transition
     * @param {string} armyName - Name of army whose turn it is
     * @param {Function} onComplete - Callback when complete
     */
    animateTurnTransition(armyName, onComplete) {
        if (!this.enabled || !window.two) return;
        
        const width = window.two.width;
        const height = window.two.height;
        
        // Create overlay
        const overlay = window.two.makeRectangle(width/2, height/2, width, height);
        overlay.fill = 'rgba(0, 0, 0, 0.7)';
        overlay.opacity = 0;
        
        // Create text
        const text = window.two.makeText(`${armyName.toUpperCase()} TURN`, width/2, height/2);
        text.size = 48;
        text.weight = 700;
        text.fill = armyName === 'RED' ? '#ff0000' : '#0000ff';
        text.stroke = '#ffffff';
        text.linewidth = 4;
        text.opacity = 0;
        text.scale = 0.5;
        
        const group = window.two.makeGroup(overlay, text);
        
        const id = this.animationId++;
        const animation = {
            type: 'turnTransition',
            element: group,
            duration: 1500,
            elapsed: 0,
            easing: 'easeInOut',
            onComplete: () => {
                group.remove();
                if (onComplete) onComplete();
            },
            update: (progress) => {
                if (progress < 0.3) {
                    // Fade in
                    const fadeProgress = progress / 0.3;
                    overlay.opacity = fadeProgress * 0.7;
                    text.opacity = fadeProgress;
                    text.scale = 0.5 + fadeProgress * 0.5;
                } else if (progress > 0.7) {
                    // Fade out
                    const fadeProgress = (progress - 0.7) / 0.3;
                    overlay.opacity = 0.7 * (1 - fadeProgress);
                    text.opacity = 1 - fadeProgress;
                    text.scale = 1 + fadeProgress * 0.2;
                } else {
                    // Hold
                    overlay.opacity = 0.7;
                    text.opacity = 1;
                    text.scale = 1;
                }
            }
        };
        
        this.animations.set(id, animation);
    }
    
    /**
     * Cancel an animation
     * @param {number} id - Animation ID
     */
    cancelAnimation(id) {
        const animation = this.animations.get(id);
        if (animation) {
            if (animation.onCancel) {
                animation.onCancel();
            }
            this.animations.delete(id);
        }
    }
    
    /**
     * Cancel all animations of a specific type
     * @param {string} type - Animation type
     */
    cancelAnimationsByType(type) {
        for (const [id, animation] of this.animations) {
            if (animation.type === type) {
                this.cancelAnimation(id);
            }
        }
    }
    
    /**
     * Enable/disable animations
     * @param {boolean} enabled - Whether animations are enabled
     */
    setEnabled(enabled) {
        this.enabled = enabled;
        if (!enabled) {
            // Cancel all active animations
            for (const id of this.animations.keys()) {
                this.cancelAnimation(id);
            }
        }
        logger.info(`Animations ${enabled ? 'enabled' : 'disabled'}`);
    }
    
    /**
     * Register a callback to run each frame
     * @param {Function} callback - Function to call each frame
     */
    onFrame(callback) {
        this.frameCallbacks.push(callback);
    }
    
    /**
     * Stop the animation loop
     */
    stop() {
        this.isRunning = false;
    }
}

// Create and export global animation system
window.animationSystem = new AnimationSystem();

// Export for module usage - commented out since this is loaded as script, not module
// export default window.animationSystem;