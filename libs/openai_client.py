"""Async OpenAI client wrapper with error handling and retry logic."""

import asyncio
import os
from typing import Any, Dict, List, Optional, Type, TypeVar

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


class OpenAIError(Exception):
    """Base exception for OpenAI client errors."""
    pass


class OpenAIRateLimitError(OpenAIError):
    """Exception raised when rate limit is exceeded."""
    pass


class OpenAIAPIError(OpenAIError):
    """Exception raised for API errors."""
    pass


class OpenAITimeoutError(OpenAIError):
    """Exception raised for timeout errors."""
    pass


class AsyncOpenAIClient:
    """
    Async wrapper around OpenAI client with error handling and retry logic.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout: float = 30.0,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key. If None, will use OPENAI_API_KEY env var
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
            base_delay: Base delay for exponential backoff
            max_delay: Maximum delay between retries
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.max_retries = max_retries
        self.timeout = timeout
        self.base_delay = base_delay
        self.max_delay = max_delay
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=self.timeout
        )
    
    async def _retry_with_backoff(self, func, *args, **kwargs) -> Any:
        """
        Execute function with exponential backoff retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            OpenAIError: Various OpenAI-related errors
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Convert to appropriate exception type
                if "rate_limit" in str(e).lower():
                    error = OpenAIRateLimitError(f"Rate limit exceeded: {e}")
                elif "timeout" in str(e).lower():
                    error = OpenAITimeoutError(f"Request timeout: {e}")
                else:
                    error = OpenAIAPIError(f"API error: {e}")
                
                # Don't retry on the last attempt
                if attempt == self.max_retries:
                    raise error
                
                # Calculate delay with exponential backoff
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        raise OpenAIAPIError(f"Max retries exceeded: {last_exception}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatCompletion:
        """
        Create a chat completion.
        
        Args:
            messages: List of message dictionaries
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            ChatCompletion response
            
        Raises:
            OpenAIError: Various OpenAI-related errors
        """
        async def _make_request():
            return await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        
        return await self._retry_with_backoff(_make_request)
    
    async def structured_completion(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> T:
        """
        Create a structured completion with Pydantic model validation.
        
        Args:
            messages: List of message dictionaries
            response_model: Pydantic model class for response validation
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Validated Pydantic model instance
            
        Raises:
            OpenAIError: Various OpenAI-related errors
        """
        # Add JSON format instruction to the last message
        if messages:
            last_message = messages[-1]
            if last_message.get("role") == "user":
                schema_description = response_model.model_json_schema()
                format_instruction = (
                    f"\n\nPlease respond with valid JSON that matches this schema:\n"
                    f"{schema_description}\n"
                    f"Respond only with the JSON, no additional text."
                )
                last_message["content"] += format_instruction
        
        # Make the API call
        completion = await self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Extract and validate the response
        import json
        import re
        try:
            content = completion.choices[0].message.content
            if not content:
                raise OpenAIAPIError("Empty response from OpenAI")
            
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
            if json_match:
                json_content = json_match.group(1).strip()
            else:
                json_content = content.strip()
            
            # Parse JSON and validate with Pydantic model
            response_data = json.loads(json_content)
            return response_model(**response_data)
            
        except json.JSONDecodeError as e:
            raise OpenAIAPIError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise OpenAIAPIError(f"Failed to parse response: {e}")
    
    async def simple_completion(
        self,
        prompt: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Create a simple text completion.
        
        Args:
            prompt: Input prompt
            model: OpenAI model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Generated text response
            
        Raises:
            OpenAIError: Various OpenAI-related errors
        """
        messages = [{"role": "user", "content": prompt}]
        completion = await self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        content = completion.choices[0].message.content
        if not content:
            raise OpenAIAPIError("Empty response from OpenAI")
        
        return content.strip()
    
    async def close(self):
        """Close the client connection."""
        await self.client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Global client instance
_client: Optional[AsyncOpenAIClient] = None


def get_openai_client() -> AsyncOpenAIClient:
    """
    Get or create the global OpenAI client instance.
    
    Returns:
        AsyncOpenAIClient instance
    """
    global _client
    if _client is None:
        _client = AsyncOpenAIClient()
    return _client


async def close_openai_client():
    """Close the global OpenAI client instance."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
