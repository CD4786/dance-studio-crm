# Use Python slim image (lighter)
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

# Copy pre-built frontend (we'll build it locally)
COPY frontend/build ./static

# Expose port
EXPOSE 8000

# Start command
CMD uvicorn server:app --host 0.0.0.0 --port $PORT