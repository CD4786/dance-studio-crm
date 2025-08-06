#!/bin/bash
set -e

echo "🚀 Starting Railway build process..."

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
yarn build

echo "✅ Build completed successfully!"

# Verify build exists
if [ -d "build" ]; then
    echo "✅ React build directory created successfully"
    echo "📁 Build contents:"
    ls -la build/
else
    echo "❌ React build directory not found!"
    exit 1
fi

cd ..
echo "🎉 Ready for deployment!"