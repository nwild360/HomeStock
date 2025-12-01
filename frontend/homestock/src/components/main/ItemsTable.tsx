import CircleButton from './CircleButton.tsx';
import {PlusIcon, MinusIcon} from './CircleButton.tsx';

interface InventoryItem {
  id: string;
  name: string;
  category: string;
  quantity: number;
  unit: string;
}

interface ItemsTableProps {
  items: InventoryItem[];
  onQuantityChange: (id: string, newQuantity: number) => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}

// Pencil Icon Component
const PencilIcon = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 528.899 528.899"
    fill="currentColor"
    xmlns="http://www.w3.org/2000/svg"
    className="flex-shrink-0"
  >
    <path d="M328.883,89.125l107.59,107.589l-272.34,272.34L56.604,361.465L328.883,89.125z M518.113,63.177l-47.981-47.981c-18.543-18.543-48.653-18.543-67.259,0l-45.961,45.961l107.59,107.59l53.611-53.611C532.495,100.753,532.495,77.559,518.113,63.177z M0.3,512.69c-1.958,8.812,5.998,16.708,14.811,14.565l119.891-29.069L27.473,390.597L0.3,512.69z"/>
  </svg>
);

// Trash Icon Component
const TrashIcon = () => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 101 101"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className="flex-shrink-0"
  >
    <path
      d="M12.625 25.25H21.0417M21.0417 25.25H88.375M21.0417 25.25V84.1666C21.0417 86.3989 21.9284 88.5397 23.5069 90.1181C25.0853 91.6965 27.2261 92.5833 29.4583 92.5833H71.5417C73.7739 92.5833 75.9147 91.6965 77.4931 90.1181C79.0716 88.5397 79.9583 86.3989 79.9583 84.1666V25.25M33.6667 25.25V16.8333C33.6667 14.6011 34.5534 12.4602 36.1319 10.8818C37.7103 9.30338 39.8511 8.41663 42.0833 8.41663H58.9167C61.1489 8.41663 63.2897 9.30338 64.8681 10.8818C66.4466 12.4602 67.3333 14.6011 67.3333 16.8333V25.25M42.0833 46.2916V71.5416M58.9167 46.2916V71.5416"
      stroke="currentColor"
      strokeWidth="4"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

function ItemsTable({ items, onQuantityChange, onEdit, onDelete }: ItemsTableProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-1.5 py-1.5 md:px-4 md:py-3 text-left text-xs md:text-base font-semibold text-gray-900">Item Name</th>
              <th className="px-1.5 py-1.5 md:px-4 md:py-3 text-left text-xs md:text-base font-semibold text-gray-900">Category</th>
              <th className="px-1.5 py-1.5 md:px-4 md:py-3 text-center text-xs md:text-base font-semibold text-gray-900">Quantity</th>
              <th className="px-1.5 py-1.5 md:px-4 md:py-3 text-left text-xs md:text-base font-semibold text-gray-900">Unit(s)</th>
              <th className="px-1.5 py-1.5 md:px-4 md:py-3 text-center text-xs md:text-base font-semibold text-gray-900">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="px-2 py-2 md:px-4 md:py-3 text-xs md:text-base text-gray-900">{item.name}</td>
                <td className="px-2 py-2 md:px-4 md:py-3 text-xs md:text-base text-gray-600">{item.category}</td>
                <td className="px-2 py-2 md:px-4 md:py-3">
                  <div className="flex items-center justify-center gap-1 md:gap-2">
                    <CircleButton 
                      onClick={() => onQuantityChange(item.id, item.quantity + 1)}
                      ariaLabel="Increase quantity"
                    >
                      <PlusIcon />
                    </CircleButton>
                    
                    <input
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      value={item.quantity}
                      onChange={(e) => {
                        const value = e.target.value;
                        
                        if (value === '') {
                          onQuantityChange(item.id, 0);
                          return;
                        }
                        
                        const cleanValue = value.replace(/\D/g, '');
                        const numValue = Math.min(parseInt(cleanValue) || 0, 999);
                        onQuantityChange(item.id, numValue);
                      }}
                      onFocus={(e) => e.target.select()}
                      onBlur={(e) => {
                        if (e.target.value === '') {
                          onQuantityChange(item.id, 0);
                        }
                      }}
                      className="w-10 md:w-12 text-center text-gray-700 border border-gray-300 rounded px-1 md:px-2 py-1 text-xs md:text-base focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                      maxLength={3}
                    />
                    
                    <CircleButton 
                      onClick={() => onQuantityChange(item.id, item.quantity - 1)}
                      ariaLabel="Decrease quantity"
                    >
                      <MinusIcon />
                    </CircleButton>
                  </div>
                </td>
                <td className="px-2 py-2 md:px-4 md:py-3 text-xs md:text-base text-gray-600">{item.unit}</td>
                <td className="px-2 py-2 md:px-4 md:py-3 text-center">
                  <div className="flex items-center justify-center gap-1 md:gap-2">
                    <button
                      onClick={() => onEdit(item.id)}
                      className="px-2 py-1 md:px-3 md:py-2 bg-blue-500 text-white text-xs md:text-sm rounded-md hover:bg-blue-600 transition-colors inline-flex items-center justify-center gap-1 md:gap-2"
                    >
                      <PencilIcon />
                      <span className="hidden sm:inline">Edit</span>
                    </button>
                    <button
                      onClick={() => onDelete(item.id)}
                      className="px-2 py-1 md:px-3 md:py-2 bg-red-500 text-white text-xs md:text-sm rounded-md hover:bg-red-600 transition-colors inline-flex items-center justify-center gap-1 md:gap-2"
                    >
                      <TrashIcon />
                      <span className="hidden sm:inline">Delete</span>
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ItemsTable;