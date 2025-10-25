import React, { useState } from 'react';
import StatBoxes from './StatBoxes';
import ItemsTable from './ItemsTable.tsx';
import type { InventoryType } from '../../types/InventoryTypes.ts';

interface InventoryItem {
  id: string;
  name: string;
  category: string;
  quantity: number;
  unit: string;
}

interface InventoryScreenProps {
  screenType: InventoryType;
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
  { id: '9', name: 'Cheese', category: 'Dairy', quantity: 1, unit: 'Blocks' },
  { id: '10', name: 'Cheese', category: 'Dairy', quantity: 1, unit: 'Blocks' },
  { id: '11', name: 'Cheese', category: 'Dairy', quantity: 1, unit: 'Blocks' },
  { id: '12', name: 'Cheese', category: 'Dairy', quantity: 1, unit: 'Blocks' },
  { id: '13', name: 'Cheese', category: 'Dairy', quantity: 1, unit: 'Blocks' },
  { id: '14', name: 'Cheese', category: 'Dairy', quantity: 1, unit: 'Blocks' },
];

const InventoryScreen: React.FC<InventoryScreenProps> = ({ screenType }) => {
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
    
    setItems(prevItems => 
      prevItems.map(item => 
        item.id === id ? { ...item, quantity: newQuantity } : item
      )
    );
    
    // TODO: Add API call here when backend is ready
    // await fetch(`/api/inventory/${id}`, {
    //   method: 'PUT',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ quantity: newQuantity })
    // });
  };

  const handleDelete = (id: string) => {
    setItems(items.filter(item => item.id !== id));
  };

  return (
    <div className="flex-1 w-full min-w-0 p-3 md:p-8 bg-gray-50 overflow-auto">
      {/* Header */}
      <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4 md:mb-8 capitalize">
        {screenType} Inventory
      </h1>

      {/* Stats Cards */}
      <StatBoxes 
        totalItems={totalItems}
        expiringItems={expiringItems}
        expiredItems={expiredItems}
        screenType={screenType}
      />

      {/* Search Bar */}
      <div className="mb-4 md:mb-6">
        <input
          type="text"
          placeholder="Search items..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-3 md:px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm md:text-base"
        />
      </div>

      {/* Pagination Controls */}
      <div className="flex w-full items-center justify-between mb-3 md:mb-4">
        <button
          onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
          disabled={currentPage === 1}
          className="px-2 md:px-4 py-1.5 md:py-2 text-xs md:text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Prev
        </button>
        
        <div className="flex items-center gap-1 md:gap-2">
          {[...Array(Math.min(5, totalPages))].map((_, i) => {
            const pageNum = i + 1;
            return (
              <button
                key={pageNum}
                onClick={() => setCurrentPage(pageNum)}
                className={`px-2 md:px-4 py-1.5 md:py-2 text-xs md:text-sm rounded-lg ${
                  currentPage === pageNum
                    ? 'bg-gray-900 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                {pageNum}
              </button>
            );
          })}
          {totalPages > 5 && <span className="px-1 md:px-2 text-xs md:text-sm">...</span>}
          {totalPages > 5 && (
            <>
              <button className="px-2 md:px-4 py-1.5 md:py-2 text-xs md:text-sm bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
                {totalPages - 1}
              </button>
              <button className="px-2 md:px-4 py-1.5 md:py-2 text-xs md:text-sm bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">
                {totalPages}
              </button>
            </>
          )}
        </div>
        
        <button
          onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage === totalPages}
          className="px-2 md:px-4 py-1.5 md:py-2 text-xs md:text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>

      {/* Table */}
      <ItemsTable 
        items={paginatedItems}
        onQuantityChange={handleQuantityChange}
        onDelete={handleDelete}
      />
    </div>
  );
};

export default InventoryScreen;