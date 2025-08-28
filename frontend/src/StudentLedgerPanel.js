// Enhanced StudentLedgerPanel with real-time synchronization
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const StudentLedgerPanel = ({ student, lesson, isOpen, onClose, onLedgerUpdate, onNavigateToDate }) => {
  const [ledgerData, setLedgerData] = useState(null);
  const [programs, setPrograms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddPayment, setShowAddPayment] = useState(false);
  const [showAddEnrollment, setShowAddEnrollment] = useState(false);
  const [showLessonHistory, setShowLessonHistory] = useState(false);
  const [lessonHistory, setLessonHistory] = useState(null);
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
    price_per_lesson: '50.00',
    initial_payment: '0.00',
    total_paid: '0.00'
  });

  // Auto-refresh when panel opens or student changes
  useEffect(() => {
    if (isOpen && student) {
      fetchLedgerData();
      fetchPrograms();
    }
  }, [isOpen, student]);

  // Listen for real-time updates via custom event
  useEffect(() => {
    const handleRealTimeUpdate = (event) => {
      const { type, data } = event.detail;
      
      // Refresh ledger data if this student is affected
      if (student && data.student_id === student.id) {
        console.log(`Real-time update for ${student.name}: ${type}`);
        fetchLedgerData();
        
        if (showLessonHistory) {
          fetchLessonHistory();
        }
      }
    };

    window.addEventListener('ledger-update', handleRealTimeUpdate);
    
    return () => {
      window.removeEventListener('ledger-update', handleRealTimeUpdate);
    };
  }, [student, showLessonHistory]);

  const fetchLedgerData = async () => {
    try {
      setLoading(true);
      setError('');
      console.log('Fetching comprehensive ledger data for student:', student.id);
      
      const response = await axios.get(`${API}/students/${student.id}/ledger`);
      console.log('Comprehensive ledger data received:', response.data);
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
      setPrograms([]);
    }
  };

  const fetchLessonHistory = async () => {
    try {
      const response = await axios.get(`${API}/students/${student.id}/lessons-history`);
      setLessonHistory(response.data);
    } catch (error) {
      console.error('Failed to fetch lesson history:', error);
    }
  };

  const handleAddPayment = async (e) => {
    e.preventDefault();
    try {
      const paymentResponse = await axios.post(`${API}/payments`, {
        student_id: student.id,
        enrollment_id: paymentData.enrollment_id || null,
        amount: parseFloat(paymentData.amount),
        payment_method: paymentData.payment_method,
        notes: paymentData.notes
      });
      
      setShowAddPayment(false);
      setPaymentData({ amount: '', payment_method: 'cash', enrollment_id: '', notes: '' });
      
      // Real-time update will be handled via WebSocket, but also refresh locally
      await fetchLedgerData();
      
      if (onLedgerUpdate) {
        onLedgerUpdate(student.id);
      }
      
      // Dispatch custom event for other components
      window.dispatchEvent(new CustomEvent('ledger-update', {
        detail: { type: 'payment_created', data: { student_id: student.id } }
      }));
      
      alert(`Payment of $${paymentData.amount} added successfully! Lesson credits updated.`);
    } catch (error) {
      console.error('Failed to add payment:', error);
      alert('Failed to add payment: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleAddEnrollment = async (e) => {
    e.preventDefault();
    try {
      const enrollmentResponse = await axios.post(`${API}/enrollments`, {
        student_id: student.id,
        program_name: enrollmentData.program_name,
        total_lessons: parseInt(enrollmentData.total_lessons),
        price_per_lesson: parseFloat(enrollmentData.price_per_lesson),
        initial_payment: parseFloat(enrollmentData.initial_payment),
        total_paid: parseFloat(enrollmentData.total_paid)
      });
      
      setShowAddEnrollment(false);
      setEnrollmentData({ 
        program_name: '', 
        total_lessons: '', 
        price_per_lesson: '50.00',
        initial_payment: '0.00', 
        total_paid: '0.00' 
      });
      
      // Real-time update will be handled via WebSocket, but also refresh locally
      await fetchLedgerData();
      
      if (onLedgerUpdate) {
        onLedgerUpdate(student.id);
      }
      
      // Dispatch custom event for other components
      window.dispatchEvent(new CustomEvent('ledger-update', {
        detail: { type: 'enrollment_created', data: { student_id: student.id } }
      }));
      
      const totalCost = parseInt(enrollmentData.total_lessons) * parseFloat(enrollmentData.price_per_lesson);
      const availableLessons = Math.floor(parseFloat(enrollmentData.initial_payment) / parseFloat(enrollmentData.price_per_lesson));
      
      alert(`Enrollment created successfully!\n\nProgram: ${enrollmentData.program_name}\nTotal Cost: $${totalCost}\nLessons Available: ${availableLessons}`);
    } catch (error) {
      console.error('Failed to add enrollment:', error);
      alert('Failed to add enrollment: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleMarkLessonAttended = async (lessonId, lessonDate) => {
    try {
      await axios.post(`${API}/lessons/${lessonId}/attend`);
      
      // Refresh both lesson history and ledger data
      await fetchLessonHistory();
      await fetchLedgerData();
      
      if (onLedgerUpdate) {
        onLedgerUpdate(student.id);
      }
      
      // Dispatch custom event
      window.dispatchEvent(new CustomEvent('ledger-update', {
        detail: { type: 'lesson_attended', data: { student_id: student.id } }
      }));
      
      alert('Lesson marked as attended! Available lessons updated.');
    } catch (error) {
      console.error('Failed to mark lesson attendance:', error);
      alert('Failed to mark attendance: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleNavigateToLesson = (lessonDate) => {
    if (onNavigateToDate) {
      onNavigateToDate(lessonDate);
      onClose(); // Close the panel after navigation
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  const getAvailableLessons = () => {
    if (!ledgerData || !ledgerData.summary) return 0;
    return ledgerData.summary.total_lessons_available || 0;
  };

  const calculateBalance = () => {
    if (!ledgerData || !ledgerData.summary) return 0;
    return ledgerData.summary.total_balance_remaining || 0;
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
          <div className="loading-state">Loading comprehensive data...</div>
        ) : error ? (
          <div className="error-state">{error}</div>
        ) : (
          <>
            {/* Enhanced Summary with Real-time Data */}
            <div className="quick-summary">
              <div className="summary-item">
                <span className="label">Balance:</span>
                <span className={`value ${calculateBalance() >= 0 ? 'positive' : 'negative'}`}>
                  {formatCurrency(calculateBalance())}
                </span>
              </div>
              <div className="summary-item">
                <span className="label">Lessons Available:</span>
                <span className="value">{getAvailableLessons()}</span>
              </div>
            </div>

            {/* Comprehensive Stats Display */}
            {ledgerData?.summary && (
              <div className="comprehensive-stats">
                <div className="stat-row">
                  <span>📚 Total Enrolled: {ledgerData.summary.total_enrolled_lessons}</span>
                  <span>✅ Lessons Taken: {ledgerData.summary.total_lessons_taken}</span>
                </div>
                <div className="stat-row">
                  <span>💰 Total Paid: {formatCurrency(ledgerData.summary.total_amount_paid)}</span>
                  <span>🎯 Grand Total: {formatCurrency(ledgerData.summary.total_grand_total)}</span>
                </div>
              </div>
            )}

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

            {/* Enhanced Activity Display */}
            <div className="recent-activity">
              <h4>Recent Activity</h4>
              
              {/* Show enrollments with enhanced credit info */}
              {ledgerData?.enrollments?.length > 0 && (
                <div className="activity-section">
                  <h5>📚 Active Enrollments</h5>
                  {ledgerData.enrollments.filter(e => e.is_active).slice(0, 3).map((enrollment, index) => {
                    const grandTotal = (enrollment.total_lessons || 0) * (enrollment.price_per_lesson || 50);
                    const amountPaid = enrollment.amount_paid || 0;
                    const balanceRemaining = grandTotal - amountPaid;
                    
                    return (
                      <div key={index} className="activity-item enrollment-item">
                        <div className="activity-details">
                          <span className="activity-name">{enrollment.program_name}</span>
                          <div className="lesson-credits-info">
                            <span className="lessons-available">
                              💎 Available: {enrollment.lessons_available || 0} lessons
                            </span>
                            <span className="lessons-taken">
                              ✅ Taken: {enrollment.lessons_taken || 0} of {enrollment.total_lessons}
                            </span>
                          </div>
                          <div className="enrollment-financial">
                            <span className="enrollment-cost">Total: {formatCurrency(grandTotal)}</span>
                            <span className="enrollment-paid">Paid: {formatCurrency(amountPaid)}</span>
                            <span className={`enrollment-balance ${balanceRemaining > 0 ? 'negative' : 'positive'}`}>
                              Balance: {formatCurrency(balanceRemaining)}
                            </span>
                          </div>
                        </div>
                        <div className="activity-actions">
                          {balanceRemaining > 0 && (
                            <button 
                              onClick={() => {
                                setPaymentData({
                                  ...paymentData,
                                  enrollment_id: enrollment.id,
                                  amount: balanceRemaining.toFixed(2)
                                });
                                setShowAddPayment(true);
                              }}
                              className="pay-balance-btn"
                              title="Pay Balance"
                            >
                              💳 Pay ${balanceRemaining.toFixed(0)}
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Show recent payments */}
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
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Lesson History Section */}
              <div className="activity-section">
                <h5>📚 Lesson History</h5>
                <button 
                  onClick={() => {
                    if (!showLessonHistory) {
                      fetchLessonHistory();
                    }
                    setShowLessonHistory(!showLessonHistory);
                  }}
                  className="toggle-history-btn"
                >
                  {showLessonHistory ? '📖 Hide History' : '📋 View All Lessons'}
                </button>
                
                {showLessonHistory && lessonHistory && (
                  <div className="lesson-history-list">
                    <div className="history-summary">
                      <span>Total: {lessonHistory.total_lessons}</span>
                      <span>Attended: {lessonHistory.attended_lessons}</span>
                      <span>Upcoming: {lessonHistory.upcoming_lessons}</span>
                    </div>
                    
                    {lessonHistory.lessons.slice(0, 10).map((historyLesson, index) => (
                      <div key={index} className={`lesson-history-item ${historyLesson.is_past ? 'past' : 'future'} ${historyLesson.is_attended ? 'attended' : ''}`}>
                        <div className="lesson-history-details">
                          <div className="lesson-date-time">
                            <span className="lesson-date">{new Date(historyLesson.start_datetime).toLocaleDateString()}</span>
                            <span className="lesson-time">{new Date(historyLesson.start_datetime).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}</span>
                          </div>
                          <div className="lesson-info">
                            <span className="lesson-type">{historyLesson.booking_type?.replace('_', ' ')}</span>
                            {historyLesson.teacher_names?.length > 0 && (
                              <span className="lesson-teacher">{historyLesson.teacher_names.join(', ')}</span>
                            )}
                          </div>
                        </div>
                        
                        <div className="lesson-history-actions">
                          <button 
                            onClick={() => handleNavigateToLesson(historyLesson.date_only)}
                            className="navigate-btn"
                            title="Go to this day"
                          >
                            📅
                          </button>
                          
                          {historyLesson.is_past && !historyLesson.is_attended && historyLesson.status !== 'cancelled' && (
                            <button 
                              onClick={() => handleMarkLessonAttended(historyLesson.id, historyLesson.date_only)}
                              className="attend-btn"
                              title="Mark as attended"
                            >
                              ✅
                            </button>
                          )}
                          
                          {historyLesson.is_attended && (
                            <span className="attended-badge" title="Attended">✅</span>
                          )}
                          
                          {historyLesson.status === 'cancelled' && (
                            <span className="cancelled-badge" title="Cancelled">❌</span>
                          )}
                        </div>
                      </div>
                    ))}
                    
                    {lessonHistory.lessons.length > 10 && (
                      <div className="more-lessons-notice">
                        Showing 10 of {lessonHistory.lessons.length} lessons
                      </div>
                    )}
                  </div>
                )}
              </div>

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

      {/* Enhanced Payment Form */}
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
            <select
              value={paymentData.enrollment_id}
              onChange={(e) => setPaymentData({...paymentData, enrollment_id: e.target.value})}
            >
              <option value="">General Payment (Auto-Apply)</option>
              {ledgerData?.enrollments?.filter(e => e.is_active).map((enrollment) => {
                const grandTotal = (enrollment.total_lessons || 0) * (enrollment.price_per_lesson || 50);
                const amountPaid = enrollment.amount_paid || 0;
                const balance = grandTotal - amountPaid;
                
                return (
                  <option key={enrollment.id} value={enrollment.id}>
                    {enrollment.program_name} - Balance: ${balance.toFixed(2)}
                  </option>
                );
              })}
            </select>
            <input
              type="text"
              value={paymentData.notes}
              onChange={(e) => setPaymentData({...paymentData, notes: e.target.value})}
              placeholder="Notes (optional)"
            />
            <div className="form-actions">
              <button type="submit" className="submit-btn">Add Payment</button>
              <button type="button" onClick={() => setShowAddPayment(false)} className="cancel-btn">Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Enhanced Enrollment Form */}
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
              value={enrollmentData.price_per_lesson}
              onChange={(e) => setEnrollmentData({...enrollmentData, price_per_lesson: e.target.value})}
              placeholder="Price per lesson ($)"
              required
            />
            <div className="enrollment-total">
              <span>Total Cost: ${(parseFloat(enrollmentData.total_lessons || 0) * parseFloat(enrollmentData.price_per_lesson || 0)).toFixed(2)}</span>
            </div>
            <input
              type="number"
              step="0.01"
              value={enrollmentData.initial_payment}
              onChange={(e) => setEnrollmentData({
                ...enrollmentData, 
                initial_payment: e.target.value,
                total_paid: e.target.value
              })}
              placeholder="Initial payment ($)"
            />
            <div className="lessons-available-preview">
              <span>Lessons Available: {Math.floor(parseFloat(enrollmentData.initial_payment || 0) / parseFloat(enrollmentData.price_per_lesson || 1))}</span>
            </div>
            <div className="form-actions">
              <button type="submit" className="submit-btn">Add Enrollment</button>
              <button type="button" onClick={() => setShowAddEnrollment(false)} className="cancel-btn">Cancel</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default StudentLedgerPanel;