"""
Test suite for TestUserService
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone
import uuid
import jwt

# Set test environment variables before imports
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test-key"
os.environ["JWT_SECRET"] = "test-secret"

from test_user_service import TestUserService, TestUser


class TestTestUserService:
    """Test cases for TestUserService"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client"""
        mock = Mock()
        
        # Mock auth admin methods
        mock.auth.admin.create_user = Mock()
        mock.auth.admin.delete_user = Mock()
        
        # Mock table methods
        mock.table = Mock(return_value=Mock())
        
        return mock
    
    @pytest.fixture
    def service(self, mock_supabase):
        """Create test user service with mocked dependencies"""
        with patch('test_user_service.create_client', return_value=mock_supabase):
            service = TestUserService(
                supabase_url="https://test.supabase.co",
                supabase_service_key="test-service-key"
            )
            service.supabase = mock_supabase
            return service
    
    def test_service_initialization_with_valid_config(self):
        """Test service initialization with valid configuration"""
        with patch('test_user_service.create_client') as mock_create_client:
            service = TestUserService(
                supabase_url="https://test.supabase.co",
                supabase_service_key="test-key"
            )
            
            assert service.supabase_url == "https://test.supabase.co"
            assert service.supabase_service_key == "test-key"
            mock_create_client.assert_called_once()
    
    def test_service_initialization_missing_config(self):
        """Test service initialization with missing configuration"""
        with pytest.raises(ValueError, match="Missing required configuration"):
            TestUserService(
                supabase_url="https://test.supabase.co",
                supabase_service_key=None
            )
    
    def test_create_test_user_success(self, service, mock_supabase):
        """Test successful test user creation"""
        # Setup mocks
        test_user_id = str(uuid.uuid4())
        mock_user = Mock(id=test_user_id, user_metadata={"is_test_user": True})
        mock_supabase.auth.admin.create_user.return_value = Mock(user=mock_user)
        
        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = Mock(data=[{"id": test_user_id}])
        mock_supabase.table.return_value = mock_table
        
        # Mock generate_tokens
        with patch('test_user_service.generate_tokens') as mock_generate_tokens:
            mock_generate_tokens.return_value = {
                'access_token': 'test-access-token',
                'refresh_token': 'test-refresh-token',
                'expires_in': 3600
            }
            
            # Create test user
            result = service.create_test_user()
            
            # Assertions
            assert isinstance(result, TestUser)
            assert result.email == "test@asynccode.test"
            assert result.id == test_user_id
            assert result.access_token == 'test-access-token'
            assert result.refresh_token == 'test-refresh-token'
            
            # Verify Supabase calls
            mock_supabase.auth.admin.create_user.assert_called_once()
            create_user_call = mock_supabase.auth.admin.create_user.call_args[0][0]
            assert create_user_call["email"] == "test@asynccode.test"
            assert create_user_call["email_confirm"] is True
            assert create_user_call["user_metadata"]["is_test_user"] is True
            
            # Verify generate_tokens was called
            mock_generate_tokens.assert_called_once_with(test_user_id)
    
    def test_create_test_user_with_custom_email(self, service, mock_supabase):
        """Test creating test user with custom email"""
        test_user_id = str(uuid.uuid4())
        mock_user = Mock(id=test_user_id, user_metadata={})
        mock_supabase.auth.admin.create_user.return_value = Mock(user=mock_user)
        
        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = Mock(data=[{"id": test_user_id}])
        mock_supabase.table.return_value = mock_table
        
        # Mock generate_tokens
        with patch('test_user_service.generate_tokens') as mock_generate_tokens:
            mock_generate_tokens.return_value = {
                'access_token': 'test-access-token',
                'refresh_token': 'test-refresh-token',
                'expires_in': 3600
            }
            
            # Create with custom email
            result = service.create_test_user(email="custom@example.test")
            
            assert result.email == "custom@example.test"
    
    def test_create_test_user_invalid_email(self, service):
        """Test creating test user with non-.test email"""
        with pytest.raises(ValueError, match="Test user email must use .test TLD"):
            service.create_test_user(email="user@example.com")
    
    def test_create_test_user_auth_failure(self, service, mock_supabase):
        """Test handling auth creation failure"""
        mock_supabase.auth.admin.create_user.return_value = Mock(user=None)
        
        with pytest.raises(Exception, match="Failed to create test user in Supabase Auth"):
            service.create_test_user()
    
    def test_delete_test_user_success(self, service, mock_supabase):
        """Test successful test user deletion"""
        user_id = str(uuid.uuid4())
        
        # Mock user lookup
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": user_id, "is_test_user": True}]
        )
        mock_table.delete.return_value.eq.return_value.execute.return_value = Mock()
        mock_supabase.table.return_value = mock_table
        
        # Perform deletion
        result = service.delete_test_user(user_id)
        
        assert result is True
        mock_supabase.auth.admin.delete_user.assert_called_once_with(user_id)
    
    def test_delete_non_test_user(self, service, mock_supabase):
        """Test preventing deletion of non-test user"""
        user_id = str(uuid.uuid4())
        
        # Mock user lookup - not a test user
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{"id": user_id, "is_test_user": False}]
        )
        mock_supabase.table.return_value = mock_table
        
        with pytest.raises(ValueError, match="Cannot delete non-test user"):
            service.delete_test_user(user_id)
    
    def test_cleanup_expired_test_users(self, service, mock_supabase):
        """Test cleanup of expired test users"""
        expired_users = [
            {"id": str(uuid.uuid4())},
            {"id": str(uuid.uuid4())}
        ]
        
        # Mock expired user query
        mock_table = Mock()
        mock_chain = Mock()
        mock_table.select.return_value.eq.return_value.lt.return_value.execute.return_value = Mock(
            data=expired_users
        )
        mock_supabase.table.return_value = mock_table
        
        # Mock delete_test_user to succeed
        with patch.object(service, 'delete_test_user', return_value=True) as mock_delete:
            result = service.cleanup_expired_test_users()
            
            assert len(result) == 2
            assert mock_delete.call_count == 2
    
    def test_jwt_token_generation(self, service):
        """Test JWT token generation"""
        user_id = str(uuid.uuid4())
        
        # Mock generate_tokens
        with patch('test_user_service.generate_tokens') as mock_generate_tokens:
            mock_generate_tokens.return_value = {
                'access_token': 'mocked-access-token',
                'refresh_token': 'mocked-refresh-token',
                'expires_in': 3600
            }
            
            # Generate tokens
            access_token = service.generate_jwt_token(user_id, "access")
            refresh_token = service.generate_jwt_token(user_id, "refresh")
            
            # Verify tokens
            assert access_token == 'mocked-access-token'
            assert refresh_token == 'mocked-refresh-token'
            
            # Verify generate_tokens was called
            assert mock_generate_tokens.call_count == 2
            mock_generate_tokens.assert_called_with(user_id)
    
    def test_jwt_token_invalid_type(self, service):
        """Test JWT token generation with invalid type"""
        with pytest.raises(ValueError, match="Invalid token type"):
            service.generate_jwt_token("user-id", "invalid")
    
    def test_get_test_user_by_email(self, service, mock_supabase):
        """Test retrieving test user by email"""
        test_user = {"id": str(uuid.uuid4()), "email": "test@asynccode.test"}
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
            data=[test_user]
        )
        mock_supabase.table.return_value = mock_table
        
        result = service.get_test_user_by_email("test@asynccode.test")
        
        assert result == test_user
    
    def test_list_test_users(self, service, mock_supabase):
        """Test listing all test users"""
        test_users = [
            {"id": str(uuid.uuid4()), "email": "test1@asynccode.test"},
            {"id": str(uuid.uuid4()), "email": "test2@asynccode.test"}
        ]
        
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = Mock(
            data=test_users
        )
        mock_supabase.table.return_value = mock_table
        
        result = service.list_test_users()
        
        assert len(result) == 2
        assert result == test_users
    
    def test_password_generation(self, service):
        """Test that generated passwords are unique and follow pattern"""
        password1 = service._generate_test_password()
        password2 = service._generate_test_password()
        
        assert password1 != password2
        assert password1.startswith("TestUser_")
        assert password1.endswith("!")
        assert len(password1) > 20