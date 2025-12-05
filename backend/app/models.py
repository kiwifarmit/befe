import uuid

from fastapi_users import schemas
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from pydantic import model_validator
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# Database Model
class User(SQLAlchemyBaseUserTableUUID, Base):
    user_credits = relationship("UserCredits", back_populates="user", uselist=False)


class UserCredits(Base):
    __tablename__ = "user_credits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    credits = Column(Integer, default=10, nullable=False)

    user = relationship("User", back_populates="user_credits")


# Pydantic Schemas
class UserRead(schemas.BaseUser[uuid.UUID]):
    @model_validator(mode="before")
    @classmethod
    def extract_credits(cls, data):
        """Extract credits from user_credits relationship before validation."""
        # Handle dict inputs (from keyword arguments or explicit dicts)
        if isinstance(data, dict):
            # If credits is already set, return as-is
            if "credits" in data:
                return data
            # If it's a dict with user_credits object, extract credits
            if "user_credits" in data and data["user_credits"]:
                data["credits"] = data["user_credits"].credits
            else:
                # Default to 0 if not present
                data["credits"] = 0
            return data

        # Handle object inputs (SQLAlchemy models)
        # CRITICAL: hasattr() and getattr() on SQLAlchemy relationships trigger lazy loading
        # which causes greenlet errors if session is closed. We must avoid checking the
        # relationship attribute at all if possible.
        #
        # Strategy: Check if 'credits' is already set first (safe), then try to access
        # relationship only if needed, catching ALL exceptions including greenlet errors.

        # Check if credits already set (safe - no relationship access)
        try:
            if hasattr(data, "credits"):
                # Check if it's actually set (not just the attribute exists)
                existing_credits = getattr(data, "credits", None)
                if existing_credits is not None:
                    return data
        except Exception:
            # If even checking credits fails, continue to try relationship
            pass

        # Credits not set - try to get from relationship
        # WARNING: Directly accessing data.user_credits WILL trigger lazy loading
        # which can cause greenlet errors. We catch everything.
        try:
            user_credits = data.user_credits  # This line can trigger greenlet error
            if user_credits:
                setattr(data, "credits", user_credits.credits)
            else:
                setattr(data, "credits", 0)
        except Exception:
            # Catch ALL exceptions including:
            # - sqlalchemy.exc.MissingGreenlet (session closed, object detached)
            # - AttributeError (relationship doesn't exist)
            # - Any other error
            # Default to 0 - endpoints that need credits should load them explicitly
            setattr(data, "credits", 0)

        return data

    credits: int = 0


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass
