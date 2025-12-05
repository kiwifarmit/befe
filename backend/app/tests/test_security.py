"""Comprehensive security tests for API endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    current_active_user,
    current_superuser,
    get_user_manager,
)
from app.db import get_async_session
from app.main import app
from app.models import User, UserCredits


@pytest.mark.asyncio
async def test_non_superuser_cannot_list_users(client: AsyncClient):
    """Test that non-superuser cannot list all users."""
    # Create mock non-superuser
    mock_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="user@example.com",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )

    async def mock_current_active_user():
        return mock_user

    app.dependency_overrides[current_active_user] = mock_current_active_user

    try:
        response = await client.get("/users")
        assert response.status_code == 403
        assert "Only superusers can list all users" in response.json()["detail"]
    finally:
        if current_active_user in app.dependency_overrides:
            del app.dependency_overrides[current_active_user]


@pytest.mark.asyncio
async def test_superuser_can_list_users(client: AsyncClient):
    """Test that superuser can list all users."""
    # Create mock superuser
    mock_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="admin@example.com",
        is_active=True,
        is_superuser=True,
        is_verified=True,
    )

    # Mock session
    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.unique.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def mock_current_active_user():
        return mock_user

    async def mock_get_async_session():
        yield mock_session

    app.dependency_overrides[current_active_user] = mock_current_active_user
    app.dependency_overrides[get_async_session] = mock_get_async_session

    try:
        response = await client.get("/users")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        if current_active_user in app.dependency_overrides:
            del app.dependency_overrides[current_active_user]
        if get_async_session in app.dependency_overrides:
            del app.dependency_overrides[get_async_session]


@pytest.mark.asyncio
async def test_non_superuser_cannot_get_user_by_id(client: AsyncClient):
    """Test that non-superuser cannot get another user by ID."""

    async def mock_current_superuser():
        # This will raise 403 because user is not superuser
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    app.dependency_overrides[current_superuser] = mock_current_superuser

    try:
        target_user_id = uuid.UUID("660e8400-e29b-41d4-a716-446655440001")
        response = await client.get(f"/users/{target_user_id}")
        assert response.status_code == 403
    finally:
        if current_superuser in app.dependency_overrides:
            del app.dependency_overrides[current_superuser]


@pytest.mark.asyncio
async def test_non_superuser_cannot_update_user(client: AsyncClient):
    """Test that non-superuser cannot update another user."""

    async def mock_current_superuser():
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    app.dependency_overrides[current_superuser] = mock_current_superuser

    try:
        target_user_id = uuid.UUID("660e8400-e29b-41d4-a716-446655440001")
        response = await client.patch(
            f"/users/{target_user_id}", json={"email": "hacked@example.com"}
        )
        assert response.status_code == 403
    finally:
        if current_superuser in app.dependency_overrides:
            del app.dependency_overrides[current_superuser]


@pytest.mark.asyncio
async def test_non_superuser_cannot_delete_user(client: AsyncClient):
    """Test that non-superuser cannot delete another user."""

    async def mock_current_superuser():
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    app.dependency_overrides[current_superuser] = mock_current_superuser

    try:
        target_user_id = uuid.UUID("660e8400-e29b-41d4-a716-446655440001")
        response = await client.delete(f"/users/{target_user_id}")
        assert response.status_code == 403
    finally:
        if current_superuser in app.dependency_overrides:
            del app.dependency_overrides[current_superuser]


@pytest.mark.asyncio
async def test_non_superuser_cannot_update_credits(client: AsyncClient):
    """Test that non-superuser cannot update user credits."""
    # Create mock non-superuser
    mock_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="user@example.com",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )

    # Mock session
    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def mock_current_active_user():
        return mock_user

    async def mock_get_async_session():
        yield mock_session

    app.dependency_overrides[current_active_user] = mock_current_active_user
    app.dependency_overrides[get_async_session] = mock_get_async_session

    try:
        target_user_id = uuid.UUID("660e8400-e29b-41d4-a716-446655440001")
        response = await client.patch(
            f"/api/users/{target_user_id}/credits", json={"credits": 1000}
        )
        assert response.status_code == 403
        assert "Only superusers can update credits" in response.json()["detail"]
    finally:
        if current_active_user in app.dependency_overrides:
            del app.dependency_overrides[current_active_user]
        if get_async_session in app.dependency_overrides:
            del app.dependency_overrides[get_async_session]


@pytest.mark.asyncio
async def test_patch_users_me_is_blocked(client: AsyncClient):
    """Test that PATCH /users/me is blocked."""
    # Create mock user
    mock_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="user@example.com",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )

    async def mock_current_active_user():
        return mock_user

    app.dependency_overrides[current_active_user] = mock_current_active_user

    try:
        response = await client.patch(
            "/users/me", json={"email": "newemail@example.com"}
        )
        assert response.status_code == 403
        assert "PATCH /users/me is not allowed" in response.json()["detail"]
        assert "/users/me/password" in response.json()["detail"]
    finally:
        if current_active_user in app.dependency_overrides:
            del app.dependency_overrides[current_active_user]


@pytest.mark.asyncio
async def test_superuser_cannot_delete_self(client: AsyncClient):
    """Test that superuser cannot delete their own account."""
    # Create mock superuser
    mock_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="admin@example.com",
        is_active=True,
        is_superuser=True,
        is_verified=True,
    )

    # Mock session
    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def mock_current_superuser():
        return mock_user

    async def mock_get_async_session():
        yield mock_session

    # Mock user_manager.delete
    from app.auth import UserManager

    mock_user_manager = MagicMock(spec=UserManager)
    mock_user_manager.delete = AsyncMock()

    async def mock_get_user_manager():
        yield mock_user_manager

    app.dependency_overrides[current_superuser] = mock_current_superuser
    app.dependency_overrides[get_async_session] = mock_get_async_session
    app.dependency_overrides[get_user_manager] = mock_get_user_manager

    try:
        # Try to delete own account
        response = await client.delete(f"/users/{mock_user.id}")
        assert response.status_code == 400
        assert "Cannot delete your own account" in response.json()["detail"]
    finally:
        if current_superuser in app.dependency_overrides:
            del app.dependency_overrides[current_superuser]
        if get_async_session in app.dependency_overrides:
            del app.dependency_overrides[get_async_session]
        if get_user_manager in app.dependency_overrides:
            del app.dependency_overrides[get_user_manager]


@pytest.mark.asyncio
async def test_business_endpoint_requires_auth(client: AsyncClient):
    """Test that business endpoints require authentication."""
    # No authentication provided
    response = await client.post("/api/sum", json={"a": 10, "b": 20})
    assert response.status_code in [401, 403, 422]  # Should fail without auth


@pytest.mark.asyncio
async def test_business_endpoint_validates_input(client: AsyncClient):
    """Test that business endpoints validate input ranges."""
    # Create mock user
    mock_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="user@example.com",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )

    async def mock_current_active_user():
        return mock_user

    app.dependency_overrides[current_active_user] = mock_current_active_user

    try:
        # Test invalid input (out of range)
        response = await client.post("/api/sum", json={"a": 2000, "b": 20})
        assert response.status_code == 422  # Validation error
    finally:
        if current_active_user in app.dependency_overrides:
            del app.dependency_overrides[current_active_user]


@pytest.mark.asyncio
async def test_business_endpoint_checks_credits(client: AsyncClient):
    """Test that business endpoints check credits before operation."""
    # Create mock user
    mock_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="user@example.com",
        is_active=True,
        is_superuser=False,
        is_verified=True,
    )

    # Mock UserCredits with 0 credits
    mock_user_credits = MagicMock(spec=UserCredits)
    mock_user_credits.credits = 0
    mock_user_credits.user_id = mock_user.id

    # Mock session
    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user_credits
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()

    async def mock_current_active_user():
        return mock_user

    async def mock_get_async_session():
        yield mock_session

    app.dependency_overrides[current_active_user] = mock_current_active_user
    app.dependency_overrides[get_async_session] = mock_get_async_session

    try:
        response = await client.post("/api/sum", json={"a": 10, "b": 20})
        assert response.status_code == 403
        assert "Insufficient credits" in response.json()["detail"]
    finally:
        if current_active_user in app.dependency_overrides:
            del app.dependency_overrides[current_active_user]
        if get_async_session in app.dependency_overrides:
            del app.dependency_overrides[get_async_session]
