import { useState, useEffect, useRef } from 'react';
import type { InventoryType } from '../../types/InventoryTypes.ts';
import { INVENTORY_ITEMS } from '../../types/InventoryTypes.ts';
import { createItem, updateItem, ItemsError } from '../../services/ItemsService.ts';
import { AuthError } from '../../services/AuthService.ts';
import { getCategories, getUnits, createCategory, createUnit, DataError } from '../../services/DataService.ts';
import type { Category, Unit } from '../../types/DataTypes.ts';
import type { Item, ItemPatch } from '../../types/ItemTypes.ts';

interface AddItemOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  onItemCreated?: () => void; // Callback to refresh the list
  editItem?: Item; // Item to edit (if provided, overlay is in edit mode)
}

function AddItemOverlay({ isOpen, onClose, onItemCreated, editItem }: AddItemOverlayProps) {
  const isEditMode = !!editItem;
  const [formData, setFormData] = useState({
    type: '' as InventoryType | '',
    name: '',
    category: '',
    quantity: 1,
    unit: '',
    notes: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Searchable dropdown state
  const [categories, setCategories] = useState<Category[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [showCategoryDropdown, setShowCategoryDropdown] = useState(false);
  const [showUnitDropdown, setShowUnitDropdown] = useState(false);
  const [categorySearch, setCategorySearch] = useState('');
  const [unitSearch, setUnitSearch] = useState('');

  // Refs for click outside detection
  const categoryRef = useRef<HTMLDivElement>(null);
  const unitRef = useRef<HTMLDivElement>(null);

  // Fetch categories and units when overlay opens
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [categoriesResponse, unitsResponse] = await Promise.all([
          getCategories(1, 1000),
          getUnits(1, 1000),
        ]);
        setCategories(categoriesResponse.items);
        setUnits(unitsResponse.items);
      } catch (err) {
        console.error('Failed to fetch categories/units:', err);
      }
    };

    if (isOpen) {
      fetchData();
    }
  }, [isOpen]);

  // Populate form when editing
  useEffect(() => {
    if (editItem && isOpen) {
      setFormData({
        type: editItem.item_type as InventoryType,
        name: editItem.item_name,
        category: editItem.category_name || '',
        quantity: editItem.quantity,
        unit: editItem.unit_name || '',
        notes: editItem.notes || ''
      });
      setCategorySearch(editItem.category_name || '');
      setUnitSearch(editItem.unit_name || '');
    } else if (!isOpen) {
      // Reset form when closing
      setFormData({
        type: '',
        name: '',
        category: '',
        quantity: 1,
        unit: '',
        notes: ''
      });
      setCategorySearch('');
      setUnitSearch('');
    }
  }, [editItem, isOpen]);

  // Click outside to close dropdowns
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (categoryRef.current && !categoryRef.current.contains(event.target as Node)) {
        setShowCategoryDropdown(false);
      }
      if (unitRef.current && !unitRef.current.contains(event.target as Node)) {
        setShowUnitDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filter categories based on search
  const filteredCategories = categories.filter(cat =>
    cat.name.toLowerCase().includes(categorySearch.toLowerCase())
  );

  // Filter units based on search
  const filteredUnits = units.filter(unit =>
    unit.name.toLowerCase().includes(unitSearch.toLowerCase())
  );

  // Handle category selection
  const handleCategorySelect = (categoryName: string) => {
    setFormData({ ...formData, category: categoryName });
    setCategorySearch(categoryName);
    setShowCategoryDropdown(false);
  };

  // Handle unit selection
  const handleUnitSelect = (unitName: string) => {
    setFormData({ ...formData, unit: unitName });
    setUnitSearch(unitName);
    setShowUnitDropdown(false);
  };

  // Create new category
  const handleCreateCategory = async () => {
    if (!categorySearch.trim()) return;

    try {
      const newCategory = await createCategory({
        name: categorySearch.trim(),
        description: null,
      });
      setCategories([...categories, newCategory]);
      handleCategorySelect(newCategory.name);
    } catch (err) {
      if (err instanceof AuthError) {
        setError('Not authenticated. Please log in again.');
        setTimeout(() => window.location.reload(), 2000);
      } else if (err instanceof DataError) {
        setError(err.message);
      } else {
        setError('Failed to create category.');
      }
    }
  };

  // Create new unit
  const handleCreateUnit = async () => {
    if (!unitSearch.trim()) return;

    try {
      const newUnit = await createUnit({
        name: unitSearch.trim(),
        abbreviation: null,
      });
      setUnits([...units, newUnit]);
      handleUnitSelect(newUnit.name);
    } catch (err) {
      if (err instanceof AuthError) {
        setError('Not authenticated. Please log in again.');
        setTimeout(() => window.location.reload(), 2000);
      } else if (err instanceof DataError) {
        setError(err.message);
      } else {
        setError('Failed to create unit.');
      }
    }
  };

  // Handle category input change
  const handleCategoryInputChange = (value: string) => {
    setCategorySearch(value);
    setFormData({ ...formData, category: value });
    setShowCategoryDropdown(true);
  };

  // Handle unit input change
  const handleUnitInputChange = (value: string) => {
    setUnitSearch(value);
    setFormData({ ...formData, unit: value });
    setShowUnitDropdown(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.type && !isEditMode) {
      setError('Please select an item type');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      if (isEditMode && editItem) {
        // Update existing item
        const patchData: ItemPatch = {
          name: formData.name !== editItem.item_name ? formData.name : undefined,
          category_name: formData.category !== (editItem.category_name || '') ? (formData.category || undefined) : undefined,
          unit_name: formData.unit !== (editItem.unit_name || '') ? (formData.unit || undefined) : undefined,
          quantity: formData.quantity !== editItem.quantity ? formData.quantity : undefined,
          notes: formData.notes !== (editItem.notes || '') ? (formData.notes || undefined) : undefined,
        };

        // Only send fields that changed
        const hasChanges = Object.values(patchData).some(v => v !== undefined);
        if (hasChanges) {
          await updateItem(editItem.item_id, patchData);
        }
      } else {
        // Create new item
        await createItem({
          item_name: formData.name,
          item_type: formData.type as InventoryType,
          category_name: formData.category || null,
          quantity: formData.quantity,
          unit_name: formData.unit || null,
          notes: formData.notes || null,
        });
      }

      // Reset form
      setFormData({
        type: '',
        name: '',
        category: '',
        quantity: 1,
        unit: '',
        notes: ''
      });
      setCategorySearch('');
      setUnitSearch('');

      // Notify parent to refresh the list
      if (onItemCreated) {
        onItemCreated();
      }

      // Close overlay
      onClose();
    } catch (err) {
      if (err instanceof AuthError) {
        setError('Not authenticated. Please log in again.');
        setTimeout(() => window.location.reload(), 2000);
      } else if (err instanceof ItemsError) {
        setError(err.message);
      } else {
        setError(isEditMode ? 'Failed to update item. Please try again.' : 'Failed to create item. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Format quantity to display (remove unnecessary decimals)
  const formatQuantity = (qty: number): string => {
    // If whole number, show without decimals
    if (qty % 1 === 0) {
      return qty.toString();
    }
    // Otherwise show with decimals
    return qty.toString();
  };

  const handleQuantityChange = (value: string) => {
    if (value === '') {
      setFormData({ ...formData, quantity: 0 });
      return;
    }

    // Allow digits and decimal point
    const cleanValue = value.replace(/[^\d.]/g, '');

    // Ensure only one decimal point
    const parts = cleanValue.split('.');
    if (parts.length > 2) {
      return; // Ignore if more than one decimal point
    }

    // Limit to 2 decimal places
    if (parts[1] && parts[1].length > 2) {
      return;
    }

    const numValue = parseFloat(cleanValue) || 0;
    if (numValue <= 999) {
      setFormData({ ...formData, quantity: numValue });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0"
        style={{ backgroundColor: 'rgba(0, 0, 0, 0.3)' }}
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 md:p-6 border-b border-gray-200">
          <h2 className="text-xl md:text-2xl font-bold text-gray-900">{isEditMode ? 'Edit Item' : 'Add Item'}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-4 md:p-6 space-y-4">
          {/* Item Type Dropdown */}
          <div>
            <label htmlFor="type" className="block text-sm font-medium text-gray-700 mb-1">
              Item Type <span className="text-red-500">*</span>
            </label>
            <select
              id="type"
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value as InventoryType })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-900"
              disabled={isEditMode}
              required
            >
              <option value="">Select a type...</option>
              {INVENTORY_ITEMS.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          {/* Item Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Item Name <span className="text-red-500">*</span>
            </label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-900"
              placeholder="e.g., Milk"
              required
            />
          </div>

          {/* Category with searchable dropdown */}
          <div ref={categoryRef} className="relative">
            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
              Category <span className="text-gray-400">(optional)</span>
            </label>
            <input
              id="category"
              type="text"
              value={categorySearch}
              onChange={(e) => handleCategoryInputChange(e.target.value)}
              onFocus={() => setShowCategoryDropdown(true)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-900"
              placeholder="Search or create category..."
            />

            {showCategoryDropdown && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                {filteredCategories.length > 0 ? (
                  <>
                    {filteredCategories.map((cat) => (
                      <div
                        key={cat.id}
                        onClick={() => handleCategorySelect(cat.name)}
                        className="px-3 py-2 hover:bg-gray-100 cursor-pointer text-gray-900"
                      >
                        {cat.name}
                      </div>
                    ))}
                  </>
                ) : categorySearch.trim() ? (
                  <div
                    onClick={handleCreateCategory}
                    className="px-3 py-2 hover:bg-blue-50 cursor-pointer text-blue-600 font-medium"
                  >
                    + Create "{categorySearch}"
                  </div>
                ) : (
                  <div className="px-3 py-2 text-gray-400 text-sm">
                    Type to search or create...
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Quantity */}
          <div>
            <label htmlFor="quantity" className="block text-sm font-medium text-gray-700 mb-1">
              Quantity <span className="text-red-500">*</span>
            </label>
            <input
              id="quantity"
              type="text"
              inputMode="decimal"
              value={formatQuantity(formData.quantity)}
              onChange={(e) => handleQuantityChange(e.target.value)}
              onFocus={(e) => e.target.select()}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-900"
              maxLength={6}
              required
            />
          </div>

          {/* Unit with searchable dropdown */}
          <div ref={unitRef} className="relative">
            <label htmlFor="unit" className="block text-sm font-medium text-gray-700 mb-1">
              Unit <span className="text-gray-400">(optional)</span>
            </label>
            <input
              id="unit"
              type="text"
              value={unitSearch}
              onChange={(e) => handleUnitInputChange(e.target.value)}
              onFocus={() => setShowUnitDropdown(true)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-900"
              placeholder="Search or create unit..."
            />

            {showUnitDropdown && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                {filteredUnits.length > 0 ? (
                  <>
                    {filteredUnits.map((unit) => (
                      <div
                        key={unit.id}
                        onClick={() => handleUnitSelect(unit.name)}
                        className="px-3 py-2 hover:bg-gray-100 cursor-pointer text-gray-900"
                      >
                        {unit.name}
                      </div>
                    ))}
                  </>
                ) : unitSearch.trim() ? (
                  <div
                    onClick={handleCreateUnit}
                    className="px-3 py-2 hover:bg-blue-50 cursor-pointer text-blue-600 font-medium"
                  >
                    + Create "{unitSearch}"
                  </div>
                ) : (
                  <div className="px-3 py-2 text-gray-400 text-sm">
                    Type to search or create...
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Notes */}
          <div>
            <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
              Notes <span className="text-gray-400">(optional)</span>
            </label>
            <textarea
              id="notes"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none text-gray-900"
              placeholder="Any additional information..."
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 bg-slate-950 text-white rounded-lg hover:bg-lime-400 hover:text-slate-950 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (isEditMode ? 'Saving...' : 'Adding...') : (isEditMode ? 'Save Changes' : 'Add Item')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default AddItemOverlay;
