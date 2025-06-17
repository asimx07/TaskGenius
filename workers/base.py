"""Base worker class and strategy pattern implementation for AI processing."""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

from libs.openai_client import AsyncOpenAIClient, get_openai_client
from libs.date_tools import DATE_CALCULATION_FUNCTIONS, FUNCTION_REGISTRY

T = TypeVar('T', bound=BaseModel)


class WorkerError(Exception):
    """Base exception for worker errors."""
    pass


class WorkerValidationError(WorkerError):
    """Exception raised when worker input validation fails."""
    pass


class WorkerProcessingError(WorkerError):
    """Exception raised when worker processing fails."""
    pass


class BaseWorker(ABC):
    """
    Abstract base class for AI workers.
    
    Implements the strategy pattern for different AI processing tasks.
    All workers follow a common interface while implementing specific logic.
    """
    
    def __init__(self, openai_client: Optional[AsyncOpenAIClient] = None):
        """
        Initialize the worker.
        
        Args:
            openai_client: Optional OpenAI client instance. If None, uses global client.
        """
        self.client = openai_client or get_openai_client()
        self._setup_function_calling()
    
    def _setup_function_calling(self):
        """Setup function calling capabilities for the worker."""
        self.available_functions = FUNCTION_REGISTRY.copy()
        self.function_definitions = DATE_CALCULATION_FUNCTIONS.copy()
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return results.
        
        Args:
            input_data: Input data for processing
            
        Returns:
            Dictionary containing processing results
            
        Raises:
            WorkerError: If processing fails
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data before processing.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if input is valid
            
        Raises:
            WorkerValidationError: If input validation fails
        """
        pass
    
    async def execute_with_function_calling(
        self,
        messages: List[Dict[str, Any]],
        response_model: Optional[Type[T]] = None,
        **kwargs
    ) -> Any:
        """
        Execute OpenAI completion with function calling support.
        
        Args:
            messages: Chat messages for OpenAI
            response_model: Optional Pydantic model for structured response
            **kwargs: Additional arguments for OpenAI client
            
        Returns:
            Response from OpenAI (structured if response_model provided)
            
        Raises:
            WorkerProcessingError: If execution fails
        """
        try:
            # Prepare function calling tools
            tools = []
            if self.function_definitions:
                tools = [{"type": "function", "function": func_def} 
                        for func_def in self.function_definitions]
            
            # Make the API call
            completion = await self.client.chat_completion(
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                **kwargs
            )
            
            # Handle function calls if present
            message = completion.choices[0].message
            
            if message.tool_calls:
                # Process function calls
                function_results = []
                for tool_call in message.tool_calls:
                    if tool_call.function.name in self.available_functions:
                        func = self.available_functions[tool_call.function.name]
                        try:
                            args = json.loads(tool_call.function.arguments)
                            result = func(**args)
                            function_results.append({
                                "tool_call_id": tool_call.id,
                                "function_name": tool_call.function.name,
                                "result": result
                            })
                        except Exception as e:
                            function_results.append({
                                "tool_call_id": tool_call.id,
                                "function_name": tool_call.function.name,
                                "error": str(e)
                            })
                
                # Add function results to conversation and get final response
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": message.tool_calls
                })
                
                for result in function_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": result["tool_call_id"],
                        "content": json.dumps(result.get("result", {"error": result.get("error")}))
                    })
                
                # Get final response
                final_completion = await self.client.chat_completion(
                    messages=messages,
                    **kwargs
                )
                final_message = final_completion.choices[0].message
                
                if response_model:
                    # Parse structured response
                    try:
                        content = final_message.content
                        if not content:
                            raise WorkerProcessingError("Empty response from OpenAI")
                        response_data = json.loads(content.strip())
                        return response_model(**response_data)
                    except json.JSONDecodeError as e:
                        raise WorkerProcessingError(f"Invalid JSON response: {e}")
                    except Exception as e:
                        raise WorkerProcessingError(f"Failed to parse response: {e}")
                else:
                    return final_message.content
            
            else:
                # No function calls, handle normally
                if response_model:
                    return await self.client.structured_completion(
                        messages=messages,
                        response_model=response_model,
                        **kwargs
                    )
                else:
                    content = message.content
                    if not content:
                        raise WorkerProcessingError("Empty response from OpenAI")
                    return content.strip()
                    
        except Exception as e:
            if isinstance(e, WorkerProcessingError):
                raise
            raise WorkerProcessingError(f"Function calling execution failed: {e}")
    
    async def simple_completion(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """
        Execute simple text completion without function calling.
        
        Args:
            messages: Chat messages for OpenAI
            **kwargs: Additional arguments for OpenAI client
            
        Returns:
            Text response from OpenAI
            
        Raises:
            WorkerProcessingError: If execution fails
        """
        try:
            completion = await self.client.chat_completion(
                messages=messages,
                **kwargs
            )
            
            content = completion.choices[0].message.content
            if not content:
                raise WorkerProcessingError("Empty response from OpenAI")
            
            return content.strip()
            
        except Exception as e:
            raise WorkerProcessingError(f"Simple completion failed: {e}")
    
    def add_context_to_messages(
        self,
        messages: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Add contextual information to messages.
        
        Args:
            messages: Original messages
            context: Context to add
            
        Returns:
            Enhanced messages with context
        """
        if not context:
            return messages
        
        enhanced_messages = messages.copy()
        context_str = "Additional context:\n"
        
        for key, value in context.items():
            if value is not None:
                context_str += f"- {key}: {value}\n"
        
        # Add context to system message or create new one
        if enhanced_messages and enhanced_messages[0]["role"] == "system":
            enhanced_messages[0]["content"] += f"\n\n{context_str}"
        else:
            enhanced_messages.insert(0, {
                "role": "system",
                "content": context_str
            })
        
        return enhanced_messages
    
    def get_current_datetime_iso(self) -> str:
        """
        Get current datetime in ISO format for AI processing.
        
        Returns:
            Current datetime as ISO string
        """
        return datetime.now().isoformat()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Workers don't own the client, so don't close it
        pass


