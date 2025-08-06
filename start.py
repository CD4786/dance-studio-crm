#!/usr/bin/env python3
"""
Railway deployment startup script
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

if __name__ == "__main__":
    import uvicorn
    from server import app
    
    port = int(os.environ.get("PORT", 8000))
    
    print("🚀 Starting Railway deployment...")
    print(f"📡 Port: {port}")
    print(f"🌐 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'development')}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)