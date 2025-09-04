#!/usr/bin/env python3
"""
Student Ledger API Diagnosis Test
Specifically tests why the frontend modal shows "No ledger data available"
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

class LedgerDiagnosisTester:
    def __init__(self, base_url="https://studio-manager-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
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
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, f"Unsupported method: {method}"

            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = response.text

            return success, response_data

        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"

    def authenticate(self):
        """Authenticate with admin credentials"""
        print("🔐 Authenticating with admin@test.com / admin123...")
        
        login_data = {
            "email": "admin@test.com",
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            self.log_test("Admin Authentication", True, f"Token obtained for user {response['user']['name']}")
            return True
        else:
            self.log_test("Admin Authentication", False, f"Login failed: {response}")
            return False

    def test_students_list(self):
        """Test getting list of students"""
        print("\n📋 Testing Students List...")
        
        success, response = self.make_request('GET', 'students')
        
        if success and isinstance(response, list):
            student_count = len(response)
            self.log_test("Students List Retrieval", True, f"Found {student_count} students")
            
            if student_count > 0:
                print(f"   📊 First 5 students:")
                for i, student in enumerate(response[:5]):
                    print(f"   {i+1}. {student.get('name', 'Unknown')} (ID: {student.get('id', 'N/A')})")
                
                return response
            else:
                self.log_test("Students Data Availability", False, "No students found")
                return []
        else:
            self.log_test("Students List Retrieval", False, f"Failed: {response}")
            return []

    def test_student_ledger_detailed(self, student_id: str, student_name: str = "Unknown"):
        """Test student ledger endpoint in detail"""
        print(f"\n💰 DETAILED LEDGER TEST for {student_name} (ID: {student_id})")
        print("=" * 60)
        
        success, response = self.make_request('GET', f'students/{student_id}/ledger')
        
        if success:
            self.log_test(f"Ledger API Response - {student_name}", True, "API call successful")
            
            if isinstance(response, dict):
                # Check structure
                required_fields = ['student', 'enrollments', 'payments', 'upcoming_lessons', 'lesson_history', 
                                 'total_paid', 'total_enrolled_lessons', 'remaining_lessons', 'lessons_taken']
                
                print(f"\n🔍 RESPONSE STRUCTURE ANALYSIS:")
                all_fields_present = True
                for field in required_fields:
                    if field in response:
                        print(f"   ✅ {field}: {type(response[field])}")
                    else:
                        print(f"   ❌ {field}: MISSING")
                        all_fields_present = False
                
                self.log_test(f"Ledger Structure - {student_name}", all_fields_present, 
                             "All required fields present" if all_fields_present else "Missing required fields")
                
                # Analyze data content
                enrollments = response.get('enrollments', [])
                payments = response.get('payments', [])
                upcoming_lessons = response.get('upcoming_lessons', [])
                lesson_history = response.get('lesson_history', [])
                
                print(f"\n📊 DATA CONTENT ANALYSIS:")
                print(f"   💵 Total Paid: ${response.get('total_paid', 0)}")
                print(f"   📚 Total Enrolled Lessons: {response.get('total_enrolled_lessons', 0)}")
                print(f"   ⏳ Remaining Lessons: {response.get('remaining_lessons', 0)}")
                print(f"   ✅ Lessons Taken: {response.get('lessons_taken', 0)}")
                print(f"   📝 Enrollments Count: {len(enrollments)}")
                print(f"   💳 Payments Count: {len(payments)}")
                print(f"   🔮 Upcoming Lessons Count: {len(upcoming_lessons)}")
                print(f"   📚 Lesson History Count: {len(lesson_history)}")
                
                # Check if there's meaningful data
                has_enrollments = len(enrollments) > 0
                has_payments = len(payments) > 0
                has_lessons = len(upcoming_lessons) > 0 or len(lesson_history) > 0
                has_financial_data = response.get('total_paid', 0) > 0 or response.get('remaining_lessons', 0) > 0
                
                print(f"\n🎯 LEDGER DATA AVAILABILITY:")
                print(f"   📝 Has Enrollments: {'✅ YES' if has_enrollments else '❌ NO'}")
                print(f"   💳 Has Payments: {'✅ YES' if has_payments else '❌ NO'}")
                print(f"   🕺 Has Lessons: {'✅ YES' if has_lessons else '❌ NO'}")
                print(f"   💰 Has Financial Data: {'✅ YES' if has_financial_data else '❌ NO'}")
                
                has_any_data = has_enrollments or has_payments or has_lessons or has_financial_data
                
                if has_any_data:
                    self.log_test(f"Ledger Data Content - {student_name}", True, "Student has ledger data")
                    
                    # Show detailed data
                    if enrollments:
                        print(f"\n📝 ENROLLMENT DETAILS:")
                        for i, enrollment in enumerate(enrollments):
                            print(f"   {i+1}. Program: {enrollment.get('program_name', 'N/A')}")
                            print(f"      Total Lessons: {enrollment.get('total_lessons', 0)}")
                            print(f"      Remaining: {enrollment.get('remaining_lessons', 0)}")
                            print(f"      Paid: ${enrollment.get('total_paid', 0)}")
                            print(f"      Active: {enrollment.get('is_active', False)}")
                    
                    if payments:
                        print(f"\n💳 PAYMENT DETAILS:")
                        for i, payment in enumerate(payments[:3]):  # Show first 3
                            print(f"   {i+1}. Amount: ${payment.get('amount', 0)}")
                            print(f"      Method: {payment.get('payment_method', 'N/A')}")
                            print(f"      Date: {payment.get('payment_date', 'N/A')}")
                    
                    if upcoming_lessons:
                        print(f"\n🔮 UPCOMING LESSON DETAILS:")
                        for i, lesson in enumerate(upcoming_lessons[:3]):  # Show first 3
                            print(f"   {i+1}. Date: {lesson.get('start_datetime', 'N/A')}")
                            print(f"      Teachers: {lesson.get('teacher_names', [])}")
                            print(f"      Type: {lesson.get('booking_type', 'N/A')}")
                            print(f"      Status: {lesson.get('status', 'N/A')}")
                    
                else:
                    self.log_test(f"Ledger Data Content - {student_name}", False, 
                                 "NO LEDGER DATA - This explains 'No ledger data available' message")
                    
                    print(f"\n🚨 ROOT CAUSE IDENTIFIED:")
                    print(f"   This student has no enrollments, payments, or lessons")
                    print(f"   Frontend modal correctly shows 'No ledger data available'")
                
                return response, has_any_data
            else:
                self.log_test(f"Ledger Response Format - {student_name}", False, 
                             f"Expected dict, got {type(response)}")
                return None, False
        else:
            self.log_test(f"Ledger API Response - {student_name}", False, f"API call failed: {response}")
            return None, False

    def create_sample_data_for_student(self, student_id: str, student_name: str = "Unknown"):
        """Create sample enrollment and payment data for testing"""
        print(f"\n🔧 CREATING SAMPLE DATA for {student_name}...")
        
        # Create enrollment
        enrollment_data = {
            "student_id": student_id,
            "program_name": "Test Bronze Program",
            "total_lessons": 8,
            "total_paid": 400.0,
            "expiry_date": (datetime.now() + timedelta(days=60)).isoformat()
        }
        
        success, response = self.make_request('POST', 'enrollments', enrollment_data, 200)
        
        if success:
            enrollment_id = response.get('id')
            self.log_test(f"Sample Enrollment Creation - {student_name}", True, 
                         f"Created enrollment with 8 lessons")
            
            # Create payment
            payment_data = {
                "student_id": student_id,
                "enrollment_id": enrollment_id,
                "amount": 400.0,
                "payment_method": "credit_card",
                "notes": "Sample payment for testing ledger"
            }
            
            payment_success, payment_response = self.make_request('POST', 'payments', payment_data, 200)
            
            if payment_success:
                self.log_test(f"Sample Payment Creation - {student_name}", True, f"Created $400 payment")
                
                # Create upcoming lesson
                teacher_success, teachers = self.make_request('GET', 'teachers')
                if teacher_success and teachers:
                    teacher_id = teachers[0]['id']
                    
                    lesson_data = {
                        "student_id": student_id,
                        "teacher_ids": [teacher_id],  # Use teacher_ids array
                        "start_datetime": (datetime.now() + timedelta(days=3)).isoformat(),
                        "duration_minutes": 60,
                        "booking_type": "private_lesson",
                        "enrollment_id": enrollment_id,
                        "notes": "Sample lesson for testing"
                    }
                    
                    lesson_success, lesson_response = self.make_request('POST', 'lessons', lesson_data, 200)
                    
                    if lesson_success:
                        self.log_test(f"Sample Lesson Creation - {student_name}", True, 
                                     f"Created upcoming lesson")
                        return True
                    else:
                        print(f"   ⚠️  Lesson creation failed: {lesson_response}")
                        return True  # Still successful with enrollment and payment
                
                return True
            else:
                self.log_test(f"Sample Payment Creation - {student_name}", False, 
                             f"Failed: {payment_response}")
                return False
        else:
            self.log_test(f"Sample Enrollment Creation - {student_name}", False, f"Failed: {response}")
            return False

    def run_diagnosis(self):
        """Run comprehensive diagnosis of student ledger issue"""
        print("🎯 STUDENT LEDGER API DIAGNOSIS")
        print("=" * 50)
        print("Testing why frontend modal shows 'No ledger data available'")
        print("=" * 50)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed.")
            return
        
        # Step 2: Get students
        students = self.test_students_list()
        
        if not students:
            print("❌ No students found. Cannot test ledger.")
            return
        
        # Step 3: Test ledger for multiple students
        students_with_data = []
        students_without_data = []
        
        # Test first 3 students for diagnosis
        test_students = students[:3] if len(students) >= 3 else students
        
        for student in test_students:
            student_id = student.get('id')
            student_name = student.get('name', 'Unknown')
            
            if student_id:
                ledger_data, has_data = self.test_student_ledger_detailed(student_id, student_name)
                
                if has_data:
                    students_with_data.append((student_id, student_name))
                else:
                    students_without_data.append((student_id, student_name))
        
        # Step 4: Create sample data for one student without data
        if students_without_data:
            print(f"\n🔧 FIXING ISSUE BY CREATING SAMPLE DATA")
            print("=" * 45)
            
            student_id, student_name = students_without_data[0]
            if self.create_sample_data_for_student(student_id, student_name):
                print(f"\n🔄 Re-testing ledger after creating sample data...")
                self.test_student_ledger_detailed(student_id, student_name)
        
        # Step 5: Final diagnosis
        print(f"\n🔍 FINAL DIAGNOSIS")
        print("=" * 25)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        print(f"\n📊 STUDENT DATA ANALYSIS:")
        print(f"Students with ledger data: {len(students_with_data)}")
        print(f"Students without ledger data: {len(students_without_data)}")
        
        if students_with_data:
            print(f"\n✅ Students with data (ledger modal will work):")
            for student_id, student_name in students_with_data:
                print(f"   - {student_name}")
        
        if students_without_data:
            print(f"\n❌ Students without data (will show 'No ledger data available'):")
            for student_id, student_name in students_without_data:
                print(f"   - {student_name}")
        
        # Final recommendation
        print(f"\n💡 RECOMMENDATION:")
        if len(students_without_data) > len(students_with_data):
            print("🚨 ISSUE CONFIRMED: Most students have no ledger data")
            print("   The frontend modal correctly shows 'No ledger data available'")
            print("   SOLUTION: Create enrollments and payments for students")
            print("   STEPS:")
            print("   1. Go to Students page")
            print("   2. Click 'Enroll' button for each student")
            print("   3. Create a program enrollment with lessons")
            print("   4. Add payments for the enrollment")
            print("   5. Optionally schedule lessons")
        elif len(students_without_data) > 0:
            print("⚠️  PARTIAL ISSUE: Some students have no ledger data")
            print("   These specific students will show 'No ledger data available'")
            print("   SOLUTION: Create enrollments for students without data")
        else:
            print("✅ NO ISSUE: All tested students have ledger data")
            print("   The ledger API is working correctly")
            print("   If frontend still shows 'No ledger data available', check:")
            print("   1. Frontend API call implementation")
            print("   2. Data parsing in StudentLedgerModal component")
            print("   3. Browser console for JavaScript errors")

if __name__ == "__main__":
    tester = LedgerDiagnosisTester()
    tester.run_diagnosis()