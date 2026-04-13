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
import { useMemo, useState } from 'react';

interface MonthYearPickerProps {
  year: number;
  month: number;
  onChange: (year: number, month: number) => void;
  className?: string;
}

const MONTHS = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
];

export function MonthYearPicker({
  year,
  month,
  onChange,
  className,
}: MonthYearPickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [pickerYear, setPickerYear] = useState(year);

  // Format display string
  const displayText = useMemo(() => {
    const date = new Date(year, month - 1, 1);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      year: 'numeric',
    });
  }, [year, month]);

  const handleMonthSelect = (selectedMonth: number) => {
    onChange(pickerYear, selectedMonth);
    setIsOpen(false);
  };

  const handleYearChange = (delta: number) => {
    setPickerYear(prev => prev + delta);
  };

  // Reset picker year when dropdown opens
  const handleOpenChange = (open: boolean) => {
    if (open) {
      setPickerYear(year);
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
            <span>{displayText}</span>
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
          {/* Year selector */}
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={() => handleYearChange(-1)}
              className="p-1.5 rounded-md hover:bg-muted transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="text-lg font-semibold">{pickerYear}</span>
            <button
              onClick={() => handleYearChange(1)}
              className="p-1.5 rounded-md hover:bg-muted transition-colors"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>

          {/* Month grid (3x4) */}
          <div className="grid grid-cols-4 gap-2">
            {MONTHS.map((monthName, index) => {
              const monthNum = index + 1;
              const isSelected = pickerYear === year && monthNum === month;
              const isCurrentMonth =
                pickerYear === new Date().getFullYear() &&
                monthNum === new Date().getMonth() + 1;

              return (
                <button
                  key={monthName}
                  onClick={() => handleMonthSelect(monthNum)}
                  className={cn(
                    'py-2 px-1 rounded-lg text-sm font-medium transition-all',
                    'hover:bg-primary/10',
                    isSelected &&
                      'bg-primary text-primary-foreground hover:bg-primary/90',
                    !isSelected && isCurrentMonth && 'ring-1 ring-primary/50'
                  )}
                >
                  {monthName}
                </button>
              );
            })}
          </div>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
