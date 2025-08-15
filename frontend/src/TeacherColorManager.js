import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const TeacherColorManager = () => {
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchTeachers();
  }, []);

  const fetchTeachers = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/teachers`);
      
      // Get colors for each teacher
      const teachersWithColors = await Promise.all(
        response.data.map(async (teacher) => {
          try {
            const colorResponse = await axios.get(`${API}/teachers/${teacher.id}/color`);
            return { ...teacher, color: colorResponse.data.color };
          } catch (error) {
            return { ...teacher, color: '#3b82f6' }; // Default blue
          }
        })
      );
      
      setTeachers(teachersWithColors);
    } catch (error) {
      console.error('Failed to fetch teachers:', error);
      setMessage('Failed to load teachers');
    } finally {
      setLoading(false);
    }
  };

  const handleColorChange = async (teacherId, newColor) => {
    try {
      setSaving(true);
      await axios.put(`${API}/teachers/${teacherId}/color`, { color: newColor });
      
      // Update local state
      setTeachers(teachers.map(teacher => 
        teacher.id === teacherId ? { ...teacher, color: newColor } : teacher
      ));
      
      setMessage('Teacher color updated successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Failed to update teacher color:', error);
      setMessage('Failed to update teacher color: ' + (error.response?.data?.detail || error.message));
      setTimeout(() => setMessage(''), 5000);
    } finally {
      setSaving(false);
    }
  };

  const handleAutoAssignColors = async () => {
    try {
      setSaving(true);
      const response = await axios.post(`${API}/teachers/colors/auto-assign`);
      
      // Update local state with new assignments
      response.data.assignments.forEach(assignment => {
        setTeachers(prevTeachers => 
          prevTeachers.map(teacher => 
            teacher.id === assignment.teacher_id 
              ? { ...teacher, color: assignment.color }
              : teacher
          )
        );
      });
      
      setMessage('Auto-assigned unique colors to all teachers!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Failed to auto-assign colors:', error);
      setMessage('Failed to auto-assign colors: ' + (error.response?.data?.detail || error.message));
      setTimeout(() => setMessage(''), 5000);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading teachers...</div>;
  }

  return (
    <div className="teacher-color-manager">
      <div className="manager-header">
        <h3>👨‍🏫 Teacher Color Assignments</h3>
        <button
          onClick={handleAutoAssignColors}
          className="btn btn-outline btn-sm"
          disabled={saving}
        >
          🎨 Auto-Assign Colors
        </button>
      </div>

      {message && (
        <div className={`message ${message.includes('Failed') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}

      <div className="teacher-color-grid">
        {teachers.map(teacher => (
          <div key={teacher.id} className="teacher-color-item">
            <div className="teacher-info">
              <div 
                className="teacher-color-preview" 
                style={{ backgroundColor: teacher.color }}
              />
              <div className="teacher-details">
                <h4>{teacher.name}</h4>
                <p>{teacher.specialties?.join(', ') || 'No specialties'}</p>
              </div>
            </div>
            
            <div className="color-controls">
              <input
                type="color"
                value={teacher.color || '#3b82f6'}
                onChange={(e) => handleColorChange(teacher.id, e.target.value)}
                className="teacher-color-picker"
                disabled={saving}
              />
              <input
                type="text"
                value={teacher.color || '#3b82f6'}
                onChange={(e) => handleColorChange(teacher.id, e.target.value)}
                className="teacher-color-text"
                disabled={saving}
              />
            </div>
          </div>
        ))}
      </div>

      {teachers.length === 0 && (
        <div className="no-teachers">
          <p>No teachers found. Add teachers first to assign colors.</p>
        </div>
      )}
    </div>
  );
};

export default TeacherColorManager;