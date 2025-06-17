"""Integration tests for task API endpoints."""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from models import Task


@pytest.mark.integration
async def test_create_task_success(async_client: AsyncClient, db_session):
    """Test successful task creation with AI processing."""
    
    # Mock AI worker responses
    with patch('views.tasks.execute_worker') as mock_execute:
        # Mock the AI worker pipeline
        mock_execute.side_effect = [
            # Title/date extraction
            {
                "title": "Buy groceries",
                "due_date": "2024-01-20T18:00:00",
                "confidence": 0.9,
                "reasoning": "Extracted shopping task with evening deadline"
            },
            # Label extraction
            {
                "label": "shopping",
                "confidence": 0.85,
                "reasoning": "Task involves purchasing items"
            },
            # Priority extraction
            {
                "priority": "medium",
                "confidence": 0.8,
                "reasoning": "Regular shopping task, not urgent"
            }
        ]
        
        # Create task
        task_data = {
            "description": "Need to buy groceries for dinner tonight by 6pm"
        }
        
        response = await async_client.post("/api/v1/tasks/", json=task_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["description"] == task_data["description"]
        assert data["title"] == "Buy groceries"
        assert data["label"] == "shopping"
        assert data["due_date"] == "2024-01-20T18:00:00"
        assert "created_at" in data
        assert "updated_at" in data
        
        # Verify AI workers were called correctly
        assert mock_execute.call_count == 3
        
        # Verify task was saved to database
        query = select(Task).where(Task.id == data["id"])
        result = await db_session.execute(query)
        task = result.scalar_one()
        
        assert task.description == task_data["description"]
        assert task.title == "Buy groceries"
        assert task.label == "shopping"


@pytest.mark.integration
async def test_create_task_ai_processing_failure(async_client: AsyncClient):
    """Test task creation when AI processing fails."""
    
    with patch('views.tasks.execute_worker') as mock_execute:
        # Mock AI worker failure
        mock_execute.side_effect = Exception("OpenAI API error")
        
        task_data = {
            "description": "Some task description"
        }
        
        response = await async_client.post("/api/v1/tasks/", json=task_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "AI processing failed" in data["detail"]


@pytest.mark.integration
async def test_create_task_validation_error(async_client: AsyncClient):
    """Test task creation with invalid input."""
    
    # Missing description
    response = await async_client.post("/api/v1/tasks/", json={})
    assert response.status_code == 422
    
    # Empty description
    response = await async_client.post("/api/v1/tasks/", json={"description": ""})
    assert response.status_code == 422
    
    # Non-string description
    response = await async_client.post("/api/v1/tasks/", json={"description": 123})
    assert response.status_code == 422


@pytest.mark.integration
async def test_list_tasks_empty(async_client: AsyncClient):
    """Test listing tasks when database is empty."""
    
    response = await async_client.get("/api/v1/tasks/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["tasks"] == []
    assert data["total"] == 0
    assert data["skip"] == 0
    assert data["limit"] == 50


@pytest.mark.integration
async def test_list_tasks_with_data(async_client: AsyncClient, db_session):
    """Test listing tasks with existing data."""
    
    # Create test tasks
    tasks = [
        Task(
            description="Task 1",
            title="Title 1",
            label="work",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        Task(
            description="Task 2", 
            title="Title 2",
            label="personal",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]
    
    for task in tasks:
        db_session.add(task)
    await db_session.commit()
    
    # Test listing all tasks
    response = await async_client.get("/api/v1/tasks/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["tasks"]) == 2
    assert data["total"] == 2
    assert data["skip"] == 0
    assert data["limit"] == 50


@pytest.mark.integration
async def test_list_tasks_with_pagination(async_client: AsyncClient, db_session):
    """Test task listing with pagination."""
    
    # Create multiple test tasks
    for i in range(5):
        task = Task(
            description=f"Task {i}",
            title=f"Title {i}",
            label="test",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(task)
    await db_session.commit()
    
    # Test pagination
    response = await async_client.get("/api/v1/tasks/?skip=2&limit=2")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["tasks"]) == 2
    assert data["total"] == 5
    assert data["skip"] == 2
    assert data["limit"] == 2


@pytest.mark.integration
async def test_list_tasks_with_label_filter(async_client: AsyncClient, db_session):
    """Test task listing with label filtering."""
    
    # Create tasks with different labels
    tasks = [
        Task(description="Work task", title="Work", label="work", 
             created_at=datetime.utcnow(), updated_at=datetime.utcnow()),
        Task(description="Personal task", title="Personal", label="personal",
             created_at=datetime.utcnow(), updated_at=datetime.utcnow()),
        Task(description="Another work task", title="Work 2", label="work",
             created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    ]
    
    for task in tasks:
        db_session.add(task)
    await db_session.commit()
    
    # Filter by work label
    response = await async_client.get("/api/v1/tasks/?label=work")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["tasks"]) == 2
    assert data["total"] == 2
    assert all(task["label"] == "work" for task in data["tasks"])


@pytest.mark.integration
async def test_get_task_success(async_client: AsyncClient, db_session):
    """Test getting a specific task by ID."""
    
    # Create test task
    task = Task(
        description="Test task",
        title="Test Title",
        label="test",
        due_date=datetime(2024, 1, 20, 18, 0),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    # Get task
    response = await async_client.get(f"/api/v1/tasks/{task.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == task.id
    assert data["description"] == "Test task"
    assert data["title"] == "Test Title"
    assert data["label"] == "test"
    assert data["due_date"] == "2024-01-20T18:00:00"


@pytest.mark.integration
async def test_get_task_not_found(async_client: AsyncClient):
    """Test getting a non-existent task."""
    
    response = await async_client.get("/api/v1/tasks/999")
    
    assert response.status_code == 404
    data = response.json()
    assert "Task not found" in data["detail"]


@pytest.mark.integration
async def test_update_task_without_description_change(async_client: AsyncClient, db_session):
    """Test updating task without changing description (no AI reprocessing)."""
    
    # Create test task
    task = Task(
        description="Original description",
        title="Original Title",
        label="original",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    # Update only title and label
    update_data = {
        "title": "Updated Title",
        "label": "updated"
    }
    
    response = await async_client.put(f"/api/v1/tasks/{task.id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == task.id
    assert data["description"] == "Original description"  # Unchanged
    assert data["title"] == "Updated Title"
    assert data["label"] == "updated"


@pytest.mark.integration
async def test_update_task_with_description_change(async_client: AsyncClient, db_session):
    """Test updating task with description change (triggers AI reprocessing)."""
    
    # Create test task
    task = Task(
        description="Original description",
        title="Original Title",
        label="original",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    with patch('views.tasks.execute_worker') as mock_execute:
        # Mock AI worker responses for reprocessing
        mock_execute.side_effect = [
            {
                "title": "New AI Title",
                "due_date": "2024-01-25T12:00:00",
                "confidence": 0.9,
                "reasoning": "Updated extraction"
            },
            {
                "label": "new_label",
                "confidence": 0.85,
                "reasoning": "Updated categorization"
            },
            {
                "priority": "high",
                "confidence": 0.8,
                "reasoning": "Updated priority"
            }
        ]
        
        # Update description
        update_data = {
            "description": "Updated description with new content"
        }
        
        response = await async_client.put(f"/api/v1/tasks/{task.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == task.id
        assert data["description"] == "Updated description with new content"
        assert data["title"] == "New AI Title"  # AI-extracted
        assert data["label"] == "new_label"  # AI-extracted
        
        # Verify AI workers were called
        assert mock_execute.call_count == 3


@pytest.mark.integration
async def test_update_task_not_found(async_client: AsyncClient):
    """Test updating a non-existent task."""
    
    update_data = {"title": "New Title"}
    response = await async_client.put("/api/v1/tasks/999", json=update_data)
    
    assert response.status_code == 404
    data = response.json()
    assert "Task not found" in data["detail"]


@pytest.mark.integration
async def test_delete_task_success(async_client: AsyncClient, db_session):
    """Test successful task deletion."""
    
    # Create test task
    task = Task(
        description="Task to delete",
        title="Delete Me",
        label="test",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    # Delete task
    response = await async_client.delete(f"/api/v1/tasks/{task.id}")
    
    assert response.status_code == 204
    
    # Verify task was deleted
    query = select(Task).where(Task.id == task.id)
    result = await db_session.execute(query)
    deleted_task = result.scalar_one_or_none()
    
    assert deleted_task is None


@pytest.mark.integration
async def test_delete_task_not_found(async_client: AsyncClient):
    """Test deleting a non-existent task."""
    
    response = await async_client.delete("/api/v1/tasks/999")
    
    assert response.status_code == 404
    data = response.json()
    assert "Task not found" in data["detail"]


@pytest.mark.integration
async def test_generate_summary_success(async_client: AsyncClient, db_session):
    """Test successful summary generation."""
    
    # Create test tasks
    base_time = datetime.utcnow()
    tasks = [
        Task(
            description="Work task 1",
            title="Complete project",
            label="work",
            created_at=base_time,
            updated_at=base_time
        ),
        Task(
            description="Personal task 1",
            title="Buy groceries",
            label="shopping",
            created_at=base_time + timedelta(hours=1),
            updated_at=base_time + timedelta(hours=1)
        )
    ]
    
    for task in tasks:
        db_session.add(task)
    await db_session.commit()
    
    with patch('views.tasks.execute_worker') as mock_execute:
        # Mock summary worker response
        mock_execute.return_value = {
            "summary": "You have a balanced mix of work and personal tasks.",
            "task_count": 2,
            "key_themes": ["work", "shopping"],
            "insights": "Good task distribution across categories."
        }
        
        # Generate summary
        summary_data = {
            "start_date": (base_time - timedelta(hours=1)).isoformat(),
            "end_date": (base_time + timedelta(hours=2)).isoformat()
        }
        
        response = await async_client.post("/api/v1/tasks/summary", json=summary_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["summary"] == "You have a balanced mix of work and personal tasks."
        assert data["task_count"] == 2
        assert "start_date" in data
        assert "end_date" in data
        
        # Verify summary worker was called
        mock_execute.assert_called_once()


@pytest.mark.integration
async def test_generate_summary_no_tasks(async_client: AsyncClient):
    """Test summary generation when no tasks exist in date range."""
    
    summary_data = {
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-01-02T00:00:00"
    }
    
    response = await async_client.post("/api/v1/tasks/summary", json=summary_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "No tasks found" in data["summary"]
    assert data["task_count"] == 0


@pytest.mark.integration
async def test_get_task_labels(async_client: AsyncClient, db_session):
    """Test getting unique task labels."""
    
    # Create tasks with different labels
    tasks = [
        Task(description="Task 1", title="Title 1", label="work",
             created_at=datetime.utcnow(), updated_at=datetime.utcnow()),
        Task(description="Task 2", title="Title 2", label="personal",
             created_at=datetime.utcnow(), updated_at=datetime.utcnow()),
        Task(description="Task 3", title="Title 3", label="work",  # Duplicate
             created_at=datetime.utcnow(), updated_at=datetime.utcnow()),
        Task(description="Task 4", title="Title 4", label=None,  # No label
             created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    ]
    
    for task in tasks:
        db_session.add(task)
    await db_session.commit()
    
    response = await async_client.get("/api/v1/tasks/labels/")
    
    assert response.status_code == 200
    labels = response.json()
    
    assert isinstance(labels, list)
    assert "work" in labels
    assert "personal" in labels
    assert len(labels) == 2  # Should not include None or duplicates
    assert labels == sorted(labels)  # Should be sorted


@pytest.mark.integration
async def test_summary_validation_error(async_client: AsyncClient):
    """Test summary generation with invalid date range."""
    
    # End date before start date
    summary_data = {
        "start_date": "2024-01-02T00:00:00",
        "end_date": "2024-01-01T00:00:00"
    }
    
    response = await async_client.post("/api/v1/tasks/summary", json=summary_data)
    
    assert response.status_code == 422
