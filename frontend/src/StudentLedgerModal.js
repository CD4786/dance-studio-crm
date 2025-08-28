import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

const StudentLedgerModal = ({ student, lesson, isOpen, onClose, onLedgerUpdate }) => {
  const [ledgerData, setLedgerData] = useState(null);
  const [programs, setPrograms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddPayment, setShowAddPayment] = useState(false);
  const [showAddEnrollment, setShowAddEnrollment] = useState(false);
  
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

  const handleAddPayment = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/payments`, {
        student_id: student.id,
        enrollment_id: paymentData.enrollment_id,
        amount: parseFloat(paymentData.amount),
        payment_method: paymentData.payment_method,
        notes: paymentData.notes
      });
      
      setShowAddPayment(false);
      setPaymentData({ amount: '', payment_method: 'cash', enrollment_id: '', notes: '' });
      await fetchLedgerData();
      
      // Notify parent component of ledger update for real-time updates
      if (onLedgerUpdate) {
        onLedgerUpdate(student.id);
      }
      
      alert('Payment added successfully!');
    } catch (error) {
      console.error('Failed to add payment:', error);
      alert('Failed to add payment');
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
      await fetchLedgerData();
      
      // Notify parent component of ledger update
      if (onLedgerUpdate) {
        onLedgerUpdate(student.id);
      }
      
      alert('Enrollment added successfully!');
    } catch (error) {
      console.error('Failed to add enrollment:', error);
      alert('Failed to add enrollment');
    }
  };

  const handleDeletePayment = async (paymentId) => {
    if (window.confirm('Are you sure you want to delete this payment?')) {
      try {
        await axios.delete(`${API}/payments/${paymentId}`);
        await fetchLedgerData();
        
        // Notify parent component of ledger update
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
    }).format(amount);
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="student-ledger-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-section">
            <h2>💰 Student Ledger</h2>
            <div className="student-info">
              <h3>{student?.name}</h3>
              {lesson && (
                <p className="lesson-context">
                  📅 Lesson: {new Date(lesson.start_datetime).toLocaleDateString()} at{' '}
                  {new Date(lesson.start_datetime).toLocaleTimeString('en-US', { 
                    hour: 'numeric', 
                    minute: '2-digit' 
                  })}
                </p>
              )}
            </div>
          </div>
          <button onClick={onClose} className="modal-close-btn">✕</button>
        </div>

        <div className="modal-content">
          {loading ? (
            <div className="loading-state">Loading ledger data...</div>
          ) : ledgerData ? (
            <>
              {/* Summary Section */}
              <div className="ledger-summary">
                <div className="summary-cards">
                  <div className="summary-card balance">
                    <div className="card-icon">💳</div>
                    <div className="card-content">
                      <h4>Current Balance</h4>
                      <span className={`balance-amount ${ledgerData.summary.balance >= 0 ? 'positive' : 'negative'}`}>
                        {formatCurrency(ledgerData.summary.balance)}
                      </span>
                    </div>
                  </div>
                  
                  <div className="summary-card lessons">
                    <div className="card-icon">📚</div>
                    <div className="card-content">
                      <h4>Lessons Remaining</h4>
                      <span className="lessons-count">{ledgerData.summary.lessons_remaining}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="quick-actions">
                <button 
                  onClick={() => setShowAddPayment(true)}
                  className="action-btn primary"
                >
                  ➕ Add Payment
                </button>
                <button 
                  onClick={() => setShowAddEnrollment(true)}
                  className="action-btn secondary"
                >
                  📝 Add Enrollment
                </button>
              </div>

              {/* Recent Transactions */}
              <div className="transactions-section">
                <h4>Recent Transactions</h4>
                <div className="transactions-list">
                  {ledgerData.recent_transactions?.slice(0, 5).map((transaction, index) => (
                    <div key={index} className="transaction-item">
                      <div className="transaction-details">
                        <span className="transaction-type">
                          {transaction.type === 'payment' ? '💰' : '📚'} {transaction.description}
                        </span>
                        <span className="transaction-date">
                          {new Date(transaction.date).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="transaction-amount">
                        <span className={`amount ${transaction.type === 'payment' ? 'positive' : 'neutral'}`}>
                          {transaction.type === 'payment' ? '+' : ''}{formatCurrency(transaction.amount)}
                        </span>
                        {transaction.type === 'payment' && (
                          <button 
                            onClick={() => handleDeletePayment(transaction.id)}
                            className="delete-btn"
                            title="Delete Payment"
                          >
                            🗑️
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Add Payment Modal */}
              {showAddPayment && (
                <div className="form-modal">
                  <div className="form-modal-content">
                    <h4>Add Payment</h4>
                    <form onSubmit={handleAddPayment}>
                      <div className="form-group">
                        <label>Amount ($)</label>
                        <input
                          type="number"
                          step="0.01"
                          value={paymentData.amount}
                          onChange={(e) => setPaymentData({...paymentData, amount: e.target.value})}
                          required
                          className="form-input"
                          placeholder="0.00"
                        />
                      </div>

                      <div className="form-group">
                        <label>Payment Method</label>
                        <select
                          value={paymentData.payment_method}
                          onChange={(e) => setPaymentData({...paymentData, payment_method: e.target.value})}
                          className="form-select"
                        >
                          <option value="cash">Cash</option>
                          <option value="check">Check</option>
                          <option value="credit_card">Credit Card</option>
                          <option value="bank_transfer">Bank Transfer</option>
                        </select>
                      </div>

                      <div className="form-group">
                        <label>Enrollment (Optional)</label>
                        <select
                          value={paymentData.enrollment_id}
                          onChange={(e) => setPaymentData({...paymentData, enrollment_id: e.target.value})}
                          className="form-select"
                        >
                          <option value="">Select Enrollment</option>
                          {ledgerData.enrollments?.map((enrollment) => (
                            <option key={enrollment.id} value={enrollment.id}>
                              {enrollment.program_name} - {enrollment.lessons_remaining} lessons left
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="form-group">
                        <label>Notes (Optional)</label>
                        <input
                          type="text"
                          value={paymentData.notes}
                          onChange={(e) => setPaymentData({...paymentData, notes: e.target.value})}
                          className="form-input"
                          placeholder="Payment notes..."
                        />
                      </div>

                      <div className="form-actions">
                        <button type="submit" className="submit-btn">Add Payment</button>
                        <button 
                          type="button" 
                          onClick={() => setShowAddPayment(false)}
                          className="cancel-btn"
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              )}

              {/* Add Enrollment Modal */}
              {showAddEnrollment && (
                <div className="form-modal">
                  <div className="form-modal-content">
                    <h4>Add Enrollment</h4>
                    <form onSubmit={handleAddEnrollment}>
                      <div className="form-group">
                        <label>Program</label>
                        <select
                          value={enrollmentData.program_name}
                          onChange={(e) => setEnrollmentData({...enrollmentData, program_name: e.target.value})}
                          className="form-select"
                          required
                        >
                          <option value="">Select Program</option>
                          {programs.map((program) => (
                            <option key={program.id} value={program.name}>
                              {program.name}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="form-group">
                        <label>Total Lessons</label>
                        <input
                          type="number"
                          value={enrollmentData.total_lessons}
                          onChange={(e) => setEnrollmentData({...enrollmentData, total_lessons: e.target.value})}
                          required
                          className="form-input"
                          placeholder="Number of lessons"
                        />
                      </div>

                      <div className="form-group">
                        <label>Amount Paid ($)</label>
                        <input
                          type="number"
                          step="0.01"
                          value={enrollmentData.total_paid}
                          onChange={(e) => setEnrollmentData({...enrollmentData, total_paid: e.target.value})}
                          required
                          className="form-input"
                          placeholder="0.00"
                        />
                      </div>

                      <div className="form-actions">
                        <button type="submit" className="submit-btn">Add Enrollment</button>
                        <button 
                          type="button" 
                          onClick={() => setShowAddEnrollment(false)}
                          className="cancel-btn"
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="no-data">No ledger data available</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StudentLedgerModal;