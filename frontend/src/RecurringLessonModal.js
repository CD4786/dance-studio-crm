import React, { useState, useEffect } from 'react';

const RecurringLessonModal = ({ 
  isOpen, 
  onClose, 
  onSubmit, 
  students, 
  teachers, 
  selectedSlot = null 
}) => {
  const [formData, setFormData] = useState({
    student_id: '',
    teacher_id: '',
    start_datetime: '',
    duration_minutes: 60,
    recurrence_pattern: 'weekly',
    end_date: '',
    max_occurrences: '',
    notes: '',
    enrollment_id: ''
  });

  const [errors, setErrors] = useState({});
  const [previewLessons, setPreviewLessons] = useState([]);

  useEffect(() => {
    if (selectedSlot) {
      setFormData(prev => ({
        ...prev,
        start_datetime: selectedSlot.datetime,
        teacher_id: selectedSlot.teacherId || ''
      }));
    }
  }, [selectedSlot]);

  // Generate preview of recurring lessons
  useEffect(() => {
    if (formData.start_datetime && formData.recurrence_pattern) {
      generatePreview();
    }
  }, [formData.start_datetime, formData.recurrence_pattern, formData.end_date, formData.max_occurrences]);

  const generatePreview = () => {
    const lessons = [];
    const startDate = new Date(formData.start_datetime);
    const endDate = formData.end_date ? new Date(formData.end_date) : null;
    const maxOccurrences = formData.max_occurrences ? parseInt(formData.max_occurrences) : null;
    
    let currentDate = new Date(startDate);
    let count = 0;

    while (count < (maxOccurrences || 10)) {
      if (endDate && currentDate > endDate) break;
      
      lessons.push({
        date: new Date(currentDate),
        formattedDate: currentDate.toLocaleDateString(),
        formattedTime: currentDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      });

      // Calculate next occurrence
      if (formData.recurrence_pattern === 'weekly') {
        currentDate.setDate(currentDate.getDate() + 7);
      } else if (formData.recurrence_pattern === 'bi_weekly') {
        currentDate.setDate(currentDate.getDate() + 14);
      } else if (formData.recurrence_pattern === 'monthly') {
        currentDate.setMonth(currentDate.getMonth() + 1);
      }

      count++;
      if (count > 52) break; // Safety limit
    }

    setPreviewLessons(lessons);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validation
    const newErrors = {};
    if (!formData.student_id) newErrors.student_id = 'Student is required';
    if (!formData.teacher_id) newErrors.teacher_id = 'Teacher is required';
    if (!formData.start_datetime) newErrors.start_datetime = 'Start date/time is required';
    
    if (!formData.end_date && !formData.max_occurrences) {
      newErrors.end_condition = 'Either end date or max occurrences is required';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    // Convert form data to API format
    const submitData = {
      ...formData,
      start_datetime: formData.start_datetime, // Keep as local datetime string
      end_date: formData.end_date || null,
      max_occurrences: formData.max_occurrences ? parseInt(formData.max_occurrences) : null,
      duration_minutes: parseInt(formData.duration_minutes)
    };

    onSubmit(submitData);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  // Auto-fill presets for common recurring patterns
  const applyPreset = (presetType) => {
    const currentDate = new Date();
    const nextWeek = new Date(currentDate);
    nextWeek.setDate(currentDate.getDate() + 7);
    
    const presets = {
      'weekly_4': {
        recurrence_pattern: 'weekly',
        max_occurrences: '4',
        end_date: '',
        notes: 'Weekly lessons for 4 weeks'
      },
      'weekly_8': {
        recurrence_pattern: 'weekly',
        max_occurrences: '8',
        end_date: '',
        notes: 'Weekly lessons for 8 weeks (2 months)'
      },
      'weekly_12': {
        recurrence_pattern: 'weekly',
        max_occurrences: '12',
        end_date: '',
        notes: 'Weekly lessons for 12 weeks (3 months)'
      },
      'biweekly_6': {
        recurrence_pattern: 'bi_weekly',
        max_occurrences: '6',
        end_date: '',
        notes: 'Bi-weekly lessons for 6 sessions (3 months)'
      },
      'monthly_6': {
        recurrence_pattern: 'monthly',
        max_occurrences: '6',
        end_date: '',
        notes: 'Monthly lessons for 6 months'
      },
      'school_year': {
        recurrence_pattern: 'weekly',
        max_occurrences: '36',
        end_date: '',
        notes: 'Weekly lessons for school year (36 weeks)'
      }
    };

    if (presets[presetType]) {
      setFormData(prev => ({
        ...prev,
        ...presets[presetType]
      }));
      
      // Clear errors when applying preset
      setErrors({});
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-90vh overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-white">Create Recurring Lessons</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl"
          >
            ×
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Form */}
          <div>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Student Selection */}
              <div>
                <label className="block text-white mb-2">Student *</label>
                <select
                  name="student_id"
                  value={formData.student_id}
                  onChange={handleChange}
                  className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                >
                  <option value="">Select a student</option>
                  {students.map(student => (
                    <option key={student.id} value={student.id}>
                      {student.name}
                    </option>
                  ))}
                </select>
                {errors.student_id && <p className="text-red-500 text-sm mt-1">{errors.student_id}</p>}
              </div>

              {/* Teacher Selection */}
              <div>
                <label className="block text-white mb-2">Teacher *</label>
                <select
                  name="teacher_id"
                  value={formData.teacher_id}
                  onChange={handleChange}
                  className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                >
                  <option value="">Select a teacher</option>
                  {teachers.map(teacher => (
                    <option key={teacher.id} value={teacher.id}>
                      {teacher.name}
                    </option>
                  ))}
                </select>
                {errors.teacher_id && <p className="text-red-500 text-sm mt-1">{errors.teacher_id}</p>}
              </div>

              {/* Start DateTime */}
              <div>
                <label className="block text-white mb-2">Start Date & Time *</label>
                <input
                  type="datetime-local"
                  name="start_datetime"
                  value={formData.start_datetime}
                  onChange={handleChange}
                  className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                />
                {errors.start_datetime && <p className="text-red-500 text-sm mt-1">{errors.start_datetime}</p>}
              </div>

              {/* Duration */}
              <div>
                <label className="block text-white mb-2">Duration (minutes)</label>
                <input
                  type="number"
                  name="duration_minutes"
                  value={formData.duration_minutes}
                  onChange={handleChange}
                  min="15"
                  max="180"
                  step="15"
                  className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                />
              </div>

              {/* Recurrence Pattern */}
              <div>
                <label className="block text-white mb-2">Recurrence Pattern</label>
                <select
                  name="recurrence_pattern"
                  value={formData.recurrence_pattern}
                  onChange={handleChange}
                  className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                >
                  <option value="weekly">Weekly</option>
                  <option value="bi_weekly">Bi-weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>

              {/* End Conditions */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-white mb-2">End Date</label>
                  <input
                    type="date"
                    name="end_date"
                    value={formData.end_date}
                    onChange={handleChange}
                    className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-white mb-2">Max Occurrences</label>
                  <input
                    type="number"
                    name="max_occurrences"
                    value={formData.max_occurrences}
                    onChange={handleChange}
                    min="1"
                    max="100"
                    placeholder="e.g., 10"
                    className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
                  />
                </div>
              </div>
              {errors.end_condition && <p className="text-red-500 text-sm mt-1">{errors.end_condition}</p>}

              {/* Notes */}
              <div>
                <label className="block text-white mb-2">Notes</label>
                <textarea
                  name="notes"
                  value={formData.notes}
                  onChange={handleChange}
                  rows="3"
                  className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none resize-none"
                  placeholder="Any special notes or requirements..."
                />
              </div>

              {/* Submit Buttons */}
              <div className="flex gap-4 pt-4">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 py-3 px-6 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-3 px-6 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all"
                >
                  Create Recurring Lessons
                </button>
              </div>
            </form>
          </div>

          {/* Preview */}
          <div>
            <h3 className="text-xl font-bold text-white mb-4">Lesson Preview</h3>
            
            {previewLessons.length > 0 ? (
              <div className="bg-gray-700 rounded-lg p-4 max-h-96 overflow-y-auto">
                <p className="text-gray-300 mb-3">
                  {previewLessons.length} lesson{previewLessons.length !== 1 ? 's' : ''} will be created:
                </p>
                <div className="space-y-2">
                  {previewLessons.slice(0, 10).map((lesson, index) => (
                    <div key={index} className="flex justify-between items-center p-2 bg-gray-600 rounded">
                      <span className="text-white">{lesson.formattedDate}</span>
                      <span className="text-purple-300">{lesson.formattedTime}</span>
                    </div>
                  ))}
                  {previewLessons.length > 10 && (
                    <div className="text-center text-gray-400 p-2">
                      ... and {previewLessons.length - 10} more lessons
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-gray-700 rounded-lg p-4 text-center text-gray-400">
                Fill in the start date and recurrence pattern to see preview
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecurringLessonModal;