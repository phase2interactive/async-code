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

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
        sandbox = await Sandbox.create(
            api_key=api_key,
            timeout=60  # 1 minute timeout for test
        )
        
        logger.info("✅ Successfully created E2B sandbox")
        
        # Test basic command execution
        result = await sandbox.process.start_and_wait("echo 'Hello from E2B!'")
        logger.info(f"✅ Command output: {result.stdout.strip()}")
        
        # Clean up
        await sandbox.close()
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
        sandbox = await Sandbox.create(
            api_key=executor.api_key,
            timeout=120
        )
        
        # Clone a small public repo for testing
        test_repo = "https://github.com/octocat/Hello-World.git"
        logger.info(f"📦 Cloning test repository: {test_repo}")
        
        clone_result = await sandbox.process.start_and_wait(
            f"git clone {test_repo} /workspace/test-repo"
        )
        
        if clone_result.exit_code != 0:
            logger.error(f"❌ Failed to clone: {clone_result.stderr}")
            return False
            
        logger.info("✅ Successfully cloned repository")
        
        # List files
        ls_result = await sandbox.process.start_and_wait("ls -la /workspace/test-repo")
        logger.info(f"📁 Repository contents:\n{ls_result.stdout}")
        
        # Clean up
        await sandbox.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Git operations test failed: {str(e)}")
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