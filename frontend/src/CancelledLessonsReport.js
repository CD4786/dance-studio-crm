import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const CancelledLessonsReport = () => {
  const [cancelledLessons, setCancelledLessons] = useState([]);
  const [students, setStudents] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    student_id: '',
    teacher_id: ''
  });
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    fetchCancelledLessons();
    fetchStudents();
    fetchTeachers();
  }, []);

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      fetchCancelledLessons();
    }, 500);

    return () => clearTimeout(debounceTimer);
  }, [filters]);

  const fetchCancelledLessons = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          params.append(key, value);
        }
      });

      const response = await axios.get(`${API}/reports/cancelled-lessons?${params}`);
      setCancelledLessons(response.data.cancelled_lessons);
      setTotalCount(response.data.total_count);
    } catch (error) {
      console.error('Failed to fetch cancelled lessons:', error);
    } finally {
      setLoading(false);
    }
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

  const handleReactivateLesson = async (lessonId) => {
    if (!window.confirm("Are you sure you want to reactivate this cancelled lesson?")) {
      return;
    }

    try {
      await axios.put(`${API}/lessons/${lessonId}/reactivate`);
      fetchCancelledLessons(); // Refresh the list
    } catch (error) {
      console.error('Failed to reactivate lesson:', error);
      alert('Failed to reactivate lesson: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteLesson = async (lessonId) => {
    if (!window.confirm("Are you sure you want to permanently delete this cancelled lesson? This action cannot be undone.")) {
      return;
    }

    try {
      await axios.delete(`${API}/lessons/${lessonId}`);
      fetchCancelledLessons(); // Refresh the list
    } catch (error) {
      console.error('Failed to delete lesson:', error);
      alert('Failed to delete lesson: ' + (error.response?.data?.detail || error.message));
    }
  };

  const clearFilters = () => {
    setFilters({
      start_date: '',
      end_date: '',
      student_id: '',
      teacher_id: ''
    });
  };

  const exportToCsv = () => {
    const csvContent = [
      ['Student', 'Teacher(s)', 'Original Date/Time', 'Booking Type', 'Cancellation Date', 'Cancelled By', 'Reason'],
      ...cancelledLessons.map(lesson => [
        lesson.student_name,
        lesson.teacher_names?.join(', ') || 'Unknown',
        new Date(lesson.start_datetime).toLocaleString(),
        lesson.booking_type?.replace('_', ' ') || 'Private Lesson',
        lesson.cancelled_at ? new Date(lesson.cancelled_at).toLocaleString() : 'Unknown',
        lesson.cancelled_by || 'Unknown',
        lesson.cancellation_reason || 'No reason provided'
      ])
    ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cancelled-lessons-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (loading && cancelledLessons.length === 0) {
    return <div className="loading">Loading cancelled lessons report...</div>;
  }

  return (
    <div className="cancelled-lessons-report">
      <div className="report-header">
        <h2>📊 Cancelled Lessons Report</h2>
        <p>View and manage all cancelled lessons</p>
      </div>

      {/* Filters Section */}
      <div className="report-filters">
        <h3>🔍 Filters</h3>
        <div className="filters-grid">
          <div className="filter-group">
            <label>Start Date:</label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => setFilters({...filters, start_date: e.target.value})}
              className="input"
            />
          </div>
          
          <div className="filter-group">
            <label>End Date:</label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => setFilters({...filters, end_date: e.target.value})}
              className="input"
            />
          </div>
          
          <div className="filter-group">
            <label>Student:</label>
            <select
              value={filters.student_id}
              onChange={(e) => setFilters({...filters, student_id: e.target.value})}
              className="input"
            >
              <option value="">All Students</option>
              {students.map(student => (
                <option key={student.id} value={student.id}>
                  {student.name}
                </option>
              ))}
            </select>
          </div>
          
          <div className="filter-group">
            <label>Teacher:</label>
            <select
              value={filters.teacher_id}
              onChange={(e) => setFilters({...filters, teacher_id: e.target.value})}
              className="input"
            >
              <option value="">All Teachers</option>
              {teachers.map(teacher => (
                <option key={teacher.id} value={teacher.id}>
                  {teacher.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="filter-actions">
          <button onClick={clearFilters} className="btn btn-outline">
            🗑️ Clear Filters
          </button>
          <button onClick={exportToCsv} className="btn btn-primary" disabled={cancelledLessons.length === 0}>
            📥 Export CSV
          </button>
        </div>
      </div>

      {/* Results Summary */}
      <div className="report-summary">
        <div className="summary-card">
          <h3>📈 Summary</h3>
          <div className="summary-stats">
            <div className="stat">
              <span className="stat-number">{totalCount}</span>
              <span className="stat-label">Total Cancelled Lessons</span>
            </div>
            <div className="stat">
              <span className="stat-number">
                {cancelledLessons.filter(l => l.cancelled_at && new Date(l.cancelled_at) >= new Date(Date.now() - 30*24*60*60*1000)).length}
              </span>
              <span className="stat-label">Cancelled This Month</span>
            </div>
          </div>
        </div>
      </div>

      {/* Cancelled Lessons List */}
      <div className="report-content">
        {loading && (
          <div className="loading-overlay">Loading...</div>
        )}
        
        {cancelledLessons.length === 0 ? (
          <div className="empty-state">
            <h3>📭 No Cancelled Lessons Found</h3>
            <p>No lessons match your current filter criteria.</p>
          </div>
        ) : (
          <div className="lessons-table">
            <div className="table-header">
              <span>Student</span>
              <span>Teacher(s)</span>
              <span>Original Date/Time</span>
              <span>Type</span>
              <span>Cancelled</span>
              <span>Reason</span>
              <span>Actions</span>
            </div>
            
            {cancelledLessons.map(lesson => (
              <div key={lesson.id} className="table-row">
                <div className="cell student-cell">
                  <strong>{lesson.student_name}</strong>
                </div>
                
                <div className="cell teachers-cell">
                  {lesson.teacher_names?.join(', ') || 'Unknown'}
                </div>
                
                <div className="cell datetime-cell">
                  <div className="datetime">
                    <div className="date">{new Date(lesson.start_datetime).toLocaleDateString()}</div>
                    <div className="time">{new Date(lesson.start_datetime).toLocaleTimeString('en-US', { 
                      hour: 'numeric', 
                      minute: '2-digit' 
                    })}</div>
                  </div>
                </div>
                
                <div className="cell type-cell">
                  <span className="booking-type">
                    {lesson.booking_type?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Private Lesson'}
                  </span>
                </div>
                
                <div className="cell cancelled-cell">
                  <div className="cancellation-info">
                    <div className="cancelled-date">
                      {lesson.cancelled_at ? new Date(lesson.cancelled_at).toLocaleDateString() : 'Unknown'}
                    </div>
                    <div className="cancelled-by">
                      By: {lesson.cancelled_by || 'Unknown'}
                    </div>
                  </div>
                </div>
                
                <div className="cell reason-cell">
                  <div className="reason">
                    {lesson.cancellation_reason || 'No reason provided'}
                  </div>
                </div>
                
                <div className="cell actions-cell">
                  <button 
                    onClick={() => handleReactivateLesson(lesson.id)}
                    className="btn btn-outline btn-sm"
                    title="Reactivate lesson"
                  >
                    🔄 Reactivate
                  </button>
                  <button 
                    onClick={() => handleDeleteLesson(lesson.id)}
                    className="btn btn-danger btn-sm"
                    title="Delete permanently"
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CancelledLessonsReport;