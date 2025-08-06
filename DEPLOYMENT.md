# 🚀 Dance Studio CRM - Deployment Guide

## Quick Deploy Options

### Option 1: Railway (Recommended)
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "Deploy from GitHub repo"
4. Connect this repository
5. Set environment variables:
   ```
   MONGO_URL=<your_mongodb_atlas_connection_string>
   SECRET_KEY=<generate_random_secret_key>
   TWILIO_ACCOUNT_SID=<optional_twilio_sid>
   TWILIO_AUTH_TOKEN=<optional_twilio_token>
   TWILIO_PHONE_NUMBER=<optional_twilio_number>
   ```
6. Deploy!

### Option 2: Heroku
1. Install Heroku CLI
2. Create app: `heroku create your-crm-app`
3. Add MongoDB: `heroku addons:create mongolab`
4. Set environment variables: `heroku config:set SECRET_KEY=your-key`
5. Deploy: `git push heroku main`

### Option 3: Vercel
1. Install Vercel CLI: `npm i -g vercel`
2. Run: `vercel`
3. Follow prompts

## Environment Variables Required

### Required
- `MONGO_URL`: MongoDB connection string
- `SECRET_KEY`: Random secret for JWT tokens

### Optional (for SMS)
- `TWILIO_ACCOUNT_SID`: Twilio Account SID
- `TWILIO_AUTH_TOKEN`: Twilio Auth Token  
- `TWILIO_PHONE_NUMBER`: Twilio phone number

## MongoDB Setup

### Option 1: MongoDB Atlas (Free)
1. Go to [mongodb.com/atlas](https://mongodb.com/atlas)
2. Create free account
3. Create cluster
4. Get connection string
5. Add to `MONGO_URL` environment variable

### Option 2: Railway MongoDB
1. In Railway dashboard
2. Add "MongoDB" service
3. Copy connection URL
4. Add to `MONGO_URL`

## Post-Deployment

1. Visit your deployed URL
2. Register first admin account
3. Add teachers and students
4. Configure SMS settings (optional)

## Support

Your CRM includes:
- ✅ Student & Teacher Management
- ✅ Daily Calendar with Drag & Drop
- ✅ SMS Reminders via Twilio
- ✅ Enrollment System
- ✅ Modern Dark UI
- ✅ Mobile Responsive