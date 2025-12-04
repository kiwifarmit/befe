import asyncio
import logging
from io import StringIO
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Create mock file handler using StringIO to avoid file I/O issues
mock_file_handler = logging.StreamHandler(StringIO())
mock_console_handler = logging.StreamHandler()

# Mock logging setup before importing app to avoid file handler issues
with patch("os.path.exists", return_value=True):
    with patch("os.makedirs"):
        with patch(
            "logging.handlers.RotatingFileHandler", return_value=mock_file_handler
        ):
            from app.main import app

            # Override TrustedHostMiddleware to allow "test" host for testing
            # Find and replace the middleware
            for i, middleware in enumerate(app.user_middleware):
                if hasattr(middleware, "cls") and "TrustedHost" in str(middleware.cls):
                    from fastapi.middleware.trustedhost import TrustedHostMiddleware

                    app.user_middleware[i] = type(middleware)(
                        TrustedHostMiddleware,
                        allowed_hosts=[
                            "localhost",
                            "127.0.0.1",
                            "0.0.0.0",
                            "nginx",
                            "test",
                            "testserver",
                        ],
                    )
                    break


@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    """Setup test logging to avoid file handler issues."""
    # Clear any existing handlers that might have file I/O issues
    root_logger = logging.getLogger()
    handlers_to_remove = []
    for handler in root_logger.handlers[:]:
        # Remove RotatingFileHandler instances that might have file issues
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            handlers_to_remove.append(handler)

    for handler in handlers_to_remove:
        root_logger.removeHandler(handler)

    yield

    # No cleanup needed - let handlers persist for other tests


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
