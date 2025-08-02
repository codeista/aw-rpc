#!/usr/bin/env python3
"""
Script to remove deprecated methods from app.py
"""
import re

def find_deprecated_methods(filename):
    """Find all deprecated method blocks in the file."""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    deprecated_blocks = []
    i = 0
    
    while i < len(lines):
        # Look for @jsonrpc.method decorator
        if lines[i].strip().startswith('@jsonrpc.method('):
            start = i
            method_name = re.search(r"@jsonrpc\.method\('([^']+)'\)", lines[i])
            if method_name:
                method = method_name.group(1)
                
                # Check if the next few lines contain DEPRECATED
                for j in range(i+1, min(i+5, len(lines))):
                    if 'DEPRECATED' in lines[j]:
                        # Find the end of this method
                        end = i + 1
                        indent_level = None
                        
                        # Skip to the def line
                        while end < len(lines) and not lines[end].strip().startswith('def '):
                            end += 1
                        
                        # Get the indentation of the def
                        if end < len(lines):
                            indent_level = len(lines[end]) - len(lines[end].lstrip())
                            end += 1
                            
                            # Find the end of the method
                            while end < len(lines):
                                if lines[end].strip() == '':
                                    end += 1
                                    continue
                                current_indent = len(lines[end]) - len(lines[end].lstrip())
                                if current_indent <= indent_level and lines[end].strip():
                                    break
                                end += 1
                        
                        deprecated_blocks.append({
                            'method': method,
                            'start': start,
                            'end': end,
                            'lines': lines[start:end]
                        })
                        break
            i = end if 'end' in locals() else i + 1
        else:
            i += 1
    
    return deprecated_blocks

def remove_deprecated_methods(input_file, output_file):
    """Remove deprecated methods and write to new file."""
    deprecated = find_deprecated_methods(input_file)
    
    print(f"Found {len(deprecated)} deprecated methods:")
    for block in deprecated:
        print(f"  - {block['method']} (lines {block['start']+1}-{block['end']}))")
    
    # Read all lines
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    # Mark lines to remove
    lines_to_remove = set()
    for block in deprecated:
        for i in range(block['start'], block['end']):
            lines_to_remove.add(i)
    
    # Write non-deprecated lines
    with open(output_file, 'w') as f:
        for i, line in enumerate(lines):
            if i not in lines_to_remove:
                f.write(line)
    
    print(f"\nWrote cleaned file to {output_file}")
    print(f"Removed {len(lines_to_remove)} lines")

if __name__ == '__main__':
    remove_deprecated_methods('app.py', 'app_clean.py')