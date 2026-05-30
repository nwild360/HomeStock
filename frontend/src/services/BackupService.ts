import type { Backup, BackupList } from '../types/BackupTypes';
import { AuthError } from './AuthService';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export class BackupError extends Error {
  statusCode?: number;

  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = 'BackupError';
    this.statusCode = statusCode;
  }
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body.detail || response.statusText;
  } catch {
    return response.statusText;
  }
}

export async function listBackups(): Promise<BackupList> {
  const response = await fetch(`${API_BASE_URL}/api/backups/`, {
    credentials: 'include',
  });
  if (!response.ok) {
    if (response.status === 401) throw new AuthError('Not authenticated', 401);
    const detail = await parseErrorDetail(response);
    throw new BackupError(detail, response.status);
  }
  return response.json();
}

export async function createBackup(): Promise<Backup> {
  const response = await fetch(`${API_BASE_URL}/api/backups/`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!response.ok) {
    if (response.status === 401) throw new AuthError('Not authenticated', 401);
    const detail = await parseErrorDetail(response);
    throw new BackupError(detail, response.status);
  }
  return response.json();
}

export async function downloadBackup(filename: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/backups/${encodeURIComponent(filename)}/download`,
    { credentials: 'include' },
  );
  if (!response.ok) {
    if (response.status === 401) throw new AuthError('Not authenticated', 401);
    throw new BackupError(`Failed to download backup: ${response.statusText}`, response.status);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function uploadBackup(file: File): Promise<Backup> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await fetch(`${API_BASE_URL}/api/backups/upload`, {
    method: 'POST',
    credentials: 'include',
    body: formData,
  });
  if (!response.ok) {
    if (response.status === 401) throw new AuthError('Not authenticated', 401);
    const detail = await parseErrorDetail(response);
    throw new BackupError(detail, response.status);
  }
  return response.json();
}

export async function restoreBackup(filename: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/backups/${encodeURIComponent(filename)}/restore`,
    { method: 'POST', credentials: 'include' },
  );
  if (!response.ok) {
    if (response.status === 401) throw new AuthError('Not authenticated', 401);
    const detail = await parseErrorDetail(response);
    throw new BackupError(detail, response.status);
  }
}

export async function deleteBackup(filename: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/backups/${encodeURIComponent(filename)}`,
    { method: 'DELETE', credentials: 'include' },
  );
  if (!response.ok) {
    if (response.status === 401) throw new AuthError('Not authenticated', 401);
    const detail = await parseErrorDetail(response);
    throw new BackupError(detail, response.status);
  }
}
