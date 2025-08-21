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
  const [filteredLessons, setFilteredLessons] = useState([]);
  const [selectedLessons, setSelectedLessons] = useState([]);
  const [sending, setSending] = useState(false);
  const [notificationSettings, setNotificationSettings] = useState({
    lesson_reminders_enabled: true,
    payment_reminders_enabled: true,
    custom_emails_enabled: true,
    default_recipient: 'parent', // 'parent', 'student', 'both'
    auto_send_reminders: false
  });
  const [lessonFilter, setLessonFilter] = useState({
    dateRange: 'next_7_days', // 'today', 'tomorrow', 'next_7_days', 'next_30_days'
    lessonType: 'all',
    instructor: 'all',
    hasEmail: 'all' // 'all', 'parent_email', 'student_email', 'both_emails', 'no_email'
  });
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');

  useEffect(() => {
    fetchStudents();
    fetchLessons();
    loadNotificationSettings();
  }, []);

  useEffect(() => {
    applyLessonFilters();
  }, [lessons, lessonFilter]);

  const loadNotificationSettings = async () => {
    try {
      const savedSettings = localStorage.getItem('notification_settings');
      if (savedSettings) {
        setNotificationSettings(JSON.parse(savedSettings));
      }
    } catch (error) {
      console.error('Failed to load notification settings:', error);
    }
  };

  const saveNotificationSettings = (newSettings) => {
    setNotificationSettings(newSettings);
    localStorage.setItem('notification_settings', JSON.stringify(newSettings));
    showMessage('Notification settings saved successfully!');
  };

  const applyLessonFilters = () => {
    let filtered = [...lessons];

    // Filter by date range
    const now = new Date();
    switch (lessonFilter.dateRange) {
      case 'today':
        const todayStart = new Date(now);
        todayStart.setHours(0, 0, 0, 0);
        const todayEnd = new Date(now);
        todayEnd.setHours(23, 59, 59, 999);
        filtered = filtered.filter(lesson => {
          const lessonDate = new Date(lesson.start_datetime);
          return lessonDate >= todayStart && lessonDate <= todayEnd;
        });
        break;
      case 'tomorrow':
        const tomorrow = new Date(now);
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(0, 0, 0, 0);
        const tomorrowEnd = new Date(tomorrow);
        tomorrowEnd.setHours(23, 59, 59, 999);
        filtered = filtered.filter(lesson => {
          const lessonDate = new Date(lesson.start_datetime);
          return lessonDate >= tomorrow && lessonDate <= tomorrowEnd;
        });
        break;
      case 'next_7_days':
        const nextWeek = new Date(now.getTime() + (7 * 24 * 60 * 60 * 1000));
        filtered = filtered.filter(lesson => {
          const lessonDate = new Date(lesson.start_datetime);
          return lessonDate >= now && lessonDate <= nextWeek;
        });
        break;
      case 'next_30_days':
        const nextMonth = new Date(now.getTime() + (30 * 24 * 60 * 60 * 1000));
        filtered = filtered.filter(lesson => {
          const lessonDate = new Date(lesson.start_datetime);
          return lessonDate >= now && lessonDate <= nextMonth;
        });
        break;
    }

    // Filter by lesson type
    if (lessonFilter.lessonType !== 'all') {
      filtered = filtered.filter(lesson => lesson.booking_type === lessonFilter.lessonType);
    }

    // Filter by instructor
    if (lessonFilter.instructor !== 'all') {
      filtered = filtered.filter(lesson => 
        lesson.teacher_ids && lesson.teacher_ids.includes(lessonFilter.instructor)
      );
    }

    // Filter by email availability
    if (lessonFilter.hasEmail !== 'all') {
      filtered = filtered.filter(lesson => {
        const student = students.find(s => s.id === lesson.student_id);
        if (!student) return false;

        const hasParentEmail = !!student.parent_email;
        const hasStudentEmail = !!student.email;

        switch (lessonFilter.hasEmail) {
          case 'parent_email':
            return hasParentEmail;
          case 'student_email':
            return hasStudentEmail;
          case 'both_emails':
            return hasParentEmail && hasStudentEmail;
          case 'no_email':
            return !hasParentEmail && !hasStudentEmail;
          default:
            return true;
        }
      });
    }

    setFilteredLessons(filtered);
  };

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

  const handleSendLessonReminder = async (lessonId, recipientType = 'auto') => {
    setSending(true);
    try {
      let sendToParent = true;
      
      if (recipientType === 'parent') {
        sendToParent = true;
      } else if (recipientType === 'student') {
        sendToParent = false;
      } else if (recipientType === 'auto') {
        sendToParent = notificationSettings.default_recipient === 'parent';
      }

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

  const handleBulkSendReminders = async (recipientType = 'auto') => {
    if (selectedLessons.length === 0) {
      showMessage('Please select lessons to send reminders for', 'error');
      return;
    }

    setSending(true);
    try {
      const results = await Promise.allSettled(
        selectedLessons.map(lessonId => 
          handleSendLessonReminder(lessonId, recipientType)
        )
      );

      const successful = results.filter(r => r.status === 'fulfilled').length;
      showMessage(`Bulk reminders sent: ${successful}/${selectedLessons.length} successful`);
      setSelectedLessons([]);
    } catch (error) {
      showMessage('Failed to send bulk reminders: ' + error.message, 'error');
    } finally {
      setSending(false);
    }
  };

  const toggleLessonSelection = (lessonId) => {
    setSelectedLessons(prev => 
      prev.includes(lessonId) 
        ? prev.filter(id => id !== lessonId)
        : [...prev, lessonId]
    );
  };

  const toggleAllLessons = () => {
    if (selectedLessons.length === filteredLessons.length) {
      setSelectedLessons([]);
    } else {
      setSelectedLessons(filteredLessons.map(lesson => lesson.id));
    }
  };

  const getRecipientInfo = (lesson) => {
    const student = students.find(s => s.id === lesson.student_id);
    if (!student) return { hasParent: false, hasStudent: false, parentName: '', studentName: '' };

    return {
      hasParent: !!student.parent_email,
      hasStudent: !!student.email,
      parentName: student.parent_name || 'Parent',
      studentName: student.name || 'Student',
      parentEmail: student.parent_email,
      studentEmail: student.email
    };
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

      {/* Notification Settings Section */}
      <div className="notification-section">
        <h3>⚙️ Notification Preferences</h3>
        <p>Control which notifications are enabled and set default recipients.</p>
        
        <div className="settings-grid">
          <div className="setting-group">
            <label className="setting-checkbox">
              <input
                type="checkbox"
                checked={notificationSettings.lesson_reminders_enabled}
                onChange={(e) => saveNotificationSettings({
                  ...notificationSettings,
                  lesson_reminders_enabled: e.target.checked
                })}
              />
              <span>Enable Lesson Reminders</span>
            </label>
          </div>
          
          <div className="setting-group">
            <label className="setting-checkbox">
              <input
                type="checkbox"
                checked={notificationSettings.payment_reminders_enabled}
                onChange={(e) => saveNotificationSettings({
                  ...notificationSettings,
                  payment_reminders_enabled: e.target.checked
                })}
              />
              <span>Enable Payment Reminders</span>
            </label>
          </div>
          
          <div className="setting-group">
            <label>Default Recipient:</label>
            <select
              value={notificationSettings.default_recipient}
              onChange={(e) => saveNotificationSettings({
                ...notificationSettings,
                default_recipient: e.target.value
              })}
              className="input"
            >
              <option value="parent">Parent (when available)</option>
              <option value="student">Student</option>
            </select>
          </div>
        </div>
      </div>

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
      {notificationSettings.lesson_reminders_enabled && (
        <div className="notification-section">
          <h3>⏰ Lesson Reminders</h3>
          <p>Filter and send reminders for upcoming lessons with full control over recipients.</p>
          
          {/* Lesson Filters */}
          <div className="filter-controls-section">
            <h4>📋 Filter Lessons</h4>
            <div className="filter-grid">
              <div className="filter-group">
                <label>Date Range:</label>
                <select
                  value={lessonFilter.dateRange}
                  onChange={(e) => setLessonFilter({...lessonFilter, dateRange: e.target.value})}
                  className="input"
                >
                  <option value="today">Today Only</option>
                  <option value="tomorrow">Tomorrow Only</option>
                  <option value="next_7_days">Next 7 Days</option>
                  <option value="next_30_days">Next 30 Days</option>
                </select>
              </div>
              
              <div className="filter-group">
                <label>Lesson Type:</label>
                <select
                  value={lessonFilter.lessonType}
                  onChange={(e) => setLessonFilter({...lessonFilter, lessonType: e.target.value})}
                  className="input"
                >
                  <option value="all">All Types</option>
                  <option value="private_lesson">Private Lesson</option>
                  <option value="meeting">Meeting</option>
                  <option value="training">Training</option>
                  <option value="party">Party</option>
                </select>
              </div>
              
              <div className="filter-group">
                <label>Email Available:</label>
                <select
                  value={lessonFilter.hasEmail}
                  onChange={(e) => setLessonFilter({...lessonFilter, hasEmail: e.target.value})}
                  className="input"
                >
                  <option value="all">All Students</option>
                  <option value="parent_email">Has Parent Email</option>
                  <option value="student_email">Has Student Email</option>
                  <option value="both_emails">Has Both Emails</option>
                  <option value="no_email">No Email Available</option>
                </select>
              </div>
            </div>
          </div>

          {/* Bulk Actions */}
          {filteredLessons.length > 0 && (
            <div className="bulk-actions-section">
              <div className="bulk-controls">
                <label className="bulk-select-all">
                  <input
                    type="checkbox"
                    checked={selectedLessons.length === filteredLessons.length && filteredLessons.length > 0}
                    onChange={toggleAllLessons}
                  />
                  <span>Select All ({filteredLessons.length} lessons)</span>
                </label>
                
                {selectedLessons.length > 0 && (
                  <div className="bulk-action-buttons">
                    <span className="selected-count">{selectedLessons.length} selected</span>
                    <button
                      onClick={() => handleBulkSendReminders('parent')}
                      className="btn btn-outline btn-sm"
                      disabled={sending}
                    >
                      📧 Send to Parents
                    </button>
                    <button
                      onClick={() => handleBulkSendReminders('student')}
                      className="btn btn-outline btn-sm"
                      disabled={sending}
                    >
                      📧 Send to Students
                    </button>
                    <button
                      onClick={() => setSelectedLessons([])}
                      className="btn btn-outline btn-sm"
                    >
                      Clear Selection
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {filteredLessons.length === 0 ? (
            <div className="empty-state">
              <p>📅 No lessons found with current filters</p>
              <p>Try adjusting your date range or filters above.</p>
            </div>
          ) : (
            <div className="lessons-list">
              <div className="lessons-header">
                <h4>Found {filteredLessons.length} lessons</h4>
              </div>
              {filteredLessons.slice(0, 20).map(lesson => {
                const recipientInfo = getRecipientInfo(lesson);
                return (
                  <div key={lesson.id} className={`lesson-reminder-card ${selectedLessons.includes(lesson.id) ? 'selected' : ''}`}>
                    <div className="lesson-card-header">
                      <label className="lesson-checkbox">
                        <input
                          type="checkbox"
                          checked={selectedLessons.includes(lesson.id)}
                          onChange={() => toggleLessonSelection(lesson.id)}
                        />
                      </label>
                      <div className="lesson-info">
                        <h4>{lesson.student_name}</h4>
                        <p><strong>Type:</strong> {lesson.booking_type?.replace('_', ' ')}</p>
                        <p><strong>Time:</strong> {new Date(lesson.start_datetime).toLocaleString()}</p>
                        <p><strong>Instructors:</strong> {lesson.teacher_names?.join(', ') || 'TBD'}</p>
                      </div>
                    </div>
                    
                    <div className="recipient-info">
                      <div className="available-recipients">
                        {recipientInfo.hasParent && (
                          <span className="recipient-tag parent">
                            👨‍👩‍👧 {recipientInfo.parentName}: {recipientInfo.parentEmail}
                          </span>
                        )}
                        {recipientInfo.hasStudent && (
                          <span className="recipient-tag student">
                            👤 {recipientInfo.studentName}: {recipientInfo.studentEmail}
                          </span>
                        )}
                        {!recipientInfo.hasParent && !recipientInfo.hasStudent && (
                          <span className="recipient-tag no-email">❌ No email available</span>
                        )}
                      </div>
                    </div>
                    
                    <div className="lesson-actions">
                      {recipientInfo.hasParent && (
                        <button
                          onClick={() => handleSendLessonReminder(lesson.id, 'parent')}
                          className="btn btn-outline btn-sm"
                          disabled={sending}
                        >
                          📧 Parent
                        </button>
                      )}
                      {recipientInfo.hasStudent && (
                        <button
                          onClick={() => handleSendLessonReminder(lesson.id, 'student')}
                          className="btn btn-outline btn-sm"
                          disabled={sending}
                        >
                          📧 Student
                        </button>
                      )}
                      {!recipientInfo.hasParent && !recipientInfo.hasStudent && (
                        <span className="no-action">No email to send to</span>
                      )}
                    </div>
                  </div>
                );
              })}
              {filteredLessons.length > 20 && (
                <p className="more-lessons">+ {filteredLessons.length - 20} more lessons (showing first 20)</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Payment Reminders Section */}
      {notificationSettings.payment_reminders_enabled && (
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