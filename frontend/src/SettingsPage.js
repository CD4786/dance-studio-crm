import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TeacherColorManager from './TeacherColorManager';

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
      
      // Apply UI changes immediately for specific settings
      if (category === 'theme') {
        if (key === 'selected_theme') {
          applyTheme(value);
        } else if (key === 'font_size') {
          applyFontSize(value);
        } else if (key === 'custom_primary_color' || key === 'custom_secondary_color') {
          const primaryColor = formData.theme?.custom_primary_color;
          const secondaryColor = formData.theme?.custom_secondary_color;
          applyCustomColors(primaryColor, secondaryColor);
        }
      }
      
      // Apply other UI changes
      if (category === 'display') {
        if (key === 'compact_mode') {
          document.documentElement.classList.toggle('compact-mode', value);
        } else if (key === 'language') {
          // Store language preference for future use
          localStorage.setItem('preferred_language', value);
        }
      }
      
      // Apply calendar settings (store in localStorage for calendar components to use)
      if (category === 'calendar') {
        localStorage.setItem(`calendar_${key}`, JSON.stringify(value));
        
        // Apply immediate effects for some calendar settings
        if (key === 'time_slot_minutes') {
          // Could trigger calendar refresh
          console.log(`Time slot minutes set to: ${value}`);
        } else if (key === 'start_hour' || key === 'end_hour') {
          console.log(`Calendar hours updated: ${key} = ${value}`);
        }
      }
      
      // Apply business rules (store for validation logic)
      if (category === 'business_rules') {
        localStorage.setItem(`business_rule_${key}`, JSON.stringify(value));
      }
      
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

  const applyTheme = (themeName) => {
    const validThemes = ['dark', 'light', 'ocean'];
    if (!validThemes.includes(themeName)) {
      themeName = 'dark'; // Default fallback
    }
    
    // Remove existing theme attributes
    document.documentElement.removeAttribute('data-theme');
    
    // Apply new theme (dark is the default, so no attribute needed)
    if (themeName !== 'dark') {
      document.documentElement.setAttribute('data-theme', themeName);
    }
    
    console.log(`Applied theme: ${themeName}`);
  };

  // Apply font size changes to the UI
  const applyFontSize = (fontSize) => {
    const validSizes = ['small', 'medium', 'large'];
    if (!validSizes.includes(fontSize)) {
      fontSize = 'medium'; // Default fallback
    }
    
    // Apply font size to CSS custom properties
    const root = document.documentElement;
    switch (fontSize) {
      case 'small':
        root.style.setProperty('--base-font-size', '14px');
        root.style.setProperty('--heading-font-size', '1.25rem');
        root.style.setProperty('--small-font-size', '12px');
        break;
      case 'large':
        root.style.setProperty('--base-font-size', '18px');
        root.style.setProperty('--heading-font-size', '1.75rem');
        root.style.setProperty('--small-font-size', '16px');
        break;
      default: // medium
        root.style.setProperty('--base-font-size', '16px');
        root.style.setProperty('--heading-font-size', '1.5rem');
        root.style.setProperty('--small-font-size', '14px');
        break;
    }
    
    console.log(`Applied font size: ${fontSize}`);
  };

  // Apply custom colors to CSS variables
  const applyCustomColors = (primaryColor, secondaryColor) => {
    const root = document.documentElement;
    if (primaryColor) {
      root.style.setProperty('--accent-primary', primaryColor);
      root.style.setProperty('--gradient-primary', `linear-gradient(135deg, ${primaryColor} 0%, ${secondaryColor || primaryColor} 100%)`);
    }
    if (secondaryColor) {
      root.style.setProperty('--accent-secondary', secondaryColor);
      root.style.setProperty('--gradient-secondary', `linear-gradient(135deg, ${primaryColor || secondaryColor} 0%, ${secondaryColor} 100%)`);
    }
    console.log(`Applied custom colors: primary=${primaryColor}, secondary=${secondaryColor}`);
  };

  // Apply all UI settings on component mount and when settings change
  useEffect(() => {
    if (settings.length > 0) {
      // Apply theme settings
      const themeSettings = settings.filter(s => s.category === 'theme');
      const themeSettingsMap = {};
      themeSettings.forEach(setting => {
        themeSettingsMap[setting.key] = setting.value;
      });
      
      // Apply theme
      if (themeSettingsMap.selected_theme) {
        applyTheme(themeSettingsMap.selected_theme);
      }
      
      // Apply font size
      if (themeSettingsMap.font_size) {
        applyFontSize(themeSettingsMap.font_size);
      }
      
      // Apply custom colors
      if (themeSettingsMap.custom_primary_color || themeSettingsMap.custom_secondary_color) {
        applyCustomColors(themeSettingsMap.custom_primary_color, themeSettingsMap.custom_secondary_color);
      }
      
      // Apply display settings
      const displaySettings = settings.filter(s => s.category === 'display');
      displaySettings.forEach(setting => {
        if (setting.key === 'compact_mode') {
          document.documentElement.classList.toggle('compact-mode', setting.value);
        }
      });
    }
  }, [settings]);

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

    // Special handling for theme settings first (before color check)
    if (key === 'selected_theme') {
      return (
        <div className="setting-input-group">
          <label>{setting.description || key}</label>
          <div className="input-with-button">
            <select
              value={value || 'dark'}
              onChange={(e) => {
                handleInputChange(category, key, e.target.value);
                // Apply theme immediately for preview
                applyTheme(e.target.value);
              }}
              className="input"
            >
              <option value="dark">🌙 Dark Theme</option>
              <option value="light">☀️ Light Theme</option>
              <option value="ocean">🌊 Ocean Theme</option>
            </select>
            <button 
              onClick={() => handleSaveSetting(category, key)}
              className="btn btn-outline btn-sm"
              disabled={saving}
            >
              Save
            </button>
          </div>
          <div className="theme-preview">
            <div className="theme-preview-text">Preview: Current theme applied</div>
          </div>
        </div>
      );
    }

    // Special handling for different setting types
    if (key.includes('color')) {
      return (
        <div className="setting-input-group">
          <label>{setting.description || key}</label>
          <div className="color-input-group">
            <input
              type="color"
              value={value || '#3b82f6'}
              onChange={(e) => handleInputChange(category, key, e.target.value)}
              className="color-picker"
            />
            <input
              type="text"
              value={value || '#3b82f6'}
              onChange={(e) => handleInputChange(category, key, e.target.value)}
              className="color-text-input"
              placeholder="#3b82f6"
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

    if (key === 'font_size') {
      return (
        <div className="setting-input-group">
          <label>{setting.description || key}</label>
          <div className="input-with-button">
            <select
              value={value || 'medium'}
              onChange={(e) => handleInputChange(category, key, e.target.value)}
              className="input"
            >
              <option value="small">📝 Small</option>
              <option value="medium">📄 Medium</option>
              <option value="large">📰 Large</option>
            </select>
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

    if (key === 'default_view') {
      return (
        <div className="setting-input-group">
          <label>{setting.description || key}</label>
          <div className="input-with-button">
            <select
              value={value || 'daily'}
              onChange={(e) => handleInputChange(category, key, e.target.value)}
              className="input"
            >
              <option value="daily">📅 Daily View</option>
              <option value="weekly">📆 Weekly View</option>
            </select>
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

    if (key === 'language') {
      return (
        <div className="setting-input-group">
          <label>{setting.description || key}</label>
          <div className="input-with-button">
            <select
              value={value || 'en'}
              onChange={(e) => handleInputChange(category, key, e.target.value)}
              className="input"
            >
              <option value="en">🇺🇸 English</option>
              <option value="es">🇪🇸 Spanish</option>
              <option value="fr">🇫🇷 French</option>
              <option value="de">🇩🇪 German</option>
            </select>
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

      case 'float':
        return (
          <div className="setting-input-group">
            <label>{setting.description || key}</label>
            <div className="input-with-button">
              <input
                type="number"
                step="0.01"
                value={value || ''}
                onChange={(e) => handleInputChange(category, key, parseFloat(e.target.value) || 0)}
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
          <div className="settings-section" data-category={activeTab}>
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
            
            {/* Add Teacher Color Manager to booking settings */}
            {activeTab === 'booking' && <TeacherColorManager />}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;