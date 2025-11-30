import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from app.auth import (
    send_reset_password_email,
    UserManager,
    get_user_db,
    get_user_manager,
    get_jwt_strategy,
)
from app.models import User
import uuid


@pytest.mark.asyncio
async def test_send_reset_password_email_no_smtp_config(monkeypatch):
    """Test email sending when SMTP is not configured."""
    monkeypatch.setenv("SMTP_HOST", "")
    monkeypatch.setenv("SMTP_USER", "")
    monkeypatch.setenv("SMTP_PASSWORD", "")
    
    # Should not raise, just log warning
    await send_reset_password_email("test@example.com", "test-token")


@pytest.mark.asyncio
async def test_send_reset_password_email_with_smtp(monkeypatch):
    """Test email sending with SMTP configured."""
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "password")
    monkeypatch.setenv("EMAILS_FROM_EMAIL", "noreply@example.com")
    
    with patch("app.auth.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        await send_reset_password_email("test@example.com", "test-token")
        mock_send.assert_called_once()
        assert mock_send.call_args[1]["hostname"] == "smtp.example.com"
        assert mock_send.call_args[1]["port"] == 587
        assert mock_send.call_args[1]["start_tls"] is True


@pytest.mark.asyncio
async def test_send_reset_password_email_port_465(monkeypatch):
    """Test email sending with port 465 (implicit TLS)."""
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "password")
    
    with patch("app.auth.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        await send_reset_password_email("test@example.com", "test-token")
        assert mock_send.call_args[1]["use_tls"] is True
        assert mock_send.call_args[1]["start_tls"] is False


@pytest.mark.asyncio
async def test_send_reset_password_email_failure(monkeypatch):
    """Test email sending failure handling."""
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "password")
    
    with patch("app.auth.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = Exception("SMTP Error")
        
        with pytest.raises(Exception, match="SMTP Error"):
            await send_reset_password_email("test@example.com", "test-token")


@pytest.mark.asyncio
async def test_user_manager_on_after_register():
    """Test UserManager on_after_register callback."""
    user_db = MagicMock()
    manager = UserManager(user_db)
    
    user = User(id=uuid.uuid4(), email="test@example.com", is_active=True)
    await manager.on_after_register(user)


@pytest.mark.asyncio
async def test_user_manager_on_after_forgot_password(monkeypatch):
    """Test UserManager on_after_forgot_password callback."""
    monkeypatch.setenv("SMTP_HOST", "")  # No SMTP, should just log
    
    user_db = MagicMock()
    manager = UserManager(user_db)
    
    user = User(id=uuid.uuid4(), email="test@example.com", is_active=True)
    await manager.on_after_forgot_password(user, "test-token")


@pytest.mark.asyncio
async def test_user_manager_on_after_request_verify():
    """Test UserManager on_after_request_verify callback."""
    user_db = MagicMock()
    manager = UserManager(user_db)
    
    user = User(id=uuid.uuid4(), email="test@example.com", is_active=True)
    await manager.on_after_request_verify(user, "test-token")


@pytest.mark.asyncio
async def test_get_user_db():
    """Test get_user_db dependency."""
    from app.auth import SQLAlchemyUserDatabase
    
    mock_session = MagicMock()
    
    async def mock_get_async_session():
        yield mock_session
    
    with patch("app.auth.get_async_session", mock_get_async_session):
        async for db in get_user_db():
            assert isinstance(db, SQLAlchemyUserDatabase)
            break


@pytest.mark.asyncio
async def test_get_user_manager():
    """Test get_user_manager dependency."""
    from app.auth import SQLAlchemyUserDatabase
    
    mock_session = MagicMock()
    mock_user_db = SQLAlchemyUserDatabase(mock_session, User)
    
    async def mock_get_user_db():
        yield mock_user_db
    
    with patch("app.auth.get_user_db", mock_get_user_db):
        async for manager in get_user_manager():
            assert isinstance(manager, UserManager)
            break


def test_get_jwt_strategy():
    """Test JWT strategy creation."""
    strategy = get_jwt_strategy()
    assert strategy is not None

