from fastapi import FastAPI, APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from enum import Enum
import os
import jwt
import uuid
import asyncio
import json
from passlib.context import CryptContext
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import email service
try:
    from email_service import EmailService
except ImportError:
    EmailService = None

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client.get_database()

# Create FastAPI app
app = FastAPI(title="Dance Studio CRM", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API router
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "dance-studio-secret-key-change-this")
ALGORITHM = "HS256"

# WebSocket Manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.user_connections:
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    pass

    async def broadcast_message(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

    async def broadcast_update(self, update_type: str, data: dict, user_id: str, user_name: str):
        message = {
            "type": update_type,
            "data": data,
            "user_id": user_id,
            "user_name": user_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_message(message)

# Global connection manager
manager = ConnectionManager()

# Enums
class UserRole(str, Enum):
    OWNER = "owner"
    MANAGER = "manager" 
    TEACHER = "teacher"

class LessonStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class BookingType(str, Enum):
    PRIVATE_LESSON = "Private lesson"
    MEETING = "Meeting"
    TRAINING = "Training"
    PARTY = "Party"

class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    ONLINE = "online"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: UserRole
    hashed_password: str
    studio_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: UserRole = UserRole.TEACHER
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
    specialties: Optional[List[str]] = []
    bio: Optional[str] = None
    color: Optional[str] = "#3b82f6"
    is_active: bool = True
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TeacherCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    specialties: Optional[List[str]] = []
    bio: Optional[str] = None

class Student(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone: Optional[str] = None
    parent_name: Optional[str] = None
    parent_email: Optional[str] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class StudentCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    parent_name: Optional[str] = None
    parent_email: Optional[str] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None

class Enrollment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    program_name: str
    total_lessons: int
    remaining_lessons: int = 0
    lessons_taken: int = 0
    price_per_lesson: float = 0.0
    amount_paid: float = 0.0
    total_paid: float = 0.0  # For backward compatibility
    grand_total: float = 0.0
    balance_remaining: float = 0.0
    lessons_available: int = 0
    purchase_date: datetime = Field(default_factory=datetime.utcnow)
    expiry_date: Optional[date] = None
    is_active: bool = True

    def calculate_totals(self):
        """Calculate derived fields based on core data"""
        self.grand_total = self.total_lessons * self.price_per_lesson
        self.balance_remaining = self.grand_total - self.amount_paid
        
        # Calculate lessons available based on amount paid
        if self.price_per_lesson > 0:
            paid_lessons = int(self.amount_paid / self.price_per_lesson)
            self.lessons_available = max(0, paid_lessons - self.lessons_taken)
        else:
            self.lessons_available = max(0, self.total_lessons - self.lessons_taken)
        
        # Update remaining lessons
        self.remaining_lessons = max(0, self.total_lessons - self.lessons_taken)

class EnrollmentCreate(BaseModel):
    student_id: str
    program_name: str
    total_lessons: int
    price_per_lesson: float = 0.0
    initial_payment: float = 0.0
    total_paid: float = 0.0  # For backward compatibility
    expiry_date: Optional[date] = None

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    enrollment_id: Optional[str] = None
    amount: float
    payment_method: PaymentMethod = PaymentMethod.CASH
    notes: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PaymentCreate(BaseModel):
    student_id: str
    enrollment_id: Optional[str] = None
    amount: float
    payment_method: PaymentMethod = PaymentMethod.CASH
    notes: Optional[str] = None

class PrivateLesson(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_ids: List[str] = []
    teacher_ids: List[str] = []
    teacher_names: Optional[List[str]] = []
    date: str  # Changed from date to str to avoid BSON serialization issues
    start_time: str
    end_time: str
    duration_minutes: int = 60
    booking_type: BookingType = BookingType.PRIVATE_LESSON
    status: LessonStatus = LessonStatus.ACTIVE
    notes: Optional[str] = None
    attended: bool = False
    created_by: str
    cancelled_by: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LessonCreate(BaseModel):
    student_ids: List[str] = []
    teacher_ids: List[str] = []
    date: str  # Changed from date to str to avoid BSON serialization issues
    start_time: str
    end_time: str
    duration_minutes: int = 60
    booking_type: BookingType = BookingType.PRIVATE_LESSON
    notes: Optional[str] = None

class Setting(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str
    key: str
    value: Any
    data_type: str  # "string", "integer", "boolean", "float", "array"
    description: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SettingCreate(BaseModel):
    category: str
    key: str
    value: Any
    data_type: str
    description: Optional[str] = None

# Student Ledger Response Model
class StudentLedgerResponse(BaseModel):
    student: Student
    enrollments: List[Enrollment] = []
    payments: List[Payment] = []
    upcoming_lessons: List[PrivateLesson] = []
    lesson_history: List[PrivateLesson] = []
    total_paid: float = 0.0
    total_enrolled_lessons: int = 0
    remaining_lessons: int = 0
    lessons_taken: int = 0

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

# Hex color validation helper
def is_valid_hex_color(color: str) -> bool:
    if not color.startswith('#') or len(color) != 7:
        return False
    try:
        int(color[1:], 16)
        return True
    except ValueError:
        return False

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: str = None):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages if needed
            pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Dashboard stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    total_teachers = await db.teachers.count_documents({"is_active": True})
    total_students = await db.students.count_documents({})
    active_enrollments = await db.enrollments.count_documents({"is_active": True})
    
    # Calculate estimated revenue from active enrollments
    enrollments = await db.enrollments.find({"is_active": True}).to_list(1000)
    estimated_revenue = sum(e.get("grand_total", 0) for e in enrollments)
    
    return {
        "total_teachers": total_teachers,
        "total_students": total_students, 
        "active_enrollments": active_enrollments,
        "estimated_monthly_revenue": estimated_revenue
    }

# Authentication routes
@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
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

# Teacher routes
@api_router.get("/teachers")
async def get_teachers():
    teachers = await db.teachers.find({"is_active": True}, {"_id": 0}).to_list(1000)
    return teachers

@api_router.post("/teachers", response_model=Teacher)
async def create_teacher(teacher_data: TeacherCreate, current_user: User = Depends(get_current_user)):
    teacher = Teacher(**teacher_data.dict())
    await db.teachers.insert_one(teacher.dict())
    return teacher

@api_router.get("/teachers/{teacher_id}/color")
async def get_teacher_color(teacher_id: str):
    teacher = await db.teachers.find_one({"id": teacher_id})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return {"teacher_id": teacher_id, "color": teacher.get("color", "#3b82f6")}

@api_router.put("/teachers/{teacher_id}/color")
async def update_teacher_color(teacher_id: str, color_data: dict, current_user: User = Depends(get_current_user)):
    teacher = await db.teachers.find_one({"id": teacher_id})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    color = color_data.get("color", "")
    if not is_valid_hex_color(color):
        raise HTTPException(status_code=400, detail="Invalid hex color format")
    
    await db.teachers.update_one({"id": teacher_id}, {"$set": {"color": color}})
    return {"message": "Color updated successfully", "color": color}

# Student routes
@api_router.get("/students")
async def get_students():
    students = await db.students.find({}, {"_id": 0}).to_list(1000)
    return students

@api_router.post("/students", response_model=Student)
async def create_student(student_data: StudentCreate, current_user: User = Depends(get_current_user)):
    student = Student(**student_data.dict())
    await db.students.insert_one(student.dict())
    return student

# Enrollment routes - with real-time synchronization
@api_router.post("/enrollments", response_model=Enrollment)
async def create_enrollment(enrollment_data: EnrollmentCreate):
    # Verify student exists
    student = await db.students.find_one({"id": enrollment_data.student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Create enrollment with calculated totals
    enrollment = Enrollment(
        student_id=enrollment_data.student_id,
        program_name=enrollment_data.program_name,
        total_lessons=enrollment_data.total_lessons,
        remaining_lessons=enrollment_data.total_lessons,
        price_per_lesson=enrollment_data.price_per_lesson,
        amount_paid=enrollment_data.initial_payment,
        total_paid=enrollment_data.total_paid,  # For backward compatibility
        expiry_date=enrollment_data.expiry_date
    )
    
    # Calculate totals
    enrollment.calculate_totals()
    
    await db.enrollments.insert_one(enrollment.dict())
    
    # Broadcast real-time update to all connected clients
    await manager.broadcast_update(
        "enrollment_created",
        {
            "enrollment_id": enrollment.id,
            "student_id": enrollment.student_id,
            "student_name": student["name"],
            "program_name": enrollment.program_name,
            "total_lessons": enrollment.total_lessons,
            "lessons_available": enrollment.lessons_available,
            "amount_paid": enrollment.amount_paid,
            "grand_total": enrollment.grand_total
        },
        "system",
        "System"
    )
    
    return enrollment

@api_router.put("/enrollments/{enrollment_id}", response_model=Enrollment)
async def update_enrollment(enrollment_id: str, enrollment_data: EnrollmentCreate):
    # Verify enrollment exists
    existing_enrollment = await db.enrollments.find_one({"id": enrollment_id})
    if not existing_enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    # Verify student exists
    student = await db.students.find_one({"id": enrollment_data.student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Update enrollment with calculated totals
    enrollment = Enrollment(
        id=enrollment_id,  # Keep the existing ID
        student_id=enrollment_data.student_id,
        program_name=enrollment_data.program_name,
        total_lessons=enrollment_data.total_lessons,
        remaining_lessons=existing_enrollment.get("remaining_lessons", enrollment_data.total_lessons),
        lessons_taken=existing_enrollment.get("lessons_taken", 0),
        price_per_lesson=enrollment_data.price_per_lesson,
        amount_paid=enrollment_data.initial_payment,
        total_paid=enrollment_data.total_paid,  # For backward compatibility
        purchase_date=existing_enrollment.get("purchase_date"),  # Keep original purchase date
        expiry_date=enrollment_data.expiry_date,
        is_active=existing_enrollment.get("is_active", True)
    )
    
    # Calculate totals
    enrollment.calculate_totals()
    
    # Update in database
    await db.enrollments.update_one(
        {"id": enrollment_id},
        {"$set": enrollment.dict()}
    )
    
    # Broadcast real-time update
    await manager.broadcast_update(
        "enrollment_updated",
        {
            "enrollment_id": enrollment.id,
            "student_id": enrollment.student_id,
            "student_name": student["name"],
            "program_name": enrollment.program_name,
            "total_lessons": enrollment.total_lessons,
            "lessons_available": enrollment.lessons_available,
            "amount_paid": enrollment.amount_paid,
            "grand_total": enrollment.grand_total
        },
        "system",
        "System"
    )
    
    return enrollment

@api_router.get("/enrollments")
async def get_enrollments():
    enrollments = await db.enrollments.find({}, {"_id": 0}).to_list(1000)
    return enrollments

# Payment routes - enhanced with enrollment credit updates and broadcasts
@api_router.post("/payments", response_model=Payment)
async def create_payment(payment_data: PaymentCreate, current_user: User = Depends(get_current_user)):
    payment_dict = payment_data.dict()
    payment = Payment(
        **payment_dict,
        created_by=current_user.id
    )
    
    await db.payments.insert_one(payment.dict())
    
    # Get student info for broadcasting
    student = await db.students.find_one({"id": payment_data.student_id})
    student_name = student["name"] if student else "Unknown Student"
    
    # Update enrollment credits if payment is linked to enrollment
    enrollment_updated = None
    if payment_data.enrollment_id:
        # Get current enrollment
        enrollment_doc = await db.enrollments.find_one({"id": payment_data.enrollment_id})
        if enrollment_doc:
            # Calculate new amount paid for this enrollment
            enrollment_payments = await db.payments.find({"enrollment_id": payment_data.enrollment_id}).to_list(1000)
            total_paid_to_enrollment = sum(p.get("amount", 0) for p in enrollment_payments)
            
            # Update enrollment with new totals
            enrollment = Enrollment(**enrollment_doc)
            enrollment.amount_paid = total_paid_to_enrollment
            enrollment.calculate_totals()
            
            # Save updated enrollment
            await db.enrollments.update_one(
                {"id": payment_data.enrollment_id},
                {"$set": {
                    "amount_paid": enrollment.amount_paid,
                    "grand_total": enrollment.grand_total,
                    "balance_remaining": enrollment.balance_remaining,
                    "lessons_available": enrollment.lessons_available
                }}
            )
            enrollment_updated = enrollment
    
    # If no specific enrollment, update all student enrollments proportionally
    else:
        enrollments = await db.enrollments.find({
            "student_id": payment_data.student_id,
            "is_active": True
        }).to_list(100)
        
        # Find enrollment with highest balance to apply payment to
        if enrollments:
            max_balance_enrollment = None
            max_balance = 0
            
            for enroll_doc in enrollments:
                enroll = Enrollment(**enroll_doc)
                enroll.calculate_totals()
                if enroll.balance_remaining > max_balance:
                    max_balance = enroll.balance_remaining
                    max_balance_enrollment = enroll
            
            if max_balance_enrollment:
                # Apply payment to this enrollment
                new_amount_paid = max_balance_enrollment.amount_paid + payment.amount
                max_balance_enrollment.amount_paid = new_amount_paid
                max_balance_enrollment.calculate_totals()
                
                await db.enrollments.update_one(
                    {"id": max_balance_enrollment.id},
                    {"$set": {
                        "amount_paid": max_balance_enrollment.amount_paid,
                        "lessons_available": max_balance_enrollment.lessons_available,
                        "balance_remaining": max_balance_enrollment.balance_remaining
                    }}
                )
                enrollment_updated = max_balance_enrollment
    
    # Broadcast comprehensive payment update
    await manager.broadcast_update(
        "payment_created",
        {
            "payment_id": payment.id,
            "student_id": payment.student_id,
            "student_name": student_name,
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "enrollment_id": payment.enrollment_id,
            "enrollment_updated": {
                "enrollment_id": enrollment_updated.id,
                "lessons_available": enrollment_updated.lessons_available,
                "balance_remaining": enrollment_updated.balance_remaining,
                "program_name": enrollment_updated.program_name
            } if enrollment_updated else None
        },
        current_user.id,
        current_user.name
    )
    
    return payment

@api_router.get("/payments")
async def get_payments():
    payments = await db.payments.find({}, {"_id": 0}).to_list(1000)
    return payments

# Lesson routes
@api_router.get("/lessons")
async def get_lessons(date_filter: str = None):
    query = {}
    if date_filter:
        query["date"] = date_filter
    lessons = await db.lessons.find(query, {"_id": 0}).to_list(1000)
    return lessons

@api_router.post("/lessons", response_model=PrivateLesson)
async def create_lesson(lesson_data: LessonCreate, current_user: User = Depends(get_current_user)):
    # Get teacher names for the lesson
    teacher_names = []
    if lesson_data.teacher_ids:
        for teacher_id in lesson_data.teacher_ids:
            teacher = await db.teachers.find_one({"id": teacher_id})
            if teacher:
                teacher_names.append(teacher["name"])
    
    lesson = PrivateLesson(
        **lesson_data.dict(),
        teacher_names=teacher_names,
        created_by=current_user.id
    )
    
    await db.lessons.insert_one(lesson.dict())
    return lesson

@api_router.post("/lessons/{lesson_id}/attend")
async def mark_lesson_attendance(lesson_id: str, current_user: User = Depends(get_current_user)):
    # Get the lesson
    lesson = await db.lessons.find_one({"id": lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Mark lesson as attended
    await db.lessons.update_one(
        {"id": lesson_id},
        {"$set": {"attended": True}}
    )
    
    # Update enrollment credits for each student in the lesson
    for student_id in lesson.get("student_ids", []):
        # Get student's active enrollments
        enrollments = await db.enrollments.find({
            "student_id": student_id,
            "is_active": True,
            "lessons_available": {"$gt": 0}
        }).sort("purchase_date", 1).to_list(100)  # Oldest first
        
        if enrollments:
            # Deduct from the first available enrollment
            enrollment_doc = enrollments[0]
            enrollment = Enrollment(**enrollment_doc)
            
            # Increment lessons taken and recalculate
            enrollment.lessons_taken += 1
            enrollment.calculate_totals()
            
            await db.enrollments.update_one(
                {"id": enrollment.id},
                {"$set": {
                    "lessons_taken": enrollment.lessons_taken,
                    "lessons_available": enrollment.lessons_available,
                    "remaining_lessons": enrollment.remaining_lessons
                }}
            )
            
            # Broadcast lesson attendance update
            await manager.broadcast_update(
                "lesson_attended",
                {
                    "lesson_id": lesson_id,
                    "student_id": student_id,
                    "enrollment_id": enrollment.id,
                    "lessons_taken": enrollment.lessons_taken,
                    "lessons_available": enrollment.lessons_available,
                    "date": lesson.get("date"),
                    "time": f"{lesson.get('start_time')} - {lesson.get('end_time')}"
                },
                current_user.id,
                current_user.name
            )
    
    return {"message": "Attendance marked successfully", "lesson_id": lesson_id}

# Student Ledger endpoint
@api_router.get("/students/{student_id}/ledger")
async def get_student_ledger(student_id: str):
    # Get student info
    student = await db.students.find_one({"id": student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get student's enrollments
    enrollments_docs = await db.enrollments.find({"student_id": student_id}).to_list(100)
    enrollments = []
    for doc in enrollments_docs:
        enrollment = Enrollment(**doc)
        enrollment.calculate_totals()  # Ensure calculations are up-to-date
        enrollments.append(enrollment)
    
    # Get student's payments
    payments_docs = await db.payments.find({"student_id": student_id}).to_list(100)
    payments = [Payment(**doc) for doc in payments_docs]
    
    # Get student's upcoming lessons
    today = datetime.utcnow().date()
    upcoming_lessons_docs = await db.lessons.find({
        "student_ids": student_id,
        "date": {"$gte": today.isoformat()},
        "status": LessonStatus.ACTIVE
    }).sort("date", 1).to_list(50)
    upcoming_lessons = [PrivateLesson(**doc) for doc in upcoming_lessons_docs]
    
    # Get student's lesson history
    lesson_history_docs = await db.lessons.find({
        "student_ids": student_id,
        "date": {"$lt": today.isoformat()}
    }).sort("date", -1).to_list(100)
    lesson_history = [PrivateLesson(**doc) for doc in lesson_history_docs]
    
    # Calculate totals
    total_paid = sum(p.amount for p in payments)
    total_enrolled_lessons = sum(e.total_lessons for e in enrollments)
    remaining_lessons = sum(e.remaining_lessons for e in enrollments)
    lessons_taken = sum(e.lessons_taken for e in enrollments)
    
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

# Get available lessons for a student
@api_router.get("/students/{student_id}/available_lessons")
async def get_student_available_lessons(student_id: str):
    enrollments_docs = await db.enrollments.find({
        "student_id": student_id,
        "is_active": True
    }).to_list(100)
    
    total_available = 0
    for doc in enrollments_docs:
        enrollment = Enrollment(**doc)
        enrollment.calculate_totals()
        total_available += enrollment.lessons_available
    
    return {"student_id": student_id, "available_lessons": total_available}

# Get lesson history for a student
@api_router.get("/students/{student_id}/lessons")
async def get_student_lessons(student_id: str):
    lessons = await db.lessons.find({
        "student_ids": student_id
    }, {"_id": 0}).sort("date", -1).to_list(100)
    return lessons

# Lesson cancellation endpoints
@api_router.post("/lessons/{lesson_id}/cancel")
async def cancel_lesson(lesson_id: str, cancel_data: dict, current_user: User = Depends(get_current_user)):
    lesson = await db.lessons.find_one({"id": lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    reason = cancel_data.get("reason", "No reason provided")
    
    await db.lessons.update_one(
        {"id": lesson_id},
        {"$set": {
            "status": LessonStatus.CANCELLED,
            "cancelled_by": current_user.id,
            "cancellation_reason": reason,
            "cancelled_at": datetime.utcnow()
        }}
    )
    
    return {"message": "Lesson cancelled successfully", "lesson_id": lesson_id}

@api_router.post("/lessons/{lesson_id}/reactivate")
async def reactivate_lesson(lesson_id: str, current_user: User = Depends(get_current_user)):
    lesson = await db.lessons.find_one({"id": lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    await db.lessons.update_one(
        {"id": lesson_id},
        {"$set": {
            "status": LessonStatus.ACTIVE,
            "cancelled_by": None,
            "cancellation_reason": None,
            "cancelled_at": None
        }}
    )
    
    return {"message": "Lesson reactivated successfully", "lesson_id": lesson_id}

# Cancelled lessons report
@api_router.get("/reports/cancelled-lessons")
async def get_cancelled_lessons_report():
    cancelled_lessons = await db.lessons.find({
        "status": LessonStatus.CANCELLED
    }, {"_id": 0}).sort("cancelled_at", -1).to_list(1000)
    return cancelled_lessons

# Settings endpoints
@api_router.get("/settings")
async def get_all_settings():
    settings = await db.settings.find({}, {"_id": 0}).to_list(1000)
    return settings

@api_router.get("/settings/{category}")
async def get_settings_by_category(category: str):
    settings = await db.settings.find({"category": category}, {"_id": 0}).to_list(100)
    return settings

@api_router.get("/settings/{category}/{key}")
async def get_specific_setting(category: str, key: str):
    setting = await db.settings.find_one({"category": category, "key": key}, {"_id": 0})
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@api_router.put("/settings/{category}/{key}")
async def update_setting(category: str, key: str, update_data: dict, current_user: User = Depends(get_current_user)):
    value = update_data.get("value")
    
    # Validate hex colors for color settings
    if "color" in key.lower() and isinstance(value, str):
        if not is_valid_hex_color(value):
            raise HTTPException(status_code=400, detail="Invalid hex color format")
    
    result = await db.settings.update_one(
        {"category": category, "key": key},
        {"$set": {"value": value, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    return {"message": "Setting updated successfully", "category": category, "key": key, "value": value}

# User management endpoints
@api_router.get("/users")
async def get_users():
    users = await db.users.find({}, {"_id": 0}).to_list(1000)
    return [UserResponse(**user) for user in users]

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.OWNER, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

# Root route handler for Railway
@app.get("/")
async def root():
    return {"message": "Dance Studio CRM API", "status": "running", "version": "1.0.0"}

# Health check at root level (without /api prefix)
@app.get("/health")
async def root_health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Include the API router in the app
app.include_router(api_router)