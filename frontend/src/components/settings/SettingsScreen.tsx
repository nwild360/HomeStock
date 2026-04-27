import { useState } from 'react';
import OidcSettingsOverlay from './OidcSettingsOverlay';
import ReceiptScanSettingsOverlay from './ReceiptScanSettingsOverlay';

function SettingsScreen() {
  const [isOidcOpen, setIsOidcOpen] = useState(false);
  const [isReceiptScanOpen, setIsReceiptScanOpen] = useState(false);

  return (
    <div className="flex-1 w-full min-w-0 p-3 md:p-8 bg-gray-50 dark:bg-gray-900 overflow-auto">
      <h1 className="text-3xl md:text-5xl font-bold text-gray-900 dark:text-gray-100 mb-4 md:mb-8">
        Settings
      </h1>

      {/* Authentication */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
          Authentication
        </h2>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm divide-y divide-gray-200 dark:divide-gray-700">
          <div className="flex items-center justify-between p-5">
            <div>
              <p className="text-gray-900 dark:text-gray-100 font-medium">SSO / OIDC</p>
              <p className="text-gray-500 text-sm mt-0.5">
                Configure Single Sign-On via Keycloak
              </p>
            </div>
            <button
              onClick={() => setIsOidcOpen(true)}
              className="appearance-none px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm font-medium transition-colors"
            >
              Configure
            </button>
          </div>
        </div>
      </section>

      {/* Integrations */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
          Integrations
        </h2>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm divide-y divide-gray-200 dark:divide-gray-700">
          <div className="flex items-center justify-between p-5">
            <div>
              <p className="text-gray-900 dark:text-gray-100 font-medium">Receipt Scan</p>
              <p className="text-gray-500 text-sm mt-0.5">
                AI-powered receipt parsing via Claude or Ollama
              </p>
            </div>
            <button
              onClick={() => setIsReceiptScanOpen(true)}
              className="appearance-none px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm font-medium transition-colors"
            >
              Configure
            </button>
          </div>
        </div>
      </section>

      <OidcSettingsOverlay isOpen={isOidcOpen} onClose={() => setIsOidcOpen(false)} />
      <ReceiptScanSettingsOverlay isOpen={isReceiptScanOpen} onClose={() => setIsReceiptScanOpen(false)} />
    </div>
  );
}

export default SettingsScreen;
