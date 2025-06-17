"""Main FastAPI application."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from db import close_db, init_db
from libs.exceptions import (
    TaskManagerError, ValidationError, DatabaseError, AIProcessingError,
    TaskNotFoundError, RateLimitError, format_error_response
)

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="Task Manager API",
    description="A task manager with AI-powered task extraction and summarization",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "service": "task-manager-api",
        "version": "1.0.0"
    }


@app.get("/")
async def root() -> dict:
    """
    Root endpoint.
    
    Returns:
        dict: Welcome message and API information
    """
    return {
        "message": "Welcome to Task Manager API",
        "docs": "/docs",
        "health": "/health"
    }


# Import workers to ensure they are registered
import workers.extractor  # noqa: F401
import workers.summarizer  # noqa: F401

# Exception handlers
@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(request: Request, exc: TaskNotFoundError):
    """Handle task not found errors."""
    return JSONResponse(
        status_code=404,
        content=format_error_response(exc)
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=422,
        content=format_error_response(exc)
    )


@app.exception_handler(AIProcessingError)
async def ai_processing_error_handler(request: Request, exc: AIProcessingError):
    """Handle AI processing errors."""
    return JSONResponse(
        status_code=422,
        content=format_error_response(exc)
    )


@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    """Handle database errors."""
    return JSONResponse(
        status_code=500,
        content=format_error_response(exc)
    )


@app.exception_handler(RateLimitError)
async def rate_limit_error_handler(request: Request, exc: RateLimitError):
    """Handle rate limit errors."""
    headers = {}
    if exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    
    return JSONResponse(
        status_code=429,
        content=format_error_response(exc),
        headers=headers
    )


@app.exception_handler(TaskManagerError)
async def general_error_handler(request: Request, exc: TaskManagerError):
    """Handle general task manager errors."""
    return JSONResponse(
        status_code=500,
        content=format_error_response(exc)
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            }
        }
    )


# Include routers
from views.tasks import router as tasks_router
app.include_router(tasks_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "true").lower() == "true",
    )
