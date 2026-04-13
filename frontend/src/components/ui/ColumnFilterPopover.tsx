import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { Filter, X } from 'lucide-react';
import * as React from 'react';

export interface FilterOption {
  label: string;
  value: string;
  count?: number;
}

export interface ColumnFilterPopoverProps {
  options: FilterOption[];
  selectedValues: string[];
  onSelectionChange: (values: string[]) => void;
  title: string;
  className?: string;
  align?: 'start' | 'center' | 'end';
  searchTerm?: string;
  onSearchChange?: (term: string) => void;
}

export function ColumnFilterPopover({
  options,
  selectedValues,
  onSelectionChange,
  title,
  className,
  align = 'start',
  searchTerm: externalSearchTerm,
  onSearchChange,
}: ColumnFilterPopoverProps) {
  const [internalSearchTerm, setInternalSearchTerm] = React.useState('');
  const [open, setOpen] = React.useState(false);

  // Use external search term if provided, otherwise use internal
  const searchTerm = externalSearchTerm ?? internalSearchTerm;
  const setSearchTerm = onSearchChange ?? setInternalSearchTerm;

  const filteredOptions = React.useMemo(() => {
    if (!searchTerm) return options;
    return options.filter(option =>
      option.label.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [options, searchTerm]);

  const handleToggle = (value: string) => {
    const newValues = selectedValues.includes(value)
      ? selectedValues.filter(v => v !== value)
      : [...selectedValues, value];
    onSelectionChange(newValues);
  };

  const handleSelectAll = () => {
    onSelectionChange(filteredOptions.map(o => o.value));
  };

  const handleClearAll = () => {
    onSelectionChange([]);
  };

  const hasCheckboxFilters = selectedValues.length > 0;
  const hasSearchFilter = Boolean(searchTerm);
  const hasActiveFilters = hasCheckboxFilters || hasSearchFilter;

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className={cn(
            'h-7 px-2 gap-1 relative',
            hasActiveFilters && 'text-primary',
            className
          )}
        >
          <Filter className="h-3.5 w-3.5" />
          {hasActiveFilters && (
            <>
              {/* Active filter dot indicator */}
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-primary" />
              {/* Count badge for checkbox selections */}
              {hasCheckboxFilters && (
                <span className="min-w-4 h-4 flex items-center justify-center rounded-full bg-primary text-primary-foreground text-[10px] font-medium">
                  {selectedValues.length}
                </span>
              )}
            </>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align={align} className="min-w-56 max-w-80">
        <DropdownMenuLabel className="flex items-center justify-between">
          <span>{title}</span>
          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              className="h-5 px-1 text-xs text-muted-foreground hover:text-foreground"
              onClick={() => {
                handleClearAll();
                setSearchTerm('');
              }}
            >
              <X className="h-3 w-3 mr-0.5" />
              Clear
            </Button>
          )}
        </DropdownMenuLabel>
        <div className="px-2 py-1.5">
          <Input
            placeholder="Search..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="h-7 text-sm"
            onClick={e => e.stopPropagation()}
            onKeyDown={e => e.stopPropagation()}
          />
        </div>
        <DropdownMenuSeparator />
        <div className="px-2 py-1 flex gap-1">
          <Button
            variant="outline"
            size="sm"
            className="h-6 text-xs flex-1"
            onClick={handleSelectAll}
          >
            Select All
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-6 text-xs flex-1"
            onClick={handleClearAll}
          >
            Clear All
          </Button>
        </div>
        <DropdownMenuSeparator />
        <div className="max-h-48 overflow-y-auto">
          {filteredOptions.length === 0 ? (
            <div className="px-2 py-4 text-center text-sm text-muted-foreground">
              No options found
            </div>
          ) : (
            filteredOptions.map(option => (
              <DropdownMenuCheckboxItem
                key={option.value}
                checked={selectedValues.includes(option.value)}
                onCheckedChange={() => handleToggle(option.value)}
                onSelect={e => e.preventDefault()}
              >
                <span className="flex-1 break-words whitespace-normal">
                  {option.label}
                </span>
                {option.count !== undefined && (
                  <span className="ml-2 text-xs text-muted-foreground">
                    {option.count}
                  </span>
                )}
              </DropdownMenuCheckboxItem>
            ))
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
