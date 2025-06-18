# TaskGenius API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, no authentication is required. The API uses OpenAI API key configured via environment variables.

## Content Type
All requests and responses use `application/json` content type.

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "field_name",
      "value": "invalid_value"
    }
  }
}
```

### Error Codes
- `VALIDATION_ERROR` (422): Input validation failed
- `AI_PROCESSING_ERROR` (422): AI processing failed
- `TASK_NOT_FOUND` (404): Task not found
- `DATABASE_ERROR` (500): Database operation failed
- `RATE_LIMIT_EXCEEDED` (429): Rate limit exceeded
- `INTERNAL_SERVER_ERROR` (500): Unexpected server error

## Endpoints

### Health Check

#### GET /health
Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "task-manager-api",
  "version": "1.0.0"
}
```

### Root

#### GET /
Get API information.

**Response:**
```json
{
  "message": "Welcome to Task Manager API",
  "docs": "/docs",
  "health": "/health"
}
```

### Tasks

#### POST /api/v1/tasks/
Create a new task with AI processing.

**Request Body:**
```json
{
  "description": "Need to finish the quarterly report for the board meeting next Friday at 2pm"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "title": "Finish Quarterly Report",
  "description": "Need to finish the quarterly report for the board meeting next Friday at 2pm",
  "label": "work",
  "due_date": "2025-06-27T14:00:00",
  "created_at": "2025-06-17T23:33:48.361709",
  "updated_at": "2025-06-17T23:33:48.361713"
}
```

**AI Processing:**
- Extracts concise title from description
- Parses natural language dates (e.g., "next Friday at 2pm")
- Automatically categorizes task with appropriate label
- Handles relative dates and time expressions

#### GET /api/v1/tasks/
List tasks with optional filtering and pagination.

**Query Parameters:**
- `skip` (int, optional): Number of tasks to skip (default: 0)
- `limit` (int, optional): Maximum number of tasks to return (default: 50, max: 100)
- `label` (string, optional): Filter by task label

**Examples:**
```
GET /api/v1/tasks/
GET /api/v1/tasks/?skip=10&limit=20
GET /api/v1/tasks/?label=work
GET /api/v1/tasks/?skip=0&limit=10&label=shopping
```

**Response (200 OK):**
```json
{
  "tasks": [
    {
      "id": 2,
      "title": "Finish Quarterly Report",
      "description": "Need to finish the quarterly report for the board meeting next Friday at 2pm",
      "label": "work",
      "due_date": "2025-06-27T14:00:00",
      "created_at": "2025-06-17T23:33:48.361709",
      "updated_at": "2025-06-17T23:33:48.361713"
    },
    {
      "id": 1,
      "title": "Buy organic milk and bread",
      "description": "Buy organic milk and bread from the grocery store tomorrow morning",
      "label": "shopping",
      "due_date": "2025-06-19T09:00:00",
      "created_at": "2025-06-17T23:33:28.802100",
      "updated_at": "2025-06-17T23:34:46.185692"
    }
  ],
  "total": 2,
  "skip": 0,
  "limit": 50
}
```

#### GET /api/v1/tasks/{task_id}
Get a specific task by ID.

