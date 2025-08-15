import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const SettingsPage = () => {
  const [settings, setSettings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('business');
  const [formData, setFormData] = useState({});
  const [message, setMessage] = useState('');

  const tabs = [
    { id: 'business', name: 'Business Settings', icon: '🏢' },
    { id: 'system', name: 'System Settings', icon: '⚙️' },
    { id: 'theme', name: 'Theme & Appearance', icon: '🎨' },
    { id: 'booking', name: 'Booking Colors', icon: '🎯' },
    { id: 'calendar', name: 'Calendar Settings', icon: '📅' },
    { id: 'display', name: 'Display Settings', icon: '🖥️' },
    { id: 'business_rules', name: 'Business Rules', icon: '📋' },
    { id: 'program', name: 'Program Settings', icon: '📚' },
    { id: 'notification', name: 'Notifications', icon: '🔔' }
  ];

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/settings`);
      setSettings(response.data);
      
      // Initialize form data
      const initialFormData = {};
      response.data.forEach(setting => {
        if (!initialFormData[setting.category]) {
          initialFormData[setting.category] = {};
        }
        initialFormData[setting.category][setting.key] = setting.value;
      });
      setFormData(initialFormData);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
      setMessage('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (category, key, value) => {
    setFormData(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
  };

  const handleArrayChange = (category, key, value) => {
    // Convert string to array (split by newlines)
    const arrayValue = value.split('\n').filter(item => item.trim() !== '');
    handleInputChange(category, key, arrayValue);
  };

  const handleSaveSetting = async (category, key) => {
    try {
      setSaving(true);
      const value = formData[category]?.[key];
      
      await axios.put(`${API}/settings/${category}/${key}`, {
        value: value
      });
      
      setMessage('Setting saved successfully!');
      setTimeout(() => setMessage(''), 3000);
      
      // Refresh settings to get updated timestamp
      fetchSettings();
    } catch (error) {
      console.error('Failed to save setting:', error);
      setMessage('Failed to save setting: ' + (error.response?.data?.detail || error.message));
      setTimeout(() => setMessage(''), 5000);
    } finally {
      setSaving(false);
    }
  };

  const handleResetDefaults = async () => {
    if (!window.confirm('Are you sure you want to reset all settings to defaults? This action cannot be undone.')) {
      return;
    }
    
    try {
      setSaving(true);
      await axios.post(`${API}/settings/reset-defaults`);
      setMessage('Settings reset to defaults successfully!');
      setTimeout(() => setMessage(''), 3000);
      fetchSettings();
    } catch (error) {
      console.error('Failed to reset settings:', error);
      setMessage('Failed to reset settings: ' + (error.response?.data?.detail || error.message));
      setTimeout(() => setMessage(''), 5000);
    } finally {
      setSaving(false);
    }
  };

  const renderSettingInput = (setting) => {
    const category = setting.category;
    const key = setting.key;
    const value = formData[category]?.[key] || setting.value;

    switch (setting.data_type) {
      case 'boolean':
        return (
          <div className="setting-input-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={value === true}
                onChange={(e) => handleInputChange(category, key, e.target.checked)}
              />
              <span>{setting.description || key}</span>
            </label>
            <button 
              onClick={() => handleSaveSetting(category, key)}
              className="btn btn-outline btn-sm"
              disabled={saving}
            >
              Save
            </button>
          </div>
        );
      
      case 'integer':
        return (
          <div className="setting-input-group">
            <label>{setting.description || key}</label>
            <div className="input-with-button">
              <input
                type="number"
                value={value || ''}
                onChange={(e) => handleInputChange(category, key, parseInt(e.target.value) || 0)}
                className="input"
              />
              <button 
                onClick={() => handleSaveSetting(category, key)}
                className="btn btn-outline btn-sm"
                disabled={saving}
              >
                Save
              </button>
            </div>
          </div>
        );
      
      case 'array':
        return (
          <div className="setting-input-group">
            <label>{setting.description || key}</label>
            <div className="input-with-button">
              <textarea
                value={Array.isArray(value) ? value.join('\n') : ''}
                onChange={(e) => handleArrayChange(category, key, e.target.value)}
                className="input"
                rows="3"
                placeholder="Enter each item on a new line"
              />
              <button 
                onClick={() => handleSaveSetting(category, key)}
                className="btn btn-outline btn-sm"
                disabled={saving}
              >
                Save
              </button>
            </div>
          </div>
        );
      
      default: // string
        return (
          <div className="setting-input-group">
            <label>{setting.description || key}</label>
            <div className="input-with-button">
              <input
                type="text"
                value={value || ''}
                onChange={(e) => handleInputChange(category, key, e.target.value)}
                className="input"
              />
              <button 
                onClick={() => handleSaveSetting(category, key)}
                className="btn btn-outline btn-sm"
                disabled={saving}
              >
                Save
              </button>
            </div>
          </div>
        );
    }
  };

  const getSettingsByCategory = (category) => {
    return settings.filter(setting => setting.category === category);
  };

  if (loading) {
    return <div className="loading">Loading settings...</div>;
  }

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h1>⚙️ Settings</h1>
        <div className="settings-actions">
          <button 
            onClick={handleResetDefaults}
            className="btn btn-outline"
            disabled={saving}
          >
            Reset to Defaults
          </button>
        </div>
      </div>

      {message && (
        <div className={`message ${message.includes('Failed') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}

      <div className="settings-content">
        <div className="settings-tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`settings-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-name">{tab.name}</span>
            </button>
          ))}
        </div>

        <div className="settings-panel">
          <div className="settings-section">
            <h2>{tabs.find(tab => tab.id === activeTab)?.name}</h2>
            <div className="settings-grid">
              {getSettingsByCategory(activeTab).map(setting => (
                <div key={setting.id} className="setting-item">
                  <div className="setting-info">
                    <h3>{setting.key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h3>
                    <p className="setting-description">{setting.description}</p>
                  </div>
                  <div className="setting-control">
                    {renderSettingInput(setting)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;