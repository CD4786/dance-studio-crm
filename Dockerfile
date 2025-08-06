# Use Python 3.11 as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Node.js and yarn
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g yarn \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy frontend package files and install Node dependencies
COPY frontend/package.json frontend/yarn.lock frontend/
WORKDIR /app/frontend
RUN yarn install --frozen-lockfile

# Copy frontend source and build React app
COPY frontend/ .
RUN REACT_APP_BACKEND_URL=https://dependable-imagination-production.up.railway.app yarn build

# Go back to app root and copy all files
WORKDIR /app
COPY . .

# Expose port
EXPOSE 8000

# Start the application
CMD ["python", "start.py"]