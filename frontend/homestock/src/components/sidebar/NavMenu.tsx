import { type InventoryType, MENU_ITEMS } from '../../types/InventoryTypes.ts';

interface NavMenuProps {
  currentScreen: InventoryType;
  onNavigate: (screen: InventoryType) => void;
  onClose?: () => void;
}

function NavMenu({ currentScreen, onNavigate, onClose }: NavMenuProps) {
  const handleClick = (itemId: InventoryType) => {
    onNavigate(itemId);
    onClose?.();
  };

  return (
    <nav className="flex-1 px-4">
      {MENU_ITEMS.map((item) => (
        <button
          key={item.id}
          onClick={() => handleClick(item.id)}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-left ${
            currentScreen === item.id 
              ? 'bg-gray-800 text-[#A3E635]' 
              : 'hover:bg-gray-800'
          }`}
        >
          <img 
            src={item.icon} 
            alt={`${item.label} icon`}
            className="w-6 h-6"
          />
          <span className="capitalize">{item.label}</span>
        </button>
      ))}
    </nav>
  );
}

export default NavMenu;