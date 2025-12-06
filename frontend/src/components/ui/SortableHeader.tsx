import { cn } from '@/lib/utils';
import { ArrowDown, ArrowUp, Filter } from 'lucide-react';
import * as React from 'react';

export interface SortableHeaderProps {
  label: string;
  field: string;
  sortField: string | null;
  sortDirection: 'asc' | 'desc';
  onSort: (field: string) => void;
  filterable?: boolean;
  hasActiveFilter?: boolean;
  onFilterClick?: (e: React.MouseEvent) => void;
  className?: string;
  align?: 'left' | 'right';
}

export function SortableHeader({
  label,
  field,
  sortField,
  sortDirection,
  onSort,
  filterable = false,
  hasActiveFilter = false,
  onFilterClick,
  className,
  align = 'left',
}: SortableHeaderProps) {
  const [isHovered, setIsHovered] = React.useState(false);
  const isActive = sortField === field;

  const handleSortClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSort(field);
  };

  const handleFilterClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onFilterClick?.(e);
  };

  const SortIcon = isActive
    ? sortDirection === 'asc'
      ? ArrowUp
      : ArrowDown
    : ArrowUp;

  return (
    <div
      className={cn(
        'flex items-center gap-1.5 select-none min-w-0',
        align === 'right' ? 'justify-end' : 'justify-start',
        className
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <span
        className="cursor-pointer hover:text-foreground transition-colors truncate"
        onClick={handleSortClick}
      >
        {label}
      </span>

      <div className="flex items-center gap-0.5 shrink-0">
        {/* Sort indicator */}
        <button
          onClick={handleSortClick}
          className={cn(
            'p-0.5 rounded transition-all duration-150',
            isActive
              ? 'text-primary opacity-100'
              : isHovered
                ? 'text-muted-foreground opacity-70 hover:opacity-100'
                : 'opacity-0'
          )}
          aria-label={`Sort by ${label}`}
        >
          <SortIcon className="h-3.5 w-3.5" />
        </button>

        {/* Filter button */}
        {filterable && (
          <button
            onClick={handleFilterClick}
            className={cn(
              'p-0.5 rounded transition-all duration-150',
              hasActiveFilter
                ? 'text-primary opacity-100'
                : isHovered
                  ? 'text-muted-foreground opacity-70 hover:opacity-100'
                  : 'opacity-0'
            )}
            aria-label={`Filter by ${label}`}
          >
            <Filter className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}
