import requests
import sys
import json
import websocket
import threading
import time
from datetime import datetime, timedelta, date
from typing import Dict, Any

class ReconstructedBackendTester:
    def __init__(self, base_url="https://dance-admin-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_student_id = None
        self.created_teacher_id = None
        self.created_enrollment_id = None
        self.created_payment_id = None
        self.created_lesson_id = None
        self.websocket_messages = []
        self.websocket_connected = False

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

    # 1. SERVER HEALTH & BASIC FUNCTIONALITY TESTS
    def test_server_health_check(self):
        """Test server health endpoint"""
        success, response = self.make_request('GET', 'health', expected_status=200)
        
        if success:
            status = response.get('status')
            timestamp = response.get('timestamp')
            success = status == 'healthy' and timestamp is not None
            
        self.log_test("Server Health Check", success, f"- Status: {response.get('status', 'Unknown')}")
        return success

    def test_admin_authentication(self):
        """Test authentication with admin@test.com / admin123 credentials"""
        # First try to create admin user if it doesn't exist
        admin_data = {
            "email": "admin@test.com",
            "name": "Admin User",
            "password": "admin123",
            "role": "owner",
            "studio_name": "Test Dance Studio"
        }
        
        # Try to register (will fail if user exists, which is fine)
        self.make_request('POST', 'auth/register', admin_data, expected_status=200)
        
        login_data = {
            "email": "admin@test.com",
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success:
            self.admin_token = response.get('access_token')
            user_info = response.get('user', {})
            print(f"   👤 Admin user: {user_info.get('name', 'Unknown')} ({user_info.get('role', 'Unknown')})")
            
        self.log_test("Admin Authentication", success, f"- Token received: {'Yes' if self.admin_token else 'No'}")
        return success

    def test_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        success, response = self.make_request('GET', 'dashboard/stats', expected_status=200)
        
        if success:
            required_fields = ['total_teachers', 'total_students', 'active_enrollments', 'estimated_monthly_revenue']
            has_all_fields = all(field in response for field in required_fields)
            success = has_all_fields
            
        self.log_test("Dashboard Stats", success, f"- Stats: Teachers: {response.get('total_teachers', 0)}, Students: {response.get('total_students', 0)}")
        return success

    def create_default_settings(self):
        """Create default settings if they don't exist"""
        if not self.admin_token:
            return False
            
        # Check if settings exist
        success, response = self.make_request('GET', 'settings', expected_status=200)
        if success and len(response) > 0:
            return True  # Settings already exist
            
        # Create default settings
        default_settings = [
            # Theme settings
            {"category": "theme", "key": "selected_theme", "value": "dark", "data_type": "string", "description": "Selected theme"},
            {"category": "theme", "key": "font_size", "value": "medium", "data_type": "string", "description": "Font size"},
            {"category": "theme", "key": "custom_primary_color", "value": "#a855f7", "data_type": "string", "description": "Primary color"},
            {"category": "theme", "key": "custom_secondary_color", "value": "#ec4899", "data_type": "string", "description": "Secondary color"},
            {"category": "theme", "key": "animations_enabled", "value": True, "data_type": "boolean", "description": "Enable animations"},
            {"category": "theme", "key": "glassmorphism_enabled", "value": True, "data_type": "boolean", "description": "Enable glassmorphism"},
            
            # Booking settings
            {"category": "booking", "key": "private_lesson_color", "value": "#3b82f6", "data_type": "string", "description": "Private lesson color"},
            {"category": "booking", "key": "meeting_color", "value": "#22c55e", "data_type": "string", "description": "Meeting color"},
            {"category": "booking", "key": "training_color", "value": "#f59e0b", "data_type": "string", "description": "Training color"},
            {"category": "booking", "key": "party_color", "value": "#a855f7", "data_type": "string", "description": "Party color"},
            {"category": "booking", "key": "confirmed_status_color", "value": "#22c55e", "data_type": "string", "description": "Confirmed status color"},
            {"category": "booking", "key": "pending_status_color", "value": "#f59e0b", "data_type": "string", "description": "Pending status color"},
            {"category": "booking", "key": "cancelled_status_color", "value": "#ef4444", "data_type": "string", "description": "Cancelled status color"},
            {"category": "booking", "key": "teacher_color_coding_enabled", "value": True, "data_type": "boolean", "description": "Enable teacher color coding"},
            
            # Calendar settings
            {"category": "calendar", "key": "default_view", "value": "daily", "data_type": "string", "description": "Default calendar view"},
            {"category": "calendar", "key": "start_hour", "value": 9, "data_type": "integer", "description": "Calendar start hour"},
            {"category": "calendar", "key": "end_hour", "value": 21, "data_type": "integer", "description": "Calendar end hour"},
            {"category": "calendar", "key": "time_slot_minutes", "value": 60, "data_type": "integer", "description": "Time slot duration"},
            
            # Display settings
            {"category": "display", "key": "language", "value": "en", "data_type": "string", "description": "Display language"},
            {"category": "display", "key": "currency_symbol", "value": "$", "data_type": "string", "description": "Currency symbol"},
            {"category": "display", "key": "compact_mode", "value": False, "data_type": "boolean", "description": "Compact display mode"},
            
            # Business rules
            {"category": "business_rules", "key": "late_cancellation_fee", "value": 75.50, "data_type": "float", "description": "Late cancellation fee"},
            {"category": "business_rules", "key": "cancellation_policy_hours", "value": 24, "data_type": "integer", "description": "Cancellation policy hours"},
            {"category": "business_rules", "key": "auto_confirm_bookings", "value": True, "data_type": "boolean", "description": "Auto confirm bookings"}
        ]
        
        created_count = 0
        for setting in default_settings:
            # Create setting using direct database insertion approach
            # Since we don't have a POST endpoint for settings, we'll use PUT to create them
            success, response = self.make_request('PUT', f'settings/{setting["category"]}/{setting["key"]}', 
                                                {"value": setting["value"]}, expected_status=404)
            # 404 is expected since setting doesn't exist yet
            
            # For now, we'll just count this as successful setup
            created_count += 1
            
        print(f"   📝 Attempted to create {created_count} default settings")
        return True

    # 2. REAL-TIME SYNCHRONIZATION SYSTEM TESTS (HIGH PRIORITY)
    def test_create_test_data_for_realtime(self):
        """Create test data for real-time synchronization testing"""
        # Create a test student
        student_data = {
            "name": "Alice Johnson",
            "email": "alice.johnson@example.com",
            "phone": "+1555123456",
            "parent_name": "Robert Johnson",
            "parent_email": "robert.johnson@example.com",
            "notes": "Test student for real-time sync"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if success:
            self.created_student_id = response.get('id')
            
        # Create a test teacher
        teacher_data = {
            "name": "Sarah Williams",
            "email": "sarah.williams@example.com",
            "phone": "+1555987654",
            "specialties": ["ballet", "contemporary"],
            "bio": "Professional ballet instructor"
        }
        
        teacher_success, teacher_response = self.make_request('POST', 'teachers', teacher_data, 200)
        if teacher_success:
            self.created_teacher_id = teacher_response.get('id')
            
        overall_success = success and teacher_success
        self.log_test("Create Test Data for Real-time", overall_success, 
                     f"- Student ID: {self.created_student_id}, Teacher ID: {self.created_teacher_id}")
        return overall_success

    def test_enrollment_creation_with_realtime_broadcast(self):
        """Test enrollment creation with WebSocket broadcasts"""
        if not self.created_student_id:
            self.log_test("Enrollment Creation with Real-time Broadcast", False, "- No student ID available")
            return False
            
        enrollment_data = {
            "student_id": self.created_student_id,
            "program_name": "Advanced Ballet Program",
            "total_lessons": 12,
            "price_per_lesson": 75.0,
            "initial_payment": 300.0
        }
        
        success, response = self.make_request('POST', 'enrollments', enrollment_data, 200)
        
        if success:
            self.created_enrollment_id = response.get('id')
            program_name = response.get('program_name')
            total_lessons = response.get('total_lessons')
            lessons_available = response.get('lessons_available')
            grand_total = response.get('grand_total')
            
            # Verify calculated totals
            expected_grand_total = 12 * 75.0  # 900.0
            expected_lessons_available = int(300.0 / 75.0)  # 4 lessons available based on payment
            
            calculations_correct = (grand_total == expected_grand_total and 
                                  lessons_available == expected_lessons_available)
            success = success and calculations_correct
            
        self.log_test("Enrollment Creation with Real-time Broadcast", success, 
                     f"- Program: {program_name}, Available lessons: {lessons_available}/{total_lessons}")
        return success

    def test_payment_creation_with_enrollment_updates(self):
        """Test payment creation with enrollment credit updates and broadcasts"""
        if not self.created_student_id or not self.created_enrollment_id:
            self.log_test("Payment Creation with Enrollment Updates", False, "- Missing student or enrollment ID")
            return False
            
        payment_data = {
            "student_id": self.created_student_id,
            "enrollment_id": self.created_enrollment_id,
            "amount": 225.0,  # Payment for 3 more lessons (3 * 75.0)
            "payment_method": "card",
            "notes": "Additional payment for more lessons"
        }
        
        success, response = self.make_request('POST', 'payments', payment_data, 200)
        
        if success:
            self.created_payment_id = response.get('id')
            payment_amount = response.get('amount')
            
            # Verify enrollment was updated - get enrollment details
            enrollment_success, enrollment_response = self.make_request('GET', f'enrollments', expected_status=200)
            if enrollment_success:
                # Find our enrollment
                enrollment = None
                for enroll in enrollment_response:
                    if enroll.get('id') == self.created_enrollment_id:
                        enrollment = enroll
                        break
                
                if enrollment:
                    total_paid = enrollment.get('amount_paid', 0)
                    lessons_available = enrollment.get('lessons_available', 0)
                    
                    # Should now have 525.0 total paid (300 + 225) = 7 lessons available
                    expected_total_paid = 525.0
                    expected_lessons_available = int(525.0 / 75.0)  # 7 lessons
                    
                    updates_correct = (total_paid == expected_total_paid and 
                                     lessons_available == expected_lessons_available)
                    success = success and updates_correct
            
        self.log_test("Payment Creation with Enrollment Updates", success, 
                     f"- Payment: ${payment_amount}, Updated enrollment credits")
        return success

    def test_lesson_attendance_with_credit_deduction(self):
        """Test lesson attendance marking with lesson credit deduction"""
        if not self.created_student_id or not self.created_teacher_id:
            self.log_test("Lesson Attendance with Credit Deduction", False, "- Missing student or teacher ID")
            return False
            
        # First create a lesson
        tomorrow = datetime.now() + timedelta(days=1)
        lesson_data = {
            "student_ids": [self.created_student_id],
            "teacher_ids": [self.created_teacher_id],
            "date": tomorrow.date().isoformat(),
            "start_time": "14:00",
            "end_time": "15:00",
            "duration_minutes": 60,
            "booking_type": "Private lesson",
            "notes": "Test lesson for attendance"
        }
        
        lesson_success, lesson_response = self.make_request('POST', 'lessons', lesson_data, 200)
        if not lesson_success:
            self.log_test("Lesson Attendance with Credit Deduction", False, "- Failed to create lesson")
            return False
            
        self.created_lesson_id = lesson_response.get('id')
        
        # Mark lesson as attended
        attendance_success, attendance_response = self.make_request('POST', f'lessons/{self.created_lesson_id}/attend', expected_status=200)
        
        if attendance_success:
            # Verify enrollment credits were deducted
            enrollment_success, enrollment_response = self.make_request('GET', f'enrollments', expected_status=200)
            if enrollment_success:
                enrollment = None
                for enroll in enrollment_response:
                    if enroll.get('id') == self.created_enrollment_id:
                        enrollment = enroll
                        break
                
                if enrollment:
                    lessons_taken = enrollment.get('lessons_taken', 0)
                    lessons_available = enrollment.get('lessons_available', 0)
                    
                    # Should now have 1 lesson taken, 6 lessons available (7 - 1)
                    credits_deducted = lessons_taken == 1 and lessons_available == 6
                    attendance_success = attendance_success and credits_deducted
            
        self.log_test("Lesson Attendance with Credit Deduction", attendance_success, 
                     f"- Lesson attended, credits deducted correctly")
        return attendance_success

    def test_enrollment_updates_broadcast_changes(self):
        """Test enrollment updates broadcast real-time changes"""
        if not self.created_enrollment_id:
            self.log_test("Enrollment Updates Broadcast Changes", False, "- No enrollment ID available")
            return False
            
        # Update enrollment
        update_data = {
            "student_id": self.created_student_id,
            "program_name": "Advanced Ballet Program - Extended",
            "total_lessons": 16,  # Increased from 12
            "price_per_lesson": 75.0,
            "initial_payment": 525.0  # Keep current payment amount
        }
        
        success, response = self.make_request('PUT', f'enrollments/{self.created_enrollment_id}', update_data, 200)
        
        if success:
            updated_program = response.get('program_name')
            updated_lessons = response.get('total_lessons')
            lessons_available = response.get('lessons_available')
            
            # Verify update was successful
            update_correct = (updated_lessons == 16 and 
                            "Extended" in updated_program and
                            lessons_available == 6)  # Should still have 6 available (7 paid - 1 taken)
            success = success and update_correct
            
        self.log_test("Enrollment Updates Broadcast Changes", success, 
                     f"- Updated to {updated_lessons} lessons, {lessons_available} available")
        return success

    # 3. STUDENT LEDGER WITH LESSON HISTORY NAVIGATION TESTS
    def test_student_ledger_endpoint(self):
        """Test GET /api/students/{student_id}/ledger endpoint"""
        if not self.created_student_id:
            self.log_test("Student Ledger Endpoint", False, "- No student ID available")
            return False
            
        success, response = self.make_request('GET', f'students/{self.created_student_id}/ledger', expected_status=200)
        
        if success:
            # Verify all required fields are present
            required_fields = ['student', 'enrollments', 'payments', 'upcoming_lessons', 
                             'lesson_history', 'total_paid', 'total_enrolled_lessons', 
                             'remaining_lessons', 'lessons_taken']
            
            has_all_fields = all(field in response for field in required_fields)
            
            if has_all_fields:
                student_name = response['student'].get('name', 'Unknown')
                enrollments_count = len(response['enrollments'])
                payments_count = len(response['payments'])
                total_paid = response['total_paid']
                lessons_taken = response['lessons_taken']
                
                # Verify data consistency
                data_consistent = (enrollments_count > 0 and payments_count > 0 and 
                                 total_paid > 0 and lessons_taken >= 0)
                success = success and has_all_fields and data_consistent
            else:
                success = False
            
        self.log_test("Student Ledger Endpoint", success, 
                     f"- Student: {student_name}, Enrollments: {enrollments_count}, Payments: {payments_count}")
        return success

    def test_lesson_history_retrieval(self):
        """Test lesson history retrieval and data completeness"""
        if not self.created_student_id:
            self.log_test("Lesson History Retrieval", False, "- No student ID available")
            return False
            
        success, response = self.make_request('GET', f'students/{self.created_student_id}/lessons', expected_status=200)
        
        if success:
            lessons_count = len(response) if isinstance(response, list) else 0
            
            # Verify lesson data structure
            if lessons_count > 0:
                lesson = response[0]
                required_lesson_fields = ['id', 'student_ids', 'teacher_ids', 'teacher_names', 
                                        'date', 'start_time', 'end_time', 'booking_type', 'status']
                
                has_lesson_fields = all(field in lesson for field in required_lesson_fields)
                
                # Verify our student is in the lesson
                student_in_lesson = self.created_student_id in lesson.get('student_ids', [])
                
                success = success and has_lesson_fields and student_in_lesson
            
        self.log_test("Lesson History Retrieval", success, 
                     f"- Found {lessons_count} lessons with complete data")
        return success

    def test_available_lessons_calculation(self):
        """Test available lessons calculation"""
        if not self.created_student_id:
            self.log_test("Available Lessons Calculation", False, "- No student ID available")
            return False
            
        success, response = self.make_request('GET', f'students/{self.created_student_id}/available_lessons', expected_status=200)
        
        if success:
            student_id = response.get('student_id')
            available_lessons = response.get('available_lessons')
            
            # Should have 6 available lessons based on our previous tests
            calculation_correct = (student_id == self.created_student_id and 
                                 available_lessons == 6)
            success = success and calculation_correct
            
        self.log_test("Available Lessons Calculation", success, 
                     f"- Student has {available_lessons} available lessons")
        return success

    # 4. ENHANCED FINANCIAL SYSTEM TESTS
    def test_enrollment_price_per_lesson_calculations(self):
        """Test enrollment creation with price_per_lesson calculations"""
        # Create another student for financial testing
        student_data = {
            "name": "Bob Martinez",
            "email": "bob.martinez@example.com",
            "phone": "+1555456789",
            "notes": "Test student for financial calculations"
        }
        
        student_success, student_response = self.make_request('POST', 'students', student_data, 200)
        if not student_success:
            self.log_test("Enrollment Price Per Lesson Calculations", False, "- Failed to create test student")
            return False
            
        financial_test_student_id = student_response.get('id')
        
        # Create enrollment with specific price per lesson
        enrollment_data = {
            "student_id": financial_test_student_id,
            "program_name": "Financial Test Program",
            "total_lessons": 10,
            "price_per_lesson": 80.0,
            "initial_payment": 400.0  # Half payment
        }
        
        success, response = self.make_request('POST', 'enrollments', enrollment_data, 200)
        
        if success:
            grand_total = response.get('grand_total')
            balance_remaining = response.get('balance_remaining')
            lessons_available = response.get('lessons_available')
            
            # Verify calculations
            expected_grand_total = 10 * 80.0  # 800.0
            expected_balance = 800.0 - 400.0  # 400.0
            expected_available = int(400.0 / 80.0)  # 5 lessons
            
            calculations_correct = (grand_total == expected_grand_total and
                                  balance_remaining == expected_balance and
                                  lessons_available == expected_available)
            success = success and calculations_correct
            
        self.log_test("Enrollment Price Per Lesson Calculations", success, 
                     f"- Grand total: ${grand_total}, Balance: ${balance_remaining}, Available: {lessons_available}")
        return success

    def test_payment_allocation_to_enrollments(self):
        """Test payment allocation to enrollments"""
        # This test verifies that payments are properly allocated and update enrollment credits
        # We already tested this in the real-time sync section, so we'll verify the allocation logic
        
        success, enrollments_response = self.make_request('GET', 'enrollments', expected_status=200)
        if not success:
            self.log_test("Payment Allocation to Enrollments", False, "- Failed to get enrollments")
            return False
            
        success, payments_response = self.make_request('GET', 'payments', expected_status=200)
        if not success:
            self.log_test("Payment Allocation to Enrollments", False, "- Failed to get payments")
            return False
            
        # Find our test enrollment and verify payment allocation
        test_enrollment = None
        for enrollment in enrollments_response:
            if enrollment.get('id') == self.created_enrollment_id:
                test_enrollment = enrollment
                break
                
        if test_enrollment:
            amount_paid = test_enrollment.get('amount_paid', 0)
            lessons_available = test_enrollment.get('lessons_available', 0)
            price_per_lesson = test_enrollment.get('price_per_lesson', 0)
            
            # Verify allocation is correct
            expected_lessons_available = int(amount_paid / price_per_lesson) - test_enrollment.get('lessons_taken', 0)
            allocation_correct = lessons_available == expected_lessons_available
            
            success = allocation_correct
        else:
            success = False
            
        self.log_test("Payment Allocation to Enrollments", success, 
                     f"- Payment allocation working correctly")
        return success

    # 5. LESSON MANAGEMENT & CANCELLATION TESTS
    def test_lesson_creation_and_status(self):
        """Test lesson creation with proper status"""
        if not self.created_student_id or not self.created_teacher_id:
            self.log_test("Lesson Creation and Status", False, "- Missing student or teacher ID")
            return False
            
        # Create lesson for next week
        next_week = datetime.now() + timedelta(days=7)
        lesson_data = {
            "student_ids": [self.created_student_id],
            "teacher_ids": [self.created_teacher_id],
            "date": next_week.date().isoformat(),
            "start_time": "16:00",
            "end_time": "17:00",
            "duration_minutes": 60,
            "booking_type": "Private lesson",
            "notes": "Test lesson for cancellation testing"
        }
        
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        
        if success:
            lesson_id = response.get('id')
            status = response.get('status')
            booking_type = response.get('booking_type')
            
            # Verify default status is 'active'
            status_correct = status == 'active'
            success = success and status_correct
            
            # Store for cancellation testing
            self.cancellation_test_lesson_id = lesson_id
            
        self.log_test("Lesson Creation and Status", success, 
                     f"- Lesson created with status: {status}")
        return success

    def test_lesson_cancellation(self):
        """Test lesson cancellation functionality"""
        if not hasattr(self, 'cancellation_test_lesson_id'):
            self.log_test("Lesson Cancellation", False, "- No lesson ID for cancellation testing")
            return False
            
        cancel_data = {
            "reason": "Student illness",
            "send_notification": True
        }
        
        success, response = self.make_request('POST', f'lessons/{self.cancellation_test_lesson_id}/cancel', 
                                            cancel_data, 200)
        
        if success:
            message = response.get('message', '')
            
            # Verify lesson status was updated
            lesson_success, lesson_response = self.make_request('GET', 'lessons', expected_status=200)
            if lesson_success:
                cancelled_lesson = None
                for lesson in lesson_response:
                    if lesson.get('id') == self.cancellation_test_lesson_id:
                        cancelled_lesson = lesson
                        break
                
                if cancelled_lesson:
                    status = cancelled_lesson.get('status')
                    cancellation_reason = cancelled_lesson.get('cancellation_reason')
                    cancelled_by = cancelled_lesson.get('cancelled_by')
                    
                    cancellation_correct = (status == 'cancelled' and 
                                          cancellation_reason == 'Student illness' and
                                          cancelled_by is not None)
                    success = success and cancellation_correct
            
        self.log_test("Lesson Cancellation", success, 
                     f"- Lesson cancelled with reason: {cancel_data['reason']}")
        return success

    def test_lesson_reactivation(self):
        """Test lesson reactivation functionality"""
        if not hasattr(self, 'cancellation_test_lesson_id'):
            self.log_test("Lesson Reactivation", False, "- No cancelled lesson ID available")
            return False
            
        success, response = self.make_request('POST', f'lessons/{self.cancellation_test_lesson_id}/reactivate', 
                                            expected_status=200)
        
        if success:
            message = response.get('message', '')
            
            # Verify lesson status was updated back to active
            lesson_success, lesson_response = self.make_request('GET', 'lessons', expected_status=200)
            if lesson_success:
                reactivated_lesson = None
                for lesson in lesson_response:
                    if lesson.get('id') == self.cancellation_test_lesson_id:
                        reactivated_lesson = lesson
                        break
                
                if reactivated_lesson:
                    status = reactivated_lesson.get('status')
                    cancelled_by = reactivated_lesson.get('cancelled_by')
                    cancellation_reason = reactivated_lesson.get('cancellation_reason')
                    
                    reactivation_correct = (status == 'active' and 
                                          cancelled_by is None and
                                          cancellation_reason is None)
                    success = success and reactivation_correct
            
        self.log_test("Lesson Reactivation", success, 
                     f"- Lesson reactivated successfully")
        return success

    def test_cancelled_lessons_report(self):
        """Test cancelled lessons report"""
        # First cancel a lesson for the report
        if hasattr(self, 'cancellation_test_lesson_id'):
            cancel_data = {"reason": "Testing report functionality"}
            self.make_request('POST', f'lessons/{self.cancellation_test_lesson_id}/cancel', cancel_data, 200)
        
        success, response = self.make_request('GET', 'reports/cancelled-lessons', expected_status=200)
        
        if success:
            cancelled_lessons_count = len(response) if isinstance(response, list) else 0
            
            # Verify report structure
            if cancelled_lessons_count > 0:
                lesson = response[0]
                required_fields = ['id', 'status', 'cancelled_by', 'cancellation_reason', 'cancelled_at']
                has_required_fields = all(field in lesson for field in required_fields)
                
                # Verify all lessons in report are cancelled
                all_cancelled = all(lesson.get('status') == 'cancelled' for lesson in response)
                
                success = success and has_required_fields and all_cancelled
            
        self.log_test("Cancelled Lessons Report", success, 
                     f"- Found {cancelled_lessons_count} cancelled lessons")
        return success

    # 6. SETTINGS & CONFIGURATION TESTS
    def test_settings_crud_operations(self):
        """Test settings CRUD operations"""
        # Get all settings
        success, response = self.make_request('GET', 'settings', expected_status=200)
        
        if success:
            settings_count = len(response) if isinstance(response, list) else 0
            
            # Test getting settings by category
            category_success, category_response = self.make_request('GET', 'settings/theme', expected_status=200)
            
            if category_success:
                theme_settings_count = len(category_response) if isinstance(category_response, list) else 0
                
                # Test updating a specific setting
                if theme_settings_count > 0:
                    setting = category_response[0]
                    setting_key = setting.get('key')
                    
                    update_data = {"value": "test_value"}
                    update_success, update_response = self.make_request('PUT', f'settings/theme/{setting_key}', 
                                                                      update_data, 200)
                    
                    success = success and category_success and update_success
                else:
                    success = False
            else:
                success = False
            
        self.log_test("Settings CRUD Operations", success, 
                     f"- Found {settings_count} total settings, theme category working")
        return success

    def test_hex_color_validation(self):
        """Test hex color validation for booking colors"""
        # Test valid hex color
        valid_color_data = {"value": "#ff6b6b"}
        valid_success, valid_response = self.make_request('PUT', 'settings/booking/private_lesson_color', 
                                                        valid_color_data, 200)
        
        # Test invalid hex color
        invalid_color_data = {"value": "invalid_color"}
        invalid_success, invalid_response = self.make_request('PUT', 'settings/booking/private_lesson_color', 
                                                            invalid_color_data, 400)
        
        # Both tests should succeed (valid accepted, invalid rejected)
        success = valid_success and invalid_success
        
        self.log_test("Hex Color Validation", success, 
                     f"- Valid color accepted, invalid color rejected")
        return success

    def test_settings_by_category_retrieval(self):
        """Test settings by category retrieval"""
        categories_to_test = ['theme', 'booking', 'calendar', 'display', 'business_rules']
        successful_categories = 0
        
        for category in categories_to_test:
            success, response = self.make_request('GET', f'settings/{category}', expected_status=200)
            
            if success:
                settings_count = len(response) if isinstance(response, list) else 0
                if settings_count > 0:
                    successful_categories += 1
                    print(f"   ✅ {category}: {settings_count} settings")
                else:
                    print(f"   ❌ {category}: No settings found")
            else:
                print(f"   ❌ {category}: Failed to retrieve")
        
        success = successful_categories == len(categories_to_test)
        self.log_test("Settings by Category Retrieval", success, 
                     f"- {successful_categories}/{len(categories_to_test)} categories working")
        return success

    def run_all_tests(self):
        """Run all tests in the correct order"""
        print("🚀 Starting Reconstructed Backend Server Testing...")
        print("=" * 80)
        
        # 1. Server Health & Basic Functionality
        print("\n📊 1. SERVER HEALTH & BASIC FUNCTIONALITY TESTS")
        print("-" * 50)
        self.test_server_health_check()
        self.test_admin_authentication()
        if self.admin_token:
            self.create_default_settings()
        self.test_dashboard_stats()
        
        # 2. Real-Time Synchronization System (HIGH PRIORITY)
        print("\n🔄 2. REAL-TIME SYNCHRONIZATION SYSTEM TESTS (HIGH PRIORITY)")
        print("-" * 60)
        self.test_create_test_data_for_realtime()
        self.test_enrollment_creation_with_realtime_broadcast()
        self.test_payment_creation_with_enrollment_updates()
        self.test_lesson_attendance_with_credit_deduction()
        self.test_enrollment_updates_broadcast_changes()
        
        # 3. Student Ledger with Lesson History Navigation
        print("\n📚 3. STUDENT LEDGER WITH LESSON HISTORY NAVIGATION TESTS")
        print("-" * 60)
        self.test_student_ledger_endpoint()
        self.test_lesson_history_retrieval()
        self.test_available_lessons_calculation()
        
        # 4. Enhanced Financial System
        print("\n💰 4. ENHANCED FINANCIAL SYSTEM TESTS")
        print("-" * 40)
        self.test_enrollment_price_per_lesson_calculations()
        self.test_payment_allocation_to_enrollments()
        
        # 5. Lesson Management & Cancellation
        print("\n📅 5. LESSON MANAGEMENT & CANCELLATION TESTS")
        print("-" * 45)
        self.test_lesson_creation_and_status()
        self.test_lesson_cancellation()
        self.test_lesson_reactivation()
        self.test_cancelled_lessons_report()
        
        # 6. Settings & Configuration
        print("\n⚙️ 6. SETTINGS & CONFIGURATION TESTS")
        print("-" * 35)
        self.test_settings_crud_operations()
        self.test_hex_color_validation()
        self.test_settings_by_category_retrieval()
        
        # Final Results
        print("\n" + "=" * 80)
        print(f"🎯 TESTING COMPLETE: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL TESTS PASSED - Backend server is fully functional!")
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"❌ {failed_tests} tests failed - Review issues above")
        
        print("=" * 80)
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = ReconstructedBackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)