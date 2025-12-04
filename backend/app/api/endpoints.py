import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.db import get_async_session
from app.models import User, UserCredits
from app.services import perform_sum_with_credits

router = APIRouter()


class SumRequest(BaseModel):
    a: int = Field(..., ge=0, le=1023)
    b: int = Field(..., ge=0, le=1023)


class SumResponse(BaseModel):
    result: int


class CreditsUpdate(BaseModel):
    credits: int = Field(..., ge=0)


@router.post("/sum", response_model=SumResponse)
async def sum_numbers(
    data: SumRequest,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    result = await perform_sum_with_credits(user, data.a, data.b, session)
    return {"result": result}


@router.patch("/users/{user_id}/credits")
async def update_user_credits(
    user_id: uuid.UUID,
    credits_data: CreditsUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Update user credits. Only superusers can update other users' credits."""
    # Check if user is trying to update their own credits or is a superuser
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Only superusers can update other users' credits"
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
