"""
Unit tests for parser_utils module.
"""
import pytest
import json
import os
import sys

# Add parent directory to path to import parser_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser_utils import (
    parse_json_response,
    parse_file_changes,
    normalize_file_path,
    validate_file_operations
)


class TestParseJsonResponse:
    """Tests for parse_json_response function."""
    
    def test_valid_json_response(self):
        """Test parsing valid JSON response."""
        response = json.dumps({
            "summary": "Test changes",
            "file_operations": [
                {"action": "create", "path": "test.py", "content": "print('test')"}
            ]
        })
        result = parse_json_response(response)
        assert len(result) == 1
        assert result[0]["action"] == "create"
        assert result[0]["path"] == "test.py"
    
    def test_invalid_json(self):
        """Test handling of invalid JSON."""
        result = parse_json_response("not json")
        assert result is None
    
    def test_missing_file_operations(self):
        """Test JSON without file_operations key."""
        response = json.dumps({"summary": "No operations"})
        result = parse_json_response(response)
        assert result is None


class TestParseFileChanges:
    """Tests for parse_file_changes function."""
    
    def test_valid_json_response(self):
        """Test parsing valid JSON response."""
        response = json.dumps({
            "file_operations": [
                {"action": "create", "path": "json_file.py", "content": "json content"}
            ]
        })
        result = parse_file_changes(response)
        assert len(result) == 1
        assert result[0]["path"] == "json_file.py"
    
    def test_invalid_json_raises_error(self):
        """Test that invalid JSON raises ValueError."""
        response = "Not JSON content"
        with pytest.raises(ValueError, match="Response must be valid JSON"):
            parse_file_changes(response)
    
    def test_missing_file_operations_raises_error(self):
        """Test that missing file_operations field raises ValueError."""
        response = json.dumps({"summary": "No operations"})
        with pytest.raises(ValueError, match="Response must be valid JSON"):
            parse_file_changes(response)
    
    def test_empty_file_operations(self):
        """Test response with empty file operations list."""
        response = json.dumps({"file_operations": []})
        result = parse_file_changes(response)
        assert result == []
    
    def test_validation_filters_invalid_operations(self):
        """Test that validation filters out invalid operations."""
        response = json.dumps({
            "file_operations": [
                {"action": "create", "path": "valid.py", "content": "content"},
                {"action": "create", "path": "missing_content.py"},  # Missing content
                {"action": "update", "path": "", "content": "no path"},  # Empty path
            ]
        })
        result = parse_file_changes(response)
        assert len(result) == 1
        assert result[0]["path"] == "valid.py"


class TestNormalizeFilePath:
    """Tests for normalize_file_path function."""
    
    def test_relative_path(self):
        """Test normalizing relative path."""
        result = normalize_file_path("src/file.py")
        assert result == "/workspace/repo/src/file.py"
    
    def test_absolute_path_under_repo(self):
        """Test path already under repo root."""
        result = normalize_file_path("/workspace/repo/src/file.py")
        assert result == "/workspace/repo/src/file.py"
    
    def test_absolute_path_not_under_repo(self):
        """Test absolute path not under repo root."""
        result = normalize_file_path("/tmp/file.py")
        assert result == "/workspace/repo/tmp/file.py"
    
    def test_path_with_spaces(self):
        """Test path with leading/trailing spaces."""
        result = normalize_file_path("  src/file.py  ")
        assert result == "/workspace/repo/src/file.py"
    
    def test_custom_repo_root(self):
        """Test with custom repo root."""
        result = normalize_file_path("file.py", "/custom/root")
        assert result == "/custom/root/file.py"


class TestValidateFileOperations:
    """Tests for validate_file_operations function."""
    
    def test_valid_operations(self):
        """Test validation of valid operations."""
        operations = [
            {"action": "create", "path": "file1.py", "content": "content1"},
            {"action": "update", "path": "file2.py", "content": "content2"},
            {"action": "delete", "path": "file3.py"}
        ]
        result = validate_file_operations(operations)
        assert len(result) == 3
    
    def test_invalid_action(self):
        """Test handling of invalid action."""
        operations = [
            {"action": "INVALID", "path": "file.py", "content": "content"}
        ]
        result = validate_file_operations(operations)
        assert len(result) == 1
        assert result[0]["action"] == "update"  # Default
    
    def test_missing_path(self):
        """Test operation with missing path."""
        operations = [
            {"action": "create", "content": "content"}
        ]
        result = validate_file_operations(operations)
        assert len(result) == 0
    
    def test_missing_content_for_create(self):
        """Test create operation without content."""
        operations = [
            {"action": "create", "path": "file.py"}
        ]
        result = validate_file_operations(operations)
        assert len(result) == 0
    
    def test_delete_without_content(self):
        """Test delete operation without content is valid."""
        operations = [
            {"action": "delete", "path": "file.py"}
        ]
        result = validate_file_operations(operations)
        assert len(result) == 1
    
    def test_non_dict_operation(self):
        """Test handling of non-dict operation."""
        operations = ["not a dict", {"action": "create", "path": "file.py", "content": "test"}]
        result = validate_file_operations(operations)
        assert len(result) == 1
        assert result[0]["path"] == "file.py"