"""Task management API endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_

from db import get_db_session
from models import Task
from libs.schema import (
    TaskCreate, TaskUpdate, TaskResponse, TaskList, 
    SummaryRequest, SummaryResponse
)
from workers.base import execute_worker, get_worker_strategy, WorkerError

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def process_task_with_ai(description: str, context: Optional[dict] = None) -> dict:
    """
    Process a task description using AI workers to extract metadata.
    
    Args:
        description: Task description in natural language
        context: Optional context for AI processing
        
    Returns:
        Dictionary containing extracted title, due_date, label, and priority
        
    Raises:
        WorkerError: If AI processing fails
    """
    try:
        # Step 1: Extract title and due date
        title_date_result = await execute_worker("extract_title_date", {
            "description": description,
            "context": context or {}
        })
        
        title = title_date_result["title"]
        due_date_str = title_date_result["due_date"]
        due_date = datetime.fromisoformat(due_date_str) if due_date_str else None
        
        # Step 2: Extract label using title and description
        label_result = await execute_worker("extract_label", {
            "description": description,
            "title": title,
            "context": context or {}
        })
        
        label = label_result["label"]
        
        # Step 3: Extract priority using all available information
        priority_result = await execute_worker("extract_priority", {
            "description": description,
            "title": title,
            "due_date": due_date_str,
            "context": context or {}
        })
        
        priority = priority_result["priority"]
        
        return {
            "title": title,
            "due_date": due_date,
            "label": label,
            "priority": priority,
            "ai_confidence": {
                "title_date": title_date_result["confidence"],
                "label": label_result["confidence"],
                "priority": priority_result["confidence"]
            }
        }
        
    except Exception as e:
        raise WorkerError(f"AI processing failed: {e}")


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new task with AI-powered metadata extraction.
    
    The AI will automatically extract:
    - Title from the description
    - Due date from natural language date references
    - Label/category based on task content
    - Priority level based on urgency indicators
    """
    try:
        # Process task with AI workers
        ai_result = await process_task_with_ai(task_data.description)
        
        # Create task with AI-extracted metadata
        task = Task(
            description=task_data.description,
            title=ai_result["title"],
            label=ai_result["label"],
            due_date=ai_result["due_date"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        return task
        
    except WorkerError as e:
        raise HTTPException(status_code=422, detail=f"AI processing failed: {e}")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create task: {e}")


@router.get("/", response_model=TaskList)
async def list_tasks(
    skip: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of tasks to return"),
    label: Optional[str] = Query(None, description="Filter by label"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    List tasks with optional filtering and pagination.
    """
    try:
        # Build query with optional filtering
        query = select(Task)
        
        if label:
            query = query.where(Task.label == label)
        
        # Get total count
        count_query = select(Task.id)
        if label:
            count_query = count_query.where(Task.label == label)
        
        total_result = await db.execute(count_query)
        total = len(total_result.fetchall())
        
        # Get paginated results
        query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        return TaskList(
            tasks=tasks,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {e}")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get a specific task by ID.
    """
    try:
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task: {e}")


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update a task with AI reprocessing if description changes.
    
    If the description is updated, AI workers will re-extract metadata.
    """
    try:
        # Get existing task
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Check if description changed and needs AI reprocessing
        description_changed = (
            task_data.description is not None and 
            task_data.description != task.description
        )
        
        if description_changed:
            # Reprocess with AI workers
            ai_result = await process_task_with_ai(task_data.description)
            
            # Update with AI-extracted metadata
            task.description = task_data.description
            task.title = ai_result["title"]
            task.label = ai_result["label"]
            task.due_date = ai_result["due_date"]
        else:
            # Update only provided fields
            if task_data.description is not None:
                task.description = task_data.description
            if task_data.title is not None:
                task.title = task_data.title
            if task_data.label is not None:
                task.label = task_data.label
            if task_data.due_date is not None:
                task.due_date = task_data.due_date
        
        task.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(task)
        
        return task
        
    except WorkerError as e:
        raise HTTPException(status_code=422, detail=f"AI processing failed: {e}")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update task: {e}")


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a task by ID.
    """
    try:
        # Check if task exists
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Delete task
        delete_query = delete(Task).where(Task.id == task_id)
        await db.execute(delete_query)
        await db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {e}")


@router.post("/summary", response_model=SummaryResponse)
async def generate_summary(
    summary_request: SummaryRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generate an AI-powered summary of tasks within a date range.
    
    Analyzes tasks and provides insights, key themes, and recommendations.
    """
    try:
        # Query tasks within date range
        query = select(Task).where(
            and_(
                Task.created_at >= summary_request.start_date,
                Task.created_at <= summary_request.end_date
            )
        ).order_by(Task.created_at.desc())
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        if not tasks:
            return SummaryResponse(
                summary="No tasks found in the specified date range.",
                start_date=summary_request.start_date,
                end_date=summary_request.end_date,
                task_count=0
            )
        
        # Convert tasks to format expected by AI worker
        task_data = []
        for task in tasks:
            task_dict = {
                "title": task.title,
                "description": task.description,
                "label": task.label,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat()
            }
            task_data.append(task_dict)
        
        # Generate summary using AI worker
        summary_result = await execute_worker("bulk_summarizer", {
            "tasks": task_data,
            "start_date": summary_request.start_date.isoformat(),
            "end_date": summary_request.end_date.isoformat()
        })
        
        return SummaryResponse(
            summary=summary_result["summary"],
            start_date=summary_request.start_date,
            end_date=summary_request.end_date,
            task_count=len(tasks)
        )
        
    except WorkerError as e:
        raise HTTPException(status_code=422, detail=f"Summary generation failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {e}")


@router.get("/labels/", response_model=List[str])
async def get_task_labels(
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get all unique task labels for filtering.
    """
    try:
        query = select(Task.label).distinct().where(Task.label.isnot(None))
        result = await db.execute(query)
        labels = [row[0] for row in result.fetchall()]
        
        return sorted(labels)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get labels: {e}")
