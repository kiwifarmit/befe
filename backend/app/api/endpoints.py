from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.auth import current_active_user
from app.models import User
from app.services import perform_sum_with_credits
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_session

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
    session: AsyncSession = Depends(get_async_session)
):
    result = await perform_sum_with_credits(user, data.a, data.b, session)
    return {"result": result}
