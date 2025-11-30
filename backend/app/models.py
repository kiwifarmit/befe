import uuid
from typing import Optional
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from fastapi_users import schemas
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Integer, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from pydantic import model_validator, BaseModel

class Base(DeclarativeBase):
    pass

# Database Model
class User(SQLAlchemyBaseUserTableUUID, Base):
    user_credits = relationship("UserCredits", back_populates="user", uselist=False)

class UserCredits(Base):
    __tablename__ = "user_credits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), unique=True, nullable=False)
    credits = Column(Integer, default=10, nullable=False)
    
    user = relationship("User", back_populates="user_credits")

# Pydantic Schemas
class UserRead(schemas.BaseUser[uuid.UUID]):
    @model_validator(mode='before')
    @classmethod
    def extract_credits(cls, data):
        """Extract credits from user_credits relationship before validation."""
        # Handle dict inputs (from keyword arguments or explicit dicts)
        if isinstance(data, dict):
            # If credits is already set, return as-is
            if 'credits' in data:
                return data
            # If it's a dict with user_credits object, extract credits
            if 'user_credits' in data and data['user_credits']:
                data['credits'] = data['user_credits'].credits
            else:
                # Default to 0 if not present
                data['credits'] = 0
            return data
        
        # Handle object inputs (SQLAlchemy models)
        if hasattr(data, 'user_credits') and data.user_credits:
            # Set credits as an attribute so Pydantic can serialize it
            setattr(data, 'credits', data.user_credits.credits)
        elif not hasattr(data, 'credits'):
            setattr(data, 'credits', 0)
        
        return data
    
    credits: int = 0

class UserCreate(schemas.BaseUserCreate):
    pass

class UserUpdate(schemas.BaseUserUpdate):
    pass

class PasswordUpdate(BaseModel):
    """Schema for password-only updates (profile page)."""
    password: str

class AdminUserUpdate(schemas.BaseUserUpdate):
    """Schema for admin user updates, including credits."""
    credits: Optional[int] = None
