"""AI worker for bulk task summarization."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from libs.prompts import PromptTemplates
from workers.base import BaseWorker, WorkerValidationError, WorkerProcessingError


class BulkSummarizerWorker(BaseWorker):
    """
    Worker for generating summaries of multiple tasks.
    
    Analyzes task lists and creates insightful summaries with key themes,
    patterns, and actionable insights.
    """
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data for bulk summarization.
        
        Args:
            input_data: Input data containing tasks and date range
            
        Returns:
            True if input is valid
            
        Raises:
            WorkerValidationError: If input validation fails
        """
        if not isinstance(input_data, dict):
            raise WorkerValidationError("Input data must be a dictionary")
        
        tasks = input_data.get("tasks")
        start_date = input_data.get("start_date")
        end_date = input_data.get("end_date")
        
        if tasks is None:
            raise WorkerValidationError("Tasks list is required")
        
        if not isinstance(tasks, list):
            raise WorkerValidationError("Tasks must be a list")
        
        if len(tasks) == 0:
            raise WorkerValidationError("Tasks list cannot be empty")
        
        if len(tasks) > 1000:
            raise WorkerValidationError("Too many tasks (max 1000)")
        
        # Validate each task has required fields
        for i, task in enumerate(tasks):
            if not isinstance(task, dict):
                raise WorkerValidationError(f"Task {i} must be a dictionary")
            
            if "title" not in task:
                raise WorkerValidationError(f"Task {i} missing title")
            
            if "description" not in task:
                raise WorkerValidationError(f"Task {i} missing description")
            
            if not isinstance(task["title"], str):
                raise WorkerValidationError(f"Task {i} title must be a string")
            
            if not isinstance(task["description"], str):
                raise WorkerValidationError(f"Task {i} description must be a string")
        
        # Validate date range if provided
        if start_date is not None:
            if not isinstance(start_date, str):
                raise WorkerValidationError("Start date must be a string")
            
            try:
                datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise WorkerValidationError("Start date must be in valid ISO format")
        
        if end_date is not None:
            if not isinstance(end_date, str):
                raise WorkerValidationError("End date must be a string")
            
            try:
                datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise WorkerValidationError("End date must be in valid ISO format")
        
        # Validate date range order
        if start_date and end_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                
                if end_dt <= start_dt:
                    raise WorkerValidationError("End date must be after start date")
            except ValueError:
                # Already validated individual dates above
                pass
        
        return True
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of multiple tasks.
        
        Args:
            input_data: Dictionary containing:
                - tasks (list): List of task dictionaries with title, description, label, due_date
                - start_date (str, optional): Start date for summary period
                - end_date (str, optional): End date for summary period
                - context (dict, optional): Additional context
                
        Returns:
            Dictionary containing:
                - summary (str): Generated summary text
                - task_count (int): Number of tasks summarized
                - key_themes (list): Key themes identified
                - insights (str): Actionable insights and recommendations
                
        Raises:
            WorkerProcessingError: If summarization fails
        """
        # Validate input
        self.validate_input(input_data)
        
        try:
            tasks = input_data["tasks"]
            start_date = input_data.get("start_date", "")
            end_date = input_data.get("end_date", "")
            context = input_data.get("context", {})
            
            # Generate prompt messages
            messages = PromptTemplates.summarize_tasks(tasks, start_date, end_date)
            
            # Add context if provided
            if context:
                messages = self.add_context_to_messages(messages, context)
            
            # Execute simple completion for summary generation
            summary_text = await self.simple_completion(
                messages=messages,
                temperature=0.3,  # Moderate temperature for creative but consistent summaries
                max_tokens=1000
            )
            
            # Parse the summary to extract key components
            summary_lines = summary_text.strip().split('\n')
            
            # Extract key themes from the summary
            key_themes = self._extract_key_themes(tasks, summary_text)
            
            # Generate insights based on the summary
            insights = self._generate_insights(tasks, summary_text)
            
            return {
                "summary": summary_text.strip(),
                "task_count": len(tasks),
                "key_themes": key_themes,
                "insights": insights
            }
            
        except Exception as e:
            if isinstance(e, (WorkerValidationError, WorkerProcessingError)):
                raise
            raise WorkerProcessingError(f"Bulk summarization failed: {e}")
    
    def _extract_key_themes(self, tasks: List[Dict[str, Any]], summary_text: str) -> List[str]:
        """
        Extract key themes from tasks and summary.
        
        Args:
            tasks: List of task dictionaries
            summary_text: Generated summary text
            
        Returns:
            List of key themes
        """
        themes = set()
        
        # Extract themes from task labels
        for task in tasks:
            label = task.get("label", "").lower()
            if label and label != "uncategorized":
                themes.add(label.title())
        
        # Extract themes from summary text (simple keyword extraction)
        summary_lower = summary_text.lower()
        theme_keywords = [
            "work", "personal", "health", "finance", "shopping", "home",
            "social", "learning", "travel", "urgent", "deadline", "meeting",
            "project", "maintenance", "exercise", "family", "education"
        ]
        
        for keyword in theme_keywords:
            if keyword in summary_lower:
                themes.add(keyword.title())
        
        return sorted(list(themes))
    
    def _generate_insights(self, tasks: List[Dict[str, Any]], summary_text: str) -> str:
        """
        Generate actionable insights from tasks and summary.
        
        Args:
            tasks: List of task dictionaries
            summary_text: Generated summary text
            
        Returns:
            Insights and recommendations
        """
        insights = []
        
        # Analyze task distribution
        total_tasks = len(tasks)
        tasks_with_dates = sum(1 for task in tasks if task.get("due_date"))
        
        if tasks_with_dates > 0:
            insights.append(f"{tasks_with_dates} of {total_tasks} tasks have due dates.")
        
        if tasks_with_dates < total_tasks * 0.5:
            insights.append("Consider adding due dates to more tasks for better time management.")
        
        # Analyze labels
        labels = [task.get("label", "uncategorized") for task in tasks]
        label_counts = {}
        for label in labels:
            label_counts[label] = label_counts.get(label, 0) + 1
        
        if label_counts:
            most_common_label = max(label_counts, key=label_counts.get)
            if most_common_label != "uncategorized":
                insights.append(f"Most tasks are related to {most_common_label} ({label_counts[most_common_label]} tasks).")
        
        # Check for overdue or urgent tasks
        current_time = datetime.now()
        overdue_count = 0
        upcoming_count = 0
        
        for task in tasks:
            due_date_str = task.get("due_date")
            if due_date_str:
                try:
                    due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                    if due_date < current_time:
                        overdue_count += 1
                    elif (due_date - current_time).days <= 3:
                        upcoming_count += 1
                except ValueError:
                    pass
        
        if overdue_count > 0:
            insights.append(f"{overdue_count} tasks appear to be overdue and need immediate attention.")
        
        if upcoming_count > 0:
            insights.append(f"{upcoming_count} tasks are due within the next 3 days.")
        
        # General recommendations
        if total_tasks > 20:
            insights.append("Consider breaking down large tasks into smaller, manageable subtasks.")
        
        if len(set(labels)) > 5:
            insights.append("You have tasks across many categories - consider focusing on one area at a time.")
        
        return " ".join(insights) if insights else "Your tasks are well-organized and balanced."


# Register worker with the global strategy
def register_summarizer_worker():
    """Register the summarizer worker with the global worker strategy."""
    from workers.base import register_worker
    
    register_worker("bulk_summarizer", BulkSummarizerWorker())


# Auto-register worker when module is imported
register_summarizer_worker()
