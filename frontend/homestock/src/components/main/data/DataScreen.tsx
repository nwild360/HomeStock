import React, { useState, useEffect } from 'react';
import DataTables from './DataTables';
import AddDataButtons from './AddDataButtons';
import AddDataOverlay from './AddDataOverlay';
import type { Category, Unit } from '../../../types/DataTypes';
import {
  getCategories,
  getUnits,
  deleteCategory,
  deleteUnit,
  DataError,
} from '../../../services/DataService';
import { AuthError } from '../../../services/AuthService';

interface DataScreenProps {
  refreshKey?: number;
  onRefresh?: () => void;
}

const DataScreen: React.FC<DataScreenProps> = ({
  refreshKey,
  onRefresh,
}) => {
  // Categories state
  const [allCategories, setAllCategories] = useState<Category[]>([]);

  // Units state
  const [allUnits, setAllUnits] = useState<Unit[]>([]);

  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Overlay state
  const [isOverlayOpen, setIsOverlayOpen] = useState(false);
  const [overlayType, setOverlayType] = useState<'category' | 'unit' | null>(null);
  const [editingItem, setEditingItem] = useState<Category | Unit | undefined>(undefined);

  // Fetch all categories and units (no backend pagination)
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Fetch all items with a large page size
        const [categoriesResponse, unitsResponse] = await Promise.all([
          getCategories(1, 1000),
          getUnits(1, 1000),
        ]);

        setAllCategories(categoriesResponse.items);
        setAllUnits(unitsResponse.items);
      } catch (err) {
        if (err instanceof AuthError) {
          console.error('Not authenticated, redirecting to login...');
          window.location.reload();
        } else if (err instanceof DataError) {
          setError(err.message);
        } else {
          setError('Failed to load data');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [refreshKey]);

  // Handlers
  const handleEditCategory = (category: Category) => {
    setEditingItem(category);
    setOverlayType('category');
    setIsOverlayOpen(true);
  };

  const handleEditUnit = (unit: Unit) => {
    setEditingItem(unit);
    setOverlayType('unit');
    setIsOverlayOpen(true);
  };

  const handleDeleteCategory = async (id: number) => {
    // Optimistic update
    setAllCategories((prev) => prev.filter((cat) => cat.id !== id));

    try {
      await deleteCategory(id);
      if (onRefresh) {
        onRefresh();
      }
    } catch (err) {
      if (err instanceof AuthError) {
        console.error('Not authenticated, redirecting to login...');
        window.location.reload();
      } else {
        console.error('Failed to delete category:', err);
        // Revert optimistic update
        if (onRefresh) {
          onRefresh();
        }
      }
    }
  };

  const handleDeleteUnit = async (id: number) => {
    // Optimistic update
    setAllUnits((prev) => prev.filter((unit) => unit.id !== id));

    try {
      await deleteUnit(id);
      if (onRefresh) {
        onRefresh();
      }
    } catch (err) {
      if (err instanceof AuthError) {
        console.error('Not authenticated, redirecting to login...');
        window.location.reload();
      } else {
        console.error('Failed to delete unit:', err);
        // Revert optimistic update
        if (onRefresh) {
          onRefresh();
        }
      }
    }
  };

  // Overlay handlers
  const handleAddCategory = () => {
    setEditingItem(undefined); // Clear edit item for create mode
    setOverlayType('category');
    setIsOverlayOpen(true);
  };

  const handleAddUnit = () => {
    setEditingItem(undefined); // Clear edit item for create mode
    setOverlayType('unit');
    setIsOverlayOpen(true);
  };

  const handleCloseOverlay = () => {
    setIsOverlayOpen(false);
    setOverlayType(null);
    setEditingItem(undefined);
  };

  const handleDataCreated = () => {
    // Trigger refresh
    if (onRefresh) {
      onRefresh();
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex-1 w-full min-w-0 p-3 md:p-8 bg-gray-50 overflow-auto flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading data...</p>
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
      <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4 md:mb-8">
        Data Management
      </h1>

      {/* Add Buttons */}
      <AddDataButtons onAddCategory={handleAddCategory} onAddUnit={handleAddUnit} />

      {/* Two Tables Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6 h-[calc(100vh-16rem)]">
        {/* Categories Table */}
        <DataTables
          title="Categories"
          items={allCategories}
          onEdit={handleEditCategory}
          onDelete={handleDeleteCategory}
          itemsPerPage={8}
        />

        {/* Units Table */}
        <DataTables
          title="Units"
          items={allUnits}
          onEdit={handleEditUnit}
          onDelete={handleDeleteUnit}
          itemsPerPage={8}
        />
      </div>

      {/* Add/Edit Data Overlay */}
      <AddDataOverlay
        isOpen={isOverlayOpen}
        onClose={handleCloseOverlay}
        type={overlayType}
        onDataCreated={handleDataCreated}
        editItem={editingItem}
      />
    </div>
  );
};

export default DataScreen;
