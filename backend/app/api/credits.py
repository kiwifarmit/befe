"""
CREDITS ENDPOINT - DO NOT REMOVE THIS FILE
==========================================
This file contains the update_user_credits endpoint required for admin credit management.
It is protected by pre-commit hook: scripts/check-endpoints.sh
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.db import get_async_session
from app.models import User, UserCredits

router = APIRouter()


class CreditsUpdate(BaseModel):
    credits: int = Field(..., ge=0)


@router.patch("/users/{user_id}/credits")
async def update_user_credits(
    user_id: uuid.UUID,
    credits_data: CreditsUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Update user credits. Only superusers can update credits (including their own)."""
    # SECURITY FIX: Only allow superusers to update credits
    # Previous check allowed users to update their own credits, enabling privilege escalation
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can update credits",
        )

    new_credits_value = credits_data.credits

    # Check if UserCredits exists
    result = await session.execute(
        select(UserCredits).where(UserCredits.user_id == user_id)
    )
    user_credits = result.scalar_one_or_none()

    if user_credits is None:
        # Create new UserCredits using insert to avoid relationship issues
        await session.execute(
            insert(UserCredits).values(user_id=user_id, credits=new_credits_value)
        )
    else:
        # Update existing UserCredits using update statement to avoid relationship issues
        await session.execute(
            update(UserCredits)
            .where(UserCredits.user_id == user_id)
            .values(credits=new_credits_value)
        )

    await session.commit()

    return {"user_id": str(user_id), "credits": new_credits_value}
