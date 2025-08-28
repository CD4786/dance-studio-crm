// Enhanced WebSocket handling for real-time synchronization
const handleRealTimeUpdate = (message) => {
  console.log('Real-time update received:', message);
  
  // Handle enrollment updates
  if (message.type === 'enrollment_created' || message.type === 'enrollment_updated') {
    console.log(`Enrollment ${message.type} for student: ${message.data.student_name}`);
    
    // Trigger comprehensive refresh for all enrollment-related displays
    onRefresh();
    handleFastRefresh();
    
    // Show notification
    setNotifications(prev => [...prev, {
      id: Date.now(),
      type: 'success',
      message: `Enrollment ${message.type === 'enrollment_created' ? 'added' : 'updated'} for ${message.data.student_name}: ${message.data.program_name}`,
      timestamp: new Date()
    }]);
  }
  
  // Handle payment updates
  else if (message.type === 'payment_created') {
    console.log(`Payment created for student: ${message.data.student_name}`);
    
    // Trigger comprehensive refresh
    onRefresh();
    handleFastRefresh();
    
    // Show detailed notification with lesson credit update
    const creditMessage = message.data.enrollment_updated ? 
      ` | ${message.data.enrollment_updated.lessons_available} lessons now available in ${message.data.enrollment_updated.program_name}` : '';
    
    setNotifications(prev => [...prev, {
      id: Date.now(),
      type: 'success', 
      message: `Payment of $${message.data.amount} received from ${message.data.student_name}${creditMessage}`,
      timestamp: new Date()
    }]);
  }
  
  // Handle lesson attendance updates
  else if (message.type === 'lesson_attended') {
    console.log(`Lesson attendance marked for student: ${message.data.student_name}`);
    
    // Trigger comprehensive refresh
    onRefresh();
    handleFastRefresh();
    
    // Show detailed notification with remaining credits
    const creditMessage = message.data.enrollment_updated ? 
      ` | ${message.data.enrollment_updated.lessons_available} lessons remaining in ${message.data.enrollment_updated.program_name}` : '';
    
    setNotifications(prev => [...prev, {
      id: Date.now(),
      type: 'info',
      message: `${message.data.student_name} marked present${creditMessage}`,
      timestamp: new Date()
    }]);
  }
  
  // Handle other lesson updates
  else if (message.type === 'lesson_created' || message.type === 'lesson_updated' || message.type === 'lesson_cancelled') {
    console.log(`Lesson ${message.type}:`, message.data);
    
    // Trigger refresh for calendar and lesson displays
    onRefresh();
    handleFastRefresh();
    
    setNotifications(prev => [...prev, {
      id: Date.now(),
      type: message.type === 'lesson_cancelled' ? 'warning' : 'info',
      message: `Lesson ${message.type.replace('lesson_', '')} for ${message.data.student_name || 'student'}`,
      timestamp: new Date()
    }]);
  }
  
  // Handle general updates
  else {
    console.log('General update received:', message.type);
    onRefresh();
  }
  
  // Auto-remove notifications after 5 seconds
  setTimeout(() => {
    setNotifications(prev => prev.filter(n => n.id !== Date.now()));
  }, 5000);
};

// Enhanced attendance handling with credit checking
const handleAttendLesson = async (lessonId) => {
  try {
    // First, get the lesson to find the student ID
    const lesson = calendarData.lessons.find(l => l.id === lessonId);
    if (!lesson) {
      alert('Lesson not found');
      return;
    }

    // Check if student has available lesson credits
    const creditsResponse = await axios.get(`${API}/students/${lesson.student_id}/lesson-credits`);
    const availableLessons = creditsResponse.data.total_lessons_available;

    if (availableLessons <= 0) {
      const confirmMessage = `⚠️ ${lesson.student_name} has NO available lesson credits!\n\nOptions:\n1. Add payment to unlock lessons\n2. Mark attendance anyway (will create negative balance)\n\nContinue anyway?`;
      
      if (!window.confirm(confirmMessage)) {
        // Open ledger to add payment
        const student = students.find(s => s.id === lesson.student_id);
        if (student) {
          setSelectedStudentForLedger(student);
          setSelectedLessonForLedger(lesson);
          setShowLedgerModal(true);
        }
        return;
      }
    }

    // Confirm attendance marking with credit info
    const confirmMessage = availableLessons > 0 ? 
      `✅ Mark ${lesson.student_name} as attended?\n\nThis will deduct 1 lesson credit.\nRemaining after: ${availableLessons - 1} lessons` :
      `⚠️ Mark ${lesson.student_name} as attended?\n\nWARNING: Student has no available credits.\nThis will create a negative balance.`;
      
    if (!window.confirm(confirmMessage)) {
      return;
    }

    // Mark attendance - backend will handle credit deduction and broadcasting
    await axios.post(`${API}/lessons/${lessonId}/attend`);
    
    // Success message will come via WebSocket real-time update
    console.log(`Attendance marked for ${lesson.student_name}`);
    
  } catch (error) {
    console.error('Failed to mark attendance:', error);
    alert('Failed to mark attendance: ' + (error.response?.data?.detail || error.message));
  }
};