class WorkerStrategy:
    """
    Strategy pattern implementation for managing multiple workers.
    
    Allows dynamic selection and execution of different AI workers
    based on the task requirements.
    """
    
    def __init__(self):
        """Initialize the worker strategy."""
        self._workers: Dict[str, BaseWorker] = {}
    
    def register_worker(self, name: str, worker: BaseWorker):
        """
        Register a worker with the strategy.
        
        Args:
            name: Unique name for the worker
            worker: Worker instance to register
        """
        self._workers[name] = worker
    
    def get_worker(self, name: str) -> Optional[BaseWorker]:
        """
        Get a registered worker by name.
        
        Args:
            name: Name of the worker to retrieve
            
        Returns:
            Worker instance or None if not found
        """
        return self._workers.get(name)
    
    def list_workers(self) -> List[str]:
        """
        List all registered worker names.
        
        Returns:
            List of worker names
        """
        return list(self._workers.keys())
    
    async def execute_worker(
        self,
        worker_name: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a specific worker with input data.
        
        Args:
            worker_name: Name of the worker to execute
            input_data: Input data for the worker
            
        Returns:
            Processing results from the worker
            
        Raises:
            WorkerError: If worker not found or execution fails
        """
        worker = self.get_worker(worker_name)
        if not worker:
            raise WorkerError(f"Worker '{worker_name}' not found")
        
        return await worker.process(input_data)
    
    async def execute_pipeline(
        self,
        pipeline: List[Dict[str, Any]],
        initial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a pipeline of workers in sequence.
        
        Args:
            pipeline: List of pipeline steps with worker names and configs
            initial_data: Initial data for the pipeline
            
        Returns:
            Final results after all pipeline steps
            
        Raises:
            WorkerError: If any pipeline step fails
        """
        current_data = initial_data.copy()
        
        for step in pipeline:
            worker_name = step.get("worker")
            if not worker_name:
                raise WorkerError("Pipeline step missing 'worker' field")
            
            # Merge step config with current data
            step_data = current_data.copy()
            step_data.update(step.get("config", {}))
            
            # Execute worker
            result = await self.execute_worker(worker_name, step_data)
            
            # Update current data with results
            current_data.update(result)
        
        return current_data


# Global worker strategy instance
_strategy = WorkerStrategy()


def get_worker_strategy() -> WorkerStrategy:
    """
    Get the global worker strategy instance.
    
    Returns:
        Global WorkerStrategy instance
    """
    return _strategy


def register_worker(name: str, worker: BaseWorker):
    """
    Register a worker with the global strategy.
    
    Args:
        name: Unique name for the worker
        worker: Worker instance to register
    """
    _strategy.register_worker(name, worker)


async def execute_worker(worker_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a worker using the global strategy.
    
    Args:
        worker_name: Name of the worker to execute
        input_data: Input data for the worker
        
    Returns:
        Processing results from the worker
    """
    return await _strategy.execute_worker(worker_name, input_data)
