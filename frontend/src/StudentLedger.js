import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : '/api';

const StudentLedger = ({ student, onClose }) => {
  const [ledgerData, setLedgerData] = useState(null);
  const [programs, setPrograms] = useState([]);
  const [showAddEnrollment, setShowAddEnrollment] = useState(false);
  const [showAddPayment, setShowAddPayment] = useState(false);
  const [showEditStudent, setShowEditStudent] = useState(false);
  const [loading, setLoading] = useState(true);
  
  const [enrollmentData, setEnrollmentData] = useState({
    program_name: '',
    total_lessons: '',
    total_paid: ''
  });
  
  const [paymentData, setPaymentData] = useState({
    amount: '',
    payment_method: 'cash',
    enrollment_id: '',
    notes: ''
  });

  const [editStudentData, setEditStudentData] = useState({
    name: '',
    email: '',
    phone: '',
    parent_name: '',
    parent_phone: '',
    parent_email: '',
    notes: ''
  });

  useEffect(() => {
    if (student) {
      fetchLedgerData();
      fetchPrograms();
      // Initialize edit form with current student data
      setEditStudentData({
        name: student.name || '',
        email: student.email || '',
        phone: student.phone || '',
        parent_name: student.parent_name || '',
        parent_phone: student.parent_phone || '',
        parent_email: student.parent_email || '',
        notes: student.notes || ''
      });
    }
  }, [student]);

  const fetchLedgerData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/students/${student.id}/ledger`);
      setLedgerData(response.data);
    } catch (error) {
      console.error('Failed to fetch ledger data:', error);
      alert('Failed to load student ledger');
    } finally {
      setLoading(false);
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

  const handleAddEnrollment = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/enrollments`, {
        student_id: student.id,
        program_name: enrollmentData.program_name,
        total_lessons: parseInt(enrollmentData.total_lessons),
        total_paid: parseFloat(enrollmentData.total_paid)
      });
      
      setShowAddEnrollment(false);
      setEnrollmentData({ program_name: '', total_lessons: '', total_paid: '' });
      fetchLedgerData();
      alert('Enrollment added successfully!');
    } catch (error) {
      console.error('Failed to add enrollment:', error);
      alert('Failed to add enrollment');
    }
  };

  const handleDeleteEnrollment = async (enrollmentId, programName) => {
    if (window.confirm(`Are you sure you want to delete the enrollment for "${programName}"? This action cannot be undone.`)) {
      try {
        await axios.delete(`${API}/enrollments/${enrollmentId}`);
        fetchLedgerData();
        alert('Enrollment deleted successfully!');
      } catch (error) {
        console.error('Failed to delete enrollment:', error);
        alert('Failed to delete enrollment');
      }
    }
  };

  const handleAddPayment = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/payments`, {
        student_id: student.id,
        amount: parseFloat(paymentData.amount),
        payment_method: paymentData.payment_method,
        enrollment_id: paymentData.enrollment_id || null,
        notes: paymentData.notes
      });
      
      setShowAddPayment(false);
      setPaymentData({ amount: '', payment_method: 'cash', enrollment_id: '', notes: '' });
      fetchLedgerData();
      alert('Payment added successfully!');
    } catch (error) {
      console.error('Failed to add payment:', error);
      alert('Failed to add payment');
    }
  };

  const handleDeletePayment = async (paymentId, amount) => {
    if (window.confirm(`Are you sure you want to delete the payment of $${amount}? This action cannot be undone.`)) {
      try {
        await axios.delete(`${API}/payments/${paymentId}`);
        fetchLedgerData();
        alert('Payment deleted successfully!');
      } catch (error) {
        console.error('Failed to delete payment:', error);
        alert('Failed to delete payment');
      }
    }
  };

  const handleEditStudent = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/students/${student.id}`, editStudentData);
      
      setShowEditStudent(false);
      fetchLedgerData();
      alert('Student information updated successfully!');
    } catch (error) {
      console.error('Failed to update student:', error);
      alert('Failed to update student information');
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const formatDateTime = (dateStr) => {
    return new Date(dateStr).toLocaleString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="modal-overlay">
        <div className="ledger-modal">
          <div className="loading">Loading student ledger...</div>
        </div>
      </div>
    );
  }

  if (!ledgerData) {
    return (
      <div className="modal-overlay">
        <div className="ledger-modal">
          <div className="error">Failed to load student ledger</div>
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay">
      <div className="ledger-modal">
        <div className="ledger-header">
          <h2>📊 Student Ledger Card</h2>
          <button onClick={onClose} className="close-btn">×</button>
        </div>

        {/* Student Info */}
        <div className="ledger-section student-info">
          <div className="student-header">
            <h3>{ledgerData.student.name}</h3>
            <button 
              onClick={() => setShowEditStudent(true)}
              className="btn btn-primary btn-sm"
              title="Edit Student Information"
            >
              ✏️ Edit Info
            </button>
          </div>
          <div className="student-details">
            <p>📧 {ledgerData.student.email}</p>
            <p>📞 {ledgerData.student.phone}</p>
            {ledgerData.student.parent_name && (
              <p>👨‍👩‍👧‍👦 Parent: {ledgerData.student.parent_name} ({ledgerData.student.parent_phone})</p>
            )}
            {ledgerData.student.notes && (
              <p>📝 Notes: {ledgerData.student.notes}</p>
            )}
          </div>
          
          {/* Financial Summary */}
          <div className="financial-summary">
            <div className="summary-item">
              <span className="label">Total Paid:</span>
              <span className="value">${ledgerData.total_paid.toFixed(2)}</span>
            </div>
            <div className="summary-item">
              <span className="label">Total Lessons Enrolled:</span>
              <span className="value">{ledgerData.total_enrolled_lessons}</span>
            </div>
            <div className="summary-item">
              <span className="label">Remaining Lessons:</span>
              <span className="value">{ledgerData.remaining_lessons}</span>
            </div>
            <div className="summary-item">
              <span className="label">Lessons Completed:</span>
              <span className="value">{ledgerData.lessons_taken}</span>
            </div>
          </div>
        </div>

        <div className="ledger-content">
          {/* Enrollments Section */}
          <div className="ledger-section">
            <div className="section-header">
              <h4>📚 Enrollments</h4>
              <button 
                onClick={() => setShowAddEnrollment(true)}
                className="btn btn-primary btn-sm"
              >
                + Add Enrollment
              </button>
            </div>
            
            {ledgerData.enrollments.length > 0 ? (
              <div className="enrollments-list">
                {ledgerData.enrollments.map(enrollment => (
                  <div key={enrollment.id} className="enrollment-card">
                    <div className="enrollment-info">
                      <h5>{enrollment.program_name}</h5>
                      <p>Lessons: {enrollment.remaining_lessons}/{enrollment.total_lessons}</p>
                      <p>Enrolled: {formatDate(enrollment.purchase_date)}</p>
                      <p>Status: {enrollment.is_active ? '✅ Active' : '❌ Inactive'}</p>
                    </div>
                    <button 
                      onClick={() => handleDeleteEnrollment(enrollment.id, enrollment.program_name)}
                      className="btn btn-danger btn-sm"
                      title="Delete Enrollment"
                    >
                      🗑️
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-state">No enrollments found</p>
            )}
          </div>

          {/* Payments Section */}
          <div className="ledger-section">
            <div className="section-header">
              <h4>💳 Payments</h4>
              <button 
                onClick={() => setShowAddPayment(true)}
                className="btn btn-primary btn-sm"
              >
                + Add Payment
              </button>
            </div>
            
            {ledgerData.payments.length > 0 ? (
              <div className="payments-list">
                {ledgerData.payments.map(payment => (
                  <div key={payment.id} className="payment-card">
                    <div className="payment-info">
                      <div className="payment-amount">${payment.amount.toFixed(2)}</div>
                      <div className="payment-method">{payment.payment_method.replace('_', ' ').toUpperCase()}</div>
                      <div className="payment-date">{formatDate(payment.payment_date)}</div>
                      {payment.notes && <div className="payment-notes">Note: {payment.notes}</div>}
                    </div>
                    <button 
                      onClick={() => handleDeletePayment(payment.id, payment.amount)}
                      className="btn btn-danger btn-sm"
                      title="Delete Payment"
                    >
                      🗑️
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-state">No payments found</p>
            )}
          </div>

          {/* Upcoming Lessons Section */}
          <div className="ledger-section">
            <h4>📅 Upcoming Lessons ({ledgerData.upcoming_lessons.length})</h4>
            {ledgerData.upcoming_lessons.length > 0 ? (
              <div className="lessons-list">
                {ledgerData.upcoming_lessons.slice(0, 5).map(lesson => (
                  <div key={lesson.id} className="lesson-card">
                    <div className="lesson-datetime">{formatDateTime(lesson.start_datetime)}</div>
                    <div className="lesson-teacher">
                      👨‍🏫 {lesson.teacher_names && lesson.teacher_names.length > 0 
                        ? lesson.teacher_names.join(', ')
                        : lesson.teacher_name || 'Unknown'
                      }
                    </div>
                    {lesson.notes && <div className="lesson-notes">📝 {lesson.notes}</div>}
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-state">No upcoming lessons</p>
            )}
          </div>

          {/* Lesson History Section */}
          <div className="ledger-section">
            <h4>📋 Recent Lesson History</h4>
            {ledgerData.lesson_history.length > 0 ? (
              <div className="lessons-list">
                {ledgerData.lesson_history.slice(0, 10).map(lesson => (
                  <div key={lesson.id} className={`lesson-card ${lesson.is_attended ? 'attended' : 'missed'}`}>
                    <div className="lesson-datetime">{formatDateTime(lesson.start_datetime)}</div>
                    <div className="lesson-teacher">👨‍🏫 {lesson.teacher_name}</div>
                    <div className="lesson-status">
                      {lesson.is_attended ? '✅ Attended' : lesson.is_cancelled ? '❌ Cancelled' : '❓ Not Marked'}
                    </div>
                    {lesson.notes && <div className="lesson-notes">📝 {lesson.notes}</div>}
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-state">No lesson history</p>
            )}
          </div>
        </div>

        {/* Add Enrollment Modal */}
        {showAddEnrollment && (
          <div className="sub-modal">
            <div className="sub-modal-content">
              <h3>Add New Enrollment</h3>
              <form onSubmit={handleAddEnrollment}>
                <div className="form-group">
                  <label>Dance Program *</label>
                  <select
                    value={enrollmentData.program_name}
                    onChange={(e) => setEnrollmentData({...enrollmentData, program_name: e.target.value})}
                    required
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
                  <input
                    type="number"
                    value={enrollmentData.total_lessons}
                    onChange={(e) => setEnrollmentData({...enrollmentData, total_lessons: e.target.value})}
                    required
                    min="1"
                    max="100"
                  />
                </div>
                <div className="form-group">
                  <label>Amount Paid</label>
                  <input
                    type="number"
                    step="0.01"
                    value={enrollmentData.total_paid}
                    onChange={(e) => setEnrollmentData({...enrollmentData, total_paid: e.target.value})}
                    placeholder="0.00"
                  />
                </div>
                <div className="form-actions">
                  <button type="button" onClick={() => setShowAddEnrollment(false)}>Cancel</button>
                  <button type="submit">Add Enrollment</button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Add Payment Modal */}
        {showAddPayment && (
          <div className="sub-modal">
            <div className="sub-modal-content">
              <h3>Add New Payment</h3>
              <form onSubmit={handleAddPayment}>
                <div className="form-group">
                  <label>Amount *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={paymentData.amount}
                    onChange={(e) => setPaymentData({...paymentData, amount: e.target.value})}
                    required
                    placeholder="0.00"
                  />
                </div>
                <div className="form-group">
                  <label>Payment Method</label>
                  <select
                    value={paymentData.payment_method}
                    onChange={(e) => setPaymentData({...paymentData, payment_method: e.target.value})}
                  >
                    <option value="cash">Cash</option>
                    <option value="credit_card">Credit Card</option>
                    <option value="debit_card">Debit Card</option>
                    <option value="check">Check</option>
                    <option value="bank_transfer">Bank Transfer</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Link to Enrollment (Optional)</label>
                  <select
                    value={paymentData.enrollment_id}
                    onChange={(e) => setPaymentData({...paymentData, enrollment_id: e.target.value})}
                  >
                    <option value="">No specific enrollment</option>
                    {ledgerData.enrollments.filter(e => e.is_active).map(enrollment => (
                      <option key={enrollment.id} value={enrollment.id}>
                        {enrollment.program_name} ({enrollment.remaining_lessons} lessons left)
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Notes</label>
                  <textarea
                    value={paymentData.notes}
                    onChange={(e) => setPaymentData({...paymentData, notes: e.target.value})}
                    placeholder="Optional notes about this payment"
                    rows="2"
                  />
                </div>
                <div className="form-actions">
                  <button type="button" onClick={() => setShowAddPayment(false)}>Cancel</button>
                  <button type="submit">Add Payment</button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Edit Student Modal */}
        {showEditStudent && (
          <div className="sub-modal">
            <div className="sub-modal-content">
              <h3>Edit Student Information</h3>
              <form onSubmit={handleEditStudent}>
                <div className="form-group">
                  <label>Full Name *</label>
                  <input
                    type="text"
                    value={editStudentData.name}
                    onChange={(e) => setEditStudentData({...editStudentData, name: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Email *</label>
                  <input
                    type="email"
                    value={editStudentData.email}
                    onChange={(e) => setEditStudentData({...editStudentData, email: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Phone *</label>
                  <input
                    type="tel"
                    value={editStudentData.phone}
                    onChange={(e) => setEditStudentData({...editStudentData, phone: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Parent Name</label>
                  <input
                    type="text"
                    value={editStudentData.parent_name}
                    onChange={(e) => setEditStudentData({...editStudentData, parent_name: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>Parent Phone</label>
                  <input
                    type="tel"
                    value={editStudentData.parent_phone}
                    onChange={(e) => setEditStudentData({...editStudentData, parent_phone: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>Parent Email</label>
                  <input
                    type="email"
                    value={editStudentData.parent_email}
                    onChange={(e) => setEditStudentData({...editStudentData, parent_email: e.target.value})}
                  />
                </div>
                <div className="form-group">
                  <label>Notes</label>
                  <textarea
                    value={editStudentData.notes}
                    onChange={(e) => setEditStudentData({...editStudentData, notes: e.target.value})}
                    rows="3"
                    placeholder="Any special notes about this student..."
                  />
                </div>
                <div className="form-actions">
                  <button type="button" onClick={() => setShowEditStudent(false)}>Cancel</button>
                  <button type="submit">Update Student</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentLedger;