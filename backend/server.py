from fastapi import FastAPI, APIRouter, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, date, time, timedelta
from enum import Enum
import jwt
from passlib.context import CryptContext
import hashlib

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
async def create_teacher(teacher_data: TeacherCreate):
    teacher = Teacher(**teacher_data.dict())
    await db.teachers.insert_one(teacher.dict())
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

# Dashboard stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    total_classes = await db.classes.count_documents({})
    total_teachers = await db.teachers.count_documents({})
    
    # Classes today
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    classes_today = await db.classes.count_documents({
        "start_datetime": {"$gte": today, "$lt": tomorrow}
    })
    
    return {
        "total_classes": total_classes,
        "total_teachers": total_teachers,
        "classes_today": classes_today
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()