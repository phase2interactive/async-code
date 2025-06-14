#!/usr/bin/env python3
"""
Simple test to check which E2B mode is active (real or simulation).
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Check E2B mode
print("🔍 Checking E2B configuration...")
print(f"E2B_API_KEY present: {'Yes' if os.getenv('E2B_API_KEY') else 'No'}")

# Import to trigger the conditional logic
try:
    from utils.code_task_e2b import USE_REAL_E2B
    
    if USE_REAL_E2B:
        print("✅ Real E2B implementation is active")
        print("   - E2B sandboxes will be used for code execution")
        print("   - Requires valid E2B_API_KEY")
    else:
        print("🔧 Simulation mode is active")
        print("   - Using subprocess for local execution")
        print("   - No E2B account required")
        
except Exception as e:
    print(f"❌ Error checking E2B mode: {str(e)}")

# Test imports
print("\n📦 Testing imports...")
try:
    from utils.code_task_e2b import run_ai_code_task_e2b
    print("✅ Successfully imported run_ai_code_task_e2b")
except Exception as e:
    print(f"❌ Failed to import: {str(e)}")

# Check other required environment variables
print("\n🔐 Checking other environment variables:")
env_vars = {
    'ANTHROPIC_API_KEY': 'Required for Claude agent',
    'OPENAI_API_KEY': 'Required for Codex/GPT agent',
    'GITHUB_TOKEN': 'Required for private repo access',
    'SUPABASE_URL': 'Required for database',
    'SUPABASE_KEY': 'Required for database',
    'JWT_SECRET': 'Required for authentication'
}

for var, description in env_vars.items():
    status = "✅" if os.getenv(var) else "❌"
    print(f"{status} {var}: {description}")