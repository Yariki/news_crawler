import os

os.environ.setdefault("APP_MODE", "test")  # set BEFORE any app imports

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from app.api.dependencies.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole
from app.main import app


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16") as pg:
        yield pg


@pytest.fixture(scope="session")
def database_url(postgres_container):
    # async driver
    return postgres_container.get_connection_url().replace("psycopg2", "asyncpg")


@pytest.fixture(scope="session", autouse=True)
def apply_migrations(database_url, postgres_container):
    # Alembic usually expects a sync URL
    sync_url = postgres_container.get_connection_url(driver="psycopg")
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", sync_url)
    command.upgrade(cfg, "head")
    yield
    command.downgrade(cfg, "base")


@pytest_asyncio.fixture
async def db_session(database_url):
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.connect() as conn:
        trans = await conn.begin()
        async with async_session(bind=conn) as session:
            yield session
        await trans.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    user = await db_session.scalar(select(User).where(User.email == "admin@news-crawler.local"))
    if user is None:
        user = User(
            email="admin@news-crawler.local",
            password_hash="pbkdf2_sha256$310000$newsmonitorseed$MBMWdU5_ONGrL7DLuwOauOK8deZCNdxIIPF6UOPAD-s=",
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()
        role = await db_session.scalar(select(Role).where(Role.name == "admin"))
        if role is None:
            role = Role(name="admin")
            db_session.add(role)
            await db_session.flush()
            db_session.add(RolePermission(role_id=role.id, permission="users:read"))
        db_session.add(UserRole(user_id=user.id, role_id=role.id))
        await db_session.commit()

    async def override_get_current_user():
        return CurrentUser(
            id=user.id,
            email=user.email,
            roles=["admin"],
            permissions=["users:read", "users:write", "roles:read", "roles:write", "audit:read"],
            is_active=user.is_active,
        )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
