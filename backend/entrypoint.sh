#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

if [ "$#" -gt 0 ]; then
  echo "Starting with custom command: $*"
  exec "$@"
fi

PORT="${PORT:-8000}"
echo "Starting API on port ${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
