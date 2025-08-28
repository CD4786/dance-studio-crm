import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const EnrollmentsPage = ({ onRefresh }) => {
  const [enrollments, setEnrollments] = useState([]);
  const [students, setStudents] = useState([]);
  const [programs, setPrograms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedEnrollment, setSelectedEnrollment] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterBy, setFilterBy] = useState('all');
  const [sortBy, setSortBy] = useState('created_date');
  const [formData, setFormData] = useState({
    student_id: '',
    program_name: '',
    total_lessons: '',
    price_per_lesson: '50.00',
    initial_payment: '0.00',
    total_paid: '0.00'
  });

  useEffect(() => {
    fetchEnrollments();
    fetchStudents();
    fetchPrograms();
  }, []); // Remove onRefresh from dependency to prevent infinite loops

  const fetchEnrollments = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/enrollments`);
      setEnrollments(response.data);
    } catch (error) {
      console.error('Failed to fetch enrollments:', error);
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

  const fetchPrograms = async () => {
    try {
      const response = await axios.get(`${API}/programs`);
      setPrograms(response.data);
    } catch (error) {
      console.error('Failed to fetch programs:', error);
    }
  };

  // Helper function to get student name
  const getStudentName = (studentId) => {
    const student = students.find(s => s.id === studentId);
    return student ? student.name : 'Unknown Student';
  };

  // Helper function to calculate enrollment totals
  const calculateEnrollmentTotals = (enrollment) => {
    const grandTotal = (enrollment.total_lessons || 0) * (enrollment.price_per_lesson || 50);
    const amountPaid = enrollment.amount_paid || 0;
    const balanceRemaining = grandTotal - amountPaid;
    
    return {
      grandTotal,
      amountPaid,
      balanceRemaining
    };
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  const handleAddEnrollment = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/enrollments`, {
        student_id: formData.student_id,
        program_name: formData.program_name,
        total_lessons: parseInt(formData.total_lessons),
        price_per_lesson: parseFloat(formData.price_per_lesson),
        initial_payment: parseFloat(formData.initial_payment),
        total_paid: parseFloat(formData.total_paid)
      });
      
      setShowAddModal(false);
      setFormData({
        student_id: '',
        program_name: '',
        total_lessons: '',
        price_per_lesson: '50.00',
        initial_payment: '0.00',
        total_paid: '0.00'
      });
      fetchEnrollments();
      onRefresh && onRefresh(); // Trigger refresh in parent components
    } catch (error) {
      console.error('Failed to create enrollment:', error);
      alert('Failed to create enrollment: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEditEnrollment = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/enrollments/${selectedEnrollment.id}`, {
        student_id: formData.student_id,
        program_name: formData.program_name,
        total_lessons: parseInt(formData.total_lessons),
        price_per_lesson: parseFloat(formData.price_per_lesson),
        initial_payment: parseFloat(formData.initial_payment),
        total_paid: parseFloat(formData.total_paid)
      });
      
      setShowEditModal(false);
      setSelectedEnrollment(null);
      setFormData({
        student_id: '',
        program_name: '',
        total_lessons: '',
        price_per_lesson: '50.00',
        initial_payment: '0.00',
        total_paid: '0.00'
      });
      fetchEnrollments();
      onRefresh && onRefresh(); // Trigger refresh in parent components
    } catch (error) {
      console.error('Failed to update enrollment:', error);
      alert('Failed to update enrollment');
    }
  };

  const handleDeleteEnrollment = async (enrollmentId) => {
    if (!window.confirm('Are you sure you want to delete this enrollment?')) {
      return;
    }

    try {
      await axios.delete(`${API}/enrollments/${enrollmentId}`);
      fetchEnrollments();
    } catch (error) {
      console.error('Failed to delete enrollment:', error);
      alert('Failed to delete enrollment');
    }
  };

  const openEditModal = (enrollment) => {
    setSelectedEnrollment(enrollment);
    setFormData({
      student_id: enrollment.student_id,
      program_name: enrollment.program_name,
      total_lessons: enrollment.total_lessons.toString(),
      price_per_lesson: (enrollment.price_per_lesson || 50).toString(),
      initial_payment: (enrollment.amount_paid || 0).toString(),
      total_paid: enrollment.total_paid.toString()
    });
    setShowEditModal(true);
  };

  // Filter and search logic
  const filteredAndSortedEnrollments = useMemo(() => {
    let filtered = enrollments.filter(enrollment => {
      const matchesSearch = searchTerm === '' || 
        enrollment.student_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        enrollment.program_name?.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesFilter = filterBy === 'all' || 
        (filterBy === 'active' && enrollment.remaining_lessons > 0) ||
        (filterBy === 'completed' && enrollment.remaining_lessons === 0) ||
        (filterBy === 'low_lessons' && enrollment.remaining_lessons <= 3 && enrollment.remaining_lessons > 0);

      return matchesSearch && matchesFilter;
    });

    // Sort the filtered results
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'student_name':
          return (a.student_name || '').localeCompare(b.student_name || '');
        case 'program_name':
          return (a.program_name || '').localeCompare(b.program_name || '');
        case 'remaining_lessons':
          return b.remaining_lessons - a.remaining_lessons;
        case 'total_paid':
          return b.total_paid - a.total_paid;
        case 'created_date':
        default:
          return new Date(b.created_at || 0) - new Date(a.created_at || 0);
      }
    });

    return filtered;
  }, [enrollments, searchTerm, filterBy, sortBy]);

  if (loading) {
    return <div className="loading">Loading enrollments...</div>;
  }

  return (
    <div className="enrollments-page">
      <div className="manager-header">
        <h2>Enrollments Management</h2>
        <button 
          onClick={() => setShowAddModal(true)}
          className="btn btn-primary"
        >
          Add Enrollment
        </button>
      </div>

      {/* Search and Filter Controls */}
      <div className="search-filter-controls">
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search enrollments by student name or program..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
        
        <div className="filter-controls">
          <select 
            value={filterBy} 
            onChange={(e) => setFilterBy(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Enrollments</option>
            <option value="active">Active (Has Lessons)</option>
            <option value="completed">Completed</option>
            <option value="low_lessons">Low Lessons (≤3)</option>
          </select>
          
          <select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value)}
            className="sort-select"
          >
            <option value="created_date">Sort by Date Added</option>
            <option value="student_name">Sort by Student</option>
            <option value="program_name">Sort by Program</option>
            <option value="remaining_lessons">Sort by Remaining</option>
            <option value="total_paid">Sort by Amount Paid</option>
          </select>
        </div>
      </div>

      {/* Results count */}
      <div className="results-info">
        <span className="results-count">
          Showing {filteredAndSortedEnrollments.length} of {enrollments.length} enrollments
        </span>
      </div>

      {/* Enrollments Grid */}
      <div className="enrollments-grid">
        {filteredAndSortedEnrollments.map(enrollment => {
          const totals = calculateEnrollmentTotals(enrollment);
          
          return (
            <div key={enrollment.id} className="enrollment-card">
              <div className="enrollment-info">
                <h3 className="student-name">{getStudentName(enrollment.student_id)}</h3>
                <p><strong>Program:</strong> {enrollment.program_name}</p>
                
                <div className="enrollment-lessons">
                  <p><strong>Total Lessons:</strong> {enrollment.total_lessons}</p>
                  <p><strong>Remaining:</strong> {enrollment.remaining_lessons}</p>
                  <p><strong>Used:</strong> {enrollment.total_lessons - enrollment.remaining_lessons}</p>
                </div>
                
                <div className="enrollment-financial">
                  <p><strong>Price Per Lesson:</strong> {formatCurrency(enrollment.price_per_lesson || 50)}</p>
                  <p><strong>Grand Total:</strong> {formatCurrency(totals.grandTotal)}</p>
                  <p><strong>Amount Paid:</strong> {formatCurrency(totals.amountPaid)}</p>
                  <p className={`balance-remaining ${totals.balanceRemaining > 0 ? 'negative' : 'positive'}`}>
                    <strong>Balance:</strong> {formatCurrency(totals.balanceRemaining)}
                  </p>
                </div>
                
                <p className="enrollment-status">
                  <span className={`status-badge ${enrollment.remaining_lessons > 0 ? 'active' : 'completed'}`}>
                    {enrollment.remaining_lessons > 0 ? 'Active' : 'Completed'}
                  </span>
                  {enrollment.remaining_lessons <= 3 && enrollment.remaining_lessons > 0 && (
                    <span className="status-badge warning">Low Lessons</span>
                  )}
                  {totals.balanceRemaining > 0 && (
                    <span className="status-badge balance-due">Balance Due</span>
                  )}
                </p>
              </div>
              
              <div className="enrollment-actions">
                <button 
                  onClick={() => openEditModal(enrollment)}
                  className="btn btn-outline btn-sm"
                >
                  Edit
                </button>
                <button 
                  onClick={() => handleDeleteEnrollment(enrollment.id)}
                  className="btn btn-danger btn-sm"
                >
                  Delete
                </button>
                {totals.balanceRemaining > 0 && (
                  <button 
                    className="btn btn-primary btn-sm balance-btn"
                    title={`Pay remaining balance: ${formatCurrency(totals.balanceRemaining)}`}
                  >
                    💳 Pay Balance
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Add Enrollment Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add New Enrollment</h3>
              <button 
                onClick={() => setShowAddModal(false)}
                className="modal-close"
              >
                ×
              </button>
            </div>
            <form onSubmit={handleAddEnrollment} className="modal-body">
              <div className="form-group">
                <label>Student:</label>
                <select
                  value={formData.student_id}
                  onChange={(e) => setFormData({...formData, student_id: e.target.value})}
                  required
                  className="input"
                >
                  <option value="">Select Student</option>
                  {students.map(student => (
                    <option key={student.id} value={student.id}>
                      {student.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Program:</label>
                <select
                  value={formData.program_name}
                  onChange={(e) => setFormData({...formData, program_name: e.target.value})}
                  className="input"
                >
                  <option value="">Select Program</option>
                  {programs.map(program => (
                    <option key={program.id} value={program.name}>
                      {program.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Total Lessons:</label>
                <input
                  type="number"
                  value={formData.total_lessons}
                  onChange={(e) => setFormData({...formData, total_lessons: e.target.value})}
                  required
                  min="1"
                  className="input"
                />
              </div>
              <div className="form-group">
                <label>Price Per Lesson ($):</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.price_per_lesson}
                  onChange={(e) => setFormData({...formData, price_per_lesson: e.target.value})}
                  required
                  min="0"
                  className="input"
                />
              </div>
              <div className="enrollment-total-display">
                <strong>Total Cost: ${(parseFloat(formData.total_lessons || 0) * parseFloat(formData.price_per_lesson || 0)).toFixed(2)}</strong>
              </div>
              <div className="form-group">
                <label>Initial Payment ($):</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.initial_payment}
                  onChange={(e) => setFormData({
                    ...formData, 
                    initial_payment: e.target.value,
                    total_paid: e.target.value // Keep for backward compatibility
                  })}
                  min="0"
                  className="input"
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowAddModal(false)} className="btn btn-outline">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Add Enrollment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Enrollment Modal */}
      {showEditModal && selectedEnrollment && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Edit Enrollment</h3>
              <button 
                onClick={() => setShowEditModal(false)}
                className="modal-close"
              >
                ×
              </button>
            </div>
            <form onSubmit={handleEditEnrollment} className="modal-body">
              <div className="form-group">
                <label>Student:</label>
                <select
                  value={formData.student_id}
                  onChange={(e) => setFormData({...formData, student_id: e.target.value})}
                  required
                  className="input"
                >
                  <option value="">Select Student</option>
                  {students.map(student => (
                    <option key={student.id} value={student.id}>
                      {student.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Program:</label>
                <select
                  value={formData.program_name}
                  onChange={(e) => setFormData({...formData, program_name: e.target.value})}
                  className="input"
                >
                  <option value="">Select Program</option>
                  {programs.map(program => (
                    <option key={program.id} value={program.name}>
                      {program.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Total Lessons:</label>
                <input
                  type="number"
                  value={formData.total_lessons}
                  onChange={(e) => setFormData({...formData, total_lessons: e.target.value})}
                  required
                  min="1"
                  className="input"
                />
              </div>
              <div className="form-group">
                <label>Price Per Lesson ($):</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.price_per_lesson}
                  onChange={(e) => setFormData({...formData, price_per_lesson: e.target.value})}
                  required
                  min="0"
                  className="input"
                />
              </div>
              <div className="enrollment-total-display">
                <strong>Total Cost: ${(parseFloat(formData.total_lessons || 0) * parseFloat(formData.price_per_lesson || 0)).toFixed(2)}</strong>
              </div>
              <div className="form-group">
                <label>Initial Payment ($):</label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.initial_payment}
                  onChange={(e) => setFormData({
                    ...formData, 
                    initial_payment: e.target.value,
                    total_paid: e.target.value // Keep for backward compatibility
                  })}
                  min="0"
                  className="input"
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowEditModal(false)} className="btn btn-outline">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Update Enrollment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnrollmentsPage;