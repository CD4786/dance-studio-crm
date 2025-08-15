import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import wsManager from "./websocket";
import RecurringLessonModal from "./RecurringLessonModal";
import StudentLedger from "./StudentLedger";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext(null);

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      const userData = localStorage.getItem('user');
      if (userData) {
        try {
          setUser(JSON.parse(userData));
        } catch (error) {
          console.error('Failed to parse user data:', error);
          // Clear invalid data
          localStorage.removeItem('user');
          localStorage.removeItem('token');
          setToken(null);
        }
      }
    }
  }, [token]);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user: userData } = response.data;
      
      setToken(access_token);
      setUser(userData);
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const register = async (userData) => {
    try {
      await axios.post(`${API}/auth/register`, userData);
      return true;
    } catch (error) {
      console.error('Registration failed:', error);
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// UI Components
const Card = ({ children, className = "" }) => (
  <div className={`card ${className}`}>{children}</div>
);

const Button = ({ children, onClick, className = "", variant = "primary", type = "button", disabled = false }) => (
  <button 
    type={type}
    onClick={onClick} 
    disabled={disabled}
    className={`btn ${variant === 'outline' ? 'btn-outline' : 'btn-primary'} ${className}`}
  >
    {children}
  </button>
);

const Input = ({ type = "text", value, onChange, placeholder, className = "", name, required = false }) => (
  <input
    type={type}
    value={value}
    onChange={onChange}
    placeholder={placeholder}
    name={name}
    required={required}
    className={`input ${className}`}
  />
);

const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          {children}
        </div>
      </div>
    </div>
  );
};

// Login Page
const LoginPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    role: 'owner',
    studio_name: ''
  });
  const { login, register, token } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = isLogin ? 
      await login(formData.email, formData.password) :
      await register(formData);
    
    if (success && !isLogin) {
      setIsLogin(true);
      setFormData({ ...formData, password: '' });
      alert('Registration successful! Please login.');
    }
  };

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  if (token) {
    return <MainApp />;
  }

  return (
    <div className="login-page">
      <div className="login-background"></div>
      <Card className="login-card">
        <h2>{isLogin ? 'Welcome Back' : 'Create Account'}</h2>
        <p>{isLogin ? 'Sign in to your studio account' : 'Set up your dance studio management'}</p>
        
        <form onSubmit={handleSubmit} className="login-form">
          {!isLogin && (
            <>
              <Input
                name="name"
                type="text"
                placeholder="Full Name"
                value={formData.name}
                onChange={handleInputChange}
                required
              />
              <Input
                name="studio_name"
                type="text"
                placeholder="Studio Name (optional)"
                value={formData.studio_name}
                onChange={handleInputChange}
              />
              <select 
                name="role" 
                value={formData.role} 
                onChange={handleInputChange}
                className="input"
              >
                <option value="owner">Studio Owner</option>
                <option value="manager">Manager</option>
                <option value="teacher">Teacher</option>
              </select>
            </>
          )}
          
          <Input
            name="email"
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleInputChange}
            required
          />
          <Input
            name="password"
            type="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleInputChange}
            required
          />
          
          <Button type="submit" className="w-full">
            {isLogin ? 'Sign In' : 'Create Account'}
          </Button>
        </form>
        
        <div className="login-switch">
          <button
            type="button"
            onClick={() => setIsLogin(!isLogin)}
          >
            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </div>
      </Card>
    </div>
  );
};

// Dashboard Component
const Dashboard = ({ onRefresh, onNavigate }) => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
  }, [onRefresh]);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  if (!stats) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      <div className="stats-grid">
        <Card 
          className="stat-card clickable"
          onClick={() => onNavigate && onNavigate('students')}
        >
          <div className="stat-content">
            <div>
              <p className="stat-number">{stats.total_students}</p>
              <p className="stat-label">Active Students</p>
            </div>
            <div className="stat-icon">👥</div>
          </div>
        </Card>
        
        <Card 
          className="stat-card clickable"
          onClick={() => onNavigate && onNavigate('teachers')}
        >
          <div className="stat-content">
            <div>
              <p className="stat-number">{stats.total_teachers}</p>
              <p className="stat-label">Teachers</p>
            </div>
            <div className="stat-icon">🎭</div>
          </div>
        </Card>
        
        <Card 
          className="stat-card clickable"
          onClick={() => onNavigate && onNavigate('students')}
        >
          <div className="stat-content">
            <div>
              <p className="stat-number">{stats.active_enrollments}</p>
              <p className="stat-label">Active Enrollments</p>
            </div>
            <div className="stat-icon">📚</div>
          </div>
        </Card>
        
        <Card 
          className="stat-card clickable"
          onClick={() => onNavigate && onNavigate('daily-calendar')}
        >
          <div className="stat-content">
            <div>
              <p className="stat-number">{stats.lessons_today}</p>
              <p className="stat-label">Lessons Today</p>
            </div>
            <div className="stat-icon">📅</div>
          </div>
        </Card>
        
        <Card 
          className="stat-card clickable"
          onClick={() => onNavigate && onNavigate('daily-calendar')}
        >
          <div className="stat-content">
            <div>
              <p className="stat-number">{stats.lessons_attended_today}</p>
              <p className="stat-label">Lessons Attended Today</p>
            </div>
            <div className="stat-icon">✅</div>
          </div>
        </Card>
        
        <Card className="stat-card">
          <div className="stat-content">
            <div>
              <p className="stat-number">${stats.estimated_monthly_revenue}</p>
              <p className="stat-label">Monthly Revenue</p>
            </div>
            <div className="stat-icon">💰</div>
          </div>
        </Card>
      </div>
    </div>
  );
};

// Daily Calendar Component
const DailyCalendar = ({ selectedDate, onRefresh }) => {
  const [calendarData, setCalendarData] = useState(null);
  const [currentDate, setCurrentDate] = useState(selectedDate);
  const [draggedLesson, setDraggedLesson] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showRecurringModal, setShowRecurringModal] = useState(false);
  const [selectedTimeSlot, setSelectedTimeSlot] = useState(null);
  const [editingLesson, setEditingLesson] = useState(null);
  const [students, setStudents] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [newLessonData, setNewLessonData] = useState({
    student_id: '',
    teacher_id: '',
    notes: '',
    enrollment_id: ''
  });

  const hours = [];
  for (let i = 9; i <= 21; i++) {
    hours.push(i);
  }

  useEffect(() => {
    setCurrentDate(selectedDate);
  }, [selectedDate]);

  useEffect(() => {
    fetchDailyData();
    fetchStudents();
    fetchTeachers();
  }, [currentDate, onRefresh]);

  const fetchDailyData = async () => {
    try {
      // Use local date string to avoid timezone conversion issues
      const year = currentDate.getFullYear();
      const month = String(currentDate.getMonth() + 1).padStart(2, '0');
      const day = String(currentDate.getDate()).padStart(2, '0');
      const dateStr = `${year}-${month}-${day}`;
      
      console.log('Fetching daily data for date:', dateStr, 'from currentDate:', currentDate);
      
      const response = await axios.get(`${API}/calendar/daily/${dateStr}`);
      setCalendarData(response.data);
    } catch (error) {
      console.error('Failed to fetch daily data:', error);
    }
  };

  const calculateInstructorStats = async (teacherId) => {
    try {
      // Get all lessons for the instructor
      const response = await axios.get(`${API}/lessons`);
      const allLessons = response.data.filter(lesson => lesson.teacher_id === teacherId);
      
      const today = new Date(currentDate);
      const todayStart = new Date(today);
      todayStart.setHours(0, 0, 0, 0);
      const todayEnd = new Date(today);
      todayEnd.setHours(23, 59, 59, 999);
      
      console.log(`Calculating stats for teacher ${teacherId}:`, {
        totalLessons: allLessons.length,
        currentDate: today.toISOString()
      });
      
      // Daily count (today)
      const dailyCount = allLessons.filter(lesson => {
        const lessonDate = new Date(lesson.start_datetime);
        return lessonDate >= todayStart && lessonDate <= todayEnd;
      }).length;
      
      // Weekly count (current week - Monday to Sunday)
      const weekStart = new Date(today);
      const dayOfWeek = weekStart.getDay();
      const diff = weekStart.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1); // Monday start
      weekStart.setDate(diff);
      weekStart.setHours(0, 0, 0, 0);
      
      const weekEnd = new Date(weekStart);
      weekEnd.setDate(weekStart.getDate() + 6);
      weekEnd.setHours(23, 59, 59, 999);
      
      const weeklyCount = allLessons.filter(lesson => {
        const lessonDate = new Date(lesson.start_datetime);
        return lessonDate >= weekStart && lessonDate <= weekEnd;
      }).length;
      
      // Monthly count (current month)
      const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
      monthStart.setHours(0, 0, 0, 0);
      const monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0);
      monthEnd.setHours(23, 59, 59, 999);
      
      const monthlyCount = allLessons.filter(lesson => {
        const lessonDate = new Date(lesson.start_datetime);
        return lessonDate >= monthStart && lessonDate <= monthEnd;
      }).length;
      
      console.log(`Stats for teacher ${teacherId}:`, {
        daily: dailyCount,
        weekly: weeklyCount, 
        monthly: monthlyCount,
        weekRange: `${weekStart.toDateString()} - ${weekEnd.toDateString()}`,
        monthRange: `${monthStart.toDateString()} - ${monthEnd.toDateString()}`
      });
      
      return {
        daily: dailyCount,
        weekly: weeklyCount,
        monthly: monthlyCount
      };
    } catch (error) {
      console.error('Failed to calculate instructor stats:', error);
      return { daily: 0, weekly: 0, monthly: 0 };
    }
  };

  const InstructorStatsDisplay = ({ teacherId, teacherName }) => {
    const [stats, setStats] = useState({ daily: 0, weekly: 0, monthly: 0 });
    const [isLoading, setIsLoading] = useState(true);
    
    useEffect(() => {
      const loadStats = async () => {
        setIsLoading(true);
        const instructorStats = await calculateInstructorStats(teacherId);
        setStats(instructorStats);
        setIsLoading(false);
      };
      
      if (teacherId) {
        loadStats();
      }
    }, [teacherId, currentDate, onRefresh]); // Added onRefresh as dependency
    
    return (
      <div className="instructor-stats">
        <div className="instructor-name">{teacherName}</div>
        <div className="stats-row">
          <span className="stat-item" title="Lessons today">
            📅 {isLoading ? '...' : stats.daily}
          </span>
          <span className="stat-item" title="Lessons this week">
            📊 {isLoading ? '...' : stats.weekly}
          </span>
          <span className="stat-item" title="Lessons this month">
            📈 {isLoading ? '...' : stats.monthly}
          </span>
        </div>
      </div>
    );
  };

  const fetchStudents = async () => {
    try {
      const response = await axios.get(`${API}/students`);
      setStudents(response.data);
    } catch (error) {
      console.error('Failed to fetch students:', error);
    }
  };

  const fetchTeachers = async () => {
    try {
      const response = await axios.get(`${API}/teachers`);
      setTeachers(response.data);
    } catch (error) {
      console.error('Failed to fetch teachers:', error);
    }
  };

  const handleTimeSlotClick = (hour, teacherId) => {
    setSelectedTimeSlot({ hour, teacherId });
    setNewLessonData({
      student_id: '',
      teacher_id: teacherId,
      notes: '',
      enrollment_id: ''
    });
    setShowAddModal(true);
  };

  const navigateDay = (direction) => {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + direction);
    setCurrentDate(newDate);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const handleCreateLesson = async (e) => {
    e.preventDefault();
    try {
      // Use currentDate directly to avoid any timezone conversion issues
      const year = currentDate.getFullYear();
      const month = String(currentDate.getMonth() + 1).padStart(2, '0');
      const day = String(currentDate.getDate()).padStart(2, '0');
      const hour = String(selectedTimeSlot.hour).padStart(2, '0');
      const localISOString = `${year}-${month}-${day}T${hour}:00:00`;
      
      console.log('Creating lesson for currentDate:', currentDate);
      console.log('Creating lesson for datetime string:', localISOString);
      
      await axios.post(`${API}/lessons`, {
        ...newLessonData,
        start_datetime: localISOString,
        duration_minutes: 60
      });

      setShowAddModal(false);
      fetchDailyData();
      onRefresh();
    } catch (error) {
      console.error('Failed to create lesson:', error);
      alert('Failed to create lesson');
    }
  };

  const handleCreateRecurringLesson = async (recurringData) => {
    try {
      console.log('Creating recurring lessons:', recurringData);
      
      const response = await axios.post(`${API}/recurring-lessons`, recurringData);
      console.log('Recurring lessons created:', response.data);
      
      setShowRecurringModal(false);
      fetchDailyData();
      onRefresh();
      
      alert(`Successfully created ${response.data.lessons_created} recurring lessons!`);
    } catch (error) {
      console.error('Failed to create recurring lessons:', error);
      alert('Failed to create recurring lessons: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleTimeSlotRightClick = (e, hour, teacherId) => {
    e.preventDefault(); // Prevent context menu
    console.log('Right-click detected on time slot:', hour, teacherId);
    
    // Prepare recurring lesson modal with pre-filled data
    const startDateTime = new Date(currentDate);
    startDateTime.setHours(hour, 0, 0, 0);
    
    const localISOString = startDateTime.toISOString().slice(0, 16); // Format for datetime-local input
    
    setSelectedTimeSlot({ 
      hour, 
      teacherId, 
      datetime: localISOString 
    });
    setShowRecurringModal(true);
  };

  const handleEditLesson = (lesson) => {
    setEditingLesson(lesson);
    setNewLessonData({
      student_id: lesson.student_id,
      teacher_id: lesson.teacher_id,
      notes: lesson.notes || '',
      enrollment_id: lesson.enrollment_id || ''
    });
    setShowEditModal(true);
  };

  const handleUpdateLesson = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/lessons/${editingLesson.id}`, newLessonData);
      setShowEditModal(false);
      fetchDailyData();
      onRefresh();
    } catch (error) {
      console.error('Failed to update lesson:', error);
      alert('Failed to update lesson');
    }
  };

  const handleDeleteLesson = async (lessonId) => {
    if (window.confirm('Are you sure you want to delete this lesson?')) {
      try {
        await axios.delete(`${API}/lessons/${lessonId}`);
        fetchDailyData();
        onRefresh();
      } catch (error) {
        console.error('Failed to delete lesson:', error);
        alert('Failed to delete lesson');
      }
    }
  };

  const handleAttendLesson = async (lessonId) => {
    try {
      await axios.post(`${API}/lessons/${lessonId}/attend`);
      fetchDailyData();
      onRefresh();
      alert('Attendance marked successfully!');
    } catch (error) {
      console.error('Failed to mark attendance:', error);
      alert('Failed to mark attendance');
    }
  };

  const handleSendReminder = async (lessonId, type) => {
    try {
      const response = await axios.post(`${API}/notifications/send-reminder`, {
        lesson_id: lessonId,
        notification_type: type
      });
      alert(`${type.toUpperCase()} reminder sent successfully!`);
    } catch (error) {
      console.error('Failed to send reminder:', error);
      alert(`Failed to send ${type} reminder: ${error.response?.data?.detail || 'Unknown error'}`);
    }
  };

  const handleDragStart = (lesson, e) => {
    setDraggedLesson(lesson);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = async (hour, teacherId, e) => {
    e.preventDefault();
    
    if (!draggedLesson) return;

    try {
      // Create date in local timezone
      const startDateTime = new Date(currentDate);
      startDateTime.setHours(hour, 0, 0, 0);
      
      // Convert to local ISO string (without timezone conversion)
      const year = startDateTime.getFullYear();
      const month = String(startDateTime.getMonth() + 1).padStart(2, '0');
      const day = String(startDateTime.getDate()).padStart(2, '0');
      const hourStr = String(hour).padStart(2, '0');
      const localISOString = `${year}-${month}-${day}T${hourStr}:00:00`;
      
      console.log('Moving lesson to:', localISOString);
      
      await axios.put(`${API}/lessons/${draggedLesson.id}`, {
        teacher_id: teacherId,
        start_datetime: localISOString,
        duration_minutes: 60
      });

      setDraggedLesson(null);
      fetchDailyData();
      onRefresh();
    } catch (error) {
      console.error('Failed to move lesson:', error);
      alert('Failed to move lesson');
    }
  };

  const getLessonForSlot = (hour, teacherId) => {
    if (!calendarData?.lessons) return null;
    return calendarData.lessons.find(lesson => {
      const lessonHour = new Date(lesson.start_datetime).getHours();
      return lessonHour === hour && lesson.teacher_id === teacherId;
    });
  };

  const LessonBlock = ({ lesson, onEdit, onDelete, onAttend, onSendReminder }) => (
    <div 
      className={`lesson-block ${lesson.is_attended ? 'attended' : ''}`}
      draggable
      onDragStart={(e) => handleDragStart(lesson, e)}
    >
      <div className="lesson-content">
        <div className="lesson-student">{lesson.student_name}</div>
        <div className="lesson-time">
          {new Date(lesson.start_datetime).toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit' 
          })}
        </div>
        {lesson.notes && <div className="lesson-notes">{lesson.notes}</div>}
      </div>
      <div className="lesson-actions">
        <button onClick={() => onEdit(lesson)} className="lesson-action-btn" title="Edit">✏️</button>
        <button onClick={() => onDelete(lesson.id)} className="lesson-action-btn" title="Delete">🗑️</button>
        {!lesson.is_attended && (
          <button onClick={() => onAttend(lesson.id)} className="lesson-action-btn" title="Mark Attended">✅</button>
        )}
        <button onClick={() => onSendReminder(lesson.id, 'email')} className="lesson-action-btn" title="Send Email Reminder">📧</button>
        <button onClick={() => onSendReminder(lesson.id, 'sms')} className="lesson-action-btn" title="Send SMS Reminder">📱</button>
      </div>
    </div>
  );

  if (!calendarData) return <div>Loading calendar...</div>;

  return (
    <div className="daily-calendar">
      <div className="calendar-header">
        <div className="calendar-title">
          <h2>Daily Schedule - {currentDate.toDateString()}</h2>
          <div className="calendar-navigation">
            <button 
              className="btn btn-outline nav-btn"
              onClick={() => navigateDay(-1)}
              title="Previous day"
            >
              ← Previous
            </button>
            <button 
              className="btn btn-outline nav-btn"
              onClick={goToToday}
              title="Go to today"
            >
              Today
            </button>
            <button 
              className="btn btn-outline nav-btn"
              onClick={() => navigateDay(1)}
              title="Next day"
            >
              Next →
            </button>
          </div>
        </div>
        <div className="calendar-controls">
          <button 
            className="btn btn-primary"
            onClick={() => setShowRecurringModal(true)}
            title="Create recurring lessons"
          >
            🔄 Recurring Lessons
          </button>
        </div>
      </div>
      
      <div className="calendar-grid">
        <div className="time-column">
          <div className="time-header">Time</div>
          {hours.map(hour => (
            <div key={hour} className="time-slot">
              {hour > 12 ? hour - 12 : hour}:00 {hour >= 12 ? 'PM' : 'AM'}
            </div>
          ))}
        </div>
        
        {calendarData.teachers.map(teacher => (
          <div key={teacher.id} className="teacher-column">
            <div className="teacher-header">
              <InstructorStatsDisplay 
                teacherId={teacher.id}
                teacherName={teacher.name}
              />
            </div>
            {hours.map(hour => {
              const lesson = getLessonForSlot(hour, teacher.id);
              return (
                <div 
                  key={`${teacher.id}-${hour}`}
                  className="calendar-slot"
                  onClick={() => !lesson && handleTimeSlotClick(hour, teacher.id)}
                  onContextMenu={(e) => !lesson && handleTimeSlotRightClick(e, hour, teacher.id)}
                  onDragOver={handleDragOver}
                  onDrop={(e) => handleDrop(hour, teacher.id, e)}
                  title={!lesson ? "Left click: Add single lesson | Right click: Add recurring lessons" : ""}
                >
                  {lesson ? (
                    <LessonBlock 
                      lesson={lesson}
                      onEdit={handleEditLesson}
                      onDelete={handleDeleteLesson}
                      onAttend={handleAttendLesson}
                      onSendReminder={handleSendReminder}
                    />
                  ) : (
                    <div className="empty-slot">+</div>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>

      <Modal 
        isOpen={showAddModal} 
        onClose={() => setShowAddModal(false)}
        title="Add Private Lesson"
      >
        <form onSubmit={handleCreateLesson}>
          <div className="form-group">
            <label>Student</label>
            <select
              value={newLessonData.student_id}
              onChange={(e) => setNewLessonData({...newLessonData, student_id: e.target.value})}
              required
              className="input"
            >
              <option value="">Select Student</option>
              {students.map(student => (
                <option key={student.id} value={student.id}>{student.name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Notes</label>
            <textarea
              value={newLessonData.notes}
              onChange={(e) => setNewLessonData({...newLessonData, notes: e.target.value})}
              placeholder="Lesson notes..."
              className="input"
              rows="3"
            />
          </div>
          <Button type="submit">Create Lesson</Button>
        </form>
      </Modal>

      <Modal 
        isOpen={showEditModal} 
        onClose={() => setShowEditModal(false)}
        title="Edit Private Lesson"
      >
        <form onSubmit={handleUpdateLesson}>
          <div className="form-group">
            <label>Student</label>
            <select
              value={newLessonData.student_id}
              onChange={(e) => setNewLessonData({...newLessonData, student_id: e.target.value})}
              required
              className="input"
            >
              <option value="">Select Student</option>
              {students.map(student => (
                <option key={student.id} value={student.id}>{student.name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Notes</label>
            <textarea
              value={newLessonData.notes}
              onChange={(e) => setNewLessonData({...newLessonData, notes: e.target.value})}
              placeholder="Lesson notes..."
              className="input"
              rows="3"
            />
          </div>
          <Button type="submit">Update Lesson</Button>
        </form>
      </Modal>

      {/* Recurring Lesson Modal */}
      <RecurringLessonModal
        isOpen={showRecurringModal}
        onClose={() => setShowRecurringModal(false)}
        onSubmit={handleCreateRecurringLesson}
        students={students}
        teachers={teachers}
        selectedSlot={selectedTimeSlot}
      />
    </div>
  );
};

// Students Manager Component
const StudentsManager = ({ onRefresh }) => {
  const [students, setStudents] = useState([]);
  const [programs, setPrograms] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [showNotificationModal, setShowNotificationModal] = useState(false);
  const [showLedger, setShowLedger] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [notificationPrefs, setNotificationPrefs] = useState({
    email_enabled: true,
    sms_enabled: false,
    reminder_hours: 24,
    email_address: '',
    phone_number: ''
  });
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    parent_name: '',
    parent_phone: '',
    parent_email: '',
    notes: ''
  });
  const [enrollmentData, setEnrollmentData] = useState({
    program_name: '',
    total_lessons: '',
    total_paid: ''
  });

  useEffect(() => {
    fetchStudents();
    fetchPrograms();
  }, [onRefresh]);

  const fetchStudents = async () => {
    try {
      const response = await axios.get(`${API}/students`);
      setStudents(response.data);
    } catch (error) {
      console.error('Failed to fetch students:', error);
    }
  };

  const fetchPrograms = async () => {
    try {
      const response = await axios.get(`${API}/programs`);
      setPrograms(response.data);
    } catch (error) {
      console.error('Failed to fetch programs:', error);
    }
  };

  const handleAddStudent = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/students`, formData);
      setShowAddModal(false);
      fetchStudents();
      onRefresh();
      setFormData({
        name: '',
        email: '',
        phone: '',
        parent_name: '',
        parent_phone: '',
        parent_email: '',
        notes: ''
      });
    } catch (error) {
      console.error('Failed to add student:', error);
      alert('Failed to add student');
    }
  };

  const handleEnroll = (student) => {
    setSelectedStudent(student);
    setEnrollmentData({
      program_name: '',
      total_lessons: '',
      total_paid: ''
    });
    setShowEnrollModal(true);
  };

  const handleDeleteStudent = async (studentId, studentName) => {
    if (window.confirm(`Are you sure you want to delete ${studentName}? This action cannot be undone.`)) {
      try {
        const response = await axios.delete(`${API}/students/${studentId}`);
        alert(response.data.message);
        fetchStudents();
        onRefresh();
      } catch (error) {
        console.error('Failed to delete student:', error);
        alert('Failed to delete student');
      }
    }
  };

  const handleNotificationPrefs = async (student) => {
    setSelectedStudent(student);
    try {
      const response = await axios.get(`${API}/notifications/preferences/${student.id}`);
      setNotificationPrefs({
        email_enabled: response.data.email_enabled,
        sms_enabled: response.data.sms_enabled,
        reminder_hours: response.data.reminder_hours,
        email_address: response.data.email_address || student.email,
        phone_number: response.data.phone_number || student.phone
      });
    } catch (error) {
      // Use defaults if no preferences exist
      setNotificationPrefs({
        email_enabled: true,
        sms_enabled: false,
        reminder_hours: 24,
        email_address: student.email,
        phone_number: student.phone || ''
      });
    }
    setShowNotificationModal(true);
  };

  const handleSaveNotificationPrefs = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/notifications/preferences`, {
        student_id: selectedStudent.id,
        ...notificationPrefs
      });
      setShowNotificationModal(false);
      alert('Notification preferences updated successfully!');
    } catch (error) {
      console.error('Failed to update notification preferences:', error);
      alert('Failed to update notification preferences');
    }
  };

  const handleCreateEnrollment = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/enrollments`, {
        student_id: selectedStudent.id,
        program_name: enrollmentData.program_name,
        total_lessons: parseInt(enrollmentData.total_lessons),
        total_paid: parseFloat(enrollmentData.total_paid)
      });
      setShowEnrollModal(false);
      setEnrollmentData({
        program_name: '',
        total_lessons: '',
        total_paid: ''
      });
      onRefresh();
      alert('Enrollment created successfully!');
    } catch (error) {
      console.error('Failed to create enrollment:', error);
      alert('Failed to create enrollment');
    }
  };

  return (
    <div className="students-manager">
      <div className="manager-header">
        <h2>Students</h2>
        <Button onClick={() => setShowAddModal(true)}>Add Student</Button>
      </div>

      <div className="students-grid">
        {students.map(student => (
          <Card key={student.id} className="student-card">
            <div className="student-info">
              <h3>{student.name}</h3>
              <p>📧 {student.email}</p>
              {student.phone && <p>📱 {student.phone}</p>}
              {student.parent_name && (
                <p>👤 Parent: {student.parent_name}</p>
              )}
              {student.notes && <p>📝 {student.notes}</p>}
            </div>
            <div className="student-actions">
              <Button 
                variant="outline" 
                onClick={() => {
                  setSelectedStudent(student);
                  setShowLedger(true);
                }}
                className="ledger-btn"
              >
                📊 Ledger
              </Button>
              <Button 
                variant="outline" 
                onClick={() => handleEnroll(student)}
              >
                Enroll
              </Button>
              <Button 
                variant="outline" 
                onClick={() => handleNotificationPrefs(student)}
                className="notification-btn"
              >
                📱 Notifications
              </Button>
              <Button 
                variant="outline" 
                onClick={() => handleDeleteStudent(student.id, student.name)}
                className="delete-btn"
              >
                Delete
              </Button>
            </div>
          </Card>
        ))}
      </div>

      <Modal 
        isOpen={showAddModal} 
        onClose={() => setShowAddModal(false)}
        title="Add New Student"
      >
        <form onSubmit={handleAddStudent} className="student-form">
          <Input
            placeholder="Full Name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            required
          />
          <Input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            required
          />
          <Input
            placeholder="Phone Number"
            value={formData.phone}
            onChange={(e) => setFormData({...formData, phone: e.target.value})}
          />
          <Input
            placeholder="Parent/Guardian Name"
            value={formData.parent_name}
            onChange={(e) => setFormData({...formData, parent_name: e.target.value})}
          />
          <Input
            placeholder="Parent Phone"
            value={formData.parent_phone}
            onChange={(e) => setFormData({...formData, parent_phone: e.target.value})}
          />
          <Input
            type="email"
            placeholder="Parent Email"
            value={formData.parent_email}
            onChange={(e) => setFormData({...formData, parent_email: e.target.value})}
          />
          <textarea
            placeholder="Notes"
            value={formData.notes}
            onChange={(e) => setFormData({...formData, notes: e.target.value})}
            className="input"
            rows="3"
          />
          <Button type="submit">Add Student</Button>
        </form>
      </Modal>

      <Modal 
        isOpen={showEnrollModal} 
        onClose={() => setShowEnrollModal(false)}
        title={`Enroll ${selectedStudent?.name}`}
      >
        <form onSubmit={handleCreateEnrollment}>
          <div className="form-group">
            <label>Dance Program *</label>
            <select
              value={enrollmentData.program_name}
              onChange={(e) => {
                setEnrollmentData({
                  ...enrollmentData,
                  program_name: e.target.value
                });
              }}
              required
              className="input"
            >
              <option value="">Select Program</option>
              {programs.map(program => (
                <option key={program.id} value={program.name}>
                  {program.name} ({program.level})
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Number of Lessons *</label>
            <Input
              type="number"
              value={enrollmentData.total_lessons}
              onChange={(e) => setEnrollmentData({...enrollmentData, total_lessons: e.target.value})}
              placeholder="Enter number of lessons"
              required
              min="1"
              max="100"
              className="input"
            />
          </div>
          <div className="form-group">
            <label>Total Paid</label>
            <Input
              type="number"
              step="0.01"
              placeholder="Amount paid"
              value={enrollmentData.total_paid}
              onChange={(e) => setEnrollmentData({...enrollmentData, total_paid: e.target.value})}
              required
            />
          </div>
          <Button type="submit">Create Enrollment</Button>
        </form>
      </Modal>

      <Modal 
        isOpen={showNotificationModal} 
        onClose={() => setShowNotificationModal(false)}
        title={`Notification Preferences${selectedStudent ? ` - ${selectedStudent.name}` : ''}`}
      >
        <form onSubmit={handleSaveNotificationPrefs}>
          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={notificationPrefs.email_enabled}
                onChange={(e) => setNotificationPrefs({
                  ...notificationPrefs, 
                  email_enabled: e.target.checked
                })}
              />
              <span>📧 Enable Email Reminders</span>
            </label>
          </div>
          
          <div className="form-group">
            <label>Email Address</label>
            <Input
              type="email"
              value={notificationPrefs.email_address}
              onChange={(e) => setNotificationPrefs({
                ...notificationPrefs, 
                email_address: e.target.value
              })}
              placeholder="Email for reminders"
            />
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={notificationPrefs.sms_enabled}
                onChange={(e) => setNotificationPrefs({
                  ...notificationPrefs, 
                  sms_enabled: e.target.checked
                })}
              />
              <span>📱 Enable SMS Reminders</span>
            </label>
          </div>
          
          <div className="form-group">
            <label>Phone Number</label>
            <Input
              type="tel"
              value={notificationPrefs.phone_number}
              onChange={(e) => setNotificationPrefs({
                ...notificationPrefs, 
                phone_number: e.target.value
              })}
              placeholder="+1234567890"
            />
          </div>

          <div className="form-group">
            <label>Reminder Time</label>
            <select
              value={notificationPrefs.reminder_hours}
              onChange={(e) => setNotificationPrefs({
                ...notificationPrefs, 
                reminder_hours: parseInt(e.target.value)
              })}
              className="input"
            >
              <option value={1}>1 hour before</option>
              <option value={2}>2 hours before</option>
              <option value={4}>4 hours before</option>
              <option value={24}>24 hours before</option>
              <option value={48}>48 hours before</option>
            </select>
          </div>

          <Button type="submit">Save Preferences</Button>
        </form>
      </Modal>

      {/* Student Ledger */}
      {showLedger && selectedStudent && (
        <StudentLedger 
          student={selectedStudent}
          onClose={() => {
            setShowLedger(false);
            setSelectedStudent(null);
            fetchStudents(); // Refresh to show updated data
            onRefresh();
          }}
        />
      )}
    </div>
  );
};

// Teachers Manager Component  
const TeachersManager = ({ onRefresh }) => {
  const [teachers, setTeachers] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingTeacher, setEditingTeacher] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    specialties: [],
    bio: ''
  });

  const danceBtyles = ['ballet', 'hip_hop', 'jazz', 'contemporary', 'tap', 'salsa', 'ballroom'];

  useEffect(() => {
    fetchTeachers();
  }, [onRefresh]);

  const fetchTeachers = async () => {
    try {
      const response = await axios.get(`${API}/teachers`);
      setTeachers(response.data);
    } catch (error) {
      console.error('Failed to fetch teachers:', error);
    }
  };

  const handleAddTeacher = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/teachers`, formData);
      setShowAddModal(false);
      fetchTeachers();
      onRefresh();
      setFormData({
        name: '',
        email: '',
        phone: '',
        specialties: [],
        bio: ''
      });
    } catch (error) {
      console.error('Failed to add teacher:', error);
      alert('Failed to add teacher');
    }
  };

  const toggleSpecialty = (specialty) => {
    const newSpecialties = formData.specialties.includes(specialty)
      ? formData.specialties.filter(s => s !== specialty)
      : [...formData.specialties, specialty];
    setFormData({...formData, specialties: newSpecialties});
  };

  const handleEditTeacher = (teacher) => {
    setEditingTeacher(teacher);
    setFormData({
      name: teacher.name,
      email: teacher.email,
      phone: teacher.phone,
      specialties: teacher.specialties || [],
      bio: teacher.bio || ''
    });
    setShowEditModal(true);
  };

  const handleUpdateTeacher = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/teachers/${editingTeacher.id}`, formData);
      setShowEditModal(false);
      setFormData({
        name: '',
        email: '',
        phone: '',
        specialties: [],
        bio: ''
      });
      setEditingTeacher(null);
      fetchTeachers();
      onRefresh();
      alert('Teacher updated successfully!');
    } catch (error) {
      console.error('Failed to update teacher:', error);
      alert('Failed to update teacher');
    }
  };

  const handleDeleteTeacher = async (teacherId, teacherName) => {
    if (window.confirm(`Are you sure you want to delete ${teacherName}? This action cannot be undone.`)) {
      try {
        const response = await axios.delete(`${API}/teachers/${teacherId}`);
        alert(response.data.message);
        fetchTeachers();
        onRefresh();
      } catch (error) {
        console.error('Failed to delete teacher:', error);
        alert('Failed to delete teacher');
      }
    }
  };

  return (
    <div className="teachers-manager">
      <div className="manager-header">
        <h2>Teachers</h2>
        <Button onClick={() => setShowAddModal(true)}>Add Teacher</Button>
      </div>

      <div className="teachers-grid">
        {teachers.map(teacher => (
          <Card key={teacher.id} className="teacher-card">
            <div className="teacher-info">
              <h3>{teacher.name}</h3>
              <p>📧 {teacher.email}</p>
              {teacher.phone && <p>📱 {teacher.phone}</p>}
              <div className="specialties">
                {teacher.specialties.map(specialty => (
                  <span key={specialty} className="specialty-badge">
                    {specialty.replace('_', ' ')}
                  </span>
                ))}
              </div>
              {teacher.bio && <p className="teacher-bio">{teacher.bio}</p>}
            </div>
            <div className="teacher-actions">
              <Button 
                variant="outline" 
                onClick={() => handleEditTeacher(teacher)}
                className="edit-btn"
              >
                ✏️ Edit
              </Button>
              <Button 
                variant="outline" 
                onClick={() => handleDeleteTeacher(teacher.id, teacher.name)}
                className="delete-btn"
              >
                🗑️ Delete
              </Button>
            </div>
          </Card>
        ))}
      </div>

      <Modal 
        isOpen={showAddModal} 
        onClose={() => setShowAddModal(false)}
        title="Add New Teacher"
      >
        <form onSubmit={handleAddTeacher} className="teacher-form">
          <Input
            placeholder="Full Name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            required
          />
          <Input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            required
          />
          <Input
            placeholder="Phone Number"
            value={formData.phone}
            onChange={(e) => setFormData({...formData, phone: e.target.value})}
          />
          <div className="form-group">
            <label>Specialties</label>
            <div className="specialties-selector">
              {danceBtyles.map(specialty => (
                <label key={specialty} className="specialty-option">
                  <input
                    type="checkbox"
                    checked={formData.specialties.includes(specialty)}
                    onChange={() => toggleSpecialty(specialty)}
                  />
                  <span>{specialty.replace('_', ' ')}</span>
                </label>
              ))}
            </div>
          </div>
          <textarea
            placeholder="Bio (optional)"
            value={formData.bio}
            onChange={(e) => setFormData({...formData, bio: e.target.value})}
            className="input"
            rows="3"
          />
          <Button type="submit">Add Teacher</Button>
        </form>
      </Modal>

      {/* Edit Teacher Modal */}
      <Modal 
        isOpen={showEditModal} 
        onClose={() => {
          setShowEditModal(false);
          setEditingTeacher(null);
          setFormData({
            name: '',
            email: '',
            phone: '',
            specialties: [],
            bio: ''
          });
        }}
        title="Edit Teacher"
      >
        <form onSubmit={handleUpdateTeacher} className="teacher-form">
          <Input
            placeholder="Full Name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            required
            className="input"
          />
          <Input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            required
            className="input"
          />
          <Input
            type="tel"
            placeholder="Phone"
            value={formData.phone}
            onChange={(e) => setFormData({...formData, phone: e.target.value})}
            className="input"
          />
          
          <div className="specialties-section">
            <h4>Dance Specialties</h4>
            <div className="specialties-grid">
              {danceBtyles.map(style => (
                <label key={style} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.specialties.includes(style)}
                    onChange={() => toggleSpecialty(style)}
                  />
                  <span>{style.replace('_', ' ')}</span>
                </label>
              ))}
            </div>
          </div>

          <textarea
            placeholder="Bio (optional)"
            value={formData.bio}
            onChange={(e) => setFormData({...formData, bio: e.target.value})}
            className="input"
            rows="3"
          />
          <Button type="submit">Update Teacher</Button>
        </form>
      </Modal>
    </div>
  );
};

