"""Unit tests for base worker class and strategy pattern."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from workers.base import (
    BaseWorker,
    WorkerError,
    WorkerProcessingError,
    WorkerStrategy,
    WorkerValidationError,
    execute_worker,
    get_worker_strategy,
    register_worker,
)


class TestResponse(BaseModel):
    """Test response model for structured responses."""
    title: str
    confidence: float


class MockWorker(BaseWorker):
    """Mock worker implementation for testing."""
    
    def __init__(self, should_fail_validation=False, should_fail_processing=False):
        super().__init__()
        self.should_fail_validation = should_fail_validation
        self.should_fail_processing = should_fail_processing
        self.process_called = False
        self.validate_called = False
    
    def validate_input(self, input_data):
        self.validate_called = True
        if self.should_fail_validation:
            raise WorkerValidationError("Validation failed")
        return True
    
    async def process(self, input_data):
        self.process_called = True
        if self.should_fail_processing:
            raise WorkerProcessingError("Processing failed")
        
        # Validate input first
        self.validate_input(input_data)
        
        return {
            "result": "success",
            "input_received": input_data
        }


@pytest.mark.unit
def test_worker_error_hierarchy():
    """Test that worker exceptions have correct hierarchy."""
    assert issubclass(WorkerValidationError, WorkerError)
    assert issubclass(WorkerProcessingError, WorkerError)
    assert issubclass(WorkerError, Exception)


@pytest.mark.unit
def test_base_worker_initialization():
    """Test base worker initialization."""
    worker = MockWorker()
    
    assert worker.client is not None
    assert hasattr(worker, 'available_functions')
    assert hasattr(worker, 'function_definitions')
    assert isinstance(worker.available_functions, dict)
    assert isinstance(worker.function_definitions, list)


@pytest.mark.unit
def test_base_worker_initialization_with_custom_client():
    """Test base worker initialization with custom OpenAI client."""
    mock_client = MagicMock()
    worker = MockWorker()
    worker.client = mock_client
    
    assert worker.client is mock_client


@pytest.mark.unit
async def test_mock_worker_successful_processing():
    """Test successful processing with mock worker."""
    worker = MockWorker()
    input_data = {"description": "test task"}
    
    result = await worker.process(input_data)
    
    assert worker.validate_called is True
    assert worker.process_called is True
    assert result["result"] == "success"
    assert result["input_received"] == input_data


@pytest.mark.unit
async def test_mock_worker_validation_failure():
    """Test worker validation failure."""
    worker = MockWorker(should_fail_validation=True)
    input_data = {"description": "test task"}
    
    with pytest.raises(WorkerValidationError, match="Validation failed"):
        await worker.process(input_data)
    
    assert worker.validate_called is True
    assert worker.process_called is True  # process is called but validation fails


@pytest.mark.unit
async def test_mock_worker_processing_failure():
    """Test worker processing failure."""
    worker = MockWorker(should_fail_processing=True)
    input_data = {"description": "test task"}
    
    with pytest.raises(WorkerProcessingError, match="Processing failed"):
        await worker.process(input_data)
    
    assert worker.process_called is True


@pytest.mark.unit
def test_base_worker_get_current_datetime_iso():
    """Test getting current datetime in ISO format."""
    worker = MockWorker()
    
    datetime_str = worker.get_current_datetime_iso()
    
    assert isinstance(datetime_str, str)
    assert "T" in datetime_str  # ISO format contains T
    assert len(datetime_str) > 10  # Should be longer than just date


@pytest.mark.unit
def test_base_worker_add_context_to_messages():
    """Test adding context to messages."""
    worker = MockWorker()
    messages = [
        {"role": "system", "content": "You are an expert."},
        {"role": "user", "content": "Help me."}
    ]
    context = {"timezone": "UTC", "user_id": "123"}
    
    enhanced_messages = worker.add_context_to_messages(messages, context)
    
    assert len(enhanced_messages) == 2
    assert enhanced_messages[0]["role"] == "system"
    assert "You are an expert." in enhanced_messages[0]["content"]
    assert "Additional context:" in enhanced_messages[0]["content"]
    assert "timezone: UTC" in enhanced_messages[0]["content"]
    assert "user_id: 123" in enhanced_messages[0]["content"]


@pytest.mark.unit
def test_base_worker_add_context_no_system_message():
    """Test adding context when no system message exists."""
    worker = MockWorker()
    messages = [{"role": "user", "content": "Help me."}]
    context = {"setting": "test"}
    
    enhanced_messages = worker.add_context_to_messages(messages, context)
    
    assert len(enhanced_messages) == 2
    assert enhanced_messages[0]["role"] == "system"
    assert "Additional context:" in enhanced_messages[0]["content"]
    assert "setting: test" in enhanced_messages[0]["content"]


@pytest.mark.unit
def test_base_worker_add_empty_context():
    """Test adding empty context doesn't change messages."""
    worker = MockWorker()
    messages = [{"role": "user", "content": "Help me."}]
    
    enhanced_messages = worker.add_context_to_messages(messages, {})
    
    assert enhanced_messages == messages


