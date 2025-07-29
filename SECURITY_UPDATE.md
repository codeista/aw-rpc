# Security Update - AW-RPC

## Overview

This update addresses security vulnerabilities and production deployment issues:

1. **Werkzeug Production Warning**: Fixed by adding proper WSGI server (Gunicorn)
2. **Dependency Vulnerabilities**: Updated all dependencies to latest secure versions
3. **Security Headers**: Added comprehensive security headers for production
4. **Configuration Management**: Environment-based configuration for security

## Changes Made

### 1. Updated Dependencies (requirements.txt)

```
Flask: 2.3.3 → 3.0.3
Flask-CORS: 4.0.0 → 5.0.0
Flask-SocketIO: 5.3.2 → 5.3.6
Flask-SQLAlchemy: 3.0.3 → 3.1.1
Werkzeug: 2.3.7 → 3.0.3
python-socketio: 5.9.0 → 5.11.3
psycopg2-binary: 2.9.5 → 2.9.9
psutil: 5.9.5 → 6.0.0

Added:
- gunicorn==22.0.0 (Production WSGI server)
- eventlet==0.35.2 (Async support for Socket.IO)
```

### 2. Production Server Configuration

**New files:**
- `gunicorn_config.py` - Gunicorn configuration with eventlet workers
- `start_production.sh` - Production startup script
- `config_production.py` - Production-specific Flask configuration
- `security_middleware.py` - Security headers and middleware

### 3. Security Enhancements

**Security Headers Added:**
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security (HSTS)
- Content-Security-Policy
- Referrer-Policy
- Permissions-Policy

**Session Security:**
- Secure cookies (HTTPS only)
- HttpOnly flag (prevents XSS)
- SameSite protection (CSRF)

### 4. App Configuration Updates

- Modified `app.py` to detect production mode and warn about development server
- Updated `app_core.py` to load production config and security middleware
- Added environment-based configuration support

## Deployment Instructions

### Development Mode (unchanged)

```bash
python app.py
```

### Production Mode

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export FLASK_ENV=production
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
```

3. Start with Gunicorn:
```bash
./start_production.sh
# or
gunicorn -c gunicorn_config.py 'app:app'
```

## Environment Variables

See `.env.example` for all available options:

- `FLASK_ENV`: Set to 'production' for production mode
- `SECRET_KEY`: Secret key for sessions (required in production)
- `DEBUG`: Must be False in production
- `PORT`: Server port (default: 5000)
- `WEB_CONCURRENCY`: Number of worker processes

## Testing the Changes

1. Run tests to ensure compatibility:
```bash
python run_regression_tests.py
```

2. Check security headers:
```bash
curl -I http://localhost:5000
```

3. Verify Socket.IO functionality with eventlet workers

## Migration Notes

- The development server (`python app.py`) still works for local development
- In production, always use Gunicorn or another WSGI server
- Update any deployment scripts to use `start_production.sh`
- Ensure HTTPS is configured at the reverse proxy level

## Security Best Practices

1. **Never run with DEBUG=True in production**
2. **Always use HTTPS in production** (configure at reverse proxy)
3. **Set a strong SECRET_KEY** from environment variables
4. **Restrict CORS origins** to specific domains
5. **Enable all security headers** via the middleware
6. **Use environment variables** for sensitive configuration
7. **Monitor logs** for security events

## Rollback Instructions

If issues occur, rollback by:

1. Checkout previous commit:
```bash
git checkout HEAD~1
```

2. Restore old requirements:
```bash
pip install -r requirements_backup.txt
```

## Future Improvements

- Add rate limiting with Flask-Limiter
- Implement CSRF protection for forms
- Add input validation middleware
- Set up security scanning in CI/CD
- Add dependency vulnerability scanning