#!/bin/bash
set -e

echo "🚀 Starting Railway build process..."

# Set environment variables for React build
export REACT_APP_BACKEND_URL="https://dependable-imagination-production.up.railway.app"
echo "🔧 Set REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip install -r requirements.txt
cd ..

# Install frontend dependencies and build
echo "📦 Installing Node.js dependencies..."
cd frontend
yarn install --frozen-lockfile

echo "🏗️ Building React application..."
echo "Using environment variables:"
echo "REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL"
yarn build

echo "✅ Build completed successfully!"

# Verify build exists and contains correct URL
if [ -d "build" ]; then
    echo "✅ React build directory created successfully"
    echo "📁 Build contents:"
    ls -la build/
    
    # Check if the correct URL is in the build
    if grep -r "dependable-imagination-production.up.railway.app" build/static/js/ > /dev/null 2>&1; then
        echo "✅ Railway URL found in build files - correct!"
    else
        echo "❌ Railway URL NOT found in build files!"
        echo "🔍 Checking for any backend URLs in build..."
        grep -r "backend" build/static/js/ | head -3 || true
        exit 1
    fi
else
    echo "❌ React build directory not found!"
    exit 1
fi

cd ..
echo "🎉 Ready for deployment!"