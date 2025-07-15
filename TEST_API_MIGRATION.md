# Test API Migration Guide

## Overview

All test execution API endpoints have been consolidated into a single flexible endpoint: `/api/tests`

## Migration Map

| Old Endpoint | New Endpoint | Notes |
|--------------|--------------|-------|
| `/api/test_create_custom_game` | `/api/tests/create-game` | Create test games |
| `/api/test_connection` | `/api/tests/websocket` | Test WebSocket connectivity |
| `/api/test-status` | `/api/tests` with `action: 'status'` | Get test status |
| `/api/run-tests` | `/api/tests` with `action: 'run'` | Run all tests |
| `/api/run-test-category/<category>` | `/api/tests` with `action: 'run', category: 'unit'` | Run category |
| `/api/quick-test` | `/api/tests` with `action: 'run', category: 'quick'` | Quick tests |
| `/run_test` | `/api/tests` with `action: 'run', tests: ['specific.py']` | Run specific test |

## Unified API Usage

### Get Test Information
```http
GET /api/tests
```

Returns available test categories, total tests, and usage examples.

### Check Test Status
```http
POST /api/tests
Content-Type: application/json

{
    "action": "status"
}
```

### Run All Tests
```http
POST /api/tests
Content-Type: application/json

{
    "action": "run"
}
```

### Run Test Category
```http
POST /api/tests
Content-Type: application/json

{
    "action": "run",
    "category": "unit"
}
```

Available categories:
- `unit` - Unit tests
- `integration` - Integration tests  
- `system` - System tests
- `quick` - Quick smoke tests

### Run Specific Tests
```http
POST /api/tests
Content-Type: application/json

{
    "action": "run",
    "tests": ["test_combat_system.py", "test_movement_system.py"]
}
```

### Stop Running Tests
```http
POST /api/tests
Content-Type: application/json

{
    "action": "stop"
}
```

## Additional Endpoints

### List Test Categories
```http
GET /api/tests/categories
```

### Get Test History
```http
GET /api/tests/history
```

### Test WebSocket Connection
```http
GET /api/tests/websocket
```

### Create Test Game
```http
POST /api/tests/create-game
Content-Type: application/json

{
    "map": "test",
    "players": 2
}
```

## Response Format

### Status Response
```json
{
    "running": true,
    "current_test": "test_combat_system.py",
    "duration": 45.2,
    "results": [
        {
            "test": "test_movement_system.py",
            "status": "passed",
            "duration": 12.5,
            "test_count": 15,
            "passed_count": 15,
            "failed_count": 0
        }
    ]
}
```

### Run Response
```json
{
    "message": "Tests started",
    "tests": ["test_combat_system.py", "test_movement_system.py"],
    "parallel": false
}
```

## Benefits

1. **Single endpoint** - `/api/tests` handles all test operations
2. **Flexible** - Run all, by category, or specific tests
3. **Consistent** - Uniform request/response format
4. **Discoverable** - GET endpoint shows all options
5. **Extensible** - Easy to add new test categories

## JavaScript Example

```javascript
// Get test info
fetch('/api/tests')
    .then(r => r.json())
    .then(data => console.log(data));

// Run unit tests
fetch('/api/tests', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        action: 'run',
        category: 'unit'
    })
});

// Check status
fetch('/api/tests', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        action: 'status'
    })
});
```

## Implementation Status

- ✅ Unified API created at `/api/tests`
- ✅ All test categories configured
- ✅ Status tracking implemented
- ⏳ Old endpoints still active (for compatibility)
- 🔜 Update test interface to use new API
- 🔜 Add test result persistence
- 🔜 Implement parallel test execution