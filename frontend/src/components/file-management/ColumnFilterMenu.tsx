import React, { useEffect, useRef, useState } from 'react';
import { FileItem } from './types';

interface ColumnFilterMenuProps {
  isOpen: boolean;
  position: { x: number; y: number };
  columnId: string;
  columnLabel: string;
  data: FileItem[];
  onClose: () => void;
  onFilter: (columnId: string, filterValue: string) => void;
}

export const ColumnFilterMenu: React.FC<ColumnFilterMenuProps> = ({
  isOpen,
  position,
  columnId,
  columnLabel,
  data,
  onClose,
  onFilter,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const menuRef = useRef<HTMLDivElement>(null);

  // Get unique values for the column
  const getUniqueValues = () => {
    const values = data.map(item => {
      switch (columnId) {
        case 'name':
          return item.name;
        case 'type':
          return item.type;
        case 'status':
          return item.status;
        case 'uploader':
          return item.uploader;
        case 'accessGroup':
          return item.accessGroup;
        case 'equipment':
          return item.equipment;
        case 'tags':
          return item.tags.join(', ');
        default:
          return '';
      }
    });

    return Array.from(new Set(values)).filter(
      value => value && value.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const uniqueValues = getUniqueValues();

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () =>
        document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      ref={menuRef}
      className="fixed z-50 bg-white border border-gray-200 rounded-lg shadow-lg p-4 min-w-48 max-w-64"
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      <div className="mb-3">
        <h3 className="font-medium text-gray-900 mb-2">
          Filter by {columnLabel}
        </h3>
        <input
          type="text"
          placeholder="Search values..."
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          autoFocus
        />
      </div>

      <div className="max-h-48 overflow-y-auto">
        <button
          onClick={() => {
            onFilter(columnId, '');
            onClose();
          }}
          className="w-full text-left px-2 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded"
        >
          Clear filter
        </button>

        {uniqueValues.map((value, index) => (
          <button
            key={index}
            onClick={() => {
              onFilter(columnId, value);
              onClose();
            }}
            className="w-full text-left px-2 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded truncate"
            title={value}
          >
            {value}
          </button>
        ))}

        {uniqueValues.length === 0 && searchTerm && (
          <div className="px-2 py-1 text-sm text-gray-500">
            No matching values found
          </div>
        )}
      </div>
    </div>
  );
};
