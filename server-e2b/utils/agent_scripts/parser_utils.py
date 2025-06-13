"""
Common parsing utilities for agent scripts.

This module provides shared functionality for parsing LLM responses
and extracting file changes.
"""
import re
from typing import List, Dict, Any


def parse_file_changes(response: str) -> List[Dict[str, str]]:
    """
    Parse LLM response to extract file changes.
    
    Looks for various patterns that indicate file modifications:
    1. Markdown code blocks with file paths
    2. Explicit file instructions (Create/Update/Modify)
    3. File paths followed by code blocks
    
    Args:
        response: The LLM response text to parse
        
    Returns:
        List of dicts with 'path', 'content', and 'action' for each file change
    """
    changes = []
    
    # Pattern 1: Markdown code blocks with file paths
    # ```python:path/to/file.py or ```path/to/file.py
    pattern = r'```(?:[\w]+:)?([\w/.-]+)\n(.*?)```'
    matches = re.findall(pattern, response, re.DOTALL)
    
    for file_path, content in matches:
        # Skip generic code blocks without clear file paths
        if '/' in file_path or file_path.endswith(('.py', '.js', '.ts', '.json', '.yml', '.yaml', '.md', '.txt', '.sh')):
            changes.append({
                'path': file_path,
                'content': content.strip(),
                'action': 'create_or_update'
            })
    
    # Pattern 2: Explicit file instructions
    # "Create/Update/Modify file path/to/file:"
    instruction_pattern = r'(Create|Update|Modify|Edit)\s+(?:the\s+)?file\s+([\w/.-]+)[\s:]+(?:\n|$)'
    instruction_matches = re.findall(instruction_pattern, response, re.IGNORECASE | re.MULTILINE)
    
    for action, file_path in instruction_matches:
        if not any(c['path'] == file_path for c in changes):
            # Find content after this instruction
            start_pattern = f"{action}.*?file\\s+{re.escape(file_path)}"
            start_match = re.search(start_pattern, response, re.IGNORECASE)
            if start_match:
                start_idx = start_match.end()
                
                # Look for the next file instruction, code block, or section
                end_patterns = [
                    r'\n(?:Create|Update|Modify|Edit)\s+(?:the\s+)?file',
                    r'\n```',
                    r'\n\n#+\s',  # Markdown headers
                    r'\n\n\n'      # Triple newline
                ]
                
                end_idx = len(response)
                for pattern in end_patterns:
                    match = re.search(pattern, response[start_idx:])
                    if match:
                        end_idx = min(end_idx, start_idx + match.start())
                
                content = response[start_idx:end_idx].strip()
                # Clean up common formatting
                content = re.sub(r'^[\s:]+', '', content)
                
                if content:
                    changes.append({
                        'path': file_path,
                        'content': content,
                        'action': action.lower()
                    })
    
    # Pattern 3: File paths followed by code blocks
    # "In file.py:\n```python\ncode\n```"
    file_block_pattern = r'(?:In|File:|For)\s+([\w/.-]+)[\s:]*\n+```[\w]*\n(.*?)```'
    file_block_matches = re.findall(file_block_pattern, response, re.DOTALL)
    
    for file_path, content in file_block_matches:
        if not any(c['path'] == file_path for c in changes):
            changes.append({
                'path': file_path,
                'content': content.strip(),
                'action': 'create_or_update'
            })
    
    # Pattern 4: File path as code block header
    # ```path/to/file.py\ncontent\n```
    header_pattern = r'```([\w/.-]+)\n(.*?)```'
    header_matches = re.findall(header_pattern, response, re.DOTALL)
    
    for file_path, content in header_matches:
        # Check if this looks like a file path (has extension or directory)
        if ('.' in file_path and not file_path.startswith('.')) or '/' in file_path:
            if not any(c['path'] == file_path for c in changes):
                changes.append({
                    'path': file_path,
                    'content': content.strip(),
                    'action': 'create_or_update'
                })
    
    return changes


def normalize_file_path(file_path: str, repo_root: str = "/workspace/repo") -> str:
    """
    Normalize a file path to be relative to the repository root.
    
    Args:
        file_path: The file path to normalize
        repo_root: The repository root directory (default: /workspace/repo)
        
    Returns:
        Normalized absolute path
    """
    # Remove leading/trailing whitespace
    file_path = file_path.strip()
    
    # If path is already absolute and under repo root, return as is
    if file_path.startswith(repo_root):
        return file_path
    
    # If path is absolute but not under repo root, make it relative
    if file_path.startswith('/'):
        file_path = file_path.lstrip('/')
    
    # Ensure path is under repo root
    return f"{repo_root}/{file_path}"