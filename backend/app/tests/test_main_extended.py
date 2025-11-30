"""Extended tests for app/main.py to increase coverage."""
import pytest
from httpx import AsyncClient
import uuid
import jwt
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import User, UserCredits
from app.auth import current_active_user
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

