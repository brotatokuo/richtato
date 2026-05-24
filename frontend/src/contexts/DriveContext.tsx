import { useAuth } from '@/hooks/useAuth';
import { driveStatementsApi } from '@/lib/api/driveStatements';
import type { DriveStatus } from '@/lib/api/driveStatements';
import { ReactNode, useCallback, useContext, useEffect, useState } from 'react';
import { DriveContext } from './DriveContextInstance';

export type { DriveContextType } from './DriveContextInstance';
export { DriveContext } from './DriveContextInstance';

export function DriveProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [driveStatus, setDriveStatus] = useState<DriveStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const refreshDriveStatus = useCallback(async () => {
    if (!isAuthenticated) {
      setDriveStatus(null);
      return;
    }
    setIsLoading(true);
    try {
      const status = await driveStatementsApi.getStatus();
      setDriveStatus(status);
    } catch {
      setDriveStatus(null);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    void refreshDriveStatus();
  }, [refreshDriveStatus]);

  const isDriveActive = Boolean(driveStatus?.active);

  return (
    <DriveContext.Provider
      value={{
        driveStatus,
        isDriveActive,
        isLoading,
        refreshDriveStatus,
      }}
    >
      {children}
    </DriveContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useDrive() {
  const context = useContext(DriveContext);
  if (!context) {
    throw new Error('useDrive must be used within a DriveProvider');
  }
  return context;
}
