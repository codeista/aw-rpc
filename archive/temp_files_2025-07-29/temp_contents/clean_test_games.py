#!/usr/bin/env python3
"""Clean up test games from database"""

import requests
import random
import string

def generate_token():
    """Generate random token"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# Test with unique tokens
test_tokens = [generate_token() for _ in range(5)]
print(f"Generated test tokens: {test_tokens}")

# Try creating games with unique tokens
for token in test_tokens:
    response = requests.post("http://localhost:5000/api", json={
        "jsonrpc": "2.0",
        "method": "game_create_v2",
        "params": {"token": token},
        "id": 1
    })
    result = response.json()
    if "error" not in result:
        print(f"✅ Created game: {token}")
    else:
        print(f"❌ Failed: {result.get('error')}")