import { useState } from 'react'
import './App.css'
import LoginScreen from './components/login/LoginScreen.tsx'
import SideBar from "./components/sidebar/SideBar.tsx"
import AddItemOverlay from './components/sidebar/AddItemOverlay.tsx';
import InventoryScreen from './components/main/InventoryScreen.tsx'
import DataScreen from './components/main/data/DataScreen.tsx'
import type { ScreenType, InventoryType } from './types/InventoryTypes.ts'
import { login, logout, AuthError } from './services/AuthService.ts'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentScreen, setCurrentScreen] = useState<ScreenType>('food');
  const [isAddItemOpen, setIsAddItemOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0); // Trigger re-fetch when incremented

  const handleNavigate = (screen: ScreenType) => {
    setCurrentScreen(screen);
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
      <SideBar
        currentScreen={currentScreen}
        onNavigate={handleNavigate}
        onAddItem={() => setIsAddItemOpen(true)}
        onLogout={handleLogout}
        />
      <AddItemOverlay
        isOpen={isAddItemOpen}
        onClose={() => setIsAddItemOpen(false)}
        onItemCreated={() => setRefreshKey(prev => prev + 1)}
      />
      {currentScreen === 'data' ? (
        <DataScreen
          refreshKey={refreshKey}
          onRefresh={() => setRefreshKey(prev => prev + 1)}
        />
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
