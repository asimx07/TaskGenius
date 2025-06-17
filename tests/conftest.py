"""Test configuration and fixtures."""

import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import app
from db import Base, get_db
from models import Task


# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# Create test session factory
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.
    
    Yields:
        AsyncSession: Test database session
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test HTTP client.
    
    Args:
        test_db: Test database session
        
    Yields:
        AsyncClient: Test HTTP client
    """
    # Override database dependency
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # Clean up
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test HTTP client.
    
    Args:
        test_db: Test database session
        
    Yields:
        AsyncClient: Test HTTP client
    """
    from db import get_db_session
    
    # Override database dependency
    async def override_get_db_session():
        yield test_db
    
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # Clean up
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db_session(test_db: AsyncSession) -> AsyncSession:
    """
    Provide a database session for tests.
    
    Args:
        test_db: Test database session
        
    Returns:
        AsyncSession: Database session
    """
    return test_db


@pytest_asyncio.fixture
async def sample_task(test_db: AsyncSession) -> Task:
    """
    Create a sample task for testing.
    
    Args:
        test_db: Test database session
        
    Returns:
        Task: Sample task instance
    """
    task = Task(
        description="Buy groceries tomorrow at 3pm",
        title="Buy groceries",
        label="shopping",
    )
    test_db.add(task)
    await test_db.commit()
    await test_db.refresh(task)
    return task


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Set test environment variables
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["OPENAI_API_KEY"] = "test-key"
