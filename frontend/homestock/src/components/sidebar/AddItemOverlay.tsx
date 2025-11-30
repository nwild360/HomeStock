import { useState } from 'react';
import type { InventoryType } from '../../types/InventoryTypes.ts';
import { MENU_ITEMS } from '../../types/InventoryTypes.ts';
import { createItem, ItemsError } from '../../services/ItemsService.ts';
import { AuthError } from '../../services/AuthService.ts';

interface AddItemOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  onItemCreated?: () => void; // Callback to refresh the list
}

function AddItemOverlay({ isOpen, onClose, onItemCreated }: AddItemOverlayProps) {
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.type) {
      setError('Please select an item type');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // Call the API to create the item
      await createItem({
        item_name: formData.name,
        item_type: formData.type,
        category_name: formData.category || null,
        quantity: formData.quantity,
        unit_name: formData.unit || null,
        notes: formData.notes || null,
      });

      // Reset form
      setFormData({
        type: '',
        name: '',
        category: '',
        quantity: 1,
        unit: '',
        notes: ''
      });

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
        setError('Failed to create item. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuantityChange = (value: string) => {
    if (value === '') {
      setFormData({ ...formData, quantity: 0 });
      return;
    }
    const cleanValue = value.replace(/\D/g, '');
    const numValue = Math.min(parseInt(cleanValue) || 0, 999);
    setFormData({ ...formData, quantity: numValue });
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
          <h2 className="text-xl md:text-2xl font-bold text-gray-900">Add Item</h2>
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
              required
            >
              <option value="">Select a type...</option>
              {MENU_ITEMS.map((item) => (
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

          {/* Category */}
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
              Category <span className="text-gray-400">(optional)</span>
            </label>
            <input
              id="category"
              type="text"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-900"
              placeholder="e.g., Dairy"
            />
          </div>

          {/* Quantity */}
          <div>
            <label htmlFor="quantity" className="block text-sm font-medium text-gray-700 mb-1">
              Quantity <span className="text-red-500">*</span>
            </label>
            <input
              id="quantity"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              value={formData.quantity}
              onChange={(e) => handleQuantityChange(e.target.value)}
              onFocus={(e) => e.target.select()}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-900"
              maxLength={3}
              required
            />
          </div>

          {/* Unit */}
          <div>
            <label htmlFor="unit" className="block text-sm font-medium text-gray-700 mb-1">
              Unit <span className="text-gray-400">(optional)</span>
            </label>
            <input
              id="unit"
              type="text"
              value={formData.unit}
              onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-900"
              placeholder="e.g., Gallons, Count, Pounds"
            />
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
              {isSubmitting ? 'Adding...' : 'Add Item'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default AddItemOverlay;