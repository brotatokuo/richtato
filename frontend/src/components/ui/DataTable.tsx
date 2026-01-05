import { Card, CardContent } from '@/components/ui/card';
import {
  ColumnFilterPopover,
  FilterOption,
} from '@/components/ui/ColumnFilterPopover';
import { Input } from '@/components/ui/input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Pagination } from '@/components/ui/Pagination';
import { SortableHeader } from '@/components/ui/SortableHeader';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Search, X } from 'lucide-react';
import { ReactNode, useEffect, useMemo, useState } from 'react';
import { Button } from './button';

/**
 * Column definition for the DataTable
 */
export interface ColumnDef<T> {
  /** Field key in the data object */
  field: keyof T;
  /** Display label for the column header */
  label: string;
  /** Custom render function for cell content */
  render?: (value: T[keyof T], row: T) => ReactNode;
  /** Enable sorting for this column (default: true) */
  sortable?: boolean;
  /** Enable filtering for this column */
  filterable?: boolean;
  /** Text alignment */
  align?: 'left' | 'right';
  /** Additional CSS class for the column */
  className?: string;
  /** Width class (e.g., 'w-28') */
  width?: string;
}

/**
 * Props for the mobile card view renderer
 */
export interface MobileCardProps<T> {
  row: T;
  onClick?: () => void;
}

/**
 * DataTable component props
 */
export interface DataTableProps<T extends { id: string | number }> {
  /** Data array to display */
  data: T[];
  /** Column definitions */
  columns: ColumnDef<T>[];
  /** Enable global search bar */
  searchable?: boolean;
  /** Fields to search across (defaults to all string fields) */
  searchFields?: (keyof T)[];
  /** Placeholder text for search input */
  searchPlaceholder?: string;
  /** Row click handler */
  onRowClick?: (row: T) => void;
  /** Loading state */
  loading?: boolean;
  /** Message to show when no data */
  emptyMessage?: string;
  /** Items per page (default: 10) */
  pageSize?: number;
  /** Default sort field */
  defaultSortField?: keyof T;
  /** Default sort direction */
  defaultSortDirection?: 'asc' | 'desc';
  /** Custom mobile card renderer */
  renderMobileCard?: (props: MobileCardProps<T>) => ReactNode;
  /** Title to display above the table */
  title?: ReactNode;
  /** Action buttons to display in header */
  headerActions?: ReactNode;
}

/**
 * Generic DataTable component with search, filter, sort, and pagination
 */
