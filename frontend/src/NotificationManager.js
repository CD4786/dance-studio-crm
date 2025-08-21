import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const NotificationManager = () => {
  const [testEmail, setTestEmail] = useState('');
  const [customEmail, setCustomEmail] = useState({
    recipient_email: '',
    subject: '',
    message: ''
  });
  const [paymentReminder, setPaymentReminder] = useState({
    student_id: '',
    amount_due: '',
    due_date: ''
  });
  const [students, setStudents] = useState([]);
  const [lessons, setLessons] = useState([]);
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');

  useEffect(() => {
    fetchStudents();
    fetchLessons();
  }, []);

  const fetchStudents = async () => {
    try {
      const response = await axios.get(`${API}/students`);
      setStudents(response.data);
    } catch (error) {
      console.error('Failed to fetch students:', error);
    }
  };

  const fetchLessons = async () => {
    try {
      const response = await axios.get(`${API}/lessons`);
      // Filter for upcoming lessons (next 7 days)
      const today = new Date();
      const nextWeek = new Date(today.getTime() + (7 * 24 * 60 * 60 * 1000));
      
      const upcomingLessons = response.data.filter(lesson => {
        const lessonDate = new Date(lesson.start_datetime);
        return lessonDate >= today && lessonDate <= nextWeek;
      });
      
      setLessons(upcomingLessons);
    } catch (error) {
      console.error('Failed to fetch lessons:', error);
    }
  };

  const showMessage = (msg, type = 'success') => {
    setMessage(msg);
    setMessageType(type);
    setTimeout(() => {
      setMessage('');
      setMessageType('');
    }, 5000);
  };

  const handleSendTestEmail = async (e) => {
    e.preventDefault();
    if (!testEmail.trim()) {
      showMessage('Please enter a valid email address', 'error');
      return;
    }

    setSending(true);
    try {
      await axios.post(`${API}/notifications/test-email`, {
        test_email: testEmail
      });
      showMessage('Test email sent successfully! Check your inbox.');
      setTestEmail('');
    } catch (error) {
      showMessage('Failed to send test email: ' + (error.response?.data?.detail || error.message), 'error');
    } finally {
      setSending(false);
    }
  };

  const handleSendCustomEmail = async (e) => {
    e.preventDefault();
    if (!customEmail.recipient_email || !customEmail.subject || !customEmail.message) {
      showMessage('Please fill in all fields', 'error');
      return;
    }

    setSending(true);
    try {
      await axios.post(`${API}/notifications/custom-email`, {
        recipient_email: customEmail.recipient_email,
        subject: customEmail.subject,
        message: customEmail.message,
        notification_type: 'custom'
      });
      showMessage('Custom email sent successfully!');
      setCustomEmail({ recipient_email: '', subject: '', message: '' });
    } catch (error) {
      showMessage('Failed to send email: ' + (error.response?.data?.detail || error.message), 'error');
    } finally {
      setSending(false);
    }
  };

  const handleSendPaymentReminder = async (e) => {
    e.preventDefault();
    if (!paymentReminder.student_id || !paymentReminder.amount_due || !paymentReminder.due_date) {
      showMessage('Please fill in all fields', 'error');
      return;
    }

    setSending(true);
    try {
      await axios.post(`${API}/notifications/payment-reminder`, {
        student_id: paymentReminder.student_id,
        amount_due: parseFloat(paymentReminder.amount_due),
        due_date: new Date(paymentReminder.due_date).toISOString()
      });
      showMessage('Payment reminder sent successfully!');
      setPaymentReminder({ student_id: '', amount_due: '', due_date: '' });
    } catch (error) {
      showMessage('Failed to send payment reminder: ' + (error.response?.data?.detail || error.message), 'error');
    } finally {
      setSending(false);
    }
  };

  const handleSendLessonReminder = async (lessonId, sendToParent = true) => {
    setSending(true);
    try {
      await axios.post(`${API}/notifications/lesson-reminder`, {
        lesson_id: lessonId,
        send_to_parent: sendToParent
      });
      showMessage('Lesson reminder sent successfully!');
    } catch (error) {
      showMessage('Failed to send lesson reminder: ' + (error.response?.data?.detail || error.message), 'error');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="notification-manager">
      <div className="notification-header">
        <h2>📧 Notification Center</h2>
        <p>Manage and send email notifications to students and parents</p>
      </div>

      {/* Message Display */}
      {message && (
        <div className={`notification-message ${messageType === 'error' ? 'error' : 'success'}`}>
          {message}
        </div>
      )}

      {/* Test Email Section */}
      <div className="notification-section">
        <h3>🧪 Test Email System</h3>
        <p>Send a test email to verify your email system is working correctly.</p>
        <form onSubmit={handleSendTestEmail} className="notification-form">
          <div className="form-group">
            <label>Test Email Address:</label>
            <input
              type="email"
              value={testEmail}
              onChange={(e) => setTestEmail(e.target.value)}
              placeholder="Enter your email address"
              className="input"
              required
            />
          </div>
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={sending}
          >
            {sending ? '📤 Sending...' : '🧪 Send Test Email'}
          </button>
        </form>
      </div>

      {/* Lesson Reminders Section */}
      <div className="notification-section">
        <h3>⏰ Upcoming Lesson Reminders</h3>
        <p>Send reminders for lessons in the next 7 days.</p>
        
        {lessons.length === 0 ? (
          <div className="empty-state">
            <p>📅 No upcoming lessons in the next 7 days</p>
          </div>
        ) : (
          <div className="lessons-list">
            {lessons.slice(0, 10).map(lesson => (
              <div key={lesson.id} className="lesson-reminder-card">
                <div className="lesson-info">
                  <h4>{lesson.student_name}</h4>
                  <p><strong>Type:</strong> {lesson.booking_type?.replace('_', ' ')}</p>
                  <p><strong>Time:</strong> {new Date(lesson.start_datetime).toLocaleString()}</p>
                  <p><strong>Instructors:</strong> {lesson.teacher_names?.join(', ') || 'TBD'}</p>
                </div>
                <div className="lesson-actions">
                  <button
                    onClick={() => handleSendLessonReminder(lesson.id, true)}
                    className="btn btn-outline btn-sm"
                    disabled={sending}
                  >
                    📧 Parent
                  </button>
                  <button
                    onClick={() => handleSendLessonReminder(lesson.id, false)}
                    className="btn btn-outline btn-sm"
                    disabled={sending}
                  >
                    📧 Student
                  </button>
                </div>
              </div>
            ))}
            {lessons.length > 10 && (
              <p className="more-lessons">+ {lessons.length - 10} more lessons</p>
            )}
          </div>
        )}
      </div>

      {/* Payment Reminders Section */}
      <div className="notification-section">
        <h3>💳 Payment Reminders</h3>
        <p>Send payment due notices to students or parents.</p>
        <form onSubmit={handleSendPaymentReminder} className="notification-form">
          <div className="form-row">
            <div className="form-group">
              <label>Student:</label>
              <select
                value={paymentReminder.student_id}
                onChange={(e) => setPaymentReminder({...paymentReminder, student_id: e.target.value})}
                className="input"
                required
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
              <label>Amount Due:</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={paymentReminder.amount_due}
                onChange={(e) => setPaymentReminder({...paymentReminder, amount_due: e.target.value})}
                placeholder="0.00"
                className="input"
                required
              />
            </div>
            <div className="form-group">
              <label>Due Date:</label>
              <input
                type="date"
                value={paymentReminder.due_date}
                onChange={(e) => setPaymentReminder({...paymentReminder, due_date: e.target.value})}
                className="input"
                required
              />
            </div>
          </div>
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={sending}
          >
            {sending ? '📤 Sending...' : '💳 Send Payment Reminder'}
          </button>
        </form>
      </div>

      {/* Custom Email Section */}
      <div className="notification-section">
        <h3>✉️ Custom Email</h3>
        <p>Send a custom email notification with your own message.</p>
        <form onSubmit={handleSendCustomEmail} className="notification-form">
          <div className="form-group">
            <label>Recipient Email:</label>
            <input
              type="email"
              value={customEmail.recipient_email}
              onChange={(e) => setCustomEmail({...customEmail, recipient_email: e.target.value})}
              placeholder="recipient@example.com"
              className="input"
              required
            />
          </div>
          <div className="form-group">
            <label>Subject:</label>
            <input
              type="text"
              value={customEmail.subject}
              onChange={(e) => setCustomEmail({...customEmail, subject: e.target.value})}
              placeholder="Email subject"
              className="input"
              required
            />
          </div>
          <div className="form-group">
            <label>Message:</label>
            <textarea
              value={customEmail.message}
              onChange={(e) => setCustomEmail({...customEmail, message: e.target.value})}
              placeholder="Type your message here..."
              className="input textarea"
              rows="6"
              required
            />
          </div>
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={sending}
          >
            {sending ? '📤 Sending...' : '✉️ Send Custom Email'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default NotificationManager;