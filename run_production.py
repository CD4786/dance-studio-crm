#!/usr/bin/env python3
"""
Production server runner for Dance Studio CRM
This script runs the entire application (frontend + backend) through a single Python server
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🚀 Starting Dance Studio CRM Production Server...")
    
    # Get the current directory
    current_dir = Path(__file__).parent
    backend_dir = current_dir / "backend"
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Set environment variables if needed
    os.environ.setdefault("HOST", "0.0.0.0")
    os.environ.setdefault("PORT", "8000")
    
    print("📍 Backend directory:", backend_dir)
    print("🌐 Server will be available at: http://localhost:8000")
    print("🎯 API endpoints available at: http://localhost:8000/api/*")
    print("💻 Frontend (React app) available at: http://localhost:8000/")
    print("")
    
    try:
        # Run the FastAPI server with uvicorn
        cmd = [
            "uvicorn", 
            "server:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ]
        
        print(f"🔄 Running command: {' '.join(cmd)}")
        print("=" * 60)
        
        # Execute the uvicorn command
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()