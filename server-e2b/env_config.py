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
    
    # E2B Configuration
    E2B_API_KEY = os.getenv('E2B_API_KEY')
    E2B_TEMPLATE_ID = os.getenv('E2B_TEMPLATE_ID')
    
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
    


# Only validate required environment variables if not in test mode
if not (os.getenv('TESTING') or 'pytest' in sys.modules):
    Config.validate_required()