import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [message, setMessage] = useState('');

  const [newUserData, setNewUserData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'teacher'
  });

  const [editUserData, setEditUserData] = useState({
    name: '',
    email: '',
    role: 'teacher',
    is_active: true
  });

  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: ''
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users:', error);
      setMessage('Failed to load users: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    
    if (newUserData.password.length < 6) {
      setMessage('Password must be at least 6 characters long');
      return;
    }

    try {
      await axios.post(`${API}/users`, newUserData);
      setMessage('User created successfully!');
      setShowAddModal(false);
      setNewUserData({ name: '', email: '', password: '', role: 'teacher' });
      fetchUsers();
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Failed to create user:', error);
      setMessage('Failed to create user: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEditUser = async (e) => {
    e.preventDefault();
    
    try {
      await axios.put(`${API}/users/${selectedUser.id}`, editUserData);
      setMessage('User updated successfully!');
      setShowEditModal(false);
      fetchUsers();
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Failed to update user:', error);
      setMessage('Failed to update user: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    
    if (passwordData.new_password.length < 6) {
      setMessage('New password must be at least 6 characters long');
      return;
    }

    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage('New passwords do not match');
      return;
    }

    try {
      const payload = {
        new_password: passwordData.new_password
      };
      
      // Include old password if changing own password
      if (passwordData.old_password) {
        payload.old_password = passwordData.old_password;
      }

      await axios.put(`${API}/users/${selectedUser.id}/password`, payload);
      setMessage('Password changed successfully!');
      setShowPasswordModal(false);
      setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Failed to change password:', error);
      setMessage('Failed to change password: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteUser = async (user) => {
    if (!window.confirm(`Are you sure you want to delete user "${user.name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await axios.delete(`${API}/users/${user.id}`);
      setMessage('User deleted successfully!');
      fetchUsers();
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Failed to delete user:', error);
      setMessage('Failed to delete user: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleToggleStatus = async (user) => {
    try {
      await axios.put(`${API}/users/${user.id}`, {
        is_active: !user.is_active
      });
      setMessage(`User ${!user.is_active ? 'activated' : 'deactivated'} successfully!`);
      fetchUsers();
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Failed to toggle user status:', error);
      setMessage('Failed to update user status: ' + (error.response?.data?.detail || error.message));
    }
  };

  const openEditModal = (user) => {
    setSelectedUser(user);
    setEditUserData({
      name: user.name,
      email: user.email,
      role: user.role,
      is_active: user.is_active
    });
    setShowEditModal(true);
  };

  const openPasswordModal = (user) => {
    setSelectedUser(user);
    setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
    setShowPasswordModal(true);
  };

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'owner': return 'role-owner';
      case 'manager': return 'role-manager';
      case 'teacher': return 'role-teacher';
      default: return 'role-default';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return <div className="loading">Loading users...</div>;
  }

  return (
    <div className="user-management-page">
      <div className="page-header">
        <h1>👥 User Management</h1>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn btn-primary"
        >
          + Add User
        </button>
      </div>

      {message && (
        <div className={`message ${message.includes('Failed') || message.includes('Error') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}

      <div className="users-grid">
        {users.map(user => (
          <div key={user.id} className={`user-card ${!user.is_active ? 'inactive' : ''}`}>
            <div className="user-info">
              <div className="user-header">
                <h3>{user.name}</h3>
                <span className={`role-badge ${getRoleBadgeColor(user.role)}`}>
                  {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                </span>
              </div>
              <p className="user-email">{user.email}</p>
              <p className="user-meta">
                Created: {formatDate(user.created_at)}
                {user.updated_at && (
                  <><br />Updated: {formatDate(user.updated_at)}</>
                )}
              </p>
              <div className={`status-indicator ${user.is_active ? 'active' : 'inactive'}`}>
                {user.is_active ? '🟢 Active' : '🔴 Inactive'}
              </div>
            </div>
            
            <div className="user-actions">
              <button
                onClick={() => openEditModal(user)}
                className="btn btn-outline btn-sm"
              >
                Edit
              </button>
              <button
                onClick={() => openPasswordModal(user)}
                className="btn btn-outline btn-sm"
              >
                Password
              </button>
              <button
                onClick={() => handleToggleStatus(user)}
                className={`btn btn-sm ${user.is_active ? 'btn-outline' : 'btn-success'}`}
              >
                {user.is_active ? 'Deactivate' : 'Activate'}
              </button>
              <button
                onClick={() => handleDeleteUser(user)}
                className="btn btn-danger btn-sm"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2>Add New User</h2>
              <button 
                onClick={() => setShowAddModal(false)}
                className="modal-close"
              >
                ×
              </button>
            </div>
            <form onSubmit={handleCreateUser}>
              <div className="form-group">
                <label>Name</label>
                <input
                  type="text"
                  value={newUserData.name}
                  onChange={(e) => setNewUserData({...newUserData, name: e.target.value})}
                  className="input"
                  required
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={newUserData.email}
                  onChange={(e) => setNewUserData({...newUserData, email: e.target.value})}
                  className="input"
                  required
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  value={newUserData.password}
                  onChange={(e) => setNewUserData({...newUserData, password: e.target.value})}
                  className="input"
                  minLength="6"
                  required
                />
              </div>
              <div className="form-group">
                <label>Role</label>
                <select
                  value={newUserData.role}
                  onChange={(e) => setNewUserData({...newUserData, role: e.target.value})}
                  className="input"
                  required
                >
                  <option value="teacher">Teacher</option>
                  <option value="manager">Manager</option>
                  <option value="owner">Owner</option>
                </select>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowAddModal(false)} className="btn btn-outline">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2>Edit User</h2>
              <button 
                onClick={() => setShowEditModal(false)}
                className="modal-close"
              >
                ×
              </button>
            </div>
            <form onSubmit={handleEditUser}>
              <div className="form-group">
                <label>Name</label>
                <input
                  type="text"
                  value={editUserData.name}
                  onChange={(e) => setEditUserData({...editUserData, name: e.target.value})}
                  className="input"
                  required
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={editUserData.email}
                  onChange={(e) => setEditUserData({...editUserData, email: e.target.value})}
                  className="input"
                  required
                />
              </div>
              <div className="form-group">
                <label>Role</label>
                <select
                  value={editUserData.role}
                  onChange={(e) => setEditUserData({...editUserData, role: e.target.value})}
                  className="input"
                  required
                >
                  <option value="teacher">Teacher</option>
                  <option value="manager">Manager</option>
                  <option value="owner">Owner</option>
                </select>
              </div>
              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={editUserData.is_active}
                    onChange={(e) => setEditUserData({...editUserData, is_active: e.target.checked})}
                  />
                  Active Account
                </label>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowEditModal(false)} className="btn btn-outline">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Update User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Change Password Modal */}
      {showPasswordModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2>Change Password</h2>
              <button 
                onClick={() => setShowPasswordModal(false)}
                className="modal-close"
              >
                ×
              </button>
            </div>
            <form onSubmit={handleChangePassword}>
              <div className="form-group">
                <label>Current Password (if changing your own)</label>
                <input
                  type="password"
                  value={passwordData.old_password}
                  onChange={(e) => setPasswordData({...passwordData, old_password: e.target.value})}
                  className="input"
                  placeholder="Leave blank if you're an owner changing another user's password"
                />
              </div>
              <div className="form-group">
                <label>New Password</label>
                <input
                  type="password"
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({...passwordData, new_password: e.target.value})}
                  className="input"
                  minLength="6"
                  required
                />
              </div>
              <div className="form-group">
                <label>Confirm New Password</label>
                <input
                  type="password"
                  value={passwordData.confirm_password}
                  onChange={(e) => setPasswordData({...passwordData, confirm_password: e.target.value})}
                  className="input"
                  minLength="6"
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowPasswordModal(false)} className="btn btn-outline">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Change Password
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;