// Weekly Calendar Component
const WeeklyCalendar = ({ selectedDate, onRefresh }) => {
  const [lessons, setLessons] = useState([]);
  const [currentDate, setCurrentDate] = useState(selectedDate);
  
  useEffect(() => {
    setCurrentDate(selectedDate);
  }, [selectedDate]);

  useEffect(() => {
    fetchWeeklyLessons();
  }, [currentDate, onRefresh]);

  const fetchWeeklyLessons = async () => {
    try {
      const startDate = getWeekStart(currentDate);
      const response = await axios.get(`${API}/lessons`);
      
      // Filter lessons for the current week
      const weekLessons = response.data.filter(lesson => {
        const lessonDate = new Date(lesson.start_datetime);
        const weekStart = getWeekStart(currentDate);
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);
        return lessonDate >= weekStart && lessonDate <= weekEnd;
      });
      
      setLessons(weekLessons);
    } catch (error) {
      console.error('Failed to fetch weekly lessons:', error);
    }
  };

  const navigateWeek = (direction) => {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + (direction * 7)); // Move by weeks
    setCurrentDate(newDate);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const handleDeleteLesson = async (lessonId) => {
    if (window.confirm('Are you sure you want to delete this lesson?')) {
      try {
        console.log('Attempting to delete lesson:', lessonId);
        console.log('API URL:', `${API}/lessons/${lessonId}`);
        
        const response = await axios.delete(`${API}/lessons/${lessonId}`);
        console.log('Delete response:', response);
        
        fetchWeeklyLessons(); // Refresh weekly view
        onRefresh(); // Refresh parent component and daily calendar stats
        alert('Lesson deleted successfully!');
      } catch (error) {
        console.error('Failed to delete lesson:', error);
        console.error('Error response:', error.response);
        
        // More detailed error message
        let errorMessage = 'Failed to delete lesson';
        if (error.response) {
          if (error.response.status === 401) {
            errorMessage = 'Authentication failed. Please log in again.';
          } else if (error.response.status === 403) {
            errorMessage = 'You do not have permission to delete this lesson.';
          } else if (error.response.status === 404) {
            errorMessage = 'Lesson not found or already deleted.';
          } else if (error.response.data && error.response.data.detail) {
            errorMessage = error.response.data.detail;
          }
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        alert(errorMessage);
      }
    }
  };

  const getWeekStart = (date) => {
    const start = new Date(date);
    const day = start.getDay();
    const diff = start.getDate() - day + (day === 0 ? -6 : 1); // Monday as start of week
    start.setDate(diff);
    start.setHours(0, 0, 0, 0);
    return start;
  };

  const getWeekDays = (startDate) => {
    const days = [];
    for (let i = 0; i < 7; i++) {
      const day = new Date(startDate);
      day.setDate(startDate.getDate() + i);
      days.push(day);
    }
    return days;
  };

  const getLessonsForDay = (day) => {
    return lessons.filter(lesson => {
      const lessonDate = new Date(lesson.start_datetime);
      return lessonDate.toDateString() === day.toDateString();
    });
  };

  const weekStart = getWeekStart(currentDate);
  const weekDays = getWeekDays(weekStart);

  return (
    <div className="weekly-calendar">
      <div className="calendar-header">
        <div className="calendar-title">
          <h2>Weekly Schedule</h2>
          <p>{weekStart.toDateString()} - {weekDays[6].toDateString()}</p>
          <div className="calendar-navigation">
            <button 
              className="btn btn-outline nav-btn"
              onClick={() => navigateWeek(-1)}
              title="Previous week"
            >
              ← Previous Week
            </button>
            <button 
              className="btn btn-outline nav-btn"
              onClick={goToToday}
              title="Go to current week"
            >
              This Week
            </button>
            <button 
              className="btn btn-outline nav-btn"
              onClick={() => navigateWeek(1)}
              title="Next week"
            >
              Next Week →
            </button>
          </div>
        </div>
      </div>
      
      <div className="week-grid">
        {weekDays.map(day => {
          const dayLessons = getLessonsForDay(day);
          return (
            <div key={day.toDateString()} className="day-column">
              <div className="day-header">
                <div className="day-name">{day.toLocaleDateString('en-US', { weekday: 'short' })}</div>
                <div className="day-number">{day.getDate()}</div>
              </div>
              <div className="day-lessons">
                {dayLessons.map(lesson => (
                  <div key={lesson.id} className={`week-lesson ${lesson.is_attended ? 'attended' : ''}`}>
                    <div className="lesson-info">
                      <div className="lesson-time">
                        {new Date(lesson.start_datetime).toLocaleTimeString('en-US', { 
                          hour: 'numeric', 
                          minute: '2-digit' 
                        })}
                      </div>
                      <div className="lesson-student">{lesson.student_name}</div>
                      <div className="lesson-teacher">{lesson.teacher_name}</div>
                    </div>
                    <button 
                      onClick={() => handleDeleteLesson(lesson.id)} 
                      className="weekly-delete-btn" 
                      title="Delete this lesson"
                    >
                      DELETE
                    </button>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Main App Component
const MainApp = () => {
  const { user, logout } = useAuth();
  const [currentView, setCurrentView] = useState('dashboard');
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [refreshKey, setRefreshKey] = useState(0);
  const [notifications, setNotifications] = useState([]);

  // WebSocket connection and real-time updates
  useEffect(() => {
    if (user && user.id) {
      console.log('🔄 Initializing real-time updates for user:', user.id);
      
      // Try to connect to WebSocket with fallback
      try {
        wsManager.connect(user.id);

        // Add connection status listener
        wsManager.on('connection', (status) => {
          console.log('📡 WebSocket connection status:', status);
          if (status.status === 'connected') {
            showToast('🔗 Real-time updates connected', 'connection');
          } else if (status.status === 'failed' || status.status === 'error') {
            console.warn('⚠️ WebSocket failed, using polling fallback');
            // Set up polling fallback for updates
            setupPollingFallback();
          }
        });

        // Add global listener for all real-time updates
        wsManager.on('*', handleRealTimeUpdate);

        // Set timeout for connection attempt
        const connectionTimeout = setTimeout(() => {
          if (!wsManager.getStatus().connected) {
            console.warn('⚠️ WebSocket connection timeout, using polling fallback');
            setupPollingFallback();
          }
        }, 5000);

        // Cleanup on component unmount
        return () => {
          clearTimeout(connectionTimeout);
          wsManager.disconnect();
        };
      } catch (error) {
        console.error('❌ WebSocket initialization failed:', error);
        setupPollingFallback();
      }
    }
  }, [user]);

  const setupPollingFallback = () => {
    console.log('🔄 Setting up polling fallback for real-time updates');
    // Set up periodic refresh as fallback
    const interval = setInterval(() => {
      setRefreshKey(prev => prev + 1);
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  };

  const handleRealTimeUpdate = (message) => {
    console.log('Real-time update received:', message);
    
    // Add notification
    const notification = {
      id: Date.now(),
      type: message.type,
      message: formatNotificationMessage(message),
      timestamp: new Date(message.timestamp),
      user_name: message.user_name
    };
    
    setNotifications(prev => [notification, ...prev.slice(0, 9)]); // Keep last 10 notifications
    
    // Auto refresh data on relevant updates
    if (['lesson_updated', 'lesson_deleted', 'lesson_attended', 'student_created', 'student_updated', 'student_deleted', 'teacher_created', 'teacher_deleted', 'recurring_series_created'].includes(message.type)) {
      setRefreshKey(prev => prev + 1);
    }

    // Show temporary toast notification
    showToast(notification.message, message.type);
  };

  const formatNotificationMessage = (message) => {
    switch (message.type) {
      case 'lesson_updated':
        return `${message.user_name} updated a lesson for ${message.data.student_name}`;
      case 'lesson_deleted':
        return `${message.user_name} deleted a lesson`;
      case 'lesson_attended':
        return `${message.user_name} marked attendance for ${message.data.student_name}`;
      case 'student_created':
        return `${message.user_name} added new student: ${message.data.student.name}`;
      case 'student_updated':
        return `${message.user_name} updated student: ${message.data.student.name}`;
      case 'student_deleted':
        return `${message.user_name} deleted student: ${message.data.student_name}`;
      case 'teacher_created':
        return `${message.user_name} added new teacher: ${message.data.teacher.name}`;
      case 'teacher_deleted':
        return `${message.user_name} deleted teacher: ${message.data.teacher_name}`;
      case 'recurring_series_created':
        return `${message.user_name} created ${message.data.lessons_count} recurring lessons for ${message.data.student_name}`;
      case 'recurring_series_cancelled':
        return `${message.user_name} cancelled recurring series (${message.data.cancelled_lessons_count} lessons)`;
      default:
        return `${message.user_name} made changes to the system`;
    }
  };

  const showToast = (message, type) => {
    // Create temporary toast element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: linear-gradient(45deg, #6366f1, #8b5cf6);
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      z-index: 10000;
      font-size: 14px;
      max-width: 300px;
      word-wrap: break-word;
      opacity: 0;
      transform: translateX(100%);
      transition: all 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 4 seconds
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (document.body.contains(toast)) {
          document.body.removeChild(toast);
        }
      }, 300);
    }, 4000);
  };

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  const handleNavigation = (view) => {
    // Map dashboard navigation to actual view names
    const viewMap = {
      'students': 'students',
      'teachers': 'teachers',
      'daily-calendar': 'daily'
    };
    
    const targetView = viewMap[view] || view;
    setCurrentView(targetView);
  };

  // Add null check for user
  if (!user) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="main-app">
      {/* Sidebar Navigation */}
      <nav className="sidebar">
        <div className="sidebar-header">
          <h1>CRM.Dance</h1>
          <p>{user.name || 'User'}</p>
          <p className="user-role">{user.role || 'user'}</p>
        </div>
        
        <div className="nav-menu">
          <button 
            className={currentView === 'dashboard' ? 'nav-item active' : 'nav-item'}
            onClick={() => setCurrentView('dashboard')}
          >
            📊 Dashboard
          </button>
          <button 
            className={currentView === 'daily' ? 'nav-item active' : 'nav-item'}
            onClick={() => setCurrentView('daily')}
          >
            📅 Daily Calendar
          </button>
          <button 
            className={currentView === 'weekly' ? 'nav-item active' : 'nav-item'}
            onClick={() => setCurrentView('weekly')}
          >
            🗓️ Weekly Calendar  
          </button>
          <button 
            className={currentView === 'students' ? 'nav-item active' : 'nav-item'}
            onClick={() => setCurrentView('students')}
          >
            👥 Students
          </button>
          <button 
            className={currentView === 'teachers' ? 'nav-item active' : 'nav-item'}
            onClick={() => setCurrentView('teachers')}
          >
            🎭 Teachers
          </button>
        </div>
        
        <div className="sidebar-footer">
          <input
            type="date"
            value={selectedDate.toISOString().split('T')[0]}
            onChange={(e) => setSelectedDate(new Date(e.target.value))}
            className="date-picker"
          />
          <Button variant="outline" onClick={logout}>
            Sign Out
          </Button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        {currentView === 'dashboard' && (
          <Dashboard 
            onRefresh={refreshKey}
            onNavigate={handleNavigation}
          />
        )}
        {currentView === 'daily' && (
          <DailyCalendar 
            selectedDate={selectedDate}
            onRefresh={handleRefresh}
          />
        )}
        {currentView === 'weekly' && (
          <WeeklyCalendar 
            selectedDate={selectedDate} 
            onRefresh={refreshKey}
          />
        )}
        {currentView === 'students' && (
          <StudentsManager onRefresh={handleRefresh} />
        )}
        {currentView === 'teachers' && (
          <TeachersManager onRefresh={handleRefresh} />
        )}
      </main>
    </div>
  );
};

// Main App Wrapper
function App() {
  return (
    <div className="App">
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </div>
  );
}

export default App;