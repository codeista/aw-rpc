# RPC Fix Summary

## Issue Identified
Movement highlights weren't appearing when clicking on units through the normal JavaScript flow due to an RPC method name mismatch.

## Root Cause
The JavaScript code in `render_legacy.js` was calling `get_unit_valid_moves` which doesn't exist as an RPC method. The actual method name is `unit_valid_moves`.

## Fix Applied
Changed the RPC call in `render_legacy.js` from:
```javascript
jsonrpc('get_unit_valid_moves', {x: unitX, y: unitY})
```

To:
```javascript
jsonrpc('get_movement_highlights', {x: unitX, y: unitY})
```

This uses the `get_movement_highlights` RPC method which:
1. Exists in the backend (app.py:4646)
2. Returns the expected format with `success` and `moves` fields
3. Properly validates unit ownership and turn order

## Test Results
After the fix:
- Movement highlights now appear through normal click flow
- No more 400 "Method not found" errors
- 6 out of 12 highlighting tests are passing (50%)
- Manual RPC workaround is no longer needed

## Remaining Issues
1. Some tests still fail due to highlights not being detected (empty array)
2. Stale element reference errors when using `ensure_turn` 
3. Visual highlight detection only finds 1 tile instead of actual count (rendering issue)

## Validation Endpoint
The user mentioned a `validate_movement` endpoint exists at `/api/browse/#/validate_movement` which could be useful for validating movement before executing it.