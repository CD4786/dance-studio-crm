#!/bin/bash
set -e

echo "🚀 Railway Build Starting..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r backend/requirements.txt

# Install Node.js dependencies  
echo "📦 Installing Node.js dependencies..."
cd frontend
yarn install --frozen-lockfile

# Build React application with Railway URL
echo "🏗️ Building React app for Railway..."
export REACT_APP_BACKEND_URL="https://dependable-imagination-production.up.railway.app"
echo "Using REACT_APP_BACKEND_URL: $REACT_APP_BACKEND_URL"
yarn build

# Verify build was created
echo "✅ Build verification:"
ls -la build/
ls -la build/static/

echo "🎉 Build completed successfully!"
cd ..
echo "📁 Final directory structure:"
ls -la frontend/build/