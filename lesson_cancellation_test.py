import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any

class LessonCancellationAPITester:
    def __init__(self, base_url="https://studio-manager-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
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
        
        if self.admin_token:
            headers['Authorization'] = f'Bearer {self.admin_token}'

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
        """Test login with admin@test.com / admin123 credentials"""
        login_data = {
            "email": "admin@test.com",
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success:
            self.admin_token = response.get('access_token')
            user_info = response.get('user', {})
            print(f"   👤 Admin user: {user_info.get('name', 'Unknown')} ({user_info.get('role', 'Unknown')})")
            
        self.log_test("Admin Authentication", success, f"- Admin token received: {'Yes' if self.admin_token else 'No'}")
        return success

    def setup_test_data(self):
        """Create test student, teacher, and lesson for cancellation testing"""
        # Create test student
        student_data = {
            "name": "Emma Rodriguez",
            "email": "emma.rodriguez@example.com",
            "phone": "+1555123456",
            "parent_name": "Maria Rodriguez",
            "parent_phone": "+1555123457",
            "parent_email": "maria.rodriguez@example.com",
            "notes": "Test student for lesson cancellation testing"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if success:
            self.created_student_id = response.get('id')
            print(f"   ✅ Created test student: {student_data['name']} (ID: {self.created_student_id})")
        else:
            self.log_test("Setup Test Data - Student", False, "- Failed to create test student")
            return False

        # Create test teacher
        teacher_data = {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "phone": "+1234567890",
            "specialties": ["ballet", "contemporary"],
            "bio": "Experienced ballet instructor for testing."
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if success:
            self.created_teacher_id = response.get('id')
            print(f"   ✅ Created test teacher: {teacher_data['name']} (ID: {self.created_teacher_id})")
        else:
            self.log_test("Setup Test Data - Teacher", False, "- Failed to create test teacher")
            return False

        # Create test enrollment
        enrollment_data = {
            "student_id": self.created_student_id,
            "program_name": "Test Cancellation Program",
            "total_lessons": 10,
            "price_per_lesson": 50.0,
            "initial_payment": 200.0,
            "total_paid": 200.0
        }
        
        success, response = self.make_request('POST', 'enrollments', enrollment_data, 200)
        if success:
            self.created_enrollment_id = response.get('id')
            print(f"   ✅ Created test enrollment (ID: {self.created_enrollment_id})")
        else:
            self.log_test("Setup Test Data - Enrollment", False, "- Failed to create test enrollment")
            return False

        # Create test lesson for tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.created_student_id,
            "teacher_ids": [self.created_teacher_id],
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "booking_type": "private_lesson",
            "notes": "Test lesson for cancellation testing",
            "enrollment_id": self.created_enrollment_id
        }
        
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        if success:
            self.created_lesson_id = response.get('id')
            print(f"   ✅ Created test lesson (ID: {self.created_lesson_id})")
        else:
            self.log_test("Setup Test Data - Lesson", False, "- Failed to create test lesson")
            return False

        self.log_test("Setup Test Data", True, "- All test data created successfully")
        return True

    def test_lesson_cancellation_api(self):
        """Test POST /api/lessons/{lesson_id}/cancel endpoint"""
        if not self.created_lesson_id:
            self.log_test("Lesson Cancellation API", False, "- No test lesson ID available")
            return False

        # Test cancellation with reason and notification options
        cancellation_data = {
            "reason": "Student requested cancellation due to scheduling conflict",
            "notify_student": True
        }

        success, response = self.make_request('PUT', f'lessons/{self.created_lesson_id}/cancel', 
                                            cancellation_data, 200)

        if success:
            message = response.get('message', '')
            lesson_id = response.get('lesson_id', '')
            
            # Verify response contains expected fields
            success = success and "cancelled successfully" in message and lesson_id == self.created_lesson_id
            
            print(f"   ✅ Cancellation response: {message}")

        self.log_test("Lesson Cancellation API", success, f"- Lesson {self.created_lesson_id} cancelled")
        return success

    def test_lesson_status_after_cancellation(self):
        """Verify lesson status changes to 'cancelled' after cancellation"""
        if not self.created_lesson_id:
            self.log_test("Lesson Status After Cancellation", False, "- No test lesson ID available")
            return False

        success, response = self.make_request('GET', f'lessons/{self.created_lesson_id}', expected_status=200)
        
        if success:
            lesson_status = response.get('status')
            is_cancelled = response.get('is_cancelled')
            cancellation_reason = response.get('cancellation_reason')
            cancelled_by = response.get('cancelled_by')
            cancelled_at = response.get('cancelled_at')
            
            # Verify lesson is properly marked as cancelled
            status_correct = lesson_status == "cancelled"
            is_cancelled_correct = is_cancelled == True
            has_reason = cancellation_reason is not None
            has_cancelled_by = cancelled_by is not None
            has_cancelled_at = cancelled_at is not None
            
            success = status_correct and is_cancelled_correct and has_reason and has_cancelled_by and has_cancelled_at
            
            print(f"   📋 Status: {lesson_status}, Cancelled: {is_cancelled}")
            print(f"   📋 Reason: {cancellation_reason}")
            print(f"   📋 Cancelled by: {cancelled_by} at {cancelled_at}")

        self.log_test("Lesson Status After Cancellation", success, 
                     f"- Status: {lesson_status}, Tracking: {'Complete' if success else 'Incomplete'}")
        return success

    def test_lesson_reactivation_api(self):
        """Test POST /api/lessons/{lesson_id}/reactivate endpoint"""
        if not self.created_lesson_id:
            self.log_test("Lesson Reactivation API", False, "- No test lesson ID available")
            return False

        # Test reactivation of cancelled lesson
        success, response = self.make_request('PUT', f'lessons/{self.created_lesson_id}/reactivate', 
                                            {}, 200)

        if success:
            message = response.get('message', '')
            lesson_id = response.get('lesson_id', '')
            
            # Verify response contains expected fields
            success = success and "reactivated successfully" in message and lesson_id == self.created_lesson_id
            
            print(f"   ✅ Reactivation response: {message}")

        self.log_test("Lesson Reactivation API", success, f"- Lesson {self.created_lesson_id} reactivated")
        return success

    def test_lesson_status_after_reactivation(self):
        """Verify lesson status changes back to 'active' after reactivation"""
        if not self.created_lesson_id:
            self.log_test("Lesson Status After Reactivation", False, "- No test lesson ID available")
            return False

        success, response = self.make_request('GET', f'lessons/{self.created_lesson_id}', expected_status=200)
        
        if success:
            lesson_status = response.get('status')
            is_cancelled = response.get('is_cancelled')
            cancellation_reason = response.get('cancellation_reason')
            cancelled_by = response.get('cancelled_by')
            cancelled_at = response.get('cancelled_at')
            
            # Verify lesson is properly reactivated
            status_correct = lesson_status == "active"
            is_cancelled_correct = is_cancelled == False
            reason_cleared = cancellation_reason is None
            cancelled_by_cleared = cancelled_by is None
            cancelled_at_cleared = cancelled_at is None
            
            success = status_correct and is_cancelled_correct and reason_cleared and cancelled_by_cleared and cancelled_at_cleared
            
            print(f"   📋 Status: {lesson_status}, Cancelled: {is_cancelled}")
            print(f"   📋 Cancellation data cleared: {reason_cleared and cancelled_by_cleared and cancelled_at_cleared}")

        self.log_test("Lesson Status After Reactivation", success, 
                     f"- Status: {lesson_status}, Reactivation: {'Complete' if success else 'Incomplete'}")
        return success

    def test_student_ledger_api(self):
        """Test GET /api/students/{student_id}/ledger endpoint"""
        if not self.created_student_id:
            self.log_test("Student Ledger API", False, "- No test student ID available")
            return False

        success, response = self.make_request('GET', f'students/{self.created_student_id}/ledger', expected_status=200)
        
        if success:
            # Verify response structure
            required_fields = ['student', 'enrollments', 'payments', 'upcoming_lessons', 
                             'lesson_history', 'total_paid', 'total_enrolled_lessons', 
                             'remaining_lessons', 'lessons_taken']
            
            has_all_fields = all(field in response for field in required_fields)
            
            if has_all_fields:
                student_info = response.get('student', {})
                enrollments = response.get('enrollments', [])
                payments = response.get('payments', [])
                upcoming_lessons = response.get('upcoming_lessons', [])
                lesson_history = response.get('lesson_history', [])
                
                print(f"   📊 Student: {student_info.get('name', 'Unknown')}")
                print(f"   📊 Enrollments: {len(enrollments)}, Payments: {len(payments)}")
                print(f"   📊 Upcoming: {len(upcoming_lessons)}, History: {len(lesson_history)}")
                print(f"   📊 Total paid: ${response.get('total_paid', 0)}")
                
                success = has_all_fields
            else:
                missing_fields = [field for field in required_fields if field not in response]
                print(f"   ❌ Missing fields: {missing_fields}")
                success = False

        self.log_test("Student Ledger API", success, 
                     f"- Response structure: {'Complete' if success else 'Incomplete'}")
        return success

    def test_data_integrity_verification(self):
        """Test that cancelled lessons preserve all data with proper status tracking"""
        if not self.created_lesson_id:
            self.log_test("Data Integrity Verification", False, "- No test lesson ID available")
            return False

        # First cancel the lesson again for testing
        cancellation_data = {
            "reason": "Testing data integrity preservation",
            "notify_student": False
        }
        
        cancel_success, _ = self.make_request('PUT', f'lessons/{self.created_lesson_id}/cancel', 
                                            cancellation_data, 200)
        
        if not cancel_success:
            self.log_test("Data Integrity Verification", False, "- Failed to cancel lesson for testing")
            return False

        # Get the lesson and verify all data is preserved
        success, response = self.make_request('GET', f'lessons/{self.created_lesson_id}', expected_status=200)
        
        if success:
            # Verify all original lesson data is preserved
            original_fields = ['id', 'student_id', 'teacher_ids', 'start_datetime', 
                             'end_datetime', 'booking_type', 'notes', 'enrollment_id']
            
            preserved_data = all(field in response for field in original_fields)
            
            # Verify cancellation tracking fields are present
            cancellation_fields = ['status', 'is_cancelled', 'cancellation_reason', 
                                 'cancelled_by', 'cancelled_at']
            
            tracking_data = all(field in response for field in cancellation_fields)
            
            # Verify lesson is still in database (not deleted)
            lesson_exists = response.get('id') == self.created_lesson_id
            
            success = preserved_data and tracking_data and lesson_exists
            
            print(f"   📋 Original data preserved: {preserved_data}")
            print(f"   📋 Cancellation tracking: {tracking_data}")
            print(f"   📋 Lesson exists in DB: {lesson_exists}")

        self.log_test("Data Integrity Verification", success, 
                     f"- Data preservation: {'Complete' if success else 'Incomplete'}")
        return success

    def test_time_slot_availability(self):
        """Test that time slots become available when lessons are cancelled"""
        if not self.created_lesson_id:
            self.log_test("Time Slot Availability", False, "- No test lesson ID available")
            return False

        # Get the lesson details to know the time slot
        success, lesson_response = self.make_request('GET', f'lessons/{self.created_lesson_id}', expected_status=200)
        
        if not success:
            self.log_test("Time Slot Availability", False, "- Failed to get lesson details")
            return False

        lesson_start = lesson_response.get('start_datetime')
        lesson_teacher_ids = lesson_response.get('teacher_ids', [])
        
        # Cancel the lesson
        cancellation_data = {
            "reason": "Testing time slot availability",
            "notify_student": False
        }
        
        cancel_success, _ = self.make_request('PUT', f'lessons/{self.created_lesson_id}/cancel', 
                                            cancellation_data, 200)
        
        if not cancel_success:
            self.log_test("Time Slot Availability", False, "- Failed to cancel lesson")
            return False

        # Try to create a new lesson at the same time slot
        new_lesson_data = {
            "student_id": self.created_student_id,
            "teacher_ids": lesson_teacher_ids,
            "start_datetime": lesson_start,
            "duration_minutes": 60,
            "booking_type": "private_lesson",
            "notes": "Testing time slot availability after cancellation"
        }
        
        success, new_lesson_response = self.make_request('POST', 'lessons', new_lesson_data, 200)
        
        if success:
            new_lesson_id = new_lesson_response.get('id')
            print(f"   ✅ New lesson created in same time slot: {new_lesson_id}")
            
            # Clean up - delete the new lesson
            self.make_request('DELETE', f'lessons/{new_lesson_id}', expected_status=200)
        else:
            print(f"   ❌ Failed to create new lesson in cancelled time slot")

        self.log_test("Time Slot Availability", success, 
                     f"- Time slot rebooking: {'Available' if success else 'Blocked'}")
        return success

    def test_error_handling_404_lesson(self):
        """Test proper 404 errors for non-existent lessons"""
        fake_lesson_id = "nonexistent-lesson-id-12345"
        
        # Test cancellation of non-existent lesson
        cancellation_data = {
            "reason": "Testing 404 error",
            "notify_student": False
        }
        
        success, response = self.make_request('PUT', f'lessons/{fake_lesson_id}/cancel', 
                                            cancellation_data, 404)
        
        cancel_404_works = success
        
        # Test reactivation of non-existent lesson
        success, response = self.make_request('PUT', f'lessons/{fake_lesson_id}/reactivate', 
                                            {}, 404)
        
        reactivate_404_works = success
        
        overall_success = cancel_404_works and reactivate_404_works
        
        print(f"   📋 Cancel 404: {'✅' if cancel_404_works else '❌'}")
        print(f"   📋 Reactivate 404: {'✅' if reactivate_404_works else '❌'}")

        self.log_test("Error Handling - 404 Lesson", overall_success, 
                     f"- Both endpoints return 404 for non-existent lessons")
        return overall_success

    def test_error_handling_400_invalid_operations(self):
        """Test 400 errors for invalid operations"""
        if not self.created_lesson_id:
            self.log_test("Error Handling - 400 Invalid Operations", False, "- No test lesson ID available")
            return False

        # First ensure lesson is active
        self.make_request('PUT', f'lessons/{self.created_lesson_id}/reactivate', {}, 200)
        
        # Try to reactivate an already active lesson
        success, response = self.make_request('PUT', f'lessons/{self.created_lesson_id}/reactivate', 
                                            {}, 400)
        
        reactivate_active_400 = success
        
        print(f"   📋 Reactivate active lesson 400: {'✅' if reactivate_active_400 else '❌'}")

        self.log_test("Error Handling - 400 Invalid Operations", reactivate_active_400, 
                     f"- Invalid operations return 400 errors")
        return reactivate_active_400

    def test_error_handling_403_unauthorized(self):
        """Test 403 Forbidden for unauthorized access"""
        if not self.created_lesson_id:
            self.log_test("Error Handling - 403 Unauthorized", False, "- No test lesson ID available")
            return False

        # Save current token
        original_token = self.admin_token
        
        # Remove token to test unauthorized access
        self.admin_token = None
        
        # Test cancellation without authentication
        cancellation_data = {
            "reason": "Testing unauthorized access",
            "notify_student": False
        }
        
        success, response = self.make_request('PUT', f'lessons/{self.created_lesson_id}/cancel', 
                                            cancellation_data, 403)
        
        cancel_403_works = success
        
        # Test reactivation without authentication
        success, response = self.make_request('PUT', f'lessons/{self.created_lesson_id}/reactivate', 
                                            {}, 403)
        
        reactivate_403_works = success
        
        # Restore token
        self.admin_token = original_token
        
        overall_success = cancel_403_works and reactivate_403_works
        
        print(f"   📋 Cancel 403: {'✅' if cancel_403_works else '❌'}")
        print(f"   📋 Reactivate 403: {'✅' if reactivate_403_works else '❌'}")

        self.log_test("Error Handling - 403 Unauthorized", overall_success, 
                     f"- Both endpoints require authentication")
        return overall_success

    def cleanup_test_data(self):
        """Clean up created test data"""
        cleanup_success = True
        
        # Delete test lesson
        if self.created_lesson_id:
            success, _ = self.make_request('DELETE', f'lessons/{self.created_lesson_id}', expected_status=200)
            if success:
                print(f"   🧹 Deleted test lesson: {self.created_lesson_id}")
            else:
                cleanup_success = False

        # Delete test enrollment
        if self.created_enrollment_id:
            success, _ = self.make_request('DELETE', f'enrollments/{self.created_enrollment_id}', expected_status=200)
            if success:
                print(f"   🧹 Deleted test enrollment: {self.created_enrollment_id}")
            else:
                cleanup_success = False

        # Delete test student
        if self.created_student_id:
            success, _ = self.make_request('DELETE', f'students/{self.created_student_id}', expected_status=200)
            if success:
                print(f"   🧹 Deleted test student: {self.created_student_id}")
            else:
                cleanup_success = False

        # Delete test teacher
        if self.created_teacher_id:
            success, _ = self.make_request('DELETE', f'teachers/{self.created_teacher_id}', expected_status=200)
            if success:
                print(f"   🧹 Deleted test teacher: {self.created_teacher_id}")
            else:
                cleanup_success = False

        self.log_test("Cleanup Test Data", cleanup_success, "- All test data cleaned up")
        return cleanup_success

    def run_all_tests(self):
        """Run all lesson cancellation and reactivation tests"""
        print("🎯 LESSON CANCELLATION & REACTIVATION API TESTING")
        print("=" * 60)
        
        # Authentication
        if not self.test_admin_login():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False

        # Setup test data
        if not self.setup_test_data():
            print("❌ Test data setup failed. Cannot proceed with tests.")
            return False

        print("\n📋 TESTING LESSON CANCELLATION FUNCTIONALITY")
        print("-" * 50)
        
        # Test lesson cancellation API
        self.test_lesson_cancellation_api()
        self.test_lesson_status_after_cancellation()
        
        print("\n📋 TESTING LESSON REACTIVATION FUNCTIONALITY")
        print("-" * 50)
        
        # Test lesson reactivation API
        self.test_lesson_reactivation_api()
        self.test_lesson_status_after_reactivation()
        
        print("\n📋 TESTING STUDENT LEDGER API")
        print("-" * 30)
        
        # Test student ledger API
        self.test_student_ledger_api()
        
        print("\n📋 TESTING DATA INTEGRITY")
        print("-" * 30)
        
        # Test data integrity
        self.test_data_integrity_verification()
        self.test_time_slot_availability()
        
        print("\n📋 TESTING ERROR HANDLING")
        print("-" * 30)
        
        # Test error handling
        self.test_error_handling_404_lesson()
        self.test_error_handling_400_invalid_operations()
        self.test_error_handling_403_unauthorized()
        
        print("\n🧹 CLEANUP")
        print("-" * 10)
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"🎯 LESSON CANCELLATION & REACTIVATION API TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Lesson cancellation and reactivation APIs are working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Please review the results above.")
            return False

if __name__ == "__main__":
    tester = LessonCancellationAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)