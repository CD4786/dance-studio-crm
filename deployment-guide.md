# 🚀 Dance Studio CRM - Deployment Guide

## Project Structure
```
dance-studio-crm/
├── backend/
│   ├── server.py              # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   └── .env                  # Backend environment variables
├── frontend/
│   ├── src/
│   │   ├── App.js            # Main React component
│   │   ├── App.css           # Styles
│   │   ├── index.js          # Entry point
│   │   ├── index.css         # Global styles
│   │   └── components/       # UI components
│   ├── public/               # Static assets
│   ├── package.json          # Dependencies
│   ├── tailwind.config.js    # Tailwind config
│   └── postcss.config.js     # PostCSS config
└── README.md

## Environment Variables Needed

### Backend (.env)
MONGO_URL="your_mongodb_atlas_connection_string"
DB_NAME="dance_studio_production"
SECRET_KEY="your_super_secret_jwt_key_here"

### Frontend (.env)
REACT_APP_BACKEND_URL="https://your-backend-url.railway.app"
```

## Deployment Steps

### 1. GitHub Repository Setup
```bash
git init
git add .
git commit -m "Initial commit: Dance Studio CRM"
git branch -M main
git remote add origin https://github.com/yourusername/dance-studio-crm.git
git push -u origin main
```

### 2. Backend Deployment (Railway)
1. Sign up at https://railway.app
2. Connect GitHub repository
3. Select backend folder
4. Set environment variables
5. Deploy

### 3. Frontend Deployment (Vercel)
1. Sign up at https://vercel.com
2. Connect GitHub repository
3. Select frontend folder
4. Set REACT_APP_BACKEND_URL
5. Deploy

### 4. Database Setup (MongoDB Atlas)
1. Create account at https://mongodb.com
2. Create cluster
3. Get connection string
4. Update backend .env

## Post-Deployment
1. Test authentication flow
2. Verify teacher management
3. Check class scheduling
4. Confirm calendar functionality

Your CRM will be live at:
- Frontend: https://your-app.vercel.app
- Backend: https://your-backend.railway.app