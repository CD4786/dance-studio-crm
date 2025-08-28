# Update enrollment creation to broadcast real-time updates
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

# Enhanced payment creation with enrollment credit updates and broadcasts
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

# Enhanced attendance marking with comprehensive updates
@api_router.post("/lessons/{lesson_id}/attend")
async def mark_lesson_attendance(lesson_id: str, current_user: User = Depends(get_current_user)):
    lesson = await db.lessons.find_one({"id": lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # Get student info
    student = await db.students.find_one({"id": lesson.get("student_id")})
    student_name = student["name"] if student else "Unknown Student"
    
    # Mark lesson as attended
    await db.lessons.update_one(
        {"id": lesson_id},
        {"$set": {"is_attended": True, "attended_at": datetime.utcnow()}}
    )
    
    # Find and deduct from student's available lesson credits
    student_id = lesson.get("student_id")
    enrollment_updated = None
    if student_id:
        # Find an active enrollment with available lessons for this student
        enrollments = await db.enrollments.find({
            "student_id": student_id,
            "is_active": True
        }).to_list(100)
        
        # Find enrollment with available lessons (prioritize by purchase date)
        for enrollment_doc in sorted(enrollments, key=lambda x: x.get("purchase_date", datetime.min)):
            enrollment = Enrollment(**enrollment_doc)
            enrollment.calculate_totals()
            
            if enrollment.lessons_available > 0:
                # Deduct one lesson from available lessons
                await db.enrollments.update_one(
                    {"id": enrollment.id},
                    {
                        "$inc": {"lessons_taken": 1},
                        "$set": {"modified_at": datetime.utcnow()}
                    }
                )
                
                # Recalculate and update the enrollment totals
                updated_enrollment_doc = await db.enrollments.find_one({"id": enrollment.id})
                updated_enrollment = Enrollment(**updated_enrollment_doc)
                updated_enrollment.calculate_totals()
                
                await db.enrollments.update_one(
                    {"id": enrollment.id},
                    {"$set": {
                        "lessons_available": updated_enrollment.lessons_available,
                        "remaining_lessons": updated_enrollment.remaining_lessons
                    }}
                )
                enrollment_updated = updated_enrollment
                break
    
    # Broadcast comprehensive attendance update
    await manager.broadcast_update(
        "lesson_attended",
        {
            "lesson_id": lesson_id,
            "student_id": student_id,
            "student_name": student_name,
            "lesson_date": lesson.get("start_datetime").isoformat() if lesson.get("start_datetime") else None,
            "enrollment_updated": {
                "enrollment_id": enrollment_updated.id,
                "lessons_taken": enrollment_updated.lessons_taken,
                "lessons_available": enrollment_updated.lessons_available,
                "remaining_lessons": enrollment_updated.remaining_lessons,
                "program_name": enrollment_updated.program_name
            } if enrollment_updated else None
        },
        current_user.id,
        current_user.name
    )
    
    return {"message": "Attendance marked successfully"}

# Enhanced student ledger endpoint with comprehensive data
@api_router.get("/students/{student_id}/ledger")
async def get_student_ledger(student_id: str, current_user: User = Depends(get_current_user)):
    # Get student info
    student = await db.students.find_one({"id": student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get all enrollments
    enrollments = await db.enrollments.find({"student_id": student_id}).to_list(1000)
    enrollment_list = []
    total_enrolled_lessons = 0
    total_lessons_taken = 0
    total_lessons_available = 0
    total_amount_paid = 0
    total_grand_total = 0
    
    for enrollment_doc in enrollments:
        enrollment = Enrollment(**enrollment_doc)
        enrollment.calculate_totals()
        
        enrollment_data = enrollment.dict()
        enrollment_list.append(enrollment_data)
        
        if enrollment.is_active:
            total_enrolled_lessons += enrollment.total_lessons
            total_lessons_taken += enrollment.lessons_taken
            total_lessons_available += enrollment.lessons_available
            total_amount_paid += enrollment.amount_paid
            total_grand_total += enrollment.grand_total
    
    # Get all payments
    payments = await db.payments.find({"student_id": student_id}).sort("payment_date", -1).to_list(1000)
    
    # Get recent lessons
    lessons = await db.lessons.find({"student_id": student_id}).sort("start_datetime", -1).limit(10).to_list(10)
    
    return {
        "student": student,
        "enrollments": enrollment_list,
        "payments": payments,
        "recent_lessons": lessons,
        "summary": {
            "total_enrolled_lessons": total_enrolled_lessons,
            "total_lessons_taken": total_lessons_taken,
            "total_lessons_available": total_lessons_available,
            "total_amount_paid": total_amount_paid,
            "total_grand_total": total_grand_total,
            "total_balance_remaining": total_grand_total - total_amount_paid
        }
    }