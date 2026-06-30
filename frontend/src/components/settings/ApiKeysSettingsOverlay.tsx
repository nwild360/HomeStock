import { useState, useEffect } from 'react';
import { AuthError } from '../../services/AuthService';
import {
  getApiKeys,
  createApiKey,
  deleteApiKey,
  ApiKeysError,
  type ApiKey,
  type ApiKeyCreated,
} from '../../services/ApiKeysService';

interface ApiKeysSettingsOverlayProps {
  isOpen: boolean;
  onClose: () => void;
}

// Trash Icon Component (matches UsersTable / ItemsTable)
const TrashIcon = () => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 101 101"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className="flex-shrink-0"
  >
    <path
      d="M12.625 25.25H21.0417M21.0417 25.25H88.375M21.0417 25.25V84.1666C21.0417 86.3989 21.9284 88.5397 23.5069 90.1181C25.0853 91.6965 27.2261 92.5833 29.4583 92.5833H71.5417C73.7739 92.5833 75.9147 91.6965 77.4931 90.1181C79.0716 88.5397 79.9583 86.3989 79.9583 84.1666V25.25M33.6667 25.25V16.8333C33.6667 14.6011 34.5534 12.4602 36.1319 10.8818C37.7103 9.30338 39.8511 8.41663 42.0833 8.41663H58.9167C61.1489 8.41663 63.2897 9.30338 64.8681 10.8818C66.4466 12.4602 67.3333 14.6011 67.3333 16.8333V25.25M42.0833 46.2916V71.5416M58.9167 46.2916V71.5416"
      stroke="white"
      strokeWidth="4"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

function formatDate(value: string | null): string {
  if (!value) return '—';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleDateString();
}

