#!/usr/bin/env python3
"""
Test script for E2B integration.
This script tests the real E2B implementation to ensure it works correctly.
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv

# Add parent directory to path to find utils module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.code_task_e2b_real import E2BCodeExecutor
from database import DatabaseOperations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_e2b_sandbox_creation():
    """Test basic E2B sandbox creation"""
    logger.info("🧪 Testing E2B sandbox creation...")
    
    try:
        from e2b import Sandbox
        
        # Check if API key is available
        api_key = os.getenv('E2B_API_KEY')
        if not api_key:
            logger.error("❌ E2B_API_KEY not found in environment")
            return False
            
        # Try to create a sandbox
        sandbox = Sandbox(
            api_key=api_key,
            timeout=60  # 1 minute timeout for test
        )
        
        logger.info("✅ Successfully created E2B sandbox")
        
        # Test basic command execution
        result = sandbox.commands.run("echo 'Hello from E2B!'")
        logger.info(f"✅ Command output: {result.stdout.strip()}")
        
        # Clean up
        sandbox.kill()
        logger.info("✅ Sandbox closed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create E2B sandbox: {str(e)}")
        return False


async def test_e2b_git_operations():
    """Test git operations in E2B sandbox"""
    logger.info("🧪 Testing git operations in E2B...")
    
    try:
        executor = E2BCodeExecutor()
        
        # Create a test sandbox
        from e2b import Sandbox
        sandbox = Sandbox(
            api_key=executor.api_key,
            timeout=120
        )
        
        # Create workspace in user's home directory (matching production)
        workspace_path = "/home/user/workspace"
        mkdir_result = sandbox.commands.run(f"mkdir -p {workspace_path}")
        if mkdir_result.exit_code != 0:
            logger.error(f"❌ Failed to create workspace: {mkdir_result.stderr}")
            return False
            
        # Clone a small public repo for testing
        test_repo = "https://github.com/octocat/Hello-World.git"
        logger.info(f"📦 Cloning test repository: {test_repo}")
        
        clone_result = sandbox.commands.run(
            f"git clone {test_repo} {workspace_path}/repo"
        )
        
        if clone_result.exit_code != 0:
            logger.error(f"❌ Failed to clone: {clone_result.stderr}")
            return False
            
        logger.info("✅ Successfully cloned repository")
        
        # List files
        ls_result = sandbox.commands.run(f"ls -la {workspace_path}/repo")
        logger.info(f"📁 Repository contents:\n{ls_result.stdout}")
        
        # Clean up
        sandbox.kill()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Git operations test failed: {str(e)}")
        return False


async def test_missing_workspace_directory_handling():
    """Test that missing /workspace directory is handled gracefully"""
    logger.info("🧪 Testing missing workspace directory handling...")
    
    try:
        from e2b import Sandbox
        executor = E2BCodeExecutor()
        
        # Create a sandbox without custom template (simulating default E2B environment)
        sandbox = Sandbox(
            api_key=executor.api_key,
            timeout=60
        )
        
        # First check current working directory
        pwd_result = sandbox.commands.run("pwd")
        logger.info(f"Current directory: {pwd_result.stdout.strip()}")
        
        # Check if workspace exists in home
        workspace_path = "/home/user/workspace"
        try:
            check_result = sandbox.commands.run(f"ls -la {workspace_path}")
            workspace_exists = True
        except Exception:
            workspace_exists = False
        
        if workspace_exists:
            logger.info(f"ℹ️ {workspace_path} already exists")
        else:
            logger.info(f"✅ {workspace_path} doesn't exist (expected)")
            
        # Try to clone without creating directory first (should fail)
        test_repo = "https://github.com/octocat/Hello-World.git"
        try:
            clone_result = sandbox.commands.run(
                f"git clone {test_repo} {workspace_path}/repo"
            )
            clone_failed = False
        except Exception as e:
            clone_failed = True
            logger.info(f"Clone failed as expected: {str(e)}")
        
        if clone_failed:
            logger.info("✅ Got expected error without directory")
            
            # Now create directory and retry
            mkdir_result = sandbox.commands.run(f"mkdir -p {workspace_path}")
            if mkdir_result.exit_code == 0:
                logger.info("✅ Successfully created workspace directory")
                
                # Try clone again
                clone_retry = sandbox.commands.run(
                    f"git clone {test_repo} {workspace_path}/repo"
                )
                
                if clone_retry.exit_code == 0:
                    logger.info("✅ Clone succeeded after creating directory")
                    sandbox.kill()
                    return True
                else:
                    logger.error(f"❌ Clone still failed: {clone_retry.stderr}")
            else:
                logger.error(f"❌ Failed to create directory: {mkdir_result.stderr}")
        else:
            logger.info("ℹ️ Clone worked without creating directory (custom template?)")
            sandbox.kill()
            return True
            
        sandbox.kill()
        return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        return False


async def test_full_execution():
    """Test full E2B task execution with a simple prompt"""
    logger.info("🧪 Testing full E2B task execution...")
    
    # Check required environment variables
    required_vars = ['E2B_API_KEY', 'GITHUB_TOKEN', 'SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    try:
        # Create a test task in the database
        test_user_id = "test-user-001"
        test_task = DatabaseOperations.create_task(
            user_id=test_user_id,
            repo_url="https://github.com/octocat/Hello-World.git",
            target_branch="master",
            agent="claude",
            chat_messages=[{
                'role': 'user',
                'content': 'Add a simple README update with the current date',
                'timestamp': 0
            }]
        )
        
        if not test_task:
            logger.error("❌ Failed to create test task in database")
            return False
            
        logger.info(f"✅ Created test task with ID: {test_task['id']}")
        
        # Execute the task
        executor = E2BCodeExecutor()
        result = await executor.execute_task(
            task_id=test_task['id'],
            user_id=test_user_id,
            github_token=os.getenv('GITHUB_TOKEN'),
            repo_url=test_task['repo_url'],
            branch=test_task['target_branch'],
            prompt=test_task['chat_messages'][0]['content'],
            agent='claude'
        )
        
        logger.info(f"✅ Task executed successfully!")
        logger.info(f"📝 Changed files: {result.get('changes', [])}")
        logger.info(f"💬 Agent output: {result.get('agent_output', '')[:200]}...")
        
        # Check task status in database
        updated_task = DatabaseOperations.get_task_by_id(test_task['id'], test_user_id)
        logger.info(f"📊 Final task status: {updated_task['status']}")
        
        return updated_task['status'] == 'completed'
        
    except Exception as e:
        logger.error(f"❌ Full execution test failed: {str(e)}")
        return False


async def main():
    """Run all tests"""
    logger.info("🚀 Starting E2B integration tests...")
    
    # Load environment variables
    load_dotenv()
    
    # Check if E2B is configured
    if not os.getenv('E2B_API_KEY'):
        logger.warning("⚠️  E2B_API_KEY not configured - tests will run in simulation mode")
        logger.info("ℹ️  To test real E2B integration, set E2B_API_KEY in your .env file")
        return
    
    # Run tests
    tests = [
        ("Sandbox Creation", test_e2b_sandbox_creation),
        ("Missing Workspace Directory Handling", test_missing_workspace_directory_handling),
        ("Git Operations", test_e2b_git_operations),
        # Uncomment to test full execution (requires all env vars)
        # ("Full Execution", test_full_execution),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("📊 Test Summary:")
    logger.info(f"{'='*50}")
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, success in results if success)
    logger.info(f"\nTotal: {total_passed}/{len(results)} tests passed")


if __name__ == "__main__":
    asyncio.run(main())