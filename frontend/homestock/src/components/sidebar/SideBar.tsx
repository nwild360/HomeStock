import { useState } from 'react';
import logo from '../../assets/HomeStock.svg';
import AddItemButton from './AddItemButton.tsx';
import NavMenu from './NavMenu.tsx';
import type { InventoryType } from '../../types/InventoryTypes.ts';

interface SidebarProps {
  currentScreen: InventoryType;
  onAddItem?: () => void;
  onNavigate?: (item: string) => void;
}

function Sidebar({ currentScreen, onAddItem, onNavigate }: SidebarProps) {
  const [isOpen, setIsOpen] = useState(false);
  
    const handleNavigate = (screen: InventoryType) => {
    onNavigate?.(screen);
    setIsOpen(false);
  };
  
  return (
    <div className="flex min-h-screen">
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-4 left-4 z-50 p-2 bg-gray-900 text-white rounded-lg md:hidden"
        aria-label="Toggle menu"
      >
        <div className="w-6 h-5 flex flex-col justify-between">
          <span className="block w-full h-0.5 bg-white"></span>
          <span className="block w-full h-0.5 bg-white"></span>
          <span className="block w-full h-0.5 bg-white"></span>
        </div>
      </button>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:relative inset-y-0 left-0 z-40 w-64 bg-gray-700 text-white flex flex-col transition-transform duration-300 ease-in-out md:transform-none ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } md:translate-x-0`}
      >
        {/* Logo and App Name */}
        <div className="flex items-center gap-3 p-5 border-b border-gray-600">
            <img 
            src={logo}
            alt="HomeStock Logo" 
            className="w-11 h-10"
            />
          <span className="text-3xl font-semibold text-[#A3E635]">HomeStock</span>
        </div>

        {/* Add Item Button */}
        <div className="p-4">
            <AddItemButton 
                onClick={() => {
                    onAddItem?.();
                    setIsOpen(false);
                    }}
        />
        </div>

        {/* Navigation Menu */}
          <NavMenu 
            currentScreen={currentScreen}
            onNavigate={handleNavigate}
          />
      </aside>
    </div>
  );
}

export default Sidebar;