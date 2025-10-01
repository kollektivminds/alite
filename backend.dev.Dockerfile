# backend.dev.Dockerfile

# --- Base Image ---
# Use an official Python slim image for a smaller production footprint.
FROM python:3.12-slim

# --- Setup ---
# Set the default working directory for all subsequent commands.
WORKDIR /app

# --- Dependency Installation ---
# Copy the requirements file first to leverage Docker's layer caching.
COPY app/backend/requirements.txt .

# Install the Python dependencies. The --no-cache-dir flag keeps the image size down.
RUN pip install --no-cache-dir -r requirements.txt

# The CMD uses --reload for automatic restarts on code changes
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]