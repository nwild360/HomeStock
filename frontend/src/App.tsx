import { useState, useEffect, useRef } from 'react'
import './App.css'
import LoginScreen from './components/login/LoginScreen.tsx'
import SideBar from "./components/sidebar/SideBar.tsx"
import AddItemOverlay from './components/sidebar/AddItemOverlay.tsx';
import InventoryScreen from './components/main/InventoryScreen.tsx'
import DataScreen from './components/main/data/DataScreen.tsx'
import UserScreen from './components/users/UserScreen.tsx'
import SettingsScreen from './components/settings/SettingsScreen.tsx'
import UtilitiesScreen from './components/utilities/UtilitiesScreen.tsx'
import type { ScreenType, InventoryType } from './types/InventoryTypes.ts'
import { login, logout, isAuthenticated, AuthError } from './services/AuthService.ts'
import { scanReceipt, type CandidateItem } from './services/ReceiptService.ts'
import ReceiptReviewOverlay from './components/sidebar/ReceiptReviewOverlay.tsx'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentScreen, setCurrentScreen] = useState<ScreenType>('food');
  const [isAddItemOpen, setIsAddItemOpen] = useState(false);
  const [isScanLoading, setIsScanLoading] = useState(false);
  const [isScanOpen, setIsScanOpen] = useState(false);
  const [scanCandidates, setScanCandidates] = useState<CandidateItem[]>([]);
  const [scanError, setScanError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // On mount, check if the user already has a valid session (e.g. after OIDC callback redirect)
  useEffect(() => {
    isAuthenticated().then(authenticated => {
      if (authenticated) setIsLoggedIn(true);
    });
  }, []);

  const handleNavigate = (screen: ScreenType) => {
    setCurrentScreen(screen);
  };

  const handleScanReceipt = () => {
    setScanError('');
    fileInputRef.current?.click();
  };

  // iOS may deliver HEIC/HEIF even when accept="image/jpeg" — convert via canvas before upload.
  // iOS Safari can decode HEIC natively, so drawing to a canvas and re-exporting as JPEG works.
  const normalizeImageForUpload = (file: File): Promise<File> => {
    if (['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      return Promise.resolve(file);
    }
    return new Promise((resolve, reject) => {
      const img = new Image();
      const url = URL.createObjectURL(file);
      img.onload = () => {
        URL.revokeObjectURL(url);
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        const ctx = canvas.getContext('2d');
        if (!ctx) { reject(new Error('Canvas not available')); return; }
        ctx.drawImage(img, 0, 0);
        canvas.toBlob(
          blob => {
            if (!blob) { reject(new Error('Image conversion failed')); return; }
            resolve(new File([blob], 'receipt.jpg', { type: 'image/jpeg' }));
          },
          'image/jpeg',
          0.92,
        );
      };
      img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('Failed to load image')); };
      img.src = url;
    });
  };

  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = ''; // reset so same file can be re-selected
    setIsScanLoading(true);
    setScanError('');
    try {
      const normalized = await normalizeImageForUpload(file);
      const items = await scanReceipt(normalized);
      setScanCandidates(items);
      setIsScanOpen(true);
    } catch (err) {
      setScanError(err instanceof Error ? err.message : 'Receipt scan failed');
    } finally {
      setIsScanLoading(false);
    }
  };

  const handleLogin = async (username: string, password: string) => {
    try {
      // Call backend authentication
      const response = await login(username, password);
      console.log('Login successful:', response.username);

      // Set logged in and navigate to food inventory
      setIsLoggedIn(true);
      setCurrentScreen('food');
    } catch (error) {
      // Re-throw error to let LoginScreen handle display
      if (error instanceof AuthError) {
        throw error;
      }
      throw new AuthError('An unexpected error occurred');
    }
  };

  const handleLogout = async () => {
    try {
      // Clear httpOnly cookie on backend
      await logout();
      console.log('User logged out successfully');
    } catch (error) {
      console.error('Logout error:', error);
      // Continue with logout even if backend call fails
    } finally {
      // Reset state and return to login screen
      setIsLoggedIn(false);
      setCurrentScreen('food'); // Reset to default screen for next login
    }
  };

  // Show login screen if not logged in
  if (!isLoggedIn) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  // Show main app if logged in
  return (
    <div className='flex h-screen w-full overflow-hidden'>
      {/* Hidden file input for receipt camera/file selection */}
      <input
        type="file"
        accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
        capture="environment"
        ref={fileInputRef}
        onChange={handleFileSelected}
        className="hidden"
      />

      {/* Scanning loading overlay */}
      {isScanLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-8 flex flex-col items-center gap-4 shadow-xl">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#A3E635]" />
            <p className="text-gray-700 dark:text-gray-200 font-medium">Scanning receipt…</p>
          </div>
        </div>
      )}

      {/* Scan error toast */}
      {scanError && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-red-600 text-white px-5 py-3 rounded-lg shadow-lg flex items-center gap-3">
          <span>{scanError}</span>
          <button
            onClick={() => setScanError('')}
            className="appearance-none text-white/80 hover:text-white"
            aria-label="Dismiss"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      <SideBar
        currentScreen={currentScreen}
        onNavigate={handleNavigate}
        onAddItem={() => setIsAddItemOpen(true)}
        onScanReceipt={handleScanReceipt}
        onLogout={handleLogout}
        />
      <AddItemOverlay
        isOpen={isAddItemOpen}
        onClose={() => setIsAddItemOpen(false)}
        onItemCreated={() => setRefreshKey(prev => prev + 1)}
      />
      <ReceiptReviewOverlay
        isOpen={isScanOpen}
        candidates={scanCandidates}
        onClose={() => { setIsScanOpen(false); setScanCandidates([]); }}
        onItemsAdded={() => { setRefreshKey(prev => prev + 1); setIsScanOpen(false); setScanCandidates([]); }}
      />
      {currentScreen === 'data' ? (
        <DataScreen
          refreshKey={refreshKey}
          onRefresh={() => setRefreshKey(prev => prev + 1)}
        />
      ) : currentScreen === 'users' ? (
        <UserScreen
          refreshKey={refreshKey}
          onRefresh={() => setRefreshKey(prev => prev + 1)}
        />
      ) : currentScreen === 'settings' ? (
        <SettingsScreen />
      ) : currentScreen === 'utilities' ? (
        <UtilitiesScreen />
      ) : (
        <InventoryScreen
          screenType={currentScreen as InventoryType}
          refreshKey={refreshKey}
          onRefresh={() => setRefreshKey(prev => prev + 1)}
        />
      )}
    </div>
  )
}

export default App
