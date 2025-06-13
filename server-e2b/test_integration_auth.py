"""
Integration test to verify the authorization header fix works end-to-end
"""
import pytest
import json
from main import app
from unittest.mock import patch, MagicMock
import jwt
from datetime import datetime, timedelta
from env_config import Config

class TestAuthIntegration:
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def valid_user_token(self):
        """Generate a valid JWT token for testing"""
        # Use the actual secret from config
        payload = {
            'user_id': 'test-user-id',
            'type': 'access',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
    
    @patch('database.DatabaseOperations.get_user_by_id')
    @patch('tasks.Github')
    def test_validate_token_with_proper_auth(self, mock_github_class, mock_get_user, client, valid_user_token):
        """Test the complete flow: auth header is sent and token validation works"""
        
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
                                 'Authorization': f'Bearer {valid_user_token}'
                             })
        
        # Should succeed
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['user'] == 'testuser'
        assert 'message' in data
    
    def test_validate_token_without_auth_header_fails(self, client):
        """Ensure the endpoint still requires authentication"""
        
        # Make request without Authorization header
        response = client.post('/api/validate-token',
                             json={'github_token': 'ghp_test123'},
                             headers={'Content-Type': 'application/json'})
        
        # Should fail with 401
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
        assert 'authorization header' in data['error'].lower()