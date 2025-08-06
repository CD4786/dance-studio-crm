# Multi-stage build for React + FastAPI
FROM node:18 AS frontend-builder

# Build frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Python backend stage
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy built frontend
COPY --from=frontend-builder /app/frontend/build ./static

# Create startup script
RUN echo '#!/bin/bash\nuvicorn server:app --host 0.0.0.0 --port $PORT' > start.sh
RUN chmod +x start.sh

# Expose port
EXPOSE $PORT

# Start the application
CMD ["./start.sh"]