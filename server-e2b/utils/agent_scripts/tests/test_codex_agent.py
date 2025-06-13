"""
Unit tests for codex_agent module.
"""
import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codex_agent import CodexAgent


class TestCodexAgent:
    """Tests for CodexAgent class."""
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        agent = CodexAgent()
        assert agent.api_key == "test_key"
        assert agent.model == "gpt-4"
        assert agent.max_tokens == 2000
        assert agent.temperature == 0.7
    
    def test_init_without_api_key(self):
        """Test initialization without API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                CodexAgent()
    
    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "test_key",
        "GPT_MODEL": "gpt-4-turbo",
        "MAX_TOKENS": "4000",
        "TEMPERATURE": "0.9"
    })
    def test_init_with_custom_env_vars(self):
        """Test initialization with custom environment variables."""
        agent = CodexAgent()
        assert agent.model == "gpt-4-turbo"
        assert agent.max_tokens == 4000
        assert agent.temperature == 0.9
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_read_prompt_success(self):
        """Test successful prompt reading."""
        agent = CodexAgent()
        with patch("builtins.open", MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "Test prompt"
            result = agent.read_prompt()
            assert result == "Test prompt"
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @patch("os.walk")
    def test_analyze_repository(self, mock_walk):
        """Test repository analysis."""
        mock_walk.return_value = [
            ("/workspace/repo", ["src", ".git"], ["README.md", "package.json"]),
            ("/workspace/repo/src", [], ["index.js", "app.py", "main.go"])
        ]
        
        agent = CodexAgent()
        result = agent.analyze_repository()
        
        assert "README.md" in result["files"]
        assert "package.json" in result["files"]
        assert "src/index.js" in result["files"]
        assert "js" in result["languages"]
        assert "py" in result["languages"]
        assert "go" in result["languages"]
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_generate_system_prompt(self):
        """Test system prompt generation."""
        agent = CodexAgent()
        repo_info = {
            "languages": ["python", "javascript"],
            "files": ["main.py", "utils.js", "test.py"]
        }
        
        prompt = agent.generate_system_prompt(repo_info)
        assert "python, javascript" in prompt
        assert "3 files" in prompt
        assert "JSON object" in prompt
        assert "file_operations" in prompt
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @patch("openai.ChatCompletion.create")
    def test_execute_task_with_function_call(self, mock_create):
        """Test task execution with function calling."""
        agent = CodexAgent()
        
        # Mock OpenAI response with function call
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = {
            "function_call": Mock(arguments=json.dumps({
                "summary": "Created test file",
                "file_operations": [
                    {"action": "create", "path": "test.py", "content": "print('test')"}
                ]
            }))
        }
        mock_create.return_value = mock_response
        
        # Mock repository analysis
        with patch.object(agent, 'analyze_repository', return_value={
            "files": [], "directories": [], "languages": ["python"], "key_files": []
        }):
            result = agent.execute_task("Create a test file")
            
            # Verify the result is JSON
            parsed = json.loads(result)
            assert parsed["summary"] == "Created test file"
            assert len(parsed["file_operations"]) == 1
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_apply_changes_with_json(self):
        """Test applying changes from JSON response."""
        agent = CodexAgent()
        
        response = json.dumps({
            "summary": "Created multiple files",
            "file_operations": [
                {"action": "create", "path": "file1.py", "content": "content1"},
                {"action": "update", "path": "file2.py", "content": "content2"},
                {"action": "delete", "path": "old.py"}
            ]
        })
        
        with patch("os.makedirs"), \
             patch("os.path.exists", side_effect=[False, False, True, True]), \
             patch("os.remove") as mock_remove, \
             patch("builtins.open", MagicMock()), \
             patch("builtins.print"):
            result = agent.apply_changes(response)
            assert result is True
            mock_remove.assert_called_once()
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_apply_changes_invalid_json(self):
        """Test that invalid JSON returns False."""
        agent = CodexAgent()
        
        # Non-JSON response
        response = "Not valid JSON"
        
        with patch("builtins.print"):
            result = agent.apply_changes(response)
            assert result is False
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_apply_changes_with_errors(self):
        """Test apply_changes returns False on errors."""
        agent = CodexAgent()
        
        response = json.dumps({
            "file_operations": [
                {"action": "create", "path": "test.py", "content": "content"}
            ]
        })
        
        with patch("os.makedirs", side_effect=Exception("Permission denied")), \
             patch("builtins.print"):
            result = agent.apply_changes(response)
            assert result is False
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @patch("openai.ChatCompletion.create")
    def test_execute_task_rate_limit_error(self, mock_create):
        """Test handling of rate limit error."""
        agent = CodexAgent()
        
        # Mock rate limit error
        import openai
        mock_create.side_effect = openai.error.RateLimitError("Rate limit exceeded")
        
        with patch.object(agent, 'analyze_repository', return_value={"files": [], "languages": []}):
            result = agent.execute_task("Test prompt")
            assert "rate limit exceeded" in result.lower()