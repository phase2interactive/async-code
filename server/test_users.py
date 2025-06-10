"""
Test User API Endpoints

This module provides API endpoints for managing test users
in development and testing environments.
"""

import os
from datetime import timedelta
from flask import Blueprint, jsonify, request, current_app
from functools import wraps
from pydantic import ValidationError

from test_user_service import TestUserService, TestUser
from auth import generate_tokens
from test_user_models import (
    TestUserCreateRequest,
    TestUserCreateResponse,
    TestUserResponse,
    TokensResponse,
    TestUserListResponse,
    CleanupResponse,
    ErrorResponse,
    HealthResponse
)

# Create blueprint
test_users_bp = Blueprint('test_users', __name__)

# Rate limiting configuration
RATE_LIMITS = {
    'create': '10 per hour',      # Max 10 test users per hour
    'delete': '20 per hour',      # Max 20 deletions per hour  
    'list': '60 per hour',        # Max 60 list requests per hour
    'cleanup': '5 per hour',      # Max 5 cleanup operations per hour
    'refresh': '30 per hour'      # Max 30 token refreshes per hour
}

# Initialize service (lazy loading)
_test_user_service = None

def get_test_user_service():
    """Get or create test user service instance"""
    global _test_user_service
    if _test_user_service is None:
        _test_user_service = TestUserService()
    return _test_user_service


def require_test_mode(f):
    """Decorator to ensure endpoints only work in test mode"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if we're in test mode
        if os.environ.get("ENVIRONMENT") == "production":
            return jsonify({"error": "Test user endpoints are disabled in production"}), 403
        
        # Additional check for test environment flag
        if not os.environ.get("ENABLE_TEST_USERS", "false").lower() == "true":
            return jsonify({"error": "Test user endpoints are not enabled"}), 403
            
        return f(*args, **kwargs)
    return decorated_function


@test_users_bp.route('/test-users', methods=['POST'])
@require_test_mode
def create_test_user():
    """
    Create a new test user
    
    Request body (optional):
    {
        "email": "custom@test.test",  // Optional, defaults to test@asynccode.test
        "user_id": "specific-uuid",    // Optional, auto-generated if not provided
        "metadata": {                  // Optional additional metadata
            "test_scenario": "auth_flow"
        }
    }
    
    Response:
    {
        "user": {
            "id": "uuid",
            "email": "test@asynccode.test",
            "created_at": "2024-01-01T00:00:00Z",
            "metadata": {},
            "expires_at": "2024-01-01T01:00:00Z"
        },
        "tokens": {
            "access_token": "jwt...",
            "refresh_token": "jwt..."
        }
    }
    """
    try:
        service = get_test_user_service()
        
        # Parse and validate request data
        data = request.get_json() or {}
        try:
            request_data = TestUserCreateRequest(**data)
        except ValidationError as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        
        # Create test user
        test_user = service.create_test_user(
            email=request_data.email,
            user_id=request_data.user_id,
            metadata=request_data.metadata
        )
        
        # Build response using Pydantic models
        response = TestUserCreateResponse(
            user=TestUserResponse(
                id=test_user.id,
                email=test_user.email,
                created_at=test_user.created_at,
                metadata=test_user.metadata,
                expires_at=test_user.created_at + timedelta(hours=1)
            ),
            tokens=TokensResponse(
                access_token=test_user.access_token,
                refresh_token=test_user.refresh_token
            )
        )
        
        return jsonify(response.model_dump(mode='json')), 201
        
    except ValueError as e:
        return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
    except Exception as e:
        return jsonify(ErrorResponse(error=f"Failed to create test user: {str(e)}").model_dump()), 500


@test_users_bp.route('/test-users/<user_id>', methods=['DELETE'])
@require_test_mode
def delete_test_user(user_id):
    """
    Delete a test user and all associated data
    
    Response:
    {
        "message": "Test user deleted successfully"
    }
    """
    try:
        service = get_test_user_service()
        
        if service.delete_test_user(user_id):
            return jsonify({"message": "Test user deleted successfully"}), 200
        else:
            return jsonify(ErrorResponse(error="Failed to delete test user").model_dump()), 500
            
    except ValueError as e:
        return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
    except Exception as e:
        return jsonify(ErrorResponse(error=f"Failed to delete test user: {str(e)}").model_dump()), 500


@test_users_bp.route('/test-users', methods=['GET'])
@require_test_mode
def list_test_users():
    """
    List all active test users
    
    Response:
    {
        "users": [
            {
                "id": "uuid",
                "email": "test@asynccode.test",
                "created_at": "2024-01-01T00:00:00Z",
                "expires_at": "2024-01-01T01:00:00Z",
                "is_test_user": true
            }
        ]
    }
    """
    try:
        service = get_test_user_service()
        users = service.list_test_users()
        
        response = TestUserListResponse(users=users)
        return jsonify(response.model_dump()), 200
        
    except Exception as e:
        return jsonify(ErrorResponse(error=f"Failed to list test users: {str(e)}").model_dump()), 500


@test_users_bp.route('/test-users/cleanup', methods=['POST'])
@require_test_mode
def cleanup_test_users():
    """
    Clean up expired test users
    
    Response:
    {
        "message": "Cleaned up 3 expired test users",
        "deleted_users": ["uuid1", "uuid2", "uuid3"]
    }
    """
    try:
        service = get_test_user_service()
        deleted_users = service.cleanup_expired_test_users()
        
        response = CleanupResponse(
            message=f"Cleaned up {len(deleted_users)} expired test users",
            deleted_users=deleted_users
        )
        return jsonify(response.model_dump()), 200
        
    except Exception as e:
        return jsonify(ErrorResponse(error=f"Failed to cleanup test users: {str(e)}").model_dump()), 500


@test_users_bp.route('/test-users/<user_id>/token', methods=['POST'])
@require_test_mode
def refresh_test_user_token(user_id):
    """
    Generate new tokens for a test user
    
    Response:
    {
        "tokens": {
            "access_token": "jwt...",
            "refresh_token": "jwt..."
        }
    }
    """
    try:
        service = get_test_user_service()
        
        # Verify user exists and is a test user
        user = service.supabase.table("users")\
            .select("*")\
            .eq("id", user_id)\
            .eq("is_test_user", True)\
            .execute()
            
        if not user.data:
            return jsonify(ErrorResponse(error="Test user not found").model_dump()), 404
        
        # Generate new tokens
        access_token = service.generate_jwt_token(user_id, "access")
        refresh_token = service.generate_jwt_token(user_id, "refresh")
        
        response = TokensResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
        
        return jsonify({"tokens": response.model_dump()}), 200
        
    except Exception as e:
        return jsonify(ErrorResponse(error=f"Failed to refresh tokens: {str(e)}").model_dump()), 500


# Health check endpoint
@test_users_bp.route('/test-users/health', methods=['GET'])
def test_users_health():
    """Check if test user service is healthy"""
    try:
        # Check if test mode is enabled
        test_mode_enabled = os.environ.get("ENABLE_TEST_USERS", "false").lower() == "true"
        
        # Try to initialize service if in test mode
        if test_mode_enabled:
            service = get_test_user_service()
            service_healthy = service is not None
        else:
            service_healthy = False
        
        response = HealthResponse(
            healthy=True,
            test_mode_enabled=test_mode_enabled,
            service_initialized=service_healthy
        )
        return jsonify(response.model_dump()), 200
        
    except Exception as e:
        response = HealthResponse(
            healthy=False,
            test_mode_enabled=False,
            service_initialized=False
        )
        return jsonify(response.model_dump()), 500