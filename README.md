# LangGraph Supervisor - Production Stack

A production-ready implementation of the LangGraph Supervisor agent with user authentication, conversation persistence, and a modern React frontend.

## Architecture

- **Backend**: FastAPI (Python) with async support
- **Frontend**: React with Vite
- **Database**: PostgreSQL
- **Authentication**: FastAPI Users (JWT)
- **Streaming**: WebSocket for real-time responses

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.13+ (for local backend development)

### Using Docker Compose (Recommended)

1. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Start all services**:
   ```bash
   docker-compose up -d
   ```

3. **Run database migrations**:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Local Development

#### Backend

```bash
cd backend
pip install -e .
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key-change-in-production
GOOGLE_API_KEY=your-google-api-key
BRAVE_API_KEY=your-brave-api-key
DATABASE_URL=postgresql+asyncpg://langraph:langraph_dev_password@localhost:5432/langraph_supervisor

# Local Agents (vLLM) Configuration
# Set USE_LOCAL_AGENTS=true to use vLLM for database and sharepoint sub-agents
USE_LOCAL_AGENTS=false
VLLM_API_BASE=http://localhost:8001/v1
VLLM_MODEL=microsoft/Phi-4-mini-instruct
VLLM_TEMPERATURE=0.0
VLLM_MAX_TOKENS=4096
```

## Features

- ✅ User authentication (register/login)
- ✅ JWT-based session management
- ✅ Conversation persistence
- ✅ Real-time streaming via WebSocket
- ✅ Tool execution status display
- ✅ Conversation history
- ✅ Multi-agent supervisor system
- ✅ MCP tool integration

## API Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/jwt/login` - Login
- `GET /api/auth/users/me` - Get current user
- `GET /api/chat/conversations` - List conversations
- `GET /api/chat/conversations/{id}/messages` - Get messages
- `POST /api/chat/` - Send message (REST)
- `WS /api/chat/ws/{conversation_id}` - WebSocket streaming

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Config, security
│   │   ├── db/           # Database models
│   │   └── services/     # Business logic
│   ├── alembic/          # Database migrations
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   └── context/      # State management
│   └── Dockerfile
└── docker-compose.yml
```

## Migration from Streamlit

The original Streamlit app (`streamlit_app.py`) has been replaced with this production stack. All functionality has been preserved and enhanced with:

- User management
- Persistent conversations
- Better error handling
- Scalable architecture

## License

MIT

