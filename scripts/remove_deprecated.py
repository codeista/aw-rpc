#!/usr/bin/env python3
"""
Remove deprecated methods from app.py
"""
import re

# List of deprecated methods to remove
DEPRECATED_METHODS = [
    'unit_move',
    'unit_move_enhanced', 
    'unit_load',
    'unit_unload',
    'load_unit',
    'unload_unit',
    'damage_estimate',
    'damage_preview', 
    'movement_preview',
    'unit_valid_moves',
    'validate_movement',
    'get_attack_targets',
    'combat_preview_old',
    'unit_attack',
    'unit_attack_enhanced',
    'get_movement_costs',
    'get_movement_highlights'
]

def remove_method_block(lines, method_name):
    """Remove a specific method block from lines."""
    i = 0
    removed_count = 0
    
    while i < len(lines):
        # Look for the method decorator
        if f"@jsonrpc.method('{method_name}')" in lines[i]:
            start = i
            
            # Find the function definition
            while i < len(lines) and not lines[i].strip().startswith('def '):
                i += 1
            
            if i < len(lines):
                # Get indentation level
                func_line = lines[i]
                indent = len(func_line) - len(func_line.lstrip())
                i += 1
                
                # Find end of function
                while i < len(lines):
                    if lines[i].strip() == '':
                        i += 1
                        continue
                    
                    line_indent = len(lines[i]) - len(lines[i].lstrip())
                    # If we hit a line with same or less indentation, we're done
                    if line_indent <= indent and lines[i].strip():
                        # Check if it's a decorator or function at same level
                        if lines[i].strip().startswith('@') or lines[i].strip().startswith('def '):
                            break
                    i += 1
                
                # Remove the lines
                del lines[start:i]
                removed_count = i - start
                i = start
        else:
            i += 1
    
    return removed_count

def main():
    # Read the file
    with open('app.py', 'r') as f:
        lines = f.readlines()
    
    original_count = len(lines)
    total_removed = 0
    
    # Remove each deprecated method
    for method in DEPRECATED_METHODS:
        removed = remove_method_block(lines, method)
        if removed > 0:
            print(f"Removed {method}: {removed} lines")
            total_removed += removed
    
    # Also remove the game_create deprecation comment
    i = 0
    while i < len(lines):
        if "DEPRECATED: Creates a new game" in lines[i]:
            # Just update the docstring
            lines[i] = lines[i].replace(
                "DEPRECATED: Creates a new game - redirects to game_create_v2",
                "Creates a new game with default 2-player configuration"
            )
            print("Updated game_create docstring")
            break
        i += 1
    
    # Write the cleaned file
    with open('app.py', 'w') as f:
        f.writelines(lines)
    
    print(f"\nTotal lines removed: {total_removed}")
    print(f"File reduced from {original_count} to {len(lines)} lines")
    print("\nDeprecated methods have been removed from app.py")

if __name__ == '__main__':
    main()