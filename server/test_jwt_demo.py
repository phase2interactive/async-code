#!/usr/bin/env python3
"""
Simple demonstration of JWT authentication functionality
"""

import os
import jwt
from datetime import datetime, timedelta, timezone

# JWT configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-very-secure-secret-key-change-this-in-production-minimum-32-chars')
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7


def generate_tokens(user_id: str) -> dict:
    """Generate access and refresh tokens for a user."""
    now = datetime.now(timezone.utc)
    
    # Access token payload
    access_payload = {
        'user_id': user_id,
        'type': 'access',
        'exp': now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        'iat': now
    }
    
    # Refresh token payload
    refresh_payload = {
        'user_id': user_id,
        'type': 'refresh',
        'exp': now + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        'iat': now
    }
    
    access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60  # in seconds
    }


def verify_token(token: str, token_type: str = 'access') -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Verify token type
        if payload.get('type') != token_type:
            raise jwt.InvalidTokenError(f'Invalid token type. Expected {token_type}')
            
        return payload
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError('Token has expired')
    except jwt.InvalidTokenError:
        raise


def main():
    print("JWT Authentication Demonstration")
    print("=" * 50)
    
    # Test user ID
    test_user_id = "550e8400-e29b-41d4-a716-446655440000"
    print(f"\nTest User ID: {test_user_id}")
    
    # Generate tokens
    print("\n1. Generating JWT tokens...")
    tokens = generate_tokens(test_user_id)
    print(f"   Access Token (truncated): {tokens['access_token'][:50]}...")
    print(f"   Refresh Token (truncated): {tokens['refresh_token'][:50]}...")
    print(f"   Expires in: {tokens['expires_in']} seconds")
    
    # Verify access token
    print("\n2. Verifying access token...")
    try:
        access_payload = verify_token(tokens['access_token'], 'access')
        print(f"   ✓ Valid access token")
        print(f"   User ID: {access_payload['user_id']}")
        print(f"   Type: {access_payload['type']}")
        print(f"   Expires: {datetime.fromtimestamp(access_payload['exp'], tz=timezone.utc)}")
    except jwt.InvalidTokenError as e:
        print(f"   ✗ Invalid token: {e}")
    
    # Verify refresh token
    print("\n3. Verifying refresh token...")
    try:
        refresh_payload = verify_token(tokens['refresh_token'], 'refresh')
        print(f"   ✓ Valid refresh token")
        print(f"   User ID: {refresh_payload['user_id']}")
        print(f"   Type: {refresh_payload['type']}")
        print(f"   Expires: {datetime.fromtimestamp(refresh_payload['exp'], tz=timezone.utc)}")
    except jwt.InvalidTokenError as e:
        print(f"   ✗ Invalid token: {e}")
    
    # Test invalid scenarios
    print("\n4. Testing invalid scenarios...")
    
    # Wrong token type
    print("   a. Using refresh token as access token:")
    try:
        verify_token(tokens['refresh_token'], 'access')
        print("      ✗ Should have failed!")
    except jwt.InvalidTokenError as e:
        print(f"      ✓ Correctly rejected: {e}")
    
    # Invalid token
    print("   b. Using invalid token:")
    try:
        verify_token('invalid.token.here', 'access')
        print("      ✗ Should have failed!")
    except jwt.InvalidTokenError as e:
        print(f"      ✓ Correctly rejected: Invalid token")
    
    # Expired token
    print("   c. Testing expired token:")
    expired_payload = {
        'user_id': test_user_id,
        'type': 'access',
        'exp': datetime.now(timezone.utc) - timedelta(hours=1),
        'iat': datetime.now(timezone.utc) - timedelta(hours=2)
    }
    expired_token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    try:
        verify_token(expired_token, 'access')
        print("      ✗ Should have failed!")
    except jwt.InvalidTokenError as e:
        print(f"      ✓ Correctly rejected: {e}")
    
    print("\n" + "=" * 50)
    print("JWT Authentication is working correctly! ✓")


if __name__ == "__main__":
    main()