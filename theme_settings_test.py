#!/usr/bin/env python3
"""
Theme Settings Investigation Test
Specifically investigating why theme dropdown is not showing up in Settings page.
"""

import requests
import json
from datetime import datetime

class ThemeSettingsInvestigator:
    def __init__(self, base_url="https://43732cd3-b12c-465b-bead-d2fab026e53c.preview.emergentagent.com"):
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
        # Try to register and login with a test user
        timestamp = datetime.now().strftime("%H%M%S")
        user_data = {
            "email": f"theme_test_{timestamp}@example.com",
            "name": f"Theme Test User {timestamp}",
            "password": "TestPassword123!",
            "role": "owner",
            "studio_name": "Theme Test Studio"
        }
        
        success, response = self.make_request('POST', 'auth/register', user_data, 200)
        
        if success:
            # Now login
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

    def test_1_check_default_settings_creation(self):
        """1. Check if theme settings are actually being created in the database"""
        print("\n🔍 INVESTIGATION 1: Default Settings Creation")
        
        success, response = self.make_request('GET', 'settings', expected_status=200)
        
        if success:
            settings_count = len(response) if isinstance(response, list) else 0
            
            # Find theme settings specifically
            theme_settings = [s for s in response if s.get('category') == 'theme']
            theme_count = len(theme_settings)
            
            print(f"   📊 Total settings found: {settings_count}")
            print(f"   🎨 Theme settings found: {theme_count}")
            
            # List all theme settings
            if theme_settings:
                print("   📋 Theme settings details:")
                for setting in theme_settings:
                    key = setting.get('key', 'Unknown')
                    value = setting.get('value', 'Unknown')
                    data_type = setting.get('data_type', 'Unknown')
                    print(f"      • {key}: {value} ({data_type})")
            else:
                print("   ⚠️  NO THEME SETTINGS FOUND!")
            
            success = theme_count > 0
            
        self.log_test("Default Settings Creation", success, f"- Found {theme_count} theme settings")
        return success

    def test_2_check_selected_theme_setting(self):
        """2. Verify that the selected_theme setting exists in the theme category"""
        print("\n🔍 INVESTIGATION 2: Selected Theme Setting")
        
        success, response = self.make_request('GET', 'settings/theme/selected_theme', expected_status=200)
        
        if success:
            key = response.get('key', 'Unknown')
            value = response.get('value', 'Unknown')
            data_type = response.get('data_type', 'Unknown')
            
            print(f"   🎯 Setting key: {key}")
            print(f"   🎨 Current value: {value}")
            print(f"   📝 Data type: {data_type}")
            
            # Check if it's the expected dropdown value
            expected_themes = ['dark', 'light', 'ocean']
            is_valid_theme = value in expected_themes
            
            if is_valid_theme:
                print(f"   ✅ Theme value '{value}' is valid (one of {expected_themes})")
            else:
                print(f"   ⚠️  Theme value '{value}' is not in expected list {expected_themes}")
            
            success = success and key == 'selected_theme' and data_type == 'string'
            
        self.log_test("Selected Theme Setting", success, f"- Value: {value}")
        return success

    def test_3_api_response_check(self):
        """3. Test GET /api/settings/theme to see what theme settings are returned"""
        print("\n🔍 INVESTIGATION 3: Theme API Response Check")
        
        success, response = self.make_request('GET', 'settings/theme', expected_status=200)
        
        if success:
            settings_count = len(response) if isinstance(response, list) else 0
            
            print(f"   📊 Theme settings returned: {settings_count}")
            
            # Check for expected theme settings
            expected_settings = {
                'selected_theme': 'dark',
                'font_size': 'medium',
                'custom_primary_color': '#a855f7',
                'custom_secondary_color': '#ec4899',
                'animations_enabled': True,
                'glassmorphism_enabled': True
            }
            
            found_settings = {}
            missing_settings = []
            
            for setting in response:
                key = setting.get('key')
                value = setting.get('value')
                if key in expected_settings:
                    found_settings[key] = value
                    print(f"   ✅ Found {key}: {value}")
            
            for expected_key in expected_settings:
                if expected_key not in found_settings:
                    missing_settings.append(expected_key)
                    print(f"   ❌ Missing {expected_key}")
            
            success = len(missing_settings) == 0
            
        self.log_test("Theme API Response Check", success, f"- Found {len(found_settings)}/6 expected settings")
        return success

    def test_4_database_query_simulation(self):
        """4. Check if settings collection has theme category entries"""
        print("\n🔍 INVESTIGATION 4: Database Query Simulation")
        
        # Get all settings and filter by theme category
        success, response = self.make_request('GET', 'settings', expected_status=200)
        
        if success:
            all_settings = response if isinstance(response, list) else []
            
            # Group by category
            categories = {}
            for setting in all_settings:
                category = setting.get('category', 'unknown')
                if category not in categories:
                    categories[category] = []
                categories[category].append(setting)
            
            print(f"   📊 Total categories found: {len(categories)}")
            print(f"   📋 Categories: {list(categories.keys())}")
            
            if 'theme' in categories:
                theme_settings = categories['theme']
                print(f"   🎨 Theme category has {len(theme_settings)} settings:")
                
                for setting in theme_settings:
                    key = setting.get('key')
                    value = setting.get('value')
                    updated_at = setting.get('updated_at', 'Unknown')
                    print(f"      • {key}: {value} (updated: {updated_at})")
                
                # Check specifically for selected_theme
                selected_theme_exists = any(s.get('key') == 'selected_theme' for s in theme_settings)
                
                if selected_theme_exists:
                    print(f"   ✅ selected_theme setting EXISTS in theme category")
                else:
                    print(f"   ❌ selected_theme setting MISSING from theme category")
                
                success = selected_theme_exists
            else:
                print(f"   ❌ Theme category NOT FOUND in database")
                success = False
            
        self.log_test("Database Query Simulation", success, f"- Theme category exists: {'theme' in categories}")
        return success

    def test_5_theme_dropdown_data_structure(self):
        """5. Verify the data structure and values for theme dropdown"""
        print("\n🔍 INVESTIGATION 5: Theme Dropdown Data Structure")
        
        success, response = self.make_request('GET', 'settings/theme/selected_theme', expected_status=200)
        
        if success:
            setting_data = response
            
            # Check all required fields for frontend dropdown
            required_fields = ['id', 'category', 'key', 'value', 'data_type']
            missing_fields = []
            
            for field in required_fields:
                if field in setting_data:
                    print(f"   ✅ {field}: {setting_data[field]}")
                else:
                    missing_fields.append(field)
                    print(f"   ❌ Missing field: {field}")
            
            # Test updating to different theme values
            theme_options = ['dark', 'light', 'ocean']
            print(f"   🔄 Testing theme options: {theme_options}")
            
            update_success_count = 0
            for theme in theme_options:
                update_data = {"value": theme}
                update_success, update_response = self.make_request('PUT', 'settings/theme/selected_theme', 
                                                                  update_data, 200)
                if update_success:
                    returned_value = update_response.get('value')
                    if returned_value == theme:
                        update_success_count += 1
                        print(f"      ✅ Successfully updated to: {theme}")
                    else:
                        print(f"      ❌ Update failed - expected {theme}, got {returned_value}")
                else:
                    print(f"      ❌ Failed to update to: {theme}")
            
            success = len(missing_fields) == 0 and update_success_count == len(theme_options)
            
        self.log_test("Theme Dropdown Data Structure", success, 
                     f"- All fields present: {len(missing_fields) == 0}, Updates working: {update_success_count}/{len(theme_options)}")
        return success

    def test_6_comprehensive_theme_settings_check(self):
        """6. Comprehensive check of all expected theme settings"""
        print("\n🔍 INVESTIGATION 6: Comprehensive Theme Settings Check")
        
        expected_theme_settings = {
            'selected_theme': {'type': 'string', 'expected_values': ['dark', 'light', 'ocean']},
            'font_size': {'type': 'string', 'expected_values': ['small', 'medium', 'large']},
            'custom_primary_color': {'type': 'string', 'pattern': '#[0-9a-fA-F]{6}'},
            'custom_secondary_color': {'type': 'string', 'pattern': '#[0-9a-fA-F]{6}'},
            'animations_enabled': {'type': 'boolean', 'expected_values': [True, False]},
            'glassmorphism_enabled': {'type': 'boolean', 'expected_values': [True, False]}
        }
        
        all_checks_passed = 0
        total_checks = len(expected_theme_settings)
        
        for setting_key, expectations in expected_theme_settings.items():
            print(f"   🔍 Checking {setting_key}...")
            
            success, response = self.make_request('GET', f'settings/theme/{setting_key}', expected_status=200)
            
            if success:
                value = response.get('value')
                data_type = response.get('data_type')
                
                # Check data type
                type_correct = data_type == expectations['type']
                
                # Check value validity
                value_valid = True
                if 'expected_values' in expectations:
                    value_valid = value in expectations['expected_values']
                elif 'pattern' in expectations and expectations['pattern'].startswith('#'):
                    # Simple hex color check
                    value_valid = isinstance(value, str) and value.startswith('#') and len(value) == 7
                
                if type_correct and value_valid:
                    all_checks_passed += 1
                    print(f"      ✅ {setting_key}: {value} ({data_type}) - VALID")
                else:
                    print(f"      ❌ {setting_key}: {value} ({data_type}) - INVALID")
                    if not type_correct:
                        print(f"         Expected type: {expectations['type']}, got: {data_type}")
                    if not value_valid:
                        print(f"         Invalid value: {value}")
            else:
                print(f"      ❌ {setting_key}: NOT FOUND")
        
        success = all_checks_passed == total_checks
        self.log_test("Comprehensive Theme Settings Check", success, 
                     f"- {all_checks_passed}/{total_checks} settings valid")
        return success

    def run_investigation(self):
        """Run the complete theme settings investigation"""
        print("🔍 THEME SETTINGS INVESTIGATION")
        print("=" * 50)
        print("Investigating why theme dropdown is not showing in Settings page")
        print()
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return
        
        # Run all investigation tests
        tests = [
            self.test_1_check_default_settings_creation,
            self.test_2_check_selected_theme_setting,
            self.test_3_api_response_check,
            self.test_4_database_query_simulation,
            self.test_5_theme_dropdown_data_structure,
            self.test_6_comprehensive_theme_settings_check
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
        
        # Summary
        print("\n" + "=" * 50)
        print("🎯 INVESTIGATION SUMMARY")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL INVESTIGATIONS PASSED - Theme settings should be working")
            print("🔍 If dropdown still not showing, issue is likely in frontend rendering")
        else:
            print("❌ SOME INVESTIGATIONS FAILED - Backend theme settings have issues")
            print("🔧 Fix the failing backend issues first")

if __name__ == "__main__":
    investigator = ThemeSettingsInvestigator()
    investigator.run_investigation()