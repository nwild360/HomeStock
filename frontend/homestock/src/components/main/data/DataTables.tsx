import { useState } from 'react';
import type { Category, Unit } from '../../../types/DataTypes';

interface DataTablesProps<T extends Category | Unit> {
  title: string;
  items: T[];
  onEdit: (item: T) => void;
  onDelete: (id: number) => void;
  itemsPerPage?: number;
}

function DataTables<T extends Category | Unit>({
  title,
  items,
  onEdit,
  onDelete,
  itemsPerPage = 8,
}: DataTablesProps<T>) {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  // Helper to check if item is a Category
  const isCategory = (item: T): item is T & Category => {
    return 'description' in item;
  };

  // Filter items based on search
  const filteredItems = items.filter((item) => {
    const searchLower = searchTerm.toLowerCase();
    const nameMatch = item.name.toLowerCase().includes(searchLower);

    if (isCategory(item)) {
      const descMatch = item.description?.toLowerCase().includes(searchLower);
      return nameMatch || descMatch;
    } else {
      const abbrevMatch = (item as Unit).abbreviation?.toLowerCase().includes(searchLower);
      return nameMatch || abbrevMatch;
    }
  });

  // Calculate pagination
  const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedItems = filteredItems.slice(startIndex, startIndex + itemsPerPage);

  // Reset to page 1 when search changes
  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
    setCurrentPage(1);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Table Header */}
      <h2 className="text-lg md:text-xl font-semibold text-gray-900 mb-3 md:mb-4">
        {title}
      </h2>

      {/* Search Bar */}
      <div className="mb-3 md:mb-4">
        <input
          type="text"
          placeholder={`Search ${title.toLowerCase()}...`}
          value={searchTerm}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
        />
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 flex-1 flex flex-col overflow-hidden">
        <div className="overflow-auto flex-1">
          <table className="w-full">
            <thead className="bg-gray-50 sticky top-0">
              <tr className="border-b border-gray-200">
                <th className="px-3 md:px-6 py-2 md:py-3 text-left text-xs md:text-sm font-medium text-gray-700">
                  Name
                </th>
                <th className="px-3 md:px-6 py-2 md:py-3 text-left text-xs md:text-sm font-medium text-gray-700">
                  {items.length > 0 && isCategory(items[0]) ? 'Description' : 'Abbreviation'}
                </th>
                <th className="px-3 md:px-6 py-2 md:py-3 text-center text-xs md:text-sm font-medium text-gray-700">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-3 md:px-6 py-6 md:py-8 text-center text-gray-500 text-sm">
                    {searchTerm ? `No ${title.toLowerCase()} match your search` : `No ${title.toLowerCase()} found`}
                  </td>
                </tr>
              ) : (
                paginatedItems.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-3 md:px-6 py-2 md:py-4 text-xs md:text-sm text-gray-900">
                      {item.name}
                    </td>
                    <td className="px-3 md:px-6 py-2 md:py-4 text-xs md:text-sm text-gray-600">
                      {isCategory(item)
                        ? item.description || '-'
                        : (item as Unit).abbreviation || '-'}
                    </td>
                    <td className="px-3 md:px-6 py-2 md:py-4 text-center">
                      <div className="flex items-center justify-center gap-1 md:gap-2">
                        <button
                          onClick={() => onEdit(item)}
                          className="px-2 md:px-3 py-1 md:py-1.5 text-xs md:text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => onDelete(item.id)}
                          className="px-2 md:px-3 py-1 md:py-1.5 text-xs md:text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        {filteredItems.length > 0 && (
          <div className="border-t border-gray-200 px-3 md:px-6 py-3 md:py-4 bg-gray-50">
            <div className="flex items-center justify-between">
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
                      className={`px-2 md:px-3 py-1 md:py-1.5 text-xs md:text-sm rounded-lg ${
                        currentPage === pageNum
                          ? 'bg-gray-900 text-white'
                          : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
                {totalPages > 5 && <span className="px-1 text-xs md:text-sm">...</span>}
                {totalPages > 5 && (
                  <button
                    onClick={() => setCurrentPage(totalPages)}
                    className={`px-2 md:px-3 py-1 md:py-1.5 text-xs md:text-sm rounded-lg ${
                      currentPage === totalPages
                        ? 'bg-gray-900 text-white'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {totalPages}
                  </button>
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
          </div>
        )}
      </div>
    </div>
  );
}

export default DataTables;
