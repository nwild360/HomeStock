import { useState } from 'react'
import './App.css'
import LoginScreen from './components/login/LoginScreen.tsx'
import SideBar from "./components/sidebar/SideBar.tsx"
import AddItemOverlay from './components/sidebar/AddItemOverlay.tsx';
import InventoryScreen from './components/main/InventoryScreen.tsx'
import type { InventoryType } from './types/InventoryTypes.ts'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentScreen, setCurrentScreen] = useState<InventoryType>('food');
  const [isAddItemOpen, setIsAddItemOpen] = useState(false);

  const handleNavigate = (screen: InventoryType) => {
    setCurrentScreen(screen);
  };

  const handleLogin = (username: string, password: string) => {
    // TODO: Add actual backend authentication here
    console.log('Login attempt:', username, password);

    // For now, just set logged in and navigate to food inventory
    setIsLoggedIn(true);
    setCurrentScreen('food');
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
        />
      <AddItemOverlay
        isOpen={isAddItemOpen}
        onClose={() => setIsAddItemOpen(false)}
      />
      <InventoryScreen screenType={currentScreen}/>
    </div>
  )
}

export default App
