#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Wait for the database to be ready
# (You might need a more robust wait script in production)
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the FastAPI application with Uvicorn
echo "Starting FastAPI server..."
# Use --host 0.0.0.0 to make it accessible outside the container
# Use --reload for development to automatically restart on code changes
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload