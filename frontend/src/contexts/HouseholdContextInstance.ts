import { createContext } from 'react';
import type { Household, HouseholdMember } from '@/lib/api/household';

export type Scope = 'personal' | 'household';

export interface HouseholdContextType {
  household: Household | null;
  isInHousehold: boolean;
  isLoading: boolean;
  scope: Scope;
  setScope: (scope: Scope) => void;
  partnerName: string | null;
  members: HouseholdMember[];
  refreshHousehold: () => Promise<void>;
}

export const HouseholdContext = createContext<HouseholdContextType | undefined>(
  undefined
);
