"""Test to ensure update_user_credits endpoint exists and is secure."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.credits import router, update_user_credits
from app.auth import current_active_user
from app.db import get_async_session
from app.main import app
from app.models import User, UserCredits


def test_update_credits_endpoint_exists():
    """Ensure the update_user_credits endpoint exists in the router."""
    routes = [r for r in router.routes if hasattr(r, "path") and "credits" in r.path]
    assert len(routes) > 0, "update_user_credits endpoint is missing!"

    credits_route = routes[0]
    assert "/users/{user_id}/credits" in credits_route.path
    assert "PATCH" in credits_route.methods


def test_update_credits_endpoint_function_exists():
    """Ensure the update_user_credits function exists."""
    assert update_user_credits is not None
    assert callable(update_user_credits)


@pytest.mark.asyncio
async def test_update_credits_creates_new_user_credits(client: AsyncClient):
    """Test that update_user_credits creates UserCredits if it doesn't exist."""
    # Create mock superuser
    mock_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="admin@example.com",
        is_active=True,
        is_superuser=True,
        is_verified=True,
    )

    target_user_id = uuid.UUID("660e8400-e29b-41d4-a716-446655440001")

    # Mock session - no UserCredits exists
    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # No UserCredits found
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()

    async def mock_current_active_user():
        return mock_user

    async def mock_get_async_session():
        yield mock_session

    app.dependency_overrides[current_active_user] = mock_current_active_user
    app.dependency_overrides[get_async_session] = mock_get_async_session

    try:
        response = await client.patch(
            f"/api/users/{target_user_id}/credits", json={"credits": 100}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["credits"] == 100
        # Verify insert was called
        assert mock_session.execute.call_count >= 2  # select + insert
        mock_session.commit.assert_called_once()
    finally:
        if current_active_user in app.dependency_overrides:
            del app.dependency_overrides[current_active_user]
        if get_async_session in app.dependency_overrides:
            del app.dependency_overrides[get_async_session]


@pytest.mark.asyncio
async def test_update_credits_updates_existing_user_credits(client: AsyncClient):
    """Test that update_user_credits updates existing UserCredits."""
    # Create mock superuser
    mock_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="admin@example.com",
        is_active=True,
        is_superuser=True,
        is_verified=True,
    )

    target_user_id = uuid.UUID("660e8400-e29b-41d4-a716-446655440001")

    # Mock existing UserCredits
    mock_user_credits = MagicMock(spec=UserCredits)
    mock_user_credits.user_id = target_user_id
    mock_user_credits.credits = 50

    # Mock session
    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user_credits
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()

    async def mock_current_active_user():
        return mock_user

    async def mock_get_async_session():
        yield mock_session

    app.dependency_overrides[current_active_user] = mock_current_active_user
    app.dependency_overrides[get_async_session] = mock_get_async_session

    try:
        response = await client.patch(
            f"/api/users/{target_user_id}/credits", json={"credits": 200}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["credits"] == 200
        # Verify update was called
        assert mock_session.execute.call_count >= 2  # select + update
        mock_session.commit.assert_called_once()
    finally:
        if current_active_user in app.dependency_overrides:
            del app.dependency_overrides[current_active_user]
        if get_async_session in app.dependency_overrides:
            del app.dependency_overrides[get_async_session]
