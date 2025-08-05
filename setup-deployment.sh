#!/bin/bash

echo "🚀 Dance Studio CRM - Deployment Setup Script"
echo "============================================="

# Step 1: Initialize Git Repository
echo "📁 Step 1: Initializing Git Repository..."
git init
git add .
git commit -m "Initial commit: Dance Studio CRM with authentication, dashboard, and teacher management"

# Step 2: Create GitHub Repository (Manual step)
echo ""
echo "📋 Step 2: Create GitHub Repository"
echo "   1. Go to https://github.com/new"
echo "   2. Repository name: dance-studio-crm"
echo "   3. Description: Comprehensive dance studio management system"
echo "   4. Make it Public or Private (your choice)"
echo "   5. Don't initialize with README (we already have one)"
echo "   6. Click 'Create repository'"
echo ""
read -p "Press Enter when you've created the GitHub repository..."

# Step 3: Connect to GitHub
echo ""
echo "🔗 Step 3: Connecting to GitHub..."
read -p "Enter your GitHub username: " username
read -p "Enter your repository name (default: dance-studio-crm): " reponame
reponame=${reponame:-dance-studio-crm}

git branch -M main
git remote add origin "https://github.com/$username/$reponame.git"
git push -u origin main

echo "✅ Code pushed to GitHub successfully!"

# Step 4: Database Setup Instructions
echo ""
echo "🗄️  Step 4: Database Setup (MongoDB Atlas)"
echo "   1. Go to https://mongodb.com/atlas"
echo "   2. Create free account"
echo "   3. Create new cluster (M0 Free tier)"
echo "   4. Create database user"
echo "   5. Whitelist your IP (0.0.0.0/0 for now)"
echo "   6. Get connection string"
echo ""

# Step 5: Backend Deployment Instructions
echo ""
echo "🖥️  Step 5: Backend Deployment (Railway)"
echo "   1. Go to https://railway.app"
echo "   2. Sign up with GitHub"
echo "   3. Click 'New Project'"
echo "   4. Select 'Deploy from GitHub repo'"
echo "   5. Choose your dance-studio-crm repository"
echo "   6. Select 'backend' as root directory"
echo "   7. Add environment variables:"
echo "      - MONGO_URL: (your MongoDB Atlas connection string)"
echo "      - DB_NAME: dance_studio_production"
echo "      - SECRET_KEY: $(openssl rand -base64 32)"
echo "   8. Deploy!"
echo ""

# Step 6: Frontend Deployment Instructions
echo ""
echo "🌐 Step 6: Frontend Deployment (Vercel)"
echo "   1. Go to https://vercel.com"
echo "   2. Sign up with GitHub"
echo "   3. Click 'New Project'"
echo "   4. Import your dance-studio-crm repository"
echo "   5. Set root directory to 'frontend'"
echo "   6. Add environment variable:"
echo "      - REACT_APP_BACKEND_URL: (your Railway backend URL)"
echo "   7. Deploy!"
echo ""

echo "🎉 Setup Complete! Your Dance Studio CRM will be live at:"
echo "   - Frontend: https://your-app.vercel.app"
echo "   - Backend: https://your-backend.railway.app"
echo ""
echo "📝 Next steps:"
echo "   1. Test the authentication flow"
echo "   2. Add some teachers"
echo "   3. Schedule classes"
echo "   4. Share with your users!"