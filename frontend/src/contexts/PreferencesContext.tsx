import { useAuth } from '@/hooks/useAuth';
import { preferencesApi, type UserPreferencesPayload } from '@/lib/api/user';
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

interface PreferencesContextType {
  preferences: UserPreferencesPayload;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  updatePreferences: (updates: Partial<UserPreferencesPayload>) => Promise<void>;
}

const PreferencesContext = createContext<PreferencesContextType | undefined>(undefined);

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [preferences, setPreferences] = useState<UserPreferencesPayload>({
    theme: 'system',
    currency: 'USD',
    date_format: 'MM/DD/YYYY',
    timezone: 'UTC',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPreferences = async () => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const prefs = await preferencesApi.get();
      setPreferences({
        theme: prefs.theme || 'system',
        currency: prefs.currency || 'USD',
        date_format: prefs.date_format || 'MM/DD/YYYY',
        timezone: prefs.timezone || 'UTC',
      });
    } catch (e: any) {
      setError(e?.message ?? 'Failed to load preferences');
      console.error('Failed to load preferences:', e);
    } finally {
      setLoading(false);
    }
  };

  const updatePreferences = async (updates: Partial<UserPreferencesPayload>) => {
    if (!isAuthenticated) {
      throw new Error('Must be authenticated to update preferences');
    }

    try {
      setError(null);
      const updated = await preferencesApi.update(updates);
      setPreferences({
        theme: updated.theme || 'system',
        currency: updated.currency || 'USD',
        date_format: updated.date_format || 'MM/DD/YYYY',
        timezone: updated.timezone || 'UTC',
      });
    } catch (e: any) {
      const errorMsg = e?.message ?? 'Failed to update preferences';
      setError(errorMsg);
      console.error('Failed to update preferences:', e);
      throw e;
    }
  };

  useEffect(() => {
    fetchPreferences();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  return (
    <PreferencesContext.Provider
      value={{
        preferences,
        loading,
        error,
        refetch: fetchPreferences,
        updatePreferences,
      }}
    >
      {children}
    </PreferencesContext.Provider>
  );
}

export function usePreferences() {
  const context = useContext(PreferencesContext);
  if (context === undefined) {
    throw new Error('usePreferences must be used within a PreferencesProvider');
  }
  return context;
}
