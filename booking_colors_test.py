#!/usr/bin/env python3
"""
Booking Colors Settings Investigation Test
Testing the booking colors settings issue where color changes are not being applied.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

class BookingColorsSettingsTester:
    def __init__(self, base_url="https://rhythm-scheduler-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.original_settings = {}  # Store original settings for restoration

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
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=10)
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

    def authenticate(self, email: str = "admin@test.com", password: str = "admin123") -> bool:
        """Authenticate with the API"""
        print(f"🔐 Authenticating with {email}...")
        
        success, response = self.make_request('POST', 'auth/login', {
            'email': email,
            'password': password
        })
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"✅ Authentication successful - User ID: {self.user_id}")
            return True
        else:
            print(f"❌ Authentication failed: {response}")
            return False

    def test_settings_retrieval(self):
        """Test GET /api/settings/booking to see current booking color settings"""
        print("\n📋 TESTING SETTINGS RETRIEVAL")
        
        # Test getting all booking settings
        success, response = self.make_request('GET', 'settings/booking')
        
        if success:
            booking_settings = response if isinstance(response, list) else []
            self.log_test("GET /api/settings/booking", True, f"Retrieved {len(booking_settings)} booking settings")
            
            # Store original settings for later restoration
            for setting in booking_settings:
                self.original_settings[setting['key']] = setting['value']
            
            # Check for expected booking color settings
            expected_color_settings = [
                'private_lesson_color', 'meeting_color', 'training_color', 'party_color',
                'confirmed_color', 'pending_color', 'cancelled_color'
            ]
            
            found_settings = [setting['key'] for setting in booking_settings]
            
            for expected_setting in expected_color_settings:
                if expected_setting in found_settings:
                    setting_data = next((s for s in booking_settings if s['key'] == expected_setting), None)
                    if setting_data:
                        self.log_test(f"Booking color setting '{expected_setting}'", True, 
                                    f"Found with value: {setting_data['value']}")
                    else:
                        self.log_test(f"Booking color setting '{expected_setting}'", False, "Setting data not found")
                else:
                    self.log_test(f"Booking color setting '{expected_setting}'", False, "Setting not found")
            
            # Verify data format and structure
            for setting in booking_settings:
                required_fields = ['id', 'category', 'key', 'value', 'data_type', 'updated_at']
                missing_fields = [field for field in required_fields if field not in setting]
                
                if not missing_fields:
                    self.log_test(f"Setting structure for '{setting['key']}'", True, 
                                "All required fields present")
                else:
                    self.log_test(f"Setting structure for '{setting['key']}'", False, 
                                f"Missing fields: {missing_fields}")
                
                # Verify hex color format for color settings
                if 'color' in setting['key'] and setting['value']:
                    if isinstance(setting['value'], str) and setting['value'].startswith('#') and len(setting['value']) == 7:
                        self.log_test(f"Hex color format for '{setting['key']}'", True, 
                                    f"Valid hex color: {setting['value']}")
                    else:
                        self.log_test(f"Hex color format for '{setting['key']}'", False, 
                                    f"Invalid hex color format: {setting['value']}")
            
            return booking_settings
        else:
            self.log_test("GET /api/settings/booking", False, f"Failed to retrieve settings: {response}")
            return []

    def test_settings_update(self):
        """Test updating a booking color setting"""
        print("\n🎨 TESTING SETTINGS UPDATE")
        
        # Test updating private_lesson_color
        test_color = "#ff6b6b"  # Red color for testing
        test_key = "private_lesson_color"
        
        success, response = self.make_request('PUT', f'settings/booking/{test_key}', {
            'value': test_color,
            'updated_by': self.user_id
        })
        
        if success:
            self.log_test(f"PUT /api/settings/booking/{test_key}", True, 
                        f"Successfully updated to {test_color}")
            
            # Immediately verify the change was saved
            success_verify, verify_response = self.make_request('GET', f'settings/booking/{test_key}')
            
            if success_verify and verify_response.get('value') == test_color:
                self.log_test("Color change verification", True, 
                            f"Color successfully saved and retrieved: {verify_response['value']}")
            else:
                self.log_test("Color change verification", False, 
                            f"Color not saved correctly. Expected: {test_color}, Got: {verify_response.get('value')}")
        else:
            self.log_test(f"PUT /api/settings/booking/{test_key}", False, f"Update failed: {response}")

    def test_multiple_color_updates(self):
        """Test updating multiple booking colors in sequence"""
        print("\n🌈 TESTING MULTIPLE COLOR UPDATES")
        
        test_colors = {
            'meeting_color': '#22c55e',      # Green
            'training_color': '#f59e0b',     # Orange  
            'party_color': '#a855f7',        # Purple
            'confirmed_color': '#10b981',    # Emerald
            'pending_color': '#f59e0b',      # Amber
            'cancelled_color': '#ef4444'     # Red
        }
        
        for setting_key, color_value in test_colors.items():
            success, response = self.make_request('PUT', f'settings/booking/{setting_key}', {
                'value': color_value,
                'updated_by': self.user_id
            })
            
            if success:
                self.log_test(f"Update {setting_key}", True, f"Set to {color_value}")
                
                # Verify the change immediately
                success_verify, verify_response = self.make_request('GET', f'settings/booking/{setting_key}')
                
                if success_verify and verify_response.get('value') == color_value:
                    self.log_test(f"Verify {setting_key}", True, "Color persisted correctly")
                else:
                    self.log_test(f"Verify {setting_key}", False, 
                                f"Color not persisted. Expected: {color_value}, Got: {verify_response.get('value')}")
            else:
                self.log_test(f"Update {setting_key}", False, f"Failed: {response}")

    def test_settings_persistence(self):
        """Test that settings persist across requests"""
        print("\n💾 TESTING SETTINGS PERSISTENCE")
        
        # Set a unique test color
        test_color = "#4ecdc4"  # Teal
        test_key = "private_lesson_color"
        
        # Update the setting
        success, response = self.make_request('PUT', f'settings/booking/{test_key}', {
            'value': test_color,
            'updated_by': self.user_id
        })
        
        if success:
            # Wait a moment and retrieve again
            import time
            time.sleep(1)
            
            # Retrieve the setting multiple times to test persistence
            for i in range(3):
                success_verify, verify_response = self.make_request('GET', f'settings/booking/{test_key}')
                
                if success_verify and verify_response.get('value') == test_color:
                    self.log_test(f"Persistence test {i+1}", True, 
                                f"Color persisted: {verify_response['value']}")
                else:
                    self.log_test(f"Persistence test {i+1}", False, 
                                f"Color not persisted. Expected: {test_color}, Got: {verify_response.get('value')}")
        else:
            self.log_test("Settings persistence setup", False, f"Failed to set test color: {response}")

    def test_database_verification(self):
        """Test database verification by checking updated_at timestamps"""
        print("\n🗄️ TESTING DATABASE VERIFICATION")
        
        # Get current timestamp
        before_update = datetime.utcnow()
        
        # Update a setting
        test_color = "#96ceb4"  # Mint green
        test_key = "meeting_color"
        
        success, response = self.make_request('PUT', f'settings/booking/{test_key}', {
            'value': test_color,
            'updated_by': self.user_id
        })
        
        if success:
            # Retrieve the setting and check updated_at timestamp
            success_verify, verify_response = self.make_request('GET', f'settings/booking/{test_key}')
            
            if success_verify:
                updated_at_str = verify_response.get('updated_at')
                if updated_at_str:
                    try:
                        # Parse the timestamp (handle different formats)
                        if updated_at_str.endswith('Z'):
                            updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                        else:
                            updated_at = datetime.fromisoformat(updated_at_str)
                        
                        # Check if timestamp is recent (within last 10 seconds)
                        time_diff = abs((datetime.utcnow() - updated_at.replace(tzinfo=None)).total_seconds())
                        
                        if time_diff < 10:
                            self.log_test("Updated timestamp verification", True, 
                                        f"Timestamp updated correctly: {updated_at_str}")
                        else:
                            self.log_test("Updated timestamp verification", False, 
                                        f"Timestamp not recent enough: {updated_at_str}")
                    except Exception as e:
                        self.log_test("Updated timestamp parsing", False, f"Failed to parse timestamp: {e}")
                else:
                    self.log_test("Updated timestamp presence", False, "No updated_at field found")
            else:
                self.log_test("Database verification", False, f"Failed to retrieve updated setting: {verify_response}")
        else:
            self.log_test("Database verification setup", False, f"Failed to update setting: {response}")

    def test_hex_color_validation(self):
        """Test hex color validation"""
        print("\n🎯 TESTING HEX COLOR VALIDATION")
        
        test_key = "private_lesson_color"
        
        # Test valid hex colors
        valid_colors = ["#ffffff", "#000000", "#ff6b6b", "#4ecdc4", "#ABCDEF"]
        
        for color in valid_colors:
            success, response = self.make_request('PUT', f'settings/booking/{test_key}', {
                'value': color,
                'updated_by': self.user_id
            })
            
            if success:
                self.log_test(f"Valid hex color {color}", True, "Accepted correctly")
            else:
                self.log_test(f"Valid hex color {color}", False, f"Rejected incorrectly: {response}")
        
        # Test invalid hex colors
        invalid_colors = ["#gggggg", "#12345", "#1234567", "red", "invalid_color"]
        
        for color in invalid_colors:
            success, response = self.make_request('PUT', f'settings/booking/{test_key}', {
                'value': color,
                'updated_by': self.user_id
            }, expected_status=400)  # Expect validation error
            
            if success:  # Success means we got the expected 400 error
                self.log_test(f"Invalid hex color {color}", True, "Properly rejected")
            else:
                # Check if it was rejected with a different status code
                if isinstance(response, dict) and 'detail' in response:
                    self.log_test(f"Invalid hex color {color}", True, f"Rejected: {response['detail']}")
                else:
                    self.log_test(f"Invalid hex color {color}", False, f"Should have been rejected: {response}")

    def restore_original_settings(self):
        """Restore original settings after testing"""
        print("\n🔄 RESTORING ORIGINAL SETTINGS")
        
        for key, original_value in self.original_settings.items():
            success, response = self.make_request('PUT', f'settings/booking/{key}', {
                'value': original_value,
                'updated_by': self.user_id
            })
            
            if success:
                self.log_test(f"Restore {key}", True, f"Restored to {original_value}")
            else:
                self.log_test(f"Restore {key}", False, f"Failed to restore: {response}")

    def run_all_tests(self):
        """Run all booking colors settings tests"""
        print("🎨 BOOKING COLORS SETTINGS INVESTIGATION")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Run all test categories
        booking_settings = self.test_settings_retrieval()
        self.test_settings_update()
        self.test_multiple_color_updates()
        self.test_settings_persistence()
        self.test_database_verification()
        self.test_hex_color_validation()
        
        # Restore original settings
        if self.original_settings:
            self.restore_original_settings()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 BOOKING COLORS SETTINGS TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Booking colors settings are working correctly.")
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} test(s) failed. There may be issues with booking colors settings.")

if __name__ == "__main__":
    tester = BookingColorsSettingsTester()
    tester.run_all_tests()