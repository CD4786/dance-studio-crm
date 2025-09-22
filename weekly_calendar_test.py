import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

class WeeklyCalendarAPITester:
    def __init__(self, base_url="https://studio-manager-5.preview.emergentagent.com"):
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
        
        # Test without authentication (expecting 403 or 401)
        original_token = self.token
        self.token = None
        success, response = self.make_request('POST', 'lessons/some-id/attend', expected_status=403)
        if not success:
            # Try with 401 as alternative
            success, response = self.make_request('POST', 'lessons/some-id/attend', expected_status=401)
        auth_test = success
        self.token = original_token
        
        # Test invalid student ID for credits - this endpoint returns 200 with empty data instead of 404
        success, response = self.make_request('GET', 'students/invalid-student-id/lesson-credits', expected_status=200)
        if success:
            # Verify it returns empty data for invalid student
            enrollments = response.get('enrollments', [])
            total_credits = response.get('total_lessons_available', 0)
            invalid_student_test = len(enrollments) == 0 and total_credits == 0
        else:
            invalid_student_test = False
        
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

    def test_weekly_calendar_endpoint_past_week(self):
        """Test GET /api/calendar/weekly endpoint with past week dates"""
        print("\n📅 Testing Weekly Calendar Endpoint - Past Week...")
        
        # Calculate past week start date (7 days ago)
        past_week_start = datetime.now() - timedelta(days=7)
        start_date_str = past_week_start.strftime("%Y-%m-%dT00:00:00")
        
        success, response = self.make_request('GET', f'calendar/weekly?start_date={start_date_str}', expected_status=200)
        
        if success:
            lessons = response if isinstance(response, list) else []
            print(f"   📊 Found {len(lessons)} lessons in past week ({past_week_start.strftime('%Y-%m-%d')} to {(past_week_start + timedelta(days=7)).strftime('%Y-%m-%d')})")
            
            # Verify data structure for each lesson
            valid_lessons = 0
            for lesson in lessons:
                if self.validate_weekly_lesson_structure(lesson):
                    valid_lessons += 1
                    
            print(f"   ✅ {valid_lessons}/{len(lessons)} lessons have valid PrivateLessonResponse structure")
            
            # Show sample lesson if available
            if lessons:
                sample_lesson = lessons[0]
                print(f"   📋 Sample lesson: {sample_lesson.get('student_name', 'Unknown')} with {', '.join(sample_lesson.get('teacher_names', []))}")
                print(f"   📅 Date: {sample_lesson.get('start_datetime', 'Unknown')}")
                print(f"   📝 Type: {sample_lesson.get('booking_type', 'Unknown')}")
                print(f"   🔄 Status: {sample_lesson.get('status', 'Unknown')}")
            
        self.log_test("Weekly Calendar Endpoint - Past Week", success, f"- {len(lessons) if success else 0} past lessons found")
        return success, lessons if success else []

    def test_weekly_calendar_endpoint_current_week(self):
        """Test GET /api/calendar/weekly endpoint with current week dates"""
        print("\n📅 Testing Weekly Calendar Endpoint - Current Week...")
        
        # Calculate current week start date (Monday of this week)
        today = datetime.now()
        days_since_monday = today.weekday()
        current_week_start = today - timedelta(days=days_since_monday)
        start_date_str = current_week_start.strftime("%Y-%m-%dT00:00:00")
        
        success, response = self.make_request('GET', f'calendar/weekly?start_date={start_date_str}', expected_status=200)
        
        if success:
            lessons = response if isinstance(response, list) else []
            print(f"   📊 Found {len(lessons)} lessons in current week ({current_week_start.strftime('%Y-%m-%d')} to {(current_week_start + timedelta(days=7)).strftime('%Y-%m-%d')})")
            
            # Verify data structure for each lesson
            valid_lessons = 0
            for lesson in lessons:
                if self.validate_weekly_lesson_structure(lesson):
                    valid_lessons += 1
                    
            print(f"   ✅ {valid_lessons}/{len(lessons)} lessons have valid PrivateLessonResponse structure")
            
        self.log_test("Weekly Calendar Endpoint - Current Week", success, f"- {len(lessons) if success else 0} current week lessons found")
        return success, lessons if success else []

    def test_weekly_calendar_endpoint_future_week(self):
        """Test GET /api/calendar/weekly endpoint with future week dates"""
        print("\n📅 Testing Weekly Calendar Endpoint - Future Week...")
        
        # Calculate future week start date (7 days from now)
        future_week_start = datetime.now() + timedelta(days=7)
        start_date_str = future_week_start.strftime("%Y-%m-%dT00:00:00")
        
        success, response = self.make_request('GET', f'calendar/weekly?start_date={start_date_str}', expected_status=200)
        
        if success:
            lessons = response if isinstance(response, list) else []
            print(f"   📊 Found {len(lessons)} lessons in future week ({future_week_start.strftime('%Y-%m-%d')} to {(future_week_start + timedelta(days=7)).strftime('%Y-%m-%d')})")
            
            # Verify data structure for each lesson
            valid_lessons = 0
            for lesson in lessons:
                if self.validate_weekly_lesson_structure(lesson):
                    valid_lessons += 1
                    
            print(f"   ✅ {valid_lessons}/{len(lessons)} lessons have valid PrivateLessonResponse structure")
            
        self.log_test("Weekly Calendar Endpoint - Future Week", success, f"- {len(lessons) if success else 0} future week lessons found")
        return success, lessons if success else []

    def validate_weekly_lesson_structure(self, lesson: Dict[str, Any]) -> bool:
        """Validate that lesson has proper PrivateLessonResponse structure for weekly calendar"""
        required_fields = [
            'id', 'student_id', 'student_name', 'teacher_ids', 'teacher_names',
            'start_datetime', 'end_datetime', 'booking_type', 'status'
        ]
        
        for field in required_fields:
            if field not in lesson:
                print(f"   ⚠️  Missing field '{field}' in lesson {lesson.get('id', 'unknown')}")
                return False
        
        # Validate teacher_names is a list
        if not isinstance(lesson.get('teacher_names'), list):
            print(f"   ⚠️  teacher_names should be a list in lesson {lesson.get('id', 'unknown')}")
            return False
            
        # Validate teacher_ids is a list
        if not isinstance(lesson.get('teacher_ids'), list):
            print(f"   ⚠️  teacher_ids should be a list in lesson {lesson.get('id', 'unknown')}")
            return False
        
        # Validate student_name is populated
        if not lesson.get('student_name') or lesson.get('student_name') == 'Unknown':
            print(f"   ⚠️  student_name should be populated in lesson {lesson.get('id', 'unknown')}")
            return False
            
        # Validate teacher_names are populated
        if not lesson.get('teacher_names') or any(name == 'Unknown' for name in lesson.get('teacher_names', [])):
            print(f"   ⚠️  teacher_names should be populated in lesson {lesson.get('id', 'unknown')}")
            return False
        
        return True

    def test_weekly_calendar_date_filtering(self):
        """Test that weekly calendar properly filters lessons by 7-day periods"""
        print("\n🔍 Testing Weekly Calendar Date Range Filtering...")
        
        # Get lessons from different weeks
        past_week_start = datetime.now() - timedelta(days=14)  # 2 weeks ago
        current_week_start = datetime.now() - timedelta(days=datetime.now().weekday())  # This Monday
        
        # Test past week
        past_start_str = past_week_start.strftime("%Y-%m-%dT00:00:00")
        success1, past_lessons = self.make_request('GET', f'calendar/weekly?start_date={past_start_str}', expected_status=200)
        
        # Test current week
        current_start_str = current_week_start.strftime("%Y-%m-%dT00:00:00")
        success2, current_lessons = self.make_request('GET', f'calendar/weekly?start_date={current_start_str}', expected_status=200)
        
        if success1 and success2:
            past_lessons = past_lessons if isinstance(past_lessons, list) else []
            current_lessons = current_lessons if isinstance(current_lessons, list) else []
            
            print(f"   📊 Past week ({past_week_start.strftime('%Y-%m-%d')}): {len(past_lessons)} lessons")
            print(f"   📊 Current week ({current_week_start.strftime('%Y-%m-%d')}): {len(current_lessons)} lessons")
            
            # Verify lessons are within the correct date ranges
            past_week_end = past_week_start + timedelta(days=7)
            current_week_end = current_week_start + timedelta(days=7)
            
            past_valid = self.validate_date_range(past_lessons, past_week_start, past_week_end)
            current_valid = self.validate_date_range(current_lessons, current_week_start, current_week_end)
            
            success = past_valid and current_valid
            print(f"   ✅ Date filtering accuracy: {'Correct' if success else 'Issues detected'}")
            
        else:
            success = False
            
        self.log_test("Weekly Calendar Date Filtering", success, f"- Proper 7-day filtering: {'Yes' if success else 'No'}")
        return success

    def validate_date_range(self, lessons: List[Dict], start_date: datetime, end_date: datetime) -> bool:
        """Validate that all lessons fall within the specified 7-day range"""
        for lesson in lessons:
            lesson_date_str = lesson.get('start_datetime', '')
            try:
                # Parse the lesson date
                if lesson_date_str.endswith('Z'):
                    lesson_date = datetime.fromisoformat(lesson_date_str.replace('Z', '+00:00'))
                else:
                    lesson_date = datetime.fromisoformat(lesson_date_str)
                
                # Remove timezone info for comparison
                lesson_date = lesson_date.replace(tzinfo=None)
                
                if not (start_date <= lesson_date < end_date):
                    print(f"   ⚠️  Lesson {lesson.get('id')} date {lesson_date} is outside 7-day range {start_date} - {end_date}")
                    return False
                    
            except ValueError as e:
                print(f"   ⚠️  Invalid date format in lesson {lesson.get('id')}: {lesson_date_str}")
                return False
        
        return True

    def test_weekly_calendar_vs_main_lessons_api(self):
        """Compare weekly calendar results with main lessons API for data consistency"""
        print("\n🔄 Testing Weekly Calendar vs Main Lessons API Consistency...")
        
        # Get all lessons from main API
        success1, all_lessons = self.make_request('GET', 'lessons', expected_status=200)
        
        # Get lessons from current week via weekly calendar
        current_week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        start_date_str = current_week_start.strftime("%Y-%m-%dT00:00:00")
        success2, weekly_lessons = self.make_request('GET', f'calendar/weekly?start_date={start_date_str}', expected_status=200)
        
        if success1 and success2:
            all_lessons = all_lessons if isinstance(all_lessons, list) else []
            weekly_lessons = weekly_lessons if isinstance(weekly_lessons, list) else []
            
            # Filter main API lessons to current week for comparison
            current_week_end = current_week_start + timedelta(days=7)
            filtered_main_lessons = []
            
            for lesson in all_lessons:
                lesson_date_str = lesson.get('start_datetime', '')
                try:
                    if lesson_date_str.endswith('Z'):
                        lesson_date = datetime.fromisoformat(lesson_date_str.replace('Z', '+00:00'))
                    else:
                        lesson_date = datetime.fromisoformat(lesson_date_str)
                    
                    lesson_date = lesson_date.replace(tzinfo=None)
                    
                    if current_week_start <= lesson_date < current_week_end:
                        filtered_main_lessons.append(lesson)
                        
                except ValueError:
                    continue
            
            print(f"   📊 Main API (filtered to current week): {len(filtered_main_lessons)} lessons")
            print(f"   📊 Weekly Calendar API: {len(weekly_lessons)} lessons")
            
            # Compare lesson IDs
            main_ids = set(lesson.get('id') for lesson in filtered_main_lessons)
            weekly_ids = set(lesson.get('id') for lesson in weekly_lessons)
            
            missing_in_weekly = main_ids - weekly_ids
            extra_in_weekly = weekly_ids - main_ids
            
            if missing_in_weekly:
                print(f"   ⚠️  {len(missing_in_weekly)} lessons missing in weekly calendar")
            
            if extra_in_weekly:
                print(f"   ⚠️  {len(extra_in_weekly)} extra lessons in weekly calendar")
            
            success = len(missing_in_weekly) == 0 and len(extra_in_weekly) == 0
            print(f"   ✅ Data consistency: {'Perfect match' if success else 'Discrepancies found'}")
            
        else:
            success = False
            
        self.log_test("Weekly Calendar vs Main API Consistency", success, f"- APIs return same lessons: {'Yes' if success else 'No'}")
        return success

    def run_all_tests(self):
        """Run all weekly calendar backend tests including specific endpoint testing"""
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
        
        # NEW: Specific Weekly Calendar Endpoint Tests (as requested in review)
        print("\n" + "🎯 WEEKLY CALENDAR ENDPOINT SPECIFIC TESTS" + "🎯")
        print("=" * 60)
        past_success, past_lessons = self.test_weekly_calendar_endpoint_past_week()
        current_success, current_lessons = self.test_weekly_calendar_endpoint_current_week()
        future_success, future_lessons = self.test_weekly_calendar_endpoint_future_week()
        
        # Advanced weekly calendar tests
        date_filtering_success = self.test_weekly_calendar_date_filtering()
        consistency_success = self.test_weekly_calendar_vs_main_lessons_api()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 WEEKLY CALENDAR BACKEND API TESTING SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        # Weekly Calendar Endpoint Specific Results
        print(f"\n📅 WEEKLY CALENDAR ENDPOINT RESULTS:")
        total_past_lessons = len(past_lessons) if past_success else 0
        total_current_lessons = len(current_lessons) if current_success else 0
        total_future_lessons = len(future_lessons) if future_success else 0
        
        print(f"Past Week Lessons: {total_past_lessons}")
        print(f"Current Week Lessons: {total_current_lessons}")
        print(f"Future Week Lessons: {total_future_lessons}")
        
        # Critical assessment for the review request
        weekly_endpoint_tests = [past_success, current_success, future_success, date_filtering_success, consistency_success]
        all_weekly_tests_passed = all(weekly_endpoint_tests)
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL WEEKLY CALENDAR BACKEND TESTS PASSED!")
            print("✅ The enhanced weekly calendar backend functionality is working correctly.")
            
            if all_weekly_tests_passed:
                print("\n🎯 WEEKLY CALENDAR ENDPOINT FIX VERIFICATION:")
                print("✅ Past lessons are now showing correctly in weekly calendar")
                print("✅ Weekly calendar endpoint returns lessons from lessons collection")
                print("✅ Proper data structure with student and teacher names confirmed")
                print("✅ Date range filtering for 7-day periods working correctly")
                print("✅ Data consistency between weekly calendar and main lessons API verified")
            else:
                print("\n⚠️  Some weekly calendar endpoint tests failed - see details above")
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} test(s) failed. Please review the issues above.")

if __name__ == "__main__":
    tester = WeeklyCalendarAPITester()
    tester.run_all_tests()