import { useState } from 'react';
import type { Category, Unit } from '../../../types/DataTypes';

interface DataTablesProps<T extends Category | Unit> {
  title: string;
  items: T[];
  onEdit: (item: T) => void;
  onDelete: (id: number) => void;
  itemsPerPage?: number;
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
