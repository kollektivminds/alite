# backend.prod.Dockerfile

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

# --- Application Code ---
# Copy the backend application source code into the container.
COPY ./app/backend /app

# --- Network Configuration ---
# Expose port 8000 to allow traffic to the container.
EXPOSE 8000

# --- Run Command ---
# Define the command to execute when the container starts.
# Runs the Uvicorn server, binding it to all network interfaces (0.0.0.0).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]