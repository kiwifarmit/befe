"""Extended tests for app/main.py to increase coverage."""
import pytest
from httpx import AsyncClient
import uuid
import jwt
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import User, UserCredits
from app.auth import current_active_user, current_superuser, get_user_manager
from app.db import get_async_session
from app.auth import SECRET


@pytest.mark.asyncio
async def test_users_me_endpoint(client: AsyncClient):
    """Test /users/me endpoint with mocked user and session."""
    # Create mock user
    mock_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="test@example.com",
        is_active=True,
        is_superuser=False,
        is_verified=True
    )
    
    # Create mock UserCredits
    mock_user_credits = MagicMock(spec=UserCredits)
    mock_user_credits.credits = 15
    mock_user_credits.user_id = mock_user.id
    
    # Mock database session
    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user_credits
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    # Override dependencies
    async def mock_get_async_session():
        yield mock_session
    
    async def mock_current_active_user():
        return mock_user
    
    app.dependency_overrides[current_active_user] = mock_current_active_user
    app.dependency_overrides[get_async_session] = mock_get_async_session
    
    try:
        response = await client.get("/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["credits"] == 15
    finally:
        if current_active_user in app.dependency_overrides:
            del app.dependency_overrides[current_active_user]
        if get_async_session in app.dependency_overrides:
            del app.dependency_overrides[get_async_session]


@pytest.mark.asyncio
async def test_users_me_endpoint_creates_credits(client: AsyncClient):
    """Test /users/me endpoint creates UserCredits if it doesn't exist."""
    # Create mock user
    mock_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="test@example.com",
        is_active=True,
        is_superuser=False,
        is_verified=True
    )
    
    # Mock database session - no UserCredits exists
    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # No UserCredits found
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    # Override dependencies
    async def mock_get_async_session():
        yield mock_session
    
    async def mock_current_active_user():
        return mock_user
    
    app.dependency_overrides[current_active_user] = mock_current_active_user
    app.dependency_overrides[get_async_session] = mock_get_async_session
    
    try:
        response = await client.get("/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["credits"] == 10  # Default credits
        # Verify UserCredits was created
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
    finally:
        if current_active_user in app.dependency_overrides:
            del app.dependency_overrides[current_active_user]
        if get_async_session in app.dependency_overrides:
            del app.dependency_overrides[get_async_session]


@pytest.mark.asyncio
async def test_api_logging_middleware_with_token(client: AsyncClient):
    """Test API logging middleware with valid JWT token."""
    # Create a valid JWT token
    user_id = str(uuid.UUID("550e8400-e29b-41d4-a716-446655440000"))
    token = jwt.encode({"sub": user_id}, SECRET, algorithm="HS256")
    
    # Mock user for authentication
    mock_user = User(
        id=uuid.UUID(user_id),
        email="test@example.com",
        is_active=True,
        is_superuser=False,
        is_verified=True,
        hashed_password="hashed"
    )
    
    # Mock UserCredits
    mock_user_credits = MagicMock(spec=UserCredits)
    mock_user_credits.credits = 10
    mock_user_credits.user_id = mock_user.id
    
    # Mock session
    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user_credits
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    async def mock_get_async_session():
        yield mock_session
    
    async def mock_current_active_user():
        return mock_user
    
    app.dependency_overrides[current_active_user] = mock_current_active_user
    app.dependency_overrides[get_async_session] = mock_get_async_session
    
    try:
        # Make request with JWT token
        response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
    finally:
        if current_active_user in app.dependency_overrides:
            del app.dependency_overrides[current_active_user]
        if get_async_session in app.dependency_overrides:
            del app.dependency_overrides[get_async_session]


@pytest.mark.asyncio
async def test_api_logging_middleware_invalid_token(client: AsyncClient):
    """Test API logging middleware with invalid token."""
    # Make request with invalid token
    response = await client.post(
        "/api/sum",
        headers={"Authorization": "Bearer invalid_token"},
        json={"a": 10, "b": 20}
    )
    # Should fail authentication, but middleware should handle it
    assert response.status_code in [401, 403, 422]


@pytest.mark.asyncio
async def test_api_logging_middleware_no_auth(client: AsyncClient):
    """Test API logging middleware without authorization header."""
    # Make request without auth header
    response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_patch_users_me_password_only(client: AsyncClient):
    """Test PATCH /users/me endpoint allows password updates only."""
    # Create mock user
    mock_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="test@example.com",
        is_active=True,
        is_superuser=False,
        is_verified=True,
        hashed_password="old_hash"
    )
    
    # Create mock UserCredits
    mock_user_credits = MagicMock(spec=UserCredits)
    mock_user_credits.credits = 15
    mock_user_credits.user_id = mock_user.id
    
    # Mock database session
    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user_credits
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    # Mock UserManager
    mock_user_manager = MagicMock()
    updated_user = User(
        id=mock_user.id,
        email=mock_user.email,  # Email unchanged
        is_active=mock_user.is_active,
        is_superuser=mock_user.is_superuser,
        is_verified=mock_user.is_verified,
        hashed_password="new_hash"
    )
    mock_user_manager.update = AsyncMock(return_value=updated_user)
    
    # Override dependencies
    async def mock_get_async_session():
        yield mock_session
    
    async def mock_current_active_user():
        return mock_user
    
    async def mock_get_user_manager():
        yield mock_user_manager
    
    app.dependency_overrides[current_active_user] = mock_current_active_user
    app.dependency_overrides[get_async_session] = mock_get_async_session
    app.dependency_overrides[get_user_manager] = mock_get_user_manager
    
    try:
        response = await client.patch(
            "/users/me",
            json={"password": "NewPassword123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"  # Email unchanged
        assert data["credits"] == 15
        # Verify UserManager.update was called with safe=True
        mock_user_manager.update.assert_called_once()
        call_args = mock_user_manager.update.call_args
        assert call_args[1]["safe"] is True  # safe mode prevents email updates
    finally:
        for dep in [current_active_user, get_async_session, get_user_manager]:
            if dep in app.dependency_overrides:
                del app.dependency_overrides[dep]


@pytest.mark.asyncio
async def test_get_users_admin_only(client: AsyncClient):
    """Test GET /users endpoint requires admin access."""
    # Create admin user
    admin_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="admin@example.com",
        is_active=True,
        is_superuser=True,
        is_verified=True
    )
    
    # Create regular user
    regular_user = User(
        id=uuid.UUID("660e8400-e29b-41d4-a716-446655440001"),
        email="user@example.com",
        is_active=True,
        is_superuser=False,
        is_verified=True
    )
    
    # Mock database session
    mock_session = MagicMock(spec=AsyncSession)
    
    # Mock count query
    count_result = MagicMock()
    count_result.scalar.return_value = 2
    
    # Mock users query
    users_result = MagicMock()
    users_result.scalars.return_value.all.return_value = [admin_user, regular_user]
    
    # Mock UserCredits queries
    credits_result1 = MagicMock()
    credits_result1.scalar_one_or_none.return_value = MagicMock(
        spec=UserCredits,
        credits=10,
        user_id=admin_user.id
    )
    
    credits_result2 = MagicMock()
    credits_result2.scalar_one_or_none.return_value = MagicMock(
        spec=UserCredits,
        credits=20,
        user_id=regular_user.id
    )
    
    # Setup execute to return different results based on call order
    call_count = [0]
    def mock_execute_side_effect(query):
        call_count[0] += 1
        if call_count[0] == 1:
            return count_result  # Count query
        elif call_count[0] == 2:
            return users_result  # Users query
        elif call_count[0] == 3:
            return credits_result1  # Credits for admin_user
        else:
            return credits_result2  # Credits for regular_user
    
    mock_session.execute = AsyncMock(side_effect=mock_execute_side_effect)
    
    # Override dependencies
    async def mock_get_async_session():
        yield mock_session
    
    async def mock_current_superuser():
        return admin_user
    
    app.dependency_overrides[current_superuser] = mock_current_superuser
    app.dependency_overrides[get_async_session] = mock_get_async_session
    
    try:
        response = await client.get("/users?page=1&size=50")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert data["total"] == 2
        assert len(data["items"]) == 2
    finally:
        for dep in [current_superuser, get_async_session]:
            if dep in app.dependency_overrides:
                del app.dependency_overrides[dep]


@pytest.mark.asyncio
async def test_get_users_non_admin_forbidden(client: AsyncClient):
    """Test GET /users endpoint rejects non-admin users."""
    # Create regular user (not admin)
    regular_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="user@example.com",
        is_active=True,
        is_superuser=False,
        is_verified=True
    )
    
    # Override dependency - non-admin user
    async def mock_current_superuser():
        # This will raise 403 because user is not superuser
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a superuser")
    
    app.dependency_overrides[current_superuser] = mock_current_superuser
    
    try:
        response = await client.get("/users?page=1&size=50")
        assert response.status_code == 403
    finally:
        if current_superuser in app.dependency_overrides:
            del app.dependency_overrides[current_superuser]


