"""
Git-related utility functions.
"""
from typing import List, Dict, Any


def parse_file_changes(git_diff: str) -> List[Dict[str, Any]]:
    """
    Parse git diff to extract individual file changes.
    
    Args:
        git_diff: Raw git diff output
        
    Returns:
        List of dicts with 'path', 'before', and 'after' content for each file
    """
    file_changes = []
    current_file = None
    before_lines = []
    after_lines = []
    in_diff = False
    
    for line in git_diff.split('\n'):
        if line.startswith('diff --git'):
            # Save previous file if exists
            if current_file:
                file_changes.append({
                    "path": current_file,
                    "before": '\n'.join(before_lines),
                    "after": '\n'.join(after_lines)
                })
            
            # Extract filename
            parts = line.split(' ')
            if len(parts) >= 4:
                current_file = parts[3][2:] if parts[3].startswith('b/') else parts[3]
            before_lines = []
            after_lines = []
            in_diff = False
            
        elif line.startswith('@@'):
            in_diff = True
        elif in_diff and current_file:
            if line.startswith('-') and not line.startswith('---'):
                before_lines.append(line[1:])
            elif line.startswith('+') and not line.startswith('+++'):
                after_lines.append(line[1:])
            elif not line.startswith('\\'):
                before_lines.append(line[1:] if line else '')
                after_lines.append(line[1:] if line else '')
    
    # Save last file
    if current_file:
        file_changes.append({
            "path": current_file,
            "before": '\n'.join(before_lines),
            "after": '\n'.join(after_lines)
        })
    
    return file_changes