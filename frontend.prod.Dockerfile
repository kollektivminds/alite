# frontend.prod.Dockerfile

# --- Stage 1: Build the React App ---
FROM node:22.19.5

# --- Setup ---
# Set the default working directory for all subsequent commands.
WORKDIR /app

# --- Dependency Installation ---
# Copy the requirements file first to leverage Docker's layer caching.
COPY app/frontend/package.json app/frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install

# --- Application Code ---
# Copy the backend application source code into the container.
COPY ./app/frontend ./
RUN pnpm run build

# --- Stage 2: Serve the App with Nginx ---
FROM nginx:stable-alpine

# Copy the built static files from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy the nginx config file
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]