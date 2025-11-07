#!/bin/bash
set -e

# Navigate to the app directory if necessary (depends on WORKDIR in Dockerfile)
# cd /app/frontend 

# Install dependencies if node_modules is empty or package.json changed
# (A volume mount might make this check less reliable, often dependencies
# are installed during the image build step instead)
if [ ! -d "node_modules" ] || ! cmp -s package.json node_modules/.package.json.sum; then
  echo "Installing dependencies..."
  pnpm install
  # Optional: Create a checksum file after successful install
  # cp package.json node_modules/.package.json.sum 
fi

# Start the Vite development server
echo "Starting Vite dev server..."
# Use --host to make it accessible outside the container
exec pnpm run dev --host 0.0.0.0 --port 5173