import { createContext } from 'react';
import type { DriveStatus } from '@/lib/api/driveStatements';

export interface DriveContextType {
  driveStatus: DriveStatus | null;
  isDriveActive: boolean;
  isLoading: boolean;
  refreshDriveStatus: () => Promise<void>;
}

export const DriveContext = createContext<DriveContextType | undefined>(
  undefined
);
