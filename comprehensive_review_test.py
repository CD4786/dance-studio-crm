#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any

class ComprehensiveReviewTester:
    def __init__(self, base_url="https://dance-studio-crm.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_teacher_id = None
        self.created_student_id = None
        self.created_lesson_id = None
        self.created_user_id = None

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

    def setup_authentication(self):
        """Setup authentication for testing"""
        print("\n🔐 AUTHENTICATION SETUP")
        print("-" * 50)
        
        # Register a test user
        timestamp = datetime.now().strftime("%H%M%S")
        user_data = {
            "email": f"test_owner_{timestamp}@example.com",
            "name": f"Test Owner {timestamp}",
            "password": "TestPassword123!",
            "role": "owner",
            "studio_name": "Test Dance Studio"
        }
        
        success, response = self.make_request('POST', 'auth/register', user_data, 200)
        if not success:
            self.log_test("User Registration", False, "- Failed to register test user")
            return False
            
        self.user_id = response.get('id')
        self.test_email = user_data['email']
        self.test_password = user_data['password']
        self.log_test("User Registration", True, f"- User ID: {self.user_id}")
        
        # Login
        login_data = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        if not success:
            self.log_test("User Login", False, "- Failed to login")
            return False
            
        self.token = response.get('access_token')
        self.log_test("User Login", True, f"- Token received: {'Yes' if self.token else 'No'}")
        
        return True

    def test_enhanced_settings_system(self):
        """Test Enhanced Settings System (46 Settings Across 9 Categories)"""
        print("\n📋 ENHANCED SETTINGS SYSTEM (46 Settings Across 9 Categories)")
        print("-" * 70)
        
        # Test getting all settings
        success, response = self.make_request('GET', 'settings', expected_status=200)
        
        if success:
            settings_count = len(response) if isinstance(response, list) else 0
            
            # Check for all expected categories
            categories = set()
            for setting in response:
                categories.add(setting.get('category', ''))
            
            expected_categories = {'business', 'system', 'theme', 'booking', 'calendar', 'display', 'business_rules', 'program', 'notification'}
            has_all_categories = expected_categories.issubset(categories)
            
            # Verify we have at least 46 settings
            success = success and settings_count >= 46 and has_all_categories
            
        self.log_test("Enhanced Settings System Creation", success, 
                     f"- Found {settings_count} settings across {len(categories)} categories")
        
        # Test CRUD operations for settings
        if success:
            # Test category-based retrieval
            success, theme_settings = self.make_request('GET', 'settings/theme', expected_status=200)
            self.log_test("Settings Category Retrieval", success, 
                         f"- Theme category has {len(theme_settings) if success else 0} settings")
            
            # Test individual setting retrieval
            success, individual_setting = self.make_request('GET', 'settings/theme/selected_theme', expected_status=200)
            self.log_test("Individual Setting Retrieval", success, 
                         f"- Retrieved theme setting: {individual_setting.get('value') if success else 'Failed'}")
            
            # Test setting update
            update_data = {"value": "royal"}
            success, update_response = self.make_request('PUT', 'settings/theme/selected_theme', update_data, 200)
            self.log_test("Setting Update", success, 
                         f"- Updated theme to: {update_response.get('value') if success else 'Failed'}")

    def test_theme_customization_system(self):
        """Test Theme Customization System"""
        print("\n🎨 THEME CUSTOMIZATION SYSTEM")
        print("-" * 50)
        
        theme_tests = [
            {"key": "selected_theme", "value": "ocean", "description": "Theme selection"},
            {"key": "font_size", "value": "large", "description": "Font size control"},
            {"key": "custom_primary_color", "value": "#ff6b6b", "description": "Custom color with hex validation"},
            {"key": "animations_enabled", "value": False, "description": "UI preference toggle"},
            {"key": "glassmorphism_enabled", "value": True, "description": "Glassmorphism toggle"}
        ]
        
        successful_tests = 0
        
        for test_case in theme_tests:
            update_data = {"value": test_case["value"]}
            success, response = self.make_request('PUT', f'settings/theme/{test_case["key"]}', update_data, 200)
            
            if success:
                returned_value = response.get('value')
                if returned_value == test_case["value"]:
                    successful_tests += 1
                    
            self.log_test(f"Theme {test_case['description']}", success, 
                         f"- {test_case['key']}: {test_case['value']}")
        
        overall_success = successful_tests == len(theme_tests)
        self.log_test("Theme Customization System", overall_success, 
                     f"- {successful_tests}/{len(theme_tests)} theme settings working")

    def test_booking_color_management(self):
        """Test Booking Color Management"""
        print("\n📅 BOOKING COLOR MANAGEMENT")
        print("-" * 50)
        
        booking_color_tests = [
            {"key": "private_lesson_color", "value": "#3b82f6", "description": "Private lesson color"},
            {"key": "meeting_color", "value": "#22c55e", "description": "Meeting color"},
            {"key": "training_color", "value": "#f59e0b", "description": "Training color"},
            {"key": "party_color", "value": "#a855f7", "description": "Party color"},
            {"key": "confirmed_status_color", "value": "#22c55e", "description": "Confirmed status color"},
            {"key": "pending_status_color", "value": "#f59e0b", "description": "Pending status color"},
            {"key": "cancelled_status_color", "value": "#ef4444", "description": "Cancelled status color"},
            {"key": "teacher_color_coding_enabled", "value": True, "description": "Teacher color coding toggle"}
        ]
        
        successful_tests = 0
        
        for test_case in booking_color_tests:
            update_data = {"value": test_case["value"]}
            success, response = self.make_request('PUT', f'settings/booking/{test_case["key"]}', update_data, 200)
            
            if success:
                returned_value = response.get('value')
                if returned_value == test_case["value"]:
                    successful_tests += 1
                    
            self.log_test(f"Booking {test_case['description']}", success, 
                         f"- {test_case['key']}: {test_case['value']}")
        
        overall_success = successful_tests == len(booking_color_tests)
        self.log_test("Booking Color Management", overall_success, 
                     f"- {successful_tests}/{len(booking_color_tests)} booking color settings working")

    def test_teacher_color_management_api(self):
        """Test Teacher Color Management API"""
        print("\n👨‍🏫 TEACHER COLOR MANAGEMENT API")
        print("-" * 50)
        
        # First create a teacher for testing
        teacher_data = {
            "name": "Test Teacher",
            "email": "test.teacher@example.com",
            "phone": "+1234567890",
            "specialties": ["ballet", "jazz"],
            "bio": "Test teacher for color management"
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            self.log_test("Teacher Color Management API", False, "- Failed to create test teacher")
            return
            
        self.created_teacher_id = response.get('id')
        
        # Test GET /api/teachers/{id}/color
        success, response = self.make_request('GET', f'teachers/{self.created_teacher_id}/color', expected_status=200)
        self.log_test("GET Teacher Color", success, 
                     f"- Teacher color: {response.get('color') if success else 'Failed'}")
        
        # Test PUT /api/teachers/{id}/color with valid hex colors
        valid_colors = ["#ff6b6b", "#4ecdc4", "#45b7d1"]
        successful_updates = 0
        
        for color in valid_colors:
            color_data = {"color": color}
            success, response = self.make_request('PUT', f'teachers/{self.created_teacher_id}/color', color_data, 200)
            if success:
                successful_updates += 1
                
        self.log_test("PUT Teacher Color (Valid)", successful_updates == len(valid_colors), 
                     f"- {successful_updates}/{len(valid_colors)} valid colors updated")
        
        # Test color validation with invalid hex codes
        invalid_colors = ["invalid_color", "#gggggg", "#12345"]
        validation_passed = 0
        
        for color in invalid_colors:
            color_data = {"color": color}
            success, response = self.make_request('PUT', f'teachers/{self.created_teacher_id}/color', color_data, 400)
            if success:
                validation_passed += 1
                
        self.log_test("PUT Teacher Color (Invalid)", validation_passed == len(invalid_colors), 
                     f"- {validation_passed}/{len(invalid_colors)} invalid colors correctly rejected")
        
        # Test POST /api/teachers/colors/auto-assign
        success, response = self.make_request('POST', 'teachers/colors/auto-assign', expected_status=200)
        assignments_count = len(response.get('assignments', [])) if success else 0
        self.log_test("POST Auto-assign Colors", success, 
                     f"- Assigned colors to {assignments_count} teachers")

    def test_user_management_system(self):
        """Test User Management System"""
        print("\n👥 USER MANAGEMENT SYSTEM")
        print("-" * 50)
        
        # Test user listing with role-based access (owners/managers only)
        success, response = self.make_request('GET', 'users', expected_status=200)
        users_count = len(response) if success and isinstance(response, list) else 0
        self.log_test("User Listing (Owner Access)", success, f"- Found {users_count} users")
        
        # Test user creation with proper authentication
        timestamp = datetime.now().strftime("%H%M%S%f")[:12]
        new_user_data = {
            "email": f"new_user_{timestamp}@example.com",
            "name": f"New User {timestamp}",
            "password": "NewUserPass123!",
            "role": "teacher"
        }
        
        success, response = self.make_request('POST', 'users', new_user_data, 200)
        if success:
            self.created_user_id = response.get('id')
            
        self.log_test("User Creation", success, f"- Created user: {new_user_data['email']}")
        
        # Test user updates (profile, role, status changes)
        if self.created_user_id:
            update_data = {
                "name": "Updated User Name",
                "role": "manager",
                "is_active": True
            }
            
            success, response = self.make_request('PUT', f'users/{self.created_user_id}', update_data, 200)
            self.log_test("User Profile Update", success, 
                         f"- Updated user role to: {response.get('role') if success else 'Failed'}")
            
            # Test password management
            password_data = {
                "new_password": "UpdatedPassword123!"
            }
            
            success, response = self.make_request('PUT', f'users/{self.created_user_id}/password', password_data, 200)
            self.log_test("Password Management", success, 
                         f"- Password update: {'Success' if success else 'Failed'}")
            
            # Test user deletion with proper safeguards (should prevent self-deletion)
            success, response = self.make_request('DELETE', f'users/{self.user_id}', expected_status=400)
            self.log_test("Self-deletion Prevention", success, "- Self-deletion correctly prevented")
            
            # Test deleting the created user (should work)
            success, response = self.make_request('DELETE', f'users/{self.created_user_id}', expected_status=200)
            self.log_test("User Deletion", success, "- User deletion successful")

    def test_lesson_time_edit_functionality(self):
        """Test Enhanced Lesson Time Edit Functionality"""
        print("\n⏰ LESSON TIME EDIT FUNCTIONALITY")
        print("-" * 50)
        
        # First create a student and teacher for testing
        student_data = {
            "name": "Test Student",
            "email": "test.student@example.com",
            "phone": "+1234567890"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            self.log_test("Lesson Time Edit", False, "- Failed to create test student")
            return
            
        self.created_student_id = response.get('id')
        
        # Create lesson with enhanced datetime handling
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.created_student_id,
            "teacher_ids": [self.created_teacher_id],
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "booking_type": "private_lesson",
            "notes": "Test lesson for time editing"
        }
        
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        if not success:
            self.log_test("Lesson Creation", False, "- Failed to create test lesson")
            return
            
        self.created_lesson_id = response.get('id')
        original_end_time = response.get('end_datetime')
        self.log_test("Lesson Creation", True, f"- Created lesson at {start_time.strftime('%H:%M')}")
        
        # Test lesson updates with date/time changes
        new_start_time = start_time.replace(hour=16, minute=30)  # Change to 4:30 PM
        update_data = {
            "start_datetime": new_start_time.isoformat(),
            "duration_minutes": 90,  # Change duration too
            "notes": "Updated lesson with new time and duration"
        }
        
        success, response = self.make_request('PUT', f'lessons/{self.created_lesson_id}', update_data, 200)
        if success:
            updated_start = response.get('start_datetime')
            updated_end = response.get('end_datetime')
            
            # Verify automatic end_datetime recalculation
            if updated_start and updated_end:
                start_dt = datetime.fromisoformat(updated_start.replace('Z', ''))
                end_dt = datetime.fromisoformat(updated_end.replace('Z', ''))
                duration_minutes = (end_dt - start_dt).seconds // 60
                
                duration_correct = duration_minutes == 90
                self.log_test("Automatic End Time Recalculation", duration_correct, 
                             f"- Duration: {duration_minutes} minutes (expected 90)")
            
        self.log_test("Lesson Time Update", success, 
                     f"- Updated to {new_start_time.strftime('%H:%M')} with 90min duration")
        
        # Test integration with multiple instructors and booking types
        if self.created_teacher_id:
            multi_instructor_update = {
                "teacher_ids": [self.created_teacher_id],
                "booking_type": "training",
                "start_datetime": start_time.replace(hour=18).isoformat()
            }
            
            success, response = self.make_request('PUT', f'lessons/{self.created_lesson_id}', multi_instructor_update, 200)
            self.log_test("Multi-instructor & Booking Type Update", success, 
                         f"- Updated to training at 18:00")

    def test_business_rules_engine(self):
        """Test Business Rules Engine"""
        print("\n💼 BUSINESS RULES ENGINE")
        print("-" * 50)
        
        business_rules_tests = [
            {"key": "cancellation_policy_hours", "value": 24, "type": "integer", "description": "Cancellation policy"},
            {"key": "max_advance_booking_days", "value": 90, "type": "integer", "description": "Advance booking limit"},
            {"key": "require_payment_before_booking", "value": True, "type": "boolean", "description": "Payment requirement"},
            {"key": "late_cancellation_fee", "value": 25.50, "type": "float", "description": "Late cancellation fee"},
            {"key": "auto_confirm_bookings", "value": False, "type": "boolean", "description": "Auto-confirmation"}
        ]
        
        successful_tests = 0
        
        for test_case in business_rules_tests:
            update_data = {"value": test_case["value"]}
            success, response = self.make_request('PUT', f'settings/business_rules/{test_case["key"]}', update_data, 200)
            
            if success:
                returned_value = response.get('value')
                data_type = response.get('data_type')
                
                # Verify data type and value
                if returned_value == test_case["value"] and data_type == test_case["type"]:
                    successful_tests += 1
                    
            self.log_test(f"Business Rule: {test_case['description']}", success, 
                         f"- {test_case['key']}: {test_case['value']} ({test_case['type']})")
        
        overall_success = successful_tests == len(business_rules_tests)
        self.log_test("Business Rules Engine", overall_success, 
                     f"- {successful_tests}/{len(business_rules_tests)} business rules working")

    def test_display_calendar_settings(self):
        """Test Display & Calendar Settings"""
        print("\n📊 DISPLAY & CALENDAR SETTINGS")
        print("-" * 50)
        
        display_calendar_tests = [
            {"category": "display", "key": "language", "value": "es", "description": "Language selection"},
            {"category": "display", "key": "currency_symbol", "value": "€", "description": "Currency settings"},
            {"category": "calendar", "key": "start_hour", "value": 9, "description": "Calendar working hours start"},
            {"category": "calendar", "key": "end_hour", "value": 21, "description": "Calendar working hours end"},
            {"category": "calendar", "key": "time_slot_minutes", "value": 60, "description": "Time slot duration"},
            {"category": "calendar", "key": "weekend_enabled", "value": True, "description": "Weekend toggle"},
            {"category": "calendar", "key": "instructor_stats_enabled", "value": True, "description": "Statistics toggle"}
        ]
        
        successful_tests = 0
        
        for test_case in display_calendar_tests:
            update_data = {"value": test_case["value"]}
            success, response = self.make_request('PUT', f'settings/{test_case["category"]}/{test_case["key"]}', update_data, 200)
            
            if success:
                returned_value = response.get('value')
                if returned_value == test_case["value"]:
                    successful_tests += 1
                    
            self.log_test(f"Display/Calendar: {test_case['description']}", success, 
                         f"- {test_case['key']}: {test_case['value']}")
        
        overall_success = successful_tests == len(display_calendar_tests)
        self.log_test("Display & Calendar Settings", overall_success, 
                     f"- {successful_tests}/{len(display_calendar_tests)} settings working")

    def run_comprehensive_review_tests(self):
        """Run all comprehensive review tests"""
        print("🎯 COMPREHENSIVE DANCE STUDIO CRM REVIEW TESTING")
        print("=" * 80)
        print("Testing Areas:")
        print("• Enhanced Settings System (46 Settings Across 9 Categories)")
        print("• Theme Customization System")
        print("• Booking Color Management")
        print("• Teacher Color Management API")
        print("• User Management System")
        print("• Lesson Time Edit Functionality")
        print("• Business Rules Engine")
        print("• Display & Calendar Settings")
        print("=" * 80)
        
        # Setup authentication
        if not self.setup_authentication():
            return 1
        
        # Run all test categories
        self.test_enhanced_settings_system()
        self.test_theme_customization_system()
        self.test_booking_color_management()
        self.test_teacher_color_management_api()
        self.test_user_management_system()
        self.test_lesson_time_edit_functionality()
        self.test_business_rules_engine()
        self.test_display_calendar_settings()
        
        # Final Results
        print("\n" + "=" * 80)
        print(f"📊 COMPREHENSIVE REVIEW TEST RESULTS")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print("=" * 80)
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL COMPREHENSIVE REVIEW TESTS PASSED!")
            return 0
        else:
            print("❌ Some tests failed - see details above")
            return 1

def main():
    tester = ComprehensiveReviewTester()
    
    try:
        result = tester.run_comprehensive_review_tests()
        return result
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Testing failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())