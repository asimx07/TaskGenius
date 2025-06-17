"""Unit tests for Pydantic schemas."""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from libs.schema import (
    BulkSummary,
    ErrorDetail,
    ErrorResponse,
    ExtractedLabel,
    ExtractedTitleDate,
    HealthResponse,
    SummaryRequest,
    SummaryResponse,
    TaskCreate,
    TaskList,
    TaskResponse,
    TaskUpdate,
)


@pytest.mark.unit
def test_task_create_valid():
    """Test TaskCreate schema with valid data."""
    task_data = {
        "description": "Buy groceries tomorrow",
        "title": "Buy groceries",
        "label": "shopping",
        "due_date": datetime.now() + timedelta(days=1)
    }
    
    task = TaskCreate(**task_data)
    
    assert task.description == "Buy groceries tomorrow"
    assert task.title == "Buy groceries"
    assert task.label == "shopping"
    assert task.due_date is not None


@pytest.mark.unit
def test_task_create_minimal():
    """Test TaskCreate schema with minimal required data."""
    task_data = {"description": "Simple task"}
    
    task = TaskCreate(**task_data)
    
    assert task.description == "Simple task"
    assert task.title is None
    assert task.label is None
    assert task.due_date is None


@pytest.mark.unit
def test_task_create_empty_description():
    """Test TaskCreate schema with empty description."""
    with pytest.raises(ValidationError) as exc_info:
        TaskCreate(description="")
    
    assert "String should have at least 1 character" in str(exc_info.value)


@pytest.mark.unit
def test_task_create_whitespace_description():
    """Test TaskCreate schema with whitespace-only description."""
    with pytest.raises(ValidationError) as exc_info:
        TaskCreate(description="   ")
    
    assert "Description cannot be empty" in str(exc_info.value)


@pytest.mark.unit
def test_task_create_strips_whitespace():
    """Test TaskCreate schema strips whitespace from description."""
    task = TaskCreate(description="  Task with spaces  ")
    
    assert task.description == "Task with spaces"


@pytest.mark.unit
def test_task_create_description_too_long():
    """Test TaskCreate schema with description too long."""
    long_description = "x" * 2001
    
    with pytest.raises(ValidationError) as exc_info:
        TaskCreate(description=long_description)
    
    assert "String should have at most 2000 characters" in str(exc_info.value)


@pytest.mark.unit
def test_task_update_valid():
    """Test TaskUpdate schema with valid data."""
    update_data = {
        "description": "Updated task description",
        "title": "Updated title",
        "label": "updated",
        "due_date": datetime.now() + timedelta(days=2)
    }
    
    task_update = TaskUpdate(**update_data)
    
    assert task_update.description == "Updated task description"
    assert task_update.title == "Updated title"
    assert task_update.label == "updated"
    assert task_update.due_date is not None


@pytest.mark.unit
def test_task_update_partial():
    """Test TaskUpdate schema with partial data."""
    update_data = {"title": "New title only"}
    
    task_update = TaskUpdate(**update_data)
    
    assert task_update.description is None
    assert task_update.title == "New title only"
    assert task_update.label is None
    assert task_update.due_date is None


@pytest.mark.unit
def test_task_update_empty_description():
    """Test TaskUpdate schema with empty description."""
    with pytest.raises(ValidationError) as exc_info:
        TaskUpdate(description="")
    
    assert "String should have at least 1 character" in str(exc_info.value)


@pytest.mark.unit
def test_task_response_valid():
    """Test TaskResponse schema with valid data."""
    now = datetime.now()
    response_data = {
        "id": 1,
        "description": "Test task",
        "title": "Test",
        "label": "test",
        "due_date": now + timedelta(days=1),
        "created_at": now,
        "updated_at": now
    }
    
    task_response = TaskResponse(**response_data)
    
    assert task_response.id == 1
    assert task_response.description == "Test task"
    assert task_response.title == "Test"
    assert task_response.label == "test"
    assert task_response.due_date is not None
    assert task_response.created_at == now
    assert task_response.updated_at == now


@pytest.mark.unit
def test_task_list_valid():
    """Test TaskList schema with valid data."""
    now = datetime.now()
    task_data = {
        "id": 1,
        "description": "Test task",
        "title": "Test",
        "label": "test",
        "due_date": None,
        "created_at": now,
        "updated_at": now
    }
    
    task_list_data = {
        "tasks": [task_data],
        "total": 1,
        "skip": 0,
        "limit": 10
    }
    
    task_list = TaskList(**task_list_data)
    
    assert len(task_list.tasks) == 1
    assert task_list.total == 1
    assert task_list.skip == 0
    assert task_list.limit == 10


