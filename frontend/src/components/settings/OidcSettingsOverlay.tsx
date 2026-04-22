import { useState, useEffect } from 'react';
import { getOidcSettings, saveOidcSettings, type OidcSettings } from '../../services/AuthService';

interface OidcSettingsOverlayProps {
  isOpen: boolean;
  onClose: () => void;
}

const EMPTY: OidcSettings = {
  enabled: false,
  issuer_url: '',
  client_id: '',
  client_secret: '',
  redirect_uri: '',
};

function OidcSettingsOverlay({ isOpen, onClose }: OidcSettingsOverlayProps) {
  const [form, setForm] = useState<OidcSettings>(EMPTY);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showSecret, setShowSecret] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setError('');
    setSuccess('');
    setIsLoading(true);
    getOidcSettings()
      .then(data => setForm(data))
      .catch(() => setError('Failed to load OIDC settings'))
      .finally(() => setIsLoading(false));
  }, [isOpen]);

  const handleChange = (field: keyof OidcSettings, value: string | boolean) => {
    setForm(prev => ({ ...prev, [field]: value }));
    setError('');
    setSuccess('');
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError('');
    setSuccess('');
    try {
      await saveOidcSettings(form);
      setSuccess('Settings saved successfully');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">OIDC / SSO Configuration</h2>
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
          {isLoading ? (
            <p className="text-gray-500 dark:text-gray-400 text-center py-8">Loading…</p>
          ) : (
            <>
              {/* Enable toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-900 dark:text-gray-100 font-medium">Enable SSO</p>
                  <p className="text-gray-500 text-sm mt-0.5">Show "Sign in with SSO" on the login screen</p>
                </div>
                <button
                  role="switch"
                  aria-checked={form.enabled}
                  onClick={() => handleChange('enabled', !form.enabled)}
                  className={`appearance-none relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    form.enabled ? '!bg-[#A3E635]' : '!bg-gray-300 dark:!bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                      form.enabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              <hr className="border-gray-200 dark:border-gray-700" />

              {/* Issuer URL */}
              <div className="flex flex-col gap-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Issuer URL</label>
                <input
                  type="url"
                  value={form.issuer_url ?? ''}
                  onChange={e => handleChange('issuer_url', e.target.value)}
                  placeholder="https://keycloak.local/realms/homestock"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
                />
                <p className="text-gray-500 text-xs">Your Keycloak realm URL (without /.well-known/…)</p>
              </div>

              {/* Client ID */}
              <div className="flex flex-col gap-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Client ID</label>
                <input
                  type="text"
                  value={form.client_id ?? ''}
                  onChange={e => handleChange('client_id', e.target.value)}
                  placeholder="homestock"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
                />
              </div>

              {/* Client Secret */}
              <div className="flex flex-col gap-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Client Secret</label>
                <div className="relative">
                  <input
                    type={showSecret ? 'text' : 'password'}
                    value={form.client_secret ?? ''}
                    onChange={e => handleChange('client_secret', e.target.value)}
                    placeholder="••••••••••••••••"
                    className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => setShowSecret(s => !s)}
                    className="appearance-none absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    aria-label={showSecret ? 'Hide secret' : 'Show secret'}
                  >
                    {showSecret ? (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    ) : (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {/* Redirect URI */}
              <div className="flex flex-col gap-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Redirect URI</label>
                <input
                  type="url"
                  value={form.redirect_uri ?? ''}
                  onChange={e => handleChange('redirect_uri', e.target.value)}
                  placeholder="https://homestock.local/api/auth/oidc/callback"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
                />
                <p className="text-gray-500 text-xs">Must match the redirect URI registered in Keycloak</p>
              </div>

              {/* Feedback */}
              {error && (
                <div className="bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-400 px-4 py-3 rounded">
                  {error}
                </div>
              )}
              {success && (
                <div className="bg-green-100 dark:bg-green-900/30 border border-green-400 dark:border-green-700 text-green-700 dark:text-green-400 px-4 py-3 rounded">
                  {success}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onClose}
            className="appearance-none px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || isLoading}
            className="px-4 py-2 rounded-lg bg-[#A3E635] hover:bg-[#8BC82E] text-gray-900 text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default OidcSettingsOverlay;
