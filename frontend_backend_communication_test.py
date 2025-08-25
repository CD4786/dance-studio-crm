#!/usr/bin/env python3
"""
Frontend-Backend Communication Test for Boolean Settings
Test what values the frontend is actually sending and how the backend handles them.
"""

import requests
import json
import sys
from datetime import datetime

class FrontendBackendCommunicationTester:
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

            return success, response_data

        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def authenticate(self):
        """Authenticate with admin credentials"""
        login_data = {
            "email": "admin@test.com",
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success:
            self.token = response.get('access_token')
            
        self.log_test("Admin Authentication", success)
        return success

    def test_string_boolean_conversion_issue(self):
        """Test the specific issue where frontend sends strings instead of booleans"""
        print("\n🔍 TESTING STRING BOOLEAN CONVERSION ISSUE")
        print("=" * 60)
        
        test_setting = {'category': 'notification', 'key': 'email_notifications_enabled'}
        
        # Test 1: Frontend sends string "false" (common issue)
        print("\n1. Testing frontend sending string 'false':")
        update_data = {"value": "false"}  # String instead of boolean
        success, response = self.make_request('PUT', f"settings/{test_setting['category']}/{test_setting['key']}", update_data, 200)
        
        if success:
            returned_value = response.get('value')
            print(f"   Input: 'false' (string)")
            print(f"   Returned: {returned_value} ({type(returned_value).__name__})")
            print(f"   Issue: String 'false' is truthy in Python, so it becomes True!")
            
            # Verify by getting the setting again
            success2, response2 = self.make_request('GET', f"settings/{test_setting['category']}/{test_setting['key']}", expected_status=200)
            if success2:
                stored_value = response2.get('value')
                print(f"   Stored value: {stored_value} ({type(stored_value).__name__})")
                
                # This is the bug! String "false" gets stored as "false" (string) which is truthy
                if isinstance(stored_value, str) and stored_value == "false":
                    print("   🐛 BUG FOUND: String 'false' stored as string, not converted to boolean False")
                    return False
        
        # Test 2: Frontend sends string "true"
        print("\n2. Testing frontend sending string 'true':")
        update_data = {"value": "true"}  # String instead of boolean
        success, response = self.make_request('PUT', f"settings/{test_setting['category']}/{test_setting['key']}", update_data, 200)
        
        if success:
            returned_value = response.get('value')
            print(f"   Input: 'true' (string)")
            print(f"   Returned: {returned_value} ({type(returned_value).__name__})")
            
            # Verify by getting the setting again
            success2, response2 = self.make_request('GET', f"settings/{test_setting['category']}/{test_setting['key']}", expected_status=200)
            if success2:
                stored_value = response2.get('value')
                print(f"   Stored value: {stored_value} ({type(stored_value).__name__})")
        
        # Test 3: Correct boolean values
        print("\n3. Testing correct boolean False:")
        update_data = {"value": False}  # Correct boolean
        success, response = self.make_request('PUT', f"settings/{test_setting['category']}/{test_setting['key']}", update_data, 200)
        
        if success:
            returned_value = response.get('value')
            print(f"   Input: False (boolean)")
            print(f"   Returned: {returned_value} ({type(returned_value).__name__})")
            
            # Verify by getting the setting again
            success2, response2 = self.make_request('GET', f"settings/{test_setting['category']}/{test_setting['key']}", expected_status=200)
            if success2:
                stored_value = response2.get('value')
                print(f"   Stored value: {stored_value} ({type(stored_value).__name__})")
        
        return True

    def test_checkbox_toggle_simulation(self):
        """Simulate what happens when a checkbox is toggled in the frontend"""
        print("\n🔍 SIMULATING CHECKBOX TOGGLE BEHAVIOR")
        print("=" * 60)
        
        test_setting = {'category': 'theme', 'key': 'animations_enabled'}
        
        # Get current value
        success, response = self.make_request('GET', f"settings/{test_setting['category']}/{test_setting['key']}", expected_status=200)
        if not success:
            print("❌ Could not get current setting value")
            return False
            
        current_value = response.get('value')
        print(f"Current value: {current_value} ({type(current_value).__name__})")
        
        # Simulate different ways frontend might send the toggle
        test_cases = [
            {
                'name': 'JavaScript boolean false',
                'value': False,
                'expected_type': bool
            },
            {
                'name': 'JavaScript string "false"',
                'value': "false",
                'expected_type': str,
                'is_problematic': True
            },
            {
                'name': 'JavaScript number 0',
                'value': 0,
                'expected_type': int,
                'is_problematic': True
            },
            {
                'name': 'JavaScript boolean true',
                'value': True,
                'expected_type': bool
            },
            {
                'name': 'JavaScript string "true"',
                'value': "true",
                'expected_type': str,
                'is_problematic': True
            },
            {
                'name': 'JavaScript number 1',
                'value': 1,
                'expected_type': int,
                'is_problematic': True
            }
        ]
        
        issues_found = []
        
        for test_case in test_cases:
            print(f"\n📤 Testing: {test_case['name']}")
            print(f"   Sending value: {test_case['value']} ({type(test_case['value']).__name__})")
            
            update_data = {"value": test_case['value']}
            success, response = self.make_request('PUT', f"settings/{test_setting['category']}/{test_setting['key']}", update_data, 200)
            
            if success:
                returned_value = response.get('value')
                returned_type = type(returned_value).__name__
                
                print(f"   📥 Backend returned: {returned_value} ({returned_type})")
                
                # Check if this is problematic
                if test_case.get('is_problematic'):
                    if isinstance(returned_value, str):
                        # String values are problematic for boolean settings
                        if returned_value in ["true", "false"]:
                            issues_found.append({
                                'test': test_case['name'],
                                'issue': f'String "{returned_value}" stored instead of boolean',
                                'input': test_case['value'],
                                'output': returned_value
                            })
                            print(f"   🐛 ISSUE: String '{returned_value}' stored instead of boolean")
                    elif isinstance(returned_value, int):
                        # Integer values are also problematic
                        issues_found.append({
                            'test': test_case['name'],
                            'issue': f'Integer {returned_value} stored instead of boolean',
                            'input': test_case['value'],
                            'output': returned_value
                        })
                        print(f"   🐛 ISSUE: Integer {returned_value} stored instead of boolean")
                else:
                    if isinstance(returned_value, bool):
                        print(f"   ✅ Correct: Boolean value handled properly")
                    else:
                        print(f"   ⚠️  Unexpected: Expected boolean but got {returned_type}")
        
        print(f"\n📊 Issues found: {len(issues_found)}")
        for issue in issues_found:
            print(f"   - {issue['test']}: {issue['issue']}")
        
        return len(issues_found) == 0

    def test_data_type_validation(self):
        """Test if the backend validates data types for boolean settings"""
        print("\n🔍 TESTING DATA TYPE VALIDATION")
        print("=" * 60)
        
        test_setting = {'category': 'notification', 'key': 'sms_notifications_enabled'}
        
        # Test invalid data types for boolean settings
        invalid_values = [
            {"value": "invalid_string", "description": "Random string"},
            {"value": 123, "description": "Random integer"},
            {"value": 45.67, "description": "Float number"},
            {"value": [], "description": "Empty array"},
            {"value": {}, "description": "Empty object"},
            {"value": None, "description": "Null value"}
        ]
        
        validation_working = True
        
        for test_case in invalid_values:
            print(f"\n📤 Testing invalid value: {test_case['value']} ({test_case['description']})")
            
            update_data = {"value": test_case['value']}
            success, response = self.make_request('PUT', f"settings/{test_setting['category']}/{test_setting['key']}", update_data, 200)
            
            if success:
                returned_value = response.get('value')
                print(f"   📥 Backend accepted: {returned_value} ({type(returned_value).__name__})")
                
                # Check if the backend should have rejected this
                if not isinstance(returned_value, bool):
                    print(f"   ⚠️  Backend should validate boolean settings but accepted {type(returned_value).__name__}")
                    validation_working = False
            else:
                print(f"   ❌ Request failed: {response}")
        
        return validation_working

    def run_communication_tests(self):
        """Run all communication tests"""
        print("🔍 FRONTEND-BACKEND BOOLEAN COMMUNICATION TESTING")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Test 1: String boolean conversion issue
        success1 = self.test_string_boolean_conversion_issue()
        self.log_test("String Boolean Conversion", success1)
        
        # Test 2: Checkbox toggle simulation
        success2 = self.test_checkbox_toggle_simulation()
        self.log_test("Checkbox Toggle Simulation", success2)
        
        # Test 3: Data type validation
        success3 = self.test_data_type_validation()
        self.log_test("Data Type Validation", success3)
        
        # Summary
        print("\n" + "=" * 60)
        print("🔍 COMMUNICATION TEST SUMMARY")
        print("=" * 60)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Conclusions
        print("\n🎯 CONCLUSIONS:")
        if self.tests_passed == self.tests_run:
            print("✅ All communication tests passed - no issues found")
        else:
            print("❌ Issues found in frontend-backend communication")
            print("   The problem is likely in how the frontend sends boolean values")
            print("   or how the backend handles type conversion for boolean settings")
        
        return self.tests_passed, self.tests_run

if __name__ == "__main__":
    tester = FrontendBackendCommunicationTester()
    passed, total = tester.run_communication_tests()
    
    if passed == total:
        print("\n🎉 All communication tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} communication tests failed")
        sys.exit(1)