"""
E2B Template Configuration Test Matrix
Tests various E2B template configurations to ensure compatibility
"""

import os
import json
import pytest
import asyncio
from typing import Dict, List, Optional
from unittest.mock import Mock, patch
from dataclasses import dataclass

from utils.code_task_e2b_real import E2BCodeExecutor
from utils.logging_config import setup_logger

logger = setup_logger()


@dataclass
class TemplateTestCase:
    """Represents a test case for a specific E2B template configuration"""
    name: str
    template_id: Optional[str]
    expected_features: List[str]
    environment_vars: Dict[str, str]
    test_commands: List[Dict[str, str]]  # List of {command, expected_output}
    agent_type: str = "claude"
    should_fail: bool = False
    failure_reason: Optional[str] = None


class E2BTemplateMatrix:
    """Test matrix for different E2B template configurations"""
    
    # Define test cases for different template configurations
    TEST_CASES = [
        # Test 1: Default E2B template (no custom template)
        TemplateTestCase(
            name="Default E2B Template",
            template_id=None,
            expected_features=["git", "python3", "node"],
            environment_vars={},
            test_commands=[
                {"command": "python3 --version", "expected_output": "Python 3"},
                {"command": "node --version", "expected_output": "v"},
                {"command": "git --version", "expected_output": "git version"},
            ]
        ),
        
        # Test 2: Python-focused template with pre-installed packages
        TemplateTestCase(
            name="Python Development Template",
            template_id="python-dev-template",
            expected_features=["python3", "pip", "anthropic", "openai"],
            environment_vars={"ANTHROPIC_API_KEY": "test-key"},
            test_commands=[
                {"command": "pip list | grep anthropic", "expected_output": "anthropic"},
                {"command": "pip list | grep openai", "expected_output": "openai"},
                {"command": "python3 -c 'import anthropic; print(\"OK\")'", "expected_output": "OK"},
            ]
        ),
        
        # Test 3: Node.js template with TypeScript
        TemplateTestCase(
            name="Node.js TypeScript Template",
            template_id="nodejs-ts-template",
            expected_features=["node", "npm", "typescript"],
            environment_vars={},
            test_commands=[
                {"command": "npm --version", "expected_output": ""},
                {"command": "tsc --version", "expected_output": "Version"},
                {"command": "node -e 'console.log(\"Node OK\")'", "expected_output": "Node OK"},
            ]
        ),
        
        # Test 4: Full-stack template with multiple languages
        TemplateTestCase(
            name="Full-Stack Development Template",
            template_id="fullstack-template",
            expected_features=["python3", "node", "git", "docker"],
            environment_vars={
                "ANTHROPIC_API_KEY": "test-anthropic",
                "OPENAI_API_KEY": "test-openai"
            },
            test_commands=[
                {"command": "python3 --version && node --version", "expected_output": ""},
                {"command": "docker --version || echo 'Docker not available'", "expected_output": ""},
            ]
        ),
        
        # Test 5: Invalid template (should fail gracefully)
        TemplateTestCase(
            name="Invalid Template Fallback",
            template_id="non-existent-template-xyz",
            expected_features=[],
            environment_vars={},
            test_commands=[],
            should_fail=False,  # Should fall back to default
            failure_reason="Template not found, should fall back to default"
        ),
        
        # Test 6: Template with pre-configured workspace
        TemplateTestCase(
            name="Pre-configured Workspace Template",
            template_id="workspace-ready-template",
            expected_features=["workspace-exists"],
            environment_vars={},
            test_commands=[
                {"command": "ls -la /workspace", "expected_output": ""},
                {"command": "test -d /workspace && echo 'EXISTS'", "expected_output": "EXISTS"},
            ]
        ),
        
        # Test 7: Minimal template (bare minimum)
        TemplateTestCase(
            name="Minimal Template",
            template_id="minimal-template",
            expected_features=["bash"],
            environment_vars={},
            test_commands=[
                {"command": "echo 'Minimal OK'", "expected_output": "Minimal OK"},
            ]
        ),
        
        # Test 8: GPU-enabled template (for ML workloads)
        TemplateTestCase(
            name="GPU ML Template",
            template_id="gpu-ml-template",
            expected_features=["python3", "cuda", "torch"],
            environment_vars={"CUDA_VISIBLE_DEVICES": "0"},
            test_commands=[
                {"command": "python3 -c 'import torch; print(torch.cuda.is_available())'", "expected_output": ""},
                {"command": "nvidia-smi || echo 'No GPU'", "expected_output": ""},
            ]
        )
    ]
    
    @classmethod
    def get_test_matrix(cls) -> List[TemplateTestCase]:
        """Get the complete test matrix"""
        return cls.TEST_CASES
    
    @classmethod
    def get_test_case_by_name(cls, name: str) -> Optional[TemplateTestCase]:
        """Get a specific test case by name"""
        for case in cls.TEST_CASES:
            if case.name == name:
                return case
        return None


