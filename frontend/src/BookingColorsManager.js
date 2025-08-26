import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BookingColorsManager = () => {
  const [bookingSettings, setBookingSettings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const API = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  // Color setting definitions with user-friendly labels
  const colorSettings = [
    { key: 'private_lesson_color', label: 'Private Lesson', description: 'Color for private lesson bookings' },
    { key: 'meeting_color', label: 'Meeting', description: 'Color for meeting bookings' },
    { key: 'training_color', label: 'Training', description: 'Color for training session bookings' },
    { key: 'party_color', label: 'Party', description: 'Color for party event bookings' },
    { key: 'confirmed_status_color', label: 'Confirmed Status', description: 'Color for confirmed bookings' },
    { key: 'pending_status_color', label: 'Pending Status', description: 'Color for pending bookings' },
    { key: 'cancelled_status_color', label: 'Cancelled Status', description: 'Color for cancelled bookings' }
  ];

  useEffect(() => {
    fetchBookingSettings();
  }, []);

  const fetchBookingSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings/booking`);
      setBookingSettings(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch booking settings:', error);
      setMessage('Failed to load booking color settings');
      setLoading(false);
    }
  };

  const updateColor = async (key, color) => {
    setSaving(true);
    try {
      await axios.put(`${API}/settings/booking/${key}`, {
        value: color,
        updated_by: 'current_user'
      });
      
      // Update local state
      setBookingSettings(prev => 
        prev.map(setting => 
          setting.key === key ? { ...setting, value: color } : setting
        )
      );
      
      setMessage('Color updated successfully!');
      
      // Apply the color change immediately to the UI
      applyColorToCSS(key, color);
      
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Failed to update color:', error);
      setMessage(error.response?.data?.detail || 'Failed to update color');
      setTimeout(() => setMessage(''), 5000);
    }
    setSaving(false);
  };

  const applyColorToCSS = (key, color) => {
    // Dynamically update CSS custom properties for immediate visual feedback
    const root = document.documentElement;
    
    switch (key) {
      case 'private_lesson_color':
        root.style.setProperty('--private-lesson-color', color);
        break;
      case 'meeting_color':
        root.style.setProperty('--meeting-color', color);
        break;
      case 'training_color':
        root.style.setProperty('--training-color', color);
        break;
      case 'party_color':
        root.style.setProperty('--party-color', color);
        break;
      case 'confirmed_status_color':
        root.style.setProperty('--confirmed-color', color);
        break;
      case 'pending_status_color':
        root.style.setProperty('--pending-color', color);
        break;
      case 'cancelled_status_color':
        root.style.setProperty('--cancelled-color', color);
        break;
    }
  };

  const getSettingValue = (key) => {
    const setting = bookingSettings.find(s => s.key === key);
    return setting?.value || '#3b82f6'; // Default blue color
  };

  const resetToDefaults = async () => {
    if (!window.confirm('Reset all booking colors to default values?')) return;
    
    setSaving(true);
    const defaultColors = {
      private_lesson_color: '#3b82f6',  // Blue
      meeting_color: '#22c55e',         // Green
      training_color: '#f59e0b',        // Orange
      party_color: '#a855f7',           // Purple
      confirmed_status_color: '#10b981',       // Emerald
      pending_status_color: '#f59e0b',         // Amber
      cancelled_status_color: '#ef4444'        // Red
    };

    try {
      for (const [key, color] of Object.entries(defaultColors)) {
        await axios.put(`${API}/settings/booking/${key}`, {
          value: color,
          updated_by: 'current_user'
        });
        applyColorToCSS(key, color);
      }
      
      await fetchBookingSettings();
      setMessage('All colors reset to defaults!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Failed to reset colors:', error);
      setMessage('Failed to reset colors');
      setTimeout(() => setMessage(''), 5000);
    }
    setSaving(false);
  };

  // Apply colors to CSS on component mount
  useEffect(() => {
    colorSettings.forEach(({ key }) => {
      const color = getSettingValue(key);
      applyColorToCSS(key, color);
    });
  }, [bookingSettings]);

  if (loading) {
    return <div className="loading">Loading booking color settings...</div>;
  }

  return (
    <div className="booking-colors-manager">
      <div className="section-header">
        <h3>🎨 Booking Colors</h3>
        <p>Customize colors for different booking types and statuses</p>
      </div>

      {message && (
        <div className={`message ${message.includes('Failed') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}

      <div className="colors-grid">
        {colorSettings.map(({ key, label, description }) => {
          const currentColor = getSettingValue(key);
          
          return (
            <div key={key} className="color-setting-card">
              <div className="color-preview-section">
                <div 
                  className="color-preview"
                  style={{ backgroundColor: currentColor }}
                  title={`Current color: ${currentColor}`}
                />
                <div className="color-input-section">
                  <input
                    type="color"
                    value={currentColor}
                    onChange={(e) => updateColor(key, e.target.value)}
                    disabled={saving}
                    className="color-picker"
                  />
                  <input
                    type="text"
                    value={currentColor}
                    onChange={(e) => {
                      if (/^#[0-9A-Fa-f]{6}$/.test(e.target.value)) {
                        updateColor(key, e.target.value);
                      }
                    }}
                    placeholder="#3b82f6"
                    className="hex-input"
                    disabled={saving}
                  />
                </div>
              </div>
              
              <div className="color-info">
                <h4>{label}</h4>
                <p>{description}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="actions-section">
        <button 
          onClick={resetToDefaults}
          className="reset-button"
          disabled={saving}
        >
          🔄 Reset to Defaults
        </button>
        
        <div className="info-section">
          <p>
            💡 <strong>Tip:</strong> Colors will be applied immediately to booking displays throughout the application.
          </p>
        </div>
      </div>
    </div>
  );
};

export default BookingColorsManager;