#!/usr/bin/env python3
"""
Comprehensive Theme Settings Integration Test
Testing both backend API and frontend integration for theme dropdown issue.
"""

import requests
import json
from datetime import datetime

class ComprehensiveThemeTest:
    def __init__(self, base_url="https://dance-studio-crm-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def make_request(self, method: str, endpoint: str, data=None, expected_status: int = 200):
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
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text, "status_code": response.status_code}

            if not success:
                print(f"   Status: {response.status_code}, Expected: {expected_status}")
                print(f"   Response: {response_data}")

            return success, response_data

        except requests.exceptions.RequestException as e:
            print(f"   Request failed: {str(e)}")
            return False, {"error": str(e)}

    def setup_authentication(self):
        """Setup authentication for testing"""
        timestamp = datetime.now().strftime("%H%M%S")
        user_data = {
            "email": f"theme_comprehensive_{timestamp}@example.com",
            "name": f"Theme Comprehensive Test {timestamp}",
            "password": "TestPassword123!",
            "role": "owner",
            "studio_name": "Theme Comprehensive Test Studio"
        }
        
        success, response = self.make_request('POST', 'auth/register', user_data, 200)
        
        if success:
            login_data = {
                "email": user_data['email'],
                "password": user_data['password']
            }
            
            success, login_response = self.make_request('POST', 'auth/login', login_data, 200)
            
            if success:
                self.token = login_response.get('access_token')
                print(f"🔐 Authentication setup successful")
                return True
        
        print(f"❌ Authentication setup failed")
        return False

    def test_backend_theme_settings_complete(self):
        """Test complete backend theme settings functionality"""
        print("\n🔍 BACKEND THEME SETTINGS COMPLETE TEST")
        
        # Test 1: Get all settings
        success, all_settings = self.make_request('GET', 'settings', expected_status=200)
        if not success:
            self.log_test("Backend - Get All Settings", False, "- Failed to fetch settings")
            return False
        
        # Test 2: Filter theme settings
        theme_settings = [s for s in all_settings if s.get('category') == 'theme']
        theme_count = len(theme_settings)
        
        print(f"   📊 Found {theme_count} theme settings")
        for setting in theme_settings:
            key = setting.get('key')
            value = setting.get('value')
            data_type = setting.get('data_type')
            print(f"      • {key}: {value} ({data_type})")
        
        # Test 3: Get theme category specifically
        success, theme_category = self.make_request('GET', 'settings/theme', expected_status=200)
        if not success:
            self.log_test("Backend - Get Theme Category", False, "- Failed to fetch theme category")
            return False
        
        theme_category_count = len(theme_category)
        print(f"   🎨 Theme category has {theme_category_count} settings")
        
        # Test 4: Get selected_theme specifically
        success, selected_theme = self.make_request('GET', 'settings/theme/selected_theme', expected_status=200)
        if not success:
            self.log_test("Backend - Get Selected Theme", False, "- Failed to fetch selected_theme")
            return False
        
        current_theme = selected_theme.get('value')
        print(f"   🎯 Current selected theme: {current_theme}")
        
        # Test 5: Update theme to each option
        theme_options = ['dark', 'light', 'ocean']
        update_success_count = 0
        
        for theme in theme_options:
            update_data = {"value": theme}
            success, response = self.make_request('PUT', 'settings/theme/selected_theme', update_data, 200)
            if success and response.get('value') == theme:
                update_success_count += 1
                print(f"      ✅ Successfully updated to: {theme}")
            else:
                print(f"      ❌ Failed to update to: {theme}")
        
        overall_success = (theme_count >= 6 and 
                          theme_category_count >= 6 and 
                          current_theme in theme_options and 
                          update_success_count == len(theme_options))
        
        self.log_test("Backend Theme Settings Complete", overall_success, 
                     f"- {theme_count} settings, {update_success_count}/{len(theme_options)} updates successful")
        return overall_success

    def test_frontend_integration_data_structure(self):
        """Test the data structure that frontend expects"""
        print("\n🔍 FRONTEND INTEGRATION DATA STRUCTURE TEST")
        
        # Test what the frontend SettingsPage.js expects
        success, all_settings = self.make_request('GET', 'settings', expected_status=200)
        if not success:
            self.log_test("Frontend Integration - Settings Data", False, "- Failed to fetch settings")
            return False
        
        # Check if settings have all required fields for frontend
        required_fields = ['id', 'category', 'key', 'value', 'data_type', 'description', 'updated_at']
        theme_settings = [s for s in all_settings if s.get('category') == 'theme']
        
        print(f"   📋 Checking {len(theme_settings)} theme settings for frontend compatibility")
        
        frontend_compatible_count = 0
        for setting in theme_settings:
            missing_fields = []
            for field in required_fields:
                if field not in setting:
                    missing_fields.append(field)
            
            if len(missing_fields) == 0:
                frontend_compatible_count += 1
                print(f"      ✅ {setting['key']}: All fields present")
            else:
                print(f"      ❌ {setting['key']}: Missing fields: {missing_fields}")
        
        # Test specific theme dropdown data
        selected_theme_setting = next((s for s in theme_settings if s['key'] == 'selected_theme'), None)
        
        if selected_theme_setting:
            theme_value = selected_theme_setting['value']
            theme_type = selected_theme_setting['data_type']
            valid_theme = theme_value in ['dark', 'light', 'ocean']
            correct_type = theme_type == 'string'
            
            print(f"   🎯 Selected theme setting:")
            print(f"      Value: {theme_value} (valid: {valid_theme})")
            print(f"      Type: {theme_type} (correct: {correct_type})")
            
            theme_dropdown_ready = valid_theme and correct_type
        else:
            print(f"   ❌ selected_theme setting not found!")
            theme_dropdown_ready = False
        
        overall_success = (frontend_compatible_count == len(theme_settings) and theme_dropdown_ready)
        
        self.log_test("Frontend Integration Data Structure", overall_success, 
                     f"- {frontend_compatible_count}/{len(theme_settings)} settings compatible")
        return overall_success

    def test_theme_category_endpoint(self):
        """Test the specific theme category endpoint that frontend uses"""
        print("\n🔍 THEME CATEGORY ENDPOINT TEST")
        
        # This is the endpoint that SettingsPage.js uses to get theme settings
        success, theme_settings = self.make_request('GET', 'settings/theme', expected_status=200)
        
        if not success:
            self.log_test("Theme Category Endpoint", False, "- Failed to fetch /api/settings/theme")
            return False
        
        # Check if we get the expected theme settings
        expected_keys = ['selected_theme', 'font_size', 'custom_primary_color', 'custom_secondary_color', 'animations_enabled', 'glassmorphism_enabled']
        found_keys = [s['key'] for s in theme_settings]
        
        print(f"   📋 Expected keys: {expected_keys}")
        print(f"   📋 Found keys: {found_keys}")
        
        missing_keys = [key for key in expected_keys if key not in found_keys]
        extra_keys = [key for key in found_keys if key not in expected_keys]
        
        if missing_keys:
            print(f"   ❌ Missing keys: {missing_keys}")
        if extra_keys:
            print(f"   ℹ️  Extra keys: {extra_keys}")
        
        # Check selected_theme specifically
        selected_theme = next((s for s in theme_settings if s['key'] == 'selected_theme'), None)
        
        if selected_theme:
            print(f"   🎯 selected_theme found:")
            print(f"      ID: {selected_theme.get('id')}")
            print(f"      Category: {selected_theme.get('category')}")
            print(f"      Key: {selected_theme.get('key')}")
            print(f"      Value: {selected_theme.get('value')}")
            print(f"      Data Type: {selected_theme.get('data_type')}")
            print(f"      Description: {selected_theme.get('description')}")
            
            theme_complete = all(field in selected_theme for field in ['id', 'category', 'key', 'value', 'data_type'])
        else:
            print(f"   ❌ selected_theme not found in theme category!")
            theme_complete = False
        
        overall_success = len(missing_keys) == 0 and theme_complete
        
        self.log_test("Theme Category Endpoint", overall_success, 
                     f"- {len(found_keys)} settings, selected_theme: {'found' if selected_theme else 'missing'}")
        return overall_success

    def test_theme_dropdown_simulation(self):
        """Simulate what the frontend theme dropdown should do"""
        print("\n🔍 THEME DROPDOWN SIMULATION TEST")
        
        # Simulate frontend getting theme settings
        success, theme_settings = self.make_request('GET', 'settings/theme', expected_status=200)
        if not success:
            self.log_test("Theme Dropdown Simulation", False, "- Failed to get theme settings")
            return False
        
        # Find selected_theme setting
        selected_theme_setting = next((s for s in theme_settings if s['key'] == 'selected_theme'), None)
        
        if not selected_theme_setting:
            self.log_test("Theme Dropdown Simulation", False, "- selected_theme setting not found")
            return False
        
        current_value = selected_theme_setting['value']
        print(f"   🎯 Current theme: {current_value}")
        
        # Simulate dropdown options
        dropdown_options = [
            {'value': 'dark', 'label': '🌙 Dark Theme'},
            {'value': 'light', 'label': '☀️ Light Theme'},
            {'value': 'ocean', 'label': '🌊 Ocean Theme'}
        ]
        
        print(f"   📋 Dropdown options:")
        for option in dropdown_options:
            is_selected = option['value'] == current_value
            print(f"      {'✅' if is_selected else '  '} {option['label']} ({option['value']})")
        
        # Simulate changing theme (like frontend would do)
        test_theme = 'ocean' if current_value != 'ocean' else 'light'
        print(f"   🔄 Simulating theme change to: {test_theme}")
        
        update_data = {"value": test_theme}
        success, response = self.make_request('PUT', 'settings/theme/selected_theme', update_data, 200)
        
        if success:
            new_value = response.get('value')
            change_successful = new_value == test_theme
            print(f"      {'✅' if change_successful else '❌'} Theme changed to: {new_value}")
        else:
            change_successful = False
            print(f"      ❌ Failed to change theme")
        
        # Verify the change persisted
        success, updated_settings = self.make_request('GET', 'settings/theme/selected_theme', expected_status=200)
        if success:
            persisted_value = updated_settings.get('value')
            persistence_check = persisted_value == test_theme
            print(f"      {'✅' if persistence_check else '❌'} Theme persisted: {persisted_value}")
        else:
            persistence_check = False
            print(f"      ❌ Failed to verify theme persistence")
        
        overall_success = change_successful and persistence_check
        
        self.log_test("Theme Dropdown Simulation", overall_success, 
                     f"- Change: {'success' if change_successful else 'failed'}, Persist: {'success' if persistence_check else 'failed'}")
        return overall_success

    def run_comprehensive_test(self):
        """Run the complete comprehensive theme test"""
        print("🔍 COMPREHENSIVE THEME SETTINGS INTEGRATION TEST")
        print("=" * 60)
        print("Testing both backend API and frontend integration compatibility")
        print()
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return
        
        # Run all tests
        tests = [
            self.test_backend_theme_settings_complete,
            self.test_frontend_integration_data_structure,
            self.test_theme_category_endpoint,
            self.test_theme_dropdown_simulation
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 COMPREHENSIVE TEST SUMMARY")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL TESTS PASSED - Backend theme settings are fully functional")
            print("🔍 Theme dropdown should be working in frontend")
            print("💡 If dropdown still not showing, check:")
            print("   1. Frontend console for JavaScript errors")
            print("   2. Network tab for failed API requests")
            print("   3. React component rendering logic")
        else:
            print("❌ SOME TESTS FAILED - Issues found in backend theme settings")
            print("🔧 Fix the failing backend issues first")

if __name__ == "__main__":
    tester = ComprehensiveThemeTest()
    tester.run_comprehensive_test()