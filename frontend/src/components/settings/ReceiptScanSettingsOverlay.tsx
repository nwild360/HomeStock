import { useState, useEffect } from 'react';
import { getReceiptScanSettings, saveReceiptScanSettings, type ReceiptScanSettings } from '../../services/ReceiptService';

interface ReceiptScanSettingsOverlayProps {
  isOpen: boolean;
  onClose: () => void;
}

const EMPTY: ReceiptScanSettings = {
  enabled: false,
  provider: null,
  api_key: null,
  model: null,
  endpoint_url: null,
};

function ReceiptScanSettingsOverlay({ isOpen, onClose }: ReceiptScanSettingsOverlayProps) {
  const [form, setForm] = useState<ReceiptScanSettings>(EMPTY);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  // True when the server has a Claude API key stored — the GET response never returns the key itself
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setError('');
    setSuccess('');
    setApiKeyConfigured(false);
    setIsLoading(true);
    getReceiptScanSettings()
      .then(data => {
        setForm(data);
        setApiKeyConfigured(data.provider === 'claude');
      })
      .catch(() => setError('Failed to load receipt scan settings'))
      .finally(() => setIsLoading(false));
  }, [isOpen]);

  const handleChange = (field: keyof ReceiptScanSettings, value: string | boolean | null) => {
    setForm(prev => ({ ...prev, [field]: value }));
    setError('');
    setSuccess('');
  };

  const handleProviderChange = (provider: 'claude' | 'ollama') => {
    setForm(prev => ({ ...prev, provider, api_key: null, endpoint_url: null }));
    setApiKeyConfigured(false);
    setError('');
    setSuccess('');
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError('');
    setSuccess('');
    try {
      await saveReceiptScanSettings(form);
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
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Receipt Scan Configuration</h2>
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
                  <p className="text-gray-900 dark:text-gray-100 font-medium">Enable Receipt Scanning</p>
                  <p className="text-gray-500 text-sm mt-0.5">Show "Scan Receipt" button in the sidebar</p>
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

              {/* Provider */}
              <div className="flex flex-col gap-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">AI Provider</label>
                <select
                  value={form.provider ?? ''}
                  onChange={e => handleProviderChange(e.target.value as 'claude' | 'ollama')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
                >
                  <option value="">Select a provider…</option>
                  <option value="claude">Claude (Anthropic API)</option>
                  <option value="ollama">Ollama (local)</option>
                </select>
              </div>

              {/* Model */}
              <div className="flex flex-col gap-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Model</label>
                <input
                  type="text"
                  value={form.model ?? ''}
                  onChange={e => handleChange('model', e.target.value || null)}
                  placeholder={form.provider === 'ollama' ? 'llava' : 'claude-haiku-4-5-20251001'}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
                />
                <p className="text-gray-500 text-xs">
                  {form.provider === 'ollama'
                    ? 'A vision-capable Ollama model, e.g. llava or moondream'
                    : 'A Claude model with vision support'}
                </p>
              </div>

              {/* Claude: API Key */}
              {form.provider === 'claude' && (
                <div className="flex flex-col gap-1">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">API Key</label>
                  <div className="relative">
                    <input
                      type={showApiKey ? 'text' : 'password'}
                      value={form.api_key ?? ''}
                      onChange={e => handleChange('api_key', e.target.value || null)}
                      placeholder="sk-ant-••••••••••••••••"
                      className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(s => !s)}
                      className="appearance-none absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                      aria-label={showApiKey ? 'Hide API key' : 'Show API key'}
                    >
                      {showApiKey ? (
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
                  {apiKeyConfigured && !form.api_key ? (
                    <p className="text-gray-500 text-xs">API key is saved — leave blank to keep existing key</p>
                  ) : (
                    <p className="text-gray-500 text-xs">Your Anthropic API key from console.anthropic.com</p>
                  )}
                </div>
              )}

              {/* Ollama: Endpoint URL */}
              {form.provider === 'ollama' && (
                <div className="flex flex-col gap-1">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Ollama Endpoint URL</label>
                  <input
                    type="url"
                    value={form.endpoint_url ?? ''}
                    onChange={e => handleChange('endpoint_url', e.target.value || null)}
                    placeholder="http://ollama:11434"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
                  />
                  <p className="text-gray-500 text-xs">Base URL of your Ollama instance (no trailing slash)</p>
                </div>
              )}

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

export default ReceiptScanSettingsOverlay;
