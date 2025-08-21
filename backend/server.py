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
from typing import List, Optional, Dict, Any, Union
import uuid
from datetime import datetime, date, time, timedelta
from enum import Enum
import jwt
from passlib.context import CryptContext
import hashlib
import json
import asyncio
import bcrypt

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
        # Convert datetime and ObjectId objects to JSON serializable formats
        def convert_objects(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'ObjectId':
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_objects(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_objects(item) for item in obj]
            return obj
        
        message = {
            "type": update_type,
            "data": convert_objects(data),
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

class BookingType(str, Enum):
    PRIVATE_LESSON = "private_lesson"
    MEETING = "meeting"
    TRAINING = "training"
    PARTY = "party"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: UserRole
    hashed_password: str
    studio_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

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

# New Dance Program model to replace LessonPackage
class DanceProgram(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    level: str  # Bronze, Silver, Gold, Beginner, etc.
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LessonPackage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    total_lessons: int
    price: float
    expiry_days: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Settings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str  # "business", "system", "program", "notification"
    key: str  # Setting key name
    value: Union[str, int, float, bool, List[str]]  # Setting value
    data_type: str  # "string", "integer", "float", "boolean", "array"
    description: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None

class SettingsUpdate(BaseModel):
    value: Union[str, int, float, bool, List[str]]
    updated_by: Optional[str] = None

# Settings response models
class SettingsResponse(BaseModel):
    id: str
    category: str
    key: str
    value: Union[str, int, float, bool, List[str]]
    data_type: str
    description: Optional[str] = None
    updated_at: datetime
    updated_by: Optional[str] = None

class Enrollment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    program_name: str  # Changed from package_id to program_name
    total_lessons: int  # Total lessons for this enrollment
    remaining_lessons: int
    total_paid: float
    purchase_date: datetime = Field(default_factory=datetime.utcnow)
    expiry_date: Optional[datetime] = None
    is_active: bool = True

class EnrollmentCreate(BaseModel):
    student_id: str
    program_name: str
    total_lessons: int  # Allow custom lesson numbers
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
    teacher_ids: List[str]  # Changed from teacher_id to support multiple teachers
    start_datetime: datetime
    end_datetime: datetime
    booking_type: BookingType = BookingType.PRIVATE_LESSON  # Added booking type
    notes: Optional[str] = None
    is_attended: bool = False
    enrollment_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Recurring lesson support
    recurring_series_id: Optional[str] = None
    # Cancellation support
    is_cancelled: bool = False
    cancellation_reason: Optional[str] = None
    modified_at: datetime = Field(default_factory=datetime.utcnow)
    modified_by: Optional[str] = None

class PrivateLessonCreate(BaseModel):
    student_id: str
    teacher_ids: List[str]  # Changed from teacher_id to support multiple teachers
    start_datetime: datetime
    duration_minutes: int = 60
    booking_type: BookingType = BookingType.PRIVATE_LESSON  # Added booking type
    notes: Optional[str] = None
    enrollment_id: Optional[str] = None

class PrivateLessonUpdate(BaseModel):
    student_id: Optional[str] = None
    teacher_ids: Optional[List[str]] = None  # Changed from teacher_id to support multiple teachers
    booking_type: Optional[BookingType] = None
    start_datetime: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    enrollment_id: Optional[str] = None

class PrivateLessonResponse(BaseModel):
    id: str
    student_id: str
    student_name: str
    teacher_ids: List[str]  # Changed from teacher_id to support multiple teachers
    teacher_names: List[str]  # Changed from teacher_name to support multiple teachers
    start_datetime: datetime
    end_datetime: datetime
    booking_type: BookingType = BookingType.PRIVATE_LESSON  # Added booking type
    notes: Optional[str] = None
    is_attended: bool = False
    enrollment_id: Optional[str] = None
    recurring_series_id: Optional[str] = None
    is_cancelled: bool = False
    cancellation_reason: Optional[str] = None

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    enrollment_id: Optional[str] = None  # Link to specific enrollment
    amount: float
    payment_method: str = "cash"  # cash, credit_card, check, etc.
    payment_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PaymentCreate(BaseModel):
    student_id: str
    enrollment_id: Optional[str] = None
    amount: float
    payment_method: str = "cash"
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None

class StudentLedgerResponse(BaseModel):
    student: Student
    enrollments: List[Enrollment]
    payments: List[Payment]
    upcoming_lessons: List[PrivateLessonResponse]
    lesson_history: List[PrivateLessonResponse]
    total_paid: float
    total_enrolled_lessons: int
    remaining_lessons: int
    lessons_taken: int

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

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class PasswordUpdate(BaseModel):
    old_password: Optional[str] = None
    new_password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole
    studio_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

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

class TeacherResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    specialties: List[ClassType]
    bio: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime
    is_active: bool = True

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
            
        # Calculate end datetime
        end_datetime = current_date + timedelta(minutes=series.duration_minutes)
        
        # Create lesson instance
        lesson = PrivateLesson(
            student_id=series.student_id,
            teacher_id=series.teacher_id,
            start_datetime=current_date,
            end_datetime=end_datetime,
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
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
async def create_student(student_data: StudentCreate, current_user: User = Depends(get_current_user)):
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
async def update_student(student_id: str, student_data: StudentCreate, current_user: User = Depends(get_current_user)):
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
async def delete_student(student_id: str, current_user: User = Depends(get_current_user)):
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

@api_router.put("/teachers/{teacher_id}", response_model=Teacher)
async def update_teacher(teacher_id: str, teacher_data: TeacherCreate, current_user: User = Depends(get_current_user)):
    existing_teacher = await db.teachers.find_one({"id": teacher_id})
    if not existing_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    update_data = teacher_data.dict()
    await db.teachers.update_one({"id": teacher_id}, {"$set": update_data})
    
    updated_teacher = await db.teachers.find_one({"id": teacher_id})
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "teacher_updated",
        {
            "teacher_id": teacher_id,
            "teacher": updated_teacher
        },
        current_user.id,
        current_user.name
    )
    
    return Teacher(**updated_teacher)

@api_router.delete("/teachers/{teacher_id}")
async def delete_teacher(teacher_id: str, current_user: User = Depends(get_current_user)):
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

# Payment Management Routes
@api_router.post("/payments", response_model=Payment)
async def create_payment(payment_data: PaymentCreate, current_user: User = Depends(get_current_user)):
    # Verify student exists
    student = await db.students.find_one({"id": payment_data.student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Verify enrollment exists if provided
    if payment_data.enrollment_id:
        enrollment = await db.enrollments.find_one({"id": payment_data.enrollment_id})
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")
    
    # Create payment
    payment_dict = payment_data.dict()
    if not payment_dict.get('payment_date'):
        payment_dict['payment_date'] = datetime.utcnow()
    
    payment = Payment(
        **payment_dict,
        created_by=current_user.id
    )
    
    await db.payments.insert_one(payment.dict())
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "payment_created",
        {
            "payment_id": payment.id,
            "student_id": payment.student_id,
            "amount": payment.amount,
            "payment_method": payment.payment_method
        },
        current_user.id,
        current_user.name
    )
    
    return payment

@api_router.get("/payments", response_model=List[Payment])
async def get_payments():
    payments = await db.payments.find().to_list(1000)
    return [Payment(**payment) for payment in payments]

@api_router.get("/students/{student_id}/payments", response_model=List[Payment])
async def get_student_payments(student_id: str):
    payments = await db.payments.find({"student_id": student_id}).sort("payment_date", -1).to_list(1000)
    return [Payment(**payment) for payment in payments]

@api_router.delete("/payments/{payment_id}")
async def delete_payment(payment_id: str, current_user: User = Depends(get_current_user)):
    payment = await db.payments.find_one({"id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    result = await db.payments.delete_one({"id": payment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "payment_deleted",
        {
            "payment_id": payment_id,
            "student_id": payment.get("student_id"),
            "amount": payment.get("amount")
        },
        current_user.id,
        current_user.name
    )
    
    return {"message": "Payment deleted successfully"}

# Student Ledger Route
@api_router.get("/students/{student_id}/ledger", response_model=StudentLedgerResponse)
async def get_student_ledger(student_id: str):
    # Get student
    student = await db.students.find_one({"id": student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get enrollments (with migration handling)
    enrollments_data = await db.enrollments.find({"student_id": student_id}).sort("purchase_date", -1).to_list(1000)
    enrollments = []
    for enrollment_doc in enrollments_data:
        # Handle migration from old package-based system
        if "package_id" in enrollment_doc and "program_name" not in enrollment_doc:
            package = await db.packages.find_one({"id": enrollment_doc["package_id"]})
            if package:
                enrollment_doc["program_name"] = f"Legacy Package: {package['name']}"
                enrollment_doc["total_lessons"] = package["total_lessons"]
            else:
                enrollment_doc["program_name"] = "Legacy Package (Unknown)"
                enrollment_doc["total_lessons"] = enrollment_doc.get("remaining_lessons", 0)
            enrollment_doc.pop("package_id", None)
        
        if "program_name" not in enrollment_doc:
            enrollment_doc["program_name"] = "Unknown Program"
        if "total_lessons" not in enrollment_doc:
            enrollment_doc["total_lessons"] = enrollment_doc.get("remaining_lessons", 0)
            
        enrollments.append(Enrollment(**enrollment_doc))
    
    # Get payments
    payments_data = await db.payments.find({"student_id": student_id}).sort("payment_date", -1).to_list(1000)
    payments = [Payment(**payment) for payment in payments_data]
    
    # Get upcoming lessons (future lessons)
    today = datetime.utcnow()
    upcoming_lessons_data = await db.lessons.find({
        "student_id": student_id,
        "start_datetime": {"$gte": today},
        "is_cancelled": {"$ne": True}
    }).sort("start_datetime", 1).to_list(1000)
    
    upcoming_lessons = []
    for lesson in upcoming_lessons_data:
        # Handle migration from old teacher_id to new teacher_ids array
        if "teacher_id" in lesson and "teacher_ids" not in lesson:
            # Migrate old single teacher_id to teacher_ids array
            lesson["teacher_ids"] = [lesson["teacher_id"]]
            lesson.pop("teacher_id", None)
        elif "teacher_ids" not in lesson:
            # Fallback if neither field exists
            lesson["teacher_ids"] = []
            
        student_doc = await db.students.find_one({"id": lesson["student_id"]})
        
        # Get all teachers for this lesson
        teacher_names = []
        for teacher_id in lesson.get("teacher_ids", []):
            teacher_doc = await db.teachers.find_one({"id": teacher_id})
            if teacher_doc:
                teacher_names.append(teacher_doc["name"])
        
        upcoming_lessons.append(PrivateLessonResponse(
            **lesson,
            student_name=student_doc["name"] if student_doc else "Unknown",
            teacher_names=teacher_names
        ))
    
    # Get lesson history (past lessons)
    lesson_history_data = await db.lessons.find({
        "student_id": student_id,
        "start_datetime": {"$lt": today}
    }).sort("start_datetime", -1).to_list(1000)
    
    lesson_history = []
    for lesson in lesson_history_data:
        # Handle migration from old teacher_id to new teacher_ids array
        if "teacher_id" in lesson and "teacher_ids" not in lesson:
            # Migrate old single teacher_id to teacher_ids array
            lesson["teacher_ids"] = [lesson["teacher_id"]]
            lesson.pop("teacher_id", None)
        elif "teacher_ids" not in lesson:
            # Fallback if neither field exists
            lesson["teacher_ids"] = []
            
        student_doc = await db.students.find_one({"id": lesson["student_id"]})
        
        # Get all teachers for this lesson
        teacher_names = []
        for teacher_id in lesson.get("teacher_ids", []):
            teacher_doc = await db.teachers.find_one({"id": teacher_id})
            if teacher_doc:
                teacher_names.append(teacher_doc["name"])
        
        lesson_history.append(PrivateLessonResponse(
            **lesson,
            student_name=student_doc["name"] if student_doc else "Unknown",
            teacher_names=teacher_names
        ))
    
    # Calculate totals
    total_paid = sum(payment.amount for payment in payments)
    total_enrolled_lessons = sum(enrollment.total_lessons for enrollment in enrollments)
    remaining_lessons = sum(enrollment.remaining_lessons for enrollment in enrollments if enrollment.is_active)
    lessons_taken = len([lesson for lesson in lesson_history if lesson.is_attended])
    
    return StudentLedgerResponse(
        student=Student(**student),
        enrollments=enrollments,
        payments=payments,
        upcoming_lessons=upcoming_lessons,
        lesson_history=lesson_history,
        total_paid=total_paid,
        total_enrolled_lessons=total_enrolled_lessons,
        remaining_lessons=remaining_lessons,
        lessons_taken=lessons_taken
    )

# Dance Programs Routes
@api_router.get("/programs", response_model=List[DanceProgram])
async def get_programs():
    programs = await db.programs.find().to_list(1000)
    return [DanceProgram(**program) for program in programs]

@api_router.get("/programs/{program_id}", response_model=DanceProgram)
async def get_program(program_id: str):
    program = await db.programs.find_one({"id": program_id})
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return DanceProgram(**program)

# Enrollment Routes
@api_router.post("/enrollments", response_model=Enrollment)
async def create_enrollment(enrollment_data: EnrollmentCreate):
    # Verify student exists
    student = await db.students.find_one({"id": enrollment_data.student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Create enrollment with the provided data
    enrollment = Enrollment(
        **enrollment_data.dict(),
        remaining_lessons=enrollment_data.total_lessons  # Use the total_lessons from the request
    )
    await db.enrollments.insert_one(enrollment.dict())
    return enrollment

@api_router.get("/enrollments", response_model=List[Enrollment])
async def get_enrollments():
    enrollments = await db.enrollments.find().to_list(1000)
    
    # Handle migration from old package-based system to new program-based system
    result = []
    for enrollment_doc in enrollments:
        # If it's an old enrollment with package_id, migrate it
        if "package_id" in enrollment_doc and "program_name" not in enrollment_doc:
            # Get package info to determine program name and total lessons
            package = await db.packages.find_one({"id": enrollment_doc["package_id"]})
            if package:
                enrollment_doc["program_name"] = f"Legacy Package: {package['name']}"
                enrollment_doc["total_lessons"] = package["total_lessons"]
            else:
                # Fallback if package not found
                enrollment_doc["program_name"] = "Legacy Package (Unknown)"
                enrollment_doc["total_lessons"] = enrollment_doc.get("remaining_lessons", 0)
            
            # Remove the old package_id field for the response
            enrollment_doc.pop("package_id", None)
        
        # Ensure required fields exist
        if "program_name" not in enrollment_doc:
            enrollment_doc["program_name"] = "Unknown Program"
        if "total_lessons" not in enrollment_doc:
            enrollment_doc["total_lessons"] = enrollment_doc.get("remaining_lessons", 0)
            
        result.append(Enrollment(**enrollment_doc))
    
    return result

@api_router.get("/students/{student_id}/enrollments", response_model=List[Enrollment])
async def get_student_enrollments(student_id: str):
    enrollments = await db.enrollments.find({"student_id": student_id, "is_active": True}).to_list(1000)
    
    # Handle migration from old package-based system to new program-based system
    result = []
    for enrollment_doc in enrollments:
        # If it's an old enrollment with package_id, migrate it
        if "package_id" in enrollment_doc and "program_name" not in enrollment_doc:
            # Get package info to determine program name and total lessons
            package = await db.packages.find_one({"id": enrollment_doc["package_id"]})
            if package:
                enrollment_doc["program_name"] = f"Legacy Package: {package['name']}"
                enrollment_doc["total_lessons"] = package["total_lessons"]
            else:
                # Fallback if package not found
                enrollment_doc["program_name"] = "Legacy Package (Unknown)"
                enrollment_doc["total_lessons"] = enrollment_doc.get("remaining_lessons", 0)
            
            # Remove the old package_id field for the response
            enrollment_doc.pop("package_id", None)
        
        # Ensure required fields exist
        if "program_name" not in enrollment_doc:
            enrollment_doc["program_name"] = "Unknown Program"
        if "total_lessons" not in enrollment_doc:
            enrollment_doc["total_lessons"] = enrollment_doc.get("remaining_lessons", 0)
            
        result.append(Enrollment(**enrollment_doc))
    
    return result

@api_router.delete("/enrollments/{enrollment_id}")
async def delete_enrollment(enrollment_id: str, current_user: User = Depends(get_current_user)):
    # Check if enrollment exists
    enrollment = await db.enrollments.find_one({"id": enrollment_id})
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    # Check for associated lessons
    associated_lessons = await db.lessons.count_documents({"enrollment_id": enrollment_id})
    
    # Delete the enrollment
    result = await db.enrollments.delete_one({"id": enrollment_id})
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "enrollment_deleted",
        {
            "enrollment_id": enrollment_id,
            "student_id": enrollment.get("student_id"),
            "program_name": enrollment.get("program_name"),
            "associated_lessons": associated_lessons
        },
        current_user.id,
        current_user.name
    )
    
    return {
        "message": "Enrollment deleted successfully",
        "associated_lessons": associated_lessons,
        "note": "Associated lessons remain in system for record keeping"
    }

# Private Lesson Routes
@api_router.post("/lessons", response_model=PrivateLessonResponse)
async def create_private_lesson(lesson_data: PrivateLessonCreate):
    # Verify student exists
    student = await db.students.find_one({"id": lesson_data.student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Verify all teachers exist and collect teacher info
    teacher_names = []
    for teacher_id in lesson_data.teacher_ids:
        teacher = await db.teachers.find_one({"id": teacher_id})
        if not teacher:
            raise HTTPException(status_code=404, detail=f"Teacher with id {teacher_id} not found")
        teacher_names.append(teacher["name"])
    
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
    
    print(f"Creating lesson at: {start_datetime} (local time) with booking type: {lesson_data.booking_type}")
    
    # Create lesson
    lesson = PrivateLesson(
        student_id=lesson_data.student_id,
        teacher_ids=lesson_data.teacher_ids,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        booking_type=lesson_data.booking_type,
        notes=lesson_data.notes,
        enrollment_id=lesson_data.enrollment_id
    )
    
    await db.lessons.insert_one(lesson.dict())
    
    return PrivateLessonResponse(
        **lesson.dict(),
        student_name=student["name"],
        teacher_names=teacher_names
    )

@api_router.get("/lessons", response_model=List[PrivateLessonResponse])
async def get_private_lessons():
    lessons = await db.lessons.find().to_list(1000)
    
    # Enrich with student and teacher names
    result = []
    for lesson_doc in lessons:
        student = await db.students.find_one({"id": lesson_doc["student_id"]})
        
        # Handle migration from old teacher_id to new teacher_ids array
        if "teacher_id" in lesson_doc and "teacher_ids" not in lesson_doc:
            # Migrate old single teacher_id to teacher_ids array
            lesson_doc["teacher_ids"] = [lesson_doc["teacher_id"]]
            lesson_doc.pop("teacher_id", None)
        elif "teacher_ids" not in lesson_doc:
            # Fallback if neither field exists
            lesson_doc["teacher_ids"] = []
        
        # Get all teachers for this lesson
        teacher_names = []
        for teacher_id in lesson_doc.get("teacher_ids", []):
            teacher = await db.teachers.find_one({"id": teacher_id})
            if teacher:
                teacher_names.append(teacher["name"])
        
        student_name = student["name"] if student else "Unknown"
        
        result.append(PrivateLessonResponse(
            **lesson_doc,
            student_name=student_name,
            teacher_names=teacher_names
        ))
    
    return result

@api_router.get("/lessons/{lesson_id}", response_model=PrivateLessonResponse)
async def get_private_lesson(lesson_id: str):
    lesson = await db.lessons.find_one({"id": lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Handle migration from old teacher_id to new teacher_ids array
    if "teacher_id" in lesson and "teacher_ids" not in lesson:
        # Migrate old single teacher_id to teacher_ids array
        lesson["teacher_ids"] = [lesson["teacher_id"]]
        lesson.pop("teacher_id", None)
    elif "teacher_ids" not in lesson:
        # Fallback if neither field exists
        lesson["teacher_ids"] = []
    
    student = await db.students.find_one({"id": lesson["student_id"]})
    
    # Get all teachers for this lesson
    teacher_names = []
    for teacher_id in lesson.get("teacher_ids", []):
        teacher = await db.teachers.find_one({"id": teacher_id})
        if teacher:
            teacher_names.append(teacher["name"])
    
    return PrivateLessonResponse(
        **lesson,
        student_name=student["name"] if student else "Unknown",
        teacher_names=teacher_names
    )

@api_router.put("/lessons/{lesson_id}", response_model=PrivateLessonResponse)
async def update_private_lesson(lesson_id: str, lesson_data: PrivateLessonUpdate, current_user: User = Depends(get_current_user)):
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
    
    # Get all teachers for this lesson and collect their names
    teacher_names = []
    for teacher_id in updated_lesson.get("teacher_ids", []):
        teacher = await db.teachers.find_one({"id": teacher_id})
        if teacher:
            teacher_names.append(teacher["name"])
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "lesson_updated",
        {
            "lesson_id": lesson_id,
            "lesson": updated_lesson,
            "student_name": student["name"] if student else "Unknown",
            "teacher_names": teacher_names
        },
        current_user.id,
        current_user.name
    )
    
    return PrivateLessonResponse(
        **updated_lesson,
        student_name=student["name"] if student else "Unknown",
        teacher_names=teacher_names
    )

@api_router.delete("/lessons/{lesson_id}")
async def delete_private_lesson(lesson_id: str, current_user: User = Depends(get_current_user)):
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
async def get_recurring_lesson_series(current_user: User = Depends(get_current_user)):
    """Get all active recurring lesson series"""
    series_list = await db.recurring_series.find({"is_active": True}).to_list(1000)
    
    # Enrich with student and teacher names and convert to proper format
    enriched_series = []
    for series_doc in series_list:
        student = await db.students.find_one({"id": series_doc["student_id"]})
        teacher = await db.teachers.find_one({"id": series_doc["teacher_id"]})
        
        # Convert to RecurringLessonSeries model to handle serialization
        series = RecurringLessonSeries(**series_doc)
        series_dict = series.dict()
        series_dict["student_name"] = student["name"] if student else "Unknown"
        series_dict["teacher_name"] = teacher["name"] if teacher else "Unknown"
        enriched_series.append(series_dict)
    
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
async def mark_lesson_attended(lesson_id: str, current_user: User = Depends(get_current_user)):
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
    
    # Get all teachers for this lesson
    teacher_names = []
    for teacher_id in lesson.get("teacher_ids", []):
        teacher = await db.teachers.find_one({"id": teacher_id})
        if teacher:
            teacher_names.append(teacher["name"])
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "lesson_attended",
        {
            "lesson_id": lesson_id,
            "student_name": student["name"] if student else "Unknown",
            "teacher_names": teacher_names,
            "start_datetime": lesson["start_datetime"]
        },
        current_user.id,
        current_user.name
    )
    
    return {"message": "Attendance marked successfully"}

# Daily Calendar Route
@api_router.get("/calendar/daily/{date}")
async def get_daily_data(date: str, current_user: User = Depends(get_current_user)):
    """Get daily calendar data with optimized queries"""
    try:
        # Parse date
        print(f"Parsing date: '{date}' (type: {type(date)})")
        target_date = datetime.strptime(date, "%Y-%m-%d")
        print(f"Parsed successfully: {target_date}")
        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Parallel database queries for better performance
        lessons_query = db.lessons.find({
            "start_datetime": {"$gte": start_date, "$lt": end_date}
        })
        
        teachers_query = db.teachers.find({})
        students_query = db.students.find({})
        
        # Execute queries concurrently
        lessons_task = lessons_query.to_list(200)
        teachers_task = teachers_query.to_list(100)
        students_task = students_query.to_list(500)
        
        lessons, teachers, students = await asyncio.gather(
            lessons_task, teachers_task, students_task
        )
        
        # Create lookup dictionaries for O(1) access
        students_dict = {s["id"]: s for s in students}
        teachers_dict = {t["id"]: t for t in teachers}
        
        # Enrich lessons with student and teacher names efficiently
        enriched_lessons = []
        for lesson_doc in lessons:
            student = students_dict.get(lesson_doc["student_id"])
            
            # Handle migration from old teacher_id to new teacher_ids array
            if "teacher_id" in lesson_doc and "teacher_ids" not in lesson_doc:
                # Migrate old single teacher_id to teacher_ids array
                lesson_doc["teacher_ids"] = [lesson_doc["teacher_id"]]
                lesson_doc.pop("teacher_id", None)
            elif "teacher_ids" not in lesson_doc:
                # Fallback if neither field exists
                lesson_doc["teacher_ids"] = []
            
            # Get all teachers for this lesson efficiently
            teacher_names = []
            teacher_ids = lesson_doc.get("teacher_ids", [])
            
            for teacher_id in teacher_ids:
                if teacher_id:
                    teacher = teachers_dict.get(teacher_id)
                    if teacher:
                        teacher_names.append(teacher["name"])
            
            enriched_lessons.append(PrivateLessonResponse(
                **lesson_doc,
                student_name=student["name"] if student else "Unknown",
                teacher_names=teacher_names
            ))
        
        # Only return active teachers with their colors
        active_teachers = []
        for teacher in teachers:
            teacher_data = TeacherResponse(**teacher)
            active_teachers.append(teacher_data)
        
        return {
            "date": date,
            "lessons": enriched_lessons,
            "teachers": active_teachers
        }
        
    except ValueError as ve:
        print(f"ValueError in date parsing: {ve}")
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        print(f"Error fetching daily data: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to fetch daily calendar data")

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

# Initialize default dance programs on startup
@app.on_event("startup")
async def create_default_programs():
    # Check if programs already exist
    existing_programs = await db.programs.count_documents({})
    if existing_programs == 0:
        default_programs = [
            DanceProgram(
                name="Beginner Program",
                level="Beginner",
                description="Introduction to ballroom dance for complete beginners"
            ),
            DanceProgram(
                name="Social Foundation",
                level="Social",
                description="Basic social dancing skills and etiquette"
            ),
            DanceProgram(
                name="Newcomers Bronze",
                level="Bronze",
                description="Entry level bronze syllabus for newcomer dancers"
            ),
            DanceProgram(
                name="Beginner Bronze",
                level="Bronze",
                description="Beginner level bronze techniques and figures"
            ),
            DanceProgram(
                name="Intermediate Bronze",
                level="Bronze",
                description="Intermediate bronze syllabus with more complex patterns"
            ),
            DanceProgram(
                name="Full Bronze",
                level="Bronze",
                description="Complete bronze syllabus mastery"
            ),
            DanceProgram(
                name="Beginner Silver",
                level="Silver",
                description="Introduction to silver level techniques"
            ),
            DanceProgram(
                name="Intermediate Silver",
                level="Silver",
                description="Intermediate silver level dancing"
            ),
            DanceProgram(
                name="Full Silver",
                level="Silver",
                description="Complete silver syllabus program"
            ),
            DanceProgram(
                name="Beginner Gold",
                level="Gold",
                description="Entry to gold level competitive dancing"
            ),
            DanceProgram(
                name="Intermediate Gold",
                level="Gold",
                description="Advanced gold level techniques"
            ),
            DanceProgram(
                name="Full Gold",
                level="Gold",
                description="Complete gold syllabus mastery"
            )
        ]
        
        for program in default_programs:
            await db.programs.insert_one(program.dict())
        print(f"✅ Created {len(default_programs)} default dance programs")
    
    # Check if settings already exist
    existing_settings = await db.settings.count_documents({})
    if existing_settings == 0:
        await create_default_settings()

# Initialize default settings
async def create_default_settings():
    """Create default application settings"""
    default_settings = [
        # Business Settings
        Settings(
            category="business",
            key="studio_name",
            value="Dance Studio",
            data_type="string",
            description="Name of the dance studio"
        ),
        Settings(
            category="business",
            key="contact_email",
            value="info@dancestudio.com",
            data_type="string",
            description="Main contact email for the studio"
        ),
        Settings(
            category="business",
            key="contact_phone",
            value="(555) 123-4567",
            data_type="string",
            description="Main contact phone number"
        ),
        Settings(
            category="business",
            key="address",
            value="123 Dance Street, City, State 12345",
            data_type="string",
            description="Studio address"
        ),
        Settings(
            category="business",
            key="operating_hours",
            value=["Monday-Friday: 9AM-9PM", "Saturday: 9AM-6PM", "Sunday: 12PM-6PM"],
            data_type="array",
            description="Studio operating hours"
        ),
        
        # System Settings
        Settings(
            category="system",
            key="timezone",
            value="America/New_York",
            data_type="string",
            description="Default timezone for the studio"
        ),
        Settings(
            category="system",
            key="currency",
            value="USD",
            data_type="string",
            description="Default currency for payments"
        ),
        Settings(
            category="system",
            key="date_format",
            value="MM/DD/YYYY",
            data_type="string",
            description="Default date format"
        ),
        Settings(
            category="system",
            key="time_format",
            value="12h",
            data_type="string",
            description="Time format (12h or 24h)"
        ),
        
        # Theme Settings
        Settings(
            category="theme",
            key="selected_theme",
            value="dark",
            data_type="string",
            description="Selected UI theme (dark, light, ocean, sunset, forest, royal)"
        ),
        Settings(
            category="theme",
            key="font_size",
            value="medium",
            data_type="string",
            description="Font size preference (small, medium, large)"
        ),
        Settings(
            category="theme",
            key="animations_enabled",
            value=True,
            data_type="boolean",
            description="Enable UI animations and transitions"
        ),
        Settings(
            category="theme",
            key="glassmorphism_enabled",
            value=True,
            data_type="boolean",
            description="Enable glassmorphism effects"
        ),
        Settings(
            category="theme",
            key="custom_primary_color",
            value="#a855f7",
            data_type="string",
            description="Custom primary color (hex code)"
        ),
        Settings(
            category="theme",
            key="custom_secondary_color",
            value="#ec4899",
            data_type="string",
            description="Custom secondary color (hex code)"
        ),
        
        # Booking Settings  
        Settings(
            category="booking",
            key="private_lesson_color",
            value="#3b82f6",
            data_type="string",
            description="Color for private lesson bookings (hex code)"
        ),
        Settings(
            category="booking",
            key="meeting_color",
            value="#22c55e",
            data_type="string",
            description="Color for meeting bookings (hex code)"
        ),
        Settings(
            category="booking",
            key="training_color",
            value="#f59e0b",
            data_type="string",
            description="Color for training bookings (hex code)"
        ),
        Settings(
            category="booking",
            key="party_color",
            value="#a855f7",
            data_type="string",
            description="Color for party bookings (hex code)"
        ),
        Settings(
            category="booking",
            key="confirmed_status_color",
            value="#22c55e",
            data_type="string",
            description="Color for confirmed bookings (hex code)"
        ),
        Settings(
            category="booking",
            key="pending_status_color",
            value="#f59e0b",
            data_type="string",
            description="Color for pending bookings (hex code)"
        ),
        Settings(
            category="booking",
            key="cancelled_status_color",
            value="#ef4444",
            data_type="string",
            description="Color for cancelled bookings (hex code)"
        ),
        Settings(
            category="booking",
            key="teacher_color_coding_enabled",
            value=True,
            data_type="boolean",
            description="Enable individual teacher color coding"
        ),
        
        # Calendar Settings
        Settings(
            category="calendar",
            key="default_view",
            value="daily",
            data_type="string",
            description="Default calendar view (daily, weekly)"
        ),
        Settings(
            category="calendar",
            key="start_hour",
            value=9,
            data_type="integer",
            description="Calendar start hour (24-hour format)"
        ),
        Settings(
            category="calendar",
            key="end_hour",
            value=21,
            data_type="integer",
            description="Calendar end hour (24-hour format)"
        ),
        Settings(
            category="calendar",
            key="time_slot_minutes",
            value=60,
            data_type="integer",
            description="Time slot duration in minutes"
        ),
        Settings(
            category="calendar",
            key="weekend_enabled",
            value=True,
            data_type="boolean",
            description="Show weekends in calendar"
        ),
        Settings(
            category="calendar",
            key="instructor_stats_enabled",
            value=True,
            data_type="boolean",
            description="Show instructor statistics on calendar"
        ),
        
        # Display Settings
        Settings(
            category="display",
            key="compact_mode",
            value=False,
            data_type="boolean",
            description="Enable compact display mode"
        ),
        Settings(
            category="display",
            key="show_lesson_notes",
            value=True,
            data_type="boolean",
            description="Show lesson notes in calendar view"
        ),
        Settings(
            category="display",
            key="currency_symbol",
            value="$",
            data_type="string",
            description="Currency symbol to display"
        ),
        Settings(
            category="display",
            key="language",
            value="en",
            data_type="string",
            description="System language (en, es, fr, de)"
        ),
        
        # Business Rules Settings
        Settings(
            category="business_rules",
            key="cancellation_policy_hours",
            value=24,
            data_type="integer",
            description="Hours before lesson that cancellation is allowed"
        ),
        Settings(
            category="business_rules",
            key="max_advance_booking_days",
            value=90,
            data_type="integer",
            description="Maximum days in advance lessons can be booked"
        ),
        Settings(
            category="business_rules",
            key="auto_confirm_bookings",
            value=True,
            data_type="boolean",
            description="Automatically confirm new bookings"
        ),
        Settings(
            category="business_rules",
            key="require_payment_before_booking",
            value=False,
            data_type="boolean",
            description="Require payment before allowing bookings"
        ),
        Settings(
            category="business_rules",
            key="late_cancellation_fee",
            value=50.0,
            data_type="float",
            description="Fee for late cancellations"
        ),
        
        # Program Settings (Enhanced)
        Settings(
            category="program",
            key="default_lesson_duration",
            value=60,
            data_type="integer",
            description="Default lesson duration in minutes"
        ),
        Settings(
            category="program",
            key="max_students_per_class",
            value=20,
            data_type="integer",
            description="Maximum students per group class"
        ),
        Settings(
            category="program",
            key="available_dance_styles",
            value=["Ballet", "Jazz", "Contemporary", "Hip Hop", "Ballroom", "Latin", "Tap", "Modern", "Salsa", "Bachata"],
            data_type="array",
            description="Available dance styles for programs"
        ),
        
        # Notification Settings (Enhanced)
        Settings(
            category="notification",
            key="reminder_hours_before",
            value=24,
            data_type="integer",
            description="Default hours before lesson to send reminders"
        ),
        Settings(
            category="notification",
            key="email_notifications_enabled",
            value=True,
            data_type="boolean",
            description="Enable email notifications"
        ),
        Settings(
            category="notification",
            key="sms_notifications_enabled",
            value=False,
            data_type="boolean",
            description="Enable SMS notifications"
        ),
        Settings(
            category="notification",
            key="booking_confirmation_email",
            value=True,
            data_type="boolean",
            description="Send email confirmation for new bookings"
        ),
        Settings(
            category="notification",
            key="payment_reminder_enabled",
            value=True,
            data_type="boolean",
            description="Send payment reminders"
        )
    ]
    
    for setting in default_settings:
        await db.settings.insert_one(setting.dict())
    print(f"✅ Created {len(default_settings)} default settings")

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
    
    # Get teacher details - handle multiple teachers
    # Handle migration from old teacher_id to new teacher_ids array
    if "teacher_id" in lesson and "teacher_ids" not in lesson:
        # Migrate old single teacher_id to teacher_ids array
        lesson["teacher_ids"] = [lesson["teacher_id"]]
        lesson.pop("teacher_id", None)
    elif "teacher_ids" not in lesson:
        # Fallback if neither field exists
        lesson["teacher_ids"] = []
    
    teacher_names = []
    for teacher_id in lesson.get("teacher_ids", []):
        teacher = await db.teachers.find_one({"id": teacher_id})
        if teacher:
            teacher_names.append(teacher["name"])
    
    teachers_text = ", ".join(teacher_names) if teacher_names else "Unknown"
    
    # Get notification preferences
    pref = await db.notification_preferences.find_one({"student_id": lesson["student_id"]})
    
    lesson_datetime = lesson["start_datetime"]
    formatted_datetime = lesson_datetime.strftime("%B %d, %Y at %I:%M %p")
    
    default_message = f"Hi {student['name']}, this is a reminder that you have a dance lesson scheduled for {formatted_datetime} with {teachers_text}. See you there!"
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
    
    else:
        raise HTTPException(status_code=400, detail="Invalid notification type")

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
        
        # Get all teachers for this lesson
        teacher_names = []
        for teacher_id in lesson_doc.get("teacher_ids", []):
            teacher = await db.teachers.find_one({"id": teacher_id})
            if teacher:
                teacher_names.append(teacher["name"])
        
        # Create a clean lesson dict without MongoDB ObjectId
        clean_lesson = {
            "id": lesson_doc["id"],
            "student_id": lesson_doc["student_id"],
            "teacher_ids": lesson_doc.get("teacher_ids", []),
            "start_datetime": lesson_doc["start_datetime"],
            "end_datetime": lesson_doc["end_datetime"],
            "booking_type": lesson_doc.get("booking_type", "private_lesson"),
            "notes": lesson_doc.get("notes"),
            "is_attended": lesson_doc.get("is_attended", False),
            "enrollment_id": lesson_doc.get("enrollment_id"),
            "student_name": student["name"] if student else "Unknown",
            "student_email": student["email"] if student else None,
            "student_phone": student.get("phone") if student else None,
            "teacher_names": teacher_names
        }
        
        enriched_lessons.append(clean_lesson)
    
    return enriched_lessons

# Settings Routes
@api_router.get("/settings", response_model=List[SettingsResponse])
async def get_all_settings():
    """Get all application settings"""
    settings = await db.settings.find().to_list(1000)
    return [SettingsResponse(**setting) for setting in settings]

@api_router.get("/settings/{category}", response_model=List[SettingsResponse])
async def get_settings_by_category(category: str):
    """Get settings by category (business, system, program, notification)"""
    settings = await db.settings.find({"category": category}).to_list(1000)
    return [SettingsResponse(**setting) for setting in settings]

@api_router.get("/settings/{category}/{key}", response_model=SettingsResponse)
async def get_setting_by_key(category: str, key: str):
    """Get a specific setting by category and key"""
    setting = await db.settings.find_one({"category": category, "key": key})
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return SettingsResponse(**setting)

@api_router.put("/settings/{category}/{key}", response_model=SettingsResponse)
async def update_setting(category: str, key: str, setting_update: SettingsUpdate, current_user: User = Depends(get_current_user)):
    """Update a specific setting"""
    # Check if setting exists
    existing_setting = await db.settings.find_one({"category": category, "key": key})
    if not existing_setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    # Update the setting
    update_data = {
        "value": setting_update.value,
        "updated_at": datetime.utcnow(),
        "updated_by": current_user.id
    }
    
    result = await db.settings.update_one(
        {"category": category, "key": key},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    # Get updated setting
    updated_setting = await db.settings.find_one({"category": category, "key": key})
    return SettingsResponse(**updated_setting)

@api_router.post("/settings/reset-defaults")
async def reset_settings_to_defaults(current_user: User = Depends(get_current_user)):
    """Reset all settings to default values"""
    # Only allow owners to reset settings
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can reset settings")
    
    # Delete all existing settings
    await db.settings.delete_many({})
    
    # Create default settings
    await create_default_settings()
    
    return {"message": "Settings reset to defaults successfully"}

# Teacher Color Management Routes
@api_router.get("/teachers/{teacher_id}/color")
async def get_teacher_color(teacher_id: str):
    """Get teacher's assigned color"""
    teacher = await db.teachers.find_one({"id": teacher_id})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    color = teacher.get("assigned_color", "#3b82f6")  # Default blue
    return {"teacher_id": teacher_id, "color": color}

@api_router.put("/teachers/{teacher_id}/color")
async def update_teacher_color(teacher_id: str, color_data: Dict[str, str], current_user: User = Depends(get_current_user)):
    """Update teacher's assigned color"""
    if current_user.role not in ["owner", "manager"]:
        raise HTTPException(status_code=403, detail="Only owners and managers can change teacher colors")
    
    teacher = await db.teachers.find_one({"id": teacher_id})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    color = color_data.get("color", "#3b82f6")
    
    # Validate hex color format
    if not color.startswith("#") or len(color) != 7:
        raise HTTPException(status_code=400, detail="Invalid color format. Use hex format like #3b82f6")
    
    # Additional validation: check if all characters after # are valid hex
    hex_chars = color[1:]
    if not all(c in '0123456789abcdefABCDEF' for c in hex_chars):
        raise HTTPException(status_code=400, detail="Invalid hex color. Use valid hex characters (0-9, A-F)")
    
    await db.teachers.update_one(
        {"id": teacher_id},
        {"$set": {"assigned_color": color, "updated_at": datetime.utcnow()}}
    )
    
    return {"teacher_id": teacher_id, "color": color, "message": "Teacher color updated successfully"}

@api_router.post("/teachers/colors/auto-assign")
async def auto_assign_teacher_colors(current_user: User = Depends(get_current_user)):
    """Automatically assign unique colors to all teachers"""
    if current_user.role not in ["owner", "manager"]:
        raise HTTPException(status_code=403, detail="Only owners and managers can assign teacher colors")
    
    # Predefined color palette
    color_palette = [
        "#3b82f6",  # Blue
        "#ef4444",  # Red
        "#22c55e",  # Green
        "#f59e0b",  # Amber
        "#a855f7",  # Purple
        "#ec4899",  # Pink
        "#06b6d4",  # Cyan
        "#84cc16",  # Lime
        "#f97316",  # Orange
        "#8b5cf6",  # Violet
        "#14b8a6",  # Teal
        "#f43f5e",  # Rose
    ]
    
    teachers = await db.teachers.find().to_list(1000)
    assignments = []
    
    for i, teacher in enumerate(teachers):
        color = color_palette[i % len(color_palette)]
        
        await db.teachers.update_one(
            {"id": teacher["id"]},
            {"$set": {"assigned_color": color, "updated_at": datetime.utcnow()}}
        )
        
        assignments.append({
            "teacher_id": teacher["id"],
            "teacher_name": teacher["name"],
            "color": color
        })
    
    return {
        "message": f"Assigned colors to {len(assignments)} teachers",
        "assignments": assignments
    }

# User Management Routes
@api_router.get("/users", response_model=List[UserResponse])
async def get_all_users(current_user: User = Depends(get_current_user)):
    """Get all users (only owners and managers can access this)"""
    if current_user.role not in ["owner", "manager"]:
        raise HTTPException(status_code=403, detail="Only owners and managers can view users")
    
    users = await db.users.find().to_list(1000)
    
    # Convert users to UserResponse, handling missing created_at field
    user_responses = []
    for user in users:
        # Ensure created_at field exists, use current time as default if missing
        if 'created_at' not in user:
            user['created_at'] = datetime.utcnow()
        
        # Convert MongoDB ObjectId to string for id field
        if '_id' in user:
            user['id'] = str(user['_id'])
            del user['_id']
        
        user_responses.append(UserResponse(**user))
    
    return user_responses

@api_router.post("/users", response_model=UserResponse)
async def create_user(user_data: UserCreate, current_user: User = Depends(get_current_user)):
    """Create a new user (only owners can create users)"""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can create new users")
    
    # Check if user with email already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Hash password
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    new_user = User(
        id=str(uuid.uuid4()),
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_password.decode('utf-8'),
        role=user_data.role,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    await db.users.insert_one(new_user.dict())
    return UserResponse(**new_user.dict())

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserUpdate, current_user: User = Depends(get_current_user)):
    """Update user details (only owners can update any user, users can update themselves)"""
    # Check if user exists
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Permission check
    if current_user.role != "owner" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only update your own profile")
    
    # If not owner, restrict what can be updated
    if current_user.role != "owner":
        if user_update.role is not None or user_update.is_active is not None:
            raise HTTPException(status_code=403, detail="Only owners can change roles or account status")
    
    # Check email uniqueness if email is being updated
    if user_update.email and user_update.email != target_user["email"]:
        existing_user = await db.users.find_one({"email": user_update.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Build update data
    update_data = {}
    if user_update.name is not None:
        update_data["name"] = user_update.name
    if user_update.email is not None:
        update_data["email"] = user_update.email
    if user_update.role is not None:
        update_data["role"] = user_update.role
    if user_update.is_active is not None:
        update_data["is_active"] = user_update.is_active
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    # Update user
    update_data["updated_at"] = datetime.utcnow()
    result = await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found or no changes made")
    
    # Get updated user
    updated_user = await db.users.find_one({"id": user_id})
    return UserResponse(**updated_user)

@api_router.put("/users/{user_id}/password")
async def change_password(user_id: str, password_update: PasswordUpdate, current_user: User = Depends(get_current_user)):
    """Change user password"""
    # Check if user exists
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Permission check
    if current_user.role != "owner" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only change your own password")
    
    # If changing own password, verify old password
    if current_user.id == user_id and password_update.old_password:
        if not bcrypt.checkpw(password_update.old_password.encode('utf-8'), target_user["hashed_password"].encode('utf-8')):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Hash new password
    new_hashed_password = bcrypt.hashpw(password_update.new_password.encode('utf-8'), bcrypt.gensalt())
    
    # Update password
    result = await db.users.update_one(
        {"id": user_id}, 
        {"$set": {"hashed_password": new_hashed_password.decode('utf-8'), "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Password changed successfully"}

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    """Delete a user (only owners can delete users)"""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can delete users")
    
    # Prevent deleting own account
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    
    # Check if user exists
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete user
    result = await db.users.delete_one({"id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

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
    print(f"🔌 WebSocket connection attempt from user: {user_id}")
    try:
        await manager.connect(websocket, user_id)
        print(f"✅ WebSocket connected for user: {user_id}")
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection",
            "data": {"status": "connected", "user_id": user_id},
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        while True:
            # Keep connection alive and listen for client messages
            try:
                data = await websocket.receive_text()
                print(f"📡 WebSocket message from {user_id}: {data}")
                
                # Handle client messages
                if data == "ping":
                    await websocket.send_text("pong")
                else:
                    # Echo back or handle other messages
                    await websocket.send_text(f"Echo: {data}")
                    
            except Exception as receive_error:
                print(f"❌ WebSocket receive error for user {user_id}: {receive_error}")
                break
                
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected for user: {user_id}")
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"❌ WebSocket error for user {user_id}: {e}")
        try:
            manager.disconnect(websocket, user_id)
        except:
            pass

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