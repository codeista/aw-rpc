# Claude Safety Hooks

## File Deletion Protection

**IMPORTANT**: Never use `rm` or delete files without explicit user permission.

### Rules:
1. **NEVER** use `rm`, `rm -f`, `rm -rf` or any deletion commands without asking first
2. **ALWAYS** ask for permission before deleting any file, even temporary ones
3. **EXCEPTION**: You may clean up files you just created in the same conversation if there was an error

### Safe Alternatives:
- Instead of deleting, consider:
  - Moving files to a `temp/` or `backup/` directory
  - Renaming files with `.old` or `.backup` suffix
  - Commenting out code instead of deleting it
  - Creating new versions instead of overwriting

### When Deletion is Needed:
1. Explain what files you want to delete and why
2. Wait for explicit user confirmation
3. Only then proceed with deletion

### Example:
```
BAD:  rm old_file.py
GOOD: "I notice old_file.py appears to be unused. May I delete it?"
      [Wait for user response]
      [If yes] rm old_file.py
```

## Other Safety Hooks

### Git Operations
- Never force push without permission
- Never reset --hard without permission
- Never change git history without permission

### System Changes
- Never modify system files without permission
- Never install packages globally without permission
- Never change file permissions without permission

### Data Safety
- Always make backups before major changes
- Never overwrite files without reading them first
- Always use version control when available