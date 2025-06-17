"""Pydantic schemas for structured data validation and serialization."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class TaskBase(BaseModel):
    """Base schema for task data."""
    
    description: str = Field(..., min_length=1, max_length=2000, description="Task description")
    title: Optional[str] = Field(None, max_length=255, description="Task title")
    label: Optional[str] = Field(None, max_length=100, description="Task label/category")
    due_date: Optional[datetime] = Field(None, description="Task due date")


class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    
    @validator('description')
    def description_must_not_be_empty(cls, v):
        """Validate that description is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""
    
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    title: Optional[str] = Field(None, max_length=255)
    label: Optional[str] = Field(None, max_length=100)
    due_date: Optional[datetime] = None
    
    @validator('description')
    def description_must_not_be_empty(cls, v):
        """Validate that description is not empty or whitespace only."""
        if v is not None and (not v or not v.strip()):
            raise ValueError('Description cannot be empty')
        return v.strip() if v else v


class TaskResponse(TaskBase):
    """Schema for task response data."""
    
    id: int = Field(..., description="Task ID")
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: datetime = Field(..., description="Task last update timestamp")
    
    class Config:
        from_attributes = True


class TaskList(BaseModel):
    """Schema for paginated task list response."""
    
    tasks: List[TaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")
    skip: int = Field(..., description="Number of tasks skipped")
    limit: int = Field(..., description="Maximum number of tasks returned")


class SummaryRequest(BaseModel):
    """Schema for summary request."""
    
    start_date: datetime = Field(..., description="Start date for summary")
    end_date: datetime = Field(..., description="End date for summary")
    
    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        """Validate that end_date is after start_date."""
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class SummaryResponse(BaseModel):
    """Schema for summary response."""
    
    summary: str = Field(..., description="Generated summary text")
    start_date: datetime = Field(..., description="Summary start date")
    end_date: datetime = Field(..., description="Summary end date")
    task_count: int = Field(..., description="Number of tasks included in summary")


# AI Worker Schemas
class ExtractedTitleDate(BaseModel):
    """Schema for AI-extracted title and date."""
    
    title: str = Field(..., max_length=255, description="Extracted task title")
    due_date: Optional[datetime] = Field(None, description="Extracted due date")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence score")


class ExtractedLabel(BaseModel):
    """Schema for AI-extracted label."""
    
    label: str = Field(..., max_length=100, description="Extracted task label/category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence score")


class BulkSummary(BaseModel):
    """Schema for AI-generated bulk summary."""
    
    summary: str = Field(..., description="Generated summary text")
    key_themes: List[str] = Field(..., description="Key themes identified")
    task_count: int = Field(..., description="Number of tasks summarized")


# Error Schemas
class ErrorDetail(BaseModel):
    """Schema for error details."""
    
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    field: Optional[str] = Field(None, description="Field that caused the error")


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    
    error: str = Field(..., description="Error type")
    details: List[ErrorDetail] = Field(..., description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


# Health Check Schema
class HealthResponse(BaseModel):
    """Schema for health check response."""
    
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
