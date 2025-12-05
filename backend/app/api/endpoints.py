from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.db import get_async_session
from app.models import User
from app.services import perform_sum_with_credits

router = APIRouter()


class SumRequest(BaseModel):
    a: int = Field(..., ge=0, le=1023)
    b: int = Field(..., ge=0, le=1023)


class SumResponse(BaseModel):
    result: int


@router.post("/sum", response_model=SumResponse)
async def sum_numbers(
    data: SumRequest,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Calculate sum of two numbers. Requires authentication and sufficient credits.

    Security checks:
    - Authentication required (via current_active_user dependency)
    - Input validation: a and b must be between 0 and 1023 (enforced by Pydantic)
    - Business logic: User must have at least 1 credit (checked in perform_sum_with_credits)
    - Credits are deducted after successful operation
    """
    result = await perform_sum_with_credits(user, data.a, data.b, session)
    return {"result": result}
