import { useState, useEffect } from 'react';
import { createCategory, createUnit, DataError } from '../../../services/dataService';
import { AuthError } from '../../../services/AuthService';

interface AddDataOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  type: 'category' | 'unit' | null;
  onDataCreated?: () => void;
}

function AddDataOverlay({ isOpen, onClose, type, onDataCreated }: AddDataOverlayProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '', // For categories
    abbreviation: '', // For units
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset form when type changes or overlay opens
  useEffect(() => {
    if (isOpen) {
      setFormData({
        name: '',
        description: '',
        abbreviation: '',
      });
      setError(null);
    }
  }, [isOpen, type]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!type) {
      setError('Invalid data type');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      if (type === 'category') {
        await createCategory({
          name: formData.name,
          description: formData.description || null,
        });
      } else {
        await createUnit({
          name: formData.name,
          abbreviation: formData.abbreviation || null,
        });
      }

      // Reset form
      setFormData({
        name: '',
        description: '',
        abbreviation: '',
      });

      // Notify parent to refresh the list
      if (onDataCreated) {
        onDataCreated();
      }

      // Close overlay
      onClose();
    } catch (err) {
      if (err instanceof AuthError) {
        setError('Not authenticated. Please log in again.');
        setTimeout(() => window.location.reload(), 2000);
      } else if (err instanceof DataError) {
        setError(err.message);
      } else {
        setError(`Failed to create ${type}. Please try again.`);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen || !type) return null;

  const isCategory = type === 'category';
  const title = isCategory ? 'Add Category' : 'Add Unit';

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
          <h2 className="text-xl md:text-2xl font-bold text-gray-900">{title}</h2>
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
          {/* Name Field */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Name <span className="text-red-500">*</span>
            </label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-900"
              placeholder={isCategory ? 'e.g., Pantry' : 'e.g., Gallon'}
              required
            />
          </div>

          {/* Conditional Field - Description for Category or Abbreviation for Unit */}
          {isCategory ? (
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                Description <span className="text-gray-400">(optional)</span>
              </label>
              <textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none text-gray-900"
                placeholder="Brief description of this category..."
              />
            </div>
          ) : (
            <div>
              <label htmlFor="abbreviation" className="block text-sm font-medium text-gray-700 mb-1">
                Abbreviation <span className="text-gray-400">(optional)</span>
              </label>
              <input
                id="abbreviation"
                type="text"
                value={formData.abbreviation}
                onChange={(e) => setFormData({ ...formData, abbreviation: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-gray-900"
                placeholder="e.g., gal, lb, oz"
                maxLength={10}
              />
            </div>
          )}

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
              {isSubmitting ? 'Adding...' : `Add ${isCategory ? 'Category' : 'Unit'}`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default AddDataOverlay;
