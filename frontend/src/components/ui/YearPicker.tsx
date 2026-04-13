import { cn } from '@/lib/utils';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from './dropdown-menu';
import {
  CalendarDays,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useState } from 'react';

interface YearPickerProps {
  year: number;
  availableYears?: number[];
  onChange: (year: number) => void;
  className?: string;
}

export function YearPicker({
  year,
  availableYears,
  onChange,
  className,
}: YearPickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [viewYear, setViewYear] = useState(year);

  // Generate years to display (show 12 years at a time in a 3x4 grid)
  const startYear = Math.floor(viewYear / 12) * 12;
  const yearsToShow = Array.from({ length: 12 }, (_, i) => startYear + i);

  const handleYearSelect = (selectedYear: number) => {
    onChange(selectedYear);
    setIsOpen(false);
  };

  const handleViewChange = (delta: number) => {
    setViewYear(prev => prev + delta * 12);
  };

  // Reset view year when dropdown opens
  const handleOpenChange = (open: boolean) => {
    if (open) {
      setViewYear(year);
    }
    setIsOpen(open);
  };

  return (
    <div className={cn(className)}>
      <DropdownMenu open={isOpen} onOpenChange={handleOpenChange}>
        <DropdownMenuTrigger asChild>
          <button
            className={cn(
              'flex items-center gap-2 px-4 py-2.5',
              'rounded-full',
              'bg-background/80 backdrop-blur-md',
              'border border-border/50',
              'shadow-lg shadow-black/10',
              'text-sm font-medium text-foreground',
              'hover:bg-background/90 hover:border-border',
              'transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-primary/50'
            )}
          >
            <CalendarDays className="h-4 w-4 text-muted-foreground" />
            <span>{year}</span>
            <ChevronDown
              className={cn(
                'h-4 w-4 text-muted-foreground transition-transform duration-200',
                isOpen && 'rotate-180'
              )}
            />
          </button>
        </DropdownMenuTrigger>

        <DropdownMenuContent
          align="end"
          side="bottom"
          sideOffset={8}
          className="w-[280px] p-4 bg-background/95 backdrop-blur-md"
        >
          {/* Year range navigation */}
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={() => handleViewChange(-1)}
              className="p-1.5 rounded-md hover:bg-muted transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="text-sm font-medium text-muted-foreground">
              {startYear} - {startYear + 11}
            </span>
            <button
              onClick={() => handleViewChange(1)}
              className="p-1.5 rounded-md hover:bg-muted transition-colors"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>

          {/* Year grid (3x4) */}
          <div className="grid grid-cols-4 gap-2">
            {yearsToShow.map(y => {
              const isSelected = y === year;
              const isCurrentYear = y === new Date().getFullYear();
              const isAvailable = !availableYears || availableYears.includes(y);

              return (
                <button
                  key={y}
                  onClick={() => isAvailable && handleYearSelect(y)}
                  disabled={!isAvailable}
                  className={cn(
                    'py-2 px-1 rounded-lg text-sm font-medium transition-all',
                    'hover:bg-primary/10',
                    isSelected &&
                      'bg-primary text-primary-foreground hover:bg-primary/90',
                    !isSelected && isCurrentYear && 'ring-1 ring-primary/50',
                    !isAvailable &&
                      'opacity-40 cursor-not-allowed hover:bg-transparent'
                  )}
                >
                  {y}
                </button>
              );
            })}
          </div>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
