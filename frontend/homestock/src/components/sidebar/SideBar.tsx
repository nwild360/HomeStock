import { useState } from 'react';
import logo from '../../assets/HomeStock.svg';
import AddItemButton from './AddItemButton.tsx';
import NavMenu from './NavMenu.tsx';
import type { ScreenType } from '../../types/InventoryTypes.ts';

interface SidebarProps {
  currentScreen: ScreenType;
  onAddItem?: () => void;
  onNavigate?: (screen: ScreenType) => void;
  onLogout?: () => void;
}

function Sidebar({ currentScreen, onAddItem, onNavigate, onLogout }: SidebarProps) {
  const [isOpen, setIsOpen] = useState(false);

    const handleNavigate = (screen: ScreenType) => {
    onNavigate?.(screen);
    setIsOpen(false);
  };

  const handleLogout = () => {
    onLogout?.();
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

        {/* Logout Button */}
        <div className="mt-auto p-4 border-t border-gray-600">
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-lg bg-red-600 hover:bg-red-700 transition-colors text-white font-medium"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M3 3a1 1 0 00-1 1v12a1 1 0 001 1h12a1 1 0 001-1V4a1 1 0 00-1-1H3zm11 4.414l-4.293 4.293a1 1 0 01-1.414 0L4 7.414 5.414 6l3.293 3.293L13 5l1 1.414z"
                clipRule="evenodd"
              />
              <path
                fillRule="evenodd"
                d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3h-2V4H4v12h11v-2h2v3a1 1 0 01-1 1H4a1 1 0 01-1-1V3z"
                clipRule="evenodd"
              />
              <path
                fillRule="evenodd"
                d="M10 9a1 1 0 011 1v6a1 1 0 11-2 0v-6a1 1 0 011-1z"
                clipRule="evenodd"
              />
            </svg>
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </div>
  );
}

export default Sidebar;