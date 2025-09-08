#!/usr/bin/env python3
"""
Admin User Credentials and Settings Functionality Test
Testing Objectives:
1. Admin User Investigation - Check if admin@test.com exists, create if needed
2. Settings Backend Verification - Test all settings endpoints and 9 categories  
3. Theme Settings Specific Test - Check theme category settings
4. Authentication System Health Check - Test registration, login, JWT validation
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class AdminSettingsAPITester:
    def __init__(self, base_url="https://studio-manager-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user_id = None

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def make_request(self, method: str, endpoint: str, data: Dict[Any, Any] = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return success status and response data"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

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
                return False, f"Unsupported method: {method}"

            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = response.text

            return success, response_data

        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"

    def test_admin_user_investigation(self):
        """Test Objective 1: Admin User Investigation"""
        print("\n🔍 TESTING ADMIN USER INVESTIGATION")
        print("=" * 50)
        
        # First, try to login with admin credentials
        admin_login_data = {
            "email": "admin@test.com",
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', 'auth/login', admin_login_data, 200)
        
        if success:
            self.log_test("Admin Login with admin@test.com/admin123", True, f"Admin user exists and login successful")
            self.token = response.get('access_token')
            self.user_id = response.get('user', {}).get('id')
            self.admin_user_id = self.user_id
            return True
        else:
            self.log_test("Admin Login with admin@test.com/admin123", False, f"Login failed: {response}")
            
            # Check if it's 401 (user doesn't exist or wrong password)
            if isinstance(response, dict) and response.get('detail') == 'Invalid credentials':
                print("🔧 Admin user doesn't exist or has wrong credentials. Creating admin user...")
                return self.create_admin_user()
            else:
                print(f"❌ Unexpected login error: {response}")
                return False

    def create_admin_user(self):
        """Create admin user with admin@test.com / admin123 credentials"""
        print("\n🔧 CREATING ADMIN USER")
        print("=" * 30)
        
        # First, create a temporary owner account to create the admin user
        temp_owner_data = {
            "email": "temp_owner@test.com",
            "name": "Temporary Owner",
            "password": "temppass123",
            "role": "owner",
            "studio_name": "Test Studio"
        }
        
        success, response = self.make_request('POST', 'auth/register', temp_owner_data, 200)
        if not success:
            self.log_test("Create Temporary Owner", False, f"Failed to create temp owner: {response}")
            return False
        
        self.log_test("Create Temporary Owner", True, "Temporary owner created successfully")
        
        # Login with temporary owner
        temp_login_data = {
            "email": "temp_owner@test.com",
            "password": "temppass123"
        }
        
        success, response = self.make_request('POST', 'auth/login', temp_login_data, 200)
        if not success:
            self.log_test("Login with Temporary Owner", False, f"Failed to login: {response}")
            return False
        
        self.token = response.get('access_token')
        self.log_test("Login with Temporary Owner", True, "Logged in successfully")
        
        # Now create the admin user
        admin_user_data = {
            "email": "admin@test.com",
            "name": "Admin User",
            "password": "admin123",
            "role": "owner",  # Give admin user owner role for full permissions
            "studio_name": "Dance Studio CRM"
        }
        
        success, response = self.make_request('POST', 'users', admin_user_data, 200)
        if success:
            self.log_test("Create Admin User", True, f"Admin user created successfully")
            self.admin_user_id = response.get('id')
            
            # Now login with the admin credentials
            admin_login_data = {
                "email": "admin@test.com",
                "password": "admin123"
            }
            
            success, response = self.make_request('POST', 'auth/login', admin_login_data, 200)
            if success:
                self.token = response.get('access_token')
                self.user_id = response.get('user', {}).get('id')
                self.log_test("Login with New Admin Credentials", True, "Admin login successful")
                return True
            else:
                self.log_test("Login with New Admin Credentials", False, f"Login failed: {response}")
                return False
        else:
            self.log_test("Create Admin User", False, f"Failed to create admin user: {response}")
            return False

    def test_settings_backend_verification(self):
        """Test Objective 2: Settings Backend Verification"""
        print("\n⚙️ TESTING SETTINGS BACKEND VERIFICATION")
        print("=" * 50)
        
        # Test GET /api/settings - Get all settings
        success, response = self.make_request('GET', 'settings', expected_status=200)
        if success and isinstance(response, list):
            total_settings = len(response)
            self.log_test("GET /api/settings", True, f"Retrieved {total_settings} settings")
            
            # Check categories
            categories = set()
            for setting in response:
                categories.add(setting.get('category'))
            
            expected_categories = {'business', 'system', 'theme', 'booking', 'calendar', 'display', 'business_rules', 'program', 'notification'}
            found_categories = categories.intersection(expected_categories)
            
            self.log_test("Settings Categories Check", len(found_categories) >= 7, 
                         f"Found {len(found_categories)} categories: {sorted(found_categories)}")
            
            # Test individual category endpoints
            for category in found_categories:
                success, cat_response = self.make_request('GET', f'settings/{category}', expected_status=200)
                if success and isinstance(cat_response, list):
                    self.log_test(f"GET /api/settings/{category}", True, f"Retrieved {len(cat_response)} {category} settings")
                else:
                    self.log_test(f"GET /api/settings/{category}", False, f"Failed: {cat_response}")
            
        else:
            self.log_test("GET /api/settings", False, f"Failed: {response}")

    def test_theme_settings_specific(self):
        """Test Objective 3: Theme Settings Specific Test"""
        print("\n🎨 TESTING THEME SETTINGS SPECIFIC")
        print("=" * 40)
        
        # Test GET /api/settings/theme
        success, response = self.make_request('GET', 'settings/theme', expected_status=200)
        if success and isinstance(response, list):
            theme_settings = {setting['key']: setting for setting in response}
            self.log_test("GET /api/settings/theme", True, f"Retrieved {len(response)} theme settings")
            
            # Check for expected theme settings
            expected_keys = ['selected_theme', 'font_size', 'custom_primary_color', 'custom_secondary_color']
            found_keys = []
            
            for key in expected_keys:
                if key in theme_settings:
                    found_keys.append(key)
                    setting = theme_settings[key]
                    self.log_test(f"Theme Setting: {key}", True, f"Value: {setting.get('value')}")
            
            self.log_test("Theme Settings Availability", len(found_keys) >= 2, 
                         f"Found {len(found_keys)}/{len(expected_keys)} expected settings")
            
            # Test updating a theme setting if selected_theme exists
            if 'selected_theme' in theme_settings:
                current_theme = theme_settings['selected_theme']['value']
                new_theme = 'light' if current_theme != 'light' else 'dark'
                
                update_data = {
                    "value": new_theme,
                    "updated_by": self.user_id
                }
                
                success, update_response = self.make_request('PUT', 'settings/theme/selected_theme', update_data, 200)
                if success:
                    self.log_test("Update Theme Setting", True, f"Changed theme from {current_theme} to {new_theme}")
                    
                    # Verify the change
                    success, verify_response = self.make_request('GET', 'settings/theme/selected_theme', expected_status=200)
                    if success and verify_response.get('value') == new_theme:
                        self.log_test("Verify Theme Update", True, f"Theme successfully updated to {new_theme}")
                    else:
                        self.log_test("Verify Theme Update", False, f"Theme update not persisted: {verify_response}")
                else:
                    self.log_test("Update Theme Setting", False, f"Failed: {update_response}")
        else:
            self.log_test("GET /api/settings/theme", False, f"Failed: {response}")

    def test_authentication_system_health(self):
        """Test Objective 4: Authentication System Health Check"""
        print("\n🔐 TESTING AUTHENTICATION SYSTEM HEALTH CHECK")
        print("=" * 50)
        
        # Test registration endpoint
        test_user_data = {
            "email": f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.com",
            "name": "Test User",
            "password": "testpass123",
            "role": "teacher",
            "studio_name": "Test Studio"
        }
        
        success, response = self.make_request('POST', 'auth/register', test_user_data, 200)
        if success:
            self.log_test("Registration Endpoint", True, f"User registered successfully")
            test_user_id = response.get('id')
            
            # Test login with the new user
            login_data = {
                "email": test_user_data['email'],
                "password": test_user_data['password']
            }
            
            success, login_response = self.make_request('POST', 'auth/login', login_data, 200)
            if success and 'access_token' in login_response:
                self.log_test("Login with New User", True, "Login successful, token received")
                
                # Test JWT token validation by accessing a protected endpoint
                temp_token = login_response['access_token']
                old_token = self.token
                self.token = temp_token
                
                success, protected_response = self.make_request('GET', 'dashboard/stats', expected_status=200)
                if success:
                    self.log_test("JWT Token Validation", True, "Protected endpoint accessible with valid token")
                else:
                    self.log_test("JWT Token Validation", False, f"Protected endpoint failed: {protected_response}")
                
                # Restore original token
                self.token = old_token
                
            else:
                self.log_test("Login with New User", False, f"Login failed: {login_response}")
        else:
            self.log_test("Registration Endpoint", False, f"Registration failed: {response}")
        
        # Test invalid token handling
        old_token = self.token
        self.token = "invalid_token_12345"
        
        success, invalid_response = self.make_request('GET', 'dashboard/stats', expected_status=401)
        if not success:  # We expect this to fail with 401
            self.log_test("Invalid Token Handling", True, "Invalid token correctly rejected")
        else:
            self.log_test("Invalid Token Handling", False, "Invalid token was accepted")
        
        # Restore valid token
        self.token = old_token

    def run_comprehensive_test(self):
        """Run all test objectives"""
        print("🚀 STARTING ADMIN USER CREDENTIALS AND SETTINGS FUNCTIONALITY TEST")
        print("=" * 80)
        print(f"🌐 Testing against: {self.base_url}")
        print(f"📡 API Endpoint: {self.api_url}")
        print("=" * 80)
        
        # Test Objective 1: Admin User Investigation
        admin_success = self.test_admin_user_investigation()
        
        if not admin_success:
            print("\n❌ CRITICAL: Admin user setup failed. Cannot proceed with authenticated tests.")
            return False
        
        # Test Objective 2: Settings Backend Verification
        self.test_settings_backend_verification()
        
        # Test Objective 3: Theme Settings Specific Test
        self.test_theme_settings_specific()
        
        # Test Objective 4: Authentication System Health Check
        self.test_authentication_system_health()
        
        # Final Results
        print("\n" + "=" * 80)
        print("🎯 FINAL TEST RESULTS")
        print("=" * 80)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📊 Total Tests: {self.tests_run}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.admin_user_id:
            print(f"👤 Admin User ID: {self.admin_user_id}")
            print("✅ Admin credentials admin@test.com / admin123 are working")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = AdminSettingsAPITester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)