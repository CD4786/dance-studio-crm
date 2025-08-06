from fastapi import FastAPI, APIRouter, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# Student Routes
@api_router.post("/students", response_model=Student)
async def create_student(student_data: StudentCreate):
    student = Student(**student_data.dict())
    await db.students.insert_one(student.dict())
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
async def update_student(student_id: str, student_data: StudentCreate):
    existing_student = await db.students.find_one({"id": student_id})
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    update_data = student_data.dict()
    await db.students.update_one({"id": student_id}, {"$set": update_data})
    
    updated_student = await db.students.find_one({"id": student_id})
    return Student(**updated_student)

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
    
    # Calculate end time
    end_datetime = lesson_data.start_datetime + timedelta(minutes=lesson_data.duration_minutes)
    
    # Create lesson
    lesson = PrivateLesson(
        student_id=lesson_data.student_id,
        teacher_id=lesson_data.teacher_id,
        start_datetime=lesson_data.start_datetime,
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
async def update_private_lesson(lesson_id: str, lesson_data: PrivateLessonUpdate):
    # Verify lesson exists
    existing_lesson = await db.lessons.find_one({"id": lesson_id})
    if not existing_lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Prepare update data
    update_data = {}
    for field, value in lesson_data.dict().items():
        if value is not None:
            update_data[field] = value
    
    # If updating datetime and duration, recalculate end_datetime
    if "start_datetime" in update_data and "duration_minutes" in update_data:
        update_data["end_datetime"] = update_data["start_datetime"] + timedelta(minutes=update_data["duration_minutes"])
    elif "start_datetime" in update_data:
        # Keep the same duration
        duration = (existing_lesson["end_datetime"] - existing_lesson["start_datetime"]).seconds // 60
        update_data["end_datetime"] = update_data["start_datetime"] + timedelta(minutes=duration)
    
    await db.lessons.update_one({"id": lesson_id}, {"$set": update_data})
    
    # Get updated lesson with enriched data
    updated_lesson = await db.lessons.find_one({"id": lesson_id})
    student = await db.students.find_one({"id": updated_lesson["student_id"]})
    teacher = await db.teachers.find_one({"id": updated_lesson["teacher_id"]})
    
    return PrivateLessonResponse(
        **updated_lesson,
        student_name=student["name"] if student else "Unknown",
        teacher_name=teacher["name"] if teacher else "Unknown"
    )

@api_router.delete("/lessons/{lesson_id}")
async def delete_private_lesson(lesson_id: str):
    result = await db.lessons.delete_one({"id": lesson_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"message": "Lesson deleted successfully"}

@api_router.post("/lessons/{lesson_id}/attend")
async def mark_lesson_attended(lesson_id: str):
    # Get lesson
    lesson = await db.lessons.find_one({"id": lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Mark as attended
    await db.lessons.update_one({"id": lesson_id}, {"$set": {"is_attended": True}})
    
    # If lesson has enrollment, deduct from remaining lessons
    if lesson.get("enrollment_id"):
        enrollment = await db.enrollments.find_one({"id": lesson["enrollment_id"]})
        if enrollment and enrollment["remaining_lessons"] > 0:
            await db.enrollments.update_one(
                {"id": lesson["enrollment_id"]}, 
                {"$inc": {"remaining_lessons": -1}}
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