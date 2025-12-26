import * as React from 'react';
import { CalendarIcon } from 'lucide-react';
import type { DateRange } from 'react-day-picker';
import { format } from 'date-fns';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

// #region agent log
fetch('http://127.0.0.1:7242/ingest/865d0811-47b7-40c2-94b4-9a9a09a7dc1a',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'date-range-picker.tsx:1',message:'Module loaded',data:{hasFormat:typeof format,hasCalendar:typeof Calendar},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'H2,H4'})}).catch(()=>{});
// #endregion

interface DateRangePickerProps {
  dateRange?: DateRange;
  onDateRangeChange?: (range: DateRange | undefined) => void;
  className?: string;
  disabled?: boolean;
}

export function DateRangePicker({
  dateRange,
  onDateRangeChange,
  className,
  disabled,
}: DateRangePickerProps) {
  // #region agent log
  fetch('http://127.0.0.1:7242/ingest/865d0811-47b7-40c2-94b4-9a9a09a7dc1a',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'date-range-picker.tsx:28',message:'DateRangePicker rendered',data:{dateRange:dateRange?{from:dateRange.from?.toString(),to:dateRange.to?.toString()}:null,disabled},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'H3,H4'})}).catch(()=>{});
  // #endregion
  const [open, setOpen] = React.useState(false);

  return (
    <div className={cn('grid gap-2', className)}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            id="date"
            variant={'outline'}
            disabled={disabled}
            className={cn(
              'w-full justify-start text-left font-normal',
              !dateRange && 'text-muted-foreground'
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {dateRange?.from ? (
              dateRange.to ? (
                <>
                  {/* #region agent log */}
                  {(()=>{fetch('http://127.0.0.1:7242/ingest/865d0811-47b7-40c2-94b4-9a9a09a7dc1a',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'date-range-picker.tsx:48',message:'Formatting date range',data:{from:dateRange.from?.toString(),to:dateRange.to?.toString()},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'H2,H3'})}).catch(()=>{});return null})()}
                  {/* #endregion */}
                  {format(dateRange.from, 'LLL dd, y')} -{' '}
                  {format(dateRange.to, 'LLL dd, y')}
                </>
              ) : (
                format(dateRange.from, 'LLL dd, y')
              )
            ) : (
              <span>Pick a date range</span>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          {/* #region agent log */}
          {(()=>{fetch('http://127.0.0.1:7242/ingest/865d0811-47b7-40c2-94b4-9a9a09a7dc1a',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'date-range-picker.tsx:62',message:'Rendering Calendar',data:{hasCalendar:typeof Calendar,mode:'range',dateRangeFrom:dateRange?.from?.toString()},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'H4'})}).catch(()=>{});return null})()}
          {/* #endregion */}
          <Calendar
            initialFocus
            mode="range"
            defaultMonth={dateRange?.from}
            selected={dateRange}
            onSelect={onDateRangeChange}
            numberOfMonths={2}
          />
        </PopoverContent>
      </Popover>
    </div>
  );
}
