"""Custom exception classes for the task manager application."""

from typing import Any, Dict, Optional


class TaskManagerError(Exception):
    """Base exception for all task manager errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(TaskManagerError):
    """Exception raised for input validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field: Field that failed validation
            value: Invalid value
        """
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        
        super().__init__(message, details)
        self.field = field
        self.value = value


class DatabaseError(TaskManagerError):
    """Exception raised for database operation errors."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        """
        Initialize database error.
        
        Args:
            message: Error message
            operation: Database operation that failed
        """
        details = {}
        if operation:
            details["operation"] = operation
        
        super().__init__(message, details)
        self.operation = operation


class AIProcessingError(TaskManagerError):
    """Exception raised for AI processing errors."""
    
    def __init__(
        self, 
        message: str, 
        worker: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize AI processing error.
        
        Args:
            message: Error message
            worker: Worker that failed
            input_data: Input data that caused the error
        """
        details = {}
        if worker:
            details["worker"] = worker
        if input_data:
            # Don't include sensitive data in error details
            safe_input = {k: v for k, v in input_data.items() 
                         if k not in ["api_key", "token", "password"]}
            details["input_data"] = safe_input
        
        super().__init__(message, details)
        self.worker = worker
        self.input_data = input_data


class TaskNotFoundError(TaskManagerError):
    """Exception raised when a task is not found."""
    
    def __init__(self, task_id: int):
        """
        Initialize task not found error.
        
        Args:
            task_id: ID of the task that was not found
        """
        message = f"Task with ID {task_id} not found"
        details = {"task_id": task_id}
        
        super().__init__(message, details)
        self.task_id = task_id


class RateLimitError(TaskManagerError):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        """
        Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
        """
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(message, details)
        self.retry_after = retry_after


class ConfigurationError(TaskManagerError):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_key: Configuration key that is invalid
        """
        details = {}
        if config_key:
            details["config_key"] = config_key
        
        super().__init__(message, details)
        self.config_key = config_key


class AuthenticationError(TaskManagerError):
    """Exception raised for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed"):
        """
        Initialize authentication error.
        
        Args:
            message: Error message
        """
        super().__init__(message)


class AuthorizationError(TaskManagerError):
    """Exception raised for authorization errors."""
    
    def __init__(self, message: str = "Access denied"):
        """
        Initialize authorization error.
        
        Args:
            message: Error message
        """
        super().__init__(message)


# Error code mappings for API responses
ERROR_CODES = {
    ValidationError: "VALIDATION_ERROR",
    DatabaseError: "DATABASE_ERROR", 
    AIProcessingError: "AI_PROCESSING_ERROR",
    TaskNotFoundError: "TASK_NOT_FOUND",
    RateLimitError: "RATE_LIMIT_EXCEEDED",
    ConfigurationError: "CONFIGURATION_ERROR",
    AuthenticationError: "AUTHENTICATION_ERROR",
    AuthorizationError: "AUTHORIZATION_ERROR",
    TaskManagerError: "GENERAL_ERROR"
}


def get_error_code(exception: Exception) -> str:
    """
    Get error code for an exception.
    
    Args:
        exception: Exception instance
        
    Returns:
        Error code string
    """
    for exc_type, code in ERROR_CODES.items():
        if isinstance(exception, exc_type):
            return code
    
    return "UNKNOWN_ERROR"


def format_error_response(exception: Exception) -> Dict[str, Any]:
    """
    Format an exception into a standardized error response.
    
    Args:
        exception: Exception to format
        
    Returns:
        Formatted error response dictionary
    """
    if isinstance(exception, TaskManagerError):
        return {
            "error": {
                "code": get_error_code(exception),
                "message": exception.message,
                "details": exception.details
            }
        }
    else:
        return {
            "error": {
                "code": "UNKNOWN_ERROR",
                "message": str(exception),
                "details": {}
            }
        }