**Path Parameters:**
- `task_id` (int): Task ID

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Buy organic milk and bread",
  "description": "Buy organic milk and bread from the grocery store tomorrow morning",
  "label": "shopping",
  "due_date": "2025-06-19T09:00:00",
  "created_at": "2025-06-17T23:33:28.802100",
  "updated_at": "2025-06-17T23:34:46.185692"
}
```

**Error Response (404 Not Found):**
```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task with ID 999 not found",
    "details": {
      "task_id": 999
    }
  }
}
```

#### PUT /api/v1/tasks/{task_id}
Update a task with AI reprocessing.

**Path Parameters:**
- `task_id` (int): Task ID

**Request Body:**
```json
{
  "description": "Buy organic milk and bread from the grocery store tomorrow morning"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Buy organic milk and bread",
  "description": "Buy organic milk and bread from the grocery store tomorrow morning",
  "label": "shopping",
  "due_date": "2025-06-19T09:00:00",
  "created_at": "2025-06-17T23:33:28.802100",
  "updated_at": "2025-06-17T23:34:46.185692"
}
```

**AI Reprocessing:**
- Re-extracts title, date, and label when description changes
- Maintains task ID and creation timestamp
- Updates modification timestamp

#### DELETE /api/v1/tasks/{task_id}
Delete a task.

**Path Parameters:**
- `task_id` (int): Task ID

**Response (204 No Content):**
No response body.

### Task Labels

#### GET /api/v1/tasks/labels/
Get all unique task labels.

**Response (200 OK):**
```json
["work", "shopping", "health", "personal", "urgent"]
```

### Task Summary

#### POST /api/v1/tasks/summary
Generate AI-powered summary of tasks within a date range.

**Request Body:**
```json
{
  "start_date": "2025-06-01T00:00:00",
  "end_date": "2025-06-30T23:59:59"
}
```

**Response (200 OK):**
```json
{
  "summary": "For the month of June 2025, you have a total of two tasks to manage. These tasks fall into two distinct categories: work and shopping. The work-related task is to finish the Quarterly Report, which is a significant responsibility given its importance for the upcoming board meeting. The shopping task, which is to buy milk, is straightforward and does not have a specified deadline.\n\nThe key theme for this period is balancing a critical work obligation with a minor personal errand. The Quarterly Report is a high-priority task due on June 27th at 2:00 PM, which should be your primary focus. This task is crucial as it directly impacts the board meeting, suggesting that it requires careful attention and possibly collaboration with colleagues to ensure accuracy and completeness.\n\nGiven the upcoming deadline for the Quarterly Report, it is advisable to allocate dedicated time slots in your schedule to work on this task, ensuring you have ample time to review and make necessary revisions before the due date. For the shopping task, consider incorporating it into your routine errands to avoid last-minute rushes.\n\nIn summary, prioritize the completion of the Quarterly Report by setting interim goals leading up to the deadline, and manage your time effectively to accommodate both professional and personal tasks.",
  "start_date": "2025-06-01T00:00:00",
  "end_date": "2025-06-30T23:59:59",
  "task_count": 2
}
```

**AI Summary Features:**
- Analyzes task patterns and themes
- Identifies priorities and deadlines
- Provides actionable recommendations
- Considers task categories and workload balance

## Data Models

### Task Model
```json
{
  "id": "integer (auto-generated)",
  "title": "string (AI-extracted, 2-50 characters)",
  "description": "string (user input, 1-1000 characters)",
  "label": "string (AI-categorized, e.g., 'work', 'shopping')",
  "due_date": "string|null (ISO datetime, AI-parsed)",
  "created_at": "string (ISO datetime, auto-generated)",
  "updated_at": "string (ISO datetime, auto-updated)"
}
```

### Task Creation Request
```json
{
  "description": "string (required, 1-1000 characters)"
}
```

### Task Update Request
```json
{
  "description": "string (required, 1-1000 characters)"
}
```

### Summary Request
```json
{
  "start_date": "string (required, ISO datetime)",
  "end_date": "string (required, ISO datetime)"
}
```

## Rate Limiting

Currently, no rate limiting is implemented at the API level. However, OpenAI API rate limits apply to AI processing operations.

## Examples

### Create a Simple Task
```bash
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"description": "Buy milk"}'
```

### Create a Complex Task with Date
```bash
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"description": "Submit tax documents by April 15th at 5pm"}'
```

### List Work Tasks
```bash
curl "http://localhost:8000/api/v1/tasks/?label=work"
```

### Update a Task
```bash
curl -X PUT http://localhost:8000/api/v1/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"description": "Buy organic milk and eggs tomorrow"}'
```

### Get Monthly Summary
```bash
curl -X POST http://localhost:8000/api/v1/tasks/summary \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-06-01T00:00:00", "end_date": "2025-06-30T23:59:59"}'
```

### Delete a Task
```bash
curl -X DELETE http://localhost:8000/api/v1/tasks/1
```

## Interactive Documentation

Visit `http://localhost:8000/docs` for interactive Swagger/OpenAPI documentation where you can test all endpoints directly in your browser.
