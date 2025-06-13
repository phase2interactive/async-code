"""
Pydantic models for Test User API validation

This module defines request and response models for the test user endpoints
to ensure data consistency and validation.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from email_validator import validate_email, EmailNotValidError


class TestUserCreateRequest(BaseModel):
    """Request model for creating a test user"""
    email: Optional[str] = Field(None, description="Test user email (must use .test TLD)")
    user_id: Optional[str] = Field(None, description="Specific user ID to use")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('email')
    def validate_test_email(cls, v):
        """Ensure email uses .test TLD and has valid format"""
        if v:
            # Check basic email format
            if '@' not in v:
                raise ValueError('Invalid email format')
            # Ensure it uses .test TLD
            if not v.endswith('.test'):
                raise ValueError('Test user email must use .test TLD for safety')
        return v


class TestUserResponse(BaseModel):
    """Response model for test user data"""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    created_at: datetime = Field(..., description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="User metadata")
    expires_at: datetime = Field(..., description="Expiration timestamp")


class TokensResponse(BaseModel):
    """Response model for JWT tokens"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")


class TestUserCreateResponse(BaseModel):
    """Response model for test user creation"""
    user: TestUserResponse
    tokens: TokensResponse


class TestUserListResponse(BaseModel):
    """Response model for listing test users"""
    users: list[Dict[str, Any]] = Field(..., description="List of test users")


class CleanupResponse(BaseModel):
    """Response model for cleanup operations"""
    message: str = Field(..., description="Cleanup result message")
    deleted_users: list[str] = Field(..., description="IDs of deleted users")


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str = Field(..., description="Error message")


class HealthResponse(BaseModel):
    """Health check response model"""
    healthy: bool = Field(..., description="Service health status")
    test_mode_enabled: bool = Field(..., description="Whether test mode is enabled")
    service_initialized: bool = Field(..., description="Whether service is initialized")