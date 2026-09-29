"""Example 47: Deployment - Docker container setup.

Example Docker configuration for running ApexGraphSwarm
in a containerized environment.
"""
# Dockerfile content (save as Dockerfile)
DOCKERFILE = """
FROM python:3.11-slim

WORKDIR /app

# Copy application
COPY apexgraphswarm/ ./apexgraphswarm/
COPY examples/ ./examples/

# Create data directory
RUN mkdir -p /data

# Environment variables
ENV APEX_CONTROL_DB=/data/control.sqlite
ENV APEX_MAX_ACTIVE=16
ENV APEX_MAX_AGENTS=100
ENV APEX_MAX_RUN_COST=100000000
ENV PYTHONUNBUFFERED=1

# Run as non-root user
RUN useradd -m apex && chown -R apex:apex /data
USER apex

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python3 -c "from apexgraphswarm.control import ControlStore; s = ControlStore('/data/control.sqlite'); s.close()" || exit 1

ENTRYPOINT ["python3", "-m", "apexgraphswarm"]
"""

# Docker Compose content (save as docker-compose.yml)
COMPOSE = """
version: '3.8'

services:
  apexgraphswarm:
    build: .
    ports:
      - "3010:3010"
    volumes:
      - apex-data:/data
    environment:
      - APEX_CONTROL_DB=/data/control.sqlite
      - APEX_MAX_ACTIVE=16
      - APEX_MAX_AGENTS=100
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python3", "-c", "from apexgraphswarm.control import ControlStore; s = ControlStore('/data/control.sqlite'); s.close()"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  apex-data:
"""

print("Dockerfile:")
print(DOCKERFILE)
print("\ndocker-compose.yml:")
print(COMPOSE)
print("\nTo deploy:")
print("  docker-compose up -d")
print("  docker-compose logs -f")
