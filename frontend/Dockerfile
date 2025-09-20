# Multi-stage build for Frontend
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create non-root user
RUN addgroup -g 1001 -S nodejs \
    && adduser -S appuser -u 1001 -G nodejs

# Set ownership
RUN chown -R appuser:nodejs /usr/share/nginx/html \
    && chown -R appuser:nodejs /var/cache/nginx \
    && chown -R appuser:nodejs /var/log/nginx \
    && chown -R appuser:nodejs /etc/nginx/conf.d \
    && touch /var/run/nginx.pid \
    && chown -R appuser:nodejs /var/run/nginx.pid

USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]