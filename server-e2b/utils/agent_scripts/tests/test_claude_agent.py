"""
Unit tests for claude_agent module.
"""
import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_agent import ClaudeAgent


class TestClaudeAgent:
    """Tests for ClaudeAgent class."""
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"})
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        agent = ClaudeAgent()
        assert agent.api_key == "test_key"
        assert agent.model == "claude-3-sonnet-20240229"
    
    def test_init_without_api_key(self):
        """Test initialization without API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                ClaudeAgent()
    
    @patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test_key",
        "CLAUDE_MODEL": "custom-model",
        "CLAUDE_MAX_TOKENS": "8000",
        "CLAUDE_TEMPERATURE": "0.5"
    })
    def test_init_with_custom_env_vars(self):
        """Test initialization with custom environment variables."""
        agent = ClaudeAgent()
        assert agent.model == "custom-model"
        assert agent.max_tokens == 8000
        assert agent.temperature == 0.5
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"})
    def test_read_prompt_success(self):
        """Test successful prompt reading."""
        agent = ClaudeAgent()
        with patch("builtins.open", MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "Test prompt"
            result = agent.read_prompt()
            assert result == "Test prompt"
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"})
    def test_read_prompt_file_not_found(self):
        """Test prompt reading with missing file."""
        agent = ClaudeAgent()
        with patch("builtins.open", side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                agent.read_prompt("/nonexistent/file.txt")
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"})
    @patch("os.walk")
    def test_analyze_repository(self, mock_walk):
        """Test repository analysis."""
        mock_walk.return_value = [
            ("/workspace/repo", ["src", ".git"], ["README.md", ".gitignore"]),
            ("/workspace/repo/src", [], ["main.py", "utils.py", "test.js"])
        ]
        
        agent = ClaudeAgent()
        result = agent.analyze_repository()
        
        assert "README.md" in result["files"]
        assert "src/main.py" in result["files"]
        assert "src/utils.py" in result["files"]
        assert "src/test.js" in result["files"]
        assert ".gitignore" not in result["files"]  # Hidden files excluded
        assert "python" in result["languages"]
        assert "javascript" in result["languages"]
        assert len(result["key_files"]) > 0
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"})
    def test_execute_task_success(self):
        """Test successful task execution."""
        agent = ClaudeAgent()
        
        # Mock the Anthropic client
        mock_message = Mock()
        mock_message.content = [Mock(text=json.dumps({
            "summary": "Test changes",
            "file_operations": [
                {"action": "create", "path": "test.py", "content": "print('test')"}
            ]
        }))]
        
        agent.client = Mock()
        agent.client.messages.create.return_value = mock_message
        
        # Mock repository analysis
        with patch.object(agent, 'analyze_repository', return_value={
            "files": [], "directories": [], "languages": ["python"], "key_files": []
        }):
            with patch.object(agent, 'read_key_files', return_value={}):
                result = agent.execute_task("Create a test file")
                
                # Verify the result is JSON
                parsed = json.loads(result)
                assert parsed["summary"] == "Test changes"
                assert len(parsed["file_operations"]) == 1
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"})
    def test_apply_changes_with_json(self):
        """Test applying changes from JSON response."""
        agent = ClaudeAgent()
        
        response = json.dumps({
            "summary": "Created test file",
            "file_operations": [
                {"action": "create", "path": "test.py", "content": "print('test')"}
            ]
        })
        
        with patch("os.makedirs"), patch("os.path.exists", return_value=False), \
             patch("builtins.open", MagicMock()), patch("builtins.print"):
            result = agent.apply_changes(response)
            assert result is True
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"})
    def test_apply_changes_with_delete(self):
        """Test applying delete operation."""
        agent = ClaudeAgent()
        
        response = json.dumps({
            "file_operations": [
                {"action": "delete", "path": "old.py"}
            ]
        })
        
        with patch("os.path.exists", return_value=True), \
             patch("os.remove") as mock_remove, \
             patch("builtins.print"):
            result = agent.apply_changes(response)
            assert result is True
            mock_remove.assert_called_once()
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"})
    def test_apply_changes_with_errors(self):
        """Test apply_changes returns False on errors."""
        agent = ClaudeAgent()
        
        response = json.dumps({
            "file_operations": [
                {"action": "create", "path": "test.py", "content": "content"}
            ]
        })
        
        with patch("os.makedirs", side_effect=Exception("Permission denied")), \
             patch("builtins.print"):
            result = agent.apply_changes(response)
            assert result is False