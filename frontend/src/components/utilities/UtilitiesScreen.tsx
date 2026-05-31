import React, { useState, useEffect, useRef } from 'react';
import BackupsTable from './BackupsTable';
import type { Backup } from '../../types/BackupTypes';
import {
  listBackups,
  createBackup,
  downloadBackup,
  uploadBackup,
  restoreBackup,
  deleteBackup,
  BackupError,
} from '../../services/BackupService';
import { AuthError } from '../../services/AuthService';

interface ConfirmAction {
  type: 'delete' | 'restore';
  filename: string;
}

const UtilitiesScreen: React.FC = () => {
  const [backups, setBackups] = useState<Backup[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchBackups = async (signal?: AbortSignal) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await listBackups(signal);
      setBackups(data.backups);
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return;
      if (err instanceof AuthError) {
        window.location.reload();
      } else {
        setError(err instanceof Error ? err.message : 'Failed to load backups');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    fetchBackups(controller.signal);
    return () => controller.abort();
  }, []);

  const handleCreateBackup = async () => {
    setIsCreating(true);
    setActionError(null);
    try {
      await createBackup();
      await fetchBackups();
    } catch (err) {
      if (err instanceof AuthError) {
        window.location.reload();
      } else {
        setActionError(err instanceof BackupError ? err.message : 'Failed to create backup');
      }
    } finally {
      setIsCreating(false);
    }
  };

  const handleDownload = async (filename: string) => {
    setActionError(null);
    try {
      await downloadBackup(filename);
    } catch (err) {
      if (err instanceof AuthError) {
        window.location.reload();
      } else {
        setActionError(err instanceof Error ? err.message : 'Failed to download backup');
      }
    }
  };

  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = '';
    if (file.size > 500 * 1024 * 1024) {
      setActionError('File must be 500 MB or smaller.');
      return;
    }
    setIsUploading(true);
    setActionError(null);
    try {
      await uploadBackup(file);
      await fetchBackups();
    } catch (err) {
      if (err instanceof AuthError) {
        window.location.reload();
      } else {
        setActionError(err instanceof BackupError ? err.message : 'Failed to upload backup');
      }
    } finally {
      setIsUploading(false);
    }
  };

  const handleConfirm = async () => {
    if (!confirmAction) return;
    setActionLoading(true);
    setActionError(null);
    try {
      if (confirmAction.type === 'delete') {
        await deleteBackup(confirmAction.filename);
        await fetchBackups();
      } else {
        await restoreBackup(confirmAction.filename);
        // Reload the page after restore — the DB state has changed under the app
        // and the connection pool has been recycled on the backend.
        window.location.reload();
        return;
      }
    } catch (err) {
      if (err instanceof AuthError) {
        window.location.reload();
      } else {
        setActionError(err instanceof BackupError ? err.message : 'Action failed');
        await fetchBackups();
      }
    } finally {
      setActionLoading(false);
      setConfirmAction(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 w-full min-w-0 p-3 md:p-8 bg-gray-50 dark:bg-gray-900 overflow-auto flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 dark:border-gray-100 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading backups...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 w-full min-w-0 p-3 md:p-8 bg-gray-50 dark:bg-gray-900 overflow-auto flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-400 px-4 py-3 rounded mb-4">
            <p className="font-bold">Error</p>
            <p>{error}</p>
          </div>
          <button
            onClick={fetchBackups}
            className="appearance-none px-4 py-2 bg-gray-900 dark:bg-gray-700 text-white rounded-lg hover:bg-gray-800 dark:hover:bg-gray-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 w-full min-w-0 p-3 md:p-8 bg-gray-50 dark:bg-gray-900 overflow-auto">
      <input
        ref={fileInputRef}
        type="file"
        accept=".zip"
        className="hidden"
        onChange={handleFileSelected}
      />

      <h1 className="text-3xl md:text-5xl font-bold text-gray-900 dark:text-gray-100 mb-4 md:mb-8">
        Utilities
      </h1>

      {/* Database Backups section */}
      <h2 className="text-lg md:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-3 md:mb-4">
        Database Backups
      </h2>

      {/* Action buttons */}
      <div className="flex flex-wrap gap-3 mb-4">
        <button
          onClick={handleCreateBackup}
          disabled={isCreating}
          className="appearance-none flex items-center gap-2 px-4 py-2 rounded-lg !bg-slate-950 text-white hover:!bg-lime-400 hover:text-slate-950 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isCreating ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
              Creating...
            </>
          ) : (
            'Create Backup'
          )}
        </button>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="appearance-none flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current" />
              Uploading...
            </>
          ) : (
            'Upload Backup'
          )}
        </button>
      </div>

      {/* Action error */}
      {actionError && (
        <div className="mb-4 flex items-start gap-3 bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg">
          <span className="flex-1 text-sm">{actionError}</span>
          <button
            onClick={() => setActionError(null)}
            className="appearance-none shrink-0 text-red-500 hover:text-red-700 dark:hover:text-red-300"
            aria-label="Dismiss"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      <BackupsTable
        backups={backups}
        confirmAction={confirmAction}
        actionLoading={actionLoading}
        onDownload={handleDownload}
        onRequestRestore={(filename) => setConfirmAction({ type: 'restore', filename })}
        onRequestDelete={(filename) => setConfirmAction({ type: 'delete', filename })}
        onConfirm={handleConfirm}
        onCancelConfirm={() => setConfirmAction(null)}
      />
    </div>
  );
};

export default UtilitiesScreen;
