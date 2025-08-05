# 🩰 Dance Studio CRM

A comprehensive dance studio management system similar to crm.dance, built with FastAPI, React, and MongoDB.

## ✨ Features

- **Multi-Role Authentication**: Owner, Manager, Teacher roles
- **Dashboard**: Real-time stats and analytics
- **Teacher Management**: Add teachers with specialties
- **Class Scheduling**: Schedule classes with calendar integration
- **Weekly Calendar**: Beautiful calendar interface
- **Studio Management**: Room allocation and capacity management

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- MongoDB

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload
```

### Frontend Setup
```bash
cd frontend
yarn install
yarn start
```

## 🔧 Environment Variables

### Backend (.env)
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="dance_studio"
SECRET_KEY="your-secret-key"
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL="http://localhost:8000"
```

## 📱 Usage

1. **Register**: Create an account as Studio Owner
2. **Login**: Access your dashboard
3. **Add Teachers**: Manage your instructor team
4. **Schedule Classes**: Create and organize dance classes
5. **View Calendar**: Monitor your weekly schedule

## 🛠 Tech Stack

- **Backend**: FastAPI, MongoDB, JWT Authentication
- **Frontend**: React, TailwindCSS, shadcn/ui
- **Database**: MongoDB with Motor (async)
- **UI Components**: Custom React components with Radix UI

## 📋 API Endpoints

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User authentication
- `GET /api/dashboard/stats` - Dashboard statistics
- `POST /api/teachers` - Create teacher
- `GET /api/teachers` - List teachers
- `POST /api/classes` - Schedule class
- `GET /api/classes` - List classes
- `GET /api/calendar/weekly` - Weekly calendar data

## 🚀 Deployment

See `deployment-guide.md` for detailed deployment instructions to:
- **Frontend**: Vercel/Netlify
- **Backend**: Railway/Render/Heroku
- **Database**: MongoDB Atlas

## 📄 License

MIT License - feel free to use for your dance studio!