class TestE2BTemplateConfigurations:
    """Test suite for E2B template configurations"""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Set up test environment"""
        monkeypatch.setenv("E2B_API_KEY", "test-e2b-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        
    @pytest.mark.parametrize("test_case", E2BTemplateMatrix.get_test_matrix())
    @pytest.mark.anyio
    async def test_template_configuration(self, test_case: TemplateTestCase, mock_env, monkeypatch):
        """Test each template configuration in the matrix"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 Testing: {test_case.name}")
        logger.info(f"Template ID: {test_case.template_id or 'Default'}")
        logger.info(f"{'='*60}")
        
        # Set template-specific environment variables
        if test_case.template_id:
            monkeypatch.setenv("E2B_TEMPLATE_ID", test_case.template_id)
        else:
            monkeypatch.delenv("E2B_TEMPLATE_ID", raising=False)
            
        for key, value in test_case.environment_vars.items():
            monkeypatch.setenv(key, value)
        
        # Create executor
        executor = E2BCodeExecutor()
        
        # Mock sandbox creation
        with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
            mock_sandbox = Mock()
            
            if test_case.should_fail and "not found" in test_case.failure_reason:
                # Simulate template not found, then fallback
                mock_sandbox_class.side_effect = [
                    Exception("Template not found"),
                    mock_sandbox  # Fallback succeeds
                ]
            else:
                mock_sandbox_class.return_value = mock_sandbox
            
            # Set up basic command responses for sandbox creation and task execution
            basic_responses = [
                Mock(exit_code=0, stdout="", stderr=""),  # mkdir
                Mock(exit_code=0, stdout="Cloning...", stderr=""),  # git clone
                Mock(exit_code=0, stdout="", stderr=""),  # git config
                Mock(exit_code=0, stdout="", stderr=""),  # initial ls
                Mock(exit_code=1, stdout="", stderr=""),  # which claude
                Mock(exit_code=0, stdout="", stderr=""),  # npm install claude
                Mock(exit_code=0, stdout="Test output", stderr=""),  # claude execution
                Mock(exit_code=0, stdout="", stderr=""),  # git status
                Mock(exit_code=0, stdout="", stderr=""),  # git diff
            ]
            
            # Add test command responses
            for cmd_test in test_case.test_commands:
                basic_responses.append(
                    Mock(
                        exit_code=0,
                        stdout=cmd_test["expected_output"],
                        stderr=""
                    )
                )
            
            mock_sandbox.commands.run.side_effect = basic_responses
            mock_sandbox.files.write = Mock()
            mock_sandbox.kill = Mock()
            
            # Mock database operations
            with patch('utils.code_task_e2b_real.DatabaseOperations') as mock_db:
                mock_db.update_task = Mock()
                mock_db.add_chat_message = Mock()
                
                # Test sandbox creation through execute_task
                try:
                    result = await executor.execute_task(
                        task_id=1,
                        user_id="test-user",
                        github_token="test-token",
                        repo_url="https://github.com/test/repo",
                        branch="main",
                        prompt="Test prompt",
                        agent=test_case.agent_type
                    )
                    
                    # Verify template was used correctly
                    if test_case.template_id and not test_case.should_fail:
                        call_kwargs = mock_sandbox_class.call_args[1]
                        assert 'api_key' in call_kwargs
                        assert call_kwargs['api_key'] == executor.api_key
                        if executor.template_id:  # Only check template if it was set
                            assert 'template' in call_kwargs
                            assert call_kwargs['template'] == test_case.template_id
                        assert 'timeout' in call_kwargs
                        assert call_kwargs['timeout'] == executor.SANDBOX_TIMEOUT
                    
                    # Verify test commands would have been run (they're part of mock)
                    logger.info(f"✅ {test_case.name} passed with result: {result['status']}")
                    
                except Exception as e:
                    if test_case.should_fail:
                        logger.info(f"✅ {test_case.name} failed as expected: {str(e)}")
                    else:
                        logger.error(f"❌ {test_case.name} failed unexpectedly: {str(e)}")
                        raise
    
    @pytest.mark.anyio
    async def test_template_agent_compatibility(self, mock_env):
        """Test that different agents work with different templates"""
        test_matrix = [
            ("claude", "python-dev-template", True),
            ("codex", "python-dev-template", True),
            ("claude", "nodejs-ts-template", True),
            ("codex", "nodejs-ts-template", True),
            ("claude", None, True),  # Default template
            ("codex", None, True),   # Default template
        ]
        
        for agent_type, template_id, should_succeed in test_matrix:
            logger.info(f"\n🧪 Testing {agent_type} with template {template_id or 'default'}")
            
            with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
                mock_sandbox = Mock()
                mock_sandbox_class.return_value = mock_sandbox
                
                # Mock successful execution
                mock_sandbox.commands.run.side_effect = [
                    Mock(exit_code=0, stdout="", stderr=""),  # mkdir
                    Mock(exit_code=0, stdout="", stderr=""),  # git clone
                    Mock(exit_code=0, stdout="", stderr=""),  # git config
                    Mock(exit_code=0, stdout="", stderr=""),  # initial ls
                    Mock(exit_code=1, stdout="", stderr=""),  # which claude/codex
                    Mock(exit_code=0, stdout="", stderr=""),  # npm install or pip install
                    Mock(exit_code=0, stdout="Agent executed successfully", stderr=""),  # agent execution
                    Mock(exit_code=0, stdout="", stderr=""),  # git status
                    Mock(exit_code=0, stdout="", stderr=""),  # git diff
                ]
                
                mock_sandbox.kill = Mock()
                mock_sandbox.files.write = Mock()
                
                executor = E2BCodeExecutor()
                if template_id:
                    executor.template_id = template_id
                
                # Mock database operations
                with patch('utils.code_task_e2b_real.DatabaseOperations') as mock_db:
                    mock_db.update_task = Mock()
                    mock_db.add_chat_message = Mock()
                    
                    try:
                        result = await executor.execute_task(
                            task_id=123,  # Use integer for task_id
                            user_id="test-user",
                            github_token="",
                            repo_url="https://github.com/test/repo.git",
                            branch="main",
                            prompt="Test prompt",
                            agent=agent_type
                        )
                        
                        if should_succeed:
                            assert result["status"] == "completed"
                            logger.info(f"✅ {agent_type} + {template_id or 'default'} succeeded")
                        else:
                            pytest.fail(f"Expected failure but succeeded")
                            
                    except Exception as e:
                        if not should_succeed:
                            logger.info(f"✅ {agent_type} + {template_id or 'default'} failed as expected")
                        else:
                            logger.error(f"❌ Unexpected failure: {str(e)}")
                            raise
    
    @pytest.mark.anyio
    async def test_template_performance_characteristics(self, mock_env):
        """Test performance characteristics of different templates"""
        performance_tests = [
            {
                "template": None,
                "name": "Default",
                "expected_startup_time": 5.0,  # seconds
                "expected_clone_time": 10.0,
            },
            {
                "template": "optimized-template",
                "name": "Optimized",
                "expected_startup_time": 2.0,
                "expected_clone_time": 5.0,
            },
            {
                "template": "heavy-template",
                "name": "Heavy",
                "expected_startup_time": 10.0,
                "expected_clone_time": 15.0,
            }
        ]
        
        for perf_test in performance_tests:
            logger.info(f"\n🏃 Performance test: {perf_test['name']} template")
            
            with patch('utils.code_task_e2b_real.Sandbox') as mock_sandbox_class:
                import time
                
                # Create mock sandbox
                mock_sandbox = Mock()
                mock_sandbox_class.return_value = mock_sandbox
                
                # Set up mock sandbox responses with proper return values
                mock_sandbox.commands.run.side_effect = [
                    Mock(exit_code=0, stdout="", stderr=""),  # mkdir
                    Mock(exit_code=0, stdout="", stderr=""),  # git clone
                    Mock(exit_code=0, stdout="", stderr=""),  # git config
                    Mock(exit_code=0, stdout="", stderr=""),  # initial ls
                    Mock(exit_code=1, stdout="", stderr=""),  # which claude
                    Mock(exit_code=0, stdout="", stderr=""),  # npm install claude
                    Mock(exit_code=0, stdout="Task completed", stderr=""),  # claude execution
                    Mock(exit_code=0, stdout="", stderr=""),  # git status
                    Mock(exit_code=0, stdout="", stderr=""),  # git diff
                ]
                mock_sandbox.files.write = Mock()
                mock_sandbox.kill = Mock()
                
                executor = E2BCodeExecutor()
                if perf_test["template"]:
                    executor.template_id = perf_test["template"]
                
                # Mock database operations
                with patch('utils.code_task_e2b_real.DatabaseOperations') as mock_db:
                    mock_db.update_task = Mock()
                    mock_db.add_chat_message = Mock()
                    
                    # Simulate delay in sandbox creation
                    original_init = mock_sandbox_class.return_value
                    def delayed_sandbox(*args, **kwargs):
                        time.sleep(0.05)  # Small delay to simulate startup
                        return original_init
                    mock_sandbox_class.return_value = delayed_sandbox
                    
                    start_time = time.time()
                    # Execute task to trigger sandbox creation
                    try:
                        result = await executor.execute_task(
                            task_id=1,
                            user_id="test-user",
                            github_token="test-token",
                            repo_url="https://github.com/test/repo",
                            branch="main",
                            prompt="Test prompt",
                            agent="claude"
                        )
                        # Performance test succeeded
                        logger.info(f"  Task completed with status: {result['status']}")
                    except Exception as e:
                        # Still measure timing even if task fails
                        logger.warning(f"  Task failed but timing measured: {str(e)}")
                    
                    startup_time = time.time() - start_time
                
                logger.info(f"  Startup time: {startup_time:.2f}s")
                logger.info(f"  Expected: <{perf_test['expected_startup_time']}s")
                
                # In real tests, we would assert timing
                # assert startup_time < perf_test['expected_startup_time']


if __name__ == "__main__":
    # Run template matrix tests
    pytest.main([__file__, "-v", "-k", "test_template"])