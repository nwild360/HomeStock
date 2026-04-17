import { useState } from 'react';
import OidcSettingsOverlay from './OidcSettingsOverlay';

function SettingsScreen() {
  const [isOidcOpen, setIsOidcOpen] = useState(false);

  return (
    <div className="flex-1 w-full min-w-0 p-3 md:p-8 bg-gray-50 overflow-auto">
      <h1 className="text-3xl md:text-5xl font-bold text-gray-900 mb-4 md:mb-8">
        Settings
      </h1>

      {/* Authentication */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
          Authentication
        </h2>
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm divide-y divide-gray-200">
          <div className="flex items-center justify-between p-5">
            <div>
              <p className="text-gray-900 font-medium">SSO / OIDC</p>
              <p className="text-gray-500 text-sm mt-0.5">
                Configure Single Sign-On via Keycloak
              </p>
            </div>
            <button
              onClick={() => setIsOidcOpen(true)}
              className="appearance-none px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 text-sm font-medium transition-colors"
            >
              Configure
            </button>
          </div>
        </div>
      </section>

      <OidcSettingsOverlay isOpen={isOidcOpen} onClose={() => setIsOidcOpen(false)} />
    </div>
  );
}

export default SettingsScreen;
