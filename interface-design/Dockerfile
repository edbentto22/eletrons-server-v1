# Multi-stage build for React/Vite frontend
FROM node:18-alpine as builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (incluindo devDependencies para o build)
RUN npm ci

# Verify Vite installation and npm scripts
RUN npm list vite || echo "Vite not found in dependencies"
RUN cat package.json | grep -A 5 '"scripts"'
RUN which npm && npm --version
RUN ls -la node_modules/.bin/ | grep vite || echo "Vite binary not found"

# Copy source code
COPY . .

# Build the application with explicit path
RUN npx vite build

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