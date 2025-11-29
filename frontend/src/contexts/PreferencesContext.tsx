import { preferencesApi, type UserPreferencesPayload } from '@/lib/api/user';
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

interface PreferencesContextType {
  preferences: UserPreferencesPayload;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

const PreferencesContext = createContext<PreferencesContextType | undefined>(undefined);

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const [preferences, setPreferences] = useState<UserPreferencesPayload>({
    theme: 'system',
    currency: 'USD',
    date_format: 'MM/DD/YYYY',
    timezone: 'UTC',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPreferences = async () => {
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

  useEffect(() => {
    fetchPreferences();
  }, []);

  return (
    <PreferencesContext.Provider
      value={{
        preferences,
        loading,
        error,
        refetch: fetchPreferences,
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
