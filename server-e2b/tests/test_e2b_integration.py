"""
Integration tests for E2B sandbox functionality with proper .env loading
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Import after loading env to ensure proper configuration
from utils.code_task_e2b_real import E2BCodeExecutor
from database import DatabaseOperations


class TestE2BSandboxCreation:
    """Test E2B sandbox creation and configuration"""
    
    @pytest.fixture
    def mock_db_operations(self):
        """Mock database operations"""
        with patch.object(DatabaseOperations, 'update_task') as mock_update, \
             patch.object(DatabaseOperations, 'add_chat_message') as mock_add_msg, \
             patch.object(DatabaseOperations, 'get_task_by_id') as mock_get_task:
            
            mock_get_task.return_value = {
                'id': 1,
                'user_id': 'test-user',
                'repo_url': 'https://github.com/test/repo',
                'target_branch': 'main',
                'agent': 'claude',
                'chat_messages': [{'role': 'user', 'content': 'Test prompt'}]
            }
            
            yield {
                'update_task': mock_update,
                'add_chat_message': mock_add_msg,
                'get_task_by_id': mock_get_task
            }
    
    def test_env_variables_loaded(self):
        """Test that environment variables are properly loaded"""
        # Check critical E2B environment variable
        e2b_api_key = os.getenv('E2B_API_KEY')
        print(f"E2B_API_KEY loaded: {'Yes' if e2b_api_key else 'No'}")
        print(f"E2B_API_KEY value: {e2b_api_key[:10]}..." if e2b_api_key else "E2B_API_KEY not set")
        
        # Check other important env vars
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        print(f"ANTHROPIC_API_KEY loaded: {'Yes' if anthropic_key else 'No'}")
        
        openai_key = os.getenv('OPENAI_API_KEY')
        print(f"OPENAI_API_KEY loaded: {'Yes' if openai_key else 'No'}")
    
    @pytest.mark.asyncio
    async def test_sandbox_create_attribute_error(self, mock_db_operations):
        """Test that captures the current Sandbox.create attribute error"""
        executor = E2BCodeExecutor()
        
        # This should fail with the current error
        with pytest.raises(Exception) as exc_info:
            await executor.execute_task(
                task_id=1,
                user_id='test-user',
                github_token='test-token',
                repo_url='https://github.com/test/repo',
                branch='main',
                prompt='Test prompt',
                agent='claude'
            )
        
        # Verify we get the expected error
        assert "Sandbox" in str(exc_info.value)
        assert "create" in str(exc_info.value)
        print(f"Captured error: {exc_info.value}")
    
    @pytest.mark.asyncio
    async def test_e2b_import_and_sandbox_creation(self):
        """Test E2B import and Sandbox class availability"""
        try:
            # Test importing E2B
            from e2b import Sandbox
            print(f"Successfully imported Sandbox from e2b")
            
            # Check what attributes Sandbox has
            print(f"Sandbox class attributes: {[attr for attr in dir(Sandbox) if not attr.startswith('_')]}")
            
            # Check if create method exists
            has_create = hasattr(Sandbox, 'create')
            print(f"Sandbox.create exists: {has_create}")
            
            # If create doesn't exist, check for constructor or other initialization methods
            if not has_create:
                # Check if we can instantiate directly
                has_init = hasattr(Sandbox, '__init__')
                print(f"Sandbox.__init__ exists: {has_init}")
                
                # List all callable methods
                callable_methods = [attr for attr in dir(Sandbox) if callable(getattr(Sandbox, attr)) and not attr.startswith('_')]
                print(f"Callable methods on Sandbox: {callable_methods}")
                
        except ImportError as e:
            print(f"Failed to import E2B: {e}")
            pytest.fail(f"E2B import failed: {e}")
    
    @pytest.mark.asyncio
    async def test_e2b_sandbox_initialization_methods(self):
        """Test different ways to initialize E2B sandbox"""
        try:
            from e2b import Sandbox
            
            # Test 1: Try direct instantiation (recommended as per deprecation warning)
            try:
                # Check if Sandbox can be instantiated directly
                sandbox = Sandbox()
                print(f"Direct instantiation worked: {type(sandbox)}")
                # Check if it's async
                if hasattr(sandbox, '__aenter__'):
                    print("Sandbox has async context manager support")
                # Close if needed
                if hasattr(sandbox, 'close'):
                    await sandbox.close()
                    print("Successfully closed sandbox")
            except Exception as e:
                print(f"Direct instantiation failed: {e}")
            
            # Test 2: Try Sandbox.create() for comparison
            try:
                sandbox = Sandbox.create()
                print(f"Sandbox.create() returned: {type(sandbox)}")
                # Check if it's a coroutine
                import inspect
                if inspect.iscoroutine(sandbox):
                    print("Sandbox.create() returns a coroutine (needs await)")
                    actual_sandbox = await sandbox
                    print(f"After awaiting: {type(actual_sandbox)}")
                    if hasattr(actual_sandbox, 'close'):
                        await actual_sandbox.close()
            except Exception as e:
                print(f"Sandbox.create() test failed: {e}")
            
            # Test 3: Check the recommended pattern
            try:
                # Test with parameters like in the real code
                sandbox = Sandbox(
                    env_vars={
                        "ANTHROPIC_API_KEY": "test-key"
                    },
                    timeout=300
                )
                print(f"Sandbox with params worked: {type(sandbox)}")
                if hasattr(sandbox, 'close'):
                    await sandbox.close()
            except Exception as e:
                print(f"Sandbox with params failed: {e}")
            
        except Exception as e:
            print(f"Test setup failed: {e}")
            pytest.fail(f"Failed to test sandbox initialization: {e}")


    def test_sandbox_close_method(self):
        """Test if sandbox.close() is sync or async"""
        from e2b import Sandbox
        import inspect
        
        # Check if close is a coroutine function
        if hasattr(Sandbox, 'close'):
            is_async = inspect.iscoroutinefunction(Sandbox.close)
            print(f"Sandbox.close is async: {is_async}")
            
            # Check the method signature
            sig = inspect.signature(Sandbox.close)
            print(f"Sandbox.close signature: {sig}")
    
    @pytest.mark.asyncio
    async def test_e2b_sandbox_creation_fixed(self):
        """Test that E2B sandbox can be created with the fixes"""
        from e2b import Sandbox
        
        sandbox = None
        try:
            # Create sandbox with minimal parameters
            sandbox = Sandbox(timeout=30)  # Short timeout for testing
            print(f"✅ Successfully created sandbox: {type(sandbox)}")
            print(f"Sandbox ID: {sandbox.id if hasattr(sandbox, 'id') else 'No ID'}")
            
            # Test basic operations
            if hasattr(sandbox, 'process'):
                result = sandbox.process.start_and_wait("echo 'Hello from E2B'")  # Not async
                print(f"Command output: {result.stdout if hasattr(result, 'stdout') else result}")
            
        except Exception as e:
            print(f"❌ Failed to create/use sandbox: {e}")
            pytest.fail(f"Sandbox creation failed: {e}")
        finally:
            if sandbox:
                try:
                    sandbox.close()
                    print("✅ Successfully closed sandbox")
                except Exception as e:
                    print(f"❌ Failed to close sandbox: {e}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, '-v', '-s'])