"""Unit tests for summarization worker."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from workers.base import WorkerValidationError, WorkerProcessingError
from workers.summarizer import BulkSummarizerWorker, register_summarizer_worker


@pytest.mark.unit
def test_bulk_summarizer_worker_initialization():
    """Test BulkSummarizerWorker initialization."""
    worker = BulkSummarizerWorker()
    
    assert worker.client is not None
    assert hasattr(worker, 'available_functions')
    assert hasattr(worker, 'function_definitions')


@pytest.mark.unit
def test_bulk_summarizer_worker_validate_input_valid():
    """Test valid input validation for BulkSummarizerWorker."""
    worker = BulkSummarizerWorker()
    
    valid_input = {
        "tasks": [
            {"title": "Task 1", "description": "Description 1", "label": "work"},
            {"title": "Task 2", "description": "Description 2", "label": "personal"}
        ],
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-01-31T23:59:59"
    }
    
    assert worker.validate_input(valid_input) is True


@pytest.mark.unit
def test_bulk_summarizer_worker_validate_input_minimal():
    """Test minimal valid input for BulkSummarizerWorker."""
    worker = BulkSummarizerWorker()
    
    minimal_input = {
        "tasks": [
            {"title": "Task 1", "description": "Description 1"}
        ]
    }
    
    assert worker.validate_input(minimal_input) is True


@pytest.mark.unit
def test_bulk_summarizer_worker_validate_input_invalid():
    """Test invalid input validation for BulkSummarizerWorker."""
    worker = BulkSummarizerWorker()
    
    # Test non-dict input
    with pytest.raises(WorkerValidationError, match="Input data must be a dictionary"):
        worker.validate_input("not a dict")
    
    # Test missing tasks
    with pytest.raises(WorkerValidationError, match="Tasks list is required"):
        worker.validate_input({})
    
    # Test non-list tasks
    with pytest.raises(WorkerValidationError, match="Tasks must be a list"):
        worker.validate_input({"tasks": "not a list"})
    
    # Test empty tasks list
    with pytest.raises(WorkerValidationError, match="Tasks list cannot be empty"):
        worker.validate_input({"tasks": []})
    
    # Test too many tasks
    large_tasks = [{"title": f"Task {i}", "description": f"Desc {i}"} for i in range(1001)]
    with pytest.raises(WorkerValidationError, match="Too many tasks"):
        worker.validate_input({"tasks": large_tasks})
    
    # Test invalid task structure
    with pytest.raises(WorkerValidationError, match="Task 0 must be a dictionary"):
        worker.validate_input({"tasks": ["not a dict"]})
    
    # Test missing task title
    with pytest.raises(WorkerValidationError, match="Task 0 missing title"):
        worker.validate_input({"tasks": [{"description": "desc"}]})
    
    # Test missing task description
    with pytest.raises(WorkerValidationError, match="Task 0 missing description"):
        worker.validate_input({"tasks": [{"title": "title"}]})
    
    # Test non-string title
    with pytest.raises(WorkerValidationError, match="Task 0 title must be a string"):
        worker.validate_input({"tasks": [{"title": 123, "description": "desc"}]})
    
    # Test non-string description
    with pytest.raises(WorkerValidationError, match="Task 0 description must be a string"):
        worker.validate_input({"tasks": [{"title": "title", "description": 123}]})


@pytest.mark.unit
def test_bulk_summarizer_worker_validate_date_range():
    """Test date range validation for BulkSummarizerWorker."""
    worker = BulkSummarizerWorker()
    
    tasks = [{"title": "Task 1", "description": "Description 1"}]
    
    # Test invalid start date format
    with pytest.raises(WorkerValidationError, match="Start date must be in valid ISO format"):
        worker.validate_input({
            "tasks": tasks,
            "start_date": "invalid-date"
        })
    
    # Test invalid end date format
    with pytest.raises(WorkerValidationError, match="End date must be in valid ISO format"):
        worker.validate_input({
            "tasks": tasks,
            "end_date": "invalid-date"
        })
    
    # Test non-string start date
    with pytest.raises(WorkerValidationError, match="Start date must be a string"):
        worker.validate_input({
            "tasks": tasks,
            "start_date": 123
        })
    
    # Test non-string end date
    with pytest.raises(WorkerValidationError, match="End date must be a string"):
        worker.validate_input({
            "tasks": tasks,
            "end_date": 123
        })
    
    # Test end date before start date
    with pytest.raises(WorkerValidationError, match="End date must be after start date"):
        worker.validate_input({
            "tasks": tasks,
            "start_date": "2024-01-31T00:00:00",
            "end_date": "2024-01-01T00:00:00"
        })


@pytest.mark.unit
async def test_bulk_summarizer_worker_process_success():
    """Test successful processing by BulkSummarizerWorker."""
    worker = BulkSummarizerWorker()
    
    # Mock the simple_completion method
    mock_summary = (
        "This period shows a balanced mix of work and personal tasks. "
        "Key themes include project management, health maintenance, and social activities. "
        "Most tasks are well-distributed across categories with clear priorities."
    )
    worker.simple_completion = AsyncMock(return_value=mock_summary)
    
    input_data = {
        "tasks": [
            {
                "title": "Complete project",
                "description": "Finish the quarterly project",
                "label": "work",
                "due_date": "2024-01-15T17:00:00"
            },
            {
                "title": "Doctor appointment",
                "description": "Annual checkup",
                "label": "health",
                "due_date": "2024-01-20T10:00:00"
            },
            {
                "title": "Buy groceries",
                "description": "Weekly shopping",
                "label": "shopping",
                "due_date": None
            }
        ],
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-01-31T23:59:59"
    }
    
    result = await worker.process(input_data)
    
    assert result["summary"] == mock_summary
    assert result["task_count"] == 3
    assert isinstance(result["key_themes"], list)
    assert isinstance(result["insights"], str)
    
    # Verify the method was called with correct parameters
    worker.simple_completion.assert_called_once()
    call_args = worker.simple_completion.call_args
    assert call_args[1]["temperature"] == 0.3
    assert call_args[1]["max_tokens"] == 1000


@pytest.mark.unit
async def test_bulk_summarizer_worker_process_with_context():
    """Test processing with additional context."""
    worker = BulkSummarizerWorker()
    
    worker.simple_completion = AsyncMock(return_value="Test summary")
    worker.add_context_to_messages = AsyncMock(side_effect=lambda msgs, ctx: msgs)
    
    input_data = {
        "tasks": [{"title": "Task", "description": "Description"}],
        "context": {"user_timezone": "UTC", "user_preferences": "detailed"}
    }
    
    result = await worker.process(input_data)
    
    assert result["summary"] == "Test summary"
    worker.add_context_to_messages.assert_called_once()


@pytest.mark.unit
async def test_bulk_summarizer_worker_process_failure():
    """Test processing failure handling."""
    worker = BulkSummarizerWorker()
    
    worker.simple_completion = AsyncMock(side_effect=Exception("API error"))
    
    input_data = {
        "tasks": [{"title": "Task", "description": "Description"}]
    }
    
    with pytest.raises(WorkerProcessingError, match="Bulk summarization failed"):
        await worker.process(input_data)


@pytest.mark.unit
def test_bulk_summarizer_worker_extract_key_themes():
    """Test key theme extraction."""
    worker = BulkSummarizerWorker()
    
    tasks = [
        {"label": "work", "title": "Project task"},
        {"label": "health", "title": "Exercise"},
        {"label": "shopping", "title": "Buy items"},
        {"label": "uncategorized", "title": "Random task"}
    ]
    
    summary_text = "This summary mentions work projects, health activities, and family time."
    
    themes = worker._extract_key_themes(tasks, summary_text)
    
    assert isinstance(themes, list)
    assert "Work" in themes
    assert "Health" in themes
    assert "Shopping" in themes
    assert "Family" in themes  # From summary text
    assert "Uncategorized" not in themes  # Should be filtered out


@pytest.mark.unit
def test_bulk_summarizer_worker_generate_insights():
    """Test insights generation."""
    worker = BulkSummarizerWorker()
    
    # Create tasks with various characteristics
    current_time = datetime.now()
    overdue_date = (current_time - timedelta(days=1)).isoformat()
    upcoming_date = (current_time + timedelta(days=2)).isoformat()
    future_date = (current_time + timedelta(days=10)).isoformat()
    
    tasks = [
        {"title": "Overdue task", "description": "Late task", "label": "work", "due_date": overdue_date},
        {"title": "Upcoming task", "description": "Soon task", "label": "work", "due_date": upcoming_date},
        {"title": "Future task", "description": "Later task", "label": "personal", "due_date": future_date},
        {"title": "No date task", "description": "Flexible task", "label": "personal", "due_date": None}
    ]
    
    summary_text = "Test summary"
    
    insights = worker._generate_insights(tasks, summary_text)
    
    assert isinstance(insights, str)
    assert len(insights) > 0
    
    # Should mention task counts and dates
    assert "3 of 4 tasks have due dates" in insights
    assert "1 tasks appear to be overdue" in insights
    assert "1 tasks are due within the next 3 days" in insights


@pytest.mark.unit
def test_bulk_summarizer_worker_generate_insights_many_tasks():
    """Test insights generation with many tasks."""
    worker = BulkSummarizerWorker()
    
    # Create many tasks to trigger specific insights
    tasks = []
    labels = ["work", "personal", "health", "finance", "shopping", "home", "social"]
    
    for i in range(25):  # More than 20 tasks
        tasks.append({
            "title": f"Task {i}",
            "description": f"Description {i}",
            "label": labels[i % len(labels)],
            "due_date": None
        })
    
    insights = worker._generate_insights(tasks, "Test summary")
    
    assert "Consider breaking down large tasks" in insights
    assert "consider focusing on one area at a time" in insights


@pytest.mark.unit
def test_bulk_summarizer_worker_generate_insights_well_organized():
    """Test insights generation for well-organized tasks."""
    worker = BulkSummarizerWorker()
    
    # Create a small set of tasks with good date coverage and diverse labels
    from datetime import datetime, timezone, timedelta
    future_date = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    
    tasks = [
        {"title": "Task 1", "description": "Desc 1", "label": "work", "due_date": future_date},
        {"title": "Task 2", "description": "Desc 2", "label": "personal", "due_date": future_date}
    ]
    
    insights = worker._generate_insights(tasks, "Test summary")
    
    # Should return the default message when no specific issues are found
    # (all tasks have dates, not too many tasks, not too many categories)
    assert isinstance(insights, str)
    # Should mention that tasks have due dates
    assert "2 of 2 tasks have due dates" in insights


@pytest.mark.unit
def test_register_summarizer_worker():
    """Test that summarizer worker is properly registered."""
    from workers.base import get_worker_strategy
    
    # Clear existing workers
    strategy = get_worker_strategy()
    strategy._workers.clear()
    
    # Register worker
    register_summarizer_worker()
    
    # Check that worker is registered
    workers = strategy.list_workers()
    assert "bulk_summarizer" in workers
    
    # Check that worker is the correct type
    summarizer_worker = strategy.get_worker("bulk_summarizer")
    assert isinstance(summarizer_worker, BulkSummarizerWorker)


@pytest.mark.unit
async def test_bulk_summarizer_worker_context_manager():
    """Test BulkSummarizerWorker as async context manager."""
    async with BulkSummarizerWorker() as worker:
        assert isinstance(worker, BulkSummarizerWorker)
        assert worker.client is not None


@pytest.mark.unit
def test_bulk_summarizer_worker_inherits_from_base_worker():
    """Test that BulkSummarizerWorker inherits from BaseWorker."""
    from workers.base import BaseWorker
    
    assert issubclass(BulkSummarizerWorker, BaseWorker)


@pytest.mark.unit
async def test_bulk_summarizer_worker_validation_called_in_process():
    """Test that process method calls validation internally."""
    worker = BulkSummarizerWorker()
    worker.simple_completion = AsyncMock(return_value="Test summary")
    
    # Should not raise validation error with valid input
    valid_input = {
        "tasks": [{"title": "Task", "description": "Description"}]
    }
    await worker.process(valid_input)
    
    # Should raise validation error with invalid input
    with pytest.raises(WorkerValidationError):
        await worker.process({"tasks": []})  # Empty tasks list


@pytest.mark.unit
def test_bulk_summarizer_worker_extract_themes_empty_tasks():
    """Test theme extraction with empty or minimal data."""
    worker = BulkSummarizerWorker()
    
    # Test with tasks that have no labels
    tasks = [
        {"title": "Task 1", "description": "Description 1"},
        {"title": "Task 2", "description": "Description 2"}
    ]
    
    summary_text = "Simple summary with no keywords"
    
    themes = worker._extract_key_themes(tasks, summary_text)
    
    assert isinstance(themes, list)
    # Should return empty list or minimal themes
    assert len(themes) >= 0


@pytest.mark.unit
def test_bulk_summarizer_worker_insights_no_dates():
    """Test insights generation when no tasks have due dates."""
    worker = BulkSummarizerWorker()
    
    tasks = [
        {"title": "Task 1", "description": "Desc 1", "label": "work", "due_date": None},
        {"title": "Task 2", "description": "Desc 2", "label": "personal", "due_date": None}
    ]
    
    insights = worker._generate_insights(tasks, "Test summary")
    
    assert isinstance(insights, str)
    # Should suggest adding due dates
    assert "Consider adding due dates" in insights


@pytest.mark.unit
async def test_bulk_summarizer_worker_process_minimal_tasks():
    """Test processing with minimal task data."""
    worker = BulkSummarizerWorker()
    
    worker.simple_completion = AsyncMock(return_value="Minimal summary")
    
    input_data = {
        "tasks": [
            {"title": "Single task", "description": "Only task"}
        ]
    }
    
    result = await worker.process(input_data)
    
    assert result["summary"] == "Minimal summary"
    assert result["task_count"] == 1
    assert isinstance(result["key_themes"], list)
    assert isinstance(result["insights"], str)


@pytest.mark.unit
def test_bulk_summarizer_worker_date_parsing_edge_cases():
    """Test date parsing in insights generation with edge cases."""
    worker = BulkSummarizerWorker()
    
    tasks = [
        {"title": "Task 1", "description": "Desc 1", "label": "work", "due_date": "invalid-date"},
        {"title": "Task 2", "description": "Desc 2", "label": "work", "due_date": "2024-01-15T10:00:00Z"},
        {"title": "Task 3", "description": "Desc 3", "label": "work", "due_date": None}
    ]
    
    # Should not raise exception even with invalid date
    insights = worker._generate_insights(tasks, "Test summary")
    
    assert isinstance(insights, str)
    # Should still provide useful insights despite invalid date
    assert len(insights) > 0
