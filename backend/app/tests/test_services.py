"""Tests for app/services.py to increase coverage."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserCredits
from app.services import perform_sum_with_credits


@pytest.mark.asyncio
async def test_perform_sum_with_credits_creates_user_credits():
    """Test perform_sum_with_credits creates UserCredits if it doesn't exist."""
    user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="test@example.com",
        is_active=True,
    )

    # Mock session - no UserCredits exists
    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    result = await perform_sum_with_credits(user, 10, 20, mock_session)

    assert result == 30
    # Verify UserCredits was created
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_perform_sum_with_credits_insufficient_credits():
    """Test perform_sum_with_credits raises HTTPException when credits are 0."""
    user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="test@example.com",
        is_active=True,
    )

    # Mock UserCredits with 0 credits
    mock_user_credits = MagicMock(spec=UserCredits)
    mock_user_credits.credits = 0
    mock_user_credits.user_id = user.id

    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user_credits
    mock_session.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc_info:
        await perform_sum_with_credits(user, 10, 20, mock_session)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Insufficient credits" in exc_info.value.detail


@pytest.mark.asyncio
async def test_perform_sum_with_credits_negative_credits():
    """Test perform_sum_with_credits raises HTTPException when credits are negative."""
    user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="test@example.com",
        is_active=True,
    )

    # Mock UserCredits with negative credits
    mock_user_credits = MagicMock(spec=UserCredits)
    mock_user_credits.credits = -5
    mock_user_credits.user_id = user.id

    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user_credits
    mock_session.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc_info:
        await perform_sum_with_credits(user, 10, 20, mock_session)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_perform_sum_with_credits_deducts_credit():
    """Test perform_sum_with_credits deducts 1 credit after calculation."""
    user = User(
        id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        email="test@example.com",
        is_active=True,
    )

    # Mock UserCredits with credits
    mock_user_credits = MagicMock(spec=UserCredits)
    mock_user_credits.credits = 10
    mock_user_credits.user_id = user.id

    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user_credits
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()

    result = await perform_sum_with_credits(user, 5, 15, mock_session)

    assert result == 20
    # Verify credit was deducted
    assert mock_user_credits.credits == 9
    mock_session.commit.assert_called_once()
    # Note: refresh is no longer called to avoid greenlet errors
