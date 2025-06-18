# TaskGenius - AI-Powered Task Manager

A sophisticated task management application that leverages AI to intelligently extract task information from natural language descriptions, automatically categorize tasks, and provide insightful summaries.

## 🚀 Features

### Core Functionality
- **Natural Language Processing**: Create tasks using everyday language
- **AI-Powered Extraction**: Automatically extracts titles, due dates, and categories
- **Smart Categorization**: Intelligent labeling based on task content
- **Task Summarization**: AI-generated insights and recommendations
- **Full CRUD Operations**: Complete task management capabilities

### AI Capabilities
- **Title Extraction**: "Need to finish the quarterly report..." → "Finish Quarterly Report"
- **Date Parsing**: "next Friday at 2pm" → "2025-06-27T14:00:00"
- **Smart Categorization**: Automatically assigns labels like "work", "shopping", "health"
- **Context Understanding**: Handles relative dates like "tomorrow morning"
- **Bulk Analysis**: Summarizes multiple tasks with actionable insights

### Technical Features
- **Async Architecture**: Full async/await implementation for high performance
- **RESTful API**: Clean, well-documented API endpoints
- **Comprehensive Testing**: 200+ test cases with extensive coverage
- **Error Handling**: Robust exception handling with detailed error responses
- **Containerized**: Docker support for easy deployment
- **Production Ready**: Security best practices and health checks

## 🏗️ Architecture

```
task_manager/
├── app.py                   # FastAPI application with middleware and routing
├── views/                   # HTTP layer - API endpoints
│   └── tasks.py            # Task CRUD operations + summarization
├── workers/                 # AI processing layer
│   ├── base.py             # Abstract worker class with strategy pattern
│   ├── extractor.py        # Title/date/label extraction workers
│   └── summarizer.py       # Task summarization worker
├── libs/                    # Utility libraries
│   ├── openai_client.py    # Async OpenAI client with retry logic
│   ├── prompts.py          # AI prompt templates
│   ├── schema.py           # Pydantic models for validation
│   ├── date_tools.py       # Date parsing utilities
│   └── exceptions.py       # Custom exception classes
├── db.py                   # Database session management
├── models.py               # SQLAlchemy ORM models
└── tests/                  # Comprehensive test suite
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key
- Docker (optional)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TaskGenius
   ```

2. **Set up environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Run the application**
   ```bash
   python -m uvicorn app:app --reload
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   # Set your OpenAI API key in .env file
   docker-compose up --build
   ```

2. **Access the application**
   - API: http://localhost:8000
   - Health Check: http://localhost:8000/health

## 📚 API Documentation

### Core Endpoints

#### Create Task
```http
POST /api/v1/tasks/
Content-Type: application/json

{
  "description": "Need to finish the quarterly report for the board meeting next Friday at 2pm"
}
```

**Response:**
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

#### List Tasks
```http
GET /api/v1/tasks/?skip=0&limit=50&label=work
```

#### Update Task
```http
PUT /api/v1/tasks/{task_id}
Content-Type: application/json

{
  "description": "Updated task description"
}
```

#### Delete Task
```http
DELETE /api/v1/tasks/{task_id}
```

#### Get Task Summary
```http
POST /api/v1/tasks/summary
Content-Type: application/json

{
  "start_date": "2025-06-01T00:00:00",
  "end_date": "2025-06-30T23:59:59"
}
```

### Additional Endpoints

- `GET /api/v1/tasks/labels/` - Get all unique task labels
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_tasks_api.py -v
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing with database
- **AI Worker Tests**: Mocked AI processing pipeline tests
- **Error Handling Tests**: Exception and validation testing

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./tasks.db` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `RELOAD` | Enable auto-reload | `true` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `*` |

### Database Configuration

The application uses SQLite by default for simplicity and portability. The database file is created automatically on first run.

## 🤖 AI Integration

### OpenAI Models
- **Default Model**: `gpt-4o`
- **Structured Completion**: JSON schema validation
- **Function Calling**: Date calculation capabilities
- **Error Handling**: Retry logic with exponential backoff

### AI Workers

1. **ExtractTitleDateWorker**: Extracts concise titles and parses due dates
2. **ExtractLabelWorker**: Categorizes tasks into appropriate labels
3. **ExtractPriorityWorker**: Determines task priority levels
4. **BulkSummarizerWorker**: Analyzes multiple tasks for insights

### Prompt Engineering
- Context-aware prompts with examples
- Structured response schemas
- Confidence scoring for AI outputs
- Reasoning explanations for transparency

## 🔒 Security

### Best Practices
- Non-root user in Docker containers
- Environment variable validation
- Input sanitization and validation
- Comprehensive error handling
- Health checks and monitoring

### API Security
- CORS configuration
- Request validation with Pydantic
- Structured error responses
- Rate limiting ready (extensible)

## 🚀 Deployment

### Production Deployment

1. **Set environment variables**
   ```bash
   export OPENAI_API_KEY="your-api-key"
   export RELOAD=false
   ```

2. **Deploy with Docker**
   ```bash
   docker-compose up -d
   ```

3. **Health monitoring**
   ```bash
   curl http://localhost:8000/health
   ```

### Scaling Considerations
- Stateless design for horizontal scaling
- SQLite suitable for moderate loads
- Easy migration to PostgreSQL if needed
- Redis integration ready for caching

## 🛠️ Development

### Code Quality
- **Type Hints**: Full type annotation coverage
- **Async/Await**: Modern async Python patterns
- **Error Handling**: Comprehensive exception hierarchy
- **Testing**: High test coverage with pytest
- **Documentation**: Detailed docstrings and comments

### Architecture Patterns
- **Strategy Pattern**: Pluggable AI workers
- **Dependency Injection**: Testable components
- **Clean Architecture**: Separated concerns
- **Factory Pattern**: Client instantiation
- **Repository Pattern**: Data access abstraction

## 📈 Performance

### Optimizations
- Async database operations
- Connection pooling ready
- Efficient JSON parsing
- Minimal Docker image layers
- Health check endpoints

### Monitoring
- Structured logging ready
- Health check endpoints
- Error tracking with detailed context
- Performance metrics ready

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run the test suite
5. Submit a pull request

### Code Standards
- Follow PEP 8 style guidelines
- Add type hints for all functions
- Write comprehensive tests
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for providing the AI capabilities
- FastAPI for the excellent web framework
- SQLAlchemy for robust ORM functionality
- Pydantic for data validation
- pytest for comprehensive testing tools

---

**TaskGenius** - Transforming natural language into organized, actionable tasks with the power of AI.
