"""
Centralized environment configuration for the application.
All environment variables should be accessed through this module.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for all environment variables."""
    
    # Database Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Authentication Configuration
    JWT_SECRET = os.getenv('JWT_SECRET')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '60'))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '7'))
    
    # API Keys
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # Container Configuration
    CONTAINER_UID = int(os.getenv('CONTAINER_UID', '1000'))
    CONTAINER_GID = int(os.getenv('CONTAINER_GID', '1000'))
    CONTAINER_USER = f"{CONTAINER_UID}:{CONTAINER_GID}"
    CONTAINER_MEM_LIMIT = os.getenv('CONTAINER_MEM_LIMIT', '2g')
    CONTAINER_CPU_SHARES = int(os.getenv('CONTAINER_CPU_SHARES', '1024'))
    
    # Security Configuration
    CONTAINER_SECURITY_OPTS = ['no-new-privileges=true']
    CONTAINER_READ_ONLY = os.getenv('CONTAINER_READ_ONLY', 'false').lower() == 'true'
    
    # Workspace Configuration
    WORKSPACE_BASE_PATH = os.getenv('WORKSPACE_BASE_PATH', '/tmp')
    WORKSPACE_PREFIX = 'ai-workspace-'
    
    # Application Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    PORT = int(os.getenv('PORT', '5000'))
    
    @classmethod
    def validate_required(cls):
        """Validate that all required environment variables are set."""
        required_vars = {
            'SUPABASE_URL': cls.SUPABASE_URL,
            'SUPABASE_SERVICE_ROLE_KEY': cls.SUPABASE_SERVICE_ROLE_KEY,
            'JWT_SECRET': cls.JWT_SECRET,
        }
        
        missing_vars = []
        for var_name, var_value in required_vars.items():
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    @classmethod
    def get_container_user_mapping(cls):
        """Get the user mapping for containers."""
        return cls.CONTAINER_USER
    
    @classmethod
    def get_workspace_path(cls, task_id):
        """Get the workspace path for a specific task."""
        return os.path.join(cls.WORKSPACE_BASE_PATH, f"{cls.WORKSPACE_PREFIX}{task_id}")
    
    @classmethod
    def get_security_options(cls):
        """Get the security options for containers."""
        return cls.CONTAINER_SECURITY_OPTS.copy()


# Only validate required environment variables if not in test mode
if not (os.getenv('TESTING') or 'pytest' in sys.modules):
    Config.validate_required()