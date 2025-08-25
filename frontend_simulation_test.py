#!/usr/bin/env python3
"""
Frontend simulation test for notification settings
Simulating exactly what the frontend might be doing
"""

import requests
import json
from datetime import datetime

class FrontendSimulationTester:
    def __init__(self, base_url="https://dance-studio-crm.preview.emergentagent.com"):
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

    def simulate_frontend_load_settings(self):
        """Simulate frontend loading all settings"""
        print("🌐 SIMULATING: Frontend loads settings page")
        
        # Frontend typically loads all settings at once
        success, response = self.make_request('GET', 'settings', 200)
        
        if success:
            notification_settings = [s for s in response if s.get('category') == 'notification']
            print(f"   📋 Frontend receives {len(notification_settings)} notification settings:")
            
            for setting in notification_settings:
                key = setting.get('key', 'unknown')
                value = setting.get('value', 'unknown')
                print(f"      • {key}: {value} ({type(value).__name__})")
                
        self.log_test("Frontend Load Settings", success, f"- Loaded {len(response) if success else 0} total settings")
        return success, response if success else []

    def simulate_user_unchecks_email_toggle(self):
        """Simulate user unchecking the email notifications toggle"""
        print("🌐 SIMULATING: User unchecks email notifications toggle")
        
        # Frontend sends the unchecked state (false)
        update_data = {"value": False}
        
        success, response = self.make_request('PUT', 'settings/notification/email_notifications_enabled', update_data, 200)
        
        if success:
            returned_value = response.get('value')
            print(f"   📧 Frontend receives response: {returned_value} ({type(returned_value).__name__})")
            
            # Check if the response is what frontend expects
            success = returned_value is False
            
        self.log_test("User Unchecks Email Toggle", success, 
                     f"- Expected: False, Got: {response.get('value') if success else 'Failed'}")
        return success

    def simulate_user_unchecks_sms_toggle(self):
        """Simulate user unchecking the SMS notifications toggle"""
        print("🌐 SIMULATING: User unchecks SMS notifications toggle")
        
        # Frontend sends the unchecked state (false)
        update_data = {"value": False}
        
        success, response = self.make_request('PUT', 'settings/notification/sms_notifications_enabled', update_data, 200)
        
        if success:
            returned_value = response.get('value')
            print(f"   📱 Frontend receives response: {returned_value} ({type(returned_value).__name__})")
            
            # Check if the response is what frontend expects
            success = returned_value is False
            
        self.log_test("User Unchecks SMS Toggle", success, 
                     f"- Expected: False, Got: {response.get('value') if success else 'Failed'}")
        return success

    def simulate_frontend_refresh_after_save(self):
        """Simulate frontend refreshing/reloading settings after save"""
        print("🌐 SIMULATING: Frontend refreshes settings after save")
        
        # Frontend reloads settings to verify changes
        success, response = self.make_request('GET', 'settings/notification', 200)
        
        if success:
            email_setting = next((s for s in response if s.get('key') == 'email_notifications_enabled'), None)
            sms_setting = next((s for s in response if s.get('key') == 'sms_notifications_enabled'), None)
            
            print(f"   📧 Email setting after refresh: {email_setting.get('value') if email_setting else 'NOT FOUND'}")
            print(f"   📱 SMS setting after refresh: {sms_setting.get('value') if sms_setting else 'NOT FOUND'}")
            
            # Check if both settings are still False
            email_correct = email_setting and email_setting.get('value') is False
            sms_correct = sms_setting and sms_setting.get('value') is False
            
            success = email_correct and sms_correct
            
        self.log_test("Frontend Refresh After Save", success, 
                     f"- Email: {email_setting.get('value') if email_setting else 'N/A'}, SMS: {sms_setting.get('value') if sms_setting else 'N/A'}")
        return success

    def simulate_page_reload_scenario(self):
        """Simulate complete page reload scenario"""
        print("🌐 SIMULATING: Complete page reload (new browser session)")
        
        # Clear token to simulate new session
        old_token = self.token
        self.token = None
        
        # Re-authenticate
        login_success = self.test_admin_login()
        if not login_success:
            self.token = old_token
            return False
        
        # Load settings fresh
        success, response = self.make_request('GET', 'settings/notification', 200)
        
        if success:
            email_setting = next((s for s in response if s.get('key') == 'email_notifications_enabled'), None)
            sms_setting = next((s for s in response if s.get('key') == 'sms_notifications_enabled'), None)
            
            print(f"   📧 Email setting after page reload: {email_setting.get('value') if email_setting else 'NOT FOUND'}")
            print(f"   📱 SMS setting after page reload: {sms_setting.get('value') if sms_setting else 'NOT FOUND'}")
            
            # Check if settings reverted back to True (this would be the bug)
            email_value = email_setting.get('value') if email_setting else None
            sms_value = sms_setting.get('value') if sms_setting else None
            
            if email_value is True or sms_value is True:
                print("   🚨 BUG DETECTED: Settings reverted back to True after page reload!")
                success = False
            else:
                print("   ✅ Settings maintained False values after page reload")
                success = True
            
        self.log_test("Page Reload Scenario", success, 
                     f"- Email: {email_setting.get('value') if email_setting else 'N/A'}, SMS: {sms_setting.get('value') if sms_setting else 'N/A'}")
        return success

    def test_multiple_rapid_toggles(self):
        """Test rapid toggling like a user might do"""
        print("🌐 SIMULATING: Rapid toggle scenario")
        
        toggle_sequence = [False, True, False, True, False]
        
        for i, value in enumerate(toggle_sequence):
            print(f"   🔄 Toggle {i+1}: Setting to {value}")
            
            # Update email setting
            update_data = {"value": value}
            success, response = self.make_request('PUT', 'settings/notification/email_notifications_enabled', update_data, 200)
            
            if success:
                returned_value = response.get('value')
                print(f"      📧 Response: {returned_value} ({type(returned_value).__name__})")
                
                if returned_value != value:
                    print(f"      🚨 MISMATCH: Expected {value}, got {returned_value}")
                    self.log_test(f"Rapid Toggle {i+1}", False, f"- Value mismatch")
                    return False
            else:
                print(f"      🚨 FAILED: Toggle {i+1} failed")
                self.log_test(f"Rapid Toggle {i+1}", False, f"- Request failed")
                return False
        
        self.log_test("Multiple Rapid Toggles", True, f"- All {len(toggle_sequence)} toggles successful")
        return True

    def test_concurrent_settings_update(self):
        """Test updating multiple notification settings at once"""
        print("🌐 SIMULATING: Concurrent settings update (Save All scenario)")
        
        # Simulate frontend sending multiple updates quickly
        import threading
        import time
        
        results = []
        
        def update_email():
            success, response = self.make_request('PUT', 'settings/notification/email_notifications_enabled', {"value": False}, 200)
            results.append(('email', success, response.get('value') if success else None))
        
        def update_sms():
            success, response = self.make_request('PUT', 'settings/notification/sms_notifications_enabled', {"value": False}, 200)
            results.append(('sms', success, response.get('value') if success else None))
        
        def update_booking():
            success, response = self.make_request('PUT', 'settings/notification/booking_confirmation_email', {"value": False}, 200)
            results.append(('booking', success, response.get('value') if success else None))
        
        # Start all updates concurrently
        threads = [
            threading.Thread(target=update_email),
            threading.Thread(target=update_sms),
            threading.Thread(target=update_booking)
        ]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Check results
        all_successful = all(result[1] for result in results)
        all_false = all(result[2] is False for result in results if result[1])
        
        print(f"   📊 Concurrent update results:")
        for setting, success, value in results:
            print(f"      • {setting}: {'✅' if success else '❌'} -> {value}")
        
        success = all_successful and all_false
        self.log_test("Concurrent Settings Update", success, 
                     f"- {len([r for r in results if r[1]])}/{len(results)} updates successful")
        return success

    def run_all_tests(self):
        """Run all frontend simulation tests"""
        print("🚀 Starting Frontend Simulation Tests for Notification Settings")
        print("=" * 70)
        
        # Authentication
        if not self.test_admin_login():
            print("❌ Cannot proceed without authentication")
            return
        
        print("\n🌐 FRONTEND SIMULATION SCENARIOS")
        print("-" * 40)
        
        # Simulate typical frontend workflow
        self.simulate_frontend_load_settings()
        self.simulate_user_unchecks_email_toggle()
        self.simulate_user_unchecks_sms_toggle()
        self.simulate_frontend_refresh_after_save()
        self.simulate_page_reload_scenario()
        
        print("\n🔄 EDGE CASE SCENARIOS")
        print("-" * 40)
        self.test_multiple_rapid_toggles()
        self.test_concurrent_settings_update()
        
        print("\n" + "=" * 70)
        print(f"📊 FINAL RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All frontend simulation tests passed!")
            print("   The notification settings API is working correctly.")
            print("   If users are experiencing toggle issues, the problem may be in:")
            print("   • Frontend JavaScript logic")
            print("   • Browser caching")
            print("   • Network connectivity")
            print("   • Frontend state management")
        else:
            print("⚠️  Some tests failed. Issues detected in notification settings API.")

if __name__ == "__main__":
    tester = FrontendSimulationTester()
    tester.run_all_tests()