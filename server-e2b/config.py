"""Configuration module - minimal backward compatibility wrapper."""
# Import from centralized configuration
from env_config import Config

# Re-export only E2B and API configurations for backward compatibility
# Docker-related configurations have been removed as they are no longer used
E2B_API_KEY = Config.E2B_API_KEY
E2B_TEMPLATE_ID = Config.E2B_TEMPLATE_ID
ANTHROPIC_API_KEY = Config.ANTHROPIC_API_KEY
OPENAI_API_KEY = Config.OPENAI_API_KEY