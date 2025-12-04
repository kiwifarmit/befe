from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserCredits


async def perform_sum_with_credits(
    user: User, a: int, b: int, session: AsyncSession
) -> int:
    """
    Calculate sum of a and b, deducting 1 credit from user.
    Raises HTTPException if user has insufficient credits.
    """
    # Get or create UserCredits for this user
    result = await session.execute(
        select(UserCredits).where(UserCredits.user_id == user.id)
    )
    user_credits = result.scalar_one_or_none()

    # If UserCredits doesn't exist, create it with default 10 credits
    if user_credits is None:
        user_credits = UserCredits(user_id=user.id, credits=10)
        session.add(user_credits)
        await session.flush()

    # Check if user has sufficient credits
    if user_credits.credits <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient credits. Please contact support to top up.",
        )

    # Calculate result
    result = a + b

    # Deduct credit
    user_credits.credits -= 1
    # Store the new credits value before commit to avoid greenlet issues
    user_credits.credits
    await session.commit()
    # Don't refresh - the commit already persisted the change
    # Accessing relationships after commit can cause greenlet errors

    return result