@pytest.mark.unit
async def test_base_worker_simple_completion():
    """Test simple completion without function calling."""
    worker = MockWorker()
    
    # Mock the client
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    
    worker.client.chat_completion = AsyncMock(return_value=mock_response)
    
    messages = [{"role": "user", "content": "Test message"}]
    result = await worker.simple_completion(messages)
    
    assert result == "Test response"
    worker.client.chat_completion.assert_called_once_with(messages=messages)


@pytest.mark.unit
async def test_base_worker_simple_completion_empty_response():
    """Test simple completion with empty response."""
    worker = MockWorker()
    
    # Mock empty response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = None
    
    worker.client.chat_completion = AsyncMock(return_value=mock_response)
    
    messages = [{"role": "user", "content": "Test message"}]
    
    with pytest.raises(WorkerProcessingError, match="Empty response from OpenAI"):
        await worker.simple_completion(messages)


@pytest.mark.unit
async def test_base_worker_simple_completion_exception():
    """Test simple completion with exception."""
    worker = MockWorker()
    
    worker.client.chat_completion = AsyncMock(side_effect=Exception("API error"))
    
    messages = [{"role": "user", "content": "Test message"}]
    
    with pytest.raises(WorkerProcessingError, match="Simple completion failed"):
        await worker.simple_completion(messages)


@pytest.mark.unit
async def test_base_worker_context_manager():
    """Test base worker as async context manager."""
    async with MockWorker() as worker:
        assert isinstance(worker, MockWorker)
        assert worker.client is not None


@pytest.mark.unit
def test_worker_strategy_initialization():
    """Test worker strategy initialization."""
    strategy = WorkerStrategy()
    
    assert isinstance(strategy._workers, dict)
    assert len(strategy._workers) == 0
    assert strategy.list_workers() == []


@pytest.mark.unit
def test_worker_strategy_register_and_get_worker():
    """Test registering and retrieving workers."""
    strategy = WorkerStrategy()
    worker = MockWorker()
    
    strategy.register_worker("test_worker", worker)
    
    assert "test_worker" in strategy.list_workers()
    retrieved_worker = strategy.get_worker("test_worker")
    assert retrieved_worker is worker
    
    # Test getting non-existent worker
    assert strategy.get_worker("non_existent") is None


@pytest.mark.unit
async def test_worker_strategy_execute_worker():
    """Test executing worker through strategy."""
    strategy = WorkerStrategy()
    worker = MockWorker()
    strategy.register_worker("test_worker", worker)
    
    input_data = {"description": "test"}
    result = await strategy.execute_worker("test_worker", input_data)
    
    assert result["result"] == "success"
    assert result["input_received"] == input_data
    assert worker.process_called is True


@pytest.mark.unit
async def test_worker_strategy_execute_nonexistent_worker():
    """Test executing non-existent worker."""
    strategy = WorkerStrategy()
    
    with pytest.raises(WorkerError, match="Worker 'nonexistent' not found"):
        await strategy.execute_worker("nonexistent", {})


@pytest.mark.unit
async def test_worker_strategy_execute_pipeline():
    """Test executing worker pipeline."""
    strategy = WorkerStrategy()
    
    # Create two workers
    worker1 = MockWorker()
    worker2 = MockWorker()
    
    strategy.register_worker("worker1", worker1)
    strategy.register_worker("worker2", worker2)
    
    pipeline = [
        {"worker": "worker1", "config": {"step": 1}},
        {"worker": "worker2", "config": {"step": 2}}
    ]
    
    initial_data = {"description": "test pipeline"}
    result = await strategy.execute_pipeline(pipeline, initial_data)
    
    # Both workers should have been called
    assert worker1.process_called is True
    assert worker2.process_called is True
    
    # Result should contain data from both steps
    assert "result" in result
    assert "input_received" in result


