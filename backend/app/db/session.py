from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import contextmanager, asynccontextmanager
from typing import Annotated, Iterator

from fastapi import Depends
from sqlalchemy import create_engine, make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

async_url = make_url(settings.database_url)  # postgresql+asyncpg://...
sync_url = async_url.set(drivername="postgresql+psycopg")

engine = create_engine(sync_url )
async_engine = create_async_engine(settings.database_url, future=True, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=False, expire_on_commit=False)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, autoflush=False, expire_on_commit=False, class_=AsyncSession)

def get_sync_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as db:
        yield db

@asynccontextmanager
async def get_db_async() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as db:
        yield db
        


SyncDbSession = Annotated[Session, Depends(get_sync_db)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
