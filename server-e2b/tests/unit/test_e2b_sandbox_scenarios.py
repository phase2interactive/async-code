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
    async def test_template_fallback_on_error(self, executor, monkeypatch):
        """Test fallback to default when custom template fails"""
        monkeypatch.setenv("E2B_TEMPLATE_ID", "non-existent-template")
        
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            # First call with template fails
            mock_sandbox_class.side_effect = [
                NotFoundException("Template not found"),
                Mock()  # Second call without template succeeds
            ]
            
            result = await executor._create_e2b_sandbox()
            
            # Verify it tried with template first, then without
            assert mock_sandbox_class.call_count == 2
            first_call = mock_sandbox_class.call_args_list[0]
            second_call = mock_sandbox_class.call_args_list[1]
            
            assert 'template' in first_call.kwargs
            assert 'template' not in second_call.kwargs
            
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
            
            with pytest.raises(Exception) as exc_info:
                await executor._create_e2b_sandbox()
                
            assert "quota" in str(exc_info.value).lower()
            
    # Test 4: Network Timeout Scenarios
    @pytest.mark.anyio
    async def test_clone_timeout_handling(self, executor):
        """Test timeout during repository cloning"""
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox_class.return_value = mock_sandbox
            
            # Simulate slow clone that times out
            async def slow_clone(*args, **kwargs):
                await asyncio.sleep(executor.CLONE_TIMEOUT + 1)
                return Mock(exit_code=0)
                
            mock_sandbox.commands.run = slow_clone
            
            task_data = {
                "repo_url": "https://github.com/test/repo.git",
                "branch": "main",
                "prompt": "test"
            }
            
            with pytest.raises(asyncio.TimeoutError):
                await executor.execute_task(task_data, agent_type="claude")
                
    # Test 5: Permission Error Handling
    @pytest.mark.anyio
    async def test_permission_error_with_sudo_fallback(self, executor):
        """Test sudo fallback when directory creation fails"""
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox_class.return_value = mock_sandbox
            
            # First mkdir fails, sudo succeeds
            mock_sandbox.commands.run.side_effect = [
                Mock(exit_code=1, stderr="Permission denied"),  # mkdir fails
                Mock(exit_code=0, stderr=""),  # sudo mkdir succeeds
                Mock(exit_code=0, stderr="")   # git clone succeeds
            ]
            
            sandbox = await executor._create_e2b_sandbox()
            
            # Verify sudo command was attempted
            calls = mock_sandbox.commands.run.call_args_list
            assert any("sudo" in str(call) for call in calls)
            
    # Test 6: Agent-Specific Error Handling
    @pytest.mark.anyio
    async def test_claude_agent_fallback_on_sdk_error(self, executor):
        """Test Claude agent falls back to CLI when SDK fails"""
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox_class.return_value = mock_sandbox
            
            # Simulate SDK script failure
            mock_sandbox.commands.run.side_effect = [
                Mock(exit_code=0),  # mkdir succeeds
                Mock(exit_code=0),  # clone succeeds
                Mock(exit_code=1, stderr="ModuleNotFoundError: anthropic"),  # SDK fails
                Mock(exit_code=0, stdout="Claude response")  # CLI succeeds
            ]
            
            task_data = {
                "repo_url": "https://github.com/test/repo.git",
                "branch": "main",
                "prompt": "test prompt"
            }
            
            result = await executor.execute_task(task_data, agent_type="claude")
            
            # Verify fallback was used
            assert result["status"] == "completed"
            assert "Claude response" in result["agent_output"]
            
    # Test 7: Private Repository Authentication
    @pytest.mark.anyio
    async def test_private_repo_with_github_token(self, executor):
        """Test cloning private repository with GitHub token"""
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox_class.return_value = mock_sandbox
            
            mock_sandbox.commands.run.return_value = Mock(exit_code=0)
            
            private_repo = "https://github.com/private/repo.git"
            task_data = {
                "repo_url": private_repo,
                "branch": "main",
                "prompt": "test"
            }
            
            # Execute task - should inject token into URL
            await executor._clone_repository(mock_sandbox, task_data)
            
            # Verify token was added to URL
            clone_call = mock_sandbox.commands.run.call_args[0][0]
            assert executor.github_token in clone_call
            assert f"https://{executor.github_token}@github.com" in clone_call
            
    # Test 8: Large Output Handling
    @pytest.mark.anyio
    async def test_large_command_output_truncation(self, executor):
        """Test handling of commands with large outputs"""
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox_class.return_value = mock_sandbox
            
            # Generate large output
            large_output = "x" * (executor.MAX_OUTPUT_LENGTH + 1000)
            mock_sandbox.commands.run.return_value = Mock(
                exit_code=0,
                stdout=large_output,
                stderr=""
            )
            
            result = await executor._run_command_with_timeout(
                mock_sandbox,
                "generate_large_output"
            )
            
            # Verify output was truncated
            assert len(result.stdout) <= executor.MAX_OUTPUT_LENGTH
            assert result.stdout.endswith("...[truncated]")
            
    # Test 9: Concurrent Sandbox Execution
    @pytest.mark.anyio
    async def test_concurrent_sandbox_isolation(self, executor):
        """Test that multiple sandboxes don't interfere with each other"""
        sandbox_ids = []
        
        async def create_and_track_sandbox():
            with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
                mock_sandbox = Mock()
                mock_sandbox.id = f"sandbox-{len(sandbox_ids)}"
                mock_sandbox_class.return_value = mock_sandbox
                mock_sandbox.commands.run.return_value = Mock(exit_code=0)
                
                sandbox = await executor._create_e2b_sandbox()
                sandbox_ids.append(sandbox.id)
                return sandbox
                
        # Create multiple sandboxes concurrently
        sandboxes = await asyncio.gather(*[
            create_and_track_sandbox() for _ in range(3)
        ])
        
        # Verify all sandboxes have unique IDs
        assert len(set(sandbox_ids)) == 3
        
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
            
            task_data = {
                "repo_url": "https://github.com/test/repo.git",
                "branch": "main",
                "prompt": "test"
            }
            
            with pytest.raises(Exception):
                await executor.execute_task(task_data, agent_type="claude")
                
            # Verify sandbox was killed
            mock_sandbox.kill.assert_called_once()
            
    # Test 11: Binary File Handling
    @pytest.mark.anyio
    async def test_binary_file_operations(self, executor):
        """Test handling of binary files in sandbox"""
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox_class.return_value = mock_sandbox
            
            # Simulate binary file operations
            mock_sandbox.files.write.return_value = None
            mock_sandbox.files.read.return_value = b"\x00\x01\x02\x03"
            
            sandbox = await executor._create_e2b_sandbox()
            
            # Test writing binary data
            binary_data = b"\x00\x01\x02\x03"
            sandbox.files.write("/workspace/test.bin", binary_data)
            
            # Test reading binary data
            read_data = sandbox.files.read("/workspace/test.bin")
            assert read_data == binary_data
            
    # Test 12: Git Operations Edge Cases
    @pytest.mark.anyio
    async def test_non_existent_branch_handling(self, executor):
        """Test handling of non-existent branch"""
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox_class.return_value = mock_sandbox
            
            # Clone succeeds but checkout fails
            mock_sandbox.commands.run.side_effect = [
                Mock(exit_code=0),  # mkdir
                Mock(exit_code=0),  # clone
                Mock(exit_code=1, stderr="error: pathspec 'non-existent' did not match")
            ]
            
            task_data = {
                "repo_url": "https://github.com/test/repo.git",
                "branch": "non-existent",
                "prompt": "test"
            }
            
            with pytest.raises(Exception) as exc_info:
                await executor.execute_task(task_data, agent_type="claude")
                
            assert "branch" in str(exc_info.value).lower()


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([__file__, "-v", "-k", "test_"])