@pytest.mark.unit
async def test_worker_strategy_execute_pipeline_missing_worker():
    """Test executing pipeline with missing worker field."""
    strategy = WorkerStrategy()
    
    pipeline = [{"config": {"step": 1}}]  # Missing 'worker' field
    
    with pytest.raises(WorkerError, match="Pipeline step missing 'worker' field"):
        await strategy.execute_pipeline(pipeline, {})


@pytest.mark.unit
async def test_worker_strategy_execute_pipeline_nonexistent_worker():
    """Test executing pipeline with non-existent worker."""
    strategy = WorkerStrategy()
    
    pipeline = [{"worker": "nonexistent"}]
    
    with pytest.raises(WorkerError, match="Worker 'nonexistent' not found"):
        await strategy.execute_pipeline(pipeline, {})


@pytest.mark.unit
def test_global_worker_strategy():
    """Test global worker strategy functions."""
    # Clear any existing workers
    strategy = get_worker_strategy()
    strategy._workers.clear()
    
    worker = MockWorker()
    register_worker("global_test", worker)
    
    retrieved_strategy = get_worker_strategy()
    assert retrieved_strategy.get_worker("global_test") is worker


@pytest.mark.unit
async def test_global_execute_worker():
    """Test global execute worker function."""
    # Clear any existing workers
    strategy = get_worker_strategy()
    strategy._workers.clear()
    
    worker = MockWorker()
    register_worker("global_exec_test", worker)
    
    input_data = {"description": "global test"}
    result = await execute_worker("global_exec_test", input_data)
    
    assert result["result"] == "success"
    assert worker.process_called is True


@pytest.mark.unit
async def test_execute_with_function_calling_no_tools():
    """Test execute with function calling when no tools are available."""
    worker = MockWorker()
    worker.function_definitions = []  # No tools available
    
    # Mock the client
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_response.choices[0].message.tool_calls = None
    
    worker.client.chat_completion = AsyncMock(return_value=mock_response)
    
    messages = [{"role": "user", "content": "Test"}]
    result = await worker.execute_with_function_calling(messages)
    
    assert result == "Test response"
    worker.client.chat_completion.assert_called_once()


@pytest.mark.unit
async def test_execute_with_function_calling_structured_response():
    """Test execute with function calling and structured response."""
    worker = MockWorker()
    worker.function_definitions = []  # No tools to simplify test
    
    # Mock structured completion
    test_response = TestResponse(title="Test Title", confidence=0.9)
    worker.client.structured_completion = AsyncMock(return_value=test_response)
    
    messages = [{"role": "user", "content": "Test"}]
    result = await worker.execute_with_function_calling(messages, response_model=TestResponse)
    
    assert isinstance(result, TestResponse)
    assert result.title == "Test Title"
    assert result.confidence == 0.9


@pytest.mark.unit
async def test_execute_with_function_calling_empty_response():
    """Test execute with function calling with empty response."""
    worker = MockWorker()
    worker.function_definitions = []
    
    # Mock empty response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = None
    mock_response.choices[0].message.tool_calls = None
    
    worker.client.chat_completion = AsyncMock(return_value=mock_response)
    
    messages = [{"role": "user", "content": "Test"}]
    
    with pytest.raises(WorkerProcessingError, match="Empty response from OpenAI"):
        await worker.execute_with_function_calling(messages)


@pytest.mark.unit
def test_worker_strategy_list_workers():
    """Test listing workers in strategy."""
    strategy = WorkerStrategy()
    strategy._workers.clear()
    
    worker1 = MockWorker()
    worker2 = MockWorker()
    
    strategy.register_worker("worker_a", worker1)
    strategy.register_worker("worker_b", worker2)
    
    workers = strategy.list_workers()
    assert len(workers) == 2
    assert "worker_a" in workers
    assert "worker_b" in workers


@pytest.mark.unit
async def test_worker_processing_with_validation_in_process():
    """Test that process method calls validation internally."""
    worker = MockWorker()
    input_data = {"description": "test"}
    
    await worker.process(input_data)
    
    # Both validation and processing should be called
    assert worker.validate_called is True
    assert worker.process_called is True


@pytest.mark.unit
def test_base_worker_setup_function_calling():
    """Test that function calling is properly set up."""
    worker = MockWorker()
    
    # Should have function registry and definitions
    assert hasattr(worker, 'available_functions')
    assert hasattr(worker, 'function_definitions')
    
    # Should contain date calculation functions
    assert 'calculate_date_from_delta' in worker.available_functions
    assert len(worker.function_definitions) > 0
    
    # Function definitions should have proper structure
    for func_def in worker.function_definitions:
        assert 'name' in func_def
        assert 'description' in func_def
        assert 'parameters' in func_def
