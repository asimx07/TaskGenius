"""Infrastructure tests for database and application startup."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import Task


@pytest.mark.integration
async def test_database_connection(test_db: AsyncSession):
    """Test that database connection works."""
    # Test basic database operations
    task = Task(
        description="Test task",
        title="Test",
        label="test"
    )
    
    test_db.add(task)
    await test_db.commit()
    await test_db.refresh(task)
    
    assert task.id is not None
    assert task.description == "Test task"
    assert task.title == "Test"
    assert task.label == "test"
    assert task.created_at is not None
    assert task.updated_at is not None


@pytest.mark.integration
async def test_app_startup(client: AsyncClient):
    """Test that the FastAPI application starts up correctly."""
    # Test that the app is accessible
    response = await client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Welcome to Task Manager API"
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"


@pytest.mark.integration
async def test_health_check_endpoint(client: AsyncClient):
    """Test the health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "task-manager-api"
    assert data["version"] == "1.0.0"


@pytest.mark.integration
async def test_docs_endpoint(client: AsyncClient):
    """Test that the OpenAPI docs are accessible."""
    response = await client.get("/docs")
    assert response.status_code == 200


@pytest.mark.integration
async def test_openapi_json(client: AsyncClient):
    """Test that the OpenAPI JSON schema is accessible."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    assert data["info"]["title"] == "Task Manager API"
    assert data["info"]["version"] == "1.0.0"


@pytest.mark.unit
async def test_task_model_to_dict(test_db: AsyncSession):
    """Test Task model to_dict method."""
    task = Task(
        description="Test task",
        title="Test",
        label="test"
    )
    
    # Add to database to get timestamps
    test_db.add(task)
    await test_db.commit()
    await test_db.refresh(task)
    
    task_dict = task.to_dict()
    
    assert task_dict["id"] is not None
    assert task_dict["description"] == "Test task"
    assert task_dict["title"] == "Test"
    assert task_dict["label"] == "test"
    assert "created_at" in task_dict
    assert "updated_at" in task_dict
    assert "due_date" in task_dict
    assert task_dict["created_at"] is not None
    assert task_dict["updated_at"] is not None


@pytest.mark.unit
async def test_task_model_repr():
    """Test Task model string representation."""
    task = Task(
        id=1,
        title="Test Task",
        label="test"
    )
    
    repr_str = repr(task)
    assert "Task(id=1" in repr_str
    assert "title='Test Task'" in repr_str
    assert "label='test'" in repr_str
