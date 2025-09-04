#!/usr/bin/env python3
"""
Booking Settings API Test Suite
Tests the booking settings API endpoints to diagnose BookingColorsManager issues.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class BookingSettingsAPITester:
    def __init__(self, base_url="https://studio-manager-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_token = None
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
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            if not success:
                print(f"   Status: {response.status_code}, Expected: {expected_status}")
                print(f"   Response: {response_data}")

            return success, response_data

        except requests.exceptions.RequestException as e:
            print(f"   Request failed: {str(e)}")
            return False, {"error": str(e)}

    def test_admin_login(self):
        """Test login with admin@test.com / admin123 credentials"""
        login_data = {
            "email": "admin@test.com",
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success:
            self.admin_token = response.get('access_token')
            self.token = self.admin_token  # Use admin token for all tests
            user_info = response.get('user', {})
            print(f"   👤 Admin user: {user_info.get('name', 'Unknown')} ({user_info.get('role', 'Unknown')})")
            
        self.log_test("Admin Login", success, f"- Admin token received: {'Yes' if self.admin_token else 'No'}")
        return success

    def test_booking_settings_retrieval(self):
        """Test GET /api/settings/booking endpoint"""
        success, response = self.make_request('GET', 'settings/booking', expected_status=200)
        
        if success:
            settings_count = len(response) if isinstance(response, list) else 0
            
            # Check for expected booking color settings
            expected_keys = [
                'private_lesson_color', 'meeting_color', 'training_color', 'party_color',
                'confirmed_status_color', 'pending_status_color', 'cancelled_status_color',
                'teacher_color_coding_enabled'
            ]
            
            found_keys = set()
            for setting in response:
                found_keys.add(setting.get('key', ''))
            
            has_all_keys = all(key in found_keys for key in expected_keys)
            success = success and settings_count >= 8 and has_all_keys
            
            print(f"   📊 Found settings: {sorted(found_keys)}")
            
        self.log_test("Booking Settings Retrieval", success, 
                     f"- Found {settings_count} booking settings with all expected keys: {has_all_keys}")
        return success

    def test_specific_booking_color_settings(self):
        """Test specific booking color settings exist and have proper values"""
        color_settings = [
            'private_lesson_color', 'meeting_color', 'training_color', 'party_color',
            'confirmed_status_color', 'pending_status_color', 'cancelled_status_color'
        ]
        
        valid_settings = 0
        
        for setting_key in color_settings:
            success, response = self.make_request('GET', f'settings/booking/{setting_key}', expected_status=200)
            
            if success:
                value = response.get('value', '')
                data_type = response.get('data_type', '')
                
                # Check if it's a valid hex color
                if isinstance(value, str) and value.startswith('#') and len(value) == 7 and data_type == 'string':
                    valid_settings += 1
                    print(f"   ✅ {setting_key}: {value}")
                else:
                    print(f"   ❌ {setting_key}: Invalid format - {value}")
            else:
                print(f"   ❌ {setting_key}: Not found")
        
        success = valid_settings == len(color_settings)
        self.log_test("Specific Booking Color Settings", success, 
                     f"- {valid_settings}/{len(color_settings)} color settings valid")
        return success

    def test_individual_setting_retrieval(self):
        """Test GET /api/settings/booking/{key} for individual settings"""
        test_keys = ['private_lesson_color', 'meeting_color', 'teacher_color_coding_enabled']
        successful_retrievals = 0
        
        for key in test_keys:
            success, response = self.make_request('GET', f'settings/booking/{key}', expected_status=200)
            
            if success:
                setting_key = response.get('key')
                setting_value = response.get('value')
                setting_category = response.get('category')
                
                if setting_key == key and setting_category == 'booking':
                    successful_retrievals += 1
                    print(f"   ✅ {key}: {setting_value}")
                else:
                    print(f"   ❌ {key}: Data mismatch")
            else:
                print(f"   ❌ {key}: Failed to retrieve")
        
        success = successful_retrievals == len(test_keys)
        self.log_test("Individual Setting Retrieval", success, 
                     f"- {successful_retrievals}/{len(test_keys)} individual settings retrieved")
        return success

    def test_booking_settings_creation_verification(self):
        """Test that default booking color settings were created during app initialization"""
        success, response = self.make_request('GET', 'settings/booking', expected_status=200)
        
        if success:
            settings_count = len(response) if isinstance(response, list) else 0
            
            # Count booking category settings specifically
            booking_settings = [s for s in response if s.get('category') == 'booking']
            booking_count = len(booking_settings)
            
            # Check for all expected settings
            expected_settings = {
                'private_lesson_color': '#3b82f6',
                'meeting_color': '#22c55e', 
                'training_color': '#f59e0b',
                'party_color': '#a855f7',
                'confirmed_status_color': '#22c55e',
                'pending_status_color': '#f59e0b',
                'cancelled_status_color': '#ef4444',
                'teacher_color_coding_enabled': True
            }
            
            found_settings = {}
            for setting in booking_settings:
                key = setting.get('key')
                value = setting.get('value')
                found_settings[key] = value
            
            all_present = all(key in found_settings for key in expected_settings.keys())
            success = success and booking_count >= 8 and all_present
            
            print(f"   📋 Expected vs Found:")
            for key, expected_value in expected_settings.items():
                found_value = found_settings.get(key, 'NOT FOUND')
                status = "✅" if found_value != 'NOT FOUND' else "❌"
                print(f"   {status} {key}: expected {expected_value}, found {found_value}")
            
        self.log_test("Booking Settings Creation Verification", success, 
                     f"- Found {booking_count} booking settings, all expected present: {all_present}")
        return success

    def test_booking_settings_authentication(self):
        """Test that booking settings endpoints require authentication"""
        # Save current token
        original_token = self.token
        
        # Test without token
        self.token = None
        success_no_auth, response = self.make_request('GET', 'settings/booking', expected_status=401)
        
        # Test with invalid token
        self.token = "invalid.token.here"
        success_invalid_auth, response = self.make_request('GET', 'settings/booking', expected_status=401)
        
        # Test update without auth
        self.token = None
        update_data = {"value": "#ff0000"}
        success_update_no_auth, response = self.make_request('PUT', 'settings/booking/private_lesson_color', 
                                                           update_data, expected_status=401)
        
        # Restore original token
        self.token = original_token
        
        # Test with valid auth (should work)
        success_with_auth, response = self.make_request('GET', 'settings/booking', expected_status=200)
        
        all_auth_tests_passed = success_no_auth and success_invalid_auth and success_update_no_auth and success_with_auth
        
        self.log_test("Booking Settings Authentication", all_auth_tests_passed, 
                     f"- No auth: 401 ✓, Invalid auth: 401 ✓, Update no auth: 401 ✓, Valid auth: 200 ✓")
        return all_auth_tests_passed

    def test_booking_settings_update_functionality(self):
        """Test updating booking color settings"""
        test_updates = [
            {"key": "private_lesson_color", "value": "#ff5722"},
            {"key": "meeting_color", "value": "#4caf50"},
            {"key": "teacher_color_coding_enabled", "value": False}
        ]
        
        successful_updates = 0
        
        for test_case in test_updates:
            update_data = {"value": test_case["value"]}
            success, response = self.make_request('PUT', f'settings/booking/{test_case["key"]}', 
                                                update_data, 200)
            
            if success:
                returned_value = response.get('value')
                if returned_value == test_case["value"]:
                    successful_updates += 1
                    print(f"   ✅ {test_case['key']}: Updated to {returned_value}")
                else:
                    print(f"   ❌ {test_case['key']}: Value mismatch - got {returned_value}")
            else:
                print(f"   ❌ {test_case['key']}: Failed to update")
        
        success = successful_updates == len(test_updates)
        self.log_test("Booking Settings Update Functionality", success, 
                     f"- {successful_updates}/{len(test_updates)} settings updated successfully")
        return success

    def test_booking_colors_hex_validation(self):
        """Test hex color validation for booking color settings"""
        # Test invalid hex colors (should fail)
        invalid_colors = ["#gggggg", "#12345", "red", "invalid_color", "#1234567"]
        validation_tests_passed = 0
        
        for invalid_color in invalid_colors:
            update_data = {"value": invalid_color}
            success, response = self.make_request('PUT', 'settings/booking/private_lesson_color', 
                                                update_data, 400)
            
            if success:
                validation_tests_passed += 1
                print(f"   ✅ Invalid color {invalid_color}: Correctly rejected")
            else:
                print(f"   ❌ Invalid color {invalid_color}: Should have been rejected")
        
        # Test valid hex colors (should succeed)
        valid_colors = ["#ffffff", "#000000", "#ff6b6b"]
        valid_color_tests = 0
        
        for valid_color in valid_colors:
            update_data = {"value": valid_color}
            success, response = self.make_request('PUT', 'settings/booking/private_lesson_color', 
                                                update_data, 200)
            
            if success:
                returned_value = response.get('value')
                if returned_value == valid_color:
                    valid_color_tests += 1
                    print(f"   ✅ Valid color {valid_color}: Accepted")
                else:
                    print(f"   ❌ Valid color {valid_color}: Value mismatch")
            else:
                print(f"   ❌ Valid color {valid_color}: Should have been accepted")
        
        all_validation_passed = (validation_tests_passed == len(invalid_colors) and 
                               valid_color_tests == len(valid_colors))
        
        self.log_test("Booking Colors Hex Validation", all_validation_passed, 
                     f"- Invalid rejected: {validation_tests_passed}/{len(invalid_colors)}, Valid accepted: {valid_color_tests}/{len(valid_colors)}")
        return all_validation_passed

    def test_booking_settings_data_structure(self):
        """Test the data structure of booking settings responses"""
        success, response = self.make_request('GET', 'settings/booking', expected_status=200)
        
        if success and isinstance(response, list) and len(response) > 0:
            # Check first setting for proper structure
            first_setting = response[0]
            required_fields = ['id', 'category', 'key', 'value', 'data_type', 'description', 'updated_at']
            
            has_all_fields = all(field in first_setting for field in required_fields)
            
            if has_all_fields:
                print(f"   📋 Sample setting structure:")
                for field in required_fields:
                    print(f"      {field}: {first_setting.get(field)}")
            
            success = has_all_fields
            
        self.log_test("Booking Settings Data Structure", success, 
                     f"- All required fields present: {has_all_fields if success else 'No'}")
        return success

    def run_all_tests(self):
        """Run all booking settings tests"""
        print("🎨 Starting Booking Settings API Tests...")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 80)
        
        # Authentication
        print("\n📋 AUTHENTICATION")
        print("-" * 40)
        if not self.test_admin_login():
            print("❌ Cannot continue without authentication")
            return False
        
        # Booking Settings Tests
        print("\n🎨 BOOKING SETTINGS TESTS")
        print("-" * 40)
        self.test_booking_settings_retrieval()
        self.test_specific_booking_color_settings()
        self.test_individual_setting_retrieval()
        self.test_booking_settings_creation_verification()
        self.test_booking_settings_authentication()
        self.test_booking_settings_update_functionality()
        self.test_booking_colors_hex_validation()
        self.test_booking_settings_data_structure()
        
        # Final Summary
        print("\n" + "=" * 80)
        print(f"🏁 BOOKING SETTINGS TEST SUMMARY")
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL BOOKING SETTINGS TESTS PASSED!")
            print("✅ BookingColorsManager should be able to load settings data")
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed.")
            print("❌ BookingColorsManager may have issues loading settings data")
        
        print("=" * 80)
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = BookingSettingsAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)