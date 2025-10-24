import { useState } from 'react'
import './App.css'
import SideBar from "./components/sidebar/SideBar.tsx"
import InventoryScreen from './components/main/InventoryScreen.tsx'
import type { InventoryType } from './types/InventoryTypes.ts'

function App() {
  const [currentScreen, setCurrentScreen] = useState<InventoryType>('food');

  const handleNavigate = (screen: InventoryType) => {
    setCurrentScreen(screen);
  };

  return (
    <div className='flex h-screen w-full overflow-hidden'>
      <SideBar currentScreen={currentScreen} onNavigate={handleNavigate}/>
      <InventoryScreen screenType={currentScreen}/>
    </div>
  )
}

export default App
