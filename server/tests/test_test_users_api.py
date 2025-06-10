"""
Test suite for Test User API endpoints
"""

import pytest
import json
from unittest.mock import Mock, patch
import os

from main import app
from test_user_service import TestUser
from datetime import datetime, timezone


class TestTestUsersAPI:
    """Test cases for test user API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def mock_test_user(self):
        """Create mock test user"""
        return TestUser(
            id="test-user-123",
            email="test@asynccode.test",
            created_at=datetime.now(timezone.utc),
            metadata={"is_test_user": True},
            access_token="test-access-token",
            refresh_token="test-refresh-token"
        )
    
    @pytest.fixture(autouse=True)
    def enable_test_mode(self):
        """Enable test mode for all tests"""
        os.environ["ENABLE_TEST_USERS"] = "true"
        os.environ["ENVIRONMENT"] = "test"
        yield
        # Cleanup
        if "ENABLE_TEST_USERS" in os.environ:
            del os.environ["ENABLE_TEST_USERS"]
        if "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]
    
    def test_create_test_user_success(self, client, mock_test_user):
        """Test successful test user creation"""
        with patch('test_users.get_test_user_service') as mock_service:
            mock_service.return_value.create_test_user.return_value = mock_test_user
            
            response = client.post(
                '/api/test-users',
                json={
                    "email": "custom@test.test",
                    "metadata": {"scenario": "auth_test"}
                }
            )
            
            assert response.status_code == 201
            data = json.loads(response.data)
            
            assert data["user"]["id"] == "test-user-123"
            assert data["user"]["email"] == "test@asynccode.test"
            assert data["tokens"]["access_token"] == "test-access-token"
            assert data["tokens"]["refresh_token"] == "test-refresh-token"
    
    def test_create_test_user_default_values(self, client, mock_test_user):
        """Test creating test user with default values"""
        with patch('test_users.get_test_user_service') as mock_service:
            mock_service.return_value.create_test_user.return_value = mock_test_user
            
            response = client.post('/api/test-users', json={})
            
            assert response.status_code == 201
            # Verify service was called with defaults
            mock_service.return_value.create_test_user.assert_called_with(
                email=None,
                user_id=None,
                metadata={}
            )
    
    def test_create_test_user_validation_error(self, client):
        """Test validation error during user creation"""
        with patch('test_users.get_test_user_service') as mock_service:
            mock_service.return_value.create_test_user.side_effect = ValueError("Invalid email")
            
            response = client.post('/api/test-users', json={"email": "bad@example.com"})
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "Invalid email" in data["error"]
    
    def test_delete_test_user_success(self, client):
        """Test successful test user deletion"""
        with patch('test_users.get_test_user_service') as mock_service:
            mock_service.return_value.delete_test_user.return_value = True
            
            response = client.delete('/api/test-users/test-user-123')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["message"] == "Test user deleted successfully"
    
    def test_delete_test_user_failure(self, client):
        """Test failed test user deletion"""
        with patch('test_users.get_test_user_service') as mock_service:
            mock_service.return_value.delete_test_user.return_value = False
            
            response = client.delete('/api/test-users/test-user-123')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert "Failed to delete test user" in data["error"]
    
    def test_list_test_users(self, client):
        """Test listing test users"""
        test_users = [
            {"id": "user-1", "email": "test1@asynccode.test", "is_test_user": True},
            {"id": "user-2", "email": "test2@asynccode.test", "is_test_user": True}
        ]
        
        with patch('test_users.get_test_user_service') as mock_service:
            mock_service.return_value.list_test_users.return_value = test_users
            
            response = client.get('/api/test-users')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data["users"]) == 2
            assert data["users"] == test_users
    
    def test_cleanup_test_users(self, client):
        """Test cleanup of expired test users"""
        deleted_users = ["user-1", "user-2", "user-3"]
        
        with patch('test_users.get_test_user_service') as mock_service:
            mock_service.return_value.cleanup_expired_test_users.return_value = deleted_users
            
            response = client.post('/api/test-users/cleanup')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["message"] == "Cleaned up 3 expired test users"
            assert data["deleted_users"] == deleted_users
    
    def test_refresh_test_user_token(self, client):
        """Test refreshing test user tokens"""
        with patch('test_users.get_test_user_service') as mock_service:
            # Mock user lookup
            mock_service.return_value.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
                data=[{"id": "test-user-123", "is_test_user": True}]
            )
            
            # Mock token generation
            mock_service.return_value.generate_jwt_token.side_effect = [
                "new-access-token",
                "new-refresh-token"
            ]
            
            response = client.post('/api/test-users/test-user-123/token')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["tokens"]["access_token"] == "new-access-token"
            assert data["tokens"]["refresh_token"] == "new-refresh-token"
    
    def test_refresh_token_user_not_found(self, client):
        """Test refreshing tokens for non-existent user"""
        with patch('test_users.get_test_user_service') as mock_service:
            # Mock empty user lookup
            mock_service.return_value.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
                data=[]
            )
            
            response = client.post('/api/test-users/unknown-user/token')
            
            assert response.status_code == 404
            data = json.loads(response.data)
            assert "Test user not found" in data["error"]
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/test-users/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["healthy"] is True
        assert data["test_mode_enabled"] is True
    
    def test_endpoints_disabled_in_production(self, client):
        """Test that endpoints are disabled in production"""
        os.environ["ENVIRONMENT"] = "production"
        
        # Test create endpoint
        response = client.post('/api/test-users', json={})
        assert response.status_code == 403
        data = json.loads(response.data)
        assert "disabled in production" in data["error"]
        
        # Test delete endpoint
        response = client.delete('/api/test-users/test-user')
        assert response.status_code == 403
        
        # Test list endpoint
        response = client.get('/api/test-users')
        assert response.status_code == 403
    
    def test_endpoints_disabled_without_flag(self, client):
        """Test that endpoints are disabled without enable flag"""
        del os.environ["ENABLE_TEST_USERS"]
        
        response = client.post('/api/test-users', json={})
        assert response.status_code == 403
        data = json.loads(response.data)
        assert "not enabled" in data["error"]