function ApiKeysSettingsOverlay({ isOpen, onClose }: ApiKeysSettingsOverlayProps) {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [label, setLabel] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  // The plaintext key returned from the most recent generate — shown once.
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    // Reset transient state every time the overlay opens.
    setLabel('');
    setError('');
    setCreatedKey(null);
    setCopied(false);
    setIsLoading(true);
    getApiKeys()
      .then(setKeys)
      .catch(err => {
        if (err instanceof AuthError) {
          window.location.reload();
        } else {
          setError(err instanceof Error ? err.message : 'Failed to load API keys');
        }
      })
      .finally(() => setIsLoading(false));
  }, [isOpen]);

  const handleGenerate = async () => {
    const trimmed = label.trim();
    if (!trimmed) {
      setError('Please enter a label for the key');
      return;
    }
    setIsGenerating(true);
    setError('');
    setCreatedKey(null);
    setCopied(false);
    try {
      const created = await createApiKey(trimmed);
      setCreatedKey(created);
      setLabel('');
      // Prepend to the list (newest first), without the secret.
      const listEntry: ApiKey = {
        id: created.id,
        label: created.label,
        key_prefix: created.key_prefix,
        created_at: created.created_at,
        last_used_at: created.last_used_at,
      };
      setKeys(prev => [listEntry, ...prev]);
    } catch (err) {
      if (err instanceof AuthError) {
        window.location.reload();
      } else if (err instanceof ApiKeysError) {
        setError(err.message);
      } else {
        setError('Failed to create API key');
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = async () => {
    if (!createdKey) return;
    try {
      await navigator.clipboard.writeText(createdKey.key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError('Could not copy to clipboard — copy the key manually');
    }
  };

  const handleDelete = async (keyId: number) => {
    if (!confirm('Delete this API key? Any scripts using it will stop working.')) {
      return;
    }
    // Optimistic removal
    setKeys(prev => prev.filter(k => k.id !== keyId));
    // If the just-generated key is the one being deleted, clear the call-out too.
    setCreatedKey(prev => (prev && prev.id === keyId ? null : prev));
    try {
      await deleteApiKey(keyId);
    } catch (err) {
      if (err instanceof AuthError) {
        window.location.reload();
      } else {
        setError('Failed to delete API key');
        // Reload the authoritative list on failure.
        getApiKeys().then(setKeys).catch(() => {});
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">API Keys</h2>
          <button
            onClick={onClose}
            className="appearance-none text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            aria-label="Close"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto p-6 flex flex-col gap-5">
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            Personal tokens for programmatic access to the HomeStock API. Send a key in the{' '}
            <code className="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">X-API-Key</code>{' '}
            header. A key has the same access as your account.
          </p>

          {/* Generate row */}
          <div className="flex flex-col sm:flex-row gap-2 sm:items-end">
            <div className="flex-1 flex flex-col gap-1">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Label</label>
              <input
                type="text"
                value={label}
                onChange={e => { setLabel(e.target.value); setError(''); }}
                onKeyDown={e => { if (e.key === 'Enter') handleGenerate(); }}
                placeholder="e.g. home-assistant"
                maxLength={100}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
              />
            </div>
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="px-4 py-2 rounded-lg bg-[#A3E635] hover:bg-[#8BC82E] text-gray-900 text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
            >
              {isGenerating ? 'Generating…' : 'Generate Token'}
            </button>
          </div>

          {/* One-time key call-out */}
          {createdKey && (
            <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-300 dark:border-amber-700 rounded-lg p-4 flex flex-col gap-2">
              <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
                Copy your new key now — you won't be able to see it again.
              </p>
              <div className="flex items-center gap-2">
                <code className="flex-1 px-3 py-2 rounded-md bg-white dark:bg-gray-900 border border-amber-300 dark:border-amber-700 text-gray-900 dark:text-gray-100 text-xs break-all font-mono">
                  {createdKey.key}
                </code>
                <button
                  onClick={handleCopy}
                  className="appearance-none px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm font-medium transition-colors whitespace-nowrap"
                >
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-400 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Keys table */}
          {isLoading ? (
            <p className="text-gray-500 dark:text-gray-400 text-center py-8">Loading…</p>
          ) : keys.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400 text-center py-8">No API keys yet.</p>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
                    <tr>
                      <th className="px-1.5 py-1.5 md:px-4 md:py-3 text-left text-xs md:text-base font-semibold text-gray-900 dark:text-gray-100">Label</th>
                      <th className="px-1.5 py-1.5 md:px-4 md:py-3 text-left text-xs md:text-base font-semibold text-gray-900 dark:text-gray-100">Prefix</th>
                      <th className="px-1.5 py-1.5 md:px-4 md:py-3 text-left text-xs md:text-base font-semibold text-gray-900 dark:text-gray-100">Created</th>
                      <th className="px-1.5 py-1.5 md:px-4 md:py-3 text-left text-xs md:text-base font-semibold text-gray-900 dark:text-gray-100">Last used</th>
                      <th className="px-1.5 py-1.5 md:px-4 md:py-3 text-center text-xs md:text-base font-semibold text-gray-900 dark:text-gray-100">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    {keys.map(k => (
                      <tr key={k.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-2 py-2 md:px-4 md:py-3 text-xs md:text-base text-gray-900 dark:text-gray-100">{k.label}</td>
                        <td className="px-2 py-2 md:px-4 md:py-3 text-xs md:text-base text-gray-500 dark:text-gray-400 font-mono">{k.key_prefix}…</td>
                        <td className="px-2 py-2 md:px-4 md:py-3 text-xs md:text-base text-gray-900 dark:text-gray-100">{formatDate(k.created_at)}</td>
                        <td className="px-2 py-2 md:px-4 md:py-3 text-xs md:text-base text-gray-900 dark:text-gray-100">{formatDate(k.last_used_at)}</td>
                        <td className="px-2 py-2 md:px-4 md:py-3 text-center">
                          <div className="flex items-center justify-center gap-1 md:gap-2">
                            <button
                              onClick={() => handleDelete(k.id)}
                              className="appearance-none px-2 py-1 md:px-3 md:py-2 !bg-red-500 text-white text-xs md:text-sm rounded-md hover:!bg-red-600 transition-colors inline-flex items-center justify-center gap-1 md:gap-2"
                              title="Delete key"
                            >
                              <TrashIcon />
                              <span className="hidden sm:inline">Delete</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onClose}
            className="appearance-none px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default ApiKeysSettingsOverlay;
