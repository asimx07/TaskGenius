"""Unit tests for OpenAI client wrapper."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from pydantic import BaseModel

from libs.openai_client import (
    AsyncOpenAIClient,
    OpenAIAPIError,
    OpenAIError,
    OpenAIRateLimitError,
    OpenAITimeoutError,
    close_openai_client,
    get_openai_client,
)


class TestResponse(BaseModel):
    """Test Pydantic model for structured responses."""
    title: str
    confidence: float


@pytest.mark.unit
async def test_openai_client_initialization():
    """Test OpenAI client initialization."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        client = AsyncOpenAIClient()
        assert client.api_key == "test-key"
        assert client.max_retries == 3
        assert client.timeout == 30.0


@pytest.mark.unit
async def test_openai_client_initialization_with_params():
    """Test OpenAI client initialization with custom parameters."""
    client = AsyncOpenAIClient(
        api_key="custom-key",
        max_retries=5,
        timeout=60.0,
        base_delay=2.0,
        max_delay=120.0
    )
    assert client.api_key == "custom-key"
    assert client.max_retries == 5
    assert client.timeout == 60.0
    assert client.base_delay == 2.0
    assert client.max_delay == 120.0


@pytest.mark.unit
async def test_openai_client_no_api_key():
    """Test OpenAI client initialization without API key."""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            AsyncOpenAIClient()


@pytest.mark.unit
async def test_chat_completion_success():
    """Test successful chat completion."""
    # Mock response
    mock_response = ChatCompletion(
        id="test-id",
        object="chat.completion",
        created=1234567890,
        model="gpt-3.5-turbo",
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content="Test response"
                ),
                finish_reason="stop"
            )
        ]
    )
    
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        client = AsyncOpenAIClient()
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            messages = [{"role": "user", "content": "Test message"}]
            result = await client.chat_completion(messages)
            
            assert result == mock_response
            mock_create.assert_called_once_with(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=None
            )


@pytest.mark.unit
async def test_simple_completion_success():
    """Test successful simple completion."""
    # Mock response
    mock_response = ChatCompletion(
        id="test-id",
        object="chat.completion",
        created=1234567890,
        model="gpt-3.5-turbo",
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content="Simple response"
                ),
                finish_reason="stop"
            )
        ]
    )
    
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        client = AsyncOpenAIClient()
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            result = await client.simple_completion("Test prompt")
            
            assert result == "Simple response"
            mock_create.assert_called_once()


@pytest.mark.unit
async def test_structured_completion_success():
    """Test successful structured completion."""
    # Mock response with JSON
    test_json = {"title": "Test Title", "confidence": 0.95}
    mock_response = ChatCompletion(
        id="test-id",
        object="chat.completion",
        created=1234567890,
        model="gpt-3.5-turbo",
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content=json.dumps(test_json)
                ),
                finish_reason="stop"
            )
        ]
    )
    
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        client = AsyncOpenAIClient()
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            messages = [{"role": "user", "content": "Extract title"}]
            result = await client.structured_completion(messages, TestResponse)
            
            assert isinstance(result, TestResponse)
            assert result.title == "Test Title"
            assert result.confidence == 0.95


@pytest.mark.unit
async def test_structured_completion_invalid_json():
    """Test structured completion with invalid JSON response."""
    # Mock response with invalid JSON
    mock_response = ChatCompletion(
        id="test-id",
        object="chat.completion",
        created=1234567890,
        model="gpt-3.5-turbo",
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content="Invalid JSON response"
                ),
                finish_reason="stop"
            )
        ]
    )
    
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        client = AsyncOpenAIClient()
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            messages = [{"role": "user", "content": "Extract title"}]
            
            with pytest.raises(OpenAIAPIError, match="Invalid JSON response"):
                await client.structured_completion(messages, TestResponse)


@pytest.mark.unit
async def test_structured_completion_empty_response():
    """Test structured completion with empty response."""
    # Mock response with empty content
    mock_response = ChatCompletion(
        id="test-id",
        object="chat.completion",
        created=1234567890,
        model="gpt-3.5-turbo",
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content=None
                ),
                finish_reason="stop"
            )
        ]
    )
    
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        client = AsyncOpenAIClient()
        
        with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            
            messages = [{"role": "user", "content": "Extract title"}]
            
            with pytest.raises(OpenAIAPIError, match="Empty response from OpenAI"):
                await client.structured_completion(messages, TestResponse)


