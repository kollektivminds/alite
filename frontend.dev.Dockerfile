# frontend.dev.Dockerfile

FROM node:23.11.0

WORKDIR /app

# Copy package management files
COPY app/frontend/package.json app/frontend/pnpm-lock.yaml ./

# Install pnpm and dependencies
RUN npm install -g pnpm && pnpm install

# Expose the Vite development port
EXPOSE 5173

# The CMD runs the development server from your package.json
# "dev": "vite"
CMD ["pnpm", "run", "dev", "--host"]