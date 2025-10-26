# Multi-stage build for React/Vite frontend
FROM node:18-alpine as builder

# Set working directory
WORKDIR /app

# Install build dependencies for Alpine
RUN apk add --no-cache python3 make g++

# Copy package files
COPY package*.json ./

# Install dependencies (incluindo devDependencies para o build)
RUN npm ci --verbose

# Verify Vite installation and npm scripts
RUN npm list vite || echo "Vite not found in dependencies"
RUN cat package.json | grep -A 5 '"scripts"'
RUN which npm && npm --version
RUN ls -la node_modules/.bin/ | grep vite || echo "Vite binary not found"

# Copy source code
COPY . .

# Build the application with more robust error handling
RUN set -e && \
    echo "Starting Vite build..." && \
    NODE_ENV=production npx vite build --mode production --logLevel info || \
    (echo "Vite build failed. Checking for common issues..." && \
     echo "Node version: $(node --version)" && \
     echo "NPM version: $(npm --version)" && \
     echo "Vite version: $(npx vite --version)" && \
     echo "Current directory contents:" && ls -la && \
     echo "Source directory contents:" && ls -la src/ && \
     echo "Package.json scripts:" && cat package.json | grep -A 10 '"scripts"' && \
     echo "Memory info:" && cat /proc/meminfo | head -5 && \
     exit 1)

# Production stage
FROM nginx:alpine

# Copy built assets from builder stage (Vite configurado para usar 'build')
COPY --from=builder /app/build /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 3000
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]