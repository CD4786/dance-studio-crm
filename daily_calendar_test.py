import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any

class DailyCalendarAPITester:
    def __init__(self, base_url="https://rhythm-scheduler-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_teacher_ids = []
        self.created_student_id = None
        self.created_lesson_ids = []

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
            
        self.log_test("Admin Authentication", success, f"- Admin token received: {'Yes' if self.token else 'No'}")
        return success

    def setup_test_data(self):
        """Create test data for calendar testing"""
        print("\n🔧 Setting up test data...")
        
        # Create test teachers
        teachers_data = [
            {
                "name": "Isabella Martinez",
                "email": "isabella.martinez@dancestudio.com",
                "phone": "+1555001001",
                "specialties": ["ballet", "contemporary"],
                "bio": "Principal ballet instructor with 15+ years experience"
            },
            {
                "name": "David Chen",
                "email": "david.chen@dancestudio.com", 
                "phone": "+1555001002",
                "specialties": ["salsa", "ballroom"],
                "bio": "International ballroom champion and instructor"
            },
            {
                "name": "Sofia Rodriguez",
                "email": "sofia.rodriguez@dancestudio.com",
                "phone": "+1555001003", 
                "specialties": ["jazz", "hip_hop"],
                "bio": "Contemporary jazz and street dance specialist"
            }
        ]
        
        for teacher_data in teachers_data:
            success, response = self.make_request('POST', 'teachers', teacher_data, 200)
            if success:
                teacher_id = response.get('id')
                self.created_teacher_ids.append(teacher_id)
                print(f"   ✅ Created teacher: {teacher_data['name']} (ID: {teacher_id})")
            else:
                print(f"   ❌ Failed to create teacher: {teacher_data['name']}")
        
        # Create test student
        student_data = {
            "name": "Alexandra Thompson",
            "email": "alexandra.thompson@example.com",
            "phone": "+1555002001",
            "parent_name": "Jennifer Thompson",
            "parent_phone": "+1555002002",
            "parent_email": "jennifer.thompson@example.com",
            "notes": "Advanced student interested in multiple dance styles"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if success:
            self.created_student_id = response.get('id')
            print(f"   ✅ Created student: {student_data['name']} (ID: {self.created_student_id})")
        else:
            print(f"   ❌ Failed to create student: {student_data['name']}")
            
        return len(self.created_teacher_ids) >= 2 and self.created_student_id is not None

    def create_test_lessons_for_today(self):
        """Create test lessons for today's date"""
        if not self.created_teacher_ids or not self.created_student_id:
            print("   ❌ Missing test data for lesson creation")
            return False
            
        today = datetime.now()
        
        # Create lessons at different times today
        lesson_times = [
            {"hour": 9, "duration": 60, "booking_type": "private_lesson", "teachers": [self.created_teacher_ids[0]]},
            {"hour": 11, "duration": 90, "booking_type": "training", "teachers": [self.created_teacher_ids[1]]},
            {"hour": 14, "duration": 60, "booking_type": "meeting", "teachers": [self.created_teacher_ids[0], self.created_teacher_ids[1]]},
            {"hour": 16, "duration": 120, "booking_type": "party", "teachers": self.created_teacher_ids[:3] if len(self.created_teacher_ids) >= 3 else self.created_teacher_ids}
        ]
        
        for lesson_config in lesson_times:
            start_time = today.replace(hour=lesson_config["hour"], minute=0, second=0, microsecond=0)
            
            lesson_data = {
                "student_id": self.created_student_id,
                "teacher_ids": lesson_config["teachers"],
                "start_datetime": start_time.isoformat(),
                "duration_minutes": lesson_config["duration"],
                "booking_type": lesson_config["booking_type"],
                "notes": f"Test {lesson_config['booking_type']} lesson at {lesson_config['hour']}:00"
            }
            
            success, response = self.make_request('POST', 'lessons', lesson_data, 200)
            if success:
                lesson_id = response.get('id')
                self.created_lesson_ids.append(lesson_id)
                teacher_names = response.get('teacher_names', [])
                print(f"   ✅ Created {lesson_config['booking_type']} lesson at {lesson_config['hour']}:00 with {len(teacher_names)} teacher(s)")
            else:
                print(f"   ❌ Failed to create lesson at {lesson_config['hour']}:00")
        
        return len(self.created_lesson_ids) > 0

    def test_daily_calendar_api_today(self):
        """Test GET /api/calendar/daily/{date} endpoint with today's date"""
        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d')
        
        success, response = self.make_request('GET', f'calendar/daily/{date_str}', expected_status=200)
        
        if success:
            # Verify response structure
            required_fields = ['date', 'lessons', 'teachers']
            has_all_fields = all(field in response for field in required_fields)
            
            if has_all_fields:
                lessons_count = len(response.get('lessons', []))
                teachers_count = len(response.get('teachers', []))
                returned_date = response.get('date')
                
                # Verify date matches request
                date_matches = returned_date == date_str
                success = success and date_matches
                
                print(f"   📅 Date: {returned_date}")
                print(f"   📚 Lessons found: {lessons_count}")
                print(f"   👥 Teachers available: {teachers_count}")
            else:
                success = False
                print(f"   ❌ Missing required fields. Got: {list(response.keys())}")
            
        self.log_test("Daily Calendar API - Today", success, 
                     f"- Date: {date_str}, Structure: {'Valid' if success else 'Invalid'}")
        return success

    def test_calendar_data_structure_verification(self):
        """Verify the response contains expected fields and proper data structure"""
        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d')
        
        success, response = self.make_request('GET', f'calendar/daily/{date_str}', expected_status=200)
        
        if success:
            # Check main structure
            main_fields_valid = all(field in response for field in ['date', 'lessons', 'teachers'])
            
            # Check lessons structure
            lessons = response.get('lessons', [])
            lessons_structure_valid = True
            teacher_ids_arrays_valid = True
            
            for lesson in lessons:
                # Check required lesson fields
                required_lesson_fields = ['id', 'student_id', 'student_name', 'teacher_ids', 'teacher_names', 
                                        'start_datetime', 'end_datetime', 'booking_type']
                if not all(field in lesson for field in required_lesson_fields):
                    lessons_structure_valid = False
                    print(f"   ❌ Lesson missing fields: {[f for f in required_lesson_fields if f not in lesson]}")
                    break
                
                # Verify teacher_ids is an array
                teacher_ids = lesson.get('teacher_ids', [])
                teacher_names = lesson.get('teacher_names', [])
                if not isinstance(teacher_ids, list) or not isinstance(teacher_names, list):
                    teacher_ids_arrays_valid = False
                    print(f"   ❌ teacher_ids or teacher_names not arrays: {type(teacher_ids)}, {type(teacher_names)}")
                    break
                
                # Verify teacher_ids and teacher_names have same length
                if len(teacher_ids) != len(teacher_names):
                    teacher_ids_arrays_valid = False
                    print(f"   ❌ teacher_ids ({len(teacher_ids)}) and teacher_names ({len(teacher_names)}) length mismatch")
                    break
            
            # Check teachers structure
            teachers = response.get('teachers', [])
            teachers_structure_valid = True
            
            for teacher in teachers:
                required_teacher_fields = ['id', 'name', 'email', 'specialties']
                if not all(field in teacher for field in required_teacher_fields):
                    teachers_structure_valid = False
                    print(f"   ❌ Teacher missing fields: {[f for f in required_teacher_fields if f not in teacher]}")
                    break
            
            success = (main_fields_valid and lessons_structure_valid and 
                      teacher_ids_arrays_valid and teachers_structure_valid)
            
            if success:
                print(f"   ✅ Main structure: Valid")
                print(f"   ✅ Lessons structure: Valid ({len(lessons)} lessons)")
                print(f"   ✅ Teacher IDs arrays: Valid")
                print(f"   ✅ Teachers structure: Valid ({len(teachers)} teachers)")
            
        self.log_test("Calendar Data Structure Verification", success, 
                     f"- All structures valid: {'Yes' if success else 'No'}")
        return success

    def test_authentication_requirement(self):
        """Test that calendar endpoints require proper authentication"""
        # Save current token
        original_token = self.token
        
        # Test without token
        self.token = None
        today = datetime.now().strftime('%Y-%m-%d')
        
        success_no_token, response = self.make_request('GET', f'calendar/daily/{today}', expected_status=403)
        
        # Test with invalid token
        self.token = "invalid.token.here"
        success_invalid_token, response = self.make_request('GET', f'calendar/daily/{today}', expected_status=401)
        
        # Restore original token
        self.token = original_token
        
        # Test with valid token
        success_valid_token, response = self.make_request('GET', f'calendar/daily/{today}', expected_status=200)
        
        overall_success = success_no_token and success_invalid_token and success_valid_token
        
        self.log_test("Authentication Requirement", overall_success, 
                     f"- No token: {'403' if success_no_token else 'Wrong'}, Invalid: {'401' if success_invalid_token else 'Wrong'}, Valid: {'200' if success_valid_token else 'Wrong'}")
        return overall_success

    def test_date_format_testing(self):
        """Test calendar API with different date formats"""
        test_dates = [
            # Today in different formats
            datetime.now().strftime('%Y-%m-%d'),
            # Tomorrow
            (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            # Yesterday  
            (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            # Future date
            (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        ]
        
        successful_requests = 0
        
        for date_str in test_dates:
            success, response = self.make_request('GET', f'calendar/daily/{date_str}', expected_status=200)
            
            if success:
                returned_date = response.get('date')
                if returned_date == date_str:
                    successful_requests += 1
                    lessons_count = len(response.get('lessons', []))
                    print(f"   ✅ {date_str}: Valid response ({lessons_count} lessons)")
                else:
                    print(f"   ❌ {date_str}: Date mismatch - got {returned_date}")
            else:
                print(f"   ❌ {date_str}: Request failed")
        
        # Test invalid date format
        invalid_success, response = self.make_request('GET', 'calendar/daily/invalid-date', expected_status=400)
        
        overall_success = successful_requests == len(test_dates) and invalid_success
        
        self.log_test("Date Format Testing", overall_success, 
                     f"- Valid dates: {successful_requests}/{len(test_dates)}, Invalid rejected: {'Yes' if invalid_success else 'No'}")
        return overall_success

    def test_lesson_data_completeness(self):
        """Test that lessons contain all required fields and proper teacher information"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        success, response = self.make_request('GET', f'calendar/daily/{today}', expected_status=200)
        
        if success:
            lessons = response.get('lessons', [])
            
            if len(lessons) == 0:
                print("   ⚠️  No lessons found for today - creating test lesson")
                # Create a quick test lesson for today
                if self.created_teacher_ids and self.created_student_id:
                    now = datetime.now()
                    lesson_data = {
                        "student_id": self.created_student_id,
                        "teacher_ids": [self.created_teacher_ids[0]],
                        "start_datetime": now.replace(hour=18, minute=0, second=0, microsecond=0).isoformat(),
                        "duration_minutes": 60,
                        "booking_type": "private_lesson",
                        "notes": "Test lesson for data completeness verification"
                    }
                    
                    lesson_success, lesson_response = self.make_request('POST', 'lessons', lesson_data, 200)
                    if lesson_success:
                        self.created_lesson_ids.append(lesson_response.get('id'))
                        print("   ✅ Created test lesson")
                        
                        # Re-fetch calendar data
                        success, response = self.make_request('GET', f'calendar/daily/{today}', expected_status=200)
                        lessons = response.get('lessons', [])
            
            complete_lessons = 0
            total_lessons = len(lessons)
            
            for lesson in lessons:
                # Check all required fields
                required_fields = [
                    'id', 'student_id', 'student_name', 'teacher_ids', 'teacher_names',
                    'start_datetime', 'end_datetime', 'booking_type', 'is_attended'
                ]
                
                has_all_fields = all(field in lesson for field in required_fields)
                
                # Check teacher data consistency
                teacher_ids = lesson.get('teacher_ids', [])
                teacher_names = lesson.get('teacher_names', [])
                teacher_data_consistent = (isinstance(teacher_ids, list) and 
                                         isinstance(teacher_names, list) and
                                         len(teacher_ids) == len(teacher_names) and
                                         len(teacher_ids) > 0)
                
                # Check datetime format
                start_datetime = lesson.get('start_datetime')
                end_datetime = lesson.get('end_datetime')
                datetime_valid = (start_datetime is not None and end_datetime is not None)
                
                if has_all_fields and teacher_data_consistent and datetime_valid:
                    complete_lessons += 1
                    print(f"   ✅ Lesson {lesson.get('id', 'Unknown')[:8]}...: Complete data")
                else:
                    print(f"   ❌ Lesson {lesson.get('id', 'Unknown')[:8]}...: Incomplete data")
                    if not has_all_fields:
                        missing = [f for f in required_fields if f not in lesson]
                        print(f"      Missing fields: {missing}")
                    if not teacher_data_consistent:
                        print(f"      Teacher data issue: IDs={len(teacher_ids)}, Names={len(teacher_names)}")
            
            success = complete_lessons == total_lessons and total_lessons > 0
            
        self.log_test("Lesson Data Completeness", success, 
                     f"- Complete lessons: {complete_lessons}/{total_lessons}")
        return success

    def test_timezone_handling(self):
        """Test for any timezone issues in lesson datetime handling"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        success, response = self.make_request('GET', f'calendar/daily/{today}', expected_status=200)
        
        if success:
            lessons = response.get('lessons', [])
            timezone_issues = 0
            
            for lesson in lessons:
                start_datetime_str = lesson.get('start_datetime')
                end_datetime_str = lesson.get('end_datetime')
                
                try:
                    # Parse datetime strings
                    if 'T' in start_datetime_str:
                        start_dt = datetime.fromisoformat(start_datetime_str.replace('Z', ''))
                        end_dt = datetime.fromisoformat(end_datetime_str.replace('Z', ''))
                        
                        # Check if lesson is actually on the requested date
                        lesson_date = start_dt.strftime('%Y-%m-%d')
                        if lesson_date != today:
                            timezone_issues += 1
                            print(f"   ⚠️  Lesson date mismatch: Expected {today}, got {lesson_date}")
                        
                        # Check if end time is after start time
                        if end_dt <= start_dt:
                            timezone_issues += 1
                            print(f"   ⚠️  Invalid time range: {start_datetime_str} to {end_datetime_str}")
                            
                except Exception as e:
                    timezone_issues += 1
                    print(f"   ❌ Datetime parsing error: {e}")
            
            success = timezone_issues == 0
            
        self.log_test("Timezone Handling", success, 
                     f"- Timezone issues found: {timezone_issues}")
        return success

    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete created lessons
        for lesson_id in self.created_lesson_ids:
            success, response = self.make_request('DELETE', f'lessons/{lesson_id}', expected_status=200)
            if success:
                print(f"   ✅ Deleted lesson: {lesson_id}")
            else:
                print(f"   ❌ Failed to delete lesson: {lesson_id}")
        
        # Delete created student
        if self.created_student_id:
            success, response = self.make_request('DELETE', f'students/{self.created_student_id}', expected_status=200)
            if success:
                print(f"   ✅ Deleted student: {self.created_student_id}")
            else:
                print(f"   ❌ Failed to delete student: {self.created_student_id}")
        
        # Delete created teachers
        for teacher_id in self.created_teacher_ids:
            success, response = self.make_request('DELETE', f'teachers/{teacher_id}', expected_status=200)
            if success:
                print(f"   ✅ Deleted teacher: {teacher_id}")
            else:
                print(f"   ❌ Failed to delete teacher: {teacher_id}")

    def run_daily_calendar_tests(self):
        """Run all daily calendar API tests"""
        print("🗓️  DAILY CALENDAR API TESTING")
        print("=" * 50)
        
        # Authentication
        if not self.test_admin_login():
            print("❌ Authentication failed - cannot proceed with tests")
            return False
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Test data setup failed - cannot proceed with tests")
            return False
        
        # Create test lessons for today
        if not self.create_test_lessons_for_today():
            print("❌ Test lesson creation failed - some tests may not be comprehensive")
        
        print("\n📋 Running Daily Calendar API Tests...")
        print("-" * 40)
        
        # Run all tests
        test_methods = [
            self.test_daily_calendar_api_today,
            self.test_calendar_data_structure_verification,
            self.test_authentication_requirement,
            self.test_date_format_testing,
            self.test_lesson_data_completeness,
            self.test_timezone_handling
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ {test_method.__name__} - ERROR: {str(e)}")
                self.tests_run += 1
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 DAILY CALENDAR API TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL DAILY CALENDAR API TESTS PASSED!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} test(s) failed")
            return False

if __name__ == "__main__":
    tester = DailyCalendarAPITester()
    success = tester.run_daily_calendar_tests()
    sys.exit(0 if success else 1)