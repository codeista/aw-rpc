#!/bin/bash
# Start the AW-RPC server properly with logging

# Activate virtual environment
source flask-env/bin/activate

# Start server in background
# Output will go to logs/awrpc_app.log instead of server.log
nohup python3 app.py > /dev/null 2>&1 &

echo "Server started. Check logs/awrpc_app.log for output"