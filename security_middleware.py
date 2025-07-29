"""Security middleware for production deployment"""

from flask import Flask, request, g
import os
import logging

logger = logging.getLogger(__name__)

def init_security(app: Flask):
    """Initialize security middleware and headers"""
    
    # Add security headers to all responses
    @app.after_request
    def add_security_headers(response):
        """Add security headers to every response"""
        
        # Only in production
        if not app.debug:
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Only add HSTS if using HTTPS
            if request.is_secure:
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            # Content Security Policy
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "font-src 'self'; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none';"
            )
            response.headers['Content-Security-Policy'] = csp
            
            # Referrer Policy
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Permissions Policy (replaces Feature-Policy)
            response.headers['Permissions-Policy'] = (
                "accelerometer=(), camera=(), geolocation=(), "
                "gyroscope=(), magnetometer=(), microphone=(), "
                "payment=(), usb=()"
            )
        
        return response
    
    # Request logging for security monitoring
    @app.before_request
    def log_request_info():
        """Log request information for security monitoring"""
        if not app.debug:
            logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")
            
            # Store request start time for performance monitoring
            g.request_start_time = os.times().elapsed
    
    # Log response time
    @app.after_request
    def log_response_info(response):
        """Log response information and timing"""
        if not app.debug and hasattr(g, 'request_start_time'):
            elapsed = os.times().elapsed - g.request_start_time
            logger.info(f"Response: {response.status_code} in {elapsed:.3f}s")
        
        return response
    
    # Error handling
    @app.errorhandler(400)
    def bad_request(error):
        """Handle bad requests securely"""
        logger.warning(f"Bad request: {error}")
        return {'error': 'Bad request'}, 400
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle forbidden requests"""
        logger.warning(f"Forbidden: {error} from {request.remote_addr}")
        return {'error': 'Forbidden'}, 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle internal errors without exposing details"""
        logger.error(f"Internal error: {error}")
        return {'error': 'Internal server error'}, 500
    
    logger.info("Security middleware initialized")