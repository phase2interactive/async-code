import pytest
import jwt
from datetime import datetime, timedelta, timezone
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import generate_tokens, verify_token, get_current_user_id, refresh_access_token

class TestJWTAuthentication:
    """Test suite for JWT authentication functionality"""
    
    def test_generate_tokens(self):
        """Test token generation"""
        user_id = "test-user-123"
        result = generate_tokens(user_id)
        
        # Check that all required fields are present
        assert 'access_token' in result
        assert 'refresh_token' in result
        assert 'expires_in' in result
        
        # Verify access token
        access_payload = jwt.decode(result['access_token'], 
                                   os.getenv('JWT_SECRET', 'your-secret-key-change-this-in-production'), 
                                   algorithms=['HS256'])
        assert access_payload['user_id'] == user_id
        assert access_payload['type'] == 'access'
        
        # Verify refresh token
        refresh_payload = jwt.decode(result['refresh_token'], 
                                    os.getenv('JWT_SECRET', 'your-secret-key-change-this-in-production'), 
                                    algorithms=['HS256'])
        assert refresh_payload['user_id'] == user_id
        assert refresh_payload['type'] == 'refresh'
    
    def test_verify_valid_access_token(self):
        """Test verification of valid access token"""
        user_id = "test-user-123"
        tokens = generate_tokens(user_id)
        
        payload = verify_token(tokens['access_token'], 'access')
        assert payload['user_id'] == user_id
        assert payload['type'] == 'access'
    
    def test_verify_invalid_token_type(self):
        """Test verification fails with wrong token type"""
        user_id = "test-user-123"
        tokens = generate_tokens(user_id)
        
        # Try to verify refresh token as access token
        with pytest.raises(jwt.InvalidTokenError, match='Invalid token type'):
            verify_token(tokens['refresh_token'], 'access')
    
    def test_verify_expired_token(self):
        """Test verification fails with expired token"""
        # Create an expired token
        now = datetime.now(timezone.utc)
        payload = {
            'user_id': 'test-user',
            'type': 'access',
            'exp': now - timedelta(hours=1),  # Expired 1 hour ago
            'iat': now - timedelta(hours=2)
        }
        
        expired_token = jwt.encode(payload, 
                                  os.getenv('JWT_SECRET', 'your-secret-key-change-this-in-production'), 
                                  algorithm='HS256')
        
        with pytest.raises(jwt.InvalidTokenError, match='Token has expired'):
            verify_token(expired_token, 'access')
    
    def test_verify_invalid_token(self):
        """Test verification fails with invalid token"""
        with pytest.raises(jwt.InvalidTokenError):
            verify_token('invalid.token.here', 'access')
    
    def test_get_current_user_id(self):
        """Test extracting user ID from token"""
        user_id = "test-user-123"
        tokens = generate_tokens(user_id)
        
        extracted_id = get_current_user_id(tokens['access_token'])
        assert extracted_id == user_id
    
    def test_refresh_access_token(self, mocker):
        """Test refreshing access token with valid refresh token"""
        # Mock the database operation
        mocker.patch('auth.DatabaseOperations.get_user_by_id', return_value={'id': 'test-user-123'})
        
        user_id = "test-user-123"
        tokens = generate_tokens(user_id)
        
        # Refresh the access token
        new_tokens = refresh_access_token(tokens['refresh_token'])
        
        # Verify new access token
        assert 'access_token' in new_tokens
        assert 'expires_in' in new_tokens
        assert 'refresh_token' not in new_tokens  # Should not return new refresh token
        
        # Verify the new access token is valid
        payload = verify_token(new_tokens['access_token'], 'access')
        assert payload['user_id'] == user_id
    
    def test_refresh_with_invalid_refresh_token(self):
        """Test refresh fails with invalid refresh token"""
        with pytest.raises(jwt.InvalidTokenError):
            refresh_access_token('invalid.refresh.token')
    
    def test_refresh_with_access_token(self):
        """Test refresh fails when using access token instead of refresh token"""
        user_id = "test-user-123"
        tokens = generate_tokens(user_id)
        
        # Try to refresh using access token
        with pytest.raises(jwt.InvalidTokenError, match='Invalid token type'):
            refresh_access_token(tokens['access_token'])


class TestAuthDecorator:
    """Test suite for the require_auth decorator"""
    
    def test_missing_authorization_header(self, app):
        """Test endpoint returns 401 when Authorization header is missing"""
        from main import app as flask_app
        
        with flask_app.test_client() as client:
            response = client.get('/api/auth/verify')
            assert response.status_code == 401
            assert response.json['error'] == 'Missing authorization header'
    
    def test_invalid_authorization_scheme(self, app):
        """Test endpoint returns 401 with invalid auth scheme"""
        from main import app as flask_app
        
        with flask_app.test_client() as client:
            response = client.get('/api/auth/verify', headers={
                'Authorization': 'Basic sometoken'
            })
            assert response.status_code == 401
            assert response.json['error'] == 'Invalid authentication scheme'
    
    def test_invalid_authorization_format(self, app):
        """Test endpoint returns 401 with invalid auth format"""
        from main import app as flask_app
        
        with flask_app.test_client() as client:
            response = client.get('/api/auth/verify', headers={
                'Authorization': 'InvalidFormat'
            })
            assert response.status_code == 401
            assert response.json['error'] == 'Invalid authorization header format'
    
    def test_valid_authorization(self, app, mocker):
        """Test endpoint works with valid JWT token"""
        # Mock the database operation
        mocker.patch('auth.DatabaseOperations.get_user_by_id', return_value={'id': 'test-user-123'})
        
        from main import app as flask_app
        
        user_id = "test-user-123"
        tokens = generate_tokens(user_id)
        
        with flask_app.test_client() as client:
            response = client.get('/api/auth/verify', headers={
                'Authorization': f'Bearer {tokens["access_token"]}'
            })
            assert response.status_code == 200
            assert response.json['valid'] == True
            assert response.json['user_id'] == user_id


@pytest.fixture
def app():
    """Create Flask app for testing"""
    import main
    main.app.config['TESTING'] = True
    return main.app