@pytest.mark.asyncio
async def test_patch_users_id_with_credits(client: AsyncClient):
    """Test PATCH /users/{id} endpoint allows credits updates."""
    # Create admin user
    admin_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="admin@example.com",
        is_active=True,
        is_superuser=True,
        is_verified=True
    )
    
    # Create target user
    target_user = User(
        id=uuid.UUID("660e8400-e29b-41d4-a716-446655440001"),
        email="target@example.com",
        is_active=True,
        is_superuser=False,
        is_verified=True
    )
    
    # Mock UserCredits
    mock_user_credits = MagicMock(spec=UserCredits)
    mock_user_credits.credits = 10
    mock_user_credits.user_id = target_user.id
    
    # Mock database session
    mock_session = MagicMock(spec=AsyncSession)
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = target_user
    credits_result = MagicMock()
    credits_result.scalar_one_or_none.return_value = mock_user_credits
    
    def mock_execute_side_effect(query):
        if "user.id" in str(query):
            return user_result
        return credits_result
    
    mock_session.execute = AsyncMock(side_effect=mock_execute_side_effect)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    # Mock UserManager
    mock_user_manager = MagicMock()
    updated_user = User(
        id=target_user.id,
        email=target_user.email,
        is_active=target_user.is_active,
        is_superuser=False,
        is_verified=target_user.is_verified,
        hashed_password="new_hash"
    )
    mock_user_manager.update = AsyncMock(return_value=updated_user)
    
    # Override dependencies
    async def mock_get_async_session():
        yield mock_session
    
    async def mock_current_superuser():
        return admin_user
    
    async def mock_get_user_manager():
        yield mock_user_manager
    
    app.dependency_overrides[current_superuser] = mock_current_superuser
    app.dependency_overrides[get_async_session] = mock_get_async_session
    app.dependency_overrides[get_user_manager] = mock_get_user_manager
    
    try:
        response = await client.patch(
            f"/users/{target_user.id}",
            json={"credits": 25, "is_active": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["credits"] == 25
        # Verify credits were updated
        assert mock_user_credits.credits == 25
        mock_session.commit.assert_called_once()
    finally:
        for dep in [current_superuser, get_async_session, get_user_manager]:
            if dep in app.dependency_overrides:
                del app.dependency_overrides[dep]


@pytest.mark.asyncio
async def test_delete_users_id_handles_credits(client: AsyncClient):
    """Test DELETE /users/{id} endpoint deletes UserCredits."""
    # Create admin user
    admin_user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="admin@example.com",
        is_active=True,
        is_superuser=True,
        is_verified=True
    )
    
    # Create target user
    target_user = User(
        id=uuid.UUID("660e8400-e29b-41d4-a716-446655440001"),
        email="target@example.com",
        is_active=True,
        is_superuser=False,
        is_verified=True
    )
    
    # Mock UserCredits
    mock_user_credits = MagicMock(spec=UserCredits)
    mock_user_credits.credits = 10
    mock_user_credits.user_id = target_user.id
    
    # Mock database session
    mock_session = MagicMock(spec=AsyncSession)
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = target_user
    credits_result = MagicMock()
    credits_result.scalar_one_or_none.return_value = mock_user_credits
    
    def mock_execute_side_effect(query):
        if "user.id" in str(query):
            return user_result
        return credits_result
    
    mock_session.execute = AsyncMock(side_effect=mock_execute_side_effect)
    mock_session.delete = AsyncMock()
    mock_session.flush = AsyncMock()
    
    # Mock UserManager
    mock_user_manager = MagicMock()
    mock_user_manager.delete = AsyncMock()
    
    # Override dependencies
    async def mock_get_async_session():
        yield mock_session
    
    async def mock_current_superuser():
        return admin_user
    
    async def mock_get_user_manager():
        yield mock_user_manager
    
    app.dependency_overrides[current_superuser] = mock_current_superuser
    app.dependency_overrides[get_async_session] = mock_get_async_session
    app.dependency_overrides[get_user_manager] = mock_get_user_manager
    
    try:
        response = await client.delete(f"/users/{target_user.id}")
        assert response.status_code == 204
        # Verify UserCredits was deleted
        mock_session.delete.assert_called_once_with(mock_user_credits)
        mock_session.flush.assert_called_once()
        # Verify user was deleted
        mock_user_manager.delete.assert_called_once()
    finally:
        for dep in [current_superuser, get_async_session, get_user_manager]:
            if dep in app.dependency_overrides:
                del app.dependency_overrides[dep]

