import React, { useState } from 'react';

interface InventoryItem {
  id: string;
  name: string;
  category: string;
  quantity: number;
  unit: string;
}

// Mock data - replace with API call later
const mockItems: InventoryItem[] = [
  { id: '1', name: 'Milk', category: 'Dairy', quantity: 2, unit: 'Gallons' },
  { id: '2', name: 'Bread', category: 'Bakery', quantity: 1, unit: 'Loaves' },
  { id: '3', name: 'Eggs', category: 'Dairy', quantity: 12, unit: 'Count' },
  { id: '4', name: 'Chicken Breast', category: 'Meat', quantity: 3, unit: 'Pounds' },
  { id: '5', name: 'Rice', category: 'Grains', quantity: 5, unit: 'Pounds' },
  { id: '6', name: 'Tomatoes', category: 'Produce', quantity: 6, unit: 'Count' },
  { id: '7', name: 'Pasta', category: 'Grains', quantity: 2, unit: 'Boxes' },
  { id: '8', name: 'Cheese', category: 'Dairy', quantity: 1, unit: 'Blocks' },
];

const InventoryScreen: React.FC = () => {
  const [items, setItems] = useState<InventoryItem[]>(mockItems);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // Filter items based on search
  const filteredItems = items.filter(item =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Pagination
  const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedItems = filteredItems.slice(startIndex, startIndex + itemsPerPage);

  // Calculate stats
  const totalItems = items.length;
  const expiringItems = 100;
  const expiredItems = 100;

  // Handlers
  const handleQuantityChange = (id: string, newQuantity: number) => {
    if (newQuantity < 0) return;
    setItems(items.map(item => 
      item.id === id ? { ...item, quantity: newQuantity } : item
    ));
  };

  const handleDelete = (id: string) => {
    setItems(items.filter(item => item.id !== id));
  };

  return (
    <div className="flex-1 w-full min-w-0 p-8 bg-gray-50 overflow-auto">
      {/* Header */}
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Food Inventory</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-center mb-3">
            {/* Card Icon */}
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-gray-900">{totalItems}</div>
            <div className="text-sm text-gray-600 mt-1">Total Items</div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-center mb-3">
            {/* Card Icon */}
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-gray-900">{expiringItems}</div>
            <div className="text-sm text-gray-600 mt-1">Expiring Soon</div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-center mb-3">
            {/* Card Icon */}
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-gray-900">{expiredItems}</div>
            <div className="text-sm text-gray-600 mt-1">Expired</div>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search items..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
        />
      </div>

      {/* Pagination Controls */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
          disabled={currentPage === 1}
          className="px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        
        <div className="flex items-center gap-2">
          {[...Array(Math.min(5, totalPages))].map((_, i) => {
            const pageNum = i + 1;
            return (
              <button
                key={pageNum}
                onClick={() => setCurrentPage(pageNum)}
                className={`px-4 py-2 text-sm rounded-lg ${
                  currentPage === pageNum
                    ? 'bg-gray-900 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                {pageNum}
              </button>
            );
          })}
          {totalPages > 5 && <span className="px-2">...</span>}
          {totalPages > 5 && (
            <>
              <button className="px-4 py-2 text-sm bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
                {totalPages - 1}
              </button>
              <button className="px-4 py-2 text-sm bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
                {totalPages}
              </button>
            </>
          )}
        </div>
        
        <button
          onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage === totalPages}
          className="px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Item Name</th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Category</th>
              <th className="px-6 py-4 text-center text-sm font-semibold text-gray-900">Quantity</th>
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Unit(s)</th>
              <th className="px-6 py-4 text-center text-sm font-semibold text-gray-900">Delete Item</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {paginatedItems.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 text-sm text-gray-900">{item.name}</td>
                <td className="px-6 py-4 text-sm text-gray-600">{item.category}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center justify-center gap-2">
                    <button
                      onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                      className="w-8 h-8 flex items-center justify-center rounded-full border-2 border-gray-900 hover:bg-gray-900 hover:text-white transition-colors"
                    >
                      {/* Plus Icon */}
                    </button>
                    <input
                      type="number"
                      value={item.quantity}
                      onChange={(e) => handleQuantityChange(item.id, parseInt(e.target.value) || 0)}
                      className="w-16 text-center border border-gray-300 rounded px-2 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                    />
                    <button
                      onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                      className="w-8 h-8 flex items-center justify-center rounded-full border-2 border-gray-900 hover:bg-gray-900 hover:text-white transition-colors"
                    >
                      {/* Minus Icon */}
                    </button>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">{item.unit}</td>
                <td className="px-6 py-4 text-center">
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="px-4 py-1.5 bg-red-500 text-white text-sm rounded-md hover:bg-red-600 transition-colors inline-flex items-center gap-1"
                  >
                    {/* Trashcan Icon */}
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default InventoryScreen;