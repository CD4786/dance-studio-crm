from fastapi import FastAPI, APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, date, time, timedelta
from enum import Enum
import jwt
from passlib.context import CryptContext
import hashlib
import json
import asyncio

# SMS Integration
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("⚠️  Twilio not installed. SMS functionality will be limited.")

# Alternative free SMS service
import requests

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('DATABASE_URL') or os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'dance_studio_crm')

print(f"🔗 Connecting to MongoDB: {mongo_url}")
print(f"📊 Database name: {db_name}")

try:
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
    # Use a fallback for Railway
    client = None
    db = None

# WebSocket Connection Manager for Real-time Updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, user_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id in self.user_connections:
            del self.user_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.user_connections:
            websocket = self.user_connections[user_id]
            try:
                await websocket.send_text(message)
            except:
                await self.disconnect(websocket, user_id)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            if connection in self.active_connections:
                self.active_connections.remove(connection)

    async def broadcast_update(self, update_type: str, data: Dict[str, Any], user_id: str, user_name: str):
        """Broadcast real-time updates to all connected users"""
        message = {
            "type": update_type,
            "data": data,
            "user_id": user_id,
            "user_name": user_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(json.dumps(message))

manager = ConnectionManager()

# SMS Configuration
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN") 
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

# Initialize Twilio client
twilio_client = None
if TWILIO_AVAILABLE and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print("✅ Twilio SMS client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Twilio client: {e}")
else:
    print("⚠️  Twilio credentials not found. SMS will be simulated.")

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"

# Enums
class UserRole(str, Enum):
    OWNER = "owner"
    MANAGER = "manager"
    TEACHER = "teacher"

class ClassType(str, Enum):
    BALLET = "ballet"
    HIP_HOP = "hip_hop"
    JAZZ = "jazz"
    CONTEMPORARY = "contemporary"
    TAP = "tap"
    SALSA = "salsa"
    BALLROOM = "ballroom"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: UserRole
    hashed_password: str
    studio_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Student(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    parent_email: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class StudentCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    parent_email: Optional[str] = None
    notes: Optional[str] = None

class LessonPackage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    total_lessons: int
    price: float
    expiry_days: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Enrollment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    package_id: str
    remaining_lessons: int
    total_paid: float
    purchase_date: datetime = Field(default_factory=datetime.utcnow)
    expiry_date: Optional[datetime] = None
    is_active: bool = True

class EnrollmentCreate(BaseModel):
    student_id: str
    package_id: str
    total_paid: float
    expiry_date: Optional[datetime] = None

# Recurring lesson patterns
class RecurrencePattern(str, Enum):
    WEEKLY = "weekly"
    BI_WEEKLY = "bi_weekly"
    MONTHLY = "monthly"

class RecurringLessonSeries(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    teacher_id: str
    start_datetime: datetime
    duration_minutes: int = 60
    recurrence_pattern: RecurrencePattern
    end_date: Optional[datetime] = None
    max_occurrences: Optional[int] = None
    notes: Optional[str] = None
    enrollment_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    is_active: bool = True

class RecurringLessonCreate(BaseModel):
    student_id: str
    teacher_id: str
    start_datetime: datetime
    duration_minutes: int = 60
    recurrence_pattern: RecurrencePattern
    end_date: Optional[datetime] = None
    max_occurrences: Optional[int] = None
    notes: Optional[str] = None
    enrollment_id: Optional[str] = None

class LessonUpdate(BaseModel):
    student_id: Optional[str] = None
    teacher_id: Optional[str] = None
    start_datetime: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    is_cancelled: Optional[bool] = None
    cancellation_reason: Optional[str] = None

class PrivateLesson(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    teacher_id: str
    start_datetime: datetime
    end_datetime: datetime
    notes: Optional[str] = None
    is_attended: bool = False
    enrollment_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Recurring lesson support
    recurring_series_id: Optional[str] = None
    is_cancelled: bool = False
    cancellation_reason: Optional[str] = None
    modified_at: datetime = Field(default_factory=datetime.utcnow)
    modified_by: Optional[str] = None

class PrivateLessonCreate(BaseModel):
    student_id: str
    teacher_id: str
    start_datetime: datetime
    duration_minutes: int = 60
    notes: Optional[str] = None
    enrollment_id: Optional[str] = None

class PrivateLessonUpdate(BaseModel):
    student_id: Optional[str] = None
    teacher_id: Optional[str] = None
    start_datetime: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None

class PrivateLessonResponse(BaseModel):
    id: str
    student_id: str
    student_name: str
    teacher_id: str
    teacher_name: str
    start_datetime: datetime
    end_datetime: datetime
    notes: Optional[str] = None
    is_attended: bool = False
    enrollment_id: Optional[str] = None

class AttendanceCreate(BaseModel):
    lesson_id: str

class NotificationPreference(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    email_enabled: bool = True
    sms_enabled: bool = False
    reminder_hours: int = 24  # Hours before lesson to send reminder
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NotificationPreferenceCreate(BaseModel):
    student_id: str
    email_enabled: bool = True
    sms_enabled: bool = False
    reminder_hours: int = 24
    email_address: Optional[str] = None
    phone_number: Optional[str] = None

class ReminderRequest(BaseModel):
    lesson_id: str
    notification_type: str  # "email" or "sms"
    message: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: UserRole
    studio_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole
    studio_name: Optional[str] = None

class Teacher(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone: Optional[str] = None
    specialties: List[ClassType]
    bio: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TeacherCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    specialties: List[ClassType]
    bio: Optional[str] = None

class DanceClass(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    class_type: ClassType
    teacher_id: str
    start_datetime: datetime
    end_datetime: datetime
    capacity: int = 20
    enrolled: int = 0
    description: Optional[str] = None
    recurring: bool = False
    recurring_pattern: Optional[str] = None
    studio_room: Optional[str] = None
    price: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ClassCreate(BaseModel):
    title: str
    class_type: ClassType
    teacher_id: str
    start_datetime: datetime
    end_datetime: datetime
    capacity: int = 20
    description: Optional[str] = None
    recurring: bool = False
    recurring_pattern: Optional[str] = None
    studio_room: Optional[str] = None
    price: Optional[float] = None

class ClassResponse(BaseModel):
    id: str
    title: str
    class_type: ClassType
    teacher_id: str
    teacher_name: str
    start_datetime: datetime
    end_datetime: datetime
    capacity: int
    enrolled: int
    description: Optional[str] = None
    studio_room: Optional[str] = None
    price: Optional[float] = None

# Helper function to generate recurring lesson instances
def generate_recurring_lessons(series: RecurringLessonSeries) -> List[PrivateLesson]:
    """Generate individual lesson instances from a recurring series"""
    lessons = []
    current_date = series.start_datetime
    count = 0
    
    while True:
        # Check end conditions
        if series.end_date and current_date > series.end_date:
            break
        if series.max_occurrences and count >= series.max_occurrences:
            break
            
        # Create lesson instance
        lesson = PrivateLesson(
            student_id=series.student_id,
            teacher_id=series.teacher_id,
            start_datetime=current_date,
            duration_minutes=series.duration_minutes,
            notes=series.notes,
            enrollment_id=series.enrollment_id,
            recurring_series_id=series.id,
            created_at=series.created_at,
            modified_by=series.created_by
        )
        lessons.append(lesson)
        
        # Calculate next occurrence
        if series.recurrence_pattern == RecurrencePattern.WEEKLY:
            current_date += timedelta(weeks=1)
        elif series.recurrence_pattern == RecurrencePattern.BI_WEEKLY:
            current_date += timedelta(weeks=2)
        elif series.recurrence_pattern == RecurrencePattern.MONTHLY:
            # Add one month (handling month boundaries)
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        count += 1
        
        # Safety limit to prevent infinite loops
        if count > 1000:
            break
    
    return lessons

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = security):
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user)

# Auth Routes
@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        name=user_data.name,
        role=user_data.role,
        hashed_password=hashed_password,
        studio_name=user_data.studio_name
    )
    
    await db.users.insert_one(user.dict())
    return UserResponse(**user.dict())

@api_router.post("/auth/login")
async def login(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token({"user_id": user["id"], "role": user["role"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(**user)
    }

# Teacher Routes
@api_router.post("/teachers", response_model=Teacher)
async def create_teacher(teacher_data: TeacherCreate, current_user: User = Depends(get_current_user)):
    teacher = Teacher(**teacher_data.dict())
    await db.teachers.insert_one(teacher.dict())
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "teacher_created",
        {
            "teacher_id": teacher.id,
            "teacher": teacher.dict()
        },
        current_user.id,
        current_user.name
    )
    
    return teacher

@api_router.get("/teachers", response_model=List[Teacher])
async def get_teachers():
    teachers = await db.teachers.find().to_list(1000)
    return [Teacher(**teacher) for teacher in teachers]

@api_router.get("/teachers/{teacher_id}", response_model=Teacher)
async def get_teacher(teacher_id: str):
    teacher = await db.teachers.find_one({"id": teacher_id})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return Teacher(**teacher)

# Class Routes
@api_router.post("/classes", response_model=ClassResponse)
async def create_class(class_data: ClassCreate):
    # Verify teacher exists
    teacher = await db.teachers.find_one({"id": class_data.teacher_id})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Create class
    dance_class = DanceClass(**class_data.dict())
    await db.classes.insert_one(dance_class.dict())
    
    # Return class with teacher name
    return ClassResponse(
        **dance_class.dict(),
        teacher_name=teacher["name"]
    )

@api_router.get("/classes", response_model=List[ClassResponse])
async def get_classes():
    classes = await db.classes.find().to_list(1000)
    
    # Enrich with teacher names
    result = []
    for class_doc in classes:
        teacher = await db.teachers.find_one({"id": class_doc["teacher_id"]})
        teacher_name = teacher["name"] if teacher else "Unknown"
        result.append(ClassResponse(**class_doc, teacher_name=teacher_name))
    
    return result

@api_router.get("/classes/{class_id}", response_model=ClassResponse)
async def get_class(class_id: str):
    class_doc = await db.classes.find_one({"id": class_id})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")
    
    teacher = await db.teachers.find_one({"id": class_doc["teacher_id"]})
    teacher_name = teacher["name"] if teacher else "Unknown"
    
    return ClassResponse(**class_doc, teacher_name=teacher_name)

@api_router.put("/classes/{class_id}", response_model=ClassResponse)
async def update_class(class_id: str, class_data: ClassCreate):
    # Verify class exists
    existing_class = await db.classes.find_one({"id": class_id})
    if not existing_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Verify teacher exists
    teacher = await db.teachers.find_one({"id": class_data.teacher_id})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Update class
    update_data = class_data.dict()
    await db.classes.update_one({"id": class_id}, {"$set": update_data})
    
    # Get updated class
    updated_class = await db.classes.find_one({"id": class_id})
    return ClassResponse(**updated_class, teacher_name=teacher["name"])

@api_router.delete("/classes/{class_id}")
async def delete_class(class_id: str):
    result = await db.classes.delete_one({"id": class_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Class not found")
    return {"message": "Class deleted successfully"}

# Calendar Routes
@api_router.get("/calendar/weekly")
async def get_weekly_calendar(start_date: str):
    try:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Get classes for the week (7 days from start_date)
    from datetime import timedelta
    end_date = start + timedelta(days=7)
    
    classes = await db.classes.find({
        "start_datetime": {"$gte": start, "$lt": end_date}
    }).sort("start_datetime", 1).to_list(1000)
    
    # Enrich with teacher names
    result = []
    for class_doc in classes:
        teacher = await db.teachers.find_one({"id": class_doc["teacher_id"]})
        teacher_name = teacher["name"] if teacher else "Unknown"
        result.append(ClassResponse(**class_doc, teacher_name=teacher_name))
    
    return result

# Student Routes
@api_router.post("/students", response_model=Student)
async def create_student(student_data: StudentCreate, current_user: dict = Depends(get_current_user)):
    student = Student(**student_data.dict())
    await db.students.insert_one(student.dict())
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "student_created",
        {
            "student_id": student.id,
            "student": student.dict()
        },
        current_user.id,
        current_user.name
    )
    
    return student

@api_router.get("/students", response_model=List[Student])
async def get_students():
    students = await db.students.find().to_list(1000)
    return [Student(**student) for student in students]

@api_router.get("/students/{student_id}", response_model=Student)
async def get_student(student_id: str):
    student = await db.students.find_one({"id": student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return Student(**student)

@api_router.put("/students/{student_id}", response_model=Student)
async def update_student(student_id: str, student_data: StudentCreate, current_user: dict = Depends(get_current_user)):
    existing_student = await db.students.find_one({"id": student_id})
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    update_data = student_data.dict()
    await db.students.update_one({"id": student_id}, {"$set": update_data})
    
    updated_student = await db.students.find_one({"id": student_id})
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "student_updated",
        {
            "student_id": student_id,
            "student": updated_student
        },
        current_user.id,
        current_user.name
    )
    
    return Student(**updated_student)

@api_router.delete("/students/{student_id}")
async def delete_student(student_id: str, current_user: dict = Depends(get_current_user)):
    # Check if student exists
    existing_student = await db.students.find_one({"id": student_id})
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check for associated lessons
    associated_lessons = await db.lessons.count_documents({"student_id": student_id})
    associated_enrollments = await db.enrollments.count_documents({"student_id": student_id})
    
    # Delete the student
    result = await db.students.delete_one({"id": student_id})
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "student_deleted",
        {
            "student_id": student_id,
            "student_name": existing_student.get("name", "Unknown"),
            "associated_lessons": associated_lessons,
            "associated_enrollments": associated_enrollments
        },
        current_user.id,
        current_user.name
    )
    
    return {
        "message": "Student deleted successfully",
        "associated_lessons": associated_lessons,
        "associated_enrollments": associated_enrollments,
        "note": "Associated lessons and enrollments remain in system for record keeping"
    }

@api_router.delete("/teachers/{teacher_id}")
async def delete_teacher(teacher_id: str, current_user: dict = Depends(get_current_user)):
    # Check if teacher exists
    existing_teacher = await db.teachers.find_one({"id": teacher_id})
    if not existing_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Check for associated lessons and classes
    associated_lessons = await db.lessons.count_documents({"teacher_id": teacher_id})
    associated_classes = await db.classes.count_documents({"teacher_id": teacher_id})
    
    # Delete the teacher
    result = await db.teachers.delete_one({"id": teacher_id})
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "teacher_deleted",
        {
            "teacher_id": teacher_id,
            "teacher_name": existing_teacher.get("name", "Unknown"),
            "associated_lessons": associated_lessons,
            "associated_classes": associated_classes
        },
        current_user.id,
        current_user.name
    )
    
    return {
        "message": "Teacher deleted successfully", 
        "associated_lessons": associated_lessons,
        "associated_classes": associated_classes,
        "note": "Associated lessons and classes remain in system for record keeping"
    }

# Enrollment Routes
@api_router.post("/enrollments", response_model=Enrollment)
async def create_enrollment(enrollment_data: EnrollmentCreate):
    # Verify student exists
    student = await db.students.find_one({"id": enrollment_data.student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Verify package exists
    package = await db.packages.find_one({"id": enrollment_data.package_id})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    # Create enrollment
    enrollment = Enrollment(
        **enrollment_data.dict(),
        remaining_lessons=package["total_lessons"]
    )
    await db.enrollments.insert_one(enrollment.dict())
    return enrollment

@api_router.get("/enrollments", response_model=List[Enrollment])
async def get_enrollments():
    enrollments = await db.enrollments.find().to_list(1000)
    return [Enrollment(**enrollment) for enrollment in enrollments]

@api_router.get("/students/{student_id}/enrollments", response_model=List[Enrollment])
async def get_student_enrollments(student_id: str):
    enrollments = await db.enrollments.find({"student_id": student_id, "is_active": True}).to_list(1000)
    return [Enrollment(**enrollment) for enrollment in enrollments]

# Private Lesson Routes
@api_router.post("/lessons", response_model=PrivateLessonResponse)
async def create_private_lesson(lesson_data: PrivateLessonCreate):
    # Verify student exists
    student = await db.students.find_one({"id": lesson_data.student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Verify teacher exists
    teacher = await db.teachers.find_one({"id": lesson_data.teacher_id})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Parse the datetime - handle both formats
    if isinstance(lesson_data.start_datetime, str):
        # If it's a string without timezone info, treat as local time
        if 'T' in lesson_data.start_datetime and not lesson_data.start_datetime.endswith('Z'):
            start_datetime = datetime.fromisoformat(lesson_data.start_datetime.replace('Z', ''))
        else:
            start_datetime = datetime.fromisoformat(lesson_data.start_datetime.replace('Z', ''))
    else:
        start_datetime = lesson_data.start_datetime
    
    # Calculate end time
    end_datetime = start_datetime + timedelta(minutes=lesson_data.duration_minutes)
    
    print(f"Creating lesson at: {start_datetime} (local time)")
    
    # Create lesson
    lesson = PrivateLesson(
        student_id=lesson_data.student_id,
        teacher_id=lesson_data.teacher_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        notes=lesson_data.notes,
        enrollment_id=lesson_data.enrollment_id
    )
    
    await db.lessons.insert_one(lesson.dict())
    
    return PrivateLessonResponse(
        **lesson.dict(),
        student_name=student["name"],
        teacher_name=teacher["name"]
    )

@api_router.get("/lessons", response_model=List[PrivateLessonResponse])
async def get_private_lessons():
    lessons = await db.lessons.find().to_list(1000)
    
    # Enrich with student and teacher names
    result = []
    for lesson_doc in lessons:
        student = await db.students.find_one({"id": lesson_doc["student_id"]})
        teacher = await db.teachers.find_one({"id": lesson_doc["teacher_id"]})
        
        student_name = student["name"] if student else "Unknown"
        teacher_name = teacher["name"] if teacher else "Unknown"
        
        result.append(PrivateLessonResponse(
            **lesson_doc,
            student_name=student_name,
            teacher_name=teacher_name
        ))
    
    return result

@api_router.get("/lessons/{lesson_id}", response_model=PrivateLessonResponse)
async def get_private_lesson(lesson_id: str):
    lesson = await db.lessons.find_one({"id": lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    student = await db.students.find_one({"id": lesson["student_id"]})
    teacher = await db.teachers.find_one({"id": lesson["teacher_id"]})
    
    return PrivateLessonResponse(
        **lesson,
        student_name=student["name"] if student else "Unknown",
        teacher_name=teacher["name"] if teacher else "Unknown"
    )

@api_router.put("/lessons/{lesson_id}", response_model=PrivateLessonResponse)
async def update_private_lesson(lesson_id: str, lesson_data: PrivateLessonUpdate, current_user: dict = Depends(get_current_user)):
    # Verify lesson exists
    existing_lesson = await db.lessons.find_one({"id": lesson_id})
    if not existing_lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Prepare update data
    update_data = {}
    for field, value in lesson_data.dict().items():
        if value is not None:
            update_data[field] = value
    
    # Add modification tracking
    update_data["modified_at"] = datetime.utcnow()
    update_data["modified_by"] = current_user.id
    
    # If updating datetime and duration, recalculate end_datetime
    if "start_datetime" in update_data:
        # Handle timezone properly
        if isinstance(update_data["start_datetime"], str):
            if 'T' in update_data["start_datetime"] and not update_data["start_datetime"].endswith('Z'):
                update_data["start_datetime"] = datetime.fromisoformat(update_data["start_datetime"].replace('Z', ''))
        
        if "duration_minutes" in update_data:
            update_data["end_datetime"] = update_data["start_datetime"] + timedelta(minutes=update_data["duration_minutes"])
        else:
            # Keep the same duration
            original_duration = (existing_lesson["end_datetime"] - existing_lesson["start_datetime"]).seconds // 60
            update_data["end_datetime"] = update_data["start_datetime"] + timedelta(minutes=original_duration)
    
    print(f"Updating lesson to: {update_data.get('start_datetime', 'no time change')}")
    
    await db.lessons.update_one({"id": lesson_id}, {"$set": update_data})
    
    # Get updated lesson with enriched data
    updated_lesson = await db.lessons.find_one({"id": lesson_id})
    student = await db.students.find_one({"id": updated_lesson["student_id"]})
    teacher = await db.teachers.find_one({"id": updated_lesson["teacher_id"]})
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "lesson_updated",
        {
            "lesson_id": lesson_id,
            "lesson": updated_lesson,
            "student_name": student["name"] if student else "Unknown",
            "teacher_name": teacher["name"] if teacher else "Unknown"
        },
        current_user.id,
        current_user.name
    )
    
    return PrivateLessonResponse(
        **updated_lesson,
        student_name=student["name"] if student else "Unknown",
        teacher_name=teacher["name"] if teacher else "Unknown"
    )

@api_router.delete("/lessons/{lesson_id}")
async def delete_private_lesson(lesson_id: str, current_user: dict = Depends(get_current_user)):
    # Check if this is part of a recurring series
    lesson = await db.lessons.find_one({"id": lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    result = await db.lessons.delete_one({"id": lesson_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "lesson_deleted",
        {
            "lesson_id": lesson_id,
            "recurring_series_id": lesson.get("recurring_series_id")
        },
        current_user.id,
        current_user.name
    )
    
    return {"message": "Lesson deleted successfully"}

# Recurring Lesson Endpoints
@api_router.post("/recurring-lessons", response_model=dict)
async def create_recurring_lesson_series(series_data: RecurringLessonCreate, current_user: User = Depends(get_current_user)):
    """Create a new recurring lesson series and generate individual lesson instances"""
    
    # Create the recurring series record
    series = RecurringLessonSeries(
        **series_data.dict(),
        created_by=current_user.id
    )
    
    # Generate individual lesson instances
    lessons = generate_recurring_lessons(series)
    
    # Store the series
    await db.recurring_series.insert_one(series.dict())
    
    # Store all lesson instances
    lesson_dicts = [lesson.dict() for lesson in lessons]
    if lesson_dicts:
        await db.lessons.insert_many(lesson_dicts)
    
    # Get student and teacher names for response
    student = await db.students.find_one({"id": series.student_id})
    teacher = await db.teachers.find_one({"id": series.teacher_id})
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "recurring_series_created",
        {
            "series_id": series.id,
            "series": series.dict(),
            "lessons_count": len(lessons),
            "student_name": student["name"] if student else "Unknown",
            "teacher_name": teacher["name"] if teacher else "Unknown"
        },
        current_user.id,
        current_user.name
    )
    
    return {
        "series_id": series.id,
        "lessons_created": len(lessons),
        "series": series.dict(),
        "student_name": student["name"] if student else "Unknown",
        "teacher_name": teacher["name"] if teacher else "Unknown"
    }

@api_router.get("/recurring-lessons")
async def get_recurring_lesson_series():
    """Get all active recurring lesson series"""
    series_list = await db.recurring_series.find({"is_active": True}).to_list(1000)
    
    # Enrich with student and teacher names
    enriched_series = []
    for series in series_list:
        student = await db.students.find_one({"id": series["student_id"]})
        teacher = await db.teachers.find_one({"id": series["teacher_id"]})
        series["student_name"] = student["name"] if student else "Unknown"
        series["teacher_name"] = teacher["name"] if teacher else "Unknown"
        enriched_series.append(series)
    
    return enriched_series

@api_router.delete("/recurring-lessons/{series_id}")
async def cancel_recurring_lesson_series(series_id: str, current_user: User = Depends(get_current_user)):
    """Cancel an entire recurring lesson series and all future lessons"""
    
    # Mark series as inactive
    result = await db.recurring_series.update_one(
        {"id": series_id}, 
        {"$set": {"is_active": False}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recurring series not found")
    
    # Cancel all future lessons in the series (after today)
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    cancel_result = await db.lessons.update_many(
        {
            "recurring_series_id": series_id,
            "start_datetime": {"$gte": today},
            "is_attended": False
        },
        {"$set": {"is_cancelled": True, "cancellation_reason": "Series cancelled"}}
    )
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "recurring_series_cancelled",
        {
            "series_id": series_id,
            "cancelled_lessons_count": cancel_result.modified_count
        },
        current_user.id,
        current_user.name
    )
    
    return {
        "message": "Recurring series cancelled successfully",
        "cancelled_lessons_count": cancel_result.modified_count
    }

@api_router.post("/lessons/{lesson_id}/attend")
async def mark_lesson_attended(lesson_id: str, current_user: dict = Depends(get_current_user)):
    # Get lesson
    lesson = await db.lessons.find_one({"id": lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Mark as attended
    await db.lessons.update_one(
        {"id": lesson_id}, 
        {
            "$set": {
                "is_attended": True,
                "modified_at": datetime.utcnow(),
                "modified_by": current_user.id
            }
        }
    )
    
    # If lesson has enrollment, deduct from remaining lessons
    if lesson.get("enrollment_id"):
        enrollment = await db.enrollments.find_one({"id": lesson["enrollment_id"]})
        if enrollment and enrollment["remaining_lessons"] > 0:
            await db.enrollments.update_one(
                {"id": lesson["enrollment_id"]}, 
                {"$inc": {"remaining_lessons": -1}}
            )
    
    # Get enriched lesson data for broadcast
    student = await db.students.find_one({"id": lesson["student_id"]})
    teacher = await db.teachers.find_one({"id": lesson["teacher_id"]})
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "lesson_attended",
        {
            "lesson_id": lesson_id,
            "student_name": student["name"] if student else "Unknown",
            "teacher_name": teacher["name"] if teacher else "Unknown",
            "start_datetime": lesson["start_datetime"]
        },
        current_user.get("id", "unknown"),
        current_user.get("name", "Unknown User")
    )
    
    return {"message": "Attendance marked successfully"}

# Daily Calendar Route
@api_router.get("/calendar/daily/{date}")
async def get_daily_calendar(date: str):
    try:
        day = datetime.fromisoformat(date).replace(hour=0, minute=0, second=0, microsecond=0)
        next_day = day + timedelta(days=1)
        
        # Get private lessons for the day
        lessons = await db.lessons.find({
            "start_datetime": {"$gte": day, "$lt": next_day}
        }).to_list(1000)
        
        # Get all teachers for columns
        teachers = await db.teachers.find().to_list(1000)
        
        # Enrich lessons with student and teacher names
        enriched_lessons = []
        for lesson_doc in lessons:
            student = await db.students.find_one({"id": lesson_doc["student_id"]})
            teacher = await db.teachers.find_one({"id": lesson_doc["teacher_id"]})
            
            enriched_lessons.append(PrivateLessonResponse(
                **lesson_doc,
                student_name=student["name"] if student else "Unknown",
                teacher_name=teacher["name"] if teacher else "Unknown"
            ))
        
        return {
            "date": date,
            "teachers": [Teacher(**teacher) for teacher in teachers],
            "lessons": enriched_lessons
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

# Package Routes (for pre-defined lesson packages)
@api_router.get("/packages", response_model=List[LessonPackage])
async def get_packages():
    packages = await db.packages.find().to_list(1000)
    return [LessonPackage(**package) for package in packages]

@api_router.post("/packages", response_model=LessonPackage)
async def create_package(package_data: LessonPackage):
    await db.packages.insert_one(package_data.dict())
    return package_data

# Dashboard stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    total_classes = await db.classes.count_documents({})
    total_teachers = await db.teachers.count_documents({})
    total_students = await db.students.count_documents({})
    active_enrollments = await db.enrollments.count_documents({"is_active": True})
    
    # Classes today
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    classes_today = await db.classes.count_documents({
        "start_datetime": {"$gte": today, "$lt": tomorrow}
    })
    
    # Private lessons today
    lessons_today = await db.lessons.count_documents({
        "start_datetime": {"$gte": today, "$lt": tomorrow}
    })
    
    # Lessons attended today
    lessons_attended_today = await db.lessons.count_documents({
        "start_datetime": {"$gte": today, "$lt": tomorrow},
        "is_attended": True
    })
    
    # Calculate estimated monthly revenue from active enrollments
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": None, "total_revenue": {"$sum": "$total_paid"}}}
    ]
    revenue_result = await db.enrollments.aggregate(pipeline).to_list(1)
    estimated_monthly_revenue = revenue_result[0]["total_revenue"] if revenue_result else 0
    
    return {
        "total_classes": total_classes,
        "total_teachers": total_teachers,
        "total_students": total_students,
        "active_enrollments": active_enrollments,
        "classes_today": classes_today,
        "lessons_today": lessons_today,
        "lessons_attended_today": lessons_attended_today,
        "estimated_monthly_revenue": estimated_monthly_revenue
    }

# Initialize default packages on startup
@app.on_event("startup")
async def create_default_packages():
    # Check if packages already exist
    existing_packages = await db.packages.count_documents({})
    if existing_packages == 0:
        default_packages = [
            LessonPackage(
                name="4-Lesson Package",
                total_lessons=4,
                price=200.0,
                expiry_days=60,
                description="Perfect for beginners - 4 private lessons"
            ),
            LessonPackage(
                name="8-Lesson Package",
                total_lessons=8,
                price=380.0,
                expiry_days=90,
                description="Most popular - 8 private lessons with discount"
            ),
            LessonPackage(
                name="Monthly Unlimited",
                total_lessons=999,
                price=500.0,
                expiry_days=30,
                description="Unlimited private lessons for one month"
            ),
        ]
        
        for package in default_packages:
            await db.packages.insert_one(package.dict())

# Notification Preferences Routes
@api_router.post("/notifications/preferences", response_model=NotificationPreference)
async def create_notification_preference(pref_data: NotificationPreferenceCreate):
    # Check if student exists
    student = await db.students.find_one({"id": pref_data.student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check if preferences already exist for this student
    existing_pref = await db.notification_preferences.find_one({"student_id": pref_data.student_id})
    if existing_pref:
        # Update existing preferences
        update_data = pref_data.dict()
        await db.notification_preferences.update_one(
            {"student_id": pref_data.student_id}, 
            {"$set": update_data}
        )
        updated_pref = await db.notification_preferences.find_one({"student_id": pref_data.student_id})
        return NotificationPreference(**updated_pref)
    else:
        # Create new preferences
        pref = NotificationPreference(**pref_data.dict())
        await db.notification_preferences.insert_one(pref.dict())
        return pref

@api_router.get("/notifications/preferences/{student_id}", response_model=NotificationPreference)
async def get_notification_preferences(student_id: str):
    pref = await db.notification_preferences.find_one({"student_id": student_id})
    if not pref:
        # Return default preferences if none exist
        return NotificationPreference(
            student_id=student_id,
            email_enabled=True,
            sms_enabled=False,
            reminder_hours=24
        )
    return NotificationPreference(**pref)

@api_router.post("/notifications/send-reminder")
async def send_lesson_reminder(reminder_request: ReminderRequest):
    # Get lesson details
    lesson = await db.lessons.find_one({"id": reminder_request.lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Get student details
    student = await db.students.find_one({"id": lesson["student_id"]})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get teacher details
    teacher = await db.teachers.find_one({"id": lesson["teacher_id"]})
    teacher_name = teacher["name"] if teacher else "Unknown"
    
    # Get notification preferences
    pref = await db.notification_preferences.find_one({"student_id": lesson["student_id"]})
    
    lesson_datetime = lesson["start_datetime"]
    formatted_datetime = lesson_datetime.strftime("%B %d, %Y at %I:%M %p")
    
    default_message = f"Hi {student['name']}, this is a reminder that you have a dance lesson scheduled for {formatted_datetime} with {teacher_name}. See you there!"
    message = reminder_request.message or default_message
    
    if reminder_request.notification_type == "email":
        if not pref or not pref.get("email_enabled", True):
            raise HTTPException(status_code=400, detail="Email notifications not enabled for this student")
        
        email_address = (pref.get("email_address") if pref else None) or student["email"]
        
        # Here you would integrate with your email service (SendGrid, Gmail, etc.)
        # For now, we'll log the message
        print(f"📧 EMAIL REMINDER: To {email_address}: {message}")
        
        return {
            "message": "Email reminder sent successfully",
            "recipient": email_address,
            "content": message,
            "lesson_datetime": formatted_datetime
        }
    
    elif reminder_request.notification_type == "sms":
        if not pref or not pref.get("sms_enabled", False):
            raise HTTPException(status_code=400, detail="SMS notifications not enabled for this student")
        
        phone_number = (pref.get("phone_number") if pref else None) or student.get("phone")
        if not phone_number:
            raise HTTPException(status_code=400, detail="No phone number available for SMS")
        
        # Clean phone number (remove spaces, dashes, etc.)
        clean_phone = ''.join(filter(str.isdigit, phone_number))
        if not clean_phone.startswith('1') and len(clean_phone) == 10:
            clean_phone = '1' + clean_phone
        if len(clean_phone) == 11:
            clean_phone = '+' + clean_phone
        
        if twilio_client and TWILIO_PHONE_NUMBER:
            try:
                # Send real SMS via Twilio
                message = twilio_client.messages.create(
                    body=message,
                    from_=TWILIO_PHONE_NUMBER,
                    to=clean_phone
                )
                print(f"✅ SMS sent successfully! Message SID: {message.sid}")
                
                return {
                    "message": "SMS reminder sent successfully via Twilio",
                    "recipient": clean_phone,
                    "content": message,
                    "lesson_datetime": formatted_datetime,
                    "sms_sid": message.sid
                }
            except Exception as e:
                print(f"❌ Twilio SMS failed: {str(e)}")
                # Fall back to free TextBelt API
                return await send_textbelt_sms(clean_phone, message, formatted_datetime)
        else:
            # Try free TextBelt API
            return await send_textbelt_sms(clean_phone, message, formatted_datetime)

# Free SMS function using TextBelt
async def send_textbelt_sms(phone_number, message, formatted_datetime):
    try:
        response = requests.post('https://textbelt.com/text', {
            'phone': phone_number,
            'message': message,
            'key': 'textbelt',  # Free tier key
        })
        result = response.json()
        
        if result.get('success'):
            print(f"✅ SMS sent via TextBelt! Text ID: {result.get('textId', 'unknown')}")
            return {
                "message": "SMS reminder sent successfully via TextBelt (Free)",
                "recipient": phone_number,
                "content": message,
                "lesson_datetime": formatted_datetime,
                "textbelt_id": result.get('textId')
            }
        else:
            print(f"❌ TextBelt SMS failed: {result.get('error', 'Unknown error')}")
            # Final fallback to simulation
            print(f"📱 SMS REMINDER (SIMULATED): To {phone_number}: {message}")
            return {
                "message": "SMS reminder simulated (all services failed)",
                "recipient": phone_number,
                "content": message,
                "lesson_datetime": formatted_datetime,
                "error": result.get('error')
            }
    except Exception as e:
        print(f"❌ TextBelt API error: {str(e)}")
        print(f"📱 SMS REMINDER (SIMULATED): To {phone_number}: {message}")
        return {
            "message": "SMS reminder simulated (API error)",
            "recipient": phone_number,
            "content": message,
            "lesson_datetime": formatted_datetime,
            "error": str(e)
        }
    
    else:
        raise HTTPException(status_code=400, detail="Invalid notification type")

@api_router.get("/notifications/upcoming-lessons")
async def get_upcoming_lessons_for_reminders():
    # Get lessons in the next 48 hours that haven't been attended yet
    now = datetime.utcnow()
    end_time = now + timedelta(hours=48)
    
    lessons = await db.lessons.find({
        "start_datetime": {"$gte": now, "$lte": end_time},
        "is_attended": False
    }).to_list(1000)
    
    # Enrich with student and teacher data
    enriched_lessons = []
    for lesson_doc in lessons:
        student = await db.students.find_one({"id": lesson_doc["student_id"]})
        teacher = await db.teachers.find_one({"id": lesson_doc["teacher_id"]})
        
        # Create a clean lesson dict without MongoDB ObjectId
        clean_lesson = {
            "id": lesson_doc["id"],
            "student_id": lesson_doc["student_id"],
            "teacher_id": lesson_doc["teacher_id"],
            "start_datetime": lesson_doc["start_datetime"],
            "end_datetime": lesson_doc["end_datetime"],
            "notes": lesson_doc.get("notes"),
            "is_attended": lesson_doc.get("is_attended", False),
            "enrollment_id": lesson_doc.get("enrollment_id"),
            "student_name": student["name"] if student else "Unknown",
            "student_email": student["email"] if student else None,
            "student_phone": student.get("phone") if student else None,
            "teacher_name": teacher["name"] if teacher else "Unknown"
        }
        
        enriched_lessons.append(clean_lesson)
    
    return enriched_lessons

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            # Handle client messages if needed (like ping/pong)
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# Mount static files for production deployment
build_dir = Path(__file__).parent.parent / "frontend" / "build"

print(f"🔍 Looking for React build at: {build_dir}")
print(f"📁 Build directory exists: {build_dir.exists()}")

if build_dir.exists():
    # Mount the React build's static directory
    static_files_dir = build_dir / "static"
    if static_files_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_files_dir)), name="static")
        static_root = build_dir
        print(f"✅ Serving static files from React build: {static_files_dir}")
        print(f"📄 Index.html exists: {(build_dir / 'index.html').exists()}")
    else:
        print(f"⚠️ Static files directory not found: {static_files_dir}")
        static_root = None
else:
    print(f"❌ React build directory not found: {build_dir}")
    static_root = None

# Serve React app for all non-API routes
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # API routes should return 404 if not found
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Handle root path - serve index.html
    if not full_path or full_path == "/":
        index_file = build_dir / "index.html"
        if index_file.exists():
            print(f"📄 Serving index.html from: {index_file}")
            return FileResponse(str(index_file), media_type="text/html")
    
    # Try to serve static files directly (for non-/static prefixed paths)
    if static_root and full_path:
        static_file_path = static_root / full_path
        if static_file_path.is_file():
            return FileResponse(str(static_file_path))
    
    # For all other paths, serve the React app index.html
    index_file = build_dir / "index.html"
    if index_file.exists():
        print(f"📄 Serving React app index.html from: {index_file}")
        return FileResponse(str(index_file), media_type="text/html")
    
    # Fallback: return simple HTML with error info
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head><title>Dance Studio CRM</title></head>
    <body>
        <h1>Dance Studio CRM</h1>
        <p>Frontend build not found. Please check deployment.</p>
        <p><a href="/docs">API Documentation</a></p>
        <p><a href="/api/dashboard/stats">API Test</a></p>
    </body>
    </html>
    """)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()