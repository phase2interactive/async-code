"""
Common parsing utilities for agent scripts.

This module provides shared functionality for parsing LLM responses
and extracting file changes. Supports both structured JSON output
and fallback regex-based parsing.
"""
import re
import json
import logging
from typing import List, Dict, Any, Union, Optional

logger = logging.getLogger(__name__)


def parse_json_response(response: str) -> Optional[List[Dict[str, str]]]:
    """
    Parse structured JSON response from LLM.
    
    Expected format:
    {
        "summary": "Description of changes",
        "file_operations": [
            {
                "action": "create" | "update" | "delete",
                "path": "path/to/file",
                "content": "file content" (optional for delete)
            }
        ]
    }
    
    Args:
        response: The LLM response text to parse
        
    Returns:
        List of dicts with 'path', 'content', and 'action' for each file change
        Returns None if parsing fails or file_operations field is missing
    """
    try:
        data = json.loads(response)
        if "file_operations" in data and isinstance(data["file_operations"], list):
            return data["file_operations"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.debug(f"Failed to parse JSON response: {e}")
    
    return None


def parse_file_changes(response: str) -> List[Dict[str, str]]:
    """
    Parse LLM response to extract file changes from structured JSON.
    
    Expected JSON format:
    {
        "summary": "Description of changes",
        "file_operations": [
            {
                "action": "create" | "update" | "delete",
                "path": "path/to/file",
                "content": "file content" (optional for delete)
            }
        ]
    }
    
    Args:
        response: The LLM response text to parse
        
    Returns:
        List of dicts with 'path', 'content', and 'action' for each file change
        
    Raises:
        ValueError: If response is not valid JSON or missing required fields
    
    Note:
        This function enforces strict JSON parsing without fallback to ensure
        reliability. If LLMs fail to produce valid JSON, the prompting strategy
        or model configuration should be adjusted rather than accepting
        ambiguous formats.
    """
    changes = parse_json_response(response)
    if changes is None:
        logger.error("Failed to parse JSON response or no file operations found")
        raise ValueError("Response must be valid JSON with 'file_operations' field")
    
    # Empty list is valid (no operations to perform)
    if not changes:
        logger.info("No file operations to perform")
        return []
    
    # Validate operations
    validated = validate_file_operations(changes)
    if not validated:
        logger.warning("No valid file operations found after validation")
    
    return validated


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


def validate_file_operations(operations: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Validate and normalize file operations from structured output.
    
    Args:
        operations: List of file operations to validate
        
    Returns:
        List of validated operations
    """
    validated = []
    
    for op in operations:
        if not isinstance(op, dict):
            logger.warning(f"Skipping non-dict operation: {op}")
            continue
            
        action = op.get('action', '').lower()
        if action not in ['create', 'update', 'delete']:
            logger.warning(f"Invalid action '{action}', defaulting to 'update'")
            action = 'update'
        
        path = op.get('path', '')
        if not path:
            logger.warning("Skipping operation with empty path")
            continue
        
        content = op.get('content', '')
        if action in ['create', 'update'] and not content:
            logger.warning(f"No content provided for {action} operation on {path}")
            continue
        
        validated.append({
            'action': action,
            'path': path,
            'content': content
        })
    
    return validated