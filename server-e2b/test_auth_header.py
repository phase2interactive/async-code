"""
Test case for authorization header bug when validating GitHub token.
This test should FAIL initially to demonstrate the bug.
"""
import pytest
import json
from main import app
from unittest.mock import patch, MagicMock
import jwt
from datetime import datetime, timedelta

class TestAuthorizationHeader:
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def mock_supabase_user(self):
        """Mock Supabase user response"""
        return {
            'id': 'test-user-id',
            'email': 'test@example.com',
            'user_metadata': {}
        }
    
    @pytest.fixture
    def valid_jwt_token(self):
        """Generate a valid JWT token for testing"""
        from env_config import Config
        payload = {
            'user_id': 'test-user-id',
            'type': 'access',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
    
    def test_validate_token_without_authorization_header(self, client):
        """Test that validate-token endpoint fails when Authorization header is missing"""
        # This test should FAIL initially, demonstrating the bug
        
        # Make request without Authorization header
        response = client.post('/api/validate-token',
                             json={'github_token': 'ghp_test123'},
                             headers={'Content-Type': 'application/json'})
        
        # Expect 401 Unauthorized with missing authorization header message
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
        assert 'authorization header' in data['error'].lower()
    
    def test_validate_token_with_invalid_authorization_format(self, client):
        """Test that validate-token endpoint fails with invalid authorization format"""
        
        # Make request with invalid Authorization header format
        response = client.post('/api/validate-token',
                             json={'github_token': 'ghp_test123'},
                             headers={
                                 'Content-Type': 'application/json',
                                 'Authorization': 'InvalidFormat token123'
                             })
        
        # Expect 401 Unauthorized
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('database.DatabaseOperations.get_user_by_id')
    @patch('tasks.Github')
    def test_validate_token_with_valid_authorization_header(self, mock_github_class, mock_get_user, client, valid_jwt_token):
        """Test that validate-token endpoint works with proper authorization header"""
        
        # Mock user exists in database
        mock_get_user.return_value = {
            'id': 'test-user-id',
            'email': 'test@example.com'
        }
        
        # Mock GitHub API
        mock_github = MagicMock()
        mock_user = MagicMock()
        mock_user.login = 'testuser'
        mock_github.get_user.return_value = mock_user
        
        mock_rate_limit = MagicMock()
        mock_rate_limit.core.remaining = 5000
        mock_rate_limit.core.limit = 5000
        mock_github.get_rate_limit.return_value = mock_rate_limit
        
        mock_github_class.return_value = mock_github
        
        # Make request with proper Authorization header
        response = client.post('/api/validate-token',
                             json={'github_token': 'ghp_test123'},
                             headers={
                                 'Content-Type': 'application/json',
                                 'Authorization': f'Bearer {valid_jwt_token}'
                             })
        
        # Should succeed
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['user'] == 'testuser'
    
    def test_auth_token_endpoint_returns_proper_format(self, client):
        """Test that the /api/auth/token endpoint returns token in expected format"""
        
        # Request token
        response = client.post('/api/auth/token',
                             json={
                                 'user_id': 'test-user-id'
                             },
                             headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify response includes tokens
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'expires_in' in data