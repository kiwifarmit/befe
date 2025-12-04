import logging
from contextlib import asynccontextmanager

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, status

# CORS Configuration
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api import credits, endpoints
from app.auth import (
    SECRET,
    UserManager,
    auth_backend,
    current_active_user,
    fastapi_users,
    get_user_manager,
)
from app.db import get_async_session, init_db
from app.logging_config import setup_logging
from app.models import User, UserCreate, UserCredits, UserRead, UserUpdate

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown (if needed in the future)


app = FastAPI(title="Minimalist Web App", lifespan=lifespan)

# Security Middleware
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0", "nginx"]
)


# API Logging Middleware
@app.middleware("http")
async def log_api_calls(request: Request, call_next):
    # Process request
    response = await call_next(request)

    # Log only API calls
    if request.url.path.startswith("/api"):
        api_logger = logging.getLogger("api_logger")

        user_id = "anonymous"

        # Try to extract user ID from JWT token
        if "Authorization" in request.headers:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "").strip()
                try:
                    # Decode without verification first to get user ID (for logging)
                    decoded_unverified = jwt.decode(
                        token, options={"verify_signature": False}
                    )
                    user_id = decoded_unverified.get("sub", "no_user_id_in_token")

                    # If request succeeded (200-299), token is valid (FastAPI-users authenticated it)
                    # So we don't need to verify signature again - just use the user ID
                    # Only check token validity if the request failed (might be due to invalid token)
                    if response.status_code >= 400:
                        try:
                            jwt.decode(
                                token,
                                SECRET,
                                algorithms=["HS256"],
                                options={"verify_signature": True},
                            )
                        except jwt.ExpiredSignatureError:
                            user_id = f"{user_id}(expired)"
                        except jwt.InvalidSignatureError:
                            user_id = f"{user_id}(invalid_sig)"
                        except jwt.InvalidTokenError:
                            # Other token errors (not signature-related)
                            user_id = f"{user_id}(token_error)"
                    # If status is 200-299, token is valid, so just use user_id as-is
                except Exception:
                    # If we can't even decode the token structure, it's completely invalid
                    user_id = "invalid_token"

        api_logger.info(
            f"Path: {request.url.path} | Method: {request.method} | Status: {response.status_code} | User: {user_id}"
        )

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],  # Add frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Routes
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)


# Custom /users/me endpoint that properly loads credits
# Defined before get_users_router so it takes precedence
@app.get("/users/me", response_model=UserRead, tags=["users"])
async def get_current_user_with_credits(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Get current user with credits loaded from UserCredits table."""
    # Get user ID (already available from user object)
    user_id = user.id

    # Load user_credits using the session
    result = await session.execute(
        select(UserCredits).where(UserCredits.user_id == user_id)
    )
    user_credits = result.scalar_one_or_none()

    # If UserCredits doesn't exist, create it with default (don't commit, let dependency handle it)
    if user_credits is None:
        user_credits = UserCredits(user_id=user_id, credits=10)
        session.add(user_credits)
        await session.flush()  # Use flush instead of commit to avoid session conflicts
        await session.refresh(user_credits)

    # Get credits value
    credits_value = user_credits.credits if user_credits else 0

    # Return UserRead with credits - use model_validate with dict to ensure validator works
    return UserRead.model_validate(
        {
            "id": user.id,  # UUID object
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "is_verified": user.is_verified,
            "credits": credits_value,
        }
    )


# Custom /users endpoint to list all users with credits
@app.get("/users", response_model=list[UserRead], tags=["users"])
async def list_users_with_credits(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """List all users with credits. Requires authentication and superuser privileges."""
    # Check if user is superuser
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can list all users",
        )

    # Get all users with their credits relationship loaded
    result = await session.execute(
        select(User).options(selectinload(User.user_credits))
    )
    all_users = result.scalars().unique().all()

    # Build response with credits
    users_with_credits = []
    for u in all_users:
        # Access all attributes while still in session context
        user_id = u.id
        email = u.email
        is_active = u.is_active
        is_superuser = u.is_superuser
        is_verified = u.is_verified

        # Get credits from relationship (already loaded)
        credits_value = u.user_credits.credits if u.user_credits else 0

        users_with_credits.append(
            UserRead.model_validate(
                {
                    "id": user_id,
                    "email": email,
                    "is_active": is_active,
                    "is_superuser": is_superuser,
                    "is_verified": is_verified,
                    "credits": credits_value,
                }
            )
        )

    return users_with_credits


# Password change schema
class PasswordChange(BaseModel):
    current_password: str
    password: str


# Password change endpoint
@app.patch("/users/me/password", tags=["users"])
async def change_password(
    password_data: PasswordChange,
    user: User = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager),
    session: AsyncSession = Depends(get_async_session),
):
    """Change user's own password. Requires current password verification."""
    try:
        # Verify current password
        from fastapi_users.password import PasswordHelper

        password_helper = PasswordHelper()

        # Check if current password is correct
        verified, updated_hash = password_helper.verify_and_update(
            password_data.current_password, user.hashed_password
        )
        if not verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        # Validate new password using UserManager
        await user_manager.validate_password(password_data.password, user)

        # Hash and update the new password
        user.hashed_password = password_helper.hash(password_data.password)
        session.add(user)
        await session.commit()

        return {"detail": "Password updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )


app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# Business Logic Routes
app.include_router(endpoints.router, prefix="/api", tags=["logic"])
app.include_router(credits.router, prefix="/api", tags=["users"])


@app.get("/")
async def root():
    return {"message": "Hello World"}