export function DataTable<T extends { id: string | number }>({
  data,
  columns,
  searchable = false,
  searchFields,
  searchPlaceholder = 'Search...',
  onRowClick,
  loading = false,
  emptyMessage = 'No data found.',
  pageSize = 10,
  defaultSortField,
  defaultSortDirection = 'desc',
  renderMobileCard,
  title,
  headerActions,
}: DataTableProps<T>) {
  // Search state
  const [searchTerm, setSearchTerm] = useState('');

  // Sort state
  const [sortField, setSortField] = useState<keyof T | null>(
    defaultSortField ?? null
  );
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>(
    defaultSortDirection
  );

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);

  // Filter state - one filter array per filterable column
  const [columnFilters, setColumnFilters] = useState<
    Record<string, string[]>
  >({});
  const [columnSearchTerms, setColumnSearchTerms] = useState<
    Record<string, string>
  >({});

  // Reset pagination when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, columnFilters, columnSearchTerms]);

  // Determine which fields to search
  const effectiveSearchFields = useMemo(() => {
    if (searchFields) return searchFields;
    // Default to all columns
    return columns.map(c => c.field);
  }, [searchFields, columns]);

  // Filter data based on search and column filters
  const filteredData = useMemo(() => {
    return data.filter(row => {
      // Global search
      if (searchTerm) {
        const matchesSearch = effectiveSearchFields.some(field => {
          const value = row[field];
          if (value == null) return false;
          return String(value).toLowerCase().includes(searchTerm.toLowerCase());
        });
        if (!matchesSearch) return false;
      }

      // Column checkbox filters
      for (const [field, selectedValues] of Object.entries(columnFilters)) {
        if (selectedValues.length > 0) {
          const value = row[field as keyof T];
          if (!selectedValues.includes(String(value))) {
            return false;
          }
        }
      }

      // Column search terms
      for (const [field, term] of Object.entries(columnSearchTerms)) {
        if (term) {
          const value = row[field as keyof T];
          if (value == null) return false;
          if (!String(value).toLowerCase().includes(term.toLowerCase())) {
            return false;
          }
        }
      }

      return true;
    });
  }, [data, searchTerm, effectiveSearchFields, columnFilters, columnSearchTerms]);

  // Sort filtered data
  const sortedData = useMemo(() => {
    if (!sortField) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];

      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return sortDirection === 'asc' ? -1 : 1;
      if (bValue == null) return sortDirection === 'asc' ? 1 : -1;

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
      }

      // Fallback to string comparison
      return sortDirection === 'asc'
        ? String(aValue).localeCompare(String(bValue))
        : String(bValue).localeCompare(String(aValue));
    });
  }, [filteredData, sortField, sortDirection]);

  // Paginate data
  const totalItems = sortedData.length;
  const totalPages = Math.ceil(totalItems / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const paginatedData = sortedData.slice(startIndex, startIndex + pageSize);

  // Generate filter options for a column
  const getFilterOptions = (field: keyof T): FilterOption[] => {
    // Get unique values from filtered data (excluding this column's filter)
    const relevantData = data.filter(row => {
      // Apply all filters except this column
      if (searchTerm) {
        const matchesSearch = effectiveSearchFields.some(f => {
          const value = row[f];
          if (value == null) return false;
          return String(value).toLowerCase().includes(searchTerm.toLowerCase());
        });
        if (!matchesSearch) return false;
      }

      for (const [f, selectedValues] of Object.entries(columnFilters)) {
        if (f !== String(field) && selectedValues.length > 0) {
          const value = row[f as keyof T];
          if (!selectedValues.includes(String(value))) {
            return false;
          }
        }
      }

      for (const [f, term] of Object.entries(columnSearchTerms)) {
        if (f !== String(field) && term) {
          const value = row[f as keyof T];
          if (value == null) return false;
          if (!String(value).toLowerCase().includes(term.toLowerCase())) {
            return false;
          }
        }
      }

      return true;
    });

    const valueCounts = new Map<string, number>();
    relevantData.forEach(row => {
      const value = String(row[field] ?? '');
      valueCounts.set(value, (valueCounts.get(value) || 0) + 1);
    });

    return Array.from(valueCounts.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([value, count]) => ({
        label: value || '(empty)',
        value,
        count,
      }));
  };

  // Handle sort
  const handleSort = (field: keyof T) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Update column filter
  const setColumnFilter = (field: string, values: string[]) => {
    setColumnFilters(prev => ({ ...prev, [field]: values }));
  };

  // Update column search term
  const setColumnSearchTerm = (field: string, term: string) => {
    setColumnSearchTerms(prev => ({ ...prev, [field]: term }));
  };

  // Check if any filters are active
  const hasActiveFilters =
    Object.values(columnFilters).some(v => v.length > 0) ||
    Object.values(columnSearchTerms).some(v => v.length > 0);

  // Clear all filters
  const clearAllFilters = () => {
    setColumnFilters({});
    setColumnSearchTerms({});
    setSearchTerm('');
    setCurrentPage(1);
  };

  // Render cell content
  const renderCell = (row: T, column: ColumnDef<T>) => {
    const value = row[column.field];
    if (column.render) {
      return column.render(value, row);
    }
    return String(value ?? '');
  };

  return (
    <div className="space-y-3">
      {/* Header with Search and Actions */}
      {(title || searchable || headerActions) && (
        <div className="flex items-center gap-4 flex-wrap py-2">
          {title && (
            <div className="shrink-0">
              {typeof title === 'string' ? (
                <h2 className="text-xl font-bold text-card-foreground">{title}</h2>
              ) : (
                title
              )}
            </div>
          )}
          {searchable && (
            <div className="flex-1 min-w-[200px] relative">
              <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                placeholder={searchPlaceholder}
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="pl-8 h-8 text-sm"
              />
            </div>
          )}
          {headerActions}
        </div>
      )}

      {/* Active filters indicator */}
      {hasActiveFilters && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm text-muted-foreground">Active filters:</span>
          {Object.entries(columnFilters).map(([field, values]) =>
            values.length > 0 ? (
              <span
                key={field}
                className="inline-flex items-center gap-1 px-2 py-0.5 bg-primary/15 text-primary text-xs rounded-full"
              >
                {columns.find(c => String(c.field) === field)?.label}:{' '}
                {values.length === 1 ? values[0] : `${values.length} selected`}
              </span>
            ) : null
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={clearAllFilters}
            className="text-xs h-6 px-2"
          >
            <X className="h-3 w-3 mr-1" />
            Clear all
          </Button>
        </div>
      )}

      {/* Mobile card view */}
      {renderMobileCard && (
        <div className="md:hidden">
          <Card className="bg-card/50 backdrop-blur-sm border-border/50">
            <CardContent className="p-0">
              {loading ? (
                <div className="py-8 flex items-center justify-center">
                  <LoadingSpinner />
                </div>
              ) : paginatedData.length === 0 ? (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  {emptyMessage}
                </div>
              ) : (
                <div className="divide-y">
                  {paginatedData.map(row => (
                    <div key={row.id}>
                      {renderMobileCard({
                        row,
                        onClick: onRowClick ? () => onRowClick(row) : undefined,
                      })}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Desktop table view */}
      <div className={renderMobileCard ? 'hidden md:block' : ''}>
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  {columns.map(column => (
                    <TableHead
                      key={String(column.field)}
                      className={`
                        ${column.align === 'right' ? 'text-right' : ''}
                        ${column.width || ''}
                        ${column.className || ''}
                      `}
                    >
                      <div
                        className={`flex items-center gap-1 ${
                          column.align === 'right' ? 'justify-end' : ''
                        }`}
                      >
                        <SortableHeader
                          label={column.label}
                          field={String(column.field)}
                          sortField={sortField ? String(sortField) : null}
                          sortDirection={sortDirection}
                          onSort={() =>
                            column.sortable !== false && handleSort(column.field)
                          }
                          align={column.align}
                        />
                        {column.filterable && (
                          <ColumnFilterPopover
                            title={`Filter by ${column.label}`}
                            options={getFilterOptions(column.field)}
                            selectedValues={
                              columnFilters[String(column.field)] || []
                            }
                            onSelectionChange={values =>
                              setColumnFilter(String(column.field), values)
                            }
                            searchTerm={columnSearchTerms[String(column.field)] || ''}
                            onSearchChange={term =>
                              setColumnSearchTerm(String(column.field), term)
                            }
                          />
                        )}
                      </div>
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell
                      colSpan={columns.length}
                      className="text-center py-8"
                    >
                      <div className="flex items-center justify-center">
                        <LoadingSpinner />
                      </div>
                    </TableCell>
                  </TableRow>
                ) : paginatedData.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={columns.length}
                      className="text-center py-8 text-muted-foreground"
                    >
                      {emptyMessage}
                    </TableCell>
                  </TableRow>
                ) : (
                  paginatedData.map(row => (
                    <TableRow
                      key={row.id}
                      className={onRowClick ? 'cursor-pointer hover:bg-muted/50' : ''}
                      onClick={() => onRowClick?.(row)}
                    >
                      {columns.map(column => (
                        <TableCell
                          key={String(column.field)}
                          className={`
                            ${column.align === 'right' ? 'text-right' : ''}
                            ${column.className || ''}
                          `}
                        >
                          {renderCell(row, column)}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
          totalItems={totalItems}
          itemsPerPage={pageSize}
        />
      )}

      {/* Empty state when no data and not loading */}
      {!loading && data.length === 0 && (
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent className="text-center py-8">
            <p className="text-muted-foreground">{emptyMessage}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
