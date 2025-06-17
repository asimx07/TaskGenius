"""Unit tests for AI prompt templates."""

from datetime import datetime

import pytest

from libs.prompts import (
    PromptTemplates,
    PromptBuilder,
    TITLE_EXTRACTION_EXAMPLES,
    LABEL_EXTRACTION_EXAMPLES,
    PRIORITY_EXTRACTION_EXAMPLES,
)


@pytest.mark.unit
def test_extract_title_and_date_prompt():
    """Test title and date extraction prompt generation."""
    description = "Call the dentist tomorrow to schedule cleaning"
    current_datetime = "2024-01-15T10:00:00"
    
    messages = PromptTemplates.extract_title_and_date(description, current_datetime)
    
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    
    # Check system message contains guidelines
    system_content = messages[0]["content"]
    assert "task analysis expert" in system_content
    assert "2-6 words" in system_content
    assert current_datetime in system_content
    assert "date calculation functions" in system_content
    
    # Check user message contains the description
    user_content = messages[1]["content"]
    assert description in user_content
    assert "Extract title and due date" in user_content


@pytest.mark.unit
def test_extract_label_prompt():
    """Test label extraction prompt generation."""
    description = "Buy groceries including milk and bread"
    title = "Buy groceries"
    
    messages = PromptTemplates.extract_label(description, title)
    
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    
    # Check system message contains categories
    system_content = messages[0]["content"]
    assert "categorization expert" in system_content
    assert "work:" in system_content
    assert "personal:" in system_content
    assert "shopping:" in system_content
    assert "health:" in system_content
    
    # Check user message contains title and description
    user_content = messages[1]["content"]
    assert title in user_content
    assert description in user_content
    assert "Categorize this task" in user_content


@pytest.mark.unit
def test_summarize_tasks_prompt():
    """Test task summarization prompt generation."""
    tasks = [
        {
            "title": "Buy groceries",
            "description": "Get milk and bread",
            "label": "shopping",
            "due_date": "2024-01-16T10:00:00"
        },
        {
            "title": "Call dentist",
            "description": "Schedule cleaning appointment",
            "label": "health",
            "due_date": None
        }
    ]
    start_date = "2024-01-15"
    end_date = "2024-01-20"
    
    messages = PromptTemplates.summarize_tasks(tasks, start_date, end_date)
    
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    
    # Check system message contains summary guidelines
    system_content = messages[0]["content"]
    assert "productivity analyst" in system_content
    assert "Overview of the time period" in system_content
    assert "Breakdown by categories" in system_content
    assert "Key themes and patterns" in system_content
    
    # Check user message contains task details
    user_content = messages[1]["content"]
    assert start_date in user_content
    assert end_date in user_content
    assert "Buy groceries" in user_content
    assert "Call dentist" in user_content
    assert "shopping" in user_content
    assert "health" in user_content
    assert "Total tasks: 2" in user_content


@pytest.mark.unit
def test_summarize_tasks_with_formatted_dates():
    """Test task summarization with proper date formatting."""
    tasks = [
        {
            "title": "Meeting",
            "description": "Team standup",
            "label": "work",
            "due_date": "2024-01-16T14:30:00Z"
        }
    ]
    
    messages = PromptTemplates.summarize_tasks(tasks, "2024-01-15", "2024-01-20")
    user_content = messages[1]["content"]
    
    # Should format the date properly
    assert "2024-01-16 14:30" in user_content


@pytest.mark.unit
def test_summarize_tasks_no_due_date():
    """Test task summarization with tasks that have no due date."""
    tasks = [
        {
            "title": "Read book",
            "description": "Finish novel",
            "label": "personal",
            "due_date": None
        }
    ]
    
    messages = PromptTemplates.summarize_tasks(tasks, "2024-01-15", "2024-01-20")
    user_content = messages[1]["content"]
    
    assert "None" in user_content


@pytest.mark.unit
def test_refine_task_title_prompt():
    """Test task title refinement prompt generation."""
    original_title = "I need to call the dentist"
    description = "Schedule a cleaning appointment for next week"
    
    messages = PromptTemplates.refine_task_title(original_title, description)
    
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    
    # Check system message contains optimization guidelines
    system_content = messages[0]["content"]
    assert "task optimization expert" in system_content
    assert "2-6 words" in system_content
    assert "action verb" in system_content
    assert "actionable" in system_content
    
    # Check user message contains both titles
    user_content = messages[1]["content"]
    assert original_title in user_content
    assert description in user_content
    assert "Improve this task title" in user_content


