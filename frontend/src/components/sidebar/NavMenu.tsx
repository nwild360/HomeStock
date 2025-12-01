import { type ScreenType, MENU_ITEMS } from '../../types/InventoryTypes.ts';

interface NavMenuProps {
  currentScreen: ScreenType;
  onNavigate: (screen: ScreenType) => void;
  onClose?: () => void;
}

function NavMenu({ currentScreen, onNavigate, onClose }: NavMenuProps) {
  const handleClick = (itemId: ScreenType) => {
    onNavigate(itemId);
    onClose?.();
  };

  return (
    <nav className="flex-1 px-4">
      {MENU_ITEMS.map((item) => (
        <div key={item.id}>
          {/* Separator line */}
          {item.separator && (
            <div className="my-3 border-t border-gray-600" />
          )}

          <button
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
        </div>
      ))}
    </nav>
  );
}

export default NavMenu;