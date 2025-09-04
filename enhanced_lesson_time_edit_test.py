import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any

class EnhancedLessonTimeEditTester:
    def __init__(self, base_url="https://studio-manager-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test data IDs
        self.created_student_id = None
        self.created_teacher_id_1 = None
        self.created_teacher_id_2 = None
        self.created_teacher_id_3 = None
        self.created_enrollment_id = None
        self.test_lesson_id = None

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

    def setup_test_data(self):
        """Setup test data for lesson time edit testing"""
        print("\n🔧 Setting up test data...")
        
        # Register and login user
        timestamp = datetime.now().strftime("%H%M%S")
        user_data = {
            "email": f"lesson_edit_test_{timestamp}@example.com",
            "name": f"Lesson Edit Tester {timestamp}",
            "password": "TestPassword123!",
            "role": "owner",
            "studio_name": "Test Dance Studio"
        }
        
        success, response = self.make_request('POST', 'auth/register', user_data, 200)
        if not success:
            print("❌ Failed to register user")
            return False
            
        # Login
        login_data = {
            "email": user_data['email'],
            "password": user_data['password']
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        if not success:
            print("❌ Failed to login")
            return False
            
        self.token = response.get('access_token')
        print(f"✅ User authenticated")
        
        # Create test student
        student_data = {
            "name": "Isabella Martinez",
            "email": "isabella.martinez@example.com",
            "phone": "+1555123456",
            "notes": "Student for lesson time edit testing"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            print("❌ Failed to create test student")
            return False
            
        self.created_student_id = response.get('id')
        print(f"✅ Created test student: {student_data['name']}")
        
        # Create multiple test teachers
        teachers_data = [
            {
                "name": "Sofia Rodriguez",
                "email": "sofia.rodriguez@example.com",
                "phone": "+1555111111",
                "specialties": ["ballet", "contemporary"],
                "bio": "Ballet and contemporary instructor"
            },
            {
                "name": "Marcus Johnson",
                "email": "marcus.johnson@example.com",
                "phone": "+1555222222",
                "specialties": ["jazz", "hip_hop"],
                "bio": "Jazz and hip hop specialist"
            },
            {
                "name": "Elena Petrov",
                "email": "elena.petrov@example.com",
                "phone": "+1555333333",
                "specialties": ["ballroom", "salsa"],
                "bio": "Ballroom and Latin dance expert"
            }
        ]
        
        teacher_ids = []
        for teacher_data in teachers_data:
            success, response = self.make_request('POST', 'teachers', teacher_data, 200)
            if not success:
                print(f"❌ Failed to create teacher: {teacher_data['name']}")
                return False
            teacher_ids.append(response.get('id'))
            print(f"✅ Created teacher: {teacher_data['name']}")
        
        self.created_teacher_id_1, self.created_teacher_id_2, self.created_teacher_id_3 = teacher_ids
        
        # Create test enrollment
        enrollment_data = {
            "student_id": self.created_student_id,
            "program_name": "Enhanced Lesson Testing Program",
            "total_lessons": 20,
            "total_paid": 1000.0
        }
        
        success, response = self.make_request('POST', 'enrollments', enrollment_data, 200)
        if not success:
            print("❌ Failed to create test enrollment")
            return False
            
        self.created_enrollment_id = response.get('id')
        print(f"✅ Created test enrollment with 20 lessons")
        
        print("✅ Test data setup complete!\n")
        return True

    def test_create_initial_lesson(self):
        """Create initial lesson for time edit testing"""
        # Create lesson for tomorrow at 2:00 PM
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": self.created_student_id,
            "teacher_ids": [self.created_teacher_id_1],
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "booking_type": "private_lesson",
            "notes": "Initial lesson for time edit testing",
            "enrollment_id": self.created_enrollment_id
        }
        
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        
        if success:
            self.test_lesson_id = response.get('id')
            original_start = response.get('start_datetime')
            original_end = response.get('end_datetime')
            teacher_names = response.get('teacher_names', [])
            
            # Verify lesson was created correctly
            success = success and len(teacher_names) == 1
            
        self.log_test("Create Initial Lesson", success, 
                     f"- Lesson ID: {self.test_lesson_id}, Teacher: {teacher_names[0] if teacher_names else 'None'}")
        return success

    def test_update_lesson_start_datetime_different_date(self):
        """Test updating lesson start_datetime to different date"""
        if not self.test_lesson_id:
            self.log_test("Update Lesson Date", False, "- No test lesson available")
            return False
            
        # Update to day after tomorrow at same time
        day_after_tomorrow = datetime.now() + timedelta(days=2)
        new_start_time = day_after_tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        
        update_data = {
            "start_datetime": new_start_time.isoformat()
        }
        
        success, response = self.make_request('PUT', f'lessons/{self.test_lesson_id}', update_data, 200)
        
        if success:
            updated_start = response.get('start_datetime')
            updated_end = response.get('end_datetime')
            
            # Parse datetime strings for comparison
            updated_start_dt = datetime.fromisoformat(updated_start.replace('Z', ''))
            updated_end_dt = datetime.fromisoformat(updated_end.replace('Z', ''))
            
            # Verify date was updated and duration preserved (60 minutes)
            duration_minutes = (updated_end_dt - updated_start_dt).total_seconds() / 60
            date_updated = updated_start_dt.date() == new_start_time.date()
            duration_preserved = abs(duration_minutes - 60) < 1  # Allow small floating point differences
            
            success = success and date_updated and duration_preserved
            
        self.log_test("Update Lesson Date", success, 
                     f"- New date: {new_start_time.date()}, Duration preserved: {duration_preserved}")
        return success

    def test_update_lesson_start_datetime_different_time(self):
        """Test updating lesson start_datetime to different time same day"""
        if not self.test_lesson_id:
            self.log_test("Update Lesson Time", False, "- No test lesson available")
            return False
            
        # Update to 4:30 PM same day
        day_after_tomorrow = datetime.now() + timedelta(days=2)
        new_start_time = day_after_tomorrow.replace(hour=16, minute=30, second=0, microsecond=0)
        
        update_data = {
            "start_datetime": new_start_time.isoformat()
        }
        
        success, response = self.make_request('PUT', f'lessons/{self.test_lesson_id}', update_data, 200)
        
        if success:
            updated_start = response.get('start_datetime')
            updated_end = response.get('end_datetime')
            
            # Parse datetime strings for comparison
            updated_start_dt = datetime.fromisoformat(updated_start.replace('Z', ''))
            updated_end_dt = datetime.fromisoformat(updated_end.replace('Z', ''))
            
            # Verify time was updated and duration preserved
            duration_minutes = (updated_end_dt - updated_start_dt).total_seconds() / 60
            time_updated = updated_start_dt.time() == new_start_time.time()
            duration_preserved = abs(duration_minutes - 60) < 1
            
            success = success and time_updated and duration_preserved
            
        self.log_test("Update Lesson Time", success, 
                     f"- New time: {new_start_time.time()}, Duration preserved: {duration_preserved}")
        return success

    def test_update_lesson_datetime_and_duration(self):
        """Test updating both start_datetime and duration simultaneously"""
        if not self.test_lesson_id:
            self.log_test("Update DateTime and Duration", False, "- No test lesson available")
            return False
            
        # Update to 3 days from now at 10:00 AM with 90 minutes duration
        three_days_later = datetime.now() + timedelta(days=3)
        new_start_time = three_days_later.replace(hour=10, minute=0, second=0, microsecond=0)
        
        update_data = {
            "start_datetime": new_start_time.isoformat(),
            "duration_minutes": 90
        }
        
        success, response = self.make_request('PUT', f'lessons/{self.test_lesson_id}', update_data, 200)
        
        if success:
            updated_start = response.get('start_datetime')
            updated_end = response.get('end_datetime')
            
            # Parse datetime strings for comparison
            updated_start_dt = datetime.fromisoformat(updated_start.replace('Z', ''))
            updated_end_dt = datetime.fromisoformat(updated_end.replace('Z', ''))
            
            # Verify both datetime and duration were updated
            duration_minutes = (updated_end_dt - updated_start_dt).total_seconds() / 60
            datetime_updated = updated_start_dt == new_start_time
            duration_updated = abs(duration_minutes - 90) < 1
            
            success = success and datetime_updated and duration_updated
            
        self.log_test("Update DateTime and Duration", success, 
                     f"- DateTime: {datetime_updated}, Duration: {duration_updated} (90 min)")
        return success

    def test_update_lesson_datetime_with_multiple_instructors(self):
        """Test updating lesson datetime along with adding multiple instructors"""
        if not self.test_lesson_id:
            self.log_test("Update DateTime + Multiple Instructors", False, "- No test lesson available")
            return False
            
        # Update to 4 days from now at 11:30 AM with multiple teachers
        four_days_later = datetime.now() + timedelta(days=4)
        new_start_time = four_days_later.replace(hour=11, minute=30, second=0, microsecond=0)
        
        update_data = {
            "start_datetime": new_start_time.isoformat(),
            "teacher_ids": [self.created_teacher_id_1, self.created_teacher_id_2],
            "duration_minutes": 75
        }
        
        success, response = self.make_request('PUT', f'lessons/{self.test_lesson_id}', update_data, 200)
        
        if success:
            updated_start = response.get('start_datetime')
            updated_end = response.get('end_datetime')
            teacher_names = response.get('teacher_names', [])
            
            # Parse datetime strings for comparison
            updated_start_dt = datetime.fromisoformat(updated_start.replace('Z', ''))
            updated_end_dt = datetime.fromisoformat(updated_end.replace('Z', ''))
            
            # Verify datetime, duration, and multiple instructors
            duration_minutes = (updated_end_dt - updated_start_dt).total_seconds() / 60
            datetime_updated = updated_start_dt == new_start_time
            duration_updated = abs(duration_minutes - 75) < 1
            multiple_teachers = len(teacher_names) == 2
            
            success = success and datetime_updated and duration_updated and multiple_teachers
            
        self.log_test("Update DateTime + Multiple Instructors", success, 
                     f"- DateTime: {datetime_updated}, Duration: {duration_updated}, Teachers: {len(teacher_names)}")
        return success

    def test_update_lesson_datetime_with_booking_type(self):
        """Test updating lesson datetime along with booking type"""
        if not self.test_lesson_id:
            self.log_test("Update DateTime + Booking Type", False, "- No test lesson available")
            return False
            
        # Update to 5 days from now at 3:00 PM with training booking type
        five_days_later = datetime.now() + timedelta(days=5)
        new_start_time = five_days_later.replace(hour=15, minute=0, second=0, microsecond=0)
        
        update_data = {
            "start_datetime": new_start_time.isoformat(),
            "booking_type": "training",
            "notes": "Updated to training session with new time"
        }
        
        success, response = self.make_request('PUT', f'lessons/{self.test_lesson_id}', update_data, 200)
        
        if success:
            updated_start = response.get('start_datetime')
            updated_booking_type = response.get('booking_type')
            updated_notes = response.get('notes')
            
            # Parse datetime strings for comparison
            updated_start_dt = datetime.fromisoformat(updated_start.replace('Z', ''))
            
            # Verify datetime, booking type, and notes were updated
            datetime_updated = updated_start_dt == new_start_time
            booking_type_updated = updated_booking_type == "training"
            notes_updated = "training session" in updated_notes.lower()
            
            success = success and datetime_updated and booking_type_updated and notes_updated
            
        self.log_test("Update DateTime + Booking Type", success, 
                     f"- DateTime: {datetime_updated}, Type: {updated_booking_type}, Notes: {notes_updated}")
        return success

    def test_update_lesson_all_fields_simultaneously(self):
        """Test updating all fields simultaneously (datetime, instructors, booking type, notes)"""
        if not self.test_lesson_id:
            self.log_test("Update All Fields Simultaneously", False, "- No test lesson available")
            return False
            
        # Update to 6 days from now at 1:15 PM with all changes
        six_days_later = datetime.now() + timedelta(days=6)
        new_start_time = six_days_later.replace(hour=13, minute=15, second=0, microsecond=0)
        
        update_data = {
            "start_datetime": new_start_time.isoformat(),
            "duration_minutes": 120,
            "teacher_ids": [self.created_teacher_id_2, self.created_teacher_id_3],
            "booking_type": "party",
            "notes": "Comprehensive update: Party lesson with multiple instructors and extended duration"
        }
        
        success, response = self.make_request('PUT', f'lessons/{self.test_lesson_id}', update_data, 200)
        
        if success:
            updated_start = response.get('start_datetime')
            updated_end = response.get('end_datetime')
            teacher_names = response.get('teacher_names', [])
            updated_booking_type = response.get('booking_type')
            updated_notes = response.get('notes')
            
            # Parse datetime strings for comparison
            updated_start_dt = datetime.fromisoformat(updated_start.replace('Z', ''))
            updated_end_dt = datetime.fromisoformat(updated_end.replace('Z', ''))
            
            # Verify all fields were updated correctly
            duration_minutes = (updated_end_dt - updated_start_dt).total_seconds() / 60
            datetime_updated = updated_start_dt == new_start_time
            duration_updated = abs(duration_minutes - 120) < 1
            teachers_updated = len(teacher_names) == 2
            booking_type_updated = updated_booking_type == "party"
            notes_updated = "comprehensive update" in updated_notes.lower()
            
            all_fields_updated = (datetime_updated and duration_updated and 
                                teachers_updated and booking_type_updated and notes_updated)
            success = success and all_fields_updated
            
        self.log_test("Update All Fields Simultaneously", success, 
                     f"- All fields updated: {all_fields_updated} (DateTime, Duration, Teachers, Type, Notes)")
        return success

    def test_update_lesson_to_same_datetime(self):
        """Test updating lesson to same datetime (no change)"""
        if not self.test_lesson_id:
            self.log_test("Update to Same DateTime", False, "- No test lesson available")
            return False
            
        # First get current lesson details
        success, current_lesson = self.make_request('GET', f'lessons/{self.test_lesson_id}', expected_status=200)
        if not success:
            self.log_test("Update to Same DateTime", False, "- Failed to get current lesson")
            return False
            
        current_start = current_lesson.get('start_datetime')
        current_end = current_lesson.get('end_datetime')
        
        # Update with same datetime
        update_data = {
            "start_datetime": current_start,
            "notes": "Updated notes but same datetime"
        }
        
        success, response = self.make_request('PUT', f'lessons/{self.test_lesson_id}', update_data, 200)
        
        if success:
            updated_start = response.get('start_datetime')
            updated_end = response.get('end_datetime')
            updated_notes = response.get('notes')
            
            # Verify datetime remained the same but notes were updated
            datetime_unchanged = updated_start == current_start and updated_end == current_end
            notes_updated = "same datetime" in updated_notes.lower()
            
            success = success and datetime_unchanged and notes_updated
            
        self.log_test("Update to Same DateTime", success, 
                     f"- DateTime unchanged: {datetime_unchanged}, Notes updated: {notes_updated}")
        return success

    def test_update_lesson_invalid_datetime_format(self):
        """Test updating lesson with invalid datetime format"""
        if not self.test_lesson_id:
            self.log_test("Update Invalid DateTime Format", False, "- No test lesson available")
            return False
            
        # Try to update with invalid datetime format
        update_data = {
            "start_datetime": "invalid-datetime-format",
            "notes": "Testing invalid datetime"
        }
        
        # This should fail with 422 validation error
        success, response = self.make_request('PUT', f'lessons/{self.test_lesson_id}', update_data, 422)
        
        self.log_test("Update Invalid DateTime Format", success, "- Invalid format correctly rejected")
        return success

    def test_multiple_datetime_updates_sequence(self):
        """Test updating lesson time multiple times in sequence"""
        if not self.test_lesson_id:
            self.log_test("Multiple DateTime Updates Sequence", False, "- No test lesson available")
            return False
            
        # Perform multiple datetime updates
        updates = [
            {
                "days_offset": 7,
                "hour": 9,
                "minute": 0,
                "duration": 45,
                "description": "Morning session"
            },
            {
                "days_offset": 8,
                "hour": 14,
                "minute": 30,
                "duration": 60,
                "description": "Afternoon session"
            },
            {
                "days_offset": 9,
                "hour": 18,
                "minute": 45,
                "duration": 90,
                "description": "Evening session"
            }
        ]
        
        successful_updates = 0
        
        for i, update_info in enumerate(updates):
            future_date = datetime.now() + timedelta(days=update_info["days_offset"])
            new_start_time = future_date.replace(
                hour=update_info["hour"], 
                minute=update_info["minute"], 
                second=0, 
                microsecond=0
            )
            
            update_data = {
                "start_datetime": new_start_time.isoformat(),
                "duration_minutes": update_info["duration"],
                "notes": f"Update #{i+1}: {update_info['description']}"
            }
            
            success, response = self.make_request('PUT', f'lessons/{self.test_lesson_id}', update_data, 200)
            
            if success:
                updated_start = response.get('start_datetime')
                updated_end = response.get('end_datetime')
                
                # Parse and verify
                updated_start_dt = datetime.fromisoformat(updated_start.replace('Z', ''))
                updated_end_dt = datetime.fromisoformat(updated_end.replace('Z', ''))
                duration_minutes = (updated_end_dt - updated_start_dt).total_seconds() / 60
                
                datetime_correct = updated_start_dt == new_start_time
                duration_correct = abs(duration_minutes - update_info["duration"]) < 1
                
                if datetime_correct and duration_correct:
                    successful_updates += 1
                    print(f"   ✅ Update #{i+1}: {update_info['description']} - {new_start_time.strftime('%Y-%m-%d %H:%M')}")
                else:
                    print(f"   ❌ Update #{i+1}: DateTime or duration mismatch")
            else:
                print(f"   ❌ Update #{i+1}: Request failed")
        
        success = successful_updates == len(updates)
        self.log_test("Multiple DateTime Updates Sequence", success, 
                     f"- {successful_updates}/{len(updates)} updates successful")
        return success

    def test_verify_calendar_reflects_updated_times(self):
        """Test that calendar API reflects updated lesson times"""
        if not self.test_lesson_id:
            self.log_test("Calendar Reflects Updated Times", False, "- No test lesson available")
            return False
            
        # Get current lesson details
        success, current_lesson = self.make_request('GET', f'lessons/{self.test_lesson_id}', expected_status=200)
        if not success:
            self.log_test("Calendar Reflects Updated Times", False, "- Failed to get current lesson")
            return False
            
        current_start = current_lesson.get('start_datetime')
        lesson_date = datetime.fromisoformat(current_start.replace('Z', '')).date()
        
        # Get daily calendar for the lesson date
        date_str = lesson_date.strftime('%Y-%m-%d')
        success, calendar_response = self.make_request('GET', f'calendar/daily/{date_str}', expected_status=200)
        
        if success:
            calendar_lessons = calendar_response.get('lessons', [])
            
            # Find our lesson in the calendar
            lesson_found = False
            lesson_time_matches = False
            
            for calendar_lesson in calendar_lessons:
                if calendar_lesson.get('id') == self.test_lesson_id:
                    lesson_found = True
                    calendar_start = calendar_lesson.get('start_datetime')
                    lesson_time_matches = calendar_start == current_start
                    break
            
            success = success and lesson_found and lesson_time_matches
            
        self.log_test("Calendar Reflects Updated Times", success, 
                     f"- Lesson found in calendar: {lesson_found}, Time matches: {lesson_time_matches}")
        return success

    def test_lesson_retrieval_after_datetime_updates(self):
        """Test lesson retrieval after multiple datetime updates"""
        if not self.test_lesson_id:
            self.log_test("Lesson Retrieval After Updates", False, "- No test lesson available")
            return False
            
        # Get lesson by ID
        success, response = self.make_request('GET', f'lessons/{self.test_lesson_id}', expected_status=200)
        
        if success:
            lesson_id = response.get('id')
            student_name = response.get('student_name')
            teacher_names = response.get('teacher_names', [])
            start_datetime = response.get('start_datetime')
            end_datetime = response.get('end_datetime')
            booking_type = response.get('booking_type')
            notes = response.get('notes')
            
            # Verify all expected fields are present and valid
            fields_present = all([
                lesson_id == self.test_lesson_id,
                student_name,
                len(teacher_names) > 0,
                start_datetime,
                end_datetime,
                booking_type,
                notes
            ])
            
            # Verify datetime consistency
            start_dt = datetime.fromisoformat(start_datetime.replace('Z', ''))
            end_dt = datetime.fromisoformat(end_datetime.replace('Z', ''))
            datetime_consistent = end_dt > start_dt
            
            success = success and fields_present and datetime_consistent
            
        self.log_test("Lesson Retrieval After Updates", success, 
                     f"- All fields present: {fields_present}, DateTime consistent: {datetime_consistent}")
        return success

    def test_data_integrity_after_updates(self):
        """Test data integrity after multiple updates"""
        if not self.test_lesson_id:
            self.log_test("Data Integrity After Updates", False, "- No test lesson available")
            return False
            
        # Get lesson details
        success, lesson_response = self.make_request('GET', f'lessons/{self.test_lesson_id}', expected_status=200)
        if not success:
            self.log_test("Data Integrity After Updates", False, "- Failed to get lesson")
            return False
            
        # Get student details
        success, student_response = self.make_request('GET', f'students/{self.created_student_id}', expected_status=200)
        if not success:
            self.log_test("Data Integrity After Updates", False, "- Failed to get student")
            return False
            
        # Get enrollment details
        success, enrollment_response = self.make_request('GET', f'students/{self.created_student_id}/enrollments', expected_status=200)
        if not success:
            self.log_test("Data Integrity After Updates", False, "- Failed to get enrollments")
            return False
            
        # Verify data relationships are intact
        lesson_student_id = lesson_response.get('student_id')
        lesson_enrollment_id = lesson_response.get('enrollment_id')
        student_id = student_response.get('id')
        
        enrollments = enrollment_response if isinstance(enrollment_response, list) else []
        enrollment_found = any(e.get('id') == lesson_enrollment_id for e in enrollments)
        
        # Verify integrity
        student_relationship_intact = lesson_student_id == student_id == self.created_student_id
        enrollment_relationship_intact = enrollment_found
        
        success = student_relationship_intact and enrollment_relationship_intact
        
        self.log_test("Data Integrity After Updates", success, 
                     f"- Student relationship: {student_relationship_intact}, Enrollment relationship: {enrollment_relationship_intact}")
        return success

    def run_all_tests(self):
        """Run all enhanced lesson time edit tests"""
        print("🚀 Starting Enhanced Lesson Time Edit Functionality Tests")
        print("=" * 70)
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Aborting tests.")
            return
        
        # Test sequence
        test_methods = [
            self.test_create_initial_lesson,
            self.test_update_lesson_start_datetime_different_date,
            self.test_update_lesson_start_datetime_different_time,
            self.test_update_lesson_datetime_and_duration,
            self.test_update_lesson_datetime_with_multiple_instructors,
            self.test_update_lesson_datetime_with_booking_type,
            self.test_update_lesson_all_fields_simultaneously,
            self.test_update_lesson_to_same_datetime,
            self.test_update_lesson_invalid_datetime_format,
            self.test_multiple_datetime_updates_sequence,
            self.test_verify_calendar_reflects_updated_times,
            self.test_lesson_retrieval_after_datetime_updates,
            self.test_data_integrity_after_updates
        ]
        
        # Run all tests
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ {test_method.__name__} - ERROR: {str(e)}")
                self.tests_run += 1
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 ENHANCED LESSON TIME EDIT TESTING SUMMARY")
        print("=" * 70)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Enhanced lesson time edit functionality is working perfectly!")
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} test(s) failed. Please review the issues above.")
        
        print("=" * 70)

if __name__ == "__main__":
    tester = EnhancedLessonTimeEditTester()
    tester.run_all_tests()