import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const ProgramsManager = () => {
  const [programs, setPrograms] = useState([]);
  const [studioName, setStudioName] = useState('Dancing on the Boulevard');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [newProgram, setNewProgram] = useState({
    name: '',
    description: '',
    default_lessons: 8,
    price_per_lesson: 50.00
  });

  useEffect(() => {
    fetchPrograms();
    loadStudioName();
  }, []);

  const fetchPrograms = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/programs`);
      setPrograms(response.data);
    } catch (error) {
      console.error('Failed to fetch programs:', error);
      showMessage('Failed to load programs', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadStudioName = () => {
    const savedName = localStorage.getItem('studio_name');
    if (savedName) {
      setStudioName(savedName);
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

  const handleStudioNameSave = () => {
    localStorage.setItem('studio_name', studioName);
    showMessage('Studio name updated! This will be reflected in new emails and notifications.');
  };

  const handleAddProgram = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await axios.post(`${API}/programs`, newProgram);
      showMessage('Program added successfully!');
      setNewProgram({
        name: '',
        description: '',
        default_lessons: 8,
        price_per_lesson: 50.00
      });
      setShowAddModal(false);
      fetchPrograms();
    } catch (error) {
      showMessage('Failed to add program: ' + (error.response?.data?.detail || error.message), 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateProgram = async (programId, updatedData) => {
    setSaving(true);
    try {
      await axios.put(`${API}/programs/${programId}`, updatedData);
      showMessage('Program updated successfully!');
      fetchPrograms();
    } catch (error) {
      showMessage('Failed to update program: ' + (error.response?.data?.detail || error.message), 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteProgram = async (programId, programName) => {
    if (!window.confirm(`Are you sure you want to delete "${programName}"? This action cannot be undone.`)) {
      return;
    }

    setSaving(true);
    try {
      await axios.delete(`${API}/programs/${programId}`);
      showMessage('Program deleted successfully!');
      fetchPrograms();
    } catch (error) {
      showMessage('Failed to delete program: ' + (error.response?.data?.detail || error.message), 'error');
    } finally {
      setSaving(false);
    }
  };

  const ProgramCard = ({ program }) => {
    const [editing, setEditing] = useState(false);
    const [editData, setEditData] = useState({
      name: program.name,
      description: program.description || '',
      default_lessons: program.default_lessons || 8,
      price_per_lesson: program.price_per_lesson || 50.00
    });

    const handleSave = () => {
      handleUpdateProgram(program.id, editData);
      setEditing(false);
    };

    const handleCancel = () => {
      setEditData({
        name: program.name,
        description: program.description || '',
        default_lessons: program.default_lessons || 8,
        price_per_lesson: program.price_per_lesson || 50.00
      });
      setEditing(false);
    };

    if (editing) {
      return (
        <div className="program-card editing">
          <div className="program-card-header">
            <input
              type="text"
              value={editData.name}
              onChange={(e) => setEditData({...editData, name: e.target.value})}
              className="input program-name-input"
              placeholder="Program name"
            />
          </div>
          <div className="program-card-body">
            <div className="form-group">
              <label>Description:</label>
              <textarea
                value={editData.description}
                onChange={(e) => setEditData({...editData, description: e.target.value})}
                className="input textarea"
                rows="3"
                placeholder="Program description"
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Default Lessons:</label>
                <input
                  type="number"
                  value={editData.default_lessons}
                  onChange={(e) => setEditData({...editData, default_lessons: parseInt(e.target.value) || 0})}
                  className="input"
                  min="1"
                />
              </div>
              <div className="form-group">
                <label>Price per Lesson:</label>
                <input
                  type="number"
                  step="0.01"
                  value={editData.price_per_lesson}
                  onChange={(e) => setEditData({...editData, price_per_lesson: parseFloat(e.target.value) || 0})}
                  className="input"
                  min="0"
                />
              </div>
            </div>
          </div>
          <div className="program-card-actions">
            <button onClick={handleSave} className="btn btn-primary btn-sm" disabled={saving}>
              ✅ Save
            </button>
            <button onClick={handleCancel} className="btn btn-outline btn-sm">
              ❌ Cancel
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="program-card">
        <div className="program-card-header">
          <h3>{program.name}</h3>
          <span className="program-id">ID: {program.id}</span>
        </div>
        <div className="program-card-body">
          {program.description && (
            <p className="program-description">{program.description}</p>
          )}
          <div className="program-details">
            <span className="program-detail">
              📚 Default Lessons: {program.default_lessons || 8}
            </span>
            <span className="program-detail">
              💰 Price: ${(program.price_per_lesson || 50).toFixed(2)} per lesson
            </span>
          </div>
        </div>
        <div className="program-card-actions">
          <button onClick={() => setEditing(true)} className="btn btn-outline btn-sm">
            ✏️ Edit
          </button>
          <button 
            onClick={() => handleDeleteProgram(program.id, program.name)} 
            className="btn btn-danger btn-sm"
            disabled={saving}
          >
            🗑️ Delete
          </button>
        </div>
      </div>
    );
  };

  if (loading) {
    return <div className="loading">Loading programs...</div>;
  }

  return (
    <div className="programs-manager">
      <div className="programs-header">
        <h2>📚 Programs Manager</h2>
        <p>Manage your studio name and dance programs</p>
      </div>

      {/* Message Display */}
      {message && (
        <div className={`programs-message ${messageType === 'error' ? 'error' : 'success'}`}>
          {message}
        </div>
      )}

      {/* Studio Name Section */}
      <div className="programs-section">
        <h3>🏢 Studio Information</h3>
        <p>This name will appear in all email notifications and system communications.</p>
        <div className="studio-name-group">
          <div className="form-group">
            <label>Studio Name:</label>
            <input
              type="text"
              value={studioName}
              onChange={(e) => setStudioName(e.target.value)}
              className="input studio-name-input"
              placeholder="Your studio name"
            />
          </div>
          <button 
            onClick={handleStudioNameSave}
            className="btn btn-primary"
            disabled={saving}
          >
            💾 Save Studio Name
          </button>
        </div>
        <div className="studio-name-preview">
          <h4>Preview:</h4>
          <div className="email-preview">
            <p><strong>From:</strong> {studioName} &lt;dancingnotifications@gmail.com&gt;</p>
            <p><strong>Footer:</strong> {studioName} | Keep Dancing! 🌟</p>
          </div>
        </div>
      </div>

      {/* Programs Section */}
      <div className="programs-section">
        <div className="section-header">
          <h3>💃 Dance Programs</h3>
          <button 
            onClick={() => setShowAddModal(true)}
            className="btn btn-primary"
          >
            ➕ Add New Program
          </button>
        </div>
        <p>Manage your dance programs, their descriptions, and default pricing.</p>

        {programs.length === 0 ? (
          <div className="empty-state">
            <p>📭 No programs found</p>
            <p>Add your first dance program to get started!</p>
          </div>
        ) : (
          <div className="programs-grid">
            {programs.map(program => (
              <ProgramCard key={program.id} program={program} />
            ))}
          </div>
        )}
      </div>

      {/* Add Program Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add New Program</h3>
              <button 
                onClick={() => setShowAddModal(false)}
                className="modal-close"
              >
                ×
              </button>
            </div>
            <form onSubmit={handleAddProgram} className="modal-body">
              <div className="form-group">
                <label>Program Name:</label>
                <input
                  type="text"
                  value={newProgram.name}
                  onChange={(e) => setNewProgram({...newProgram, name: e.target.value})}
                  className="input"
                  placeholder="e.g., Ballet, Hip Hop, Salsa"
                  required
                />
              </div>
              <div className="form-group">
                <label>Description:</label>
                <textarea
                  value={newProgram.description}
                  onChange={(e) => setNewProgram({...newProgram, description: e.target.value})}
                  className="input textarea"
                  rows="3"
                  placeholder="Brief description of the program"
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Default Lessons:</label>
                  <input
                    type="number"
                    value={newProgram.default_lessons}
                    onChange={(e) => setNewProgram({...newProgram, default_lessons: parseInt(e.target.value) || 0})}
                    className="input"
                    min="1"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Price per Lesson:</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newProgram.price_per_lesson}
                    onChange={(e) => setNewProgram({...newProgram, price_per_lesson: parseFloat(e.target.value) || 0})}
                    className="input"
                    min="0"
                    required
                  />
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowAddModal(false)} className="btn btn-outline">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Adding...' : 'Add Program'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProgramsManager;