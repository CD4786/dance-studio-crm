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
    date: date
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
    date: date
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
    teachers = await db.teachers.find({"is_active": True}).to_list(1000)
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
    students = await db.students.find().to_list(1000)
    return students

@api_router.post("/students", response_model=Student)
async def create_student(student_data: StudentCreate, current_user: User = Depends(get_current_user)):
    student = Student(**student_data.dict())
    await db.students.insert_one(student.dict())
    return student