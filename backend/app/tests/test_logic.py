import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.db import get_async_session
from app.main import app
from app.models import User, UserCredits


@pytest.mark.asyncio
async def test_sum_endpoint(client: AsyncClient):
    """Test sum endpoint with mocked database session."""
    # Create mock user
    mock_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="test@example.com",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )

    # Create a mock UserCredits object
    mock_user_credits = MagicMock(spec=UserCredits)
    mock_user_credits.credits = 10
    mock_user_credits.user_id = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")

    # Mock the database session and query result
    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user_credits
    mock_execute = AsyncMock(return_value=mock_result)
    mock_session.execute = mock_execute
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    # Override dependencies
    async def mock_current_active_user():
        return mock_user

    async def mock_get_async_session():
        yield mock_session

    app.dependency_overrides[current_active_user] = mock_current_active_user
    app.dependency_overrides[get_async_session] = mock_get_async_session

    try:
        response = await client.post("/api/sum", json={"a": 10, "b": 20})
        assert response.status_code == 200
        assert response.json() == {"result": 30}

        # Verify credits were deducted
        assert mock_user_credits.credits == 9
        mock_session.commit.assert_called_once()
    finally:
        # Clean up dependency overrides
        if current_active_user in app.dependency_overrides:
            del app.dependency_overrides[current_active_user]
        if get_async_session in app.dependency_overrides:
            del app.dependency_overrides[get_async_session]


@pytest.mark.asyncio
async def test_sum_endpoint_validation(client: AsyncClient):
    """Test sum endpoint validation - FastAPI returns 422 for validation errors."""
    # Create mock user for authentication
    mock_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="test@example.com",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )

    async def mock_current_active_user():
        return mock_user

    app.dependency_overrides[current_active_user] = mock_current_active_user

    try:
        response = await client.post("/api/sum", json={"a": 2000, "b": 20})
        # FastAPI returns 422 Unprocessable Entity for Pydantic validation errors
        assert response.status_code == 422
    finally:
        if current_active_user in app.dependency_overrides:
            del app.dependency_overrides[current_active_user]
