#!/usr/bin/env python3
"""
Settings API Debug Test - Focus on Boolean Toggle Issues
Debug the settings API to identify why boolean toggle settings are not saving properly.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Union

class SettingsAPIDebugger:
    def __init__(self, base_url="https://studio-manager-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.debug_info = []

    def log_debug(self, message: str, data: Any = None):
        """Log debug information"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        debug_entry = f"[{timestamp}] {message}"
        if data:
            debug_entry += f"\n  Data: {json.dumps(data, indent=2, default=str)}"
        self.debug_info.append(debug_entry)
        print(debug_entry)

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
                response_data = {"raw_response": response.text, "status_code": response.status_code}

            if not success:
                self.log_debug(f"Request failed: {method} {endpoint}", {
                    "expected_status": expected_status,
                    "actual_status": response.status_code,
                    "response": response_data
                })

            return success, response_data

        except requests.exceptions.RequestException as e:
            self.log_debug(f"Request exception: {method} {endpoint}", {"error": str(e)})
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
            user_info = response.get('user', {})
            self.log_debug("Authentication successful", {
                "user": user_info.get('name'),
                "role": user_info.get('role'),
                "token_received": bool(self.token)
            })
        else:
            self.log_debug("Authentication failed", response)
            
        self.log_test("Admin Authentication", success)
        return success

    def test_settings_data_structure(self):
        """Test 1: Settings API Data Structure Test - GET /api/settings"""
        self.log_debug("=== TEST 1: Settings API Data Structure ===")
        
        success, response = self.make_request('GET', 'settings', expected_status=200)
        
        if success:
            settings_count = len(response) if isinstance(response, list) else 0
            
            # Analyze data structure
            categories = {}
            boolean_settings = []
            data_types = {}
            
            for setting in response:
                category = setting.get('category', 'unknown')
                key = setting.get('key', 'unknown')
                value = setting.get('value')
                data_type = setting.get('data_type', 'unknown')
                
                if category not in categories:
                    categories[category] = []
                categories[category].append(key)
                
                if data_type not in data_types:
                    data_types[data_type] = 0
                data_types[data_type] += 1
                
                if data_type == 'boolean':
                    boolean_settings.append({
                        'category': category,
                        'key': key,
                        'value': value,
                        'value_type': type(value).__name__
                    })
            
            self.log_debug("Settings data structure analysis", {
                "total_settings": settings_count,
                "categories": {k: len(v) for k, v in categories.items()},
                "data_types": data_types,
                "boolean_settings_count": len(boolean_settings)
            })
            
            # Focus on boolean settings
            self.log_debug("Boolean settings detailed analysis", boolean_settings)
            
        self.log_test("Settings Data Structure", success, f"- Found {settings_count} settings")
        return success, response if success else []

    def test_boolean_settings_current_values(self, all_settings):
        """Test 2: Check current boolean values in database"""
        self.log_debug("=== TEST 2: Boolean Settings Current Values ===")
        
        boolean_settings = [s for s in all_settings if s.get('data_type') == 'boolean']
        
        notification_booleans = []
        theme_booleans = []
        other_booleans = []
        
        for setting in boolean_settings:
            category = setting.get('category')
            key = setting.get('key')
            value = setting.get('value')
            
            setting_info = {
                'category': category,
                'key': key,
                'value': value,
                'value_type': type(value).__name__,
                'is_true_boolean': isinstance(value, bool),
                'string_representation': str(value)
            }
            
            if category == 'notification':
                notification_booleans.append(setting_info)
            elif category == 'theme':
                theme_booleans.append(setting_info)
            else:
                other_booleans.append(setting_info)
        
        self.log_debug("Notification boolean settings", notification_booleans)
        self.log_debug("Theme boolean settings", theme_booleans)
        self.log_debug("Other boolean settings", other_booleans)
        
        # Check for specific settings mentioned in the review
        target_settings = [
            'email_notifications_enabled',
            'sms_notifications_enabled', 
            'animations_enabled'
        ]
        
        found_targets = []
        for setting in boolean_settings:
            if setting.get('key') in target_settings:
                found_targets.append({
                    'category': setting.get('category'),
                    'key': setting.get('key'),
                    'value': setting.get('value'),
                    'data_type_stored': type(setting.get('value')).__name__
                })
        
        self.log_debug("Target boolean settings found", found_targets)
        
        success = len(boolean_settings) > 0
        self.log_test("Boolean Settings Current Values", success, f"- Found {len(boolean_settings)} boolean settings")
        return success, boolean_settings

    def test_boolean_settings_update_false(self):
        """Test 3: Boolean Settings Update Test - Set to false"""
        self.log_debug("=== TEST 3: Boolean Settings Update to False ===")
        
        # Test specific settings mentioned in the review
        test_cases = [
            {'category': 'notification', 'key': 'email_notifications_enabled', 'value': False},
            {'category': 'notification', 'key': 'sms_notifications_enabled', 'value': False},
            {'category': 'theme', 'key': 'animations_enabled', 'value': False}
        ]
        
        results = []
        successful_updates = 0
        
        for test_case in test_cases:
            self.log_debug(f"Testing update: {test_case['category']}/{test_case['key']} = {test_case['value']}")
            
            # First, get current value
            success, current_response = self.make_request('GET', f"settings/{test_case['category']}/{test_case['key']}", expected_status=200)
            current_value = current_response.get('value') if success else 'unknown'
            
            # Update the setting
            update_data = {"value": test_case['value']}
            success, response = self.make_request('PUT', f"settings/{test_case['category']}/{test_case['key']}", update_data, 200)
            
            if success:
                returned_value = response.get('value')
                updated_at = response.get('updated_at')
                
                result = {
                    'setting': f"{test_case['category']}/{test_case['key']}",
                    'requested_value': test_case['value'],
                    'current_value_before': current_value,
                    'returned_value': returned_value,
                    'returned_type': type(returned_value).__name__,
                    'update_successful': returned_value == test_case['value'],
                    'updated_at': updated_at
                }
                
                if result['update_successful']:
                    successful_updates += 1
                    
            else:
                result = {
                    'setting': f"{test_case['category']}/{test_case['key']}",
                    'requested_value': test_case['value'],
                    'current_value_before': current_value,
                    'error': response,
                    'update_successful': False
                }
            
            results.append(result)
            self.log_debug(f"Update result for {test_case['category']}/{test_case['key']}", result)
        
        success = successful_updates == len(test_cases)
        self.log_test("Boolean Settings Update to False", success, f"- {successful_updates}/{len(test_cases)} updates successful")
        return success, results

    def test_boolean_settings_persistence(self, update_results):
        """Test 4: Settings Save Response and Persistence Test"""
        self.log_debug("=== TEST 4: Boolean Settings Persistence Test ===")
        
        persistence_results = []
        successful_retrievals = 0
        
        for result in update_results:
            if not result.get('update_successful'):
                continue
                
            setting_path = result['setting']
            expected_value = result['requested_value']
            
            # Wait a moment and retrieve the setting again
            success, response = self.make_request('GET', f"settings/{setting_path}", expected_status=200)
            
            if success:
                retrieved_value = response.get('value')
                persistence_result = {
                    'setting': setting_path,
                    'expected_value': expected_value,
                    'retrieved_value': retrieved_value,
                    'retrieved_type': type(retrieved_value).__name__,
                    'persistence_successful': retrieved_value == expected_value,
                    'full_response': response
                }
                
                if persistence_result['persistence_successful']:
                    successful_retrievals += 1
                    
            else:
                persistence_result = {
                    'setting': setting_path,
                    'expected_value': expected_value,
                    'error': response,
                    'persistence_successful': False
                }
            
            persistence_results.append(persistence_result)
            self.log_debug(f"Persistence test for {setting_path}", persistence_result)
        
        success = successful_retrievals == len([r for r in update_results if r.get('update_successful')])
        self.log_test("Boolean Settings Persistence", success, f"- {successful_retrievals} settings persisted correctly")
        return success, persistence_results

    def test_boolean_toggle_transitions(self):
        """Test 5: Test both true→false and false→true transitions"""
        self.log_debug("=== TEST 5: Boolean Toggle Transitions ===")
        
        # Use a test setting for toggle testing
        test_setting = {'category': 'theme', 'key': 'animations_enabled'}
        
        # Get current value
        success, current_response = self.make_request('GET', f"settings/{test_setting['category']}/{test_setting['key']}", expected_status=200)
        if not success:
            self.log_test("Boolean Toggle Transitions", False, "- Could not get current value")
            return False, []
        
        current_value = current_response.get('value')
        self.log_debug(f"Current value for {test_setting['category']}/{test_setting['key']}", {
            'value': current_value,
            'type': type(current_value).__name__
        })
        
        transitions = []
        
        # Test transition 1: current → opposite
        opposite_value = not current_value if isinstance(current_value, bool) else (False if current_value else True)
        
        update_data = {"value": opposite_value}
        success, response = self.make_request('PUT', f"settings/{test_setting['category']}/{test_setting['key']}", update_data, 200)
        
        transition_1 = {
            'from': current_value,
            'to': opposite_value,
            'success': success,
            'returned_value': response.get('value') if success else None,
            'correct_transition': response.get('value') == opposite_value if success else False
        }
        transitions.append(transition_1)
        self.log_debug("Transition 1 (current → opposite)", transition_1)
        
        # Test transition 2: opposite → back to original
        if transition_1['success']:
            update_data = {"value": current_value}
            success, response = self.make_request('PUT', f"settings/{test_setting['category']}/{test_setting['key']}", update_data, 200)
            
            transition_2 = {
                'from': opposite_value,
                'to': current_value,
                'success': success,
                'returned_value': response.get('value') if success else None,
                'correct_transition': response.get('value') == current_value if success else False
            }
            transitions.append(transition_2)
            self.log_debug("Transition 2 (opposite → original)", transition_2)
        
        successful_transitions = sum(1 for t in transitions if t.get('correct_transition'))
        success = successful_transitions == len(transitions)
        
        self.log_test("Boolean Toggle Transitions", success, f"- {successful_transitions}/{len(transitions)} transitions successful")
        return success, transitions

    def test_database_storage_investigation(self):
        """Test 6: Database Storage Investigation"""
        self.log_debug("=== TEST 6: Database Storage Investigation ===")
        
        # Get all settings and analyze storage patterns
        success, response = self.make_request('GET', 'settings', expected_status=200)
        
        if not success:
            self.log_test("Database Storage Investigation", False, "- Could not retrieve settings")
            return False, {}
        
        storage_analysis = {
            'boolean_values_analysis': {},
            'data_type_consistency': {},
            'potential_issues': []
        }
        
        boolean_settings = [s for s in response if s.get('data_type') == 'boolean']
        
        for setting in boolean_settings:
            value = setting.get('value')
            value_type = type(value).__name__
            
            key = f"{setting.get('category')}/{setting.get('key')}"
            storage_analysis['boolean_values_analysis'][key] = {
                'stored_value': value,
                'stored_type': value_type,
                'is_python_bool': isinstance(value, bool),
                'string_representation': str(value)
            }
            
            # Check for potential issues
            if not isinstance(value, bool):
                storage_analysis['potential_issues'].append({
                    'setting': key,
                    'issue': f'Boolean setting stored as {value_type} instead of bool',
                    'value': value
                })
            
            if value_type not in storage_analysis['data_type_consistency']:
                storage_analysis['data_type_consistency'][value_type] = 0
            storage_analysis['data_type_consistency'][value_type] += 1
        
        self.log_debug("Database storage analysis", storage_analysis)
        
        # Check for specific problematic patterns
        issues_found = len(storage_analysis['potential_issues'])
        success = issues_found == 0
        
        self.log_test("Database Storage Investigation", success, f"- {issues_found} storage issues found")
        return success, storage_analysis

    def test_frontend_backend_communication(self):
        """Test 7: Frontend-Backend Communication Test"""
        self.log_debug("=== TEST 7: Frontend-Backend Communication Test ===")
        
        # Test different data formats that frontend might send
        test_cases = [
            {'value': True, 'description': 'Python boolean True'},
            {'value': False, 'description': 'Python boolean False'},
            {'value': 'true', 'description': 'String "true"'},
            {'value': 'false', 'description': 'String "false"'},
            {'value': 1, 'description': 'Integer 1'},
            {'value': 0, 'description': 'Integer 0'},
        ]
        
        test_setting = {'category': 'theme', 'key': 'glassmorphism_enabled'}
        communication_results = []
        
        for test_case in test_cases:
            self.log_debug(f"Testing frontend communication with {test_case['description']}: {test_case['value']}")
            
            update_data = {"value": test_case['value']}
            success, response = self.make_request('PUT', f"settings/{test_setting['category']}/{test_setting['key']}", update_data, 200)
            
            result = {
                'input_value': test_case['value'],
                'input_type': type(test_case['value']).__name__,
                'description': test_case['description'],
                'request_successful': success,
                'returned_value': response.get('value') if success else None,
                'returned_type': type(response.get('value')).__name__ if success and response.get('value') is not None else None,
                'conversion_correct': None
            }
            
            if success:
                # Check if conversion was handled correctly
                returned_val = response.get('value')
                if test_case['value'] in [True, 'true', 1]:
                    result['conversion_correct'] = returned_val is True
                elif test_case['value'] in [False, 'false', 0]:
                    result['conversion_correct'] = returned_val is False
            
            communication_results.append(result)
            self.log_debug(f"Communication test result", result)
        
        successful_conversions = sum(1 for r in communication_results if r.get('conversion_correct'))
        success = successful_conversions > 0  # At least some conversions should work
        
        self.log_test("Frontend-Backend Communication", success, f"- {successful_conversions}/{len(test_cases)} conversions handled correctly")
        return success, communication_results

    def run_comprehensive_debug(self):
        """Run all debug tests"""
        print("🔍 SETTINGS API BOOLEAN TOGGLE DEBUG TESTING")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Test 1: Settings API Data Structure
        success, all_settings = self.test_settings_data_structure()
        if not success:
            print("❌ Cannot proceed without settings data")
            return
        
        # Test 2: Boolean Settings Current Values
        success, boolean_settings = self.test_boolean_settings_current_values(all_settings)
        
        # Test 3: Boolean Settings Update Test
        success, update_results = self.test_boolean_settings_update_false()
        
        # Test 4: Settings Persistence Test
        if update_results:
            success, persistence_results = self.test_boolean_settings_persistence(update_results)
        
        # Test 5: Boolean Toggle Transitions
        success, transition_results = self.test_boolean_toggle_transitions()
        
        # Test 6: Database Storage Investigation
        success, storage_analysis = self.test_database_storage_investigation()
        
        # Test 7: Frontend-Backend Communication
        success, communication_results = self.test_frontend_backend_communication()
        
        # Summary
        print("\n" + "=" * 60)
        print("🔍 DEBUG SUMMARY")
        print("=" * 60)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Key findings
        print("\n🔑 KEY FINDINGS:")
        
        # Check for critical issues
        critical_issues = []
        
        if hasattr(self, 'storage_analysis') and self.storage_analysis.get('potential_issues'):
            critical_issues.extend(self.storage_analysis['potential_issues'])
        
        if critical_issues:
            print("❌ CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"   - {issue}")
        else:
            print("✅ No critical storage issues detected")
        
        print(f"\n📊 Debug information collected: {len(self.debug_info)} entries")
        
        return self.tests_passed, self.tests_run

if __name__ == "__main__":
    debugger = SettingsAPIDebugger()
    passed, total = debugger.run_comprehensive_debug()
    
    if passed == total:
        print("\n🎉 All debug tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} debug tests failed")
        sys.exit(1)