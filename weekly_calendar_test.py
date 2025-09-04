import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any

class WeeklyCalendarAPITester:
    def __init__(self, base_url="https://studio-manager-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_student_id = None
        self.created_teacher_id = None
        self.created_lesson_id = None
        self.created_enrollment_id = None

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

    def test_create_test_data(self):
        """Create test student, teacher, and enrollment for lesson testing"""
        # Create test student
        student_data = {
            "name": "Alice Johnson",
            "email": "alice.johnson@example.com",
            "phone": "+1555123456",
            "parent_name": "Bob Johnson",
            "parent_phone": "+1555123457",
            "parent_email": "bob.johnson@example.com",
            "notes": "Test student for weekly calendar testing"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            self.log_test("Create Test Student", False, "- Failed to create test student")
            return False
            
        self.created_student_id = response.get('id')
        print(f"   ✅ Created test student: {student_data['name']} (ID: {self.created_student_id})")

        # Create test teacher
        teacher_data = {
            "name": "Maria Rodriguez",
            "email": "maria.rodriguez@example.com",
            "phone": "+1555987654",
            "specialties": ["ballet", "contemporary"],
            "bio": "Professional ballet instructor for weekly calendar testing"
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            self.log_test("Create Test Teacher", False, "- Failed to create test teacher")
            return False
            
        self.created_teacher_id = response.get('id')
        print(f"   ✅ Created test teacher: {teacher_data['name']} (ID: {self.created_teacher_id})")

        # Create test enrollment
        enrollment_data = {
            "student_id": self.created_student_id,
            "program_name": "Weekly Calendar Test Program",
            "total_lessons": 10,
            "price_per_lesson": 50.0,
            "initial_payment": 200.0,
            "total_paid": 200.0
        }
        
        success, response = self.make_request('POST', 'enrollments', enrollment_data, 200)
        if not success:
            self.log_test("Create Test Enrollment", False, "- Failed to create test enrollment")
            return False
            
        self.created_enrollment_id = response.get('id')
        print(f"   ✅ Created test enrollment: {enrollment_data['program_name']} (ID: {self.created_enrollment_id})")

        self.log_test("Create Test Data", True, f"- Student, Teacher, and Enrollment created successfully")
        return True

    def test_lesson_fetching_api(self):
        """Test GET /api/lessons endpoint for weekly calendar"""
        success, response = self.make_request('GET', 'lessons', expected_status=200)
        
        if not success:
            self.log_test("Lesson Fetching API", False, "- Failed to fetch lessons")
            return False
            
        lessons_count = len(response) if isinstance(response, list) else 0
        
        # Verify response structure for weekly calendar
        if lessons_count > 0:
            lesson = response[0]
            required_fields = ['id', 'student_id', 'student_name', 'teacher_names', 'start_datetime', 'is_attended', 'status']
            missing_fields = [field for field in required_fields if field not in lesson]
            
            if missing_fields:
                self.log_test("Lesson Fetching API", False, f"- Missing required fields: {missing_fields}")
                return False
                
            # Verify data types
            if not isinstance(lesson.get('teacher_names'), list):
                self.log_test("Lesson Fetching API", False, "- teacher_names should be a list")
                return False
                
            print(f"   ✅ Lesson structure verified with all required fields")
            print(f"   📋 Sample lesson: {lesson.get('student_name')} with {', '.join(lesson.get('teacher_names', []))}")
        
        self.log_test("Lesson Fetching API", True, f"- Found {lessons_count} lessons with proper structure")
        return True

    def test_create_lesson_for_attendance(self):
        """Create a lesson for attendance testing"""
        if not self.created_student_id or not self.created_teacher_id:
            self.log_test("Create Lesson for Attendance", False, "- Missing test data")
            return False
            
        # Create lesson for today
        today = datetime.now()
        start_time = today.replace(hour=14, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.created_student_id,
            "teacher_ids": [self.created_teacher_id],
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "booking_type": "private_lesson",
            "notes": "Test lesson for weekly calendar attendance",
            "enrollment_id": self.created_enrollment_id
        }
        
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        
        if success:
            self.created_lesson_id = response.get('id')
            student_name = response.get('student_name')
            teacher_names = response.get('teacher_names', [])
            
        self.log_test("Create Lesson for Attendance", success, 
                     f"- Lesson ID: {self.created_lesson_id}, Student: {student_name}, Teachers: {teacher_names}")
        return success

    def test_lesson_attendance_api(self):
        """Test POST /api/lessons/{lesson_id}/attend endpoint"""
        if not self.created_lesson_id:
            self.log_test("Lesson Attendance API", False, "- No lesson ID available")
            return False
            
        success, response = self.make_request('POST', f'lessons/{self.created_lesson_id}/attend', expected_status=200)
        
        if success:
            message = response.get('message', '')
            lesson_id = response.get('lesson_id', '')
            credits_deducted = response.get('credits_deducted', False)
            
            print(f"   ✅ Attendance marked successfully")
            print(f"   📝 Message: {message}")
            print(f"   💳 Credits deducted: {credits_deducted}")
            
        self.log_test("Lesson Attendance API", success, f"- Attendance marking: {'Success' if success else 'Failed'}")
        return success

    def test_lesson_credits_check_api(self):
        """Test GET /api/students/{student_id}/lesson-credits endpoint"""
        if not self.created_student_id:
            self.log_test("Lesson Credits Check API", False, "- No student ID available")
            return False
            
        success, response = self.make_request('GET', f'students/{self.created_student_id}/lesson-credits', expected_status=200)
        
        if success:
            total_credits = response.get('total_lessons_available', 0)
            enrollments = response.get('enrollments', [])
            student_id = response.get('student_id', '')
            
            print(f"   ✅ Credits check successful")
            print(f"   💎 Total available credits: {total_credits}")
            print(f"   📊 Enrollments: {len(enrollments)} enrollments")
            print(f"   👤 Student ID: {student_id}")
            
            # Verify response structure
            required_fields = ['student_id', 'total_lessons_available', 'enrollments']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                self.log_test("Lesson Credits Check API", False, f"- Missing fields: {missing_fields}")
                return False
                
            # Verify enrollment structure if any enrollments exist
            if enrollments:
                enrollment = enrollments[0]
                enrollment_fields = ['id', 'program_name', 'total_lessons', 'lessons_taken', 'lessons_available']
                enrollment_missing = [field for field in enrollment_fields if field not in enrollment]
                if enrollment_missing:
                    self.log_test("Lesson Credits Check API", False, f"- Missing enrollment fields: {enrollment_missing}")
                    return False
                    
        self.log_test("Lesson Credits Check API", success, f"- Credits: {total_credits}, Enrollments: {len(enrollments)}")
        return success

    def test_lesson_deletion_api(self):
        """Test DELETE /api/lessons/{lesson_id} endpoint"""
        if not self.created_lesson_id:
            self.log_test("Lesson Deletion API", False, "- No lesson ID available")
            return False
            
        success, response = self.make_request('DELETE', f'lessons/{self.created_lesson_id}', expected_status=200)
        
        if success:
            message = response.get('message', '')
            print(f"   ✅ Lesson deleted successfully")
            print(f"   📝 Message: {message}")
            
        self.log_test("Lesson Deletion API", success, f"- Deletion: {'Success' if success else 'Failed'}")
        return success

    def test_lesson_status_consistency(self):
        """Test data consistency for lesson status updates"""
        if not self.created_student_id or not self.created_teacher_id:
            self.log_test("Lesson Status Consistency", False, "- Missing test data")
            return False
            
        # Create a new lesson for consistency testing
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.created_student_id,
            "teacher_ids": [self.created_teacher_id],
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "booking_type": "private_lesson",
            "notes": "Test lesson for status consistency",
            "enrollment_id": self.created_enrollment_id
        }
        
        # Create lesson
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        if not success:
            self.log_test("Lesson Status Consistency", False, "- Failed to create test lesson")
            return False
            
        test_lesson_id = response.get('id')
        
        # Check initial status
        success, response = self.make_request('GET', f'lessons/{test_lesson_id}', expected_status=200)
        if not success:
            self.log_test("Lesson Status Consistency", False, "- Failed to fetch lesson")
            return False
            
        initial_status = response.get('status', 'unknown')
        initial_attended = response.get('is_attended', False)
        
        # Mark attendance
        success, response = self.make_request('POST', f'lessons/{test_lesson_id}/attend', expected_status=200)
        if not success:
            self.log_test("Lesson Status Consistency", False, "- Failed to mark attendance")
            return False
            
        # Check status after attendance
        success, response = self.make_request('GET', f'lessons/{test_lesson_id}', expected_status=200)
        if not success:
            self.log_test("Lesson Status Consistency", False, "- Failed to fetch lesson after attendance")
            return False
            
        updated_attended = response.get('is_attended', False)
        
        # Verify consistency
        consistency_check = (
            initial_attended == False and 
            updated_attended == True
        )
        
        if consistency_check:
            print(f"   ✅ Status consistency verified")
            print(f"   📊 Initial attended: {initial_attended} → Updated attended: {updated_attended}")
        
        # Clean up test lesson
        self.make_request('DELETE', f'lessons/{test_lesson_id}', expected_status=200)
        
        self.log_test("Lesson Status Consistency", consistency_check, 
                     f"- Status updates consistent: {consistency_check}")
        return consistency_check

    def test_error_handling(self):
        """Test error handling for invalid lesson IDs and authentication"""
        # Test with invalid lesson ID
        success, response = self.make_request('POST', 'lessons/invalid-lesson-id/attend', expected_status=404)
        invalid_lesson_test = success
        
        # Test without authentication
        original_token = self.token
        self.token = None
        success, response = self.make_request('POST', 'lessons/some-id/attend', expected_status=401)
        auth_test = success
        self.token = original_token
        
        # Test invalid student ID for credits
        success, response = self.make_request('GET', 'students/invalid-student-id/lesson-credits', expected_status=404)
        invalid_student_test = success
        
        overall_success = invalid_lesson_test and auth_test and invalid_student_test
        
        print(f"   ✅ Invalid lesson ID test: {'PASSED' if invalid_lesson_test else 'FAILED'}")
        print(f"   🔒 Authentication test: {'PASSED' if auth_test else 'FAILED'}")
        print(f"   👤 Invalid student ID test: {'PASSED' if invalid_student_test else 'FAILED'}")
        
        self.log_test("Error Handling", overall_success, 
                     f"- All error scenarios handled correctly: {overall_success}")
        return overall_success

    def cleanup_test_data(self):
        """Clean up created test data"""
        cleanup_success = True
        
        # Delete test enrollment
        if self.created_enrollment_id:
            success, _ = self.make_request('DELETE', f'enrollments/{self.created_enrollment_id}', expected_status=200)
            if success:
                print(f"   🗑️ Cleaned up test enrollment: {self.created_enrollment_id}")
            else:
                cleanup_success = False
                
        # Delete test student
        if self.created_student_id:
            success, _ = self.make_request('DELETE', f'students/{self.created_student_id}', expected_status=200)
            if success:
                print(f"   🗑️ Cleaned up test student: {self.created_student_id}")
            else:
                cleanup_success = False
                
        # Delete test teacher
        if self.created_teacher_id:
            success, _ = self.make_request('DELETE', f'teachers/{self.created_teacher_id}', expected_status=200)
            if success:
                print(f"   🗑️ Cleaned up test teacher: {self.created_teacher_id}")
            else:
                cleanup_success = False
                
        self.log_test("Cleanup Test Data", cleanup_success, 
                     f"- Test data cleanup: {'Complete' if cleanup_success else 'Partial'}")
        return cleanup_success

    def run_all_tests(self):
        """Run all weekly calendar backend tests"""
        print("🚀 Starting Weekly Calendar Backend API Testing...")
        print("=" * 60)
        
        # Authentication
        if not self.test_admin_login():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
            
        # Test data setup
        if not self.test_create_test_data():
            print("❌ Test data creation failed. Cannot proceed with lesson tests.")
            return
            
        # Core weekly calendar API tests
        self.test_lesson_fetching_api()
        self.test_create_lesson_for_attendance()
        self.test_lesson_attendance_api()
        self.test_lesson_credits_check_api()
        self.test_lesson_deletion_api()
        self.test_lesson_status_consistency()
        self.test_error_handling()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 WEEKLY CALENDAR BACKEND API TESTING SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL WEEKLY CALENDAR BACKEND TESTS PASSED!")
            print("✅ The enhanced weekly calendar backend functionality is working correctly.")
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} test(s) failed. Please review the issues above.")

if __name__ == "__main__":
    tester = WeeklyCalendarAPITester()
    tester.run_all_tests()