@pytest.mark.unit
def test_summary_request_valid():
    """Test SummaryRequest schema with valid data."""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    summary_request = SummaryRequest(
        start_date=start_date,
        end_date=end_date
    )
    
    assert summary_request.start_date == start_date
    assert summary_request.end_date == end_date


@pytest.mark.unit
def test_summary_request_invalid_date_range():
    """Test SummaryRequest schema with invalid date range."""
    start_date = datetime.now()
    end_date = start_date - timedelta(days=1)  # End before start
    
    with pytest.raises(ValidationError) as exc_info:
        SummaryRequest(start_date=start_date, end_date=end_date)
    
    assert "End date must be after start date" in str(exc_info.value)


@pytest.mark.unit
def test_summary_response_valid():
    """Test SummaryResponse schema with valid data."""
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    summary_response = SummaryResponse(
        summary="This is a test summary",
        start_date=start_date,
        end_date=end_date,
        task_count=5
    )
    
    assert summary_response.summary == "This is a test summary"
    assert summary_response.start_date == start_date
    assert summary_response.end_date == end_date
    assert summary_response.task_count == 5


@pytest.mark.unit
def test_extracted_title_date_valid():
    """Test ExtractedTitleDate schema with valid data."""
    extracted = ExtractedTitleDate(
        title="Buy groceries",
        due_date=datetime.now() + timedelta(days=1),
        confidence=0.95
    )
    
    assert extracted.title == "Buy groceries"
    assert extracted.due_date is not None
    assert extracted.confidence == 0.95


@pytest.mark.unit
def test_extracted_title_date_invalid_confidence():
    """Test ExtractedTitleDate schema with invalid confidence."""
    with pytest.raises(ValidationError) as exc_info:
        ExtractedTitleDate(
            title="Test",
            confidence=1.5  # Invalid confidence > 1.0
        )
    
    assert "Input should be less than or equal to 1" in str(exc_info.value)


@pytest.mark.unit
def test_extracted_label_valid():
    """Test ExtractedLabel schema with valid data."""
    extracted = ExtractedLabel(
        label="shopping",
        confidence=0.85
    )
    
    assert extracted.label == "shopping"
    assert extracted.confidence == 0.85


@pytest.mark.unit
def test_bulk_summary_valid():
    """Test BulkSummary schema with valid data."""
    bulk_summary = BulkSummary(
        summary="Summary of tasks",
        key_themes=["shopping", "work", "personal"],
        task_count=10
    )
    
    assert bulk_summary.summary == "Summary of tasks"
    assert bulk_summary.key_themes == ["shopping", "work", "personal"]
    assert bulk_summary.task_count == 10


@pytest.mark.unit
def test_error_detail_valid():
    """Test ErrorDetail schema with valid data."""
    error_detail = ErrorDetail(
        message="Validation failed",
        code="VALIDATION_ERROR",
        field="description"
    )
    
    assert error_detail.message == "Validation failed"
    assert error_detail.code == "VALIDATION_ERROR"
    assert error_detail.field == "description"


@pytest.mark.unit
def test_error_response_valid():
    """Test ErrorResponse schema with valid data."""
    error_detail = ErrorDetail(message="Test error")
    error_response = ErrorResponse(
        error="ValidationError",
        details=[error_detail]
    )
    
    assert error_response.error == "ValidationError"
    assert len(error_response.details) == 1
    assert error_response.details[0].message == "Test error"
    assert error_response.timestamp is not None


@pytest.mark.unit
def test_health_response_valid():
    """Test HealthResponse schema with valid data."""
    health_response = HealthResponse(
        status="healthy",
        service="task-manager-api",
        version="1.0.0"
    )
    
    assert health_response.status == "healthy"
    assert health_response.service == "task-manager-api"
    assert health_response.version == "1.0.0"
    assert health_response.timestamp is not None


@pytest.mark.unit
def test_task_create_missing_description():
    """Test TaskCreate schema with missing description."""
    with pytest.raises(ValidationError) as exc_info:
        TaskCreate()
    
    assert "Field required" in str(exc_info.value)


@pytest.mark.unit
def test_task_response_missing_required_fields():
    """Test TaskResponse schema with missing required fields."""
    with pytest.raises(ValidationError) as exc_info:
        TaskResponse(description="Test")
    
    assert "Field required" in str(exc_info.value)
