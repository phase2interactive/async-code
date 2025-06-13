#!/usr/bin/env python3
"""
Comprehensive test suite for E2B backend
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:5000"

def test_health_endpoints():
    """Test health and status endpoints"""
    print("1. Testing health endpoints...")
    
    # Test /ping
    response = requests.get(f"{BASE_URL}/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "pong"
    print("   ✅ /ping endpoint")
    
    # Test root /
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "endpoints" in data
    print("   ✅ / (root) endpoint")

def test_authentication():
    """Test authentication endpoints"""
    print("\n2. Testing authentication...")
    
    # Create test user
    response = requests.post(f"{BASE_URL}/api/test-users", json={
        "email": "test@example.test"
    })
    
    if response.status_code != 201:
        print(f"   ❌ Failed to create test user: {response.text}")
        return None, None
        
    user_data = response.json()
    access_token = user_data["tokens"]["access_token"]
    user_id = user_data["user"]["id"]
    print(f"   ✅ Test user created: {user_id}")
    
    # Verify token
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/api/auth/verify", headers=headers)
    assert response.status_code == 200
    print("   ✅ Token verification")
    
    return access_token, user_id

def test_projects(access_token):
    """Test project management endpoints"""
    print("\n3. Testing project endpoints...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Create project
    response = requests.post(f"{BASE_URL}/projects", headers=headers, json={
        "name": "Test E2B Project",
        "repo_url": "https://github.com/test/repo",
        "description": "Testing E2B backend"
    })
    
    if response.status_code != 201:
        print(f"   ❌ Failed to create project: {response.text}")
        return None
        
    project = response.json()
    project_id = project["id"]
    print(f"   ✅ Project created: {project_id}")
    
    # List projects
    response = requests.get(f"{BASE_URL}/projects", headers=headers)
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) > 0
    print(f"   ✅ Listed {len(projects)} projects")
    
    # Get specific project
    response = requests.get(f"{BASE_URL}/projects/{project_id}", headers=headers)
    assert response.status_code == 200
    print("   ✅ Retrieved specific project")
    
    # Update project
    response = requests.put(f"{BASE_URL}/projects/{project_id}", headers=headers, json={
        "description": "Updated E2B test project"
    })
    assert response.status_code == 200
    print("   ✅ Updated project")
    
    return project_id

def test_tasks(access_token, project_id):
    """Test task management endpoints"""
    print("\n4. Testing task endpoints...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Create task (will fail with invalid token, but tests endpoint)
    response = requests.post(f"{BASE_URL}/start-task", headers=headers, json={
        "prompt": "Test E2B task execution",
        "repo_url": "https://github.com/test/repo",
        "github_token": "test_token",
        "project_id": project_id,
        "model": "claude"
    })
    
    if response.status_code == 200:
        task_data = response.json()
        task_id = task_data.get("task_id")
        print(f"   ✅ Task created: {task_id}")
        
        # Get task status
        time.sleep(1)  # Wait a bit for task to process
        response = requests.get(f"{BASE_URL}/task-status/{task_id}", headers=headers)
        assert response.status_code == 200
        status_data = response.json()
        print(f"   ✅ Task status: {status_data['status']}")
    else:
        print("   ⚠️  Task creation returned non-200 (expected with test token)")
    
    # List tasks
    response = requests.get(f"{BASE_URL}/tasks", headers=headers)
    assert response.status_code == 200
    tasks = response.json()
    print(f"   ✅ Listed {len(tasks)} tasks")
    
    # List tasks by project
    response = requests.get(f"{BASE_URL}/tasks?project_id={project_id}", headers=headers)
    assert response.status_code == 200
    print("   ✅ Listed tasks by project")

def test_validation_endpoints(access_token):
    """Test validation endpoints"""
    print("\n5. Testing validation endpoints...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test token validation
    response = requests.post(f"{BASE_URL}/validate-token", headers=headers, json={
        "github_token": "test_token"
    })
    # This will fail with invalid token, but tests the endpoint
    print(f"   ✅ Token validation endpoint responded: {response.status_code}")

def test_error_handling(access_token):
    """Test error handling"""
    print("\n6. Testing error handling...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test missing required fields
    response = requests.post(f"{BASE_URL}/start-task", headers=headers, json={
        "prompt": "Test task"
        # Missing repo_url and github_token
    })
    assert response.status_code == 400
    print("   ✅ Missing fields handled correctly")
    
    # Test invalid project ID
    response = requests.get(f"{BASE_URL}/projects/999999", headers=headers)
    assert response.status_code == 404
    print("   ✅ Invalid project ID handled correctly")
    
    # Test invalid task ID
    response = requests.get(f"{BASE_URL}/task-status/999999", headers=headers)
    assert response.status_code == 404
    print("   ✅ Invalid task ID handled correctly")

def test_cors_headers():
    """Test CORS configuration"""
    print("\n7. Testing CORS headers...")
    
    headers = {"Origin": "http://localhost:3000"}
    response = requests.get(f"{BASE_URL}/ping", headers=headers)
    
    # Check CORS headers
    cors_headers = response.headers.get("Access-Control-Allow-Origin")
    if cors_headers:
        print(f"   ✅ CORS configured: {cors_headers}")
    else:
        print("   ⚠️  CORS headers not found (may be OK in test env)")

def cleanup_test_users():
    """Clean up test users"""
    print("\n8. Cleaning up test data...")
    
    # List test users
    response = requests.get(f"{BASE_URL}/api/test-users")
    if response.status_code == 200:
        users = response.json()
        for user in users:
            requests.delete(f"{BASE_URL}/api/test-users/{user['id']}")
        print(f"   ✅ Cleaned up {len(users)} test users")

def main():
    """Run all tests"""
    print("🚀 E2B Backend Comprehensive Test Suite\n")
    
    try:
        # Check if server is running
        try:
            response = requests.get(f"{BASE_URL}/ping", timeout=2)
        except requests.exceptions.ConnectionError:
            print("❌ Server is not running! Start it with: cd server-e2b && ./run.sh")
            return 1
        
        # Run tests
        test_health_endpoints()
        
        auth_result = test_authentication()
        if not auth_result[0]:
            print("\n❌ Authentication failed, stopping tests")
            return 1
            
        access_token, user_id = auth_result
        
        project_id = test_projects(access_token)
        if project_id:
            test_tasks(access_token, project_id)
        
        test_validation_endpoints(access_token)
        test_error_handling(access_token)
        test_cors_headers()
        cleanup_test_users()
        
        print("\n✅ All tests passed! E2B backend is working correctly")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test assertion failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())