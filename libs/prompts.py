"""AI prompt templates for task extraction and summarization."""

from datetime import datetime
from typing import Dict, Any, List, Optional


class PromptTemplates:
    """Collection of AI prompt templates for various tasks."""
    
    @staticmethod
    def extract_title_and_date(description: str, current_datetime: str) -> List[Dict[str, Any]]:
        """
        Generate messages for extracting title and date from task description.
        
        Args:
            description: Task description in natural language
            current_datetime: Current datetime in ISO format
            
        Returns:
            List of messages for OpenAI chat completion
        """
        return [
            {
                "role": "system",
                "content": (
                    "You are a task analysis expert. Your job is to extract a concise title and due date "
                    "from natural language task descriptions. "
                    f"Current date and time: {current_datetime}\n\n"
                    "Guidelines:\n"
                    "- Create a short, actionable title (2-6 words)\n"
                    "- If a date/time is mentioned, use the date calculation functions to determine the exact datetime\n"
                    "- If no date is mentioned, set due_date to null\n"
                    "- Be intelligent about interpreting relative dates like 'tomorrow', 'next week', 'Friday'\n"
                    "- Focus on the main action or deliverable\n"
                    "- Remove unnecessary words like 'I need to', 'remember to', etc."
                )
            },
            {
                "role": "user",
                "content": f"Extract title and due date from this task: '{description}'"
            }
        ]
    
    @staticmethod
    def extract_label(description: str, title: str) -> List[Dict[str, Any]]:
        """
        Generate messages for extracting label/category from task description.
        
        Args:
            description: Task description in natural language
            title: Extracted task title
            
        Returns:
            List of messages for OpenAI chat completion
        """
        return [
            {
                "role": "system",
                "content": (
                    "You are a task categorization expert. Your job is to assign appropriate labels/categories "
                    "to tasks based on their description and title.\n\n"
                    "Common categories include:\n"
                    "- work: Professional tasks, meetings, deadlines, projects\n"
                    "- personal: Personal errands, self-care, hobbies, family\n"
                    "- health: Medical appointments, exercise, wellness\n"
                    "- finance: Bills, banking, investments, budgeting\n"
                    "- shopping: Groceries, purchases, errands\n"
                    "- home: Cleaning, maintenance, repairs, organization\n"
                    "- social: Events, gatherings, calls, relationships\n"
                    "- learning: Education, courses, reading, skill development\n"
                    "- travel: Trips, bookings, planning, transportation\n"
                    "- urgent: Time-sensitive or high-priority tasks\n\n"
                    "Choose the most appropriate single label. If none fit perfectly, "
                    "create a relevant 1-2 word label that captures the essence of the task."
                )
            },
            {
                "role": "user",
                "content": f"Categorize this task:\nTitle: {title}\nDescription: {description}"
            }
        ]
    
    @staticmethod
    def summarize_tasks(tasks: List[Dict[str, Any]], start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Generate messages for creating a summary of multiple tasks.
        
        Args:
            tasks: List of task dictionaries with title, description, label, due_date
            start_date: Start date for summary period
            end_date: End date for summary period
            
        Returns:
            List of messages for OpenAI chat completion
        """
        # Format tasks for the prompt
        task_list = []
        for i, task in enumerate(tasks, 1):
            due_date_str = task.get('due_date', 'No due date')
            if due_date_str and due_date_str != 'No due date':
                try:
                    due_date_obj = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                    due_date_str = due_date_obj.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            task_list.append(
                f"{i}. {task.get('title', 'Untitled')} "
                f"[{task.get('label', 'uncategorized')}] "
                f"- Due: {due_date_str}\n"
                f"   Description: {task.get('description', 'No description')}"
            )
        
        tasks_text = "\n\n".join(task_list)
        
        return [
            {
                "role": "system",
                "content": (
                    "You are a productivity analyst. Your job is to create insightful summaries "
                    "of task lists that help users understand their workload and priorities.\n\n"
                    "Your summary should include:\n"
                    "1. Overview of the time period and total tasks\n"
                    "2. Breakdown by categories/labels\n"
                    "3. Key themes and patterns\n"
                    "4. Upcoming deadlines and priorities\n"
                    "5. Actionable insights or recommendations\n\n"
                    "Keep the summary concise but informative (2-4 paragraphs)."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Create a summary for tasks from {start_date} to {end_date}:\n\n"
                    f"{tasks_text}\n\n"
                    f"Total tasks: {len(tasks)}"
                )
            }
        ]
    
    @staticmethod
    def refine_task_title(original_title: str, description: str) -> List[Dict[str, Any]]:
        """
        Generate messages for refining an existing task title.
        
        Args:
            original_title: Current task title
            description: Full task description
            
        Returns:
            List of messages for OpenAI chat completion
        """
        return [
            {
                "role": "system",
                "content": (
                    "You are a task optimization expert. Your job is to improve task titles "
                    "to make them more clear, actionable, and concise.\n\n"
                    "Guidelines:\n"
                    "- Keep titles between 2-6 words when possible\n"
                    "- Start with an action verb when appropriate\n"
                    "- Be specific but concise\n"
                    "- Remove redundant words\n"
                    "- Make it immediately clear what needs to be done\n"
                    "- Consider the full context from the description"
                )
            },
            {
                "role": "user",
                "content": (
                    f"Improve this task title:\n"
                    f"Current title: {original_title}\n"
                    f"Full description: {description}\n\n"
                    f"Provide a better, more actionable title."
                )
            }
        ]
    
    @staticmethod
    def extract_task_priority(description: str, title: str, due_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate messages for extracting task priority level.
        
        Args:
            description: Task description
            title: Task title
            due_date: Due date if available
            
        Returns:
            List of messages for OpenAI chat completion
        """
        due_info = f"Due date: {due_date}" if due_date else "No due date specified"
        
        return [
            {
                "role": "system",
                "content": (
                    "You are a priority assessment expert. Your job is to determine the priority level "
                    "of tasks based on their content, urgency, and importance.\n\n"
                    "Priority levels:\n"
                    "- high: Urgent and important, time-sensitive, critical deadlines\n"
                    "- medium: Important but not urgent, or urgent but not critical\n"
                    "- low: Neither urgent nor critical, can be done when time allows\n\n"
                    "Consider factors like:\n"
                    "- Explicit urgency words (urgent, ASAP, immediately, deadline)\n"
                    "- Due date proximity\n"
                    "- Impact on other tasks or people\n"
                    "- Consequences of delay"
                )
            },
            {
                "role": "user",
                "content": (
                    f"Determine the priority level for this task:\n"
                    f"Title: {title}\n"
                    f"Description: {description}\n"
                    f"{due_info}"
                )
            }
        ]


class PromptBuilder:
    """Helper class for building dynamic prompts with context."""
    
    @staticmethod
    def add_context_to_messages(
        messages: List[Dict[str, Any]], 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Add contextual information to existing messages.
        
        Args:
            messages: Original message list
            context: Additional context to include
            
        Returns:
            Enhanced message list with context
        """
        enhanced_messages = messages.copy()
        
        if context:
            context_str = "Additional context:\n"
            for key, value in context.items():
                if value is not None:
                    context_str += f"- {key}: {value}\n"
            
            # Add context to the system message
            if enhanced_messages and enhanced_messages[0]["role"] == "system":
                enhanced_messages[0]["content"] += f"\n\n{context_str}"
            else:
                # Insert context as first system message
                enhanced_messages.insert(0, {
                    "role": "system",
                    "content": context_str
                })
        
        return enhanced_messages
    
    @staticmethod
    def create_few_shot_examples(
        base_messages: List[Dict[str, Any]], 
        examples: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Add few-shot examples to messages for better AI performance.
        
        Args:
            base_messages: Original message list
            examples: List of example input/output pairs
            
        Returns:
            Enhanced message list with examples
        """
        enhanced_messages = base_messages.copy()
        
        # Insert examples before the final user message
        if examples and len(enhanced_messages) >= 2:
            example_messages = []
            for example in examples:
                example_messages.extend([
                    {"role": "user", "content": example["input"]},
                    {"role": "assistant", "content": example["output"]}
                ])
            
            # Insert examples before the last user message
            enhanced_messages = (
                enhanced_messages[:-1] + 
                example_messages + 
                enhanced_messages[-1:]
            )
        
        return enhanced_messages


# Pre-defined example sets for few-shot learning
TITLE_EXTRACTION_EXAMPLES = [
    {
        "input": "I need to remember to call the dentist tomorrow to schedule my cleaning appointment",
        "output": "Call dentist"
    },
    {
        "input": "Buy groceries for the week including milk, bread, and vegetables",
        "output": "Buy groceries"
    },
    {
        "input": "Finish the quarterly report that's due next Friday",
        "output": "Finish quarterly report"
    }
]

LABEL_EXTRACTION_EXAMPLES = [
    {
        "input": "Title: Call dentist\nDescription: Schedule cleaning appointment",
        "output": "health"
    },
    {
        "input": "Title: Buy groceries\nDescription: Get milk, bread, and vegetables",
        "output": "shopping"
    },
    {
        "input": "Title: Finish quarterly report\nDescription: Complete Q4 financial analysis",
        "output": "work"
    }
]

PRIORITY_EXTRACTION_EXAMPLES = [
    {
        "input": "Title: Submit tax documents\nDescription: URGENT - deadline is tomorrow!",
        "output": "high"
    },
    {
        "input": "Title: Read book\nDescription: Finish reading the novel I started",
        "output": "low"
    },
    {
        "input": "Title: Prepare presentation\nDescription: Create slides for Monday's client meeting",
        "output": "medium"
    }
]
