import React, { useState, useEffect } from 'react';
import { AuthError } from '../../services/AuthService';
import { getAllUsers, getCurrentUser, deleteUser, UsersError, type User } from '../../services/UsersService';
import AddUserOverlay from './AddUserOverlay';
import UsersTable from './UsersTable';

interface UserScreenProps {
  refreshKey?: number;
  onRefresh?: () => void;
}

const UserScreen: React.FC<UserScreenProps> = ({ refreshKey, onRefresh }) => {
  const [users, setUsers] = useState<User[]>([]);
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddUserOpen, setIsAddUserOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | undefined>(undefined);

  // Fetch all users and current user info
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const [allUsers, currentUser] = await Promise.all([
          getAllUsers(),
          getCurrentUser()
        ]);

        setUsers(allUsers);
        setCurrentUserId(currentUser.id);
      } catch (err) {
        if (err instanceof AuthError) {
          console.error('Not authenticated, redirecting to login...');
          window.location.reload();
        } else if (err instanceof UsersError) {
          setError(err.message);
        } else {
          setError('Failed to load users');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [refreshKey]);

  const handleAddUser = () => {
    setIsAddUserOpen(true);
  };

  const handleUserCreated = () => {
    setIsAddUserOpen(false);
    if (onRefresh) {
      onRefresh();
    }
  };

  const handleEdit = (userId: number) => {
    const user = users.find(u => u.id === userId);
    if (user) {
      setEditingUser(user);
      setIsAddUserOpen(true);
    }
  };

  const handleDelete = async (userId: number) => {
    if (!confirm('Are you sure you want to delete this user?')) {
      return;
    }

    // Optimistic update - remove from UI immediately
    setUsers(prevUsers => prevUsers.filter(user => user.id !== userId));

    try {
      await deleteUser(userId);
      if (onRefresh) {
        onRefresh();
      }
    } catch (err) {
      if (err instanceof AuthError) {
        console.error('Not authenticated, redirecting to login...');
        window.location.reload();
      } else {
        console.error('Failed to delete user:', err);
        // Revert optimistic update on error
        if (onRefresh) {
          onRefresh();
        }
      }
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex-1 w-full min-w-0 p-3 md:p-8 bg-gray-50 overflow-auto flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading users...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex-1 w-full min-w-0 p-3 md:p-8 bg-gray-50 overflow-auto flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <p className="font-bold">Error</p>
            <p>{error}</p>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 w-full min-w-0 p-3 md:p-8 bg-gray-50 overflow-auto">
      {/* Header */}
      <h1 className="text-3xl md:text-5xl font-bold text-gray-900 mb-4 md:mb-8">
        User Management
      </h1>

      {/* Add User Button */}
      <div className="mb-4 md:mb-6">
        <button
          onClick={handleAddUser}
          className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add User
        </button>
      </div>

      {/* Users Table */}
      <UsersTable
        users={users}
        currentUserId={currentUserId || 0}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />

      {/* Add User Overlay */}
      <AddUserOverlay
        isOpen={isAddUserOpen}
        onClose={() => {
          setIsAddUserOpen(false);
          setEditingUser(undefined);
        }}
        onUserCreated={handleUserCreated}
        editUser={editingUser}
        currentUserId={currentUserId || 0}
      />
    </div>
  );
};

export default UserScreen;
