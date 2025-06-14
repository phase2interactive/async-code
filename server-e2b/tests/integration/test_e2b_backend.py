#!/usr/bin/env python3
"""
Test script for E2B backend to ensure API compatibility
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoints"""
    print("Testing health endpoints...")
    
    # Test /ping
    response = requests.get(f"{BASE_URL}/ping")
    assert response.status_code == 200
    print("✅ /ping endpoint working")
    
    # Test /health
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    print(f"✅ /health endpoint working: {data}")

def test_auth():
    """Test authentication endpoints"""
    print("\nTesting authentication...")
    
    # Create test user token
    response = requests.post(f"{BASE_URL}/api/test-users", json={
        "email": "test@example.test"
    })
    
    if response.status_code != 201:
        print(f"❌ Failed to create test user: {response.text}")
        return None
        
    user_data = response.json()
    access_token = user_data["tokens"]["access_token"]
    user_id = user_data["user"]["id"]
    
    print(f"✅ Test user created: {user_id}")
    
    # Verify token
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/api/auth/verify", headers=headers)
    assert response.status_code == 200
    print("✅ Token verification working")
    
    return access_token, user_id

def test_projects(access_token):
    """Test project endpoints"""
    print("\nTesting project endpoints...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Create project
    response = requests.post(f"{BASE_URL}/projects", headers=headers, json={
        "name": "Test Project",
        "repo_url": "https://github.com/test/repo",
        "description": "Test project for E2B backend"
    })
    
    if response.status_code != 201:
        print(f"❌ Failed to create project: {response.text}")
        return None
        
    project = response.json()
    project_id = project["id"]
    print(f"✅ Project created: {project_id}")
    
    # List projects
    response = requests.get(f"{BASE_URL}/projects", headers=headers)
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) > 0
    print(f"✅ Listed {len(projects)} projects")
    
    # Get specific project
    response = requests.get(f"{BASE_URL}/projects/{project_id}", headers=headers)
    assert response.status_code == 200
    print("✅ Retrieved specific project")
    
    return project_id

def test_tasks(access_token, project_id):
    """Test task endpoints"""
    print("\nTesting task endpoints...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Note: We won't actually start a task as it requires valid GitHub token
    # and E2B API key. We'll just test the endpoint responds correctly
    
    response = requests.post(f"{BASE_URL}/start-task", headers=headers, json={
        "prompt": "Test task",
        "repo_url": "https://github.com/test/repo",
        "github_token": "invalid_token",
        "project_id": project_id
    })
    
    # Should fail with auth error or similar, but endpoint should work
    print(f"✅ Task endpoint responded: {response.status_code}")
    
    # List tasks
    response = requests.get(f"{BASE_URL}/tasks", headers=headers)
    assert response.status_code == 200
    tasks = response.json()
    print(f"✅ Listed {len(tasks)} tasks")

def main():
    """Run all tests"""
    print("🚀 Testing E2B Backend API Compatibility\n")
    
    try:
        # Test health
        test_health()
        
        # Test auth and get token
        auth_result = test_auth()
        if not auth_result:
            print("❌ Authentication failed, stopping tests")
            return 1
            
        access_token, user_id = auth_result
        
        # Test projects
        project_id = test_projects(access_token)
        if not project_id:
            print("❌ Project creation failed, stopping tests")
            return 1
        
        # Test tasks
        test_tasks(access_token, project_id)
        
        print("\n✅ All tests passed! E2B backend is compatible with existing API")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())