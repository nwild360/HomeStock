import { useState, useEffect } from 'react';
import { getCategories, getUnits } from '../../services/DataService.ts';
import { bulkCreateItems } from '../../services/ItemsService.ts';
import type { ItemCreate } from '../../types/ItemTypes.ts';
import type { Category, Unit } from '../../types/DataTypes.ts';
import type { CandidateItem } from '../../services/ReceiptService.ts';

interface ReceiptReviewOverlayProps {
  isOpen: boolean;
  candidates: CandidateItem[];
  onClose: () => void;
  onItemsAdded: () => void;
}

interface ReviewRow {
  id: string;
  included: boolean;
  item_name: string;
  item_type: 'food' | 'household';
  category_name: string;
  quantity: string;
  unit_name: string;
  expiration_date: string;
  notes: string;
  submitError?: string;
  submitted?: boolean;
}

// Shared input className to keep things consistent
const inputCls = 'w-full px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm focus:ring-1 focus:ring-blue-500 outline-none disabled:opacity-60';
const selectCls = inputCls;
const labelCls = 'block text-xs font-medium text-gray-500 dark:text-gray-400 mb-0.5';

function ReceiptReviewOverlay({ isOpen, candidates, onClose, onItemsAdded }: ReceiptReviewOverlayProps) {
  const [rows, setRows] = useState<ReviewRow[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  useEffect(() => {
    if (!isOpen) return;
    setSubmitError('');
    setRows(
      candidates.map((c, i) => ({
        id: String(i),
        included: true,
        item_name: c.item_name,
        item_type: c.item_type,
        category_name: c.category_name ?? '',
        quantity: String(c.quantity ?? 1),
        unit_name: c.unit_name ?? '',
        expiration_date: '',
        notes: c.notes ?? '',
      }))
    );
    Promise.all([getCategories(1, 1000), getUnits(1, 1000)])
      .then(([catPage, unitPage]) => {
        setCategories(catPage.items);
        setUnits(unitPage.items);
        // Clear AI-suggested values that don't exist in the DB — avoids silent 400s on submit
        const categoryNames = new Set(catPage.items.map(c => c.name));
        const unitNames = new Set(unitPage.items.map(u => u.name));
        setRows(prev => prev.map(r => ({
          ...r,
          category_name: categoryNames.has(r.category_name) ? r.category_name : '',
          unit_name: unitNames.has(r.unit_name) ? r.unit_name : '',
        })));
      })
      .catch(() => {});
  }, [isOpen, candidates]);

  const updateRow = (id: string, field: keyof ReviewRow, value: string | boolean) => {
    setRows(prev => prev.map(r => r.id === id ? { ...r, [field]: value, submitError: undefined } : r));
  };

  const removeRow = (id: string) => {
    setRows(prev => prev.filter(r => r.id !== id));
  };

  const includedCount = rows.filter(r => r.included && !r.submitted).length;
  const allIncluded = rows.filter(r => !r.submitted).every(r => r.included);

  const toggleAll = () => {
    const next = !allIncluded;
    setRows(prev => prev.map(r => r.submitted ? r : { ...r, included: next }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setSubmitError('');

    const selectedIndices: number[] = [];
    const selectedItems: ItemCreate[] = [];
    rows.forEach((row, i) => {
      if (!row.included || row.submitted) return;
      selectedIndices.push(i);
      selectedItems.push({
        item_name: row.item_name.trim() || 'Unknown Item',
        item_type: row.item_type,
        category_name: row.category_name || null,
        quantity: parseFloat(row.quantity) || 1,
        unit_name: row.unit_name || null,
        expiration_date: row.expiration_date || null,
        notes: row.notes || null,
      });
    });

    if (selectedItems.length === 0) return;

    try {
      const results = await bulkCreateItems(selectedItems);
      const updatedRows = [...rows];
      results.forEach((result, i) => {
        const rowIndex = selectedIndices[i];
        if (result.status === 201) {
          updatedRows[rowIndex] = { ...updatedRows[rowIndex], submitted: true, submitError: undefined };
        } else {
          updatedRows[rowIndex] = { ...updatedRows[rowIndex], submitError: result.error ?? 'Failed to add' };
        }
      });
      setRows(updatedRows);
      if (results.every(r => r.status === 201)) {
        onItemsAdded();
        onClose();
      }
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to add items');
    } finally {
      setIsSubmitting(false);
    }
  };

  const hasFailures = rows.some(r => r.submitError);

  if (!isOpen) return null;

  const rowStateClass = (row: ReviewRow) =>
    [
      row.submitted ? 'opacity-40' : '',
      !row.included && !row.submitted ? 'opacity-50' : '',
    ].join(' ');

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 md:p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-3xl max-h-[95vh] md:max-h-[90vh] flex flex-col">

        {/* Header */}
        <div className="flex items-center justify-between px-4 py-4 md:px-6 border-b border-gray-200 dark:border-gray-700 shrink-0">
          <h2 className="text-lg md:text-xl font-semibold text-gray-900 dark:text-gray-100">
            Review Scanned Items
            <span className="ml-2 text-base font-normal text-gray-500">({rows.length})</span>
          </h2>
          <button
            onClick={onClose}
            className="appearance-none text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            aria-label="Close"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Empty state */}
        {rows.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center p-10 gap-3 text-gray-500 dark:text-gray-400">
            <svg className="w-12 h-12 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-lg font-medium">No items detected</p>
            <p className="text-sm">Try a clearer photo of the receipt</p>
            <button
              onClick={onClose}
              className="mt-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm font-medium transition-colors"
            >
              Close
            </button>
          </div>
        ) : (
          <>
            {/* Select all */}
            <div className="px-4 md:px-6 py-2.5 border-b border-gray-200 dark:border-gray-700 shrink-0">
              <button
                onClick={toggleAll}
                className="appearance-none text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                {allIncluded ? 'Deselect All' : 'Select All'}
              </button>
            </div>

            {/* Scrollable body */}
            <div className="overflow-y-auto flex-1">

              {/* ── MOBILE: card list ── */}
              <div className="md:hidden divide-y divide-gray-100 dark:divide-gray-700">
                {rows.map(row => (
                  <div
                    key={row.id}
                    className={`p-4 ${rowStateClass(row)} ${row.submitError ? 'bg-red-50 dark:bg-red-900/20' : ''}`}
                  >
                    {/* Card header: checkbox + name + trash/check */}
                    <div className="flex items-center gap-2 mb-3">
                      <input
                        type="checkbox"
                        checked={row.included}
                        disabled={row.submitted}
                        onChange={e => updateRow(row.id, 'included', e.target.checked)}
                        className="w-4 h-4 shrink-0 rounded border-gray-300 text-lime-500 focus:ring-lime-500"
                      />
                      <input
                        type="text"
                        value={row.item_name}
                        disabled={row.submitted}
                        onChange={e => updateRow(row.id, 'item_name', e.target.value)}
                        className={`flex-1 px-2 py-1.5 border rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm font-medium focus:ring-1 focus:ring-blue-500 outline-none disabled:opacity-60 ${
                          row.submitError ? 'border-red-400' : 'border-gray-300 dark:border-gray-600'
                        }`}
                      />
                      {row.submitted ? (
                        <svg className="w-5 h-5 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <button
                          onClick={() => removeRow(row.id)}
                          className="appearance-none text-gray-300 hover:text-red-500 dark:text-gray-600 dark:hover:text-red-400 shrink-0"
                          aria-label="Remove"
                        >
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      )}
                    </div>

                    {/* Error message */}
                    {row.submitError && (
                      <p className="text-xs text-red-600 dark:text-red-400 mb-2">{row.submitError}</p>
                    )}

                    {/* 2-col grid of fields */}
                    <div className="grid grid-cols-2 gap-x-3 gap-y-2">
                      <div>
                        <label className={labelCls}>Type</label>
                        <select value={row.item_type} disabled={row.submitted} onChange={e => updateRow(row.id, 'item_type', e.target.value)} className={selectCls}>
                          <option value="food">Food</option>
                          <option value="household">Household</option>
                        </select>
                      </div>
                      <div>
                        <label className={labelCls}>Quantity</label>
                        <input type="number" min="0" step="0.01" value={row.quantity} disabled={row.submitted} onChange={e => updateRow(row.id, 'quantity', e.target.value)} className={inputCls} />
                      </div>
                      <div>
                        <label className={labelCls}>Category</label>
                        <select value={row.category_name} disabled={row.submitted} onChange={e => updateRow(row.id, 'category_name', e.target.value)} className={selectCls}>
                          <option value=""></option>
                          {categories.map(c => <option key={c.id} value={c.name}>{c.name}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className={labelCls}>Unit</label>
                        <select value={row.unit_name} disabled={row.submitted} onChange={e => updateRow(row.id, 'unit_name', e.target.value)} className={selectCls}>
                          <option value=""></option>
                          {units.map(u => <option key={u.id} value={u.name}>{u.name}</option>)}
                        </select>
                      </div>
                      <div className="col-span-2">
                        <label className={labelCls}>Expiration Date</label>
                        <input type="date" value={row.expiration_date} disabled={row.submitted} onChange={e => updateRow(row.id, 'expiration_date', e.target.value)} className={inputCls} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* ── DESKTOP: table ── */}
              <table className="hidden md:table w-full text-sm">
                <thead className="sticky top-0 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                  <tr>
                    <th className="w-8 px-3 py-2"></th>
                    <th className="px-2 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Item Name</th>
                    <th className="px-2 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-24">Type</th>
                    <th className="px-2 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-16">Qty</th>
                    <th className="px-2 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-28">Category</th>
                    <th className="px-2 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-24">Unit</th>
                    <th className="px-2 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-32">Exp Date</th>
                    <th className="w-8 px-2 py-2"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {rows.map(row => (
                    <tr
                      key={row.id}
                      className={`${rowStateClass(row)} ${row.submitError ? 'bg-red-50 dark:bg-red-900/20' : ''}`}
                    >
                      <td className="px-3 py-2">
                        <input
                          type="checkbox"
                          checked={row.included}
                          disabled={row.submitted}
                          onChange={e => updateRow(row.id, 'included', e.target.checked)}
                          className="w-4 h-4 rounded border-gray-300 text-lime-500 focus:ring-lime-500"
                        />
                      </td>
                      <td className="px-2 py-1.5">
                        <div className="flex flex-col gap-0.5">
                          <input
                            type="text"
                            value={row.item_name}
                            disabled={row.submitted}
                            onChange={e => updateRow(row.id, 'item_name', e.target.value)}
                            className={`w-full px-2 py-1 border rounded text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-700 text-sm focus:ring-1 focus:ring-blue-500 outline-none disabled:opacity-60 ${
                              row.submitError ? 'border-red-400' : 'border-gray-300 dark:border-gray-600'
                            }`}
                          />
                          {row.submitError && (
                            <span className="text-xs text-red-600 dark:text-red-400">{row.submitError}</span>
                          )}
                        </div>
                      </td>
                      <td className="px-2 py-1.5">
                        <select value={row.item_type} disabled={row.submitted} onChange={e => updateRow(row.id, 'item_type', e.target.value)} className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm focus:ring-1 focus:ring-blue-500 outline-none disabled:opacity-60">
                          <option value="food">Food</option>
                          <option value="household">Household</option>
                        </select>
                      </td>
                      <td className="px-2 py-1.5">
                        <input type="number" min="0" step="0.01" value={row.quantity} disabled={row.submitted} onChange={e => updateRow(row.id, 'quantity', e.target.value)} className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm focus:ring-1 focus:ring-blue-500 outline-none disabled:opacity-60" />
                      </td>
                      <td className="px-2 py-1.5">
                        <select value={row.category_name} disabled={row.submitted} onChange={e => updateRow(row.id, 'category_name', e.target.value)} className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm focus:ring-1 focus:ring-blue-500 outline-none disabled:opacity-60">
                          <option value=""></option>
                          {categories.map(c => <option key={c.id} value={c.name}>{c.name}</option>)}
                        </select>
                      </td>
                      <td className="px-2 py-1.5">
                        <select value={row.unit_name} disabled={row.submitted} onChange={e => updateRow(row.id, 'unit_name', e.target.value)} className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm focus:ring-1 focus:ring-blue-500 outline-none disabled:opacity-60">
                          <option value=""></option>
                          {units.map(u => <option key={u.id} value={u.name}>{u.name}</option>)}
                        </select>
                      </td>
                      <td className="px-2 py-1.5">
                        <input type="date" value={row.expiration_date} disabled={row.submitted} onChange={e => updateRow(row.id, 'expiration_date', e.target.value)} className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm focus:ring-1 focus:ring-blue-500 outline-none disabled:opacity-60" />
                      </td>
                      <td className="px-2 py-1.5">
                        {row.submitted ? (
                          <svg className="w-4 h-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        ) : (
                          <button onClick={() => removeRow(row.id)} className="appearance-none text-gray-300 hover:text-red-500 dark:text-gray-600 dark:hover:text-red-400 transition-colors" aria-label="Remove row">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

            </div>

            {/* Footer */}
            <div className="shrink-0 border-t border-gray-200 dark:border-gray-700 px-4 py-3 md:px-4 md:py-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {includedCount} of {rows.filter(r => !r.submitted).length} selected
              </span>
              {submitError && (
                <p className="text-sm text-red-600 dark:text-red-400">{submitError}</p>
              )}
              <div className="flex gap-3 md:ml-auto">
                <button
                  onClick={onClose}
                  className="appearance-none flex-1 md:flex-none px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={isSubmitting || includedCount === 0}
                  className="flex-1 md:flex-none px-4 py-2 rounded-lg bg-[#A3E635] hover:bg-[#8BC82E] text-gray-900 text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Adding…' : hasFailures ? 'Retry Failed' : `Add ${includedCount} Item${includedCount !== 1 ? 's' : ''} →`}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default ReceiptReviewOverlay;
