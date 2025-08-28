import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import SettingsPage from './SettingsPage';
import EnrollmentsPage from './EnrollmentsPage';
import StudentLedger from './StudentLedger';
import StudentLedgerPanel from './StudentLedgerPanel';
import CancelledLessonsReport from './CancelledLessonsReport';
import UserManagement from './UserManagement';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [activeView, setActiveView] = useState('dashboard');
  const [currentDate, setCurrentDate] = useState(new Date());
  const [students, setStudents] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedStudentLedger, setSelectedStudentLedger] = useState(null);
  const [notifications, setNotifications] = useState([]);

  // Authentication
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      const userData = localStorage.getItem('user');
      if (userData) {
        setUser(JSON.parse(userData));
      }
      fetchInitialData();
    } else {
      setLoading(false);
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

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
  };

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [studentsRes, teachersRes, lessonsRes] = await Promise.all([
        axios.get(`${API}/students`),
        axios.get(`${API}/teachers`),
        axios.get(`${API}/lessons`)
      ]);
      
      setStudents(studentsRes.data);
      setTeachers(teachersRes.data);
      setLessons(lessonsRes.data);
    } catch (error) {
      console.error('Failed to fetch initial data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchInitialData();
  };

  const handleOpenLedger = (studentId) => {
    setSelectedStudentLedger(studentId);
  };

  const handleCloseLedger = () => {
    setSelectedStudentLedger(null);
  };

  const handleNavigateToDate = (date) => {
    setCurrentDate(new Date(date));
    setActiveView('dashboard');
    handleCloseLedger();
  };

  // Login Form Component
  const LoginForm = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loginLoading, setLoginLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
      e.preventDefault();
      setLoginLoading(true);
      setError('');
      
      const success = await login(email, password);
      if (!success) {
        setError('Invalid credentials');
      }
      setLoginLoading(false);
    };

    return (
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <h1>🩰 Dance Studio CRM</h1>
            <p>Welcome back! Please sign in to continue.</p>
          </div>
          
          <form onSubmit={handleSubmit} className="login-form">
            {error && <div className="error-message">{error}</div>}
            
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                required
              />
            </div>
            
            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
              />
            </div>
            
            <button type="submit" disabled={loginLoading} className="login-button">
              {loginLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
          
          <div className="login-footer">
            <p>Demo credentials: admin@test.com / admin123</p>
          </div>
        </div>
      </div>
    );
  };

  // Navigation Sidebar
  const Sidebar = () => (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>🩰 Dance CRM</h2>
        <div className="user-info">
          <span>{user?.name}</span>
          <button onClick={logout} className="logout-btn">Logout</button>
        </div>
      </div>
      
      <nav className="sidebar-nav">
        <button 
          className={activeView === 'dashboard' ? 'nav-item active' : 'nav-item'}
          onClick={() => setActiveView('dashboard')}
        >
          📅 Daily Calendar
        </button>
        <button 
          className={activeView === 'students' ? 'nav-item active' : 'nav-item'}
          onClick={() => setActiveView('students')}
        >
          👥 Students
        </button>
        <button 
          className={activeView === 'enrollments' ? 'nav-item active' : 'nav-item'}
          onClick={() => setActiveView('enrollments')}
        >
          📚 Enrollments
        </button>
        <button 
          className={activeView === 'reports' ? 'nav-item active' : 'nav-item'}
          onClick={() => setActiveView('reports')}
        >
          📊 Reports
        </button>
        <button 
          className={activeView === 'users' ? 'nav-item active' : 'nav-item'}
          onClick={() => setActiveView('users')}
        >
          👤 Users
        </button>
        <button 
          className={activeView === 'settings' ? 'nav-item active' : 'nav-item'}
          onClick={() => setActiveView('settings')}
        >
          ⚙️ Settings
        </button>
      </nav>
    </div>
  );

  // Main Content Area
  const MainContent = () => {
    if (loading) {
      return <div className="loading">Loading...</div>;
    }

    switch (activeView) {
      case 'dashboard':
        return (
          <div className="dashboard">
            <h1>Daily Calendar</h1>
            <p>Dashboard functionality will be implemented here.</p>
            <div className="stats-grid">
              <div className="stat-card">
                <h3>Total Students</h3>
                <p>{students.length}</p>
              </div>
              <div className="stat-card">
                <h3>Total Teachers</h3>
                <p>{teachers.length}</p>
              </div>
              <div className="stat-card">
                <h3>Today's Lessons</h3>
                <p>{lessons.filter(l => l.date === currentDate.toISOString().split('T')[0]).length}</p>
              </div>
            </div>
          </div>
        );
      case 'students':
        return (
          <div className="students-view">
            <h1>Students Management</h1>
            <div className="students-grid">
              {students.map(student => (
                <div key={student.id} className="student-card">
                  <h3>{student.name}</h3>
                  <p>{student.email}</p>
                  <button onClick={() => handleOpenLedger(student.id)}>
                    View Ledger
                  </button>
                </div>
              ))}
            </div>
          </div>
        );
      case 'enrollments':
        return <EnrollmentsPage onRefresh={handleRefresh} />;
      case 'reports':
        return <CancelledLessonsReport />;
      case 'users':
        return <UserManagement />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <div>View not found</div>;
    }
  };

  // Don't render anything if not authenticated
  if (!token) {
    return <LoginForm />;
  }

  return (
    <div className="app">
      <Sidebar />
      <main className="main-content">
        <MainContent />
      </main>
      
      {/* Student Ledger Panel */}
      {selectedStudentLedger && (
        <StudentLedgerPanel
          studentId={selectedStudentLedger}
          onClose={handleCloseLedger}
          onNavigateToDate={handleNavigateToDate}
          onRefresh={handleRefresh}
        />
      )}
      
      {/* Notifications */}
      {notifications.length > 0 && (
        <div className="notifications">
          {notifications.map(notification => (
            <div key={notification.id} className={`notification ${notification.type}`}>
              {notification.message}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;