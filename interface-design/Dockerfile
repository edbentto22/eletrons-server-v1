# Single-stage build for React/Vite frontend - Optimized for Coolify
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    curl

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies with specific npm configuration
RUN npm config set fund false && \
    npm config set audit false && \
    npm ci --only=production --no-optional

# Install dev dependencies separately for build
RUN npm ci --only=development --no-optional

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Start nginx to serve the built files
CMD ["npx", "serve", "-s", "build", "-l", "3000"]