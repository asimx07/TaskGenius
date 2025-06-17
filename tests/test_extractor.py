"""Unit tests for extraction workers."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from libs.schema import TaskExtractionResult, LabelExtractionResult
from workers.base import WorkerValidationError, WorkerProcessingError
from workers.extractor import (
    ExtractTitleDateWorker,
    ExtractLabelWorker,
    ExtractPriorityWorker,
    register_extraction_workers,
)


@pytest.mark.unit
def test_extract_title_date_worker_initialization():
    """Test ExtractTitleDateWorker initialization."""
    worker = ExtractTitleDateWorker()
    
    assert worker.client is not None
    assert hasattr(worker, 'available_functions')
    assert hasattr(worker, 'function_definitions')


@pytest.mark.unit
def test_extract_title_date_worker_validate_input_valid():
    """Test valid input validation for ExtractTitleDateWorker."""
    worker = ExtractTitleDateWorker()
    
    valid_input = {"description": "Call the dentist tomorrow"}
    assert worker.validate_input(valid_input) is True


@pytest.mark.unit
def test_extract_title_date_worker_validate_input_invalid():
    """Test invalid input validation for ExtractTitleDateWorker."""
    worker = ExtractTitleDateWorker()
    
    # Test missing description
    with pytest.raises(WorkerValidationError, match="Description is required"):
        worker.validate_input({})
    
    # Test non-string description
    with pytest.raises(WorkerValidationError, match="Description must be a string"):
        worker.validate_input({"description": 123})
    
    # Test empty description
    with pytest.raises(WorkerValidationError, match="Description cannot be empty"):
        worker.validate_input({"description": ""})
    
    # Test too long description
    long_desc = "x" * 1001
    with pytest.raises(WorkerValidationError, match="Description too long"):
        worker.validate_input({"description": long_desc})
    
    # Test non-dict input
    with pytest.raises(WorkerValidationError, match="Input data must be a dictionary"):
        worker.validate_input("not a dict")


@pytest.mark.unit
async def test_extract_title_date_worker_process_success():
    """Test successful processing by ExtractTitleDateWorker."""
    worker = ExtractTitleDateWorker()
    
    # Mock the execute_with_function_calling method
    mock_result = TaskExtractionResult(
        title="Call dentist",
        due_date=datetime(2024, 1, 16, 10, 0),
        confidence=0.9,
        reasoning="Extracted 'call dentist' as action and 'tomorrow' as due date"
    )
    
    worker.execute_with_function_calling = AsyncMock(return_value=mock_result)
    
    input_data = {"description": "Call the dentist tomorrow"}
    result = await worker.process(input_data)
    
    assert result["title"] == "Call dentist"
    assert result["due_date"] == "2024-01-16T10:00:00"
    assert result["confidence"] == 0.9
    assert "reasoning" in result
    
    # Verify the method was called with correct parameters
    worker.execute_with_function_calling.assert_called_once()
    call_args = worker.execute_with_function_calling.call_args
    assert call_args[1]["response_model"] == TaskExtractionResult
    assert call_args[1]["temperature"] == 0.1


@pytest.mark.unit
async def test_extract_title_date_worker_process_no_due_date():
    """Test processing when no due date is found."""
    worker = ExtractTitleDateWorker()
    
    # Mock result with no due date
    mock_result = TaskExtractionResult(
        title="Read book",
        due_date=None,
        confidence=0.8,
        reasoning="No specific date mentioned"
    )
    
    worker.execute_with_function_calling = AsyncMock(return_value=mock_result)
    
    input_data = {"description": "Read a good book"}
    result = await worker.process(input_data)
    
    assert result["title"] == "Read book"
    assert result["due_date"] is None
    assert result["confidence"] == 0.8


@pytest.mark.unit
async def test_extract_title_date_worker_process_with_context():
    """Test processing with additional context."""
    worker = ExtractTitleDateWorker()
    
    mock_result = TaskExtractionResult(
        title="Team meeting",
        due_date=datetime(2024, 1, 17, 14, 0),
        confidence=0.95,
        reasoning="Meeting scheduled for specific time"
    )
    
    worker.execute_with_function_calling = AsyncMock(return_value=mock_result)
    worker.add_context_to_messages = MagicMock(side_effect=lambda msgs, ctx: msgs)
    
    input_data = {
        "description": "Team meeting at 2pm tomorrow",
        "context": {"timezone": "UTC", "user_id": "123"}
    }
    
    result = await worker.process(input_data)
    
    assert result["title"] == "Team meeting"
    worker.add_context_to_messages.assert_called_once()


@pytest.mark.unit
async def test_extract_title_date_worker_process_failure():
    """Test processing failure handling."""
    worker = ExtractTitleDateWorker()
    
    worker.execute_with_function_calling = AsyncMock(side_effect=Exception("API error"))
    
    input_data = {"description": "Call the dentist"}
    
    with pytest.raises(WorkerProcessingError, match="Title and date extraction failed"):
        await worker.process(input_data)


@pytest.mark.unit
def test_extract_label_worker_initialization():
    """Test ExtractLabelWorker initialization."""
    worker = ExtractLabelWorker()
    
    assert worker.client is not None
    assert hasattr(worker, 'available_functions')


@pytest.mark.unit
def test_extract_label_worker_validate_input_valid():
    """Test valid input validation for ExtractLabelWorker."""
    worker = ExtractLabelWorker()
    
    valid_input = {
        "description": "Buy groceries including milk and bread",
        "title": "Buy groceries"
    }
    assert worker.validate_input(valid_input) is True


@pytest.mark.unit
def test_extract_label_worker_validate_input_invalid():
    """Test invalid input validation for ExtractLabelWorker."""
    worker = ExtractLabelWorker()
    
    # Test missing description
    with pytest.raises(WorkerValidationError, match="Description is required"):
        worker.validate_input({"title": "Test"})
    
    # Test missing title
    with pytest.raises(WorkerValidationError, match="Title is required"):
        worker.validate_input({"description": "Test description"})
    
    # Test non-string inputs
    with pytest.raises(WorkerValidationError, match="Description and title must be strings"):
        worker.validate_input({"description": 123, "title": "Test"})
    
    # Test empty inputs
    with pytest.raises(WorkerValidationError, match="Description and title cannot be empty"):
        worker.validate_input({"description": "", "title": "Test"})


@pytest.mark.unit
async def test_extract_label_worker_process_success():
    """Test successful processing by ExtractLabelWorker."""
    worker = ExtractLabelWorker()
    
    # Mock the execute_with_function_calling method
    mock_result = LabelExtractionResult(
        label="shopping",
        confidence=0.9,
        reasoning="Task involves purchasing items, categorized as shopping"
    )
    
    worker.execute_with_function_calling = AsyncMock(return_value=mock_result)
    
    input_data = {
        "description": "Buy groceries including milk and bread",
        "title": "Buy groceries"
    }
    result = await worker.process(input_data)
    
    assert result["label"] == "shopping"
    assert result["confidence"] == 0.9
    assert "reasoning" in result
    
    # Verify the method was called with correct parameters
    worker.execute_with_function_calling.assert_called_once()
    call_args = worker.execute_with_function_calling.call_args
    assert call_args[1]["response_model"] == LabelExtractionResult
    assert call_args[1]["temperature"] == 0.2


@pytest.mark.unit
async def test_extract_label_worker_process_failure():
    """Test processing failure handling for ExtractLabelWorker."""
    worker = ExtractLabelWorker()
    
    worker.execute_with_function_calling = AsyncMock(side_effect=Exception("API error"))
    
    input_data = {
        "description": "Buy groceries",
        "title": "Buy groceries"
    }
    
    with pytest.raises(WorkerProcessingError, match="Label extraction failed"):
        await worker.process(input_data)


@pytest.mark.unit
def test_extract_priority_worker_initialization():
    """Test ExtractPriorityWorker initialization."""
    worker = ExtractPriorityWorker()
    
    assert worker.client is not None
    assert hasattr(worker, 'available_functions')


@pytest.mark.unit
def test_extract_priority_worker_validate_input_valid():
    """Test valid input validation for ExtractPriorityWorker."""
    worker = ExtractPriorityWorker()
    
    # Valid input without due date
    valid_input = {
        "description": "URGENT: Submit tax documents",
        "title": "Submit tax documents"
    }
    assert worker.validate_input(valid_input) is True
    
    # Valid input with due date
    valid_input_with_date = {
        "description": "Submit tax documents",
        "title": "Submit tax documents",
        "due_date": "2024-01-16T23:59:59"
    }
    assert worker.validate_input(valid_input_with_date) is True


@pytest.mark.unit
def test_extract_priority_worker_validate_input_invalid():
    """Test invalid input validation for ExtractPriorityWorker."""
    worker = ExtractPriorityWorker()
    
    # Test missing description
    with pytest.raises(WorkerValidationError, match="Description is required"):
        worker.validate_input({"title": "Test"})
    
    # Test missing title
    with pytest.raises(WorkerValidationError, match="Title is required"):
        worker.validate_input({"description": "Test description"})
    
    # Test invalid due date format
    with pytest.raises(WorkerValidationError, match="Due date must be in valid ISO format"):
        worker.validate_input({
            "description": "Test",
            "title": "Test",
            "due_date": "invalid-date"
        })
    
    # Test non-string due date
    with pytest.raises(WorkerValidationError, match="Due date must be a string if provided"):
        worker.validate_input({
            "description": "Test",
            "title": "Test",
            "due_date": 123
        })


@pytest.mark.unit
async def test_extract_priority_worker_process_high_priority():
    """Test processing high priority task."""
    worker = ExtractPriorityWorker()
    
    # Mock simple_completion to return high priority response
    worker.simple_completion = AsyncMock(return_value="High priority\nThis task is urgent and time-sensitive.")
    
    input_data = {
        "description": "URGENT: Submit tax documents before deadline",
        "title": "Submit tax documents",
        "due_date": "2024-01-16T23:59:59"
    }
    
    result = await worker.process(input_data)
    
    assert result["priority"] == "high"
    assert result["confidence"] == 0.8
    assert "reasoning" in result


@pytest.mark.unit
async def test_extract_priority_worker_process_medium_priority():
    """Test processing medium priority task."""
    worker = ExtractPriorityWorker()
    
    worker.simple_completion = AsyncMock(return_value="Medium priority\nImportant but not urgent.")
    
    input_data = {
        "description": "Prepare presentation for next week",
        "title": "Prepare presentation"
    }
    
    result = await worker.process(input_data)
    
    assert result["priority"] == "medium"
    assert result["confidence"] == 0.8


@pytest.mark.unit
async def test_extract_priority_worker_process_low_priority():
    """Test processing low priority task."""
    worker = ExtractPriorityWorker()
    
    worker.simple_completion = AsyncMock(return_value="Low priority\nCan be done when time allows.")
    
    input_data = {
        "description": "Read a book when I have time",
        "title": "Read book"
    }
    
    result = await worker.process(input_data)
    
    assert result["priority"] == "low"
    assert result["confidence"] == 0.8


@pytest.mark.unit
async def test_extract_priority_worker_process_unclear_priority():
    """Test processing when priority is unclear."""
    worker = ExtractPriorityWorker()
    
    worker.simple_completion = AsyncMock(return_value="This task seems moderately important.")
    
    input_data = {
        "description": "Some task description",
        "title": "Some task"
    }
    
    result = await worker.process(input_data)
    
    assert result["priority"] == "medium"  # Default when unclear
    assert result["confidence"] == 0.6  # Lower confidence


@pytest.mark.unit
async def test_extract_priority_worker_process_failure():
    """Test processing failure handling for ExtractPriorityWorker."""
    worker = ExtractPriorityWorker()
    
    worker.simple_completion = AsyncMock(side_effect=Exception("API error"))
    
    input_data = {
        "description": "Some task",
        "title": "Some task"
    }
    
    with pytest.raises(WorkerProcessingError, match="Priority extraction failed"):
        await worker.process(input_data)


@pytest.mark.unit
def test_register_extraction_workers():
    """Test that extraction workers are properly registered."""
    from workers.base import get_worker_strategy
    
    # Clear existing workers
    strategy = get_worker_strategy()
    strategy._workers.clear()
    
    # Register workers
    register_extraction_workers()
    
    # Check that workers are registered
    workers = strategy.list_workers()
    assert "extract_title_date" in workers
    assert "extract_label" in workers
    assert "extract_priority" in workers
    
    # Check that workers are the correct type
    title_date_worker = strategy.get_worker("extract_title_date")
    label_worker = strategy.get_worker("extract_label")
    priority_worker = strategy.get_worker("extract_priority")
    
    assert isinstance(title_date_worker, ExtractTitleDateWorker)
    assert isinstance(label_worker, ExtractLabelWorker)
    assert isinstance(priority_worker, ExtractPriorityWorker)


@pytest.mark.unit
async def test_extract_title_date_worker_context_manager():
    """Test ExtractTitleDateWorker as async context manager."""
    async with ExtractTitleDateWorker() as worker:
        assert isinstance(worker, ExtractTitleDateWorker)
        assert worker.client is not None


@pytest.mark.unit
async def test_extract_label_worker_context_manager():
    """Test ExtractLabelWorker as async context manager."""
    async with ExtractLabelWorker() as worker:
        assert isinstance(worker, ExtractLabelWorker)
        assert worker.client is not None


@pytest.mark.unit
async def test_extract_priority_worker_context_manager():
    """Test ExtractPriorityWorker as async context manager."""
    async with ExtractPriorityWorker() as worker:
        assert isinstance(worker, ExtractPriorityWorker)
        assert worker.client is not None


@pytest.mark.unit
def test_extract_title_date_worker_get_current_datetime():
    """Test getting current datetime from ExtractTitleDateWorker."""
    worker = ExtractTitleDateWorker()
    
    datetime_str = worker.get_current_datetime_iso()
    
    assert isinstance(datetime_str, str)
    assert "T" in datetime_str
    
    # Should be parseable as datetime
    parsed_dt = datetime.fromisoformat(datetime_str)
    assert isinstance(parsed_dt, datetime)


@pytest.mark.unit
async def test_workers_validation_called_in_process():
    """Test that all workers call validation in their process methods."""
    # Test ExtractTitleDateWorker
    title_date_worker = ExtractTitleDateWorker()
    title_date_worker.execute_with_function_calling = AsyncMock(
        return_value=TaskExtractionResult(
            title="Test", due_date=None, confidence=0.8, reasoning="Test"
        )
    )
    
    # Should not raise validation error with valid input
    await title_date_worker.process({"description": "Valid description"})
    
    # Should raise validation error with invalid input
    with pytest.raises(WorkerValidationError):
        await title_date_worker.process({})
    
    # Test ExtractLabelWorker
    label_worker = ExtractLabelWorker()
    label_worker.execute_with_function_calling = AsyncMock(
        return_value=LabelExtractionResult(
            label="test", confidence=0.8, reasoning="Test"
        )
    )
    
    # Should not raise validation error with valid input
    await label_worker.process({"description": "Valid", "title": "Valid"})
    
    # Should raise validation error with invalid input
    with pytest.raises(WorkerValidationError):
        await label_worker.process({"description": "Valid"})  # Missing title
    
    # Test ExtractPriorityWorker
    priority_worker = ExtractPriorityWorker()
    priority_worker.simple_completion = AsyncMock(return_value="Medium priority")
    
    # Should not raise validation error with valid input
    await priority_worker.process({"description": "Valid", "title": "Valid"})
    
    # Should raise validation error with invalid input
    with pytest.raises(WorkerValidationError):
        await priority_worker.process({"description": "Valid"})  # Missing title


@pytest.mark.unit
def test_all_workers_inherit_from_base_worker():
    """Test that all extraction workers inherit from BaseWorker."""
    from workers.base import BaseWorker
    
    assert issubclass(ExtractTitleDateWorker, BaseWorker)
    assert issubclass(ExtractLabelWorker, BaseWorker)
    assert issubclass(ExtractPriorityWorker, BaseWorker)