@pytest.mark.unit
async def test_retry_with_backoff_rate_limit():
    """Test retry logic with rate limit error."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        client = AsyncOpenAIClient(max_retries=2, base_delay=0.01)
        
        # Mock function that fails with rate limit error
        mock_func = AsyncMock()
        mock_func.side_effect = [
            Exception("rate_limit exceeded"),
            Exception("rate_limit exceeded"),
            "success"
        ]
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await client._retry_with_backoff(mock_func)
            assert result == "success"
            assert mock_func.call_count == 3


@pytest.mark.unit
async def test_retry_with_backoff_max_retries_exceeded():
    """Test retry logic when max retries are exceeded."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        client = AsyncOpenAIClient(max_retries=1, base_delay=0.01)
        
        # Mock function that always fails
        mock_func = AsyncMock()
        mock_func.side_effect = Exception("rate_limit exceeded")
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(OpenAIRateLimitError, match="Rate limit exceeded"):
                await client._retry_with_backoff(mock_func)
            
            assert mock_func.call_count == 2  # Initial + 1 retry


@pytest.mark.unit
async def test_retry_with_backoff_timeout_error():
    """Test retry logic with timeout error."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        client = AsyncOpenAIClient(max_retries=1, base_delay=0.01)
        
        # Mock function that fails with timeout error
        mock_func = AsyncMock()
        mock_func.side_effect = Exception("timeout occurred")
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(OpenAITimeoutError, match="Request timeout"):
                await client._retry_with_backoff(mock_func)


@pytest.mark.unit
async def test_retry_with_backoff_api_error():
    """Test retry logic with general API error."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        client = AsyncOpenAIClient(max_retries=1, base_delay=0.01)
        
        # Mock function that fails with general error
        mock_func = AsyncMock()
        mock_func.side_effect = Exception("general api error")
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            with pytest.raises(OpenAIAPIError, match="API error"):
                await client._retry_with_backoff(mock_func)


@pytest.mark.unit
async def test_context_manager():
    """Test async context manager functionality."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        async with AsyncOpenAIClient() as client:
            assert isinstance(client, AsyncOpenAIClient)
            
        # Client should be closed after context manager


@pytest.mark.unit
async def test_global_client_functions():
    """Test global client getter and closer functions."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        # Get client
        client1 = get_openai_client()
        assert isinstance(client1, AsyncOpenAIClient)
        
        # Get same client instance
        client2 = get_openai_client()
        assert client1 is client2
        
        # Close client
        await close_openai_client()
        
        # Get new client instance
        client3 = get_openai_client()
        assert client3 is not client1


@pytest.mark.unit
async def test_exponential_backoff_delay_calculation():
    """Test exponential backoff delay calculation."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        client = AsyncOpenAIClient(base_delay=1.0, max_delay=10.0)
        
        # Mock function that fails multiple times
        mock_func = AsyncMock()
        mock_func.side_effect = [
            Exception("error"),
            Exception("error"),
            Exception("error"),
            "success"
        ]
        
        delays = []
        
        async def mock_sleep(delay):
            delays.append(delay)
        
        with patch('asyncio.sleep', side_effect=mock_sleep):
            result = await client._retry_with_backoff(mock_func)
            assert result == "success"
            
            # Check exponential backoff: 1.0, 2.0, 4.0
            assert len(delays) == 3
            assert delays[0] == 1.0
            assert delays[1] == 2.0
            assert delays[2] == 4.0


@pytest.mark.unit
async def test_max_delay_cap():
    """Test that delay is capped at max_delay."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        client = AsyncOpenAIClient(base_delay=10.0, max_delay=15.0, max_retries=3)
        
        # Mock function that fails multiple times
        mock_func = AsyncMock()
        mock_func.side_effect = [
            Exception("error"),
            Exception("error"),
            Exception("error"),
            "success"
        ]
        
        delays = []
        
        async def mock_sleep(delay):
            delays.append(delay)
        
        with patch('asyncio.sleep', side_effect=mock_sleep):
            result = await client._retry_with_backoff(mock_func)
            assert result == "success"
            
            # Check that delay is capped: 10.0, 15.0 (capped), 15.0 (capped)
            assert len(delays) == 3
            assert delays[0] == 10.0
            assert delays[1] == 15.0  # Capped at max_delay
            assert delays[2] == 15.0  # Capped at max_delay
