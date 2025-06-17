"""AI workers for extracting task information from natural language descriptions."""

from datetime import datetime
from typing import Any, Dict, Optional

from libs.prompts import PromptTemplates
from libs.schema import TaskExtractionResult, LabelExtractionResult
from workers.base import BaseWorker, WorkerValidationError, WorkerProcessingError


class ExtractTitleDateWorker(BaseWorker):
    """
    Worker for extracting task title and due date from natural language descriptions.
    
    Uses AI with function calling to intelligently parse dates and extract concise titles.
    """
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data for title and date extraction.
        
        Args:
            input_data: Input data containing task description
            
        Returns:
            True if input is valid
            
        Raises:
            WorkerValidationError: If input validation fails
        """
        if not isinstance(input_data, dict):
            raise WorkerValidationError("Input data must be a dictionary")
        
        description = input_data.get("description")
        if not description:
            raise WorkerValidationError("Description is required")
        
        if not isinstance(description, str):
            raise WorkerValidationError("Description must be a string")
        
        if len(description.strip()) == 0:
            raise WorkerValidationError("Description cannot be empty")
        
        if len(description) > 1000:
            raise WorkerValidationError("Description too long (max 1000 characters)")
        
        return True
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract title and due date from task description.
        
        Args:
            input_data: Dictionary containing:
                - description (str): Task description in natural language
                - context (dict, optional): Additional context for processing
                
        Returns:
            Dictionary containing:
                - title (str): Extracted task title
                - due_date (str|None): Extracted due date in ISO format or None
                - confidence (float): Confidence score for extraction
                - reasoning (str): Explanation of extraction logic
                
        Raises:
            WorkerProcessingError: If extraction fails
        """
        # Validate input
        self.validate_input(input_data)
        
        try:
            description = input_data["description"]
            context = input_data.get("context", {})
            current_datetime = self.get_current_datetime_iso()
            
            # Generate prompt messages
            messages = PromptTemplates.extract_title_and_date(description, current_datetime)
            
            # Add context if provided
            if context:
                messages = self.add_context_to_messages(messages, context)
            
            # Execute with function calling for date parsing
            result = await self.execute_with_function_calling(
                messages=messages,
                response_model=TaskExtractionResult,
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=500
            )
            
            # Convert result to dictionary format
            return {
                "title": result.title,
                "due_date": result.due_date.isoformat() if result.due_date else None,
                "confidence": result.confidence,
                "reasoning": result.reasoning
            }
            
        except Exception as e:
            if isinstance(e, (WorkerValidationError, WorkerProcessingError)):
                raise
            raise WorkerProcessingError(f"Title and date extraction failed: {e}")


class ExtractLabelWorker(BaseWorker):
    """
    Worker for extracting task labels/categories from descriptions and titles.
    
    Categorizes tasks into appropriate labels based on content analysis.
    """
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data for label extraction.
        
        Args:
            input_data: Input data containing description and title
            
        Returns:
            True if input is valid
            
        Raises:
            WorkerValidationError: If input validation fails
        """
        if not isinstance(input_data, dict):
            raise WorkerValidationError("Input data must be a dictionary")
        
        description = input_data.get("description")
        title = input_data.get("title")
        
        if not description:
            raise WorkerValidationError("Description is required")
        
        if not title:
            raise WorkerValidationError("Title is required")
        
        if not isinstance(description, str) or not isinstance(title, str):
            raise WorkerValidationError("Description and title must be strings")
        
        if len(description.strip()) == 0 or len(title.strip()) == 0:
            raise WorkerValidationError("Description and title cannot be empty")
        
        return True
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract label/category from task description and title.
        
        Args:
            input_data: Dictionary containing:
                - description (str): Task description
                - title (str): Task title
                - context (dict, optional): Additional context
                
        Returns:
            Dictionary containing:
                - label (str): Extracted task label/category
                - confidence (float): Confidence score for categorization
                - reasoning (str): Explanation of categorization logic
                
        Raises:
            WorkerProcessingError: If extraction fails
        """
        # Validate input
        self.validate_input(input_data)
        
        try:
            description = input_data["description"]
            title = input_data["title"]
            context = input_data.get("context", {})
            
            # Generate prompt messages
            messages = PromptTemplates.extract_label(description, title)
            
            # Add context if provided
            if context:
                messages = self.add_context_to_messages(messages, context)
            
            # Execute simple completion (no function calling needed for labels)
            result = await self.execute_with_function_calling(
                messages=messages,
                response_model=LabelExtractionResult,
                temperature=0.2,  # Slightly higher temperature for creativity in categorization
                max_tokens=300
            )
            
            # Convert result to dictionary format
            return {
                "label": result.label,
                "confidence": result.confidence,
                "reasoning": result.reasoning
            }
            
        except Exception as e:
            if isinstance(e, (WorkerValidationError, WorkerProcessingError)):
                raise
            raise WorkerProcessingError(f"Label extraction failed: {e}")


