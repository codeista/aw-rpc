#!/bin/bash

# Production startup script for AW-RPC

# Set production environment
export FLASK_ENV=production
export PRODUCTION=1

# Disable debug mode
export DEBUG=False

# Set secret key (should be from environment or secrets management)
export SECRET_KEY=${SECRET_KEY:-$(python -c 'import secrets; print(secrets.token_hex(32))')}

# Set port (default 5000)
export PORT=${PORT:-5000}

# Set number of workers (default: CPU cores * 2 + 1)
export WEB_CONCURRENCY=${WEB_CONCURRENCY:-$(($(nproc) * 2 + 1))}

# Log startup
echo "Starting AW-RPC in production mode..."
echo "Port: $PORT"
echo "Workers: $WEB_CONCURRENCY"

# Start gunicorn with configuration
exec gunicorn -c gunicorn_config.py 'app:app'