"""
Test User Management Service

This module provides functionality for creating and managing test users
for automated testing. It integrates with Supabase for user creation
and JWT token generation for authentication.
"""

import os
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from supabase import create_client, Client
from auth import generate_tokens

logger = logging.getLogger(__name__)


@dataclass
class TestUser:
    """Test user data structure"""
    id: str
    email: str
    created_at: datetime
    metadata: Dict[str, Any]
    access_token: str
    refresh_token: str


class TestUserService:
    """Service for managing test users in isolated test environments"""
    
    DEFAULT_TEST_EMAIL = "test@asynccode.test"
    TEST_USER_PREFIX = "test_user_"
    TEST_USER_TTL_HOURS = 1  # Auto cleanup after 1 hour
    
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_service_key: Optional[str] = None
    ):
        """
        Initialize the test user service
        
        Args:
            supabase_url: Supabase project URL
            supabase_service_key: Service role key for admin operations
        """
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_URL")
        self.supabase_service_key = supabase_service_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        if not all([self.supabase_url, self.supabase_service_key]):
            raise ValueError("Missing required configuration: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        
        # Create Supabase client with service role key
        self.supabase: Client = create_client(
            self.supabase_url,
            self.supabase_service_key
        )
        
        logger.info("TestUserService initialized")
    
    def create_test_user(
        self,
        email: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TestUser:
        """
        Create a test user for automated testing
        
        Args:
            email: Email address for the test user (defaults to test@asynccode.test)
            user_id: Specific user ID to use (for consistent testing)
            metadata: Additional metadata to store with the user
            
        Returns:
            TestUser object with user details and authentication tokens
        """
        email = email or self.DEFAULT_TEST_EMAIL
        user_id = user_id or str(uuid.uuid4())
        
        # Ensure test user email uses .test TLD
        if not email.endswith(".test"):
            raise ValueError("Test user email must use .test TLD for safety")
        
        try:
            # Create user in Supabase Auth
            auth_response = self.supabase.auth.admin.create_user({
                "email": email,
                "password": self._generate_test_password(),
                "email_confirm": True,  # Auto-confirm email for test users
                "user_metadata": {
                    "is_test_user": True,
                    "created_by": "test_user_service",
                    "ttl_hours": self.TEST_USER_TTL_HOURS,
                    **(metadata or {})
                }
            })
            
            if not auth_response.user:
                raise Exception("Failed to create test user in Supabase Auth")
            
            # Use the actual user ID from Supabase
            created_user_id = auth_response.user.id
            
            # Create user record in database
            user_data = {
                "id": created_user_id,
                "email": email,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_test_user": True,
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=self.TEST_USER_TTL_HOURS)).isoformat()
            }
            
            db_response = self.supabase.table("users").insert(user_data).execute()
            
            # Generate JWT tokens using auth module
            tokens = generate_tokens(created_user_id)
            
            test_user = TestUser(
                id=created_user_id,
                email=email,
                created_at=datetime.now(timezone.utc),
                metadata=auth_response.user.user_metadata,
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token']
            )
            
            logger.info(f"Created test user: {email} (ID: {created_user_id})")
            return test_user
            
        except Exception as e:
            logger.error(f"Failed to create test user: {str(e)}")
            raise
    
    def delete_test_user(self, user_id: str) -> bool:
        """
        Delete a test user and all associated data
        
        Args:
            user_id: ID of the test user to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            # Verify this is a test user
            user_response = self.supabase.table("users").select("*").eq("id", user_id).execute()
            if not user_response.data or not user_response.data[0].get("is_test_user"):
                raise ValueError("Cannot delete non-test user")
            
            # Delete user's data from tables (cascade should handle most)
            # Delete in order of dependencies
            tables_to_clean = ["tasks", "projects"]
            for table in tables_to_clean:
                self.supabase.table(table).delete().eq("user_id", user_id).execute()
            
            # Delete from users table
            self.supabase.table("users").delete().eq("id", user_id).execute()
            
            # Delete from Supabase Auth
            self.supabase.auth.admin.delete_user(user_id)
            
            logger.info(f"Deleted test user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete test user {user_id}: {str(e)}")
            return False
    
    def cleanup_expired_test_users(self) -> List[str]:
        """
        Clean up test users that have exceeded their TTL
        
        Returns:
            List of deleted user IDs
        """
        try:
            # Find expired test users
            current_time = datetime.now(timezone.utc).isoformat()
            expired_users = self.supabase.table("users")\
                .select("id")\
                .eq("is_test_user", True)\
                .lt("expires_at", current_time)\
                .execute()
            
            deleted_users = []
            for user in expired_users.data:
                if self.delete_test_user(user["id"]):
                    deleted_users.append(user["id"])
            
            if deleted_users:
                logger.info(f"Cleaned up {len(deleted_users)} expired test users")
            
            return deleted_users
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired test users: {str(e)}")
            return []
    
    def generate_jwt_token(self, user_id: str, token_type: str = "access") -> str:
        """
        Generate a JWT token for a test user
        
        Args:
            user_id: ID of the test user
            token_type: Type of token ("access" or "refresh")
            
        Returns:
            JWT token string
        """
        # Use auth module to generate tokens
        tokens = generate_tokens(user_id)
        
        if token_type == "access":
            return tokens['access_token']
        elif token_type == "refresh":
            return tokens['refresh_token']
        else:
            raise ValueError(f"Invalid token type: {token_type}")
    
    def _generate_test_password(self) -> str:
        """Generate a secure password for test users"""
        # Use a consistent but secure pattern for test passwords
        return f"TestUser_{uuid.uuid4().hex[:16]}!"
    
    def get_test_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get test user details by email
        
        Args:
            email: Email address of the test user
            
        Returns:
            User data dictionary or None if not found
        """
        try:
            response = self.supabase.table("users")\
                .select("*")\
                .eq("email", email)\
                .eq("is_test_user", True)\
                .execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Failed to get test user by email: {str(e)}")
            return None
    
    def list_test_users(self) -> List[Dict[str, Any]]:
        """
        List all active test users
        
        Returns:
            List of test user records
        """
        try:
            response = self.supabase.table("users")\
                .select("*")\
                .eq("is_test_user", True)\
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Failed to list test users: {str(e)}")
            return []