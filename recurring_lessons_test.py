#!/usr/bin/env python3
"""
Focused test for recurring lessons creation endpoint to diagnose 500 error
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any

class RecurringLessonsAPITester:
    def __init__(self, base_url="https://studio-manager-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.student_id = None
        self.teacher_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_enrollment_id = None
        self.created_recurring_series_id = None

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
                print(f"   Status: {response.status_code}, Expected: {expected_status}")
                print(f"   Response: {response_data}")

            return success, response_data

        except requests.exceptions.RequestException as e:
            print(f"   Request failed: {str(e)}")
            return False, {"error": str(e)}

    def setup_test_data(self):
        """Set up test data (user, student, teacher)"""
        print("\n🔧 Setting up test data...")
        
        # Register user
        timestamp = datetime.now().strftime("%H%M%S")
        user_data = {
            "email": f"recurring_test_{timestamp}@example.com",
            "name": f"Recurring Test User {timestamp}",
            "password": "TestPassword123!",
            "role": "owner",
            "studio_name": "Test Dance Studio"
        }
        
        success, response = self.make_request('POST', 'auth/register', user_data, 200)
        if not success:
            print("❌ Failed to register user")
            return False
            
        self.user_id = response.get('id')
        self.test_email = user_data['email']
        self.test_password = user_data['password']
        
        # Login
        login_data = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        if not success:
            print("❌ Failed to login")
            return False
            
        self.token = response.get('access_token')
        
        # Create teacher
        teacher_data = {
            "name": "Recurring Test Teacher",
            "email": "recurring.teacher@example.com",
            "phone": "+1234567890",
            "specialties": ["ballet", "contemporary"],
            "bio": "Teacher for recurring lesson testing"
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            print("❌ Failed to create teacher")
            return False
            
        self.created_teacher_id = response.get('id')
        
        # Create student
        student_data = {
            "name": "Recurring Test Student",
            "email": "recurring.student@example.com",
            "phone": "+1555123456",
            "notes": "Student for recurring lesson testing"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            print("❌ Failed to create student")
            return False
            
        self.created_student_id = response.get('id')
        
        # Create enrollment
        enrollment_data = {
            "student_id": self.created_student_id,
            "program_name": "Beginner Program",
            "total_lessons": 20,
            "total_paid": 1000.0
        }
        
        success, response = self.make_request('POST', 'enrollments', enrollment_data, 200)
        if not success:
            print("❌ Failed to create enrollment")
            return False
            
        self.created_enrollment_id = response.get('id')
        
        print("✅ Test data setup completed")
        return True

    def test_get_recurring_lessons_empty(self):
        """Test GET /api/recurring-lessons returns empty array initially"""
        success, response = self.make_request('GET', 'recurring-lessons', expected_status=200)
        
        if success:
            is_list = isinstance(response, list)
            is_empty = len(response) == 0 if is_list else False
            success = is_list and is_empty
            
        self.log_test("GET Recurring Lessons (Empty)", success, 
                     f"- Response type: {type(response)}, Length: {len(response) if isinstance(response, list) else 'N/A'}")
        return success

    def test_create_recurring_lesson_weekly(self):
        """Test POST /api/recurring-lessons with weekly pattern"""
        if not self.created_student_id or not self.created_teacher_id:
            self.log_test("Create Recurring Lesson Weekly", False, "- Missing student or teacher ID")
            return False
            
        # Create weekly recurring lesson starting tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        end_date = start_time + timedelta(weeks=4)  # 4 weeks of lessons
        
        recurring_data = {
            "student_id": self.created_student_id,
            "teacher_id": self.created_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "recurrence_pattern": "weekly",
            "end_date": end_date.isoformat(),
            "notes": "Weekly ballet lesson series",
            "enrollment_id": self.created_enrollment_id
        }
        
        success, response = self.make_request('POST', 'recurring-lessons', recurring_data, 200)
        
        lessons_created = 0
        if success:
            self.created_recurring_series_id = response.get('series_id')
            lessons_created = response.get('lessons_created', 0)
            student_name = response.get('student_name', 'Unknown')
            teacher_name = response.get('teacher_name', 'Unknown')
            
        self.log_test("Create Recurring Lesson Weekly", success, 
                     f"- Series ID: {self.created_recurring_series_id}, Lessons: {lessons_created}, Student: {student_name}, Teacher: {teacher_name}")
        return success

    def test_create_recurring_lesson_monthly(self):
        """Test POST /api/recurring-lessons with monthly pattern"""
        if not self.created_student_id or not self.created_teacher_id:
            self.log_test("Create Recurring Lesson Monthly", False, "- Missing student or teacher ID")
            return False
            
        # Create monthly recurring lesson
        next_week = datetime.now() + timedelta(days=7)
        start_time = next_week.replace(hour=14, minute=0, second=0, microsecond=0)
        
        recurring_data = {
            "student_id": self.created_student_id,
            "teacher_id": self.created_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 90,
            "recurrence_pattern": "monthly",
            "max_occurrences": 3,
            "notes": "Monthly advanced technique lesson"
        }
        
        success, response = self.make_request('POST', 'recurring-lessons', recurring_data, 200)
        
        lessons_created = 0
        if success:
            lessons_created = response.get('lessons_created', 0)
            
        self.log_test("Create Recurring Lesson Monthly", success, f"- Lessons created: {lessons_created}")
        return success

    def test_create_recurring_lesson_bi_weekly(self):
        """Test POST /api/recurring-lessons with bi-weekly pattern"""
        if not self.created_student_id or not self.created_teacher_id:
            self.log_test("Create Recurring Lesson Bi-weekly", False, "- Missing student or teacher ID")
            return False
            
        # Create bi-weekly recurring lesson
        next_week = datetime.now() + timedelta(days=7)
        start_time = next_week.replace(hour=16, minute=30, second=0, microsecond=0)
        
        recurring_data = {
            "student_id": self.created_student_id,
            "teacher_id": self.created_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 75,
            "recurrence_pattern": "bi_weekly",
            "max_occurrences": 5,
            "notes": "Bi-weekly contemporary dance lesson"
        }
        
        success, response = self.make_request('POST', 'recurring-lessons', recurring_data, 200)
        
        lessons_created = 0
        if success:
            lessons_created = response.get('lessons_created', 0)
            
        self.log_test("Create Recurring Lesson Bi-weekly", success, f"- Lessons created: {lessons_created}")
        return success

    def test_get_recurring_lessons_with_data(self):
        """Test GET /api/recurring-lessons returns created series"""
        success, response = self.make_request('GET', 'recurring-lessons', expected_status=200)
        
        series_count = 0
        if success:
            series_count = len(response) if isinstance(response, list) else 0
            
            # Check if our created series is in the list
            found_series = False
            if isinstance(response, list) and self.created_recurring_series_id:
                for series in response:
                    if series.get('id') == self.created_recurring_series_id:
                        found_series = True
                        break
                        
            success = success and series_count > 0 and found_series
            
        self.log_test("GET Recurring Lessons (With Data)", success, 
                     f"- Found {series_count} series, Contains created series: {found_series if 'found_series' in locals() else 'N/A'}")
        return success

    def test_cancel_recurring_lesson_series(self):
        """Test DELETE /api/recurring-lessons/{series_id}"""
        if not self.created_recurring_series_id:
            self.log_test("Cancel Recurring Lesson Series", False, "- No recurring series ID available")
            return False
            
        success, response = self.make_request('DELETE', f'recurring-lessons/{self.created_recurring_series_id}', expected_status=200)
        
        cancelled_lessons = 0
        if success:
            cancelled_lessons = response.get('cancelled_lessons_count', 0)
            message = response.get('message', '')
            
        self.log_test("Cancel Recurring Lesson Series", success, 
                     f"- Message: {message if 'message' in locals() else 'N/A'}, Cancelled lessons: {cancelled_lessons}")
        return success

    def test_authentication_required(self):
        """Test that recurring lesson endpoints require authentication"""
        # Save current token
        original_token = self.token
        
        # Remove token
        self.token = None
        
        # Test GET without auth
        success_get, response_get = self.make_request('GET', 'recurring-lessons', expected_status=403)
        
        # Test POST without auth
        recurring_data = {
            "student_id": "test",
            "teacher_id": "test",
            "start_datetime": datetime.now().isoformat(),
            "duration_minutes": 60,
            "recurrence_pattern": "weekly"
        }
        success_post, response_post = self.make_request('POST', 'recurring-lessons', recurring_data, 403)
        
        # Restore token
        self.token = original_token
        
        success = success_get and success_post
        self.log_test("Authentication Required", success, 
                     f"- GET returns 403: {success_get}, POST returns 403: {success_post}")
        return success

    def test_invalid_recurrence_pattern(self):
        """Test creating recurring lesson with invalid pattern"""
        if not self.created_student_id or not self.created_teacher_id:
            self.log_test("Invalid Recurrence Pattern", False, "- Missing student or teacher ID")
            return False
            
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        recurring_data = {
            "student_id": self.created_student_id,
            "teacher_id": self.created_teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "recurrence_pattern": "invalid_pattern",
            "max_occurrences": 3
        }
        
        success, response = self.make_request('POST', 'recurring-lessons', recurring_data, 422)
        
        self.log_test("Invalid Recurrence Pattern", success, "- Expected 422 validation error")
        return success

    def test_cancel_nonexistent_series(self):
        """Test cancelling a non-existent recurring series"""
        fake_series_id = "nonexistent-series-id"
        success, response = self.make_request('DELETE', f'recurring-lessons/{fake_series_id}', expected_status=404)
        
        self.log_test("Cancel Nonexistent Series", success, "- Expected 404 error")
        return success

    def test_verify_lessons_created_in_database(self):
        """Test that individual lesson instances are created in the database"""
        # Get all lessons to see if recurring lessons were created
        success, response = self.make_request('GET', 'lessons', expected_status=200)
        
        recurring_lessons_count = 0
        if success and isinstance(response, list):
            # Count lessons that have recurring_series_id
            for lesson in response:
                if lesson.get('recurring_series_id'):
                    recurring_lessons_count += 1
                    
        success = success and recurring_lessons_count > 0
        self.log_test("Verify Lessons Created in Database", success, 
                     f"- Found {recurring_lessons_count} recurring lesson instances")
        return success

    def run_all_tests(self):
        """Run all recurring lesson tests"""
        print("🚀 Starting Recurring Lessons API Testing...")
        print(f"🔗 Testing against: {self.base_url}")
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Aborting tests.")
            return 1
        
        print("\n📋 Running Recurring Lessons Tests...")
        
        # Test sequence
        test_methods = [
            self.test_get_recurring_lessons_empty,
            self.test_create_recurring_lesson_weekly,
            self.test_create_recurring_lesson_monthly,
            self.test_create_recurring_lesson_bi_weekly,
            self.test_get_recurring_lessons_with_data,
            self.test_verify_lessons_created_in_database,
            self.test_cancel_recurring_lesson_series,
            self.test_authentication_required,
            self.test_invalid_recurrence_pattern,
            self.test_cancel_nonexistent_series
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ {test_method.__name__} - EXCEPTION: {str(e)}")
                self.tests_run += 1
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "   Success Rate: 0%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All recurring lesson tests passed!")
            return 0
        else:
            print("⚠️  Some recurring lesson tests failed.")
            return 1

def main():
    tester = RecurringLessonsAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    import sys
    sys.exit(main())