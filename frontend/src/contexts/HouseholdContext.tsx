import { useAuth } from '@/hooks/useAuth';
import { householdApi } from '@/lib/api/household';
import { ReactNode, useCallback, useContext, useEffect, useState } from 'react';
import type { Household } from '@/lib/api/household';
import { HouseholdContext } from './HouseholdContextInstance';

export type { HouseholdContextType } from './HouseholdContextInstance';
export { HouseholdContext } from './HouseholdContextInstance';

export function HouseholdProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, user } = useAuth();
  const [household, setHousehold] = useState<Household | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const refreshHousehold = useCallback(async () => {
    if (!isAuthenticated) {
      setHousehold(null);
      return;
    }
    setIsLoading(true);
    try {
      const data = await householdApi.getHousehold();
      setHousehold(data);
    } catch {
      setHousehold(null);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    refreshHousehold();
  }, [refreshHousehold]);

  const isInHousehold = !!household;
  const members = household?.members ?? [];
  const partnerName =
    members.find(m => m.user_id !== user?.id)?.username ?? null;

  return (
    <HouseholdContext.Provider
      value={{
        household,
        isInHousehold,
        isLoading,
        partnerName,
        members,
        refreshHousehold,
      }}
    >
      {children}
    </HouseholdContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useHousehold() {
  const context = useContext(HouseholdContext);
  if (!context) {
    throw new Error('useHousehold must be used within a HouseholdProvider');
  }
  return context;
}
