from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.models.permission import Permission
from app.models.role import Role
import logging

logger = logging.getLogger(__name__)

async def __seed_permissions(db: AsyncSession):
    
    if await db.scalar(select(Permission).limit(1)) is not None:
        return  # Permissions already seeded, skip seeding
    pass

async def __seed_roles(db: AsyncSession):
    
    if await db.scalar(select(Role).limit(1)) is not None:
        return  # Roles already seeded, skip seeding
    
    list_of_roles = [
        {"name": "admin", "description": "Administrator role with full access", "is_system": True},
        {"name": "manager", "description": "Manager user", "is_system": True},
        {"name": "user", "description": "Regular user role with limited access", "is_system": True},
    ]   
    
    db.add_all([Role(**role) for role in list_of_roles])
    await db.commit()

async def __seed_users(session: AsyncSession):
    
    if await session.scalar(select(User).limit(1)) is not None:
        return  # Users already seeded, skip seeding
    
    # Add your seed users here
    user = {
        "username": "admin",
        "email": "admin@user.com",
        "password": "admin",
        "is_active": True,
        "is_verified": True,
    }
    # Add the user to the session
    try:
        session.add(User(
            email=user["email"],
            username=user["username"],
            hashed_password=user["password"],
            is_active=user["is_active"],
            is_verified=user["is_verified"],
        ))
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error("Error seeding users: %s", e)

async def seed_data(session: AsyncSession):
    try:
        # Add your seed data here
        await __seed_permissions(session)
        await __seed_roles(session)
        await __seed_users(session)
    except Exception as e:
        await session.rollback()
        await session.close()
        logger.error("Error seeding data: %s", e)
