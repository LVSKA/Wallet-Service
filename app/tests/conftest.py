import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.db.session import Base, get_session, engine as global_engine
from app.main import app
from app.models.wallet import Wallet


@pytest_asyncio.fixture
async def session_factory() -> AsyncGenerator[async_sessionmaker, None]:
    # Создаем изолированный engine под event_loop конкретного теста без кеширования в пуле (NullPool)
    test_engine = create_async_engine(global_engine.url, poolclass=NullPool)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    yield factory

    # Чистим таблицы и закрываем engine после каждого теста
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client(session_factory: async_sessionmaker) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def existing_wallet(session_factory: async_sessionmaker) -> Wallet:
    async with session_factory() as session:
        wallet = Wallet(id=uuid.uuid4(), balance=1000)
        session.add(wallet)
        await session.commit()
        await session.refresh(wallet)
        return wallet