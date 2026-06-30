// API Keys Service for HomeStock API

import { AuthError } from './AuthService';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const API_BASE = `${API_BASE_URL}/api`;

export interface ApiKey {
  id: number;
  label: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
}

// Returned once at creation — includes the one-time plaintext key.
export interface ApiKeyCreated extends ApiKey {
  key: string;
}

// Custom error class for API Keys API
export class ApiKeysError extends Error {
  statusCode?: number;

  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = 'ApiKeysError';
    this.statusCode = statusCode;
  }
}

/**
 * List the current user's API keys
 */
export async function getApiKeys(): Promise<ApiKey[]> {
  const response = await fetch(`${API_BASE}/auth/keys`, {
    method: 'GET',
    credentials: 'include', // Include httpOnly cookie
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    if (response.status === 401) throw new AuthError('Not authenticated', 401);
    const errorData = await response.json().catch(() => ({ detail: 'Failed to get API keys' }));
    throw new ApiKeysError(errorData.detail || 'Failed to get API keys', response.status);
  }

  return response.json();
}

/**
 * Mint a new API key. The plaintext key is only returned here, once.
 */
export async function createApiKey(label: string): Promise<ApiKeyCreated> {
  const response = await fetch(`${API_BASE}/auth/keys`, {
    method: 'POST',
    credentials: 'include', // Include httpOnly cookie
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ label }),
  });

  if (!response.ok) {
    if (response.status === 401) throw new AuthError('Not authenticated', 401);
    const errorData = await response.json().catch(() => ({ detail: 'Failed to create API key' }));
    throw new ApiKeysError(errorData.detail || 'Failed to create API key', response.status);
  }

  return response.json();
}

/**
 * Delete an API key by ID
 */
export async function deleteApiKey(keyId: number): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/keys/${keyId}`, {
    method: 'DELETE',
    credentials: 'include', // Include httpOnly cookie
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    if (response.status === 401) throw new AuthError('Not authenticated', 401);
    const errorData = await response.json().catch(() => ({ detail: 'Failed to delete API key' }));
    throw new ApiKeysError(errorData.detail || 'Failed to delete API key', response.status);
  }
}
