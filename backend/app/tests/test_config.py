"""Tests for app/config.py to increase coverage."""

import os
from unittest.mock import patch


def test_get_default_user_credits_from_env():
    """Test get_default_user_credits reads from environment variable."""
    # Clear cache
    import app.config
    from app.config import get_default_user_credits

    app.config._default_credits_cache = None

    with patch.dict(os.environ, {"DEFAULT_USER_CREDITS": "25"}):
        result = get_default_user_credits()
        assert result == 25


def test_get_default_user_credits_default_value():
    """Test get_default_user_credits returns default when env var not set."""
    # Clear cache
    import app.config
    from app.config import get_default_user_credits

    app.config._default_credits_cache = None

    with patch.dict(os.environ, {}, clear=True):
        # Remove DEFAULT_USER_CREDITS if it exists
        os.environ.pop("DEFAULT_USER_CREDITS", None)
        result = get_default_user_credits()
        assert result == 10  # Default value


def test_get_default_user_credits_invalid_value():
    """Test get_default_user_credits handles invalid env var value."""
    # Clear cache
    import app.config
    from app.config import get_default_user_credits

    app.config._default_credits_cache = None

    with patch.dict(os.environ, {"DEFAULT_USER_CREDITS": "invalid"}):
        result = get_default_user_credits()
        assert result == 10  # Should fall back to default


def test_get_default_user_credits_caching():
    """Test that get_default_user_credits caches the value."""
    # Clear cache
    import app.config
    from app.config import get_default_user_credits

    app.config._default_credits_cache = None

    with patch.dict(os.environ, {"DEFAULT_USER_CREDITS": "30"}):
        result1 = get_default_user_credits()
        # Change env var - should still return cached value
        with patch.dict(os.environ, {"DEFAULT_USER_CREDITS": "40"}):
            result2 = get_default_user_credits()
            assert result1 == result2 == 30  # Should use cached value


def test_get_default_user_credits_dotenv_loading():
    """Test that dotenv loading is attempted (if available)."""
    # This test verifies that the config module can be imported
    # whether or not dotenv is available
    # The actual dotenv loading happens at module import time
    # and is already tested by the fact that the module imports successfully
    # Clear cache
    import app.config
    from app.config import get_default_user_credits

    app.config._default_credits_cache = None

    # Test that function works regardless of dotenv availability
    # If dotenv is available, it will be used; if not, env vars from system are used
    result = get_default_user_credits()
    assert isinstance(result, int)
    assert result > 0
