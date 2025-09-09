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
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text, "status_code": response.status_code}

            if not success:
                print(f"   ❌ Status: {response.status_code}, Expected: {expected_status}")
                print(f"   📄 Response: {json.dumps(response_data, indent=2)}")

            return success, response_data

        except requests.exceptions.RequestException as e:
            print(f"   💥 Request failed: {str(e)}")
            return False, {"error": str(e)}

    def test_admin_login(self):
        """Test login with admin@test.com / admin123 credentials"""
        login_data = {
            "email": "admin@test.com",
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success:
            self.token = response.get('access_token')
            user_info = response.get('user', {})
            print(f"   👤 Admin user: {user_info.get('name', 'Unknown')} ({user_info.get('role', 'Unknown')})")
            
        self.log_test("Admin Login", success, f"- Admin token received: {'Yes' if self.token else 'No'}")
        return success

    def setup_test_data(self):
        """Create test student and teacher for recurring lessons"""
        # Create test student
        student_data = {
            "name": "Emma Rodriguez",
            "email": "emma.rodriguez@example.com",
            "phone": "+1555123456",
            "parent_name": "Maria Rodriguez",
            "parent_phone": "+1555123457",
            "parent_email": "maria.rodriguez@example.com",
            "notes": "Test student for recurring lessons"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if success:
            self.student_id = response.get('id')
            print(f"   👩‍🎓 Created test student: {response.get('name')} (ID: {self.student_id})")
        else:
            print(f"   ❌ Failed to create test student")
            return False

        # Create test teacher
        teacher_data = {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "phone": "+1234567890",
            "specialties": ["ballet", "contemporary"],
            "bio": "Experienced ballet instructor for recurring lessons testing."
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if success:
            self.teacher_id = response.get('id')
            print(f"   👩‍🏫 Created test teacher: {response.get('name')} (ID: {self.teacher_id})")
        else:
            print(f"   ❌ Failed to create test teacher")
            return False

        self.log_test("Setup Test Data", True, f"- Student: {self.student_id[:8]}..., Teacher: {self.teacher_id[:8]}...")
        return True

    def test_recurring_lessons_endpoint_basic(self):
        """Test basic recurring lessons creation with minimal data"""
        if not self.student_id or not self.teacher_id:
            self.log_test("Recurring Lessons Basic", False, "- Missing test data")
            return False

        # Test with minimal required data
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        
        recurring_data = {
            "student_id": self.student_id,
            "teacher_id": self.teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "recurrence_pattern": "weekly",
            "max_occurrences": 4
        }
        
        print(f"   📋 Testing with data: {json.dumps(recurring_data, indent=2, default=str)}")
        
        success, response = self.make_request('POST', 'recurring-lessons', recurring_data, 200)
        
        if success:
            series_id = response.get('series_id')
            lessons_created = response.get('lessons_created', 0)
            print(f"   ✅ Created series {series_id} with {lessons_created} lessons")
        else:
            print(f"   ❌ Failed to create recurring lessons")
            # Check if it's a 500 error
            if isinstance(response, dict) and response.get('status_code') == 500:
                print(f"   🚨 500 Internal Server Error detected!")
                print(f"   📄 Error details: {response}")
        
        self.log_test("Recurring Lessons Basic", success, f"- Created {response.get('lessons_created', 0)} lessons")
        return success

    def test_recurring_lessons_with_teacher_ids_array(self):
        """Test recurring lessons creation with teacher_ids array (new format)"""
        if not self.student_id or not self.teacher_id:
            self.log_test("Recurring Lessons with teacher_ids", False, "- Missing test data")
            return False

        tomorrow = datetime.now() + timedelta(days=2)
        start_time = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)
        
        # Test with teacher_ids array instead of teacher_id
        recurring_data = {
            "student_id": self.student_id,
            "teacher_ids": [self.teacher_id],  # Using array format
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "recurrence_pattern": "weekly",
            "max_occurrences": 3,
            "notes": "Testing with teacher_ids array format"
        }
        
        print(f"   📋 Testing with teacher_ids array: {json.dumps(recurring_data, indent=2, default=str)}")
        
        success, response = self.make_request('POST', 'recurring-lessons', recurring_data, 200)
        
        if success:
            series_id = response.get('series_id')
            lessons_created = response.get('lessons_created', 0)
            print(f"   ✅ Created series {series_id} with {lessons_created} lessons using teacher_ids array")
        else:
            print(f"   ❌ Failed with teacher_ids array format")
            if isinstance(response, dict) and response.get('status_code') == 500:
                print(f"   🚨 500 Internal Server Error with teacher_ids array!")
        
        self.log_test("Recurring Lessons with teacher_ids", success, f"- teacher_ids array format")
        return success

    def test_different_recurrence_patterns(self):
        """Test all recurrence patterns: weekly, bi_weekly, monthly"""
        if not self.student_id or not self.teacher_id:
            self.log_test("Different Recurrence Patterns", False, "- Missing test data")
            return False

        patterns = [
            {"pattern": "weekly", "occurrences": 4, "description": "Weekly lessons for 4 weeks"},
            {"pattern": "bi_weekly", "occurrences": 6, "description": "Bi-weekly lessons for 6 sessions"},
            {"pattern": "monthly", "occurrences": 6, "description": "Monthly lessons for 6 months"}
        ]
        
        successful_patterns = 0
        
        for i, pattern_test in enumerate(patterns):
            future_date = datetime.now() + timedelta(days=3 + i)
            start_time = future_date.replace(hour=16 + i, minute=0, second=0, microsecond=0)
            
            recurring_data = {
                "student_id": self.student_id,
                "teacher_id": self.teacher_id,
                "start_datetime": start_time.isoformat(),
                "duration_minutes": 60,
                "recurrence_pattern": pattern_test["pattern"],
                "max_occurrences": pattern_test["occurrences"],
                "notes": pattern_test["description"]
            }
            
            print(f"   🔄 Testing {pattern_test['pattern']} pattern...")
            
            success, response = self.make_request('POST', 'recurring-lessons', recurring_data, 200)
            
            if success:
                lessons_created = response.get('lessons_created', 0)
                print(f"   ✅ {pattern_test['pattern']}: Created {lessons_created} lessons")
                successful_patterns += 1
            else:
                print(f"   ❌ {pattern_test['pattern']}: Failed")
                if isinstance(response, dict) and response.get('status_code') == 500:
                    print(f"   🚨 500 Error with {pattern_test['pattern']} pattern!")
        
        success = successful_patterns == len(patterns)
        self.log_test("Different Recurrence Patterns", success, 
                     f"- {successful_patterns}/{len(patterns)} patterns working")
        return success

    def test_data_structure_validation(self):
        """Test data structure validation and error handling"""
        if not self.student_id or not self.teacher_id:
            self.log_test("Data Structure Validation", False, "- Missing test data")
            return False

        test_cases = [
            {
                "name": "Missing student_id",
                "data": {
                    "teacher_id": self.teacher_id,
                    "start_datetime": (datetime.now() + timedelta(days=1)).isoformat(),
                    "recurrence_pattern": "weekly",
                    "max_occurrences": 4
                },
                "expected_status": 422
            },
            {
                "name": "Missing teacher_id",
                "data": {
                    "student_id": self.student_id,
                    "start_datetime": (datetime.now() + timedelta(days=1)).isoformat(),
                    "recurrence_pattern": "weekly",
                    "max_occurrences": 4
                },
                "expected_status": 422
            },
            {
                "name": "Invalid recurrence_pattern",
                "data": {
                    "student_id": self.student_id,
                    "teacher_id": self.teacher_id,
                    "start_datetime": (datetime.now() + timedelta(days=1)).isoformat(),
                    "recurrence_pattern": "invalid_pattern",
                    "max_occurrences": 4
                },
                "expected_status": 422
            },
            {
                "name": "Invalid student_id",
                "data": {
                    "student_id": "nonexistent-student-id",
                    "teacher_id": self.teacher_id,
                    "start_datetime": (datetime.now() + timedelta(days=1)).isoformat(),
                    "recurrence_pattern": "weekly",
                    "max_occurrences": 4
                },
                "expected_status": 404
            }
        ]
        
        successful_validations = 0
        
        for test_case in test_cases:
            print(f"   🧪 Testing: {test_case['name']}")
            
            success, response = self.make_request('POST', 'recurring-lessons', 
                                                test_case['data'], test_case['expected_status'])
            
            if success:
                print(f"   ✅ {test_case['name']}: Correctly returned {test_case['expected_status']}")
                successful_validations += 1
            else:
                print(f"   ❌ {test_case['name']}: Unexpected response")
                if isinstance(response, dict) and response.get('status_code') == 500:
                    print(f"   🚨 500 Error during validation test!")
        
        success = successful_validations == len(test_cases)
        self.log_test("Data Structure Validation", success, 
                     f"- {successful_validations}/{len(test_cases)} validations working")
        return success

    def test_model_compatibility(self):
        """Test RecurringLessonCreate model and PrivateLesson model creation"""
        if not self.student_id or not self.teacher_id:
            self.log_test("Model Compatibility", False, "- Missing test data")
            return False

        # Test with all possible fields to check model compatibility
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=17, minute=30, second=0, microsecond=0)
        
        comprehensive_data = {
            "student_id": self.student_id,
            "teacher_id": self.teacher_id,
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 90,
            "recurrence_pattern": "weekly",
            "max_occurrences": 3,
            "notes": "Comprehensive model compatibility test with all fields",
            "enrollment_id": None  # Optional field
        }
        
        print(f"   🔍 Testing comprehensive model compatibility...")
        print(f"   📋 Data: {json.dumps(comprehensive_data, indent=2, default=str)}")
        
        success, response = self.make_request('POST', 'recurring-lessons', comprehensive_data, 200)
        
        if success:
            series_id = response.get('series_id')
            lessons_created = response.get('lessons_created', 0)
            student_name = response.get('student_name', 'Unknown')
            teacher_name = response.get('teacher_name', 'Unknown')
            
            print(f"   ✅ Model compatibility successful:")
            print(f"      📊 Series ID: {series_id}")
            print(f"      📚 Lessons created: {lessons_created}")
            print(f"      👩‍🎓 Student: {student_name}")
            print(f"      👩‍🏫 Teacher: {teacher_name}")
            
            # Verify the generated lessons have correct structure
            lessons_success, lessons_response = self.make_request('GET', 'lessons', expected_status=200)
            if lessons_success:
                recurring_lessons = [l for l in lessons_response if l.get('recurring_series_id') == series_id]
                if recurring_lessons:
                    sample_lesson = recurring_lessons[0]
                    print(f"   🔍 Sample lesson structure:")
                    print(f"      🆔 ID: {sample_lesson.get('id', 'Missing')}")
                    print(f"      👥 Teacher IDs: {sample_lesson.get('teacher_ids', 'Missing')}")
                    print(f"      📅 Start: {sample_lesson.get('start_datetime', 'Missing')}")
                    print(f"      ⏱️ End: {sample_lesson.get('end_datetime', 'Missing')}")
                    print(f"      📝 Notes: {sample_lesson.get('notes', 'Missing')}")
        else:
            print(f"   ❌ Model compatibility failed")
            if isinstance(response, dict) and response.get('status_code') == 500:
                print(f"   🚨 500 Error during model compatibility test!")
                print(f"   🔍 This suggests an issue with the RecurringLessonCreate or PrivateLesson models")
        
        self.log_test("Model Compatibility", success, f"- All model fields working")
        return success

    def diagnose_500_error(self):
        """Specific test to diagnose the 500 error"""
        print(f"\n🔍 DIAGNOSING 500 ERROR IN RECURRING LESSONS ENDPOINT")
        print(f"=" * 60)
        
        if not self.student_id or not self.teacher_id:
            print(f"❌ Cannot diagnose - missing test data")
            return False

        # Test 1: Minimal data to isolate the issue
        print(f"\n1️⃣ Testing with absolute minimal data...")
        minimal_data = {
            "student_id": self.student_id,
            "teacher_id": self.teacher_id,
            "start_datetime": "2025-01-16T14:00:00",
            "recurrence_pattern": "weekly"
        }
        
        success, response = self.make_request('POST', 'recurring-lessons', minimal_data, 200)
        if not success and isinstance(response, dict) and response.get('status_code') == 500:
            print(f"🚨 500 ERROR with minimal data - issue is fundamental")
            print(f"📄 Error response: {json.dumps(response, indent=2)}")
        elif success:
            print(f"✅ Minimal data works - issue is with specific fields")
        
        # Test 2: Check teacher_id vs teacher_ids conversion
        print(f"\n2️⃣ Testing teacher_id to teacher_ids conversion...")
        conversion_data = {
            "student_id": self.student_id,
            "teacher_id": self.teacher_id,  # Single teacher_id
            "start_datetime": "2025-01-16T15:00:00",
            "duration_minutes": 60,
            "recurrence_pattern": "weekly",
            "max_occurrences": 2
        }
        
        success, response = self.make_request('POST', 'recurring-lessons', conversion_data, 200)
        if not success and isinstance(response, dict) and response.get('status_code') == 500:
            print(f"🚨 500 ERROR with teacher_id conversion - this is likely the issue!")
            print(f"📄 Error response: {json.dumps(response, indent=2)}")
        elif success:
            print(f"✅ teacher_id conversion works")
        
        # Test 3: Check datetime parsing
        print(f"\n3️⃣ Testing datetime parsing...")
        datetime_formats = [
            "2025-01-16T16:00:00",
            "2025-01-16T16:00:00.000Z",
            "2025-01-16 16:00:00",
        ]
        
        for dt_format in datetime_formats:
            print(f"   Testing datetime format: {dt_format}")
            dt_data = {
                "student_id": self.student_id,
                "teacher_id": self.teacher_id,
                "start_datetime": dt_format,
                "recurrence_pattern": "weekly",
                "max_occurrences": 1
            }
            
            success, response = self.make_request('POST', 'recurring-lessons', dt_data, 200)
            if not success and isinstance(response, dict) and response.get('status_code') == 500:
                print(f"   🚨 500 ERROR with datetime format: {dt_format}")
            elif success:
                print(f"   ✅ Datetime format works: {dt_format}")
        
        # Test 4: Check generate_recurring_lessons function
        print(f"\n4️⃣ Testing generate_recurring_lessons function...")
        generation_data = {
            "student_id": self.student_id,
            "teacher_id": self.teacher_id,
            "start_datetime": "2025-01-16T17:00:00",
            "duration_minutes": 60,
            "recurrence_pattern": "weekly",
            "max_occurrences": 3,
            "notes": "Testing lesson generation"
        }
        
        success, response = self.make_request('POST', 'recurring-lessons', generation_data, 200)
        if not success and isinstance(response, dict) and response.get('status_code') == 500:
            print(f"🚨 500 ERROR during lesson generation - issue in generate_recurring_lessons function")
            print(f"📄 Error response: {json.dumps(response, indent=2)}")
        elif success:
            print(f"✅ Lesson generation works - created {response.get('lessons_created', 0)} lessons")
        
        print(f"\n📊 DIAGNOSIS SUMMARY:")
        print(f"=" * 40)
        print(f"If you see 500 errors above, the issue is likely in:")
        print(f"1. teacher_id to teacher_ids conversion in generate_recurring_lessons()")
        print(f"2. RecurringLessonCreate model validation")
        print(f"3. PrivateLesson model creation with teacher_ids array")
        print(f"4. Database insertion of lesson instances")
        
        return True

    def cleanup_test_data(self):
        """Clean up created test data"""
        if self.student_id:
            self.make_request('DELETE', f'students/{self.student_id}', expected_status=200)
            print(f"   🧹 Cleaned up test student: {self.student_id}")
        
        if self.teacher_id:
            self.make_request('DELETE', f'teachers/{self.teacher_id}', expected_status=200)
            print(f"   🧹 Cleaned up test teacher: {self.teacher_id}")

    def run_all_tests(self):
        """Run all recurring lessons tests"""
        print(f"🚀 STARTING RECURRING LESSONS API TESTING")
        print(f"=" * 50)
        
        # Authentication
        if not self.test_admin_login():
            print(f"❌ Cannot proceed without authentication")
            return
        
        # Setup test data
        if not self.setup_test_data():
            print(f"❌ Cannot proceed without test data")
            return
        
        # Run tests
        print(f"\n📋 RUNNING RECURRING LESSONS TESTS")
        print(f"=" * 40)
        
        self.test_recurring_lessons_endpoint_basic()
        self.test_recurring_lessons_with_teacher_ids_array()
        self.test_different_recurrence_patterns()
        self.test_data_structure_validation()
        self.test_model_compatibility()
        
        # Diagnosis
        self.diagnose_500_error()
        
        # Cleanup
        print(f"\n🧹 CLEANING UP")
        print(f"=" * 20)
        self.cleanup_test_data()
        
        # Summary
        print(f"\n📊 TEST SUMMARY")
        print(f"=" * 20)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed < self.tests_run:
            print(f"\n🚨 ISSUES FOUND - CHECK OUTPUT ABOVE FOR 500 ERRORS")
        else:
            print(f"\n✅ ALL TESTS PASSED - RECURRING LESSONS ENDPOINT WORKING")

if __name__ == "__main__":
    tester = RecurringLessonsAPITester()
    tester.run_all_tests()