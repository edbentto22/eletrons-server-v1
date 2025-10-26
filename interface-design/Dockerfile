# Minimal React/Vite frontend build - Coolify Compatible
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install minimal system dependencies
RUN apk add --no-cache curl

# Copy package files
COPY package*.json ./

# Install all dependencies in one step
RUN npm ci --silent

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Simple health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Serve the built files from build directory (configured in vite.config.ts)
CMD ["npx", "serve", "-s", "build", "-l", "3000"]