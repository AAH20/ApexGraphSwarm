# ApexGraphSwarm - Multi-stage Dockerfile
# Builds Next.js frontend + Python backend into a single runtime image

# ============================================================
# Stage 1: Build Next.js frontend
# ============================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /build

# Copy package files first for better layer caching
COPY apps/web/package.json apps/web/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY apps/web/ ./

# Build the Next.js application
RUN npm run build

# ============================================================
# Stage 2: Python backend (stdlib-only, no dependencies)
# ============================================================
FROM python:3.12-slim AS python-builder

WORKDIR /python

# Copy Python package (stdlib-only, no pip install needed)
COPY apexgraphswarm/ ./apexgraphswarm/

# ============================================================
# Stage 3: Final runtime image
# ============================================================
FROM node:20-alpine

# Install Python 3 and required system packages
RUN apk add --no-cache \
    python3 \
    py3-pip \
    sqlite \
    && ln -sf /usr/bin/python3 /usr/bin/python

WORKDIR /app

# Copy Next.js build output
COPY --from=frontend-builder /build ./

# Copy Python backend
COPY --from=python-builder /python/apexgraphswarm ./apexgraphswarm

# Create runtime directory for SQLite and other data
RUN mkdir -p /app/.runtime

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3010
ENV APEX_CONTROL_DB_PATH=/app/.runtime/control.sqlite

# Expose the application port
EXPOSE 3010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3010 || exit 1

# Run the application
CMD ["npm", "start"]
