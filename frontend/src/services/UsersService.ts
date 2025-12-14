// User Management Service for HomeStock API

const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const API_BASE = `${API_BASE_URL}/api`;

export interface User {
  id: number;
  username: string;
}

export interface UserCreate {
  username: string;
  password: string;
}

export interface PasswordChange {
  current_password: string;
  new_password: string;
}

export interface UsernameChange {
  new_username: string;
}

// Custom error class for Users API
export class UsersError extends Error {
  statusCode?: number;

  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = 'UsersError';
    this.statusCode = statusCode;
  }
}

/**
 * Get all users
 */
export async function getAllUsers(): Promise<User[]> {
  const response = await fetch(`${API_BASE}/auth/users`, {
    method: 'GET',
    credentials: 'include', // Include httpOnly cookie
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to get users' }));
    throw new UsersError(errorData.detail || 'Failed to get users', response.status);
  }

  return response.json();
}

/**
 * Get current user info
 */
export async function getCurrentUser(): Promise<User> {
  const response = await fetch(`${API_BASE}/auth/me`, {
    method: 'GET',
    credentials: 'include', // Include httpOnly cookie
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to get user info' }));
    throw new UsersError(errorData.detail || 'Failed to get user info', response.status);
  }

  return response.json();
}

/**
 * Register a new user (admin only - requires authentication)
 */
export async function registerUser(userData: UserCreate): Promise<User> {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    credentials: 'include', // Include httpOnly cookie
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to create user' }));
    throw new UsersError(errorData.detail || 'Failed to create user', response.status);
  }

  return response.json();
}

/**
 * Change current user's password
 */
export async function changePassword(passwordData: PasswordChange): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE}/auth/me/password`, {
    method: 'PATCH',
    credentials: 'include', // Include httpOnly cookie
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(passwordData),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to change password' }));
    throw new UsersError(errorData.detail || 'Failed to change password', response.status);
  }

  return response.json();
}

/**
 * Change current user's username
 */
export async function changeUsername(usernameData: UsernameChange): Promise<User> {
  const response = await fetch(`${API_BASE}/auth/me/username`, {
    method: 'PATCH',
    credentials: 'include', // Include httpOnly cookie
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(usernameData),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to change username' }));
    throw new UsersError(errorData.detail || 'Failed to change username', response.status);
  }

  return response.json();
}

/**
 * Delete a user by ID
 */
export async function deleteUser(userId: number): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE}/auth/users/${userId}`, {
    method: 'DELETE',
    credentials: 'include', // Include httpOnly cookie
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to delete user' }));
    throw new UsersError(errorData.detail || 'Failed to delete user', response.status);
  }

  return response.json();
}
