/**
 * Authentication Service
 *
 * Handles login, logout, and authentication state using httpOnly cookies.
 *
 * Security features:
 * - JWT stored in httpOnly cookie (immune to XSS)
 * - SameSite=Strict (prevents CSRF)
 * - credentials: 'include' for automatic cookie transmission
 *
 * Configuration (.env):
 * - Development: VITE_API_URL=http://localhost:8000
 * - Production:  VITE_API_URL= (empty, uses relative URLs)
 */

// In production, use relative URLs (same domain via NPM path routing)
// In development, use absolute URL to backend container
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export interface LoginResponse {
  message: string;
  token_type: string;
  username: string;
}

export interface UserInfo {
  id: number;
  username: string;
}

export class AuthError extends Error {
  statusCode?: number;

  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = 'AuthError';
    this.statusCode = statusCode;
  }
}

/**
 * Login user with username and password.
 * Sets httpOnly cookie on success.
 */
export async function login(username: string, password: string): Promise<LoginResponse> {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await fetch(`${API_BASE_URL}/api/auth/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
    credentials: 'include', // CRITICAL: Include cookies in request
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Invalid username or password', 401);
    }
    throw new AuthError('Login failed. Please try again.', response.status);
  }

  const data: LoginResponse = await response.json();
  return data;
}

/**
 * Logout user by clearing the httpOnly cookie.
 */
export async function logout(): Promise<void> {
  try {
    await fetch(`${API_BASE_URL}/api/auth/logout`, {
      method: 'POST',
      credentials: 'include', // Send cookie to be cleared
    });
  } catch (error) {
    // Even if logout request fails, we can't do much
    console.error('Logout request failed:', error);
  }
}

/**
 * Get current user information.
 * Throws AuthError if not authenticated.
 */
export async function getCurrentUser(): Promise<UserInfo> {
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    method: 'GET',
    credentials: 'include', // Send cookie for authentication
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    throw new AuthError('Failed to get user info', response.status);
  }

  const data: UserInfo = await response.json();
  return data;
}

/**
 * Check if user is authenticated.
 * Returns true if authenticated, false otherwise.
 */
export async function isAuthenticated(): Promise<boolean> {
  try {
    await getCurrentUser();
    return true;
  } catch (error) {
    if (error instanceof AuthError && error.statusCode === 401) {
      return false;
    }
    // For other errors, assume not authenticated
    return false;
  }
}
