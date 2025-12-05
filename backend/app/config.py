"""Application configuration from environment variables."""

import logging
import os
from pathlib import Path

# Try to load .env file if python-dotenv is available (for local development)
# Look for .env in project root (parent of backend directory)
try:
    from dotenv import load_dotenv

    # Try multiple possible .env locations
    # 1. Project root (parent of backend/)
    backend_dir = Path(__file__).parent.parent.parent
    env_file = backend_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # 2. Current directory
        load_dotenv()
except ImportError:
    # python-dotenv not installed, skip (Docker passes env vars directly)
    pass

logger = logging.getLogger(__name__)

# Cache the value to avoid repeated env lookups
_default_credits_cache: int | None = None


def get_default_user_credits() -> int:
    """
    Get default credits for new users from environment variable.

    Reads from DEFAULT_USER_CREDITS environment variable.
    In Docker, this comes from docker-compose.yml.
    For local development, can be set in .env file (requires python-dotenv).

    Returns:
        int: Default credits value (defaults to 10 if not set)
    """
    global _default_credits_cache

    if _default_credits_cache is not None:
        return _default_credits_cache

    default_credits_str = os.getenv("DEFAULT_USER_CREDITS", "10")
    try:
        default_credits = int(default_credits_str)
        _default_credits_cache = default_credits
        logger.info(
            f"Default user credits configured: {default_credits} "
            f"(from DEFAULT_USER_CREDITS env var: {default_credits_str})"
        )
        return default_credits
    except ValueError:
        # If invalid value, return default and log warning
        logger.warning(
            f"Invalid DEFAULT_USER_CREDITS value: '{default_credits_str}'. "
            "Using default value: 10"
        )
        _default_credits_cache = 10
        return 10
