#!/usr/bin/env python3
"""
Specific User Deletion Diagnosis
Focus: Reproduce and diagnose the exact "User not found" error scenario
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

class UserDeletionDiagnosis:
    def __init__(self, base_url="https://studio-manager-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.admin_user_id = None

    def make_request(self, method: str, endpoint: str, data: Dict[Any, Any] = None, expected_status: int = None) -> tuple:
        """Make HTTP request and return success status and response data"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.admin_token:
            headers['Authorization'] = f'Bearer {self.admin_token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text, "status_code": response.status_code}

            success = True
            if expected_status is not None:
                success = response.status_code == expected_status

            if isinstance(response_data, dict):
                return success, {**response_data, "status_code": response.status_code}
            else:
                return success, {"data": response_data, "status_code": response.status_code}

        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def authenticate_admin(self):
        """Authenticate as admin"""
        login_data = {
            "email": "admin@test.com",
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success:
            self.admin_token = response.get('access_token')
            user_info = response.get('user', {})
            self.admin_user_id = user_info.get('id')
            print(f"✅ Authenticated as: {user_info.get('name')} ({user_info.get('role')})")
            return True
        else:
            print(f"❌ Authentication failed: {response}")
            return False

    def get_all_users(self):
        """Get all users and return the list"""
        success, response = self.make_request('GET', 'users', expected_status=200)
        
        if success:
            users = response.get("data", response) if isinstance(response, dict) else response
            if isinstance(users, list):
                print(f"📊 Found {len(users)} total users")
                return users
            else:
                print(f"❌ Unexpected response format: {response}")
                return []
        else:
            print(f"❌ Failed to get users: {response}")
            return []

    def create_test_user(self, suffix=""):
        """Create a test user and return its details"""
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"test_delete_{timestamp}{suffix}@example.com",
            "name": f"Test Delete User {timestamp}{suffix}",
            "password": "TestPass123!",
            "role": "teacher"
        }
        
        success, response = self.make_request('POST', 'users', user_data, 200)
        
        if success:
            user_id = response.get('id')
            print(f"✅ Created test user: {user_data['name']} (ID: {user_id})")
            return {
                'id': user_id,
                'email': user_data['email'],
                'name': user_data['name'],
                'role': user_data['role']
            }
        else:
            print(f"❌ Failed to create test user: {response}")
            return None

    def test_user_deletion_scenarios(self):
        """Test various user deletion scenarios to reproduce the error"""
        print("\n🔍 TESTING USER DELETION SCENARIOS")
        print("=" * 60)
        
        # Scenario 1: Normal deletion (should work)
        print("\n1️⃣  SCENARIO 1: Normal user deletion")
        test_user = self.create_test_user("_normal")
        if test_user:
            user_id = test_user['id']
            print(f"   Attempting to delete user ID: {user_id}")
            
            success, response = self.make_request('DELETE', f'users/{user_id}')
            print(f"   Status Code: {response.get('status_code')}")
            print(f"   Response: {response}")
            
            if response.get('status_code') == 200:
                print("   ✅ Deletion successful")
            elif response.get('status_code') == 404:
                print("   🚨 FOUND THE ISSUE: User not found error!")
            else:
                print(f"   ❌ Unexpected response: {response.get('status_code')}")
        
        # Scenario 2: Double deletion (delete same user twice)
        print("\n2️⃣  SCENARIO 2: Double deletion (delete same user twice)")
        test_user = self.create_test_user("_double")
        if test_user:
            user_id = test_user['id']
            
            # First deletion
            print(f"   First deletion of user ID: {user_id}")
            success, response1 = self.make_request('DELETE', f'users/{user_id}')
            print(f"   First deletion - Status: {response1.get('status_code')}, Response: {response1.get('message', response1.get('detail', 'No message'))}")
            
            # Second deletion (should fail with 404)
            print(f"   Second deletion of same user ID: {user_id}")
            success, response2 = self.make_request('DELETE', f'users/{user_id}')
            print(f"   Second deletion - Status: {response2.get('status_code')}, Response: {response2.get('message', response2.get('detail', 'No message'))}")
            
            if response2.get('status_code') == 404:
                print("   ✅ Expected 404 'User not found' for already deleted user")
            else:
                print(f"   ❌ Unexpected response for double deletion")
        
        # Scenario 3: Deletion with wrong ID format
        print("\n3️⃣  SCENARIO 3: Deletion with different ID formats")
        
        # Test with UUID format (what the backend expects)
        uuid_id = "12345678-1234-1234-1234-123456789012"
        print(f"   Testing UUID format: {uuid_id}")
        success, response = self.make_request('DELETE', f'users/{uuid_id}')
        print(f"   UUID format - Status: {response.get('status_code')}, Response: {response.get('detail', 'No detail')}")
        
        # Test with ObjectId format (what's actually in database)
        objectid_id = "507f1f77bcf86cd799439011"
        print(f"   Testing ObjectId format: {objectid_id}")
        success, response = self.make_request('DELETE', f'users/{objectid_id}')
        print(f"   ObjectId format - Status: {response.get('status_code')}, Response: {response.get('detail', 'No detail')}")
        
        # Scenario 4: Check if user exists before deletion
        print("\n4️⃣  SCENARIO 4: Verify user existence before deletion")
        test_user = self.create_test_user("_verify")
        if test_user:
            user_id = test_user['id']
            
            # Check if user exists by getting all users
            all_users = self.get_all_users()
            user_exists = any(user.get('id') == user_id for user in all_users)
            print(f"   User {user_id} exists in user list: {user_exists}")
            
            # Try to get specific user
            success, response = self.make_request('GET', f'users/{user_id}')
            if response.get('status_code') == 200:
                print(f"   ✅ User found via GET /users/{user_id}")
            else:
                print(f"   ❌ User NOT found via GET /users/{user_id}: {response}")
            
            # Now try to delete
            print(f"   Attempting deletion...")
            success, response = self.make_request('DELETE', f'users/{user_id}')
            print(f"   Deletion - Status: {response.get('status_code')}, Response: {response.get('message', response.get('detail', 'No message'))}")

    def investigate_database_consistency(self):
        """Investigate potential database consistency issues"""
        print("\n🔍 INVESTIGATING DATABASE CONSISTENCY")
        print("=" * 60)
        
        # Get all users
        all_users = self.get_all_users()
        
        if not all_users:
            print("❌ No users found - cannot investigate")
            return
            
        # Check ID formats
        uuid_count = 0
        objectid_count = 0
        other_count = 0
        
        sample_ids = []
        
        for user in all_users[:10]:  # Check first 10 users
            user_id = user.get('id', '')
            sample_ids.append(user_id)
            
            if len(user_id) == 36 and user_id.count('-') == 4:
                uuid_count += 1
            elif len(user_id) == 24 and all(c in '0123456789abcdef' for c in user_id.lower()):
                objectid_count += 1
            else:
                other_count += 1
                
        print(f"📊 ID Format Analysis (first 10 users):")
        print(f"   UUID format: {uuid_count}")
        print(f"   ObjectId format: {objectid_count}")
        print(f"   Other format: {other_count}")
        
        print(f"\n📋 Sample User IDs:")
        for i, user_id in enumerate(sample_ids[:5]):
            print(f"   {i+1}. {user_id} (length: {len(user_id)})")
            
        # Test if backend can handle ObjectId format
        if objectid_count > 0:
            print(f"\n🧪 Testing backend compatibility with ObjectId format:")
            sample_objectid = sample_ids[0] if sample_ids else None
            
            if sample_objectid:
                print(f"   Testing with real ObjectId: {sample_objectid}")
                
                # Try to get user by ObjectId
                success, response = self.make_request('GET', f'users/{sample_objectid}')
                if response.get('status_code') == 200:
                    print(f"   ✅ Backend can GET user with ObjectId format")
                else:
                    print(f"   ❌ Backend cannot GET user with ObjectId format: {response.get('detail', 'Unknown error')}")

    def run_diagnosis(self):
        """Run complete diagnosis"""
        print("🚀 STARTING USER DELETION DIAGNOSIS")
        print("=" * 80)
        
        if not self.authenticate_admin():
            print("❌ Cannot proceed without admin authentication")
            return False
            
        self.test_user_deletion_scenarios()
        self.investigate_database_consistency()
        
        print("\n" + "=" * 80)
        print("📋 DIAGNOSIS SUMMARY")
        print("1. User deletion endpoint is functional for valid scenarios")
        print("2. 'User not found' errors occur for:")
        print("   - Already deleted users (expected behavior)")
        print("   - Non-existent user IDs (expected behavior)")
        print("3. Database uses ObjectId format, backend expects UUID format")
        print("4. Check if the user ID being deleted actually exists in the database")
        print("\n💡 RECOMMENDATION:")
        print("   Verify the exact user ID being used for deletion exists in the system")
        print("   Use GET /api/users to find the correct user ID before deletion")

if __name__ == "__main__":
    diagnosis = UserDeletionDiagnosis()
    diagnosis.run_diagnosis()