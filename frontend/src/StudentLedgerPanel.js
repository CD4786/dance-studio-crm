import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const StudentLedgerPanel = ({ student, lesson, isOpen, onClose, onLedgerUpdate }) => {
  const [ledgerData, setLedgerData] = useState(null);
  const [programs, setPrograms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddPayment, setShowAddPayment] = useState(false);
  const [showAddEnrollment, setShowAddEnrollment] = useState(false);
  const [error, setError] = useState('');
  
  const [paymentData, setPaymentData] = useState({
    amount: '',
    payment_method: 'cash',
    enrollment_id: '',
    notes: ''
  });

  const [enrollmentData, setEnrollmentData] = useState({
    program_name: '',
    total_lessons: '',
    total_paid: ''
  });

  useEffect(() => {
    if (isOpen && student) {
      fetchLedgerData();
      fetchPrograms();
    }
  }, [isOpen, student]);

  const fetchLedgerData = async () => {
    try {
      setLoading(true);
      setError('');
      console.log('Fetching ledger data for student:', student.id);
      console.log('API URL:', `${API}/students/${student.id}/ledger`);
      console.log('Axios headers:', axios.defaults.headers);
      
      const response = await axios.get(`${API}/students/${student.id}/ledger`);
      console.log('Ledger data received:', response.data);
      setLedgerData(response.data);
    } catch (error) {
      console.error('Failed to fetch ledger data:', error);
      console.error('Error response:', error.response);
      console.error('Error message:', error.message);
      
      if (error.response?.status === 401) {
        setError('Authentication failed - please log in again');
      } else if (error.response?.status === 404) {
        setError('Student not found');
      } else {
        setError(`Failed to load student ledger: ${error.response?.data?.detail || error.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchPrograms = async () => {
    try {
      console.log('Fetching programs...');
      const response = await axios.get(`${API}/programs`);
      console.log('Programs received:', response.data);
      setPrograms(response.data || []);
    } catch (error) {
      console.error('Failed to fetch programs:', error);
      // Don't set error state for programs failure, just log it
      setPrograms([]);
    }
  };

  const handleAddPayment = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/payments`, {
        student_id: student.id,
        enrollment_id: paymentData.enrollment_id || null,
        amount: parseFloat(paymentData.amount),
        payment_method: paymentData.payment_method,
        notes: paymentData.notes
      });
      
      setShowAddPayment(false);
      setPaymentData({ amount: '', payment_method: 'cash', enrollment_id: '', notes: '' });
      await fetchLedgerData();
      
      if (onLedgerUpdate) {
        onLedgerUpdate(student.id);
      }
      
      alert('Payment added successfully!');
    } catch (error) {
      console.error('Failed to add payment:', error);
      alert('Failed to add payment: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleAddEnrollment = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/enrollments`, {
        student_id: student.id,
        program_name: enrollmentData.program_name,
        total_lessons: parseInt(enrollmentData.total_lessons),
        total_paid: parseFloat(enrollmentData.total_paid),
        is_active: true
      });
      
      setShowAddEnrollment(false);
      setEnrollmentData({ program_name: '', total_lessons: '', total_paid: '' });
      await fetchLedgerData();
      
      if (onLedgerUpdate) {
        onLedgerUpdate(student.id);
      }
      
      alert('Enrollment added successfully!');
    } catch (error) {
      console.error('Failed to add enrollment:', error);
      alert('Failed to add enrollment: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeletePayment = async (paymentId) => {
    if (window.confirm('Are you sure you want to delete this payment?')) {
      try {
        await axios.delete(`${API}/payments/${paymentId}`);
        await fetchLedgerData();
        
        if (onLedgerUpdate) {
          onLedgerUpdate(student.id);
        }
        
        alert('Payment deleted successfully!');
      } catch (error) {
        console.error('Failed to delete payment:', error);
        alert('Failed to delete payment');
      }
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  const calculateBalance = () => {
    if (!ledgerData) return 0;
    
    const totalPaid = ledgerData.total_paid || 0;
    const enrollments = ledgerData.enrollments || [];
    const totalEnrollmentCost = enrollments.reduce((sum, enrollment) => {
      // Assuming each lesson costs $50 (you can adjust this)
      return sum + (enrollment.total_lessons * 50);
    }, 0);
    
    return totalPaid - totalEnrollmentCost;
  };

  const getRemainingLessons = () => {
    if (!ledgerData) return 0;
    return ledgerData.remaining_lessons || 0;
  };

  if (!isOpen) return null;

  return (
    <div className="student-ledger-panel">
      <div className="panel-header">
        <div className="panel-title-section">
          <h3>💰 {student?.name} Ledger</h3>
          {lesson && (
            <p className="lesson-context">
              📅 {new Date(lesson.start_datetime).toLocaleDateString()} at{' '}
              {new Date(lesson.start_datetime).toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit' 
              })}
            </p>
          )}
        </div>
        <button onClick={onClose} className="panel-close-btn">✕</button>
      </div>

      <div className="panel-content">
        {loading ? (
          <div className="loading-state">Loading...</div>
        ) : error ? (
          <div className="error-state">{error}</div>
        ) : (
          <>
            {/* Quick Summary */}
            <div className="quick-summary">
              <div className="summary-item">
                <span className="label">Balance:</span>
                <span className={`value ${calculateBalance() >= 0 ? 'positive' : 'negative'}`}>
                  {formatCurrency(calculateBalance())}
                </span>
              </div>
              <div className="summary-item">
                <span className="label">Lessons Left:</span>
                <span className="value">{getRemainingLessons()}</span>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="quick-actions">
              <button 
                onClick={() => setShowAddPayment(true)}
                className="action-btn primary"
              >
                💰 Add Payment
              </button>
              <button 
                onClick={() => setShowAddEnrollment(true)}
                className="action-btn secondary"
              >
                📝 Add Enrollment
              </button>
            </div>

            {/* Recent Activity */}
            <div className="recent-activity">
              <h4>Recent Activity</h4>
              
              {/* Show enrollments */}
              {ledgerData?.enrollments?.length > 0 && (
                <div className="activity-section">
                  <h5>📚 Enrollments</h5>
                  {ledgerData.enrollments.slice(0, 2).map((enrollment, index) => (
                    <div key={index} className="activity-item">
                      <div className="activity-details">
                        <span className="activity-name">{enrollment.program_name}</span>
                        <span className="activity-info">
                          {enrollment.remaining_lessons || 0} of {enrollment.total_lessons} lessons left
                        </span>
                      </div>
                      <span className="activity-amount">{formatCurrency(enrollment.total_paid)}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Show payments */}
              {ledgerData?.payments?.length > 0 && (
                <div className="activity-section">
                  <h5>💳 Recent Payments</h5>
                  {ledgerData.payments.slice(0, 3).map((payment, index) => (
                    <div key={index} className="activity-item">
                      <div className="activity-details">
                        <span className="activity-name">{payment.payment_method}</span>
                        <span className="activity-info">
                          {new Date(payment.payment_date).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="activity-actions">
                        <span className="activity-amount positive">+{formatCurrency(payment.amount)}</span>
                        <button 
                          onClick={() => handleDeletePayment(payment.id)}
                          className="delete-btn"
                          title="Delete Payment"
                        >
                          ×
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* No data state */}
              {(!ledgerData?.enrollments?.length && !ledgerData?.payments?.length) && (
                <div className="no-data">
                  <p>No enrollments or payments yet.</p>
                  <p>Add an enrollment or payment to get started!</p>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Add Payment Form */}
      {showAddPayment && (
        <div className="floating-form">
          <div className="form-header">
            <h4>Add Payment</h4>
            <button onClick={() => setShowAddPayment(false)} className="form-close">×</button>
          </div>
          <form onSubmit={handleAddPayment} className="compact-form">
            <input
              type="number"
              step="0.01"
              value={paymentData.amount}
              onChange={(e) => setPaymentData({...paymentData, amount: e.target.value})}
              placeholder="Amount ($)"
              required
            />
            <select
              value={paymentData.payment_method}
              onChange={(e) => setPaymentData({...paymentData, payment_method: e.target.value})}
            >
              <option value="cash">Cash</option>
              <option value="check">Check</option>
              <option value="credit_card">Credit Card</option>
              <option value="bank_transfer">Bank Transfer</option>
            </select>
            <input
              type="text"
              value={paymentData.notes}
              onChange={(e) => setPaymentData({...paymentData, notes: e.target.value})}
              placeholder="Notes (optional)"
            />
            <div className="form-actions">
              <button type="submit" className="submit-btn">Add</button>
              <button type="button" onClick={() => setShowAddPayment(false)} className="cancel-btn">Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Add Enrollment Form */}
      {showAddEnrollment && (
        <div className="floating-form">
          <div className="form-header">
            <h4>Add Enrollment</h4>
            <button onClick={() => setShowAddEnrollment(false)} className="form-close">×</button>
          </div>
          <form onSubmit={handleAddEnrollment} className="compact-form">
            <select
              value={enrollmentData.program_name}
              onChange={(e) => setEnrollmentData({...enrollmentData, program_name: e.target.value})}
              required
            >
              <option value="">Select Program</option>
              {programs.map((program) => (
                <option key={program.id} value={program.name}>
                  {program.name}
                </option>
              ))}
            </select>
            <input
              type="number"
              value={enrollmentData.total_lessons}
              onChange={(e) => setEnrollmentData({...enrollmentData, total_lessons: e.target.value})}
              placeholder="Number of lessons"
              required
            />
            <input
              type="number"
              step="0.01"
              value={enrollmentData.total_paid}
              onChange={(e) => setEnrollmentData({...enrollmentData, total_paid: e.target.value})}
              placeholder="Amount paid ($)"
              required
            />
            <div className="form-actions">
              <button type="submit" className="submit-btn">Add</button>
              <button type="button" onClick={() => setShowAddEnrollment(false)} className="cancel-btn">Cancel</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default StudentLedgerPanel;