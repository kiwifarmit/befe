#!/usr/bin/env python3
import asyncio
import sys
import os

# Set PYTHONPATH to include the parent directory
# Script is at /home/appuser/app/scripts/manage_user.py, so parent is /home/appuser/app
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Also add common container paths if they exist
for path in ['/app', '/home/appuser/app']:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

from app.db import get_async_session, init_db
from app.models import UserCreate, UserCredits
from fastapi_users.exceptions import UserAlreadyExists
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from app.models import User
from app.auth import UserManager

async def create_user(email, password, is_superuser=False):
    # Initialize DB first to ensure tables exist
    await init_db()

    async for session in get_async_session():
        user_db = SQLAlchemyUserDatabase(session, User)
        user_manager = UserManager(user_db)

        try:
            user = await user_manager.create(
                UserCreate(
                    email=email,
                    password=password,
                    is_superuser=is_superuser,
                    is_active=True,
                    is_verified=True
                )
            )

            # Create UserCredits record with default 10 credits
            user_credits = UserCredits(user_id=user.id, credits=10)
            session.add(user_credits)
            await session.commit()

            print(f"User {user.email} created successfully with ID: {user.id}")
        except UserAlreadyExists:
            print(f"User {email} already exists")
        except Exception as e:
            print(f"Error creating user: {e}")
            import traceback
            traceback.print_exc()
        break

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python manage_user.py <email> <password> [--admin]")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]
    is_admin = "--admin" in sys.argv

    asyncio.run(create_user(email, password, is_admin))
