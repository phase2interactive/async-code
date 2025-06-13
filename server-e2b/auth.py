import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify
from database import DatabaseOperations
from env_config import Config


def generate_tokens(user_id: str) -> dict:
    """
    Generate access and refresh tokens for a user.
    
    Args:
        user_id: The user's ID from Supabase
        
    Returns:
        dict: Contains access_token and refresh_token
    """
    now = datetime.now(timezone.utc)
    
    # Access token payload
    access_payload = {
        'user_id': user_id,
        'type': 'access',
        'exp': now + timedelta(minutes=Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        'iat': now
    }
    
    # Refresh token payload
    refresh_payload = {
        'user_id': user_id,
        'type': 'refresh',
        'exp': now + timedelta(days=Config.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        'iat': now
    }
    
    access_token = jwt.encode(access_payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60  # in seconds
    }


def verify_token(token: str, token_type: str = 'access') -> dict:
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token to verify
        token_type: Either 'access' or 'refresh'
        
    Returns:
        dict: The decoded token payload
        
    Raises:
        jwt.InvalidTokenError: If the token is invalid
    """
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        
        # Verify token type
        if payload.get('type') != token_type:
            raise jwt.InvalidTokenError(f'Invalid token type. Expected {token_type}')
            
        return payload
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError('Token has expired')
    except jwt.InvalidTokenError:
        raise


def get_current_user_id(token: str) -> str:
    """
    Extract user_id from a valid access token.
    
    Args:
        token: The JWT access token
        
    Returns:
        str: The user_id from the token
        
    Raises:
        jwt.InvalidTokenError: If the token is invalid
    """
    payload = verify_token(token, 'access')
    return payload['user_id']


def require_auth(f):
    """
    Decorator to require authentication for an endpoint.
    
    Extracts the JWT token from the Authorization header,
    validates it, and adds the user_id to the request context.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'Missing authorization header'}), 401
            
        # Extract token from "Bearer <token>" format
        try:
            scheme, token = auth_header.split(' ')
            if scheme.lower() != 'bearer':
                return jsonify({'error': 'Invalid authentication scheme'}), 401
        except ValueError:
            return jsonify({'error': 'Invalid authorization header format'}), 401
            
        # Verify token
        try:
            user_id = get_current_user_id(token)
            
            # Verify user exists in database
            user = DatabaseOperations.get_user_by_id(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 401
                
            # Add user_id to request context
            request.user_id = user_id
            
        except jwt.InvalidTokenError as e:
            return jsonify({'error': str(e)}), 401
        except Exception as e:
            return jsonify({'error': 'Authentication failed'}), 401
            
        return f(*args, **kwargs)
        
    return decorated_function


def refresh_access_token(refresh_token: str) -> dict:
    """
    Generate a new access token using a valid refresh token.
    
    Args:
        refresh_token: The refresh token
        
    Returns:
        dict: Contains new access_token and expires_in
        
    Raises:
        jwt.InvalidTokenError: If the refresh token is invalid
    """
    payload = verify_token(refresh_token, 'refresh')
    user_id = payload['user_id']
    
    # Verify user still exists
    user = DatabaseOperations.get_user_by_id(user_id)
    if not user:
        raise jwt.InvalidTokenError('User not found')
    
    # Generate new access token only
    now = datetime.now(timezone.utc)
    access_payload = {
        'user_id': user_id,
        'type': 'access',
        'exp': now + timedelta(minutes=Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        'iat': now
    }
    
    access_token = jwt.encode(access_payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
    
    return {
        'access_token': access_token,
        'expires_in': Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }