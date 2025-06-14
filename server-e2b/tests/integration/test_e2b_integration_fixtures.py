"""
E2B Integration Test Fixtures
Provides reusable fixtures and test utilities that mirror production code paths
"""

import os
import json
import asyncio
import tempfile
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from unittest.mock import Mock, patch

import pytest
from e2b import Sandbox

from utils.code_task_e2b_real import E2BCodeExecutor
from utils.database import DatabaseManager
from utils.logging_config import setup_logger

logger = setup_logger()


class E2BTestFixtures:
    """Reusable test fixtures for E2B integration testing"""
    
    @staticmethod
    def create_mock_task_data(
        repo_url: str = "https://github.com/test/repo.git",
        branch: str = "main",
        prompt: str = "Test prompt",
        github_token: Optional[str] = None,
        additional_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create mock task data matching production format"""
        task_data = {
            "id": "test-task-123",
            "repo_url": repo_url,
            "branch": branch,
            "prompt": prompt,
            "user_id": "test-user",
            "created_at": "2024-01-01T00:00:00Z",
            "status": "pending"
        }
        
        if github_token:
            task_data["github_token"] = github_token
            
        if additional_context:
            task_data.update(additional_context)
            
        return task_data
    
    @staticmethod
    async def create_real_e2b_sandbox(
        api_key: Optional[str] = None,
        template_id: Optional[str] = None,
        timeout: int = 300
    ) -> Sandbox:
        """Create a real E2B sandbox for integration testing"""
        if not api_key:
            api_key = os.getenv("E2B_API_KEY")
            if not api_key:
                pytest.skip("E2B_API_KEY not set")
                
        kwargs = {
            "api_key": api_key,
            "timeout": timeout
        }
        
        if template_id:
            kwargs["template"] = template_id
            
        return Sandbox(**kwargs)
    
    @staticmethod
    @asynccontextmanager
    async def production_like_executor(
        mock_database: bool = True,
        custom_env: Optional[Dict[str, str]] = None
    ):
        """Create an E2B executor with production-like configuration"""
        # Set up environment
        env_vars = {
            "E2B_API_KEY": os.getenv("E2B_API_KEY", "test-api-key"),
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", "test-anthropic-key"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "test-openai-key"),
            "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", "test-github-token"),
            "SUPABASE_URL": os.getenv("SUPABASE_URL", "https://test.supabase.co"),
            "SUPABASE_KEY": os.getenv("SUPABASE_KEY", "test-supabase-key")
        }
        
        if custom_env:
            env_vars.update(custom_env)
            
        # Mock or real database
        if mock_database:
            with patch('utils.database.DatabaseManager') as mock_db:
                mock_db_instance = Mock()
                mock_db.return_value = mock_db_instance
                
                # Mock database methods
                mock_db_instance.update_task_status = AsyncMock()
                mock_db_instance.add_chat_message = AsyncMock()
                mock_db_instance.update_task_result = AsyncMock()
                
                with patch.dict(os.environ, env_vars):
                    executor = E2BCodeExecutor()
                    executor.db = mock_db_instance
                    yield executor
        else:
            with patch.dict(os.environ, env_vars):
                executor = E2BCodeExecutor()
                yield executor


class TestE2BIntegrationWithFixtures:
    """Integration tests using production-like fixtures"""
    
    @pytest.mark.asyncio
    async def test_full_task_execution_flow(self):
        """Test complete task execution flow matching production"""
        async with E2BTestFixtures.production_like_executor() as executor:
            # Create task data
            task_data = E2BTestFixtures.create_mock_task_data(
                repo_url="https://github.com/octocat/Hello-World.git",
                prompt="List all files in the repository"
            )
            
            # Mock sandbox creation and execution
            with patch.object(executor, '_create_e2b_sandbox') as mock_create:
                mock_sandbox = Mock()
                mock_create.return_value = mock_sandbox
                
                # Mock successful execution
                mock_sandbox.commands.run.side_effect = [
                    Mock(exit_code=0, stdout="", stderr=""),  # mkdir
                    Mock(exit_code=0, stdout="Cloning...", stderr=""),  # clone
                    Mock(exit_code=0, stdout="README\nLICENSE", stderr="")  # agent
                ]
                
                mock_sandbox.kill = Mock()
                
                # Execute task
                result = await executor.execute_task(task_data, agent_type="claude")
                
                # Verify production-like flow
                assert result["status"] == "completed"
                assert "README" in result["agent_output"]
                
                # Verify database interactions
                executor.db.update_task_status.assert_called()
                executor.db.add_chat_message.assert_called()
                executor.db.update_task_result.assert_called()
                
                # Verify sandbox cleanup
                mock_sandbox.kill.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_with_database_updates(self):
        """Test error handling updates database correctly"""
        async with E2BTestFixtures.production_like_executor() as executor:
            task_data = E2BTestFixtures.create_mock_task_data()
            
            with patch.object(executor, '_create_e2b_sandbox') as mock_create:
                # Simulate sandbox creation failure
                mock_create.side_effect = Exception("Sandbox creation failed")
                
                # Execute should handle error gracefully
                result = await executor.execute_task(task_data, agent_type="claude")
                
                # Verify error handling
                assert result["status"] == "failed"
                assert "error" in result
                assert "Sandbox creation failed" in result["error"]
                
                # Verify database was updated with error
                executor.db.update_task_status.assert_any_call(
                    task_data["id"],
                    "failed",
                    error=pytest.StringContaining("Sandbox creation failed")
                )
    
    @pytest.mark.asyncio
    async def test_agent_switching_production_flow(self):
        """Test switching between Claude and Codex agents"""
        async with E2BTestFixtures.production_like_executor() as executor:
            task_data = E2BTestFixtures.create_mock_task_data()
            
            # Test Claude agent
            with patch.object(executor, '_execute_claude_agent') as mock_claude:
                mock_claude.return_value = "Claude output"
                
                with patch.object(executor, '_create_e2b_sandbox'):
                    with patch.object(executor, '_clone_repository'):
                        result = await executor.execute_task(task_data, agent_type="claude")
                        
                mock_claude.assert_called_once()
                assert result["agent_output"] == "Claude output"
            
            # Test Codex agent
            with patch.object(executor, '_execute_codex_agent') as mock_codex:
                mock_codex.return_value = "Codex output"
                
                with patch.object(executor, '_create_e2b_sandbox'):
                    with patch.object(executor, '_clone_repository'):
                        result = await executor.execute_task(task_data, agent_type="codex")
                        
                mock_codex.assert_called_once()
                assert result["agent_output"] == "Codex output"
    
    @pytest.mark.asyncio
    async def test_git_operations_with_patches(self):
        """Test git patch generation matching production"""
        async with E2BTestFixtures.production_like_executor() as executor:
            task_data = E2BTestFixtures.create_mock_task_data(
                prompt="Create a new file called test.txt"
            )
            
            with patch.object(executor, '_create_e2b_sandbox') as mock_create:
                mock_sandbox = Mock()
                mock_create.return_value = mock_sandbox
                
                # Mock git operations
                mock_sandbox.commands.run.side_effect = [
                    Mock(exit_code=0),  # mkdir
                    Mock(exit_code=0),  # clone
                    Mock(exit_code=0, stdout="File created"),  # agent execution
                    Mock(exit_code=0, stdout=""),  # git add
                    Mock(exit_code=0, stdout=""),  # git commit
                    Mock(exit_code=0, stdout="diff --git a/test.txt...")  # git format-patch
                ]
                
                mock_sandbox.kill = Mock()
                
                result = await executor.execute_task(task_data, agent_type="claude")
                
                # Verify patch was generated
                assert result["status"] == "completed"
                assert "patches" in result
                assert result["patches"]
                
                # Verify git commands were called
                calls = [call[0][0] for call in mock_sandbox.commands.run.call_args_list]
                assert any("git add" in call for call in calls)
                assert any("git commit" in call for call in calls)
                assert any("git format-patch" in call for call in calls)
    
    @pytest.mark.asyncio
    async def test_environment_variable_injection(self):
        """Test environment variables are properly injected into sandbox"""
        custom_env = {
            "CUSTOM_VAR": "custom_value",
            "GITHUB_TOKEN": "real-github-token"
        }
        
        async with E2BTestFixtures.production_like_executor(custom_env=custom_env) as executor:
            # Verify executor has correct environment
            assert executor.github_token == "real-github-token"
            
            with patch('e2b.Sandbox') as mock_sandbox_class:
                mock_sandbox = Mock()
                mock_sandbox_class.return_value = mock_sandbox
                
                sandbox = await executor._create_e2b_sandbox()
                
                # Verify sandbox creation included environment setup
                assert mock_sandbox_class.called
    
    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self):
        """Test multiple tasks can execute concurrently"""
        async with E2BTestFixtures.production_like_executor() as executor:
            tasks = [
                E2BTestFixtures.create_mock_task_data(prompt=f"Task {i}")
                for i in range(3)
            ]
            
            with patch.object(executor, '_create_e2b_sandbox') as mock_create:
                # Create different sandboxes for each task
                mock_sandboxes = []
                for i in range(3):
                    mock_sandbox = Mock()
                    mock_sandbox.id = f"sandbox-{i}"
                    mock_sandbox.commands.run.return_value = Mock(
                        exit_code=0,
                        stdout=f"Output {i}"
                    )
                    mock_sandbox.kill = Mock()
                    mock_sandboxes.append(mock_sandbox)
                
                mock_create.side_effect = mock_sandboxes
                
                # Execute tasks concurrently
                results = await asyncio.gather(*[
                    executor.execute_task(task, agent_type="claude")
                    for task in tasks
                ])
                
                # Verify all tasks completed
                assert len(results) == 3
                assert all(r["status"] == "completed" for r in results)
                
                # Verify each sandbox was killed
                for sandbox in mock_sandboxes:
                    sandbox.kill.assert_called_once()


class TestE2BRealIntegration:
    """Real integration tests that require actual E2B API access"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_sandbox_creation(self):
        """Test creating a real E2B sandbox"""
        if not os.getenv("E2B_API_KEY"):
            pytest.skip("E2B_API_KEY required for real integration tests")
            
        sandbox = await E2BTestFixtures.create_real_e2b_sandbox()
        
        try:
            # Test basic command execution
            result = sandbox.commands.run("echo 'Hello from E2B'")
            assert result.exit_code == 0
            assert "Hello from E2B" in result.stdout
            
            # Test workspace directory
            mkdir_result = sandbox.commands.run("mkdir -p /workspace")
            assert mkdir_result.exit_code == 0
            
            ls_result = sandbox.commands.run("ls -la /workspace")
            assert ls_result.exit_code == 0
            
        finally:
            sandbox.kill()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_git_clone(self):
        """Test real git clone operation in E2B"""
        if not os.getenv("E2B_API_KEY"):
            pytest.skip("E2B_API_KEY required for real integration tests")
            
        async with E2BTestFixtures.production_like_executor(mock_database=True) as executor:
            sandbox = await executor._create_e2b_sandbox()
            
            try:
                task_data = E2BTestFixtures.create_mock_task_data(
                    repo_url="https://github.com/octocat/Hello-World.git"
                )
                
                await executor._clone_repository(sandbox, task_data)
                
                # Verify clone succeeded
                ls_result = sandbox.commands.run("ls -la /workspace/repo")
                assert ls_result.exit_code == 0
                assert "README" in ls_result.stdout
                
            finally:
                sandbox.kill()


if __name__ == "__main__":
    # Run only unit tests by default
    pytest.main([__file__, "-v", "-m", "not integration"])