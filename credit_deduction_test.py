import requests
import json
from datetime import datetime, timedelta

class CreditDeductionTester:
    def __init__(self, base_url="https://studio-manager-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None

    def make_request(self, method: str, endpoint: str, data=None, expected_status: int = 200):
        """Make HTTP request"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            return success, response_data

        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def test_credit_deduction_flow(self):
        """Test the complete credit deduction flow"""
        print("🧪 Testing Credit Deduction Flow...")
        
        # Login
        login_data = {"email": "admin@test.com", "password": "admin123"}
        success, response = self.make_request('POST', 'auth/login', login_data, 200)
        if not success:
            print("❌ Login failed")
            return
        self.token = response.get('access_token')
        print("✅ Logged in successfully")

        # Create test student
        student_data = {
            "name": "Credit Test Student",
            "email": "credit.test@example.com",
            "phone": "+1555999888"
        }
        success, response = self.make_request('POST', 'students', student_data, 200)
        if not success:
            print("❌ Failed to create student")
            return
        student_id = response.get('id')
        print(f"✅ Created student: {student_id}")

        # Create test teacher
        teacher_data = {
            "name": "Credit Test Teacher",
            "email": "credit.teacher@example.com",
            "specialties": ["ballet"]
        }
        success, response = self.make_request('POST', 'teachers', teacher_data, 200)
        if not success:
            print("❌ Failed to create teacher")
            return
        teacher_id = response.get('id')
        print(f"✅ Created teacher: {teacher_id}")

        # Create enrollment with payment
        enrollment_data = {
            "student_id": student_id,
            "program_name": "Credit Test Program",
            "total_lessons": 5,
            "price_per_lesson": 50.0,
            "initial_payment": 250.0,  # Full payment for 5 lessons
            "total_paid": 250.0
        }
        success, response = self.make_request('POST', 'enrollments', enrollment_data, 200)
        if not success:
            print("❌ Failed to create enrollment")
            return
        enrollment_id = response.get('id')
        print(f"✅ Created enrollment: {enrollment_id}")

        # Check initial credits
        success, response = self.make_request('GET', f'students/{student_id}/lesson-credits', expected_status=200)
        if success:
            initial_credits = response.get('total_lessons_available', 0)
            print(f"📊 Initial credits: {initial_credits}")
        else:
            print("❌ Failed to get initial credits")
            return

        # Create a lesson
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        
        lesson_data = {
            "student_id": student_id,
            "teacher_ids": [teacher_id],
            "start_datetime": start_time.isoformat(),
            "duration_minutes": 60,
            "booking_type": "private_lesson",
            "enrollment_id": enrollment_id
        }
        success, response = self.make_request('POST', 'lessons', lesson_data, 200)
        if not success:
            print("❌ Failed to create lesson")
            return
        lesson_id = response.get('id')
        print(f"✅ Created lesson: {lesson_id}")

        # Mark attendance
        success, response = self.make_request('POST', f'lessons/{lesson_id}/attend', expected_status=200)
        if not success:
            print("❌ Failed to mark attendance")
            return
        print("✅ Marked attendance")

        # Check credits after attendance
        success, response = self.make_request('GET', f'students/{student_id}/lesson-credits', expected_status=200)
        if success:
            final_credits = response.get('total_lessons_available', 0)
            print(f"📊 Final credits: {final_credits}")
            
            if final_credits == initial_credits - 1:
                print("✅ Credit deduction working correctly!")
            else:
                print(f"⚠️  Credit deduction issue: Expected {initial_credits - 1}, got {final_credits}")
        else:
            print("❌ Failed to get final credits")

        # Cleanup
        self.make_request('DELETE', f'lessons/{lesson_id}', expected_status=200)
        self.make_request('DELETE', f'enrollments/{enrollment_id}', expected_status=200)
        self.make_request('DELETE', f'students/{student_id}', expected_status=200)
        self.make_request('DELETE', f'teachers/{teacher_id}', expected_status=200)
        print("🗑️ Cleanup completed")

if __name__ == "__main__":
    tester = CreditDeductionTester()
    tester.test_credit_deduction_flow()