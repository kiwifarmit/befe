import logging
import os
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import aiosmtplib
from fastapi import Depends, HTTPException, Request, status
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_session
from app.models import User, UserCreate

logger = logging.getLogger(__name__)


async def send_reset_password_email(email: str, token: str):
    """Send password reset email with token."""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("EMAILS_FROM_EMAIL", smtp_user)

    if not all([smtp_host, smtp_user, smtp_password]):
        logger.warning("SMTP not configured. Password reset email NOT sent.")
        logger.info(f"Password reset token for {email}: {token}")
        return

    # Create email
    message = MIMEMultipart("alternative")
    message["Subject"] = "Password Reset Request"
    message["From"] = from_email
    message["To"] = email

    # Create reset URL
    reset_url = f"http://localhost:5173/reset-password?token={token}"

    text_content = f"""
Hello,

You requested a password reset. Click the link below to reset your password:

{reset_url}

If you didn't request this, please ignore this email.

This link will expire in 1 hour.
"""

    html_content = f"""
<html>
<body>
    <h2>Password Reset Request</h2>
    <p>You requested a password reset. Click the button below to reset your password:</p>
    <p><a href="{reset_url}" style="background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Reset Password</a></p>
    <p>Or copy this link: <br><code>{reset_url}</code></p>
    <p>If you didn't request this, please ignore this email.</p>
    <p><small>This link will expire in 1 hour.</small></p>
</body>
</html>
"""

    message.attach(MIMEText(text_content, "plain"))
    message.attach(MIMEText(html_content, "html"))

    try:
        # Port 465 uses implicit SSL, port 587 uses STARTTLS
        use_tls = smtp_port == 465
        use_starttls = smtp_port == 587

        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            use_tls=use_tls,
            start_tls=use_starttls,
            timeout=30,
        )
        logger.info(f"Password reset email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send email to {email}: {e}")
        raise  # Re-raise to help debug


SECRET = os.getenv("SECRET_KEY", "SECRET")

logger = logging.getLogger(__name__)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        logger.info(f"User {user.id} has registered.")

    async def validate_password(self, password: str, user: User | UserCreate) -> None:
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long",
            )
        if not any(char.isdigit() for char in password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one number",
            )
        if not any(char.isupper() for char in password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one uppercase letter",
            )
        if not any(char.islower() for char in password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one lowercase letter",
            )
        await super().validate_password(password, user)

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        logger.info(f"User {user.email} requested password reset")
        await send_reset_password_email(user.email, token)

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        logger.info(
            f"Verification requested for user {user.id}. Verification token: {token}"
        )


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)

# Security dependency: requires superuser
current_superuser = fastapi_users.current_user(active=True, superuser=True)
