#!/usr/bin/env python3
"""
Script to replace console.log statements with logger calls in render.js
"""
import re
import sys

def categorize_log(line, content):
    """Categorize log statement based on content"""
    content_lower = content.lower()
    
    # ERROR level patterns
    if any(word in content_lower for word in ['error', 'failed', 'exception', 'critical']):
        return 'error'
    
    # WARN level patterns
    if any(word in content_lower for word in ['warning', 'warn', 'deprecated', 'invalid']):
        return 'warn'
    
    # INFO level patterns (important game events)
    if any(word in content_lower for word in ['turn ended', 'unit created', 'game loaded', 
                                               'connected', 'disconnected', 'update', 
                                               'attack', 'move', 'capture']):
        return 'info'
    
    # DEBUG level (everything else)
    return 'debug'

def replace_console_logs(file_path):
    """Replace console.log statements with appropriate logger calls"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Track replacements
    replacements = {
        'debug': 0,
        'info': 0,
        'warn': 0,
        'error': 0
    }
    
    # Pattern to match console.log, console.error, console.warn
    patterns = [
        (r'console\.log\((.*?)\);', 'log'),
        (r'console\.error\((.*?)\);', 'error'),
        (r'console\.warn\((.*?)\);', 'warn'),
        (r'console\.info\((.*?)\);', 'info')
    ]
    
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        new_line = line
        for pattern, default_level in patterns:
            if re.search(pattern, line):
                match = re.search(pattern, line)
                if match:
                    log_content = match.group(1)
                    
                    # Determine appropriate log level
                    if default_level in ['error', 'warn', 'info']:
                        level = default_level
                    else:
                        level = categorize_log(line, log_content)
                    
                    # Replace with logger call
                    replacement = f'logger.{level}({log_content});'
                    new_line = line.replace(match.group(0), replacement)
                    replacements[level] += 1
                    
                    # Special handling for multi-line logs
                    if not new_line.strip().endswith(';'):
                        # This might be a multi-line console.log, need manual review
                        print(f"WARNING: Potential multi-line log at line {i+1}")
        
        new_lines.append(new_line)
    
    # Write back
    with open(file_path, 'w') as f:
        f.write('\n'.join(new_lines))
    
    # Report
    total = sum(replacements.values())
    print(f"Replaced {total} console statements:")
    for level, count in replacements.items():
        print(f"  {level}: {count}")
    
    return replacements

if __name__ == '__main__':
    file_path = '/home/box/Documents/aw-rpc/static/js/render.js'
    replace_console_logs(file_path)