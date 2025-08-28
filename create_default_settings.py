import requests
import json
from datetime import datetime

def create_default_settings():
    base_url = 'https://dance-admin-1.preview.emergentagent.com'
    api_url = f'{base_url}/api'
    
    # Login to get token
    login_data = {'email': 'admin@test.com', 'password': 'admin123'}
    response = requests.post(f'{api_url}/auth/login', json=login_data, timeout=10)
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return False
        
    token = response.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Default settings to create
    default_settings = [
        # Theme settings
        {"category": "theme", "key": "selected_theme", "value": "dark", "data_type": "string", "description": "Selected theme"},
        {"category": "theme", "key": "font_size", "value": "medium", "data_type": "string", "description": "Font size"},
        {"category": "theme", "key": "custom_primary_color", "value": "#a855f7", "data_type": "string", "description": "Primary color"},
        {"category": "theme", "key": "custom_secondary_color", "value": "#ec4899", "data_type": "string", "description": "Secondary color"},
        {"category": "theme", "key": "animations_enabled", "value": True, "data_type": "boolean", "description": "Enable animations"},
        {"category": "theme", "key": "glassmorphism_enabled", "value": True, "data_type": "boolean", "description": "Enable glassmorphism"},
        
        # Booking settings
        {"category": "booking", "key": "private_lesson_color", "value": "#3b82f6", "data_type": "string", "description": "Private lesson color"},
        {"category": "booking", "key": "meeting_color", "value": "#22c55e", "data_type": "string", "description": "Meeting color"},
        {"category": "booking", "key": "training_color", "value": "#f59e0b", "data_type": "string", "description": "Training color"},
        {"category": "booking", "key": "party_color", "value": "#a855f7", "data_type": "string", "description": "Party color"},
        {"category": "booking", "key": "confirmed_status_color", "value": "#22c55e", "data_type": "string", "description": "Confirmed status color"},
        {"category": "booking", "key": "pending_status_color", "value": "#f59e0b", "data_type": "string", "description": "Pending status color"},
        {"category": "booking", "key": "cancelled_status_color", "value": "#ef4444", "data_type": "string", "description": "Cancelled status color"},
        {"category": "booking", "key": "teacher_color_coding_enabled", "value": True, "data_type": "boolean", "description": "Enable teacher color coding"},
        
        # Calendar settings
        {"category": "calendar", "key": "default_view", "value": "daily", "data_type": "string", "description": "Default calendar view"},
        {"category": "calendar", "key": "start_hour", "value": 9, "data_type": "integer", "description": "Calendar start hour"},
        {"category": "calendar", "key": "end_hour", "value": 21, "data_type": "integer", "description": "Calendar end hour"},
        {"category": "calendar", "key": "time_slot_minutes", "value": 60, "data_type": "integer", "description": "Time slot duration"},
        
        # Display settings
        {"category": "display", "key": "language", "value": "en", "data_type": "string", "description": "Display language"},
        {"category": "display", "key": "currency_symbol", "value": "$", "data_type": "string", "description": "Currency symbol"},
        {"category": "display", "key": "compact_mode", "value": False, "data_type": "boolean", "description": "Compact display mode"},
        
        # Business rules
        {"category": "business_rules", "key": "late_cancellation_fee", "value": 75.50, "data_type": "float", "description": "Late cancellation fee"},
        {"category": "business_rules", "key": "cancellation_policy_hours", "value": 24, "data_type": "integer", "description": "Cancellation policy hours"},
        {"category": "business_rules", "key": "auto_confirm_bookings", "value": True, "data_type": "boolean", "description": "Auto confirm bookings"}
    ]
    
    # Insert settings directly into MongoDB using the backend's database connection
    from motor.motor_asyncio import AsyncIOMotorClient
    import asyncio
    import os
    from dotenv import load_dotenv
    from pathlib import Path
    import uuid
    
    # Load environment variables
    ROOT_DIR = Path(__file__).parent / 'backend'
    load_dotenv(ROOT_DIR / '.env')
    
    async def insert_settings():
        mongo_url = os.environ.get('MONGO_URL')
        client = AsyncIOMotorClient(mongo_url)
        db = client.get_database()
        
        created_count = 0
        for setting in default_settings:
            # Check if setting already exists
            existing = await db.settings.find_one({
                "category": setting["category"], 
                "key": setting["key"]
            })
            
            if not existing:
                setting_doc = {
                    "id": str(uuid.uuid4()),
                    "category": setting["category"],
                    "key": setting["key"],
                    "value": setting["value"],
                    "data_type": setting["data_type"],
                    "description": setting["description"],
                    "updated_at": datetime.utcnow()
                }
                
                await db.settings.insert_one(setting_doc)
                created_count += 1
                print(f"✅ Created setting: {setting['category']}.{setting['key']}")
            else:
                print(f"ℹ️ Setting exists: {setting['category']}.{setting['key']}")
        
        print(f"\n📝 Created {created_count} new settings")
        client.close()
        return created_count
    
    # Run the async function
    return asyncio.run(insert_settings())

if __name__ == "__main__":
    create_default_settings()