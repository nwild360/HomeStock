import React from 'react';
import type { Backup } from '../../types/BackupTypes';

interface ConfirmAction {
  type: 'delete' | 'restore';
  filename: string;
}

interface BackupsTableProps {
  backups: Backup[];
  confirmAction: ConfirmAction | null;
  actionLoading: boolean;
  onDownload: (filename: string) => void;
  onRequestRestore: (filename: string) => void;
  onRequestDelete: (filename: string) => void;
  onConfirm: () => void;
  onCancelConfirm: () => void;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

const BackupsTable: React.FC<BackupsTableProps> = ({
  backups,
  confirmAction,
  actionLoading,
  onDownload,
  onRequestRestore,
  onRequestDelete,
  onConfirm,
  onCancelConfirm,
}) => {
  if (backups.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-8 text-center">
        <p className="text-gray-500 dark:text-gray-400">No backups yet. Create your first backup above.</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
            <th className="text-left px-4 py-3 font-semibold text-gray-700 dark:text-gray-300">Name</th>
            <th className="text-left px-4 py-3 font-semibold text-gray-700 dark:text-gray-300 hidden sm:table-cell">Created</th>
            <th className="text-left px-4 py-3 font-semibold text-gray-700 dark:text-gray-300 hidden md:table-cell">Size</th>
            <th className="text-right px-4 py-3 font-semibold text-gray-700 dark:text-gray-300">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
          {backups.map((backup) => {
            const isPending = confirmAction?.filename === backup.name;
            return (
              <tr key={backup.name} className="hover:bg-gray-50 dark:hover:bg-gray-750">
                <td className="px-4 py-3 font-mono text-xs text-gray-800 dark:text-gray-200 break-all">
                  {backup.name}
                  <div className="sm:hidden text-gray-500 dark:text-gray-400 font-sans font-normal text-xs mt-0.5">
                    {formatDate(backup.created_at)} · {formatSize(backup.size_bytes)}
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-600 dark:text-gray-400 hidden sm:table-cell whitespace-nowrap">
                  {formatDate(backup.created_at)}
                </td>
                <td className="px-4 py-3 text-gray-600 dark:text-gray-400 hidden md:table-cell">
                  {formatSize(backup.size_bytes)}
                </td>
                <td className="px-4 py-3 text-right">
                  {isPending ? (
                    <div className="flex items-center justify-end gap-2 flex-wrap">
                      <span className="text-xs text-gray-600 dark:text-gray-400">
                        {confirmAction.type === 'restore'
                          ? 'Restore? All current data will be replaced and the page will reload.'
                          : 'Delete this backup?'}
                      </span>
                      <button
                        onClick={onConfirm}
                        disabled={actionLoading}
                        className="appearance-none px-3 py-1.5 text-xs font-medium rounded-md bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        {actionLoading ? 'Working…' : 'Yes'}
                      </button>
                      <button
                        onClick={onCancelConfirm}
                        disabled={actionLoading}
                        className="appearance-none px-3 py-1.5 text-xs font-medium rounded-md border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => onDownload(backup.name)}
                        title="Download"
                        className="appearance-none px-3 py-1.5 text-xs font-medium rounded-md bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                      >
                        Download
                      </button>
                      <button
                        onClick={() => onRequestRestore(backup.name)}
                        title="Restore"
                        className="appearance-none px-3 py-1.5 text-xs font-medium rounded-md bg-amber-500 text-white hover:bg-amber-600 transition-colors"
                      >
                        Restore
                      </button>
                      <button
                        onClick={() => onRequestDelete(backup.name)}
                        title="Delete"
                        className="appearance-none px-3 py-1.5 text-xs font-medium rounded-md bg-red-600 text-white hover:bg-red-700 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default BackupsTable;
