import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any

class StudentLedgerTester:
    def __init__(self, base_url="https://rhythm-scheduler-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # Test data storage
        self.test_student_id = None
        self.test_teacher_id = None
        self.test_enrollment_ids = []
        self.test_payment_ids = []
        self.test_lesson_ids = []

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
        """Setup authentication and test data"""
        print("\n🔧 Setting up test data...")
        
        # Register and login
        timestamp = datetime.now().strftime("%H%M%S")
        user_data = {
            "email": f"ledger_test_{timestamp}@example.com",
            "name": f"Ledger Test User {timestamp}",
            "password": "TestPassword123!",
            "role": "owner",
            "studio_name": "Test Dance Studio"
        }
        
        success, response = self.make_request('POST', 'auth/register', user_data, 200)
        if not success:
            print("❌ Failed to register test user")
            return False
            
        self.user_id = response.get('id')
        
        # Login
        login_data = {
            "email": user_data['email'],
            "password": user_data['password']
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        if not success:
            print("❌ Failed to login test user")
            return False
            
        self.token = response.get('access_token')
        
        # Create test student
        student_data = {
            "name": "Isabella Martinez",
            "email": "isabella.martinez@example.com",
            "phone": "+1555123456",
            "parent_name": "Carmen Martinez",
            "parent_phone": "+1555123457",
            "parent_email": "carmen.martinez@example.com",
            "notes": "Advanced student interested in competitive ballroom dancing"
        }
        
        success, response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            print("❌ Failed to create test student")
            return False
            
        self.test_student_id = response.get('id')
        
        # Create test teacher
        teacher_data = {
            "name": "Marco Rodriguez",
            "email": "marco.rodriguez@example.com",
            "phone": "+1555987654",
            "specialties": ["ballroom", "salsa"],
            "bio": "Professional ballroom dance instructor with 15+ years experience"
        }
        
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            print("❌ Failed to create test teacher")
            return False
            
        self.test_teacher_id = response.get('id')
        
        print(f"✅ Test data setup complete - Student: {self.test_student_id}, Teacher: {self.test_teacher_id}")
        return True

    def test_payment_creation_cash(self):
        """Test creating a cash payment"""
        payment_data = {
            "student_id": self.test_student_id,
            "amount": 250.00,
            "payment_method": "cash",
            "notes": "Cash payment for Bronze program enrollment"
        }
        
        success, response = self.make_request('POST', 'payments', payment_data, 200)
        
        if success:
            payment_id = response.get('id')
            self.test_payment_ids.append(payment_id)
            amount = response.get('amount')
            method = response.get('payment_method')
            
        self.log_test("Payment Creation - Cash", success, 
                     f"- Amount: ${amount}, Method: {method}")
        return success

    def test_payment_creation_credit_card(self):
        """Test creating a credit card payment"""
        payment_data = {
            "student_id": self.test_student_id,
            "amount": 400.00,
            "payment_method": "credit_card",
            "notes": "Credit card payment for Silver program"
        }
        
        success, response = self.make_request('POST', 'payments', payment_data, 200)
        
        if success:
            payment_id = response.get('id')
            self.test_payment_ids.append(payment_id)
            amount = response.get('amount')
            method = response.get('payment_method')
            
        self.log_test("Payment Creation - Credit Card", success, 
                     f"- Amount: ${amount}, Method: {method}")
        return success

    def test_payment_creation_check(self):
        """Test creating a check payment"""
        payment_data = {
            "student_id": self.test_student_id,
            "amount": 150.00,
            "payment_method": "check",
            "notes": "Check payment #1234 for additional lessons"
        }
        
        success, response = self.make_request('POST', 'payments', payment_data, 200)
        
        if success:
            payment_id = response.get('id')
            self.test_payment_ids.append(payment_id)
            amount = response.get('amount')
            method = response.get('payment_method')
            
        self.log_test("Payment Creation - Check", success, 
                     f"- Amount: ${amount}, Method: {method}")
        return success

    def test_payment_with_enrollment_link(self):
        """Test creating a payment linked to specific enrollment"""
        # First create an enrollment
        enrollment_data = {
            "student_id": self.test_student_id,
            "program_name": "Full Bronze",
            "total_lessons": 20,
            "total_paid": 800.00
        }
        
        success, enrollment_response = self.make_request('POST', 'enrollments', enrollment_data, 200)
        if not success:
            self.log_test("Payment with Enrollment Link", False, "- Failed to create enrollment")
            return False
            
        enrollment_id = enrollment_response.get('id')
        self.test_enrollment_ids.append(enrollment_id)
        
        # Create payment linked to enrollment
        payment_data = {
            "student_id": self.test_student_id,
            "enrollment_id": enrollment_id,
            "amount": 800.00,
            "payment_method": "credit_card",
            "notes": "Full payment for Bronze program enrollment"
        }
        
        success, response = self.make_request('POST', 'payments', payment_data, 200)
        
        if success:
            payment_id = response.get('id')
            self.test_payment_ids.append(payment_id)
            linked_enrollment = response.get('enrollment_id')
            amount = response.get('amount')
            
        self.log_test("Payment with Enrollment Link", success, 
                     f"- Amount: ${amount}, Linked to enrollment: {linked_enrollment == enrollment_id}")
        return success

    def test_get_all_payments(self):
        """Test retrieving all payments"""
        success, response = self.make_request('GET', 'payments', expected_status=200)
        
        if success:
            payments_count = len(response) if isinstance(response, list) else 0
            # Should have at least the payments we created
            has_our_payments = payments_count >= len(self.test_payment_ids)
            success = success and has_our_payments
            
        self.log_test("Get All Payments", success, f"- Found {payments_count} payments")
        return success

    def test_get_student_payments(self):
        """Test retrieving payments for specific student"""
        success, response = self.make_request('GET', f'students/{self.test_student_id}/payments', expected_status=200)
        
        if success:
            payments_count = len(response) if isinstance(response, list) else 0
            # Should have exactly the payments we created for this student
            expected_count = len(self.test_payment_ids)
            has_correct_count = payments_count == expected_count
            
            # Verify payment details
            total_amount = sum(payment.get('amount', 0) for payment in response)
            expected_total = 250.00 + 400.00 + 150.00 + 800.00  # Sum of all payments created
            
            success = success and has_correct_count and abs(total_amount - expected_total) < 0.01
            
        self.log_test("Get Student Payments", success, 
                     f"- Found {payments_count} payments, Total: ${total_amount}")
        return success

    def test_payment_deletion(self):
        """Test deleting a payment"""
        if not self.test_payment_ids:
            self.log_test("Payment Deletion", False, "- No payment IDs available")
            return False
            
        payment_id = self.test_payment_ids[0]
        success, response = self.make_request('DELETE', f'payments/{payment_id}', expected_status=200)
        
        if success:
            message = response.get('message', '')
            # Remove from our tracking list
            self.test_payment_ids.remove(payment_id)
            
        self.log_test("Payment Deletion", success, f"- Message: {message}")
        return success

    def test_create_multiple_enrollments(self):
        """Test creating multiple enrollments for comprehensive ledger testing"""
        enrollments_data = [
            {
                "program_name": "Beginner Silver",
                "total_lessons": 15,
                "total_paid": 600.00
            },
            {
                "program_name": "Intermediate Bronze",
                "total_lessons": 12,
                "total_paid": 480.00
            },
            {
                "program_name": "Wedding Dance Preparation",
                "total_lessons": 8,
                "total_paid": 400.00
            }
        ]
        
        successful_enrollments = 0
        
        for enrollment_data in enrollments_data:
            enrollment_data["student_id"] = self.test_student_id
            
            success, response = self.make_request('POST', 'enrollments', enrollment_data, 200)
            
            if success:
                enrollment_id = response.get('id')
                self.test_enrollment_ids.append(enrollment_id)
                successful_enrollments += 1
                program_name = response.get('program_name')
                total_lessons = response.get('total_lessons')
                print(f"   ✅ Created enrollment: {program_name} ({total_lessons} lessons)")
            else:
                print(f"   ❌ Failed to create enrollment: {enrollment_data['program_name']}")
        
        success = successful_enrollments == len(enrollments_data)
        self.log_test("Create Multiple Enrollments", success, 
                     f"- Created {successful_enrollments}/{len(enrollments_data)} enrollments")
        return success

    def test_create_lessons_for_ledger(self):
        """Test creating lessons for comprehensive ledger testing"""
        if not self.test_enrollment_ids:
            self.log_test("Create Lessons for Ledger", False, "- No enrollment IDs available")
            return False
            
        # Create lessons - some past, some future, some attended
        lessons_data = [
            {
                "start_datetime": (datetime.now() - timedelta(days=7)).replace(hour=14, minute=0, second=0, microsecond=0),
                "notes": "Past lesson - Bronze technique",
                "attended": True
            },
            {
                "start_datetime": (datetime.now() - timedelta(days=3)).replace(hour=15, minute=0, second=0, microsecond=0),
                "notes": "Past lesson - Silver patterns",
                "attended": True
            },
            {
                "start_datetime": (datetime.now() - timedelta(days=1)).replace(hour=16, minute=0, second=0, microsecond=0),
                "notes": "Recent lesson - Wedding dance prep",
                "attended": False
            },
            {
                "start_datetime": (datetime.now() + timedelta(days=2)).replace(hour=14, minute=0, second=0, microsecond=0),
                "notes": "Upcoming lesson - Advanced technique",
                "attended": False
            },
            {
                "start_datetime": (datetime.now() + timedelta(days=5)).replace(hour=15, minute=30, second=0, microsecond=0),
                "notes": "Future lesson - Competition preparation",
                "attended": False
            }
        ]
        
        successful_lessons = 0
        
        for i, lesson_data in enumerate(lessons_data):
            # Create lesson
            lesson_create_data = {
                "student_id": self.test_student_id,
                "teacher_id": self.test_teacher_id,
                "start_datetime": lesson_data["start_datetime"].isoformat(),
                "duration_minutes": 60,
                "notes": lesson_data["notes"],
                "enrollment_id": self.test_enrollment_ids[i % len(self.test_enrollment_ids)]
            }
            
            success, response = self.make_request('POST', 'lessons', lesson_create_data, 200)
            
            if success:
                lesson_id = response.get('id')
                self.test_lesson_ids.append(lesson_id)
                
                # Mark as attended if specified
                if lesson_data["attended"]:
                    attend_success, _ = self.make_request('POST', f'lessons/{lesson_id}/attend', expected_status=200)
                    if attend_success:
                        print(f"   ✅ Lesson marked as attended: {lesson_data['notes']}")
                    else:
                        print(f"   ⚠️ Failed to mark lesson as attended: {lesson_data['notes']}")
                
                successful_lessons += 1
                print(f"   ✅ Created lesson: {lesson_data['notes']}")
            else:
                print(f"   ❌ Failed to create lesson: {lesson_data['notes']}")
        
        success = successful_lessons == len(lessons_data)
        self.log_test("Create Lessons for Ledger", success, 
                     f"- Created {successful_lessons}/{len(lessons_data)} lessons")
        return success

    def test_comprehensive_student_ledger(self):
        """Test comprehensive student ledger retrieval"""
        success, response = self.make_request('GET', f'students/{self.test_student_id}/ledger', expected_status=200)
        
        if success:
            # Verify ledger structure
            required_fields = ['student', 'enrollments', 'payments', 'upcoming_lessons', 
                             'lesson_history', 'total_paid', 'total_enrolled_lessons', 
                             'remaining_lessons', 'lessons_taken']
            
            has_all_fields = all(field in response for field in required_fields)
            
            if has_all_fields:
                student = response.get('student', {})
                enrollments = response.get('enrollments', [])
                payments = response.get('payments', [])
                upcoming_lessons = response.get('upcoming_lessons', [])
                lesson_history = response.get('lesson_history', [])
                
                total_paid = response.get('total_paid', 0)
                total_enrolled_lessons = response.get('total_enrolled_lessons', 0)
                remaining_lessons = response.get('remaining_lessons', 0)
                lessons_taken = response.get('lessons_taken', 0)
                
                # Verify student details
                student_name = student.get('name', '')
                is_correct_student = student_name == "Isabella Martinez"
                
                # Verify counts
                enrollments_count = len(enrollments)
                payments_count = len(payments)
                upcoming_count = len(upcoming_lessons)
                history_count = len(lesson_history)
                
                # Expected values based on our test data
                expected_enrollments = len(self.test_enrollment_ids)  # Should be 4 (1 + 3)
                expected_payments = len(self.test_payment_ids)  # Should be 3 (after deletion)
                expected_total_paid = 400.00 + 150.00 + 800.00 + 600.00 + 480.00 + 400.00  # Remaining payments + enrollments
                
                success = (has_all_fields and is_correct_student and 
                          enrollments_count >= expected_enrollments and
                          payments_count >= expected_payments and
                          total_paid > 0 and total_enrolled_lessons > 0)
                
                print(f"   📊 Ledger Summary:")
                print(f"   - Student: {student_name}")
                print(f"   - Enrollments: {enrollments_count}")
                print(f"   - Payments: {payments_count}")
                print(f"   - Total Paid: ${total_paid}")
                print(f"   - Total Enrolled Lessons: {total_enrolled_lessons}")
                print(f"   - Remaining Lessons: {remaining_lessons}")
                print(f"   - Lessons Taken: {lessons_taken}")
                print(f"   - Upcoming Lessons: {upcoming_count}")
                print(f"   - Lesson History: {history_count}")
            else:
                success = False
                
        self.log_test("Comprehensive Student Ledger", success, 
                     f"- All required fields present: {has_all_fields}")
        return success

    def test_ledger_financial_calculations(self):
        """Test accuracy of financial calculations in ledger"""
        success, response = self.make_request('GET', f'students/{self.test_student_id}/ledger', expected_status=200)
        
        if success:
            payments = response.get('payments', [])
            enrollments = response.get('enrollments', [])
            
            # Calculate expected totals manually
            manual_total_paid = sum(payment.get('amount', 0) for payment in payments)
            manual_total_lessons = sum(enrollment.get('total_lessons', 0) for enrollment in enrollments)
            manual_remaining_lessons = sum(enrollment.get('remaining_lessons', 0) 
                                         for enrollment in enrollments 
                                         if enrollment.get('is_active', True))
            
            # Get ledger calculations
            ledger_total_paid = response.get('total_paid', 0)
            ledger_total_lessons = response.get('total_enrolled_lessons', 0)
            ledger_remaining_lessons = response.get('remaining_lessons', 0)
            
            # Verify calculations match
            paid_matches = abs(manual_total_paid - ledger_total_paid) < 0.01
            lessons_match = manual_total_lessons == ledger_total_lessons
            remaining_match = manual_remaining_lessons == ledger_remaining_lessons
            
            success = paid_matches and lessons_match and remaining_match
            
            print(f"   💰 Financial Verification:")
            print(f"   - Total Paid: Manual=${manual_total_paid}, Ledger=${ledger_total_paid} ({'✅' if paid_matches else '❌'})")
            print(f"   - Total Lessons: Manual={manual_total_lessons}, Ledger={ledger_total_lessons} ({'✅' if lessons_match else '❌'})")
            print(f"   - Remaining: Manual={manual_remaining_lessons}, Ledger={ledger_remaining_lessons} ({'✅' if remaining_match else '❌'})")
            
        self.log_test("Ledger Financial Calculations", success, 
                     f"- All calculations accurate: {success}")
        return success

    def test_ledger_lesson_filtering(self):
        """Test proper filtering of upcoming vs historical lessons"""
        success, response = self.make_request('GET', f'students/{self.test_student_id}/ledger', expected_status=200)
        
        if success:
            upcoming_lessons = response.get('upcoming_lessons', [])
            lesson_history = response.get('lesson_history', [])
            
            now = datetime.now()
            
            # Verify upcoming lessons are all in the future
            upcoming_valid = True
            for lesson in upcoming_lessons:
                lesson_time = datetime.fromisoformat(lesson.get('start_datetime', '').replace('Z', ''))
                if lesson_time <= now:
                    upcoming_valid = False
                    print(f"   ❌ Found past lesson in upcoming: {lesson.get('notes', '')}")
                    break
            
            # Verify historical lessons are all in the past
            history_valid = True
            for lesson in lesson_history:
                lesson_time = datetime.fromisoformat(lesson.get('start_datetime', '').replace('Z', ''))
                if lesson_time > now:
                    history_valid = False
                    print(f"   ❌ Found future lesson in history: {lesson.get('notes', '')}")
                    break
            
            success = upcoming_valid and history_valid
            
            print(f"   📅 Lesson Filtering:")
            print(f"   - Upcoming Lessons: {len(upcoming_lessons)} ({'✅' if upcoming_valid else '❌'})")
            print(f"   - Historical Lessons: {len(lesson_history)} ({'✅' if history_valid else '❌'})")
            
        self.log_test("Ledger Lesson Filtering", success, 
                     f"- Proper time-based filtering: {success}")
        return success

    def test_enrollment_deletion_from_ledger(self):
        """Test deleting enrollment from ledger interface"""
        if not self.test_enrollment_ids:
            self.log_test("Enrollment Deletion from Ledger", False, "- No enrollment IDs available")
            return False
            
        enrollment_id = self.test_enrollment_ids[0]
        success, response = self.make_request('DELETE', f'enrollments/{enrollment_id}', expected_status=200)
        
        if success:
            message = response.get('message', '')
            associated_lessons = response.get('associated_lessons', 0)
            note = response.get('note', '')
            
            # Remove from our tracking
            self.test_enrollment_ids.remove(enrollment_id)
            
            print(f"   🗑️ Enrollment Deletion:")
            print(f"   - Message: {message}")
            print(f"   - Associated Lessons: {associated_lessons}")
            print(f"   - Note: {note}")
            
        self.log_test("Enrollment Deletion from Ledger", success, 
                     f"- Enrollment deleted with {associated_lessons} associated lessons")
        return success

    def test_ledger_real_time_updates(self):
        """Test that ledger reflects real-time updates after operations"""
        # Get initial ledger state
        success, initial_response = self.make_request('GET', f'students/{self.test_student_id}/ledger', expected_status=200)
        if not success:
            self.log_test("Ledger Real-time Updates", False, "- Failed to get initial ledger")
            return False
            
        initial_payments_count = len(initial_response.get('payments', []))
        initial_total_paid = initial_response.get('total_paid', 0)
        
        # Add a new payment
        payment_data = {
            "student_id": self.test_student_id,
            "amount": 100.00,
            "payment_method": "cash",
            "notes": "Real-time update test payment"
        }
        
        success, payment_response = self.make_request('POST', 'payments', payment_data, 200)
        if not success:
            self.log_test("Ledger Real-time Updates", False, "- Failed to create test payment")
            return False
            
        new_payment_id = payment_response.get('id')
        self.test_payment_ids.append(new_payment_id)
        
        # Get updated ledger state
        success, updated_response = self.make_request('GET', f'students/{self.test_student_id}/ledger', expected_status=200)
        if not success:
            self.log_test("Ledger Real-time Updates", False, "- Failed to get updated ledger")
            return False
            
        updated_payments_count = len(updated_response.get('payments', []))
        updated_total_paid = updated_response.get('total_paid', 0)
        
        # Verify updates
        payments_increased = updated_payments_count == initial_payments_count + 1
        total_increased = abs((updated_total_paid - initial_total_paid) - 100.00) < 0.01
        
        success = payments_increased and total_increased
        
        print(f"   🔄 Real-time Update Verification:")
        print(f"   - Payments Count: {initial_payments_count} → {updated_payments_count} ({'✅' if payments_increased else '❌'})")
        print(f"   - Total Paid: ${initial_total_paid} → ${updated_total_paid} ({'✅' if total_increased else '❌'})")
        
        self.log_test("Ledger Real-time Updates", success, 
                     f"- Ledger reflects real-time changes: {success}")
        return success

    def test_authentication_required(self):
        """Test that all endpoints require proper authentication"""
        # Save current token
        original_token = self.token
        
        # Test without token
        self.token = None
        
        endpoints_to_test = [
            ('POST', 'payments', {"student_id": "test", "amount": 100}),
            ('GET', 'payments', None),
            ('GET', f'students/{self.test_student_id}/payments', None),
            ('DELETE', f'payments/{self.test_payment_ids[0] if self.test_payment_ids else "test"}', None),
            ('GET', f'students/{self.test_student_id}/ledger', None),
            ('DELETE', f'enrollments/{self.test_enrollment_ids[0] if self.test_enrollment_ids else "test"}', None)
        ]
        
        auth_required_count = 0
        
        for method, endpoint, data in endpoints_to_test:
            success, response = self.make_request(method, endpoint, data, 403)
            if success:  # 403 Forbidden is expected
                auth_required_count += 1
                print(f"   ✅ {method} {endpoint} - Requires authentication")
            else:
                print(f"   ❌ {method} {endpoint} - Authentication not enforced")
        
        # Restore token
        self.token = original_token
        
        success = auth_required_count == len(endpoints_to_test)
        self.log_test("Authentication Required", success, 
                     f"- {auth_required_count}/{len(endpoints_to_test)} endpoints require auth")
        return success

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete payments
        for payment_id in self.test_payment_ids:
            self.make_request('DELETE', f'payments/{payment_id}', expected_status=200)
        
        # Delete lessons
        for lesson_id in self.test_lesson_ids:
            self.make_request('DELETE', f'lessons/{lesson_id}', expected_status=200)
        
        # Delete enrollments
        for enrollment_id in self.test_enrollment_ids:
            self.make_request('DELETE', f'enrollments/{enrollment_id}', expected_status=200)
        
        # Delete student and teacher
        if self.test_student_id:
            self.make_request('DELETE', f'students/{self.test_student_id}', expected_status=200)
        
        if self.test_teacher_id:
            self.make_request('DELETE', f'teachers/{self.test_teacher_id}', expected_status=200)
        
        print("✅ Cleanup completed")

    def run_all_tests(self):
        """Run all Student Ledger Card system tests"""
        print("🎭 Starting Student Ledger Card System Testing")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Aborting tests.")
            return
        
        # Payment Management Tests
        print("\n💰 PAYMENT MANAGEMENT TESTING")
        print("-" * 40)
        self.test_payment_creation_cash()
        self.test_payment_creation_credit_card()
        self.test_payment_creation_check()
        self.test_payment_with_enrollment_link()
        self.test_get_all_payments()
        self.test_get_student_payments()
        self.test_payment_deletion()
        
        # Enrollment Management Tests
        print("\n📚 ENROLLMENT MANAGEMENT TESTING")
        print("-" * 40)
        self.test_create_multiple_enrollments()
        self.test_enrollment_deletion_from_ledger()
        
        # Lesson Management Tests
        print("\n🕺 LESSON MANAGEMENT TESTING")
        print("-" * 40)
        self.test_create_lessons_for_ledger()
        
        # Comprehensive Ledger Tests
        print("\n📊 COMPREHENSIVE STUDENT LEDGER TESTING")
        print("-" * 40)
        self.test_comprehensive_student_ledger()
        self.test_ledger_financial_calculations()
        self.test_ledger_lesson_filtering()
        self.test_ledger_real_time_updates()
        
        # Security Tests
        print("\n🔒 AUTHENTICATION & AUTHORIZATION TESTING")
        print("-" * 40)
        self.test_authentication_required()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"🎯 STUDENT LEDGER CARD SYSTEM TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Student Ledger Card system is working perfectly!")
        else:
            print("⚠️  Some tests failed. Please review the issues above.")

if __name__ == "__main__":
    tester = StudentLedgerTester()
    tester.run_all_tests()