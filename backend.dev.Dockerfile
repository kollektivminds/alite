# backend.dev.Dockerfile

# --- Base Image ---
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION=1.7.1
ENV POETRY_VIRTUALENVS_CREATE=false

# Install system dependencies and Poetry
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/*

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# --- Setup ---
WORKDIR /app

# --- Dependency Installation ---
COPY /backend/pyproject.toml /backend/poetry.lock* ./

# Install the Python dependencies. The --no-cache-dir flag keeps the image size down.
RUN poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the backend code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# The CMD uses --reload for automatic restarts on code changes
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]