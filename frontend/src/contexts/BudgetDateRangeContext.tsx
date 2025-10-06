import { createContext, ReactNode, useContext, useMemo, useState } from 'react';

interface BudgetDateRange {
  startDate: string; // YYYY-MM-DD
  endDate: string; // YYYY-MM-DD
  setRange: (range: { startDate: string; endDate: string }) => void;
}

const BudgetDateRangeContext = createContext<BudgetDateRange | undefined>(
  undefined
);

function getCurrentMonthRange(): { startDate: string; endDate: string } {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), 1);
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  const toIso = (d: Date) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
      d.getDate()
    ).padStart(2, '0')}`;
  return { startDate: toIso(start), endDate: toIso(end) };
}

export function BudgetDateRangeProvider({ children }: { children: ReactNode }) {
  const initial = useMemo(getCurrentMonthRange, []);
  const [range, setRangeState] = useState(initial);

  const value = useMemo<BudgetDateRange>(
    () => ({
      startDate: range.startDate,
      endDate: range.endDate,
      setRange: ({ startDate, endDate }) =>
        setRangeState({ startDate, endDate }),
    }),
    [range]
  );

  return (
    <BudgetDateRangeContext.Provider value={value}>
      {children}
    </BudgetDateRangeContext.Provider>
  );
}

export function useBudgetDateRange(): BudgetDateRange {
  const ctx = useContext(BudgetDateRangeContext);
  if (!ctx) {
    throw new Error(
      'useBudgetDateRange must be used within BudgetDateRangeProvider'
    );
  }
  return ctx;
}
