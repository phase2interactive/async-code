#!/usr/bin/env python3
"""
Unit tests for E2B backend components
"""

import sys
import os
import json
import tempfile
import subprocess
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("1. Testing module imports...")
    
    try:
        import main
        print("   ✅ main.py imports successfully")
    except Exception as e:
        print(f"   ❌ Failed to import main.py: {e}")
        return False
    
    try:
        import database
        print("   ✅ database.py imports successfully")
    except Exception as e:
        print(f"   ❌ Failed to import database.py: {e}")
        return False
    
    try:
        from utils.code_task_e2b import run_ai_code_task_e2b
        print("   ✅ code_task_e2b.py imports successfully")
    except Exception as e:
        print(f"   ❌ Failed to import code_task_e2b.py: {e}")
        return False
    
    try:
        import auth
        print("   ✅ auth.py imports successfully")
    except Exception as e:
        print(f"   ❌ Failed to import auth.py: {e}")
        return False
    
    return True

def test_auth_functions():
    """Test authentication functions"""
    print("\n2. Testing authentication functions...")
    
    try:
        from auth import generate_tokens, decode_token
        
        # Test token generation
        test_user_id = "test-user-123"
        tokens = generate_tokens(test_user_id)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        print("   ✅ Token generation works")
        
        # Test token decoding
        decoded = decode_token(tokens["access_token"])
        assert decoded["sub"] == test_user_id
        print("   ✅ Token decoding works")
        
        return True
    except Exception as e:
        print(f"   ❌ Auth test failed: {e}")
        return False

def test_e2b_task_execution():
    """Test E2B task execution simulation"""
    print("\n3. Testing E2B task execution...")
    
    try:
        from utils.code_task_e2b import simulate_ai_execution, parse_file_changes
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=temp_dir, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=temp_dir, check=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=temp_dir, check=True)
            
            # Create initial commit
            test_file = os.path.join(temp_dir, "README.md")
            with open(test_file, "w") as f:
                f.write("# Test Repo\n")
            subprocess.run(["git", "add", "-A"], cwd=temp_dir, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, check=True)
            
            # Test simulation
            result = simulate_ai_execution(temp_dir, "Test prompt", "claude")
            
            assert result["success"] == True
            assert "commit_hash" in result
            assert "git_diff" in result
            assert "changed_files" in result
            print("   ✅ E2B task simulation works")
            
            # Test diff parsing
            if result["git_diff"]:
                file_changes = parse_file_changes(result["git_diff"])
                assert isinstance(file_changes, list)
                print("   ✅ Git diff parsing works")
            
        return True
    except Exception as e:
        print(f"   ❌ E2B task test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_loading():
    """Test configuration loading"""
    print("\n4. Testing configuration...")
    
    try:
        from env_config import Config
        
        # Check if required env vars are set
        required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "JWT_SECRET"]
        missing = [var for var in required_vars if not getattr(Config, var)]
        
        if missing:
            print(f"   ⚠️  Missing env vars: {', '.join(missing)} (OK for unit tests)")
        else:
            print("   ✅ All required environment variables are set")
        
        # Check default values
        assert Config.JWT_ALGORITHM == "HS256"
        assert Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 0
        print("   ✅ Default configurations loaded correctly")
        
        return True
    except Exception as e:
        print(f"   ❌ Config test failed: {e}")
        return False

def test_models():
    """Test Pydantic models"""
    print("\n5. Testing data models...")
    
    try:
        from models import TaskStatus
        from test_user_models import TestUserCreateRequest
        
        # Test TaskStatus enum
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        print("   ✅ TaskStatus enum works")
        
        # Test model validation
        test_request = TestUserCreateRequest(email="test@example.test")
        assert test_request.email == "test@example.test"
        print("   ✅ Model validation works")
        
        return True
    except Exception as e:
        print(f"   ❌ Model test failed: {e}")
        return False

def main():
    """Run all unit tests"""
    print("🧪 E2B Backend Unit Tests\n")
    
    tests = [
        test_imports,
        test_auth_functions,
        test_e2b_task_execution,
        test_config_loading,
        test_models
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print(f"\n📊 Test Summary:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    
    if failed == 0:
        print("\n✅ All unit tests passed!")
        return 0
    else:
        print(f"\n❌ {failed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())