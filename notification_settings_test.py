#!/usr/bin/env python3
"""
Focused test for notification settings boolean toggle issue
Testing email_notifications_enabled and sms_notifications_enabled settings
"""

import requests
import json
from datetime import datetime

class NotificationSettingsDebugger:
    def __init__(self, base_url="https://dance-admin-1.preview.emergentagent.com"):
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
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text, "status_code": response.status_code}

            if not success:
                print(f"   ⚠️  Status: {response.status_code}, Expected: {expected_status}")
                print(f"   📄 Response: {json.dumps(response_data, indent=2)}")

            return success, response_data

        except requests.exceptions.RequestException as e:
            print(f"   🔥 Request failed: {str(e)}")
            return False, {"error": str(e)}

    def test_admin_login(self):
        """Test login with admin credentials"""
        login_data = {
            "email": "admin@test.com",
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success:
            self.token = response.get('access_token')
            user_info = response.get('user', {})
            print(f"   👤 Admin user: {user_info.get('name', 'Unknown')} ({user_info.get('role', 'Unknown')})")
            
        self.log_test("Admin Login", success, f"- Token received: {'Yes' if self.token else 'No'}")
        return success

    def test_get_notification_settings_initial(self):
        """Get initial notification settings to see current state"""
        success, response = self.make_request('GET', 'settings/notification', 200)
        
        if success:
            print(f"   📋 Found {len(response)} notification settings:")
            for setting in response:
                key = setting.get('key', 'unknown')
                value = setting.get('value', 'unknown')
                data_type = setting.get('data_type', 'unknown')
                print(f"      • {key}: {value} ({data_type})")
                
        self.log_test("Get Initial Notification Settings", success, f"- Found {len(response) if success else 0} settings")
        return success

    def test_get_specific_email_setting(self):
        """Get the specific email_notifications_enabled setting"""
        success, response = self.make_request('GET', 'settings/notification/email_notifications_enabled', 200)
        
        if success:
            key = response.get('key', 'unknown')
            value = response.get('value', 'unknown')
            data_type = response.get('data_type', 'unknown')
            print(f"   📧 Email setting: {key} = {value} (type: {data_type}, python type: {type(value).__name__})")
                
        self.log_test("Get Email Notifications Setting", success, f"- Current value: {response.get('value') if success else 'N/A'}")
        return success

    def test_get_specific_sms_setting(self):
        """Get the specific sms_notifications_enabled setting"""
        success, response = self.make_request('GET', 'settings/notification/sms_notifications_enabled', 200)
        
        if success:
            key = response.get('key', 'unknown')
            value = response.get('value', 'unknown')
            data_type = response.get('data_type', 'unknown')
            print(f"   📱 SMS setting: {key} = {value} (type: {data_type}, python type: {type(value).__name__})")
                
        self.log_test("Get SMS Notifications Setting", success, f"- Current value: {response.get('value') if success else 'N/A'}")
        return success

    def test_turn_off_email_notifications_boolean(self):
        """Test turning OFF email notifications using boolean false"""
        update_data = {"value": False}
        
        success, response = self.make_request('PUT', 'settings/notification/email_notifications_enabled', update_data, 200)
        
        if success:
            returned_value = response.get('value')
            data_type = response.get('data_type')
            print(f"   📧 Email setting updated: value = {returned_value} (type: {data_type}, python type: {type(returned_value).__name__})")
            
            # Check if the value is actually False
            success = returned_value is False
            
        self.log_test("Turn OFF Email Notifications (boolean)", success, 
                     f"- Expected: False, Got: {response.get('value') if success else 'Failed'}")
        return success

    def test_turn_off_sms_notifications_boolean(self):
        """Test turning OFF SMS notifications using boolean false"""
        update_data = {"value": False}
        
        success, response = self.make_request('PUT', 'settings/notification/sms_notifications_enabled', update_data, 200)
        
        if success:
            returned_value = response.get('value')
            data_type = response.get('data_type')
            print(f"   📱 SMS setting updated: value = {returned_value} (type: {data_type}, python type: {type(returned_value).__name__})")
            
            # Check if the value is actually False
            success = returned_value is False
            
        self.log_test("Turn OFF SMS Notifications (boolean)", success, 
                     f"- Expected: False, Got: {response.get('value') if success else 'Failed'}")
        return success

    def test_turn_off_email_notifications_string(self):
        """Test turning OFF email notifications using string 'false'"""
        update_data = {"value": "false"}
        
        success, response = self.make_request('PUT', 'settings/notification/email_notifications_enabled', update_data, 200)
        
        if success:
            returned_value = response.get('value')
            data_type = response.get('data_type')
            print(f"   📧 Email setting updated: value = {returned_value} (type: {data_type}, python type: {type(returned_value).__name__})")
            
            # Check if the value is actually False (should be converted from string)
            success = returned_value is False
            
        self.log_test("Turn OFF Email Notifications (string 'false')", success, 
                     f"- Expected: False, Got: {response.get('value') if success else 'Failed'}")
        return success

    def test_turn_off_sms_notifications_string(self):
        """Test turning OFF SMS notifications using string 'false'"""
        update_data = {"value": "false"}
        
        success, response = self.make_request('PUT', 'settings/notification/sms_notifications_enabled', update_data, 200)
        
        if success:
            returned_value = response.get('value')
            data_type = response.get('data_type')
            print(f"   📱 SMS setting updated: value = {returned_value} (type: {data_type}, python type: {type(returned_value).__name__})")
            
            # Check if the value is actually False (should be converted from string)
            success = returned_value is False
            
        self.log_test("Turn OFF SMS Notifications (string 'false')", success, 
                     f"- Expected: False, Got: {response.get('value') if success else 'Failed'}")
        return success

    def test_verify_persistence_email(self):
        """Verify that email setting persists after being set to False"""
        success, response = self.make_request('GET', 'settings/notification/email_notifications_enabled', 200)
        
        if success:
            value = response.get('value')
            print(f"   📧 Email setting persistence check: {value} (python type: {type(value).__name__})")
            success = value is False
                
        self.log_test("Verify Email Setting Persistence", success, 
                     f"- Value after save: {response.get('value') if success else 'Failed'}")
        return success

    def test_verify_persistence_sms(self):
        """Verify that SMS setting persists after being set to False"""
        success, response = self.make_request('GET', 'settings/notification/sms_notifications_enabled', 200)
        
        if success:
            value = response.get('value')
            print(f"   📱 SMS setting persistence check: {value} (python type: {type(value).__name__})")
            success = value is False
                
        self.log_test("Verify SMS Setting Persistence", success, 
                     f"- Value after save: {response.get('value') if success else 'Failed'}")
        return success

    def test_turn_on_email_notifications(self):
        """Test turning ON email notifications to verify toggle works both ways"""
        update_data = {"value": True}
        
        success, response = self.make_request('PUT', 'settings/notification/email_notifications_enabled', update_data, 200)
        
        if success:
            returned_value = response.get('value')
            print(f"   📧 Email setting turned ON: {returned_value} (python type: {type(returned_value).__name__})")
            success = returned_value is True
            
        self.log_test("Turn ON Email Notifications", success, 
                     f"- Expected: True, Got: {response.get('value') if success else 'Failed'}")
        return success

    def test_turn_on_sms_notifications(self):
        """Test turning ON SMS notifications to verify toggle works both ways"""
        update_data = {"value": True}
        
        success, response = self.make_request('PUT', 'settings/notification/sms_notifications_enabled', update_data, 200)
        
        if success:
            returned_value = response.get('value')
            print(f"   📱 SMS setting turned ON: {returned_value} (python type: {type(returned_value).__name__})")
            success = returned_value is True
            
        self.log_test("Turn ON SMS Notifications", success, 
                     f"- Expected: True, Got: {response.get('value') if success else 'Failed'}")
        return success

    def test_database_raw_check(self):
        """Check what's actually stored in the database by getting all notification settings"""
        success, response = self.make_request('GET', 'settings/notification', 200)
        
        if success:
            print(f"   🗄️  Database raw check - All notification settings:")
            for setting in response:
                key = setting.get('key', 'unknown')
                value = setting.get('value', 'unknown')
                data_type = setting.get('data_type', 'unknown')
                updated_at = setting.get('updated_at', 'unknown')
                print(f"      • {key}: {value} ({data_type}) - Updated: {updated_at}")
                
                # Check for the specific settings we're testing
                if key in ['email_notifications_enabled', 'sms_notifications_enabled']:
                    print(f"        🔍 Python type: {type(value).__name__}")
                    print(f"        🔍 JSON representation: {json.dumps(value)}")
                
        self.log_test("Database Raw Check", success, f"- Checked {len(response) if success else 0} settings")
        return success

    def test_invalid_boolean_values(self):
        """Test various invalid boolean values to see error handling"""
        invalid_values = ["invalid", "yes", "no", 1, 0, "1", "0", "on", "off"]
        
        print(f"   🧪 Testing invalid boolean values for email_notifications_enabled:")
        
        for invalid_value in invalid_values:
            update_data = {"value": invalid_value}
            success, response = self.make_request('PUT', 'settings/notification/email_notifications_enabled', update_data)
            
            if success:
                returned_value = response.get('value')
                print(f"      • {invalid_value} ({type(invalid_value).__name__}) -> {returned_value} ({type(returned_value).__name__})")
            else:
                print(f"      • {invalid_value} ({type(invalid_value).__name__}) -> ERROR: {response.get('detail', 'Unknown error')}")
        
        self.log_test("Invalid Boolean Values Test", True, "- Tested various input types")
        return True

    def run_all_tests(self):
        """Run all notification settings tests"""
        print("🚀 Starting Notification Settings Boolean Debug Tests")
        print("=" * 60)
        
        # Authentication
        if not self.test_admin_login():
            print("❌ Cannot proceed without authentication")
            return
        
        print("\n📋 INITIAL STATE CHECK")
        print("-" * 30)
        self.test_get_notification_settings_initial()
        self.test_get_specific_email_setting()
        self.test_get_specific_sms_setting()
        
        print("\n🔄 BOOLEAN FALSE TESTS")
        print("-" * 30)
        self.test_turn_off_email_notifications_boolean()
        self.test_turn_off_sms_notifications_boolean()
        
        print("\n🔄 STRING FALSE TESTS")
        print("-" * 30)
        self.test_turn_off_email_notifications_string()
        self.test_turn_off_sms_notifications_string()
        
        print("\n💾 PERSISTENCE VERIFICATION")
        print("-" * 30)
        self.test_verify_persistence_email()
        self.test_verify_persistence_sms()
        
        print("\n🔄 BOOLEAN TRUE TESTS")
        print("-" * 30)
        self.test_turn_on_email_notifications()
        self.test_turn_on_sms_notifications()
        
        print("\n🗄️  DATABASE INSPECTION")
        print("-" * 30)
        self.test_database_raw_check()
        
        print("\n🧪 EDGE CASE TESTING")
        print("-" * 30)
        self.test_invalid_boolean_values()
        
        print("\n" + "=" * 60)
        print(f"📊 FINAL RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! Notification settings are working correctly.")
        else:
            print("⚠️  Some tests failed. There may be issues with boolean toggle functionality.")

if __name__ == "__main__":
    debugger = NotificationSettingsDebugger()
    debugger.run_all_tests()