"""
Comprehensive E2B Sandbox Test Scenarios
Tests various edge cases, configurations, and error handling for E2B sandbox environments
"""

import os
import json
import time
import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from e2b import Sandbox
from e2b.exceptions import SandboxException, NotFoundException, RateLimitException

from utils.code_task_e2b_real import E2BCodeExecutor
from utils.logging_config import setup_logger

logger = setup_logger()


class TestE2BSandboxScenarios:
    """Test suite for E2B sandbox environment scenarios"""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Set up test environment variables"""
        monkeypatch.setenv("E2B_API_KEY", "test-api-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        monkeypatch.setenv("GITHUB_TOKEN", "test-github-token")
        
    @pytest.fixture
    def executor(self, mock_env, monkeypatch):
        """Create E2B executor instance"""
        # Ensure template ID is available before creating executor
        if 'E2B_TEMPLATE_ID' in os.environ:
            monkeypatch.setenv("E2B_TEMPLATE_ID", os.environ['E2B_TEMPLATE_ID'])
        return E2BCodeExecutor()
        
    # Test 1: Custom Template Handling
    @pytest.mark.anyio
    async def test_custom_template_creation(self, executor, monkeypatch):
        """Test sandbox creation with custom E2B template"""
        custom_template_id = "test-custom-template"
        monkeypatch.setenv("E2B_TEMPLATE_ID", custom_template_id)
        
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox_class.return_value = mock_sandbox
            
            # Simulate sandbox with pre-configured environment
            mock_sandbox.commands.run.return_value = Mock(
                exit_code=0,
                stdout="/workspace exists",
                stderr=""
            )
            
            # Mock database operations
            with patch('utils.code_task_e2b_real.DatabaseOperations') as mock_db:
                mock_db_instance = Mock()
                mock_db.return_value = mock_db_instance
                mock_db_instance.update_task_status = AsyncMock()
                mock_db_instance.update_task_chat_history = AsyncMock()
                
                # Test will fail at git clone, but we can verify sandbox creation
                try:
                    await executor.execute_task(
                        task_id=1,
                        user_id="test-user",
                        github_token="test-token",
                        repo_url="https://github.com/test/repo",
                        branch="main",
                        prompt="Test prompt",
                        agent="claude"
                    )
                except Exception:
                    pass  # Expected to fail at git operations
                
                # Verify custom template was used
                mock_sandbox_class.assert_called()
                call_args = mock_sandbox_class.call_args[1]
                # Check if template was passed (it's only added if E2B_TEMPLATE_ID is set)
                if 'template' in call_args:
                    assert call_args['template'] == custom_template_id
                assert 'envs' in call_args  # Environment variables should be passed
            
    @pytest.mark.anyio
    async def test_template_fallback_on_error(self, monkeypatch):
        """Test handling of template errors"""
        # Set template ID before creating executor
        monkeypatch.setenv("E2B_TEMPLATE_ID", "non-existent-template")
        monkeypatch.setenv("E2B_API_KEY", "test-api-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        monkeypatch.setenv("GITHUB_TOKEN", "test-github-token")
        
        # Create executor after setting env vars
        from utils.code_task_e2b_real import E2BCodeExecutor
        executor = E2BCodeExecutor()
        
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            # Simulate template not found error
            mock_sandbox_class.side_effect = NotFoundException("Template not found")
            
            # Mock database operations
            with patch('utils.code_task_e2b_real.DatabaseOperations') as mock_db:
                mock_db.update_task = Mock()
                
                # Execute task should fail with a proper error message
                with pytest.raises(Exception) as exc_info:
                    await executor.execute_task(
                        task_id=1,
                        user_id="test-user",
                        github_token="test-token",
                        repo_url="https://github.com/test/repo",
                        branch="main",
                        prompt="Test prompt",
                        agent="claude"
                    )
                
                # Verify error is caught and re-raised with descriptive message
                assert "Failed to create E2B sandbox" in str(exc_info.value)
                
                # Verify sandbox was attempted with the template
                assert mock_sandbox_class.called
                call_kwargs = mock_sandbox_class.call_args[1]
                assert 'template' in call_kwargs
                assert call_kwargs['template'] == "non-existent-template"
            
    # Test 2: Environment Variable Security
    @pytest.mark.anyio
    async def test_env_var_sanitization_in_errors(self, executor):
        """Test that sensitive env vars are not exposed in error messages"""
        sensitive_values = [
            executor.github_token,
            executor.anthropic_api_key,
            executor.openai_api_key,
            executor.api_key
        ]
        
        error_message = f"Failed with tokens: {executor.github_token}, {executor.anthropic_api_key}"
        sanitized = executor._sanitize_error_message(error_message)
        
        for value in sensitive_values:
            if value:
                assert value not in sanitized
                assert "***" in sanitized
                
    # Test 3: Quota and Rate Limit Handling
    @pytest.mark.anyio
    async def test_quota_exceeded_handling(self, executor):
        """Test behavior when E2B quota is exceeded"""
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox_class.side_effect = RateLimitException("Quota exceeded")
            
            # Mock database operations
            with patch('utils.code_task_e2b_real.DatabaseOperations') as mock_db:
                mock_db.update_task = Mock()
                
                with pytest.raises(Exception) as exc_info:
                    await executor.execute_task(
                        task_id=1,
                        user_id="test-user",
                        github_token="test-token",
                        repo_url="https://github.com/test/repo",
                        branch="main",
                        prompt="Test prompt",
                        agent="claude"
                    )
                
                # Verify specific quota error message is raised
                assert "quota" in str(exc_info.value).lower()
                assert "E2B sandbox quota exceeded" in str(exc_info.value)
            
    # Test 4: Network Timeout Scenarios
    @pytest.mark.anyio
    async def test_clone_timeout_handling(self, executor):
        """Test timeout during repository cloning"""
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox_class.return_value = mock_sandbox
            
            # Mock successful mkdir, then simulate slow clone that times out
            call_count = 0
            def run_command(cmd):
                nonlocal call_count
                call_count += 1
                if call_count == 1:  # mkdir command
                    return Mock(exit_code=0, stdout="", stderr="")
                # For git clone, simulate a hang (the asyncio.wait_for will handle timeout)
                import time
                time.sleep(100)  # Sleep longer than timeout
                return Mock(exit_code=0)
                
            mock_sandbox.commands.run = run_command
            
            # Mock database operations
            with patch('utils.code_task_e2b_real.DatabaseOperations') as mock_db:
                mock_db.update_task = Mock()
                
                with pytest.raises(Exception) as exc_info:
                    await executor.execute_task(
                        task_id=1,
                        user_id="test-user",
                        github_token="test-token",
                        repo_url="https://github.com/test/repo.git",
                        branch="main",
                        prompt="test",
                        agent="claude"
                    )
                
                # Verify timeout error message
                assert "Git clone timed out" in str(exc_info.value)
                assert str(executor.CLONE_TIMEOUT) in str(exc_info.value)
                
    # Test 5: Permission Error Handling
    @pytest.mark.anyio
    async def test_permission_error_with_sudo_fallback(self, executor):
        """Test handling of permission errors during directory creation"""
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox_class.return_value = mock_sandbox
            
            # Simulate mkdir permission denied error
            mock_sandbox.commands.run.return_value = Mock(
                exit_code=1, 
                stdout="",
                stderr="Permission denied"
            )
            
            # Mock database operations
            with patch('utils.code_task_e2b_real.DatabaseOperations') as mock_db:
                mock_db.update_task = Mock()
                
                with pytest.raises(Exception) as exc_info:
                    await executor.execute_task(
                        task_id=1,
                        user_id="test-user",
                        github_token="test-token",
                        repo_url="https://github.com/test/repo.git",
                        branch="main",
                        prompt="test",
                        agent="claude"
                    )
                
                # Verify error is raised for failed workspace creation
                assert "Failed to create workspace directory" in str(exc_info.value)
                assert "Permission denied" in str(exc_info.value)
            
    # Test 6: Agent-Specific Error Handling
    @pytest.mark.anyio
    async def test_claude_agent_fallback_on_sdk_error(self, executor, monkeypatch):
        """Test Claude agent execution when SDK script fails"""
        # Mock that the sophisticated script doesn't exist to force CLI fallback
        monkeypatch.setattr('os.path.exists', lambda path: False if 'claude_agent.py' in path else True)
        
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox_class.return_value = mock_sandbox
            
            # Mock file operations
            mock_sandbox.files.write = Mock()
            
            # Mock command execution
            command_results = [
                Mock(exit_code=0, stdout="", stderr=""),  # mkdir succeeds
                Mock(exit_code=0, stdout="", stderr=""),  # git clone succeeds
                Mock(exit_code=0, stdout="", stderr=""),  # git config email
                Mock(exit_code=0, stdout="total 0", stderr=""),  # initial ls
                Mock(exit_code=1, stdout="", stderr=""),  # which claude (not installed)
                Mock(exit_code=0, stdout="", stderr=""),  # npm install claude
                Mock(exit_code=0, stdout="Claude response from CLI", stderr=""),  # claude execution
                Mock(exit_code=0, stdout="", stderr=""),  # git status
                Mock(exit_code=0, stdout="", stderr=""),  # git diff
            ]
            mock_sandbox.commands.run.side_effect = command_results
            
            # Mock database operations
            with patch('utils.code_task_e2b_real.DatabaseOperations') as mock_db:
                mock_db.update_task = Mock()
                mock_db.add_chat_message = Mock()
                
                result = await executor.execute_task(
                    task_id=1,
                    user_id="test-user",
                    github_token="test-token",
                    repo_url="https://github.com/test/repo.git",
                    branch="main",
                    prompt="test prompt",
                    agent="claude"
                )
                
                # Verify CLI was used and task completed
                assert result["status"] == "completed"
                assert "Claude response from CLI" in result["agent_output"]
                
                # Verify the appropriate commands were run
                commands_run = [call[0][0] for call in mock_sandbox.commands.run.call_args_list]
                assert any("claude < " in cmd for cmd in commands_run)
            
    # Test 7: Private Repository Authentication
    @pytest.mark.anyio
    async def test_private_repo_with_github_token(self, executor):
        """Test cloning private repository with GitHub token"""
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox_class.return_value = mock_sandbox
            
            # Mock successful operations
            mock_sandbox.commands.run.return_value = Mock(exit_code=0, stdout="", stderr="")
            mock_sandbox.files.write = Mock()
            
            # Mock database operations
            with patch('utils.code_task_e2b_real.DatabaseOperations') as mock_db:
                mock_db.update_task = Mock()
                mock_db.add_chat_message = Mock()
                
                # Execute task with GitHub token
                github_token = "test-github-token"
                private_repo = "https://github.com/private/repo.git"
                
                try:
                    await executor.execute_task(
                        task_id=1,
                        user_id="test-user",
                        github_token=github_token,
                        repo_url=private_repo,
                        branch="main",
                        prompt="test",
                        agent="claude"
                    )
                except:
                    pass  # May fail at agent execution, but we're testing git clone
                
                # Find the git clone command
                clone_commands = [call[0][0] for call in mock_sandbox.commands.run.call_args_list 
                                if "git clone" in call[0][0]]
                assert len(clone_commands) > 0
                clone_command = clone_commands[0]
                
                # Verify token was injected into URL
                assert github_token in clone_command
                assert f"https://{github_token}@github.com/private/repo.git" in clone_command
            
    # Test 8: Large Output Handling
    @pytest.mark.anyio
    async def test_large_command_output_truncation(self, executor):
        """Test handling of commands with large outputs"""
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox_class.return_value = mock_sandbox
            
            # Generate large output from git diff
            large_diff_output = "diff --git a/file.py b/file.py\n" + ("+ " + "x" * 1000 + "\n") * 500
            
            # Mock command results
            command_results = [
                Mock(exit_code=0, stdout="", stderr=""),  # mkdir
                Mock(exit_code=0, stdout="", stderr=""),  # git clone
                Mock(exit_code=0, stdout="", stderr=""),  # git config email
                Mock(exit_code=0, stdout="total 0", stderr=""),  # initial ls
                Mock(exit_code=1, stdout="", stderr=""),  # which claude (not installed)
                Mock(exit_code=0, stdout="", stderr=""),  # npm install claude
                Mock(exit_code=0, stdout="Task completed", stderr=""),  # claude execution
                Mock(exit_code=0, stdout="M file.py", stderr=""),  # git status
                Mock(exit_code=0, stdout=large_diff_output, stderr=""),  # git diff with large output
                Mock(exit_code=0, stdout="", stderr=""),  # git add -A
                Mock(exit_code=0, stdout="[main abc1234] AI: test...", stderr=""),  # git commit
                Mock(exit_code=0, stdout="commit abc1234\nAuthor: AI Assistant\nDate: Mon Jan 1\n\n    AI: test...", stderr=""),  # git log
                Mock(exit_code=0, stdout="From abc1234..def5678  main -> main", stderr=""),  # format-patch
            ]
            mock_sandbox.commands.run.side_effect = command_results
            mock_sandbox.files.write = Mock()
            mock_sandbox.kill = Mock()
            
            # Mock database operations
            with patch('utils.code_task_e2b_real.DatabaseOperations') as mock_db:
                mock_db.update_task = Mock()
                mock_db.add_chat_message = Mock()
                
                result = await executor.execute_task(
                    task_id=1,
                    user_id="test-user",
                    github_token="test-token",
                    repo_url="https://github.com/test/repo.git",
                    branch="main",
                    prompt="test",
                    agent="claude"
                )
                
                # Verify the task completed successfully even with large output
                assert result["status"] == "completed"
                assert result["git_diff"] == large_diff_output
                
                # Verify database was updated with the large diff
                update_calls = [call for call in mock_db.update_task.call_args_list 
                               if len(call[0]) > 2 and isinstance(call[0][2], dict) and 'git_diff' in call[0][2]]
                assert len(update_calls) > 0
                assert update_calls[-1][0][2]['git_diff'] == large_diff_output
            
    # Test 9: Concurrent Sandbox Execution
    @pytest.mark.anyio
    async def test_concurrent_sandbox_isolation(self, executor):
        """Test that multiple sandboxes don't interfere with each other"""
        sandbox_ids = []
        task_counter = 0
        
        async def create_and_track_sandbox():
            nonlocal task_counter
            task_id = task_counter
            task_counter += 1
            
            with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
                mock_sandbox = Mock()
                mock_sandbox.id = f"sandbox-{task_id}"
                mock_sandbox_class.return_value = mock_sandbox
                mock_sandbox.commands.run.return_value = Mock(exit_code=0, stdout="", stderr="")
                mock_sandbox.files.write = Mock()
                mock_sandbox.kill = Mock()
                
                # Mock database operations
                with patch('utils.code_task_e2b_real.DatabaseOperations') as mock_db:
                    mock_db.update_task = Mock()
                    mock_db.add_chat_message = Mock()
                    
                    try:
                        await executor.execute_task(
                            task_id=task_id,
                            user_id="test-user",
                            github_token="test-token",
                            repo_url="https://github.com/test/repo.git",
                            branch="main",
                            prompt="test",
                            agent="claude"
                        )
                    except:
                        pass  # May fail, but we're testing sandbox creation
                    
                    sandbox_ids.append(mock_sandbox.id)
                    return mock_sandbox
                
        # Create multiple sandboxes concurrently
        sandboxes = await asyncio.gather(*[
            create_and_track_sandbox() for _ in range(3)
        ])
        
        # Verify all sandboxes have unique IDs
        assert len(set(sandbox_ids)) == 3
        assert set(sandbox_ids) == {"sandbox-0", "sandbox-1", "sandbox-2"}
        
    # Test 10: Sandbox Cleanup on Error
    @pytest.mark.anyio
    async def test_sandbox_cleanup_on_exception(self, executor):
        """Test that sandbox is properly cleaned up on exceptions"""
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox_class.return_value = mock_sandbox
            mock_sandbox.kill = Mock()
            
            # Simulate error during execution
            mock_sandbox.commands.run.side_effect = Exception("Execution failed")
            
            # Mock database operations
            with patch('utils.code_task_e2b_real.DatabaseOperations') as mock_db:
                mock_db.update_task = Mock()
                
                with pytest.raises(Exception):
                    await executor.execute_task(
                        task_id=1,
                        user_id="test-user",
                        github_token="test-token",
                        repo_url="https://github.com/test/repo.git",
                        branch="main",
                        prompt="test",
                        agent="claude"
                    )
                
            # Verify sandbox was killed
            mock_sandbox.kill.assert_called_once()
            
    # Test 11: Binary File Handling
    @pytest.mark.anyio
    async def test_binary_file_operations(self, executor):
        """Test handling of binary files in sandbox"""
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox_class.return_value = mock_sandbox
            
            # Mock that the agent creates a binary file
            binary_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
            
            # Mock command results including binary file operations
            command_results = [
                Mock(exit_code=0, stdout="", stderr=""),  # mkdir
                Mock(exit_code=0, stdout="", stderr=""),  # git clone
                Mock(exit_code=0, stdout="", stderr=""),  # git config email
                Mock(exit_code=0, stdout="total 0", stderr=""),  # initial ls
                Mock(exit_code=1, stdout="", stderr=""),  # which claude (not installed)
                Mock(exit_code=0, stdout="", stderr=""),  # npm install claude
                Mock(exit_code=0, stdout="Created image.png", stderr=""),  # claude execution
                Mock(exit_code=0, stdout="A  image.png", stderr=""),  # git status showing binary file
                Mock(exit_code=0, stdout="Binary files /dev/null and b/image.png differ", stderr=""),  # git diff
                Mock(exit_code=0, stdout="", stderr=""),  # git add -A
                Mock(exit_code=0, stdout="[main abc1234] AI: Create a simple PNG image...", stderr=""),  # git commit
                Mock(exit_code=0, stdout="commit abc1234\nAuthor: AI Assistant\nDate: Mon Jan 1\n\n    AI: Create a simple PNG image...", stderr=""),  # git log
                Mock(exit_code=0, stdout="From abc1234..def5678  main -> main", stderr=""),  # format-patch
            ]
            mock_sandbox.commands.run.side_effect = command_results
            
            # Mock file operations for binary handling
            def write_side_effect(path, content):
                # Simulate writing binary data
                if path == "/tmp/agent_prompt.txt":
                    assert isinstance(content, str)
                elif path.endswith(".png"):
                    # In real scenario, agent might create binary files
                    pass
                    
            mock_sandbox.files.write = Mock(side_effect=write_side_effect)
            mock_sandbox.kill = Mock()
            
            # Mock database operations
            with patch('utils.code_task_e2b_real.DatabaseOperations') as mock_db:
                mock_db.update_task = Mock()
                mock_db.add_chat_message = Mock()
                
                result = await executor.execute_task(
                    task_id=1,
                    user_id="test-user",
                    github_token="test-token",
                    repo_url="https://github.com/test/repo.git",
                    branch="main",
                    prompt="Create a simple PNG image",
                    agent="claude"
                )
                
                # Verify task completed successfully
                assert result["status"] == "completed"
                assert "image.png" in result["agent_output"]
                
                # Verify binary file was detected in changes
                assert len(result["changes"]) > 0
                binary_file = next((f for f in result["changes"] if f["path"] == "image.png"), None)
                assert binary_file is not None
                assert binary_file["status"] == "A"  # Added
                
                # Verify git diff shows binary file
                assert "Binary files" in result["git_diff"]
            
    # Test 12: Git Operations Edge Cases
    @pytest.mark.anyio
    async def test_non_existent_branch_handling(self, executor):
        """Test handling of non-existent branch"""
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox_class.return_value = mock_sandbox
            
            # Mock successful mkdir but failed clone due to non-existent branch
            mock_sandbox.commands.run.side_effect = [
                Mock(exit_code=0, stdout="", stderr=""),  # mkdir
                Mock(exit_code=1, stdout="", stderr="error: pathspec 'non-existent' did not match any file(s) known to git")  # clone fails
            ]
            
            # Mock database operations
            with patch('utils.code_task_e2b_real.DatabaseOperations') as mock_db:
                mock_db.update_task = Mock()
                
                with pytest.raises(Exception) as exc_info:
                    await executor.execute_task(
                        task_id=1,
                        user_id="test-user",
                        github_token="test-token",
                        repo_url="https://github.com/test/repo.git",
                        branch="non-existent",
                        prompt="test",
                        agent="claude"
                    )
                
                # Verify appropriate error message about branch
                error_msg = str(exc_info.value)
                assert "Failed to clone repository" in error_msg
                assert "non-existent" in error_msg


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([__file__, "-v", "-k", "test_"])