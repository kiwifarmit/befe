from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.main import app, lifespan


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


@pytest.mark.asyncio
async def test_lifespan_startup():
    """Test lifespan startup event."""
    mock_init_db = AsyncMock()

    with patch("app.main.init_db", mock_init_db):
        async with lifespan(app):
            pass

    mock_init_db.assert_called_once()
