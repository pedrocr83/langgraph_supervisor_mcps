#!/bin/bash

set -euo pipefail

# Start script for LangGraph Supervisor

echo "🚀 Starting LangGraph Supervisor..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env with your API keys before continuing."
    exit 1
fi

# Determine PostgreSQL host port (avoid conflicts with local Postgres)
is_port_available() {
    python3 - "$1" <<'PY' "$1"
import socket
import sys

port = int(sys.argv[1])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(0.1)
    result = sock.connect_ex(("127.0.0.1", port))
sys.exit(0 if result != 0 else 1)
PY
}

select_postgres_port() {
    local user_port="${POSTGRES_PORT:-}"
    local default_port=5432
    local candidates=(5432 5433 5434 5435 5436 5437 5438 5439 5440)

    if [[ -n "$user_port" ]]; then
        if is_port_available "$user_port"; then
            echo "📦 Using PostgreSQL host port $user_port (from POSTGRES_PORT)."
            export POSTGRES_PORT="$user_port"
            return
        fi
        echo "❌ POSTGRES_PORT=$user_port is already in use. Please choose another value."
        exit 1
    fi

    for port in "${candidates[@]}"; do
        if is_port_available "$port"; then
            POSTGRES_PORT="$port"
            export POSTGRES_PORT
            if [[ "$port" == "$default_port" ]]; then
                echo "📦 Using PostgreSQL host port $port."
            else
                echo "ℹ️  Port $default_port is busy; using PostgreSQL host port $port instead."
            fi
            return
        fi
    done

    echo "❌ Unable to find a free host port for PostgreSQL (tried ${candidates[*]})."
    exit 1
}

select_postgres_port

# Resolve docker compose command (plugin preferred)
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
else
    echo "❌ Docker Compose is not installed. Please install docker compose plugin or docker-compose v1."
    exit 1
fi

# Guard against unsupported DOCKER_HOST scheme with docker-compose v1
if [[ "${COMPOSE_CMD[0]}" == "docker-compose" ]] && [[ "${DOCKER_HOST:-}" == http+docker://* ]]; then
    echo "❌ Detected DOCKER_HOST='${DOCKER_HOST}'. docker-compose v1 does not support the http+docker scheme."
    echo "   Please clear DOCKER_HOST or use the Docker Compose plugin (docker compose)."
    exit 1
fi

# Start services
echo "🐳 Starting Docker services..."
"${COMPOSE_CMD[@]}" up -d || {
    echo "❌ Failed to start Docker services."
    exit 1
}

# Wait for postgres to be ready
echo "⏳ Waiting for PostgreSQL..."
sleep 5

# Run migrations (optional - tables are auto-created on startup)
echo "📊 Running database migrations..."
if "${COMPOSE_CMD[@]}" exec -T backend alembic upgrade head 2>/dev/null; then
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

