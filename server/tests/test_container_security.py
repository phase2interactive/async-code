"""Unit tests for container security configuration."""
import unittest
from unittest.mock import Mock, patch, MagicMock
import docker.types
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock database module before importing code_task_v2
sys.modules['database'] = MagicMock()

from utils.code_task_v2 import _run_ai_code_task_v2_internal


class TestContainerSecurity(unittest.TestCase):
    """Test suite for container security configurations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.task_id = 123
        self.user_id = "test-user"
        self.github_token = "test-token"
        
        # Mock task data
        self.mock_task = {
            'id': self.task_id,
            'agent': 'claude',
            'repo_url': 'https://github.com/test/repo.git',
            'target_branch': 'main',
            'chat_messages': [{'role': 'user', 'content': 'Test prompt'}]
        }
    
    @patch('utils.code_task_v2.docker_client')
    @patch('utils.code_task_v2.DatabaseOperations')
    @patch('utils.code_task_v2.os.makedirs')
    @patch('utils.code_task_v2.os.chown')
    def test_container_security_options(self, mock_chown, mock_makedirs, mock_db, mock_docker):
        """Test that containers are created with proper security options."""
        # Setup mocks
        mock_db.get_task_by_id.return_value = self.mock_task
        mock_container = Mock()
        mock_container.id = 'test-container-id'
        mock_container.status = 'exited'
        mock_container.logs.return_value = b'COMMIT_HASH=test123\n=== PATCH START ===\n=== PATCH END ==='
        mock_container.wait.return_value = {'StatusCode': 0}
        
        # Capture container creation kwargs
        container_kwargs_capture = {}
        def capture_kwargs(**kwargs):
            container_kwargs_capture.update(kwargs)
            return mock_container
        
        mock_docker.containers.run.side_effect = capture_kwargs
        
        # Run the function
        _run_ai_code_task_v2_internal(self.task_id, self.user_id, self.github_token)
        
        # Verify security options
        self.assertIn('security_opt', container_kwargs_capture)
        self.assertIn('no-new-privileges=true', container_kwargs_capture['security_opt'])
        
        # Verify user mapping
        self.assertEqual(container_kwargs_capture['user'], '1000:1000')
        
        # Verify privileged mode is NOT set
        self.assertNotIn('privileged', container_kwargs_capture)
        
        # Verify host PID namespace is NOT used
        self.assertNotIn('pid_mode', container_kwargs_capture)
        
        # Verify no dangerous capabilities
        self.assertNotIn('cap_add', container_kwargs_capture)
    
    @patch('utils.code_task_v2.docker_client')
    @patch('utils.code_task_v2.DatabaseOperations')
    @patch('utils.code_task_v2.os.makedirs')
    @patch('utils.code_task_v2.os.chown')
    def test_workspace_permissions(self, mock_chown, mock_makedirs, mock_db, mock_docker):
        """Test that workspace is created with proper permissions."""
        # Setup mocks
        mock_db.get_task_by_id.return_value = self.mock_task
        mock_container = Mock()
        mock_container.id = 'test-container-id'
        mock_container.status = 'exited'
        mock_container.logs.return_value = b'COMMIT_HASH=test123'
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_docker.containers.run.return_value = mock_container
        
        # Run the function
        _run_ai_code_task_v2_internal(self.task_id, self.user_id, self.github_token)
        
        # Verify workspace creation
        expected_workspace = f'/tmp/ai-workspace-{self.task_id}'
        mock_makedirs.assert_called_with(expected_workspace, exist_ok=True)
        
        # Verify ownership set to UID 1000
        mock_chown.assert_called_with(expected_workspace, 1000, 1000)
    
    @patch('utils.code_task_v2.docker_client')
    @patch('utils.code_task_v2.DatabaseOperations')
    def test_no_sandbox_bypass_env_vars(self, mock_db, mock_docker):
        """Test that sandbox bypass environment variables are not set."""
        # Setup mocks
        mock_db.get_task_by_id.return_value = {**self.mock_task, 'agent': 'codex'}
        mock_container = Mock()
        mock_container.id = 'test-container-id'
        mock_container.status = 'exited'
        mock_container.logs.return_value = b'COMMIT_HASH=test123'
        mock_container.wait.return_value = {'StatusCode': 0}
        
        # Capture environment variables
        env_vars_capture = {}
        def capture_kwargs(**kwargs):
            env_vars_capture.update(kwargs.get('environment', {}))
            return mock_container
        
        mock_docker.containers.run.side_effect = capture_kwargs
        
        # Run the function
        _run_ai_code_task_v2_internal(self.task_id, self.user_id, self.github_token)
        
        # Verify dangerous env vars are NOT set
        self.assertNotIn('CODEX_UNSAFE_ALLOW_NO_SANDBOX', env_vars_capture)
        self.assertNotIn('CODEX_DISABLE_SANDBOX', env_vars_capture)
        self.assertNotIn('CODEX_NO_SANDBOX', env_vars_capture)
        
        # Verify safe env vars ARE set
        self.assertIn('CODEX_QUIET_MODE', env_vars_capture)
        self.assertEqual(env_vars_capture['CODEX_QUIET_MODE'], '1')
    
    @patch('utils.code_task_v2.docker_client')
    @patch('utils.code_task_v2.DatabaseOperations')
    def test_volume_mounting(self, mock_db, mock_docker):
        """Test that volumes are mounted with proper permissions."""
        # Setup mocks
        mock_db.get_task_by_id.return_value = self.mock_task
        mock_container = Mock()
        mock_container.id = 'test-container-id'
        mock_container.status = 'exited'
        mock_container.logs.return_value = b'COMMIT_HASH=test123'
        mock_container.wait.return_value = {'StatusCode': 0}
        
        # Capture container kwargs
        container_kwargs_capture = {}
        def capture_kwargs(**kwargs):
            container_kwargs_capture.update(kwargs)
            return mock_container
        
        mock_docker.containers.run.side_effect = capture_kwargs
        
        # Run the function
        _run_ai_code_task_v2_internal(self.task_id, self.user_id, self.github_token)
        
        # Verify volume mounting
        self.assertIn('volumes', container_kwargs_capture)
        expected_workspace = f'/tmp/ai-workspace-{self.task_id}'
        self.assertIn(expected_workspace, container_kwargs_capture['volumes'])
        
        # Verify volume mode is read-write
        volume_config = container_kwargs_capture['volumes'][expected_workspace]
        self.assertEqual(volume_config['mode'], 'rw')


if __name__ == '__main__':
    unittest.main()