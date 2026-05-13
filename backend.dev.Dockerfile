# backend.dev.Dockerfile

# --- Base Image ---
FROM python:3.12-slim

# --- Setup ---
WORKDIR /app

# --- Dependency Installation ---
COPY app/backend/requirements.txt .

# Install the Python dependencies. The --no-cache-dir flag keeps the image size down.
RUN pip install --no-cache-dir -r requirements.txt

# The CMD uses --reload for automatic restarts on code changes
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]