@pytest.mark.unit
def test_extract_task_priority_prompt():
    """Test task priority extraction prompt generation."""
    description = "URGENT: Submit tax documents before deadline"
    title = "Submit tax documents"
    due_date = "2024-01-16T23:59:59"
    
    messages = PromptTemplates.extract_task_priority(description, title, due_date)
    
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    
    # Check system message contains priority levels
    system_content = messages[0]["content"]
    assert "priority assessment expert" in system_content
    assert "high:" in system_content
    assert "medium:" in system_content
    assert "low:" in system_content
    assert "urgent" in system_content.lower()
    
    # Check user message contains task details
    user_content = messages[1]["content"]
    assert title in user_content
    assert description in user_content
    assert due_date in user_content


@pytest.mark.unit
def test_extract_task_priority_no_due_date():
    """Test task priority extraction without due date."""
    description = "Read a book when I have time"
    title = "Read book"
    
    messages = PromptTemplates.extract_task_priority(description, title)
    
    user_content = messages[1]["content"]
    assert "No due date specified" in user_content


@pytest.mark.unit
def test_prompt_builder_add_context():
    """Test adding context to existing messages."""
    original_messages = [
        {"role": "system", "content": "You are an expert."},
        {"role": "user", "content": "Help me with this task."}
    ]
    
    context = {
        "user_timezone": "UTC",
        "user_preferences": "concise responses",
        "empty_value": None
    }
    
    enhanced_messages = PromptBuilder.add_context_to_messages(original_messages, context)
    
    assert len(enhanced_messages) == 2
    assert enhanced_messages[0]["role"] == "system"
    
    # Check that context was added to system message
    system_content = enhanced_messages[0]["content"]
    assert "You are an expert." in system_content
    assert "Additional context:" in system_content
    assert "user_timezone: UTC" in system_content
    assert "user_preferences: concise responses" in system_content
    assert "empty_value" not in system_content  # Should skip None values


@pytest.mark.unit
def test_prompt_builder_add_context_no_system_message():
    """Test adding context when no system message exists."""
    original_messages = [
        {"role": "user", "content": "Help me with this task."}
    ]
    
    context = {"setting": "test"}
    
    enhanced_messages = PromptBuilder.add_context_to_messages(original_messages, context)
    
    assert len(enhanced_messages) == 2
    assert enhanced_messages[0]["role"] == "system"
    assert "Additional context:" in enhanced_messages[0]["content"]
    assert "setting: test" in enhanced_messages[0]["content"]
    assert enhanced_messages[1]["role"] == "user"


@pytest.mark.unit
def test_prompt_builder_add_empty_context():
    """Test adding empty context doesn't change messages."""
    original_messages = [
        {"role": "system", "content": "You are an expert."},
        {"role": "user", "content": "Help me."}
    ]
    
    enhanced_messages = PromptBuilder.add_context_to_messages(original_messages, {})
    
    assert enhanced_messages == original_messages


@pytest.mark.unit
def test_prompt_builder_few_shot_examples():
    """Test adding few-shot examples to messages."""
    base_messages = [
        {"role": "system", "content": "You are a categorizer."},
        {"role": "user", "content": "Categorize: Buy milk"}
    ]
    
    examples = [
        {"input": "Call doctor", "output": "health"},
        {"input": "Buy groceries", "output": "shopping"}
    ]
    
    enhanced_messages = PromptBuilder.create_few_shot_examples(base_messages, examples)
    
    assert len(enhanced_messages) == 6  # system + 2 examples (4 messages) + user
    assert enhanced_messages[0]["role"] == "system"
    assert enhanced_messages[1]["role"] == "user"
    assert enhanced_messages[1]["content"] == "Call doctor"
    assert enhanced_messages[2]["role"] == "assistant"
    assert enhanced_messages[2]["content"] == "health"
    assert enhanced_messages[3]["role"] == "user"
    assert enhanced_messages[3]["content"] == "Buy groceries"
    assert enhanced_messages[4]["role"] == "assistant"
    assert enhanced_messages[4]["content"] == "shopping"
    assert enhanced_messages[5]["role"] == "user"
    assert enhanced_messages[5]["content"] == "Categorize: Buy milk"


@pytest.mark.unit
def test_prompt_builder_few_shot_examples_empty():
    """Test adding empty examples doesn't change messages."""
    base_messages = [
        {"role": "system", "content": "You are an expert."},
        {"role": "user", "content": "Help me."}
    ]
    
    enhanced_messages = PromptBuilder.create_few_shot_examples(base_messages, [])
    
    assert enhanced_messages == base_messages


@pytest.mark.unit
def test_title_extraction_examples_structure():
    """Test that title extraction examples have correct structure."""
    assert isinstance(TITLE_EXTRACTION_EXAMPLES, list)
    assert len(TITLE_EXTRACTION_EXAMPLES) > 0
    
    for example in TITLE_EXTRACTION_EXAMPLES:
        assert "input" in example
        assert "output" in example
        assert isinstance(example["input"], str)
        assert isinstance(example["output"], str)
        assert len(example["input"]) > 0
        assert len(example["output"]) > 0


@pytest.mark.unit
def test_label_extraction_examples_structure():
    """Test that label extraction examples have correct structure."""
    assert isinstance(LABEL_EXTRACTION_EXAMPLES, list)
    assert len(LABEL_EXTRACTION_EXAMPLES) > 0
    
    for example in LABEL_EXTRACTION_EXAMPLES:
        assert "input" in example
        assert "output" in example
        assert "Title:" in example["input"]
        assert "Description:" in example["input"]


@pytest.mark.unit
def test_priority_extraction_examples_structure():
    """Test that priority extraction examples have correct structure."""
    assert isinstance(PRIORITY_EXTRACTION_EXAMPLES, list)
    assert len(PRIORITY_EXTRACTION_EXAMPLES) > 0
    
    for example in PRIORITY_EXTRACTION_EXAMPLES:
        assert "input" in example
        assert "output" in example
        assert example["output"] in ["high", "medium", "low"]


@pytest.mark.unit
def test_prompt_templates_all_methods_return_lists():
    """Test that all PromptTemplates methods return lists of messages."""
    # Test extract_title_and_date
    messages1 = PromptTemplates.extract_title_and_date("test", "2024-01-15T10:00:00")
    assert isinstance(messages1, list)
    assert all(isinstance(msg, dict) for msg in messages1)
    assert all("role" in msg and "content" in msg for msg in messages1)
    
    # Test extract_label
    messages2 = PromptTemplates.extract_label("test desc", "test title")
    assert isinstance(messages2, list)
    assert all(isinstance(msg, dict) for msg in messages2)
    
    # Test summarize_tasks
    messages3 = PromptTemplates.summarize_tasks([], "2024-01-15", "2024-01-20")
    assert isinstance(messages3, list)
    assert all(isinstance(msg, dict) for msg in messages3)
    
    # Test refine_task_title
    messages4 = PromptTemplates.refine_task_title("old title", "description")
    assert isinstance(messages4, list)
    assert all(isinstance(msg, dict) for msg in messages4)
    
    # Test extract_task_priority
    messages5 = PromptTemplates.extract_task_priority("desc", "title")
    assert isinstance(messages5, list)
    assert all(isinstance(msg, dict) for msg in messages5)


@pytest.mark.unit
def test_prompt_templates_message_roles():
    """Test that all prompt templates have correct message roles."""
    test_cases = [
        PromptTemplates.extract_title_and_date("test", "2024-01-15T10:00:00"),
        PromptTemplates.extract_label("test desc", "test title"),
        PromptTemplates.summarize_tasks([], "2024-01-15", "2024-01-20"),
        PromptTemplates.refine_task_title("old title", "description"),
        PromptTemplates.extract_task_priority("desc", "title")
    ]
    
    for messages in test_cases:
        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"
        
        # Check that all messages have valid roles
        valid_roles = {"system", "user", "assistant"}
        for msg in messages:
            assert msg["role"] in valid_roles


@pytest.mark.unit
def test_prompt_content_not_empty():
    """Test that all generated prompts have non-empty content."""
    test_cases = [
        PromptTemplates.extract_title_and_date("test task", "2024-01-15T10:00:00"),
        PromptTemplates.extract_label("test description", "test title"),
        PromptTemplates.summarize_tasks([{"title": "test", "description": "test", "label": "test"}], "2024-01-15", "2024-01-20"),
        PromptTemplates.refine_task_title("old title", "description"),
        PromptTemplates.extract_task_priority("description", "title", "2024-01-16")
    ]
    
    for messages in test_cases:
        for msg in messages:
            assert len(msg["content"].strip()) > 0
            assert msg["content"] != ""
