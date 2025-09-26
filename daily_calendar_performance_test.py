#!/usr/bin/env python3
"""
Daily Calendar API Performance Testing
=====================================

This script tests the performance of the Daily Calendar API to diagnose slow loading issues.
It focuses on measuring response times, data sizes, and identifying bottlenecks.

Testing Objectives:
1. Daily Calendar API Performance - Test GET /api/calendar/daily/{date} endpoint
2. Students and Teachers API Performance - Test GET /api/students and GET /api/teachers endpoints  
3. Database Query Performance - Check for slow queries
4. API Response Times - Measure response times for each endpoint

Author: Backend Testing Agent
Date: Current Session
"""

import requests
import time
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
import statistics

class DailyCalendarPerformanceTester:
    def __init__(self, base_url="https://studio-manager-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.performance_data = {}
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")

    def make_request(self, method: str, endpoint: str, data: Dict[Any, Any] = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return success status, response data, and timing info"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        start_time = time.time()
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}, 0

            end_time = time.time()
            response_time = end_time - start_time
            
            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            if not success:
                print(f"   Status: {response.status_code}, Expected: {expected_status}")
                print(f"   Response: {str(response_data)[:200]}...")

            return success, response_data, response_time

        except requests.exceptions.RequestException as e:
            end_time = time.time()
            response_time = end_time - start_time
            print(f"   Request failed: {str(e)}")
            return False, {"error": str(e)}, response_time

    def authenticate(self):
        """Authenticate with admin credentials"""
        login_data = {
            "email": "admin@test.com",
            "password": "admin123"
        }
        
        success, response, response_time = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success:
            self.token = response.get('access_token')
            user_info = response.get('user', {})
            print(f"   👤 Authenticated as: {user_info.get('name', 'Unknown')} ({user_info.get('role', 'Unknown')})")
            
        self.log_test("Authentication", success, f"- Login time: {response_time:.3f}s")
        return success

    def measure_data_size(self, data):
        """Calculate the size of response data in bytes"""
        try:
            json_str = json.dumps(data)
            return len(json_str.encode('utf-8'))
        except:
            return 0

    def test_daily_calendar_performance(self):
        """Test Daily Calendar API performance with multiple dates"""
        print("\n🔍 TESTING DAILY CALENDAR API PERFORMANCE")
        
        # Test with multiple dates to get comprehensive performance data
        test_dates = []
        today = datetime.now()
        
        # Test current date, past dates, and future dates
        for i in range(-7, 8):  # 15 days total: 7 past, today, 7 future
            test_date = today + timedelta(days=i)
            test_dates.append(test_date.strftime('%Y-%m-%d'))
        
        response_times = []
        data_sizes = []
        lesson_counts = []
        teacher_counts = []
        
        for date_str in test_dates:
            success, response, response_time = self.make_request('GET', f'calendar/daily/{date_str}', expected_status=200)
            
            if success:
                response_times.append(response_time)
                data_size = self.measure_data_size(response)
                data_sizes.append(data_size)
                
                lessons = response.get('lessons', [])
                teachers = response.get('teachers', [])
                lesson_counts.append(len(lessons))
                teacher_counts.append(len(teachers))
                
                print(f"   📅 {date_str}: {response_time:.3f}s, {data_size:,} bytes, {len(lessons)} lessons, {len(teachers)} teachers")
            else:
                print(f"   ❌ {date_str}: Failed to fetch data")
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            avg_data_size = statistics.mean(data_sizes)
            max_data_size = max(data_sizes)
            total_lessons = sum(lesson_counts)
            total_teachers = max(teacher_counts) if teacher_counts else 0
            
            # Performance thresholds
            performance_acceptable = avg_response_time < 2.0  # Under 2 seconds average
            max_time_acceptable = max_response_time < 5.0     # Under 5 seconds max
            
            success = performance_acceptable and max_time_acceptable
            
            details = f"""
   📊 PERFORMANCE SUMMARY:
   - Average Response Time: {avg_response_time:.3f}s
   - Min Response Time: {min_response_time:.3f}s  
   - Max Response Time: {max_response_time:.3f}s
   - Average Data Size: {avg_data_size:,.0f} bytes ({avg_data_size/1024:.1f} KB)
   - Max Data Size: {max_data_size:,} bytes ({max_data_size/1024:.1f} KB)
   - Total Lessons Found: {total_lessons}
   - Teachers in System: {total_teachers}
   - Dates Tested: {len(test_dates)}"""
            
            self.performance_data['daily_calendar'] = {
                'avg_response_time': avg_response_time,
                'max_response_time': max_response_time,
                'min_response_time': min_response_time,
                'avg_data_size': avg_data_size,
                'max_data_size': max_data_size,
                'total_lessons': total_lessons,
                'total_teachers': total_teachers,
                'dates_tested': len(test_dates)
            }
            
            self.log_test("Daily Calendar API Performance", success, details)
            return success
        else:
            self.log_test("Daily Calendar API Performance", False, "- No successful requests")
            return False

    def test_students_api_performance(self):
        """Test Students API performance and data size"""
        print("\n👥 TESTING STUDENTS API PERFORMANCE")
        
        # Test multiple requests to get consistent timing
        response_times = []
        data_sizes = []
        student_counts = []
        
        for i in range(5):  # 5 requests for average
            success, response, response_time = self.make_request('GET', 'students', expected_status=200)
            
            if success:
                response_times.append(response_time)
                data_size = self.measure_data_size(response)
                data_sizes.append(data_size)
                student_counts.append(len(response) if isinstance(response, list) else 0)
                
                print(f"   Request {i+1}: {response_time:.3f}s, {data_size:,} bytes, {len(response) if isinstance(response, list) else 0} students")
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            avg_data_size = statistics.mean(data_sizes)
            avg_student_count = statistics.mean(student_counts)
            
            # Check if response time is reasonable for the amount of data
            performance_acceptable = avg_response_time < 1.0  # Under 1 second for students
            
            details = f"""
   📊 STUDENTS API SUMMARY:
   - Average Response Time: {avg_response_time:.3f}s
   - Average Data Size: {avg_data_size:,.0f} bytes ({avg_data_size/1024:.1f} KB)
   - Average Student Count: {avg_student_count:.0f}
   - Data per Student: {avg_data_size/avg_student_count if avg_student_count > 0 else 0:.0f} bytes"""
            
            self.performance_data['students_api'] = {
                'avg_response_time': avg_response_time,
                'avg_data_size': avg_data_size,
                'avg_student_count': avg_student_count
            }
            
            self.log_test("Students API Performance", performance_acceptable, details)
            return performance_acceptable
        else:
            self.log_test("Students API Performance", False, "- No successful requests")
            return False

    def test_teachers_api_performance(self):
        """Test Teachers API performance and data size"""
        print("\n🎭 TESTING TEACHERS API PERFORMANCE")
        
        # Test multiple requests to get consistent timing
        response_times = []
        data_sizes = []
        teacher_counts = []
        
        for i in range(5):  # 5 requests for average
            success, response, response_time = self.make_request('GET', 'teachers', expected_status=200)
            
            if success:
                response_times.append(response_time)
                data_size = self.measure_data_size(response)
                data_sizes.append(data_size)
                teacher_counts.append(len(response) if isinstance(response, list) else 0)
                
                print(f"   Request {i+1}: {response_time:.3f}s, {data_size:,} bytes, {len(response) if isinstance(response, list) else 0} teachers")
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            avg_data_size = statistics.mean(data_sizes)
            avg_teacher_count = statistics.mean(teacher_counts)
            
            # Check if response time is reasonable for the amount of data
            performance_acceptable = avg_response_time < 1.0  # Under 1 second for teachers
            
            details = f"""
   📊 TEACHERS API SUMMARY:
   - Average Response Time: {avg_response_time:.3f}s
   - Average Data Size: {avg_data_size:,.0f} bytes ({avg_data_size/1024:.1f} KB)
   - Average Teacher Count: {avg_teacher_count:.0f}
   - Data per Teacher: {avg_data_size/avg_teacher_count if avg_teacher_count > 0 else 0:.0f} bytes"""
            
            self.performance_data['teachers_api'] = {
                'avg_response_time': avg_response_time,
                'avg_data_size': avg_data_size,
                'avg_teacher_count': avg_teacher_count
            }
            
            self.log_test("Teachers API Performance", performance_acceptable, details)
            return performance_acceptable
        else:
            self.log_test("Teachers API Performance", False, "- No successful requests")
            return False

    def test_lessons_api_performance(self):
        """Test Lessons API performance to understand data volume"""
        print("\n📚 TESTING LESSONS API PERFORMANCE")
        
        success, response, response_time = self.make_request('GET', 'lessons', expected_status=200)
        
        if success:
            data_size = self.measure_data_size(response)
            lesson_count = len(response) if isinstance(response, list) else 0
            
            # Analyze lesson data structure
            if lesson_count > 0:
                sample_lesson = response[0]
                lesson_fields = len(sample_lesson.keys()) if isinstance(sample_lesson, dict) else 0
                avg_lesson_size = data_size / lesson_count if lesson_count > 0 else 0
                
                print(f"   📊 Lessons Analysis:")
                print(f"   - Total Lessons: {lesson_count}")
                print(f"   - Response Time: {response_time:.3f}s")
                print(f"   - Total Data Size: {data_size:,} bytes ({data_size/1024:.1f} KB)")
                print(f"   - Average Lesson Size: {avg_lesson_size:.0f} bytes")
                print(f"   - Fields per Lesson: {lesson_fields}")
                
                # Check for potential performance issues
                performance_acceptable = response_time < 3.0  # Under 3 seconds for all lessons
                
                self.performance_data['lessons_api'] = {
                    'response_time': response_time,
                    'data_size': data_size,
                    'lesson_count': lesson_count,
                    'avg_lesson_size': avg_lesson_size,
                    'lesson_fields': lesson_fields
                }
                
                details = f"- {lesson_count} lessons, {response_time:.3f}s, {data_size/1024:.1f} KB"
                self.log_test("Lessons API Performance", performance_acceptable, details)
                return performance_acceptable
            else:
                self.log_test("Lessons API Performance", True, "- No lessons found (empty response)")
                return True
        else:
            self.log_test("Lessons API Performance", False, "- Failed to fetch lessons")
            return False

    def test_concurrent_api_calls(self):
        """Test how the system handles concurrent API calls"""
        print("\n⚡ TESTING CONCURRENT API PERFORMANCE")
        
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def make_concurrent_request(endpoint, result_queue):
            success, response, response_time = self.make_request('GET', endpoint)
            result_queue.put({
                'endpoint': endpoint,
                'success': success,
                'response_time': response_time,
                'data_size': self.measure_data_size(response) if success else 0
            })
        
        # Test concurrent requests to different endpoints
        endpoints = [
            'students',
            'teachers', 
            'lessons',
            f'calendar/daily/{datetime.now().strftime("%Y-%m-%d")}',
            'dashboard/stats'
        ]
        
        threads = []
        start_time = time.time()
        
        # Start all requests simultaneously
        for endpoint in endpoints:
            thread = threading.Thread(target=make_concurrent_request, args=(endpoint, results_queue))
            thread.start()
            threads.append(thread)
        
        # Wait for all requests to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        successful_requests = [r for r in results if r['success']]
        avg_response_time = statistics.mean([r['response_time'] for r in successful_requests]) if successful_requests else 0
        total_data_size = sum([r['data_size'] for r in successful_requests])
        
        performance_acceptable = total_time < 5.0 and len(successful_requests) == len(endpoints)
        
        details = f"""
   📊 CONCURRENT REQUESTS SUMMARY:
   - Total Time: {total_time:.3f}s
   - Successful Requests: {len(successful_requests)}/{len(endpoints)}
   - Average Response Time: {avg_response_time:.3f}s
   - Total Data Transferred: {total_data_size:,} bytes ({total_data_size/1024:.1f} KB)"""
        
        for result in results:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['endpoint']}: {result['response_time']:.3f}s")
        
        self.performance_data['concurrent_requests'] = {
            'total_time': total_time,
            'successful_requests': len(successful_requests),
            'total_requests': len(endpoints),
            'avg_response_time': avg_response_time,
            'total_data_size': total_data_size
        }
        
        self.log_test("Concurrent API Performance", performance_acceptable, details)
        return performance_acceptable

    def analyze_performance_bottlenecks(self):
        """Analyze performance data to identify bottlenecks"""
        print("\n🔍 PERFORMANCE BOTTLENECK ANALYSIS")
        
        if not self.performance_data:
            print("   ⚠️  No performance data available for analysis")
            return False
        
        bottlenecks = []
        recommendations = []
        
        # Analyze Daily Calendar performance
        if 'daily_calendar' in self.performance_data:
            dc_data = self.performance_data['daily_calendar']
            if dc_data['avg_response_time'] > 1.0:
                bottlenecks.append(f"Daily Calendar API slow: {dc_data['avg_response_time']:.3f}s average")
                recommendations.append("Consider caching daily calendar data or optimizing database queries")
            
            if dc_data['max_data_size'] > 100000:  # 100KB
                bottlenecks.append(f"Daily Calendar returns large data: {dc_data['max_data_size']/1024:.1f} KB")
                recommendations.append("Consider pagination or reducing data fields in daily calendar response")
        
        # Analyze Students API performance
        if 'students_api' in self.performance_data:
            students_data = self.performance_data['students_api']
            if students_data['avg_response_time'] > 0.5:
                bottlenecks.append(f"Students API slow: {students_data['avg_response_time']:.3f}s average")
                recommendations.append("Consider implementing pagination for students list")
        
        # Analyze Teachers API performance  
        if 'teachers_api' in self.performance_data:
            teachers_data = self.performance_data['teachers_api']
            if teachers_data['avg_response_time'] > 0.5:
                bottlenecks.append(f"Teachers API slow: {teachers_data['avg_response_time']:.3f}s average")
                recommendations.append("Consider caching teachers data as it changes infrequently")
        
        # Analyze Lessons API performance
        if 'lessons_api' in self.performance_data:
            lessons_data = self.performance_data['lessons_api']
            if lessons_data['response_time'] > 2.0:
                bottlenecks.append(f"Lessons API very slow: {lessons_data['response_time']:.3f}s")
                recommendations.append("Lessons API needs pagination - returning all lessons is inefficient")
            
            if lessons_data['data_size'] > 500000:  # 500KB
                bottlenecks.append(f"Lessons API returns too much data: {lessons_data['data_size']/1024:.1f} KB")
                recommendations.append("Implement date-based filtering for lessons API")
        
        print("   🚨 IDENTIFIED BOTTLENECKS:")
        if bottlenecks:
            for i, bottleneck in enumerate(bottlenecks, 1):
                print(f"   {i}. {bottleneck}")
        else:
            print("   ✅ No major performance bottlenecks identified")
        
        print("\n   💡 RECOMMENDATIONS:")
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        else:
            print("   ✅ System performance appears optimal")
        
        return len(bottlenecks) == 0

    def generate_performance_report(self):
        """Generate a comprehensive performance report"""
        print("\n📊 COMPREHENSIVE PERFORMANCE REPORT")
        print("=" * 60)
        
        if not self.performance_data:
            print("No performance data available")
            return
        
        # Daily Calendar Analysis
        if 'daily_calendar' in self.performance_data:
            dc = self.performance_data['daily_calendar']
            print(f"\n🗓️  DAILY CALENDAR API:")
            print(f"   Response Time: {dc['min_response_time']:.3f}s - {dc['max_response_time']:.3f}s (avg: {dc['avg_response_time']:.3f}s)")
            print(f"   Data Size: {dc['avg_data_size']/1024:.1f} KB average, {dc['max_data_size']/1024:.1f} KB maximum")
            print(f"   Content: {dc['total_lessons']} lessons, {dc['total_teachers']} teachers")
            
            # Performance rating
            if dc['avg_response_time'] < 1.0:
                print("   ✅ Performance: EXCELLENT")
            elif dc['avg_response_time'] < 2.0:
                print("   ⚠️  Performance: GOOD")
            else:
                print("   🚨 Performance: NEEDS IMPROVEMENT")
        
        # Students API Analysis
        if 'students_api' in self.performance_data:
            students = self.performance_data['students_api']
            print(f"\n👥 STUDENTS API:")
            print(f"   Response Time: {students['avg_response_time']:.3f}s average")
            print(f"   Data Size: {students['avg_data_size']/1024:.1f} KB ({students['avg_student_count']:.0f} students)")
            print(f"   Efficiency: {students['avg_data_size']/students['avg_student_count'] if students['avg_student_count'] > 0 else 0:.0f} bytes per student")
        
        # Teachers API Analysis
        if 'teachers_api' in self.performance_data:
            teachers = self.performance_data['teachers_api']
            print(f"\n🎭 TEACHERS API:")
            print(f"   Response Time: {teachers['avg_response_time']:.3f}s average")
            print(f"   Data Size: {teachers['avg_data_size']/1024:.1f} KB ({teachers['avg_teacher_count']:.0f} teachers)")
            print(f"   Efficiency: {teachers['avg_data_size']/teachers['avg_teacher_count'] if teachers['avg_teacher_count'] > 0 else 0:.0f} bytes per teacher")
        
        # Lessons API Analysis
        if 'lessons_api' in self.performance_data:
            lessons = self.performance_data['lessons_api']
            print(f"\n📚 LESSONS API:")
            print(f"   Response Time: {lessons['response_time']:.3f}s")
            print(f"   Data Size: {lessons['data_size']/1024:.1f} KB ({lessons['lesson_count']} lessons)")
            print(f"   Efficiency: {lessons['avg_lesson_size']:.0f} bytes per lesson")
            
            if lessons['lesson_count'] > 100:
                print("   ⚠️  WARNING: Returning all lessons may cause performance issues")
        
        # Concurrent Requests Analysis
        if 'concurrent_requests' in self.performance_data:
            concurrent = self.performance_data['concurrent_requests']
            print(f"\n⚡ CONCURRENT PERFORMANCE:")
            print(f"   Total Time: {concurrent['total_time']:.3f}s for {concurrent['total_requests']} simultaneous requests")
            print(f"   Success Rate: {concurrent['successful_requests']}/{concurrent['total_requests']} ({concurrent['successful_requests']/concurrent['total_requests']*100:.1f}%)")
            print(f"   Average Response: {concurrent['avg_response_time']:.3f}s per request")
        
        print("\n" + "=" * 60)

    def run_all_tests(self):
        """Run all performance tests"""
        print("🚀 STARTING DAILY CALENDAR API PERFORMANCE TESTING")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with testing.")
            return False
        
        # Run all performance tests
        tests = [
            self.test_daily_calendar_performance,
            self.test_students_api_performance,
            self.test_teachers_api_performance,
            self.test_lessons_api_performance,
            self.test_concurrent_api_calls
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
        
        # Analyze results
        self.analyze_performance_bottlenecks()
        self.generate_performance_report()
        
        print(f"\n📊 TESTING SUMMARY:")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100) if self.tests_run > 0 else 0:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    """Main function to run the performance tests"""
    tester = DailyCalendarPerformanceTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ ALL PERFORMANCE TESTS COMPLETED SUCCESSFULLY")
        sys.exit(0)
    else:
        print("\n❌ SOME PERFORMANCE TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()