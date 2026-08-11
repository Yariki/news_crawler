import os
from types import SimpleNamespace
from typing import Any
from sqlalchemy.future import select
from app.models.user import User

from faker import Faker

from app.core.rbac import AuthorizationContext

os.environ["APP_MODE"] = "test"  # set BEFORE any app imports

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from app.db.session import get_db
from app.main import app
from app.core.auth import get_current_active_user, get_current_user
from app.core.rbac import get_authorization_context


@pytest.fixture
def faker() -> Faker:
    return Faker()

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

    # VS Code's Python extension may load DATABASE_URL from the workspace .env.
    # migrations/env.py gives that variable precedence over Alembic's configured
    # URL, so pin it to the dynamically allocated Testcontainers URL here.
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv("DATABASE_URL", sync_url)
        command.upgrade(cfg, "head")

    yield

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv("DATABASE_URL", sync_url)
        command.downgrade(cfg, "base")


@pytest_asyncio.fixture
async def db_session(database_url):
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    async with engine.connect() as conn:
        trans = await conn.begin()
        async with async_session(bind=conn) as session:
            yield session
        if trans.is_active:
            await trans.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test/api"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


async def set_authorization_context(db_session: AsyncSession, *permission: str, user_name: str, role: str = 'admin' ) -> AuthorizationContext:
    
    user_query = (
        select(User)
        .where(User.username == user_name)
    )
    user = (await db_session.execute(user_query)).scalar_one()
    
    current_user = SimpleNamespace(id=user.id, is_active=True)
    
    context = AuthorizationContext(user_id=user.id, roles=frozenset({role}), permissions=frozenset(permission))

    async def override_current_user() -> Any:
        return current_user

    async def override_context() -> AuthorizationContext:
        return context

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_current_active_user] = override_current_user
    app.dependency_overrides[get_authorization_context] = override_context
    
    return context


pytest_plugins = [
    "tests.conftest_plugins.user",
    "tests.conftest_plugins.source",
]