class ExtractPriorityWorker(BaseWorker):
    """
    Worker for extracting task priority from descriptions, titles, and due dates.
    
    Determines priority level based on urgency indicators and due date proximity.
    """
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data for priority extraction.
        
        Args:
            input_data: Input data containing description and title
            
        Returns:
            True if input is valid
            
        Raises:
            WorkerValidationError: If input validation fails
        """
        if not isinstance(input_data, dict):
            raise WorkerValidationError("Input data must be a dictionary")
        
        description = input_data.get("description")
        title = input_data.get("title")
        
        if not description:
            raise WorkerValidationError("Description is required")
        
        if not title:
            raise WorkerValidationError("Title is required")
        
        if not isinstance(description, str) or not isinstance(title, str):
            raise WorkerValidationError("Description and title must be strings")
        
        if len(description.strip()) == 0 or len(title.strip()) == 0:
            raise WorkerValidationError("Description and title cannot be empty")
        
        # Due date is optional but must be valid if provided
        due_date = input_data.get("due_date")
        if due_date is not None:
            if not isinstance(due_date, str):
                raise WorkerValidationError("Due date must be a string if provided")
            
            # Try to parse the due date to validate format
            try:
                datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            except ValueError:
                raise WorkerValidationError("Due date must be in valid ISO format")
        
        return True
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract priority level from task information.
        
        Args:
            input_data: Dictionary containing:
                - description (str): Task description
                - title (str): Task title
                - due_date (str, optional): Due date in ISO format
                - context (dict, optional): Additional context
                
        Returns:
            Dictionary containing:
                - priority (str): Priority level (high, medium, low)
                - confidence (float): Confidence score for priority assessment
                - reasoning (str): Explanation of priority determination
                
        Raises:
            WorkerProcessingError: If extraction fails
        """
        # Validate input
        self.validate_input(input_data)
        
        try:
            description = input_data["description"]
            title = input_data["title"]
            due_date = input_data.get("due_date")
            context = input_data.get("context", {})
            
            # Generate prompt messages
            messages = PromptTemplates.extract_task_priority(description, title, due_date)
            
            # Add context if provided
            if context:
                messages = self.add_context_to_messages(messages, context)
            
            # Execute simple completion
            response_text = await self.simple_completion(
                messages=messages,
                temperature=0.1,  # Low temperature for consistent priority assessment
                max_tokens=200
            )
            
            # Parse the response to extract priority and reasoning
            # Expected format: priority level followed by reasoning
            lines = response_text.strip().split('\n')
            priority_line = lines[0].lower().strip()
            
            # Extract priority level
            if 'high' in priority_line:
                priority = 'high'
            elif 'medium' in priority_line:
                priority = 'medium'
            elif 'low' in priority_line:
                priority = 'low'
            else:
                # Default to medium if unclear
                priority = 'medium'
            
            # Extract reasoning (rest of the response)
            reasoning = response_text.strip()
            
            # Calculate confidence based on clarity of response
            confidence = 0.8 if priority in priority_line else 0.6
            
            return {
                "priority": priority,
                "confidence": confidence,
                "reasoning": reasoning
            }
            
        except Exception as e:
            if isinstance(e, (WorkerValidationError, WorkerProcessingError)):
                raise
            raise WorkerProcessingError(f"Priority extraction failed: {e}")


# Register workers with the global strategy
def register_extraction_workers():
    """Register all extraction workers with the global worker strategy."""
    from workers.base import register_worker
    
    register_worker("extract_title_date", ExtractTitleDateWorker())
    register_worker("extract_label", ExtractLabelWorker())
    register_worker("extract_priority", ExtractPriorityWorker())


# Auto-register workers when module is imported
register_extraction_workers()
