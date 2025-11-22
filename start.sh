#!/bin/bash

# Start script for LangGraph Supervisor

echo "🚀 Starting LangGraph Supervisor..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env with your API keys before continuing."
    exit 1
fi

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for postgres to be ready
echo "⏳ Waiting for PostgreSQL..."
sleep 5

# Run migrations (optional - tables are auto-created on startup)
echo "📊 Running database migrations..."
if docker-compose exec -T backend alembic upgrade head 2>/dev/null; then
    echo "✅ Migrations completed"
else
    echo "⚠️  Migrations skipped (tables will be auto-created on startup)"
fi

echo "✅ Setup complete!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"

