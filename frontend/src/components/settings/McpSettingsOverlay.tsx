import { useState, useEffect } from 'react';
import { getMcpSettings, saveMcpSettings, type McpSettings } from '../../services/McpService';
import { getOidcConfig } from '../../services/AuthService';

interface McpSettingsOverlayProps {
  isOpen: boolean;
  onClose: () => void;
}

const EMPTY: McpSettings = {
  enabled: false,
  allow_api_keys: false,
  server_url: null,
  required_scope: 'mcp:tools',
};

function Toggle({ checked, onChange }: { checked: boolean; onChange: () => void }) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      onClick={onChange}
      className={`appearance-none relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        checked ? '!bg-[#A3E635]' : '!bg-gray-300 dark:!bg-gray-600'
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
          checked ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  );
}

function CopyField({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  return (
    <div className="flex gap-2">
      <input
        type="text"
        readOnly
        value={value}
        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 font-mono text-xs outline-none"
      />
      <button
        type="button"
        onClick={copy}
        className="appearance-none px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 text-xs font-medium transition-colors shrink-0"
      >
        {copied ? 'Copied!' : 'Copy'}
      </button>
    </div>
  );
}

function McpSettingsOverlay({ isOpen, onClose }: McpSettingsOverlayProps) {
  const [form, setForm] = useState<McpSettings>(EMPTY);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [oidcEnabled, setOidcEnabled] = useState(false);

  const defaultEndpoint = `${window.location.origin}/mcp`;

  useEffect(() => {
    if (!isOpen) return;
    setError('');
    setSuccess('');
    setIsLoading(true);
    Promise.all([
      getMcpSettings(),
      getOidcConfig().catch(() => ({ enabled: false })),
    ])
      .then(([settings, oidc]) => {
        setForm({ ...settings, server_url: settings.server_url || defaultEndpoint });
        setOidcEnabled(oidc.enabled);
      })
      .catch(() => setError('Failed to load MCP settings'))
      .finally(() => setIsLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  const handleChange = (field: keyof McpSettings, value: string | boolean | null) => {
    setForm(prev => ({ ...prev, [field]: value }));
    setError('');
    setSuccess('');
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError('');
    setSuccess('');
    try {
      const saved = await saveMcpSettings(form);
      setForm({ ...saved, server_url: saved.server_url || defaultEndpoint });
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
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">MCP Server Configuration</h2>
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
                  <p className="text-gray-900 dark:text-gray-100 font-medium">Enable MCP Server</p>
                  <p className="text-gray-500 text-sm mt-0.5">
                    Let AI agents manage your inventory via the Model Context Protocol
                  </p>
                </div>
                <Toggle checked={form.enabled} onChange={() => handleChange('enabled', !form.enabled)} />
              </div>

              <hr className="border-gray-200 dark:border-gray-700" />

              {/* Endpoint */}
              <div className="flex flex-col gap-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">MCP Endpoint</label>
                <CopyField value={defaultEndpoint} />
                <p className="text-gray-500 text-xs">
                  Point your MCP client (Claude Code, Claude Desktop, …) at this URL using the Streamable HTTP transport.
                </p>
              </div>

              {/* OAuth section */}
              <div className="flex flex-col gap-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  OAuth Sign-In (recommended)
                </label>
                {oidcEnabled ? (
                  <p className="text-gray-500 text-xs">
                    Agents sign in through your SSO / OIDC provider with short-lived tokens. Connect with:
                  </p>
                ) : (
                  <p className="text-amber-600 dark:text-amber-400 text-xs">
                    SSO / OIDC is not configured — OAuth sign-in is unavailable. Configure it under
                    Settings → SSO / OIDC, or allow API key auth below.
                  </p>
                )}
                {oidcEnabled && (
                  <CopyField value={`claude mcp add --transport http homestock ${form.server_url || defaultEndpoint}`} />
                )}
              </div>

              {oidcEnabled && (
                <div className="flex flex-col gap-1">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Server URL (OAuth audience)</label>
                  <input
                    type="url"
                    value={form.server_url ?? ''}
                    onChange={e => handleChange('server_url', e.target.value || null)}
                    placeholder={defaultEndpoint}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
                  />
                  <p className="text-gray-500 text-xs">
                    Public URL of this MCP server as agents reach it — access tokens must carry it as their audience
                    (configure an Audience mapper in Keycloak).
                  </p>
                </div>
              )}

              {oidcEnabled && (
                <div className="flex flex-col gap-1">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Required scope</label>
                  <input
                    type="text"
                    value={form.required_scope ?? ''}
                    onChange={e => handleChange('required_scope', e.target.value || null)}
                    placeholder="mcp:tools"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
                  />
                  <p className="text-gray-500 text-xs">
                    OAuth scope that must be present on agent tokens. Leave blank if your realm grants MCP access
                    via client roles instead of scopes — the audience check above still applies.
                  </p>
                </div>
              )}

              <hr className="border-gray-200 dark:border-gray-700" />

              {/* API key fallback */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-900 dark:text-gray-100 font-medium">Allow API Key Auth</p>
                  <p className="text-gray-500 text-sm mt-0.5">
                    Fallback for headless agents — long-lived keys, less secure than OAuth
                  </p>
                </div>
                <Toggle checked={form.allow_api_keys} onChange={() => handleChange('allow_api_keys', !form.allow_api_keys)} />
              </div>
              {form.allow_api_keys && (
                <div className="flex flex-col gap-1">
                  <p className="text-gray-500 text-xs">
                    Create keys under Settings → API Keys, then connect with:
                  </p>
                  <CopyField
                    value={`claude mcp add --transport http homestock ${defaultEndpoint} --header "Authorization: Bearer hs_live_..."`}
                  />
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

export default McpSettingsOverlay;
