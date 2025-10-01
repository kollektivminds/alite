#!/bin/bash

# start_dev.sh - A script to launch the development environment for the language app.

# --- Configuration ---
BACKEND_DIR="./app/backend"
FRONTEND_DIR="./app/frontend"
BACKEND_VENV_PATH="./vocab/bin/activate"
BACKEND_ENV_FILE="$BACKEND_DIR/.env"

# --- Style and Color Definitions ---
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- Main Script Logic ---

echo -e "${YELLOW}Starting Development Environment...${NC}"

# --- 1. Load Backend Environment Variables ---
# Check if the .env file exists and then load it.
# This ensures variables like DATABASE_URL are available.
if [ -f "$BACKEND_ENV_FILE" ]; then
    echo -e "${BLUE}Loading backend environment variables from .env file...${NC}"
    export $(grep -v '^#' $BACKEND_ENV_FILE | xargs)
else
    echo -e "${YELLOW}Warning: Backend .env file not found at $BACKEND_ENV_FILE. DATABASE_URL might not be set.${NC}"
fi

# --- 2. Activate Python Virtual Environment ---
# Check if the virtual environment's activate script exists.
if [ -f "$BACKEND_VENV_PATH" ]; then
    echo -e "${BLUE}Activating Python virtual environment...${NC}"
    source "$BACKEND_VENV_PATH"
else
    echo -e "${YELLOW}Warning: Python virtual environment not found at $BACKEND_VENV_PATH. Make sure you've created it.${NC}"
fi

# --- 3. Start the Backend Server (Uvicorn) ---
echo -e "${GREEN}Starting FastAPI backend server with Uvicorn...${NC}"
(cd "$BACKEND_DIR" && uvicorn main:app --reload) &
BACKEND_PID=$! # Store the Process ID (PID) of the backend server

# --- 4. Start the Frontend Server (npm) ---
echo -e "${GREEN}Starting React frontend server with npm...${NC}"
(cd "$FRONTEND_DIR" && pnpm run dev) &
FRONTEND_PID=$! # Store the Process ID of the frontend server

# --- 5. Wait for User to Stop the Script ---
echo -e "${YELLOW}Development servers are running in the background.${NC}"
echo "Backend is running on PID: ${BACKEND_PID}"
echo "Frontend is running on PID: ${FRONTEND_PID}"
echo -e "${YELLOW}Press Ctrl+C to shut down all servers.${NC}"

# This function will run when Ctrl+C is pressed
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill $BACKEND_PID
    kill $FRONTEND_PID
    echo "All servers stopped."
}

# Trap the Ctrl+C signal (SIGINT) and call the cleanup function
trap cleanup SIGINT

# Wait indefinitely until the script is interrupted.
# This keeps the script alive so it can manage the background processes.
wait