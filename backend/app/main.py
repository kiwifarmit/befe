from fastapi import FastAPI, Depends, Request, HTTPException, status, Query
from contextlib import asynccontextmanager
from app.db import init_db, get_async_session
from app.auth import auth_backend, fastapi_users, SECRET, current_active_user, current_superuser, get_user_db, get_user_manager
from app.models import UserRead, UserCreate, UserUpdate, User, UserCredits, PasswordUpdate, AdminUserUpdate
from app.logging_config import setup_logging
from app.api import endpoints
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import object_session
from typing import List
import logging
import jwt
import math
import uuid

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

# CORS Configuration
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI(title="Minimalist Web App", lifespan=lifespan)

# Security Middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0", "nginx"]
)

# API Logging Middleware
@app.middleware("http")
async def log_api_calls(request: Request, call_next):
    # Process request
    response = await call_next(request)
    
    # Log all API endpoints (exclude static files and docs)
    path = request.url.path
    if not (path.startswith("/docs") or path.startswith("/openapi.json") or path.startswith("/redoc") or path.startswith("/static")):
        api_logger = logging.getLogger("api_logger")
        
        user_id = "anonymous"
        
        # Try to extract user ID from JWT token
        if "Authorization" in request.headers:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "").strip()
                try:
                    # Decode without verification first to get user ID (for logging)
                    decoded_unverified = jwt.decode(token, options={"verify_signature": False})
                    user_id = decoded_unverified.get("sub", "no_user_id_in_token")
                    
                    # If request succeeded (200-299), token is valid (FastAPI-users authenticated it)
                    # So we don't need to verify signature again - just use the user ID
                    # Only check token validity if the request failed (might be due to invalid token)
                    if response.status_code >= 400:
                        try:
                            jwt.decode(token, SECRET, algorithms=["HS256"], options={"verify_signature": True})
                        except jwt.ExpiredSignatureError:
                            user_id = f"{user_id}(expired)"
                        except jwt.InvalidSignatureError:
                            user_id = f"{user_id}(invalid_sig)"
                        except jwt.InvalidTokenError:
                            # Other token errors (not signature-related)
                            user_id = f"{user_id}(token_error)"
                    # If status is 200-299, token is valid, so just use user_id as-is
                except Exception as e:
                    # If we can't even decode the token structure, it's completely invalid
                    user_id = "invalid_token"
        
        api_logger.info(f"Path: {path} | Method: {request.method} | Status: {response.status_code} | User: {user_id}")
        
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], # Add frontend origins
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
    session: AsyncSession = Depends(get_async_session)
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
    return UserRead.model_validate({
        "id": user.id,  # UUID object
        "email": user.email,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "is_verified": user.is_verified,
        "credits": credits_value
    })

# Custom PATCH /users/me endpoint that only allows password updates
@app.patch("/users/me", response_model=UserRead, tags=["users"])
async def update_current_user_password(
    password_update: PasswordUpdate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    user_manager = Depends(get_user_manager)
):
    """Update current user's password only. Email updates are not allowed."""
    # Update password using UserManager
    updated_user = await user_manager.update(
        UserUpdate(password=password_update.password),
        user,
        safe=True  # Safe mode prevents updating email, is_superuser, etc.
    )
    
    # Load credits
    result = await session.execute(
        select(UserCredits).where(UserCredits.user_id == updated_user.id)
    )
    user_credits = result.scalar_one_or_none()
    
    if user_credits is None:
        user_credits = UserCredits(user_id=updated_user.id, credits=10)
        session.add(user_credits)
        await session.flush()
        await session.refresh(user_credits)
    
    credits_value = user_credits.credits if user_credits else 0
    
    return UserRead.model_validate({
        "id": updated_user.id,
        "email": updated_user.email,
        "is_active": updated_user.is_active,
        "is_superuser": updated_user.is_superuser,
        "is_verified": updated_user.is_verified,
        "credits": credits_value
    })

# Admin-only endpoints for user management
@app.get("/users", response_model=dict, tags=["users"])
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    admin_user: User = Depends(current_superuser),
    session: AsyncSession = Depends(get_async_session)
):
    """List all users with pagination. Admin only."""
    # Calculate offset
    offset = (page - 1) * size
    
    # Get total count
    count_result = await session.execute(select(func.count(User.id)))
    total = count_result.scalar()
    
    # Get users with pagination (ordered by email for consistent results)
    users_result = await session.execute(
        select(User).order_by(User.email).offset(offset).limit(size)
    )
    users = users_result.scalars().all()
    
    # Load credits for each user
    user_list = []
    for user in users:
        credits_result = await session.execute(
            select(UserCredits).where(UserCredits.user_id == user.id)
        )
        user_credits = credits_result.scalar_one_or_none()
        credits_value = user_credits.credits if user_credits else 0
        
        user_list.append(UserRead.model_validate({
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "is_verified": user.is_verified,
            "credits": credits_value
        }))
    
    # Calculate total pages
    total_pages = math.ceil(total / size) if total > 0 else 0
    
    return {
        "items": user_list,
        "total": total,
        "page": page,
        "size": size,
        "pages": total_pages
    }

@app.get("/users/{user_id}", response_model=UserRead, tags=["users"])
async def get_user_by_id(
    user_id: uuid.UUID,
    admin_user: User = Depends(current_superuser),
    session: AsyncSession = Depends(get_async_session)
):
    """Get user by ID with credits. Admin only."""
    # Get user
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Load credits
    credits_result = await session.execute(
        select(UserCredits).where(UserCredits.user_id == user.id)
    )
    user_credits = credits_result.scalar_one_or_none()
    credits_value = user_credits.credits if user_credits else 0
    
    return UserRead.model_validate({
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "is_verified": user.is_verified,
        "credits": credits_value
    })

@app.patch("/users/{user_id}", response_model=UserRead, tags=["users"])
async def update_user_by_id(
    user_id: uuid.UUID,
    user_update: AdminUserUpdate,
    admin_user: User = Depends(current_superuser),
    session: AsyncSession = Depends(get_async_session),
    user_manager = Depends(get_user_manager)
):
    """Update user by ID, including credits. Admin only."""
    # Get user
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Update user fields (email, password, is_active, is_superuser)
    update_dict = user_update.model_dump(exclude_unset=True, exclude={"credits"})
    if update_dict:
        updated_user = await user_manager.update(
            UserUpdate(**update_dict),
            user,
            safe=False  # Admin can update all fields
        )
    else:
        updated_user = user
    
    # Update credits if provided
    if user_update.credits is not None:
        credits_result = await session.execute(
            select(UserCredits).where(UserCredits.user_id == user_id)
        )
        user_credits = credits_result.scalar_one_or_none()
        
        if user_credits is None:
            user_credits = UserCredits(user_id=user_id, credits=user_update.credits)
            session.add(user_credits)
        else:
            user_credits.credits = user_update.credits
            session.add(user_credits)
        
        await session.commit()
        await session.refresh(user_credits)
        credits_value = user_credits.credits
    else:
        # Load existing credits
        credits_result = await session.execute(
            select(UserCredits).where(UserCredits.user_id == user_id)
        )
        user_credits = credits_result.scalar_one_or_none()
        credits_value = user_credits.credits if user_credits else 0
    
    return UserRead.model_validate({
        "id": updated_user.id,
        "email": updated_user.email,
        "is_active": updated_user.is_active,
        "is_superuser": updated_user.is_superuser,
        "is_verified": updated_user.is_verified,
        "credits": credits_value
    })

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["users"])
async def delete_user_by_id(
    user_id: uuid.UUID,
    admin_user: User = Depends(current_superuser),
    session: AsyncSession = Depends(get_async_session),
    user_manager = Depends(get_user_manager)
):
    """Delete user by ID, including UserCredits. Admin only."""
    # Get user
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Delete UserCredits first (if exists)
    credits_result = await session.execute(
        select(UserCredits).where(UserCredits.user_id == user_id)
    )
    user_credits = credits_result.scalar_one_or_none()
    if user_credits:
        await session.delete(user_credits)
        await session.flush()
    
    # Delete user (this will be handled by UserManager)
    await user_manager.delete(user)
    
    return None

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# Business Logic Routes
app.include_router(endpoints.router, prefix="/api", tags=["logic"])

@app.get("/")
async def root():
    return {"message": "Hello World"}
