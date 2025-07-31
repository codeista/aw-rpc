# API Response Analysis

## Current Response Formats

### Successful Unit Creation
```json
{
  "can_be_attacked": false,
  "can_be_moved_to": false,
  "capture_hp": 20,
  "mapTile": {
    "army": null,
    "type": "BEACH_W"
  },
  "unit": {
    "army": "RED",
    "can_attack": false,
    "can_capture": true,
    "can_move": false,
    "config": {...},
    "id": "bc553f80-ef85-4ef2-81a4-30db8e33b3cd",
    "status": {...},
    "type": "INFANTRY"
  },
  "x": 0,
  "y": 3
}
```

### Error Response
```json
{
  "error": true,
  "error_code": "INTERNAL_ERROR",
  "message": "Internal server error",
  "details": {}
}
```

## Issues with Current Format

1. **Inconsistent error handling** - Errors wrapped in "result" object
2. **No clear success indicator** - Must infer from presence of data
3. **Mixed concerns** - Tile info mixed with operation result
4. **Verbose for simple operations** - Lots of data for unit creation

## Suggested Improvements

### Option 1: Clear Success/Error Structure
```json
// Success
{
  "success": true,
  "data": {
    "unit": {...},
    "tile": {...},
    "position": {"x": 0, "y": 3}
  }
}

// Error
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "Not enough funds to create TANK (need 7000, have 5000)",
    "details": {
      "required": 7000,
      "available": 5000,
      "unit_type": "TANK"
    }
  }
}
```

### Option 2: Operation-Specific Responses
```json
// unit_create response
{
  "success": true,
  "unit_id": "abc123",
  "unit_type": "TANK",
  "position": {"x": 0, "y": 3},
  "cost": 7000,
  "remaining_funds": 43000
}

// unit_move response  
{
  "success": true,
  "from": {"x": 0, "y": 3},
  "to": {"x": 1, "y": 3},
  "fuel_used": 1,
  "fuel_remaining": 69
}
```

### Option 3: Keep Current But Add Metadata
```json
{
  "_meta": {
    "success": true,
    "operation": "unit_create",
    "cost": 7000
  },
  // ... existing tile data ...
}
```

## Recommendation

For now, the current format works but could benefit from:
1. Consistent error structure
2. Clear success indicators
3. Operation-specific metadata

The tests can work with current format - just need proper handling.