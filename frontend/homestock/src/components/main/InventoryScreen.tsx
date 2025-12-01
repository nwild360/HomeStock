import React, { useState, useEffect } from 'react';
import StatBoxes from './StatBoxes';
import ItemsTable from './ItemsTable.tsx';
import AddItemOverlay from '../sidebar/AddItemOverlay.tsx';
import type { InventoryType } from '../../types/InventoryTypes.ts';
import { getItems, getItem, updateStock, deleteItem, ItemsError } from '../../services/ItemsService.ts';
import { AuthError } from '../../services/AuthService.ts';
import type { Item } from '../../types/ItemTypes.ts';

interface InventoryItem {
  id: string;
  name: string;
  category: string;
  quantity: number;
  unit: string;
}

interface InventoryScreenProps {
  screenType: InventoryType;
  refreshKey?: number;
  onRefresh?: () => void;
}

const InventoryScreen: React.FC<InventoryScreenProps> = ({ screenType, refreshKey, onRefresh }) => {
  const [backendItems, setBackendItems] = useState<Item[]>([]); // Store original backend items
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalItems, setTotalItems] = useState(0);
  const [editingItem, setEditingItem] = useState<Item | undefined>(undefined);
  const itemsPerPage = 10;

  // Fetch items from backend on mount and when screenType changes
  useEffect(() => {
    const fetchItems = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Fetch all items (we'll filter by type client-side for now)
        const response = await getItems(1, 1000); // Fetch up to 1000 items for client-side filtering

        // Filter items by screenType
        const filteredByType = response.items.filter(
          (item) => item.item_type === screenType
        );

        // Store original backend items
        setBackendItems(filteredByType);

        // Transform backend items to frontend format
        const transformedItems: InventoryItem[] = filteredByType.map((item) => ({
          id: item.item_id.toString(),
          name: item.item_name,
          category: item.category_name || 'Uncategorized',
          quantity: Number(item.quantity),
          unit: item.unit_name || '',
        }));

        setItems(transformedItems);
        setTotalItems(transformedItems.length);
      } catch (err) {
        if (err instanceof AuthError) {
          // User not authenticated - redirect to login
          console.error('Not authenticated, redirecting to login...');
          window.location.reload(); // This will show the login screen
        } else if (err instanceof ItemsError) {
          setError(err.message);
        } else {
          setError('An unexpected error occurred while loading items');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchItems();
  }, [screenType, refreshKey]);

  // Filter items based on search
  const filteredItems = items.filter((item) => {
    if (!searchTerm) return true;

    const searchLower = searchTerm.toLowerCase().trim();
    const nameMatch = item.name?.toLowerCase().trim().includes(searchLower) || false;
    const categoryMatch = item.category?.toLowerCase().trim().includes(searchLower) || false;

    return nameMatch || categoryMatch;
  });

  // Handle search change and reset to page 1
  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
    setCurrentPage(1);
  };

  // Pagination
  const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedItems = filteredItems.slice(startIndex, startIndex + itemsPerPage);

  // Calculate stats
  const expiringItems = 0; // TODO: Implement when expiration dates are added
  const expiredItems = 0; // TODO: Implement when expiration dates are added

  // Handlers
  const handleQuantityChange = async (id: string, newQuantity: number) => {
    if (newQuantity < 0) return;

    // Optimistic update - update UI immediately
    setItems(prevItems =>
      prevItems.map(item =>
        item.id === id ? { ...item, quantity: newQuantity } : item
      )
    );

    try {
      // Call API to update stock
      await updateStock(Number(id), { new_qty: newQuantity });
    } catch (err) {
      if (err instanceof AuthError) {
        console.error('Not authenticated, redirecting to login...');
        window.location.reload();
      } else {
        console.error('Failed to update quantity:', err);
        // Revert optimistic update on error
        if (onRefresh) {
          onRefresh();
        }
      }
    }
  };

  const handleEdit = async (id: string) => {
    try {
      // Fetch the latest item data from the server
      const item = await getItem(Number(id));
      setEditingItem(item);
    } catch (err) {
      if (err instanceof AuthError) {
        console.error('Not authenticated, redirecting to login...');
        window.location.reload();
      } else {
        console.error('Failed to fetch item for editing:', err);
        // Fallback to cached data if fetch fails
        const cachedItem = backendItems.find(item => item.item_id.toString() === id);
        if (cachedItem) {
          setEditingItem(cachedItem);
        }
      }
    }
  };

  const handleDelete = async (id: string) => {
    // Optimistic update - remove from UI immediately
    setItems(prevItems => prevItems.filter(item => item.id !== id));

    try {
      // Call API to delete item
      await deleteItem(Number(id));
    } catch (err) {
      if (err instanceof AuthError) {
        console.error('Not authenticated, redirecting to login...');
        window.location.reload();
      } else {
        console.error('Failed to delete item:', err);
        // Revert optimistic update on error
        if (onRefresh) {
          onRefresh();
        }
      }
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex-1 w-full min-w-0 p-3 md:p-8 bg-gray-50 overflow-auto flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading inventory...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex-1 w-full min-w-0 p-3 md:p-8 bg-gray-50 overflow-auto flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <p className="font-bold">Error</p>
            <p>{error}</p>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

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
          onChange={(e) => handleSearchChange(e.target.value)}
          className="w-full px-3 md:px-4 py-2 border border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm md:text-base"
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
        onEdit={handleEdit}
        onDelete={handleDelete}
      />

      {/* Edit Item Overlay */}
      <AddItemOverlay
        isOpen={!!editingItem}
        onClose={() => setEditingItem(undefined)}
        onItemCreated={onRefresh}
        editItem={editingItem}
      />
    </div>
  );
};

export default InventoryScreen;