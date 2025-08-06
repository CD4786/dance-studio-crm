# Railway Deployment Instructions

Railway will now use Docker to build the application.

## What the Dockerfile does:
1. Uses Python 3.11 as base image
2. Installs Node.js 18 and yarn
3. Installs Python backend dependencies
4. Installs frontend dependencies
5. Builds React app with Railway URL
6. Starts the FastAPI server

## Environment Variables Required:
Set these in Railway dashboard:
- DATABASE_URL=your-mongodb-connection-string
- DB_NAME=dance_studio_crm
- SECRET_KEY=your-production-secret

## Expected Result:
Railway deployment should now build successfully and show the Dance Studio CRM application.