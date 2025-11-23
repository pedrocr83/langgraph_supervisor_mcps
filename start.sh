#!/bin/bash

set -euo pipefail

# Start script for LangGraph Supervisor

# Create logs directory
LOGS_DIR="logs"
mkdir -p "$LOGS_DIR"

# Log file with timestamp
LOG_FILE="$LOGS_DIR/startup_$(date +%Y%m%d_%H%M%S).log"
DOCKER_LOG_FILE="$LOGS_DIR/docker_$(date +%Y%m%d).log"

# Function to log both to console and file
log() {
    echo "$1" | tee -a "$LOG_FILE"
}

log "🚀 Starting LangGraph Supervisor..."
log "📝 Log file: $LOG_FILE"
log "📝 Docker log file: $DOCKER_LOG_FILE"
log ""

# Check if .env exists
if [ ! -f .env ]; then
    log "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    log "📝 Please edit .env with your API keys before continuing."
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
    local default_port=5433  # Changed default to 5433 to avoid common conflicts
    local candidates=(5433 5434 5432 5435 5436 5437 5438 5439 5440)

    if [[ -n "$user_port" ]]; then
        if is_port_available "$user_port"; then
            log "📦 Using PostgreSQL host port $user_port (from POSTGRES_PORT)."
            export POSTGRES_PORT="$user_port"
            return
        fi
        log "❌ POSTGRES_PORT=$user_port is already in use. Please choose another value."
        exit 1
    fi

    for port in "${candidates[@]}"; do
        if is_port_available "$port"; then
            POSTGRES_PORT="$port"
            export POSTGRES_PORT
            if [[ "$port" == "$default_port" ]]; then
                log "📦 Using PostgreSQL host port $port."
            else
                log "ℹ️  Port $default_port is busy; using PostgreSQL host port $port instead."
            fi
            return
        fi
    done

    log "❌ Unable to find a free host port for PostgreSQL (tried ${candidates[*]})."
    exit 1
}

select_postgres_port

# Resolve docker compose command (plugin preferred)
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
else
    log "❌ Docker Compose is not installed. Please install docker compose plugin or docker-compose v1."
    exit 1
fi

# Guard against unsupported DOCKER_HOST scheme with docker-compose v1
if [[ "${COMPOSE_CMD[0]}" == "docker-compose" ]] && [[ "${DOCKER_HOST:-}" == http+docker://* ]]; then
    log "❌ Detected DOCKER_HOST='${DOCKER_HOST}'. docker-compose v1 does not support the http+docker scheme."
    log "   Please clear DOCKER_HOST or use the Docker Compose plugin (docker compose)."
    exit 1
fi

# Log startup information
log "=" | tee -a "$LOG_FILE"
log "STARTUP INFORMATION" | tee -a "$LOG_FILE"
log "=" | tee -a "$LOG_FILE"
log "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
log "Docker Compose: ${COMPOSE_CMD[*]}" | tee -a "$LOG_FILE"
log "PostgreSQL Port: ${POSTGRES_PORT:-5432}" | tee -a "$LOG_FILE"
log "" | tee -a "$LOG_FILE"

# Start services
log "🐳 Starting Docker services..."
"${COMPOSE_CMD[@]}" up -d 2>&1 | tee -a "$LOG_FILE" || {
    log "❌ Failed to start Docker services."
    exit 1
}

# Start logging docker-compose logs in background
log "📝 Starting continuous Docker log capture to $DOCKER_LOG_FILE..."
"${COMPOSE_CMD[@]}" logs -f >> "$DOCKER_LOG_FILE" 2>&1 &
DOCKER_LOG_PID=$!
log "   Docker log PID: $DOCKER_LOG_PID"
log ""

# Wait for postgres to be ready
log "⏳ Waiting for PostgreSQL..."
max_wait=30
wait_count=0
while [ $wait_count -lt $max_wait ]; do
    if "${COMPOSE_CMD[@]}" exec -T postgres pg_isready -U langraph -d langraph_supervisor >/dev/null 2>&1; then
        log "✅ PostgreSQL is ready"
        break
    fi
    wait_count=$((wait_count + 1))
    sleep 1
done

if [ $wait_count -eq $max_wait ]; then
    log "⚠️  PostgreSQL not ready after ${max_wait}s, continuing anyway..."
fi

# Test database connection using psql (more reliable than SQLAlchemy for initial test)
log "📊 Testing database connection..."
if "${COMPOSE_CMD[@]}" exec -T postgres psql -U langraph -d langraph_supervisor -c "SELECT 1;" >/dev/null 2>&1; then
    log "✅ Database is accessible via psql"
else
    log "⚠️  Database connection test had issues"
    log "   This might be due to a fresh database initialization"
    log "   The application will create tables on startup if needed"
fi

# Skip migrations - tables auto-create on startup
log "ℹ️  Migrations skipped (tables auto-create on FastAPI startup)"
log "   This is the recommended approach for this application"

log ""
log "✅ Setup complete!"
log ""
log "🌐 Frontend: http://localhost:3000"
log "🔧 Backend API: http://localhost:8000"
log "📚 API Docs: http://localhost:8000/docs"
log ""
log "📝 Logs:"
log "   - Startup log: $LOG_FILE"
log "   - Docker logs: $DOCKER_LOG_FILE"
log "   - Application logs: $LOGS_DIR/misteriosai_*.log (inside backend container)"
log ""
log "To view live logs: tail -f $DOCKER_LOG_FILE"
log "To stop: docker-compose down"
log ""
log "Note: Docker logs are being continuously written to $DOCKER_LOG_FILE"
log "      (Background process PID: $DOCKER_LOG_PID)"

