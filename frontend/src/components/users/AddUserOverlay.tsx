import React, { useState, useEffect } from 'react';
import { registerUser, changePassword, changeUsername, UsersError, type User } from '../../services/UsersService';
import { AuthError } from '../../services/AuthService';

interface AddUserOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  onUserCreated: () => void;
  editUser?: User; // User to edit (if provided, overlay is in edit mode)
  currentUserId?: number; // Current user ID to check permissions
}

const AddUserOverlay: React.FC<AddUserOverlayProps> = ({ isOpen, onClose, onUserCreated, editUser, currentUserId }) => {
  const isEditMode = !!editUser;
  const isCurrentUser = editUser?.id === currentUserId;

  // Create mode state
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Edit mode state
  const [newUsername, setNewUsername] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Pre-fill form when editing
  useEffect(() => {
    if (isEditMode && editUser) {
      setNewUsername('');
    }
  }, [isEditMode, editUser]);

  if (!isOpen) return null;

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!username || !password || !confirmPassword) {
      setError('All fields are required');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
      setError('Username can only contain letters, numbers, underscores, and hyphens');
      return;
    }

    if (!/^[a-zA-Z0-9_-]+$/.test(password)) {
      setError('Password can only contain letters, numbers, underscores, and hyphens');
      return;
    }

    setIsSubmitting(true);

    try {
      await registerUser({ username, password });

      // Reset form
      setUsername('');
      setPassword('');
      setConfirmPassword('');
      setError(null);

      // Notify parent
      onUserCreated();
      onClose();
    } catch (err) {
      if (err instanceof AuthError) {
        console.error('Not authenticated, redirecting to login...');
        window.location.reload();
      } else if (err instanceof UsersError) {
        setError(err.message);
      } else {
        setError('Failed to create user');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChangeUsername = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!newUsername) {
      setError('Username is required');
      return;
    }

    if (!/^[a-zA-Z0-9_-]+$/.test(newUsername)) {
      setError('Username can only contain letters, numbers, underscores, and hyphens');
      return;
    }

    setIsSubmitting(true);

    try {
      await changeUsername({ new_username: newUsername });

      setNewUsername('');
      setError(null);
      onUserCreated();
      onClose();
    } catch (err) {
      if (err instanceof AuthError) {
        console.error('Not authenticated, redirecting to login...');
        window.location.reload();
      } else if (err instanceof UsersError) {
        setError(err.message);
      } else {
        setError('Failed to change username');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!currentPassword || !newPassword || !confirmNewPassword) {
      setError('All password fields are required');
      return;
    }

    if (newPassword !== confirmNewPassword) {
      setError('New passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    if (!/^[a-zA-Z0-9_-]+$/.test(newPassword)) {
      setError('Password can only contain letters, numbers, underscores, and hyphens');
      return;
    }

    setIsSubmitting(true);

    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword
      });

      alert('Password changed successfully. You will be logged out.');
      window.location.reload();
    } catch (err) {
      if (err instanceof AuthError) {
        console.error('Not authenticated, redirecting to login...');
        window.location.reload();
      } else if (err instanceof UsersError) {
        setError(err.message);
      } else {
        setError('Failed to change password');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setUsername('');
    setPassword('');
    setConfirmPassword('');
    setNewUsername('');
    setCurrentPassword('');
    setNewPassword('');
    setConfirmNewPassword('');
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            {isEditMode ? `Edit User: ${editUser.username}` : 'Add New User'}
          </h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          {!isEditMode ? (
            // CREATE MODE
            <form onSubmit={handleCreateUser} className="space-y-4">
              {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                  {error}
                </div>
              )}

              <div>
                <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                  Username
                </label>
                <input
                  type="text"
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  placeholder="Enter username"
                  disabled={isSubmitting}
                  minLength={3}
                  maxLength={50}
                  required
                />
                <p className="mt-1 text-xs text-gray-500">3-50 characters, alphanumeric with _ or -</p>
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  placeholder="Enter password"
                  disabled={isSubmitting}
                  minLength={8}
                  maxLength={100}
                  required
                />
                <p className="mt-1 text-xs text-gray-500">8-100 characters, alphanumeric with _ or -</p>
              </div>

              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                  Confirm Password
                </label>
                <input
                  type="password"
                  id="confirmPassword"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  placeholder="Confirm password"
                  disabled={isSubmitting}
                  minLength={8}
                  maxLength={100}
                  required
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={handleClose}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Creating...' : 'Create User'}
                </button>
              </div>
            </form>
          ) : (
            // EDIT MODE
            <div className="space-y-6">
              {!isCurrentUser && (
                <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded">
                  You can only edit your own account.
                </div>
              )}

              {isCurrentUser && (
                <>
                  {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                      {error}
                    </div>
                  )}

                  {/* Change Username */}
                  <div className="border-b pb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Change Username</h3>
                    <form onSubmit={handleChangeUsername} className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Current Username
                        </label>
                        <input
                          type="text"
                          value={editUser.username}
                          disabled
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600"
                        />
                      </div>

                      <div>
                        <label htmlFor="newUsername" className="block text-sm font-medium text-gray-700 mb-2">
                          New Username
                        </label>
                        <input
                          type="text"
                          id="newUsername"
                          value={newUsername}
                          onChange={(e) => setNewUsername(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                          placeholder="Enter new username"
                          disabled={isSubmitting}
                          minLength={3}
                          maxLength={50}
                        />
                        <p className="mt-1 text-xs text-gray-500">3-50 characters, alphanumeric with _ or -</p>
                      </div>

                      <button
                        type="submit"
                        className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={isSubmitting || !newUsername}
                      >
                        {isSubmitting ? 'Changing...' : 'Change Username'}
                      </button>
                    </form>
                  </div>

                  {/* Change Password */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Change Password</h3>
                    <form onSubmit={handleChangePassword} className="space-y-4">
                      <div>
                        <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700 mb-2">
                          Current Password
                        </label>
                        <input
                          type="password"
                          id="currentPassword"
                          value={currentPassword}
                          onChange={(e) => setCurrentPassword(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                          placeholder="Enter current password"
                          disabled={isSubmitting}
                        />
                      </div>

                      <div>
                        <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-2">
                          New Password
                        </label>
                        <input
                          type="password"
                          id="newPassword"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                          placeholder="Enter new password"
                          disabled={isSubmitting}
                          minLength={8}
                          maxLength={100}
                        />
                        <p className="mt-1 text-xs text-gray-500">8-100 characters, alphanumeric with _ or -</p>
                      </div>

                      <div>
                        <label htmlFor="confirmNewPassword" className="block text-sm font-medium text-gray-700 mb-2">
                          Confirm New Password
                        </label>
                        <input
                          type="password"
                          id="confirmNewPassword"
                          value={confirmNewPassword}
                          onChange={(e) => setConfirmNewPassword(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                          placeholder="Confirm new password"
                          disabled={isSubmitting}
                          minLength={8}
                          maxLength={100}
                        />
                      </div>

                      <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded text-sm">
                        <strong>Warning:</strong> Changing your password will log you out.
                      </div>

                      <button
                        type="submit"
                        className="w-full px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={isSubmitting || !currentPassword || !newPassword || !confirmNewPassword}
                      >
                        {isSubmitting ? 'Changing...' : 'Change Password'}
                      </button>
                    </form>
                  </div>
                </>
              )}

              <div className="flex justify-end pt-4 border-t">
                <button
                  onClick={handleClose}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AddUserOverlay;
