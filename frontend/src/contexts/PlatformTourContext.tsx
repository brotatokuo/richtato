import { PlatformTour } from '@/components/tour/PlatformTour';
import { useAuth } from '@/hooks/useAuth';
import { usePlatformTourResumeEffect } from '@/hooks/usePlatformTourResume';
import { usePreferences } from '@/contexts/PreferencesContext';
import {
  getPlatformTourStepIndex,
  PLATFORM_TOUR_RESUME_KEY,
} from '@/lib/tour/platformTourSteps';
import { cleanupJoyridePortal } from '@/lib/tour/platformTourEvents';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { useNavigate } from 'react-router-dom';

interface PlatformTourContextType {
  isRunning: boolean;
  startTour: (stepIndex?: number) => void;
  stopTour: () => void;
  markOAuthResume: () => void;
}

const PlatformTourContext = createContext<PlatformTourContextType | undefined>(
  undefined
);

export function PlatformTourProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const { preferences, loading, initialized, updatePreferences } =
    usePreferences();
  const navigate = useNavigate();
  const [run, setRun] = useState(false);
  const [initialStepIndex, setInitialStepIndex] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const autoStartedRef = useRef(false);

  const completeTour = useCallback(async () => {
    setRun(false);
    setIsRunning(false);
    sessionStorage.removeItem(PLATFORM_TOUR_RESUME_KEY);
    cleanupJoyridePortal();

    if (preferences.platform_tour_completed) {
      return;
    }

    try {
      await updatePreferences({ platform_tour_completed: true });
    } catch {
      // Preference persistence failure should not block closing the tour.
    }
  }, [preferences.platform_tour_completed, updatePreferences]);

  const startTour = useCallback(
    (stepIndex = 0) => {
      setInitialStepIndex(stepIndex);
      setRun(true);
      if (stepIndex === 0) {
        navigate('/dashboard');
      }
    },
    [navigate]
  );

  const stopTour = useCallback(() => {
    setRun(false);
    setIsRunning(false);
  }, []);

  const markOAuthResume = useCallback(() => {
    sessionStorage.setItem(
      PLATFORM_TOUR_RESUME_KEY,
      String(getPlatformTourStepIndex('drive-folder-actions'))
    );
  }, []);

  usePlatformTourResumeEffect(startTour, isRunning);

  useEffect(() => {
    if (
      !isAuthenticated ||
      !initialized ||
      loading ||
      preferences.platform_tour_completed ||
      autoStartedRef.current ||
      isRunning ||
      run
    ) {
      return;
    }

    if (sessionStorage.getItem(PLATFORM_TOUR_RESUME_KEY)) {
      return;
    }

    autoStartedRef.current = true;
    startTour(0);
  }, [
    isAuthenticated,
    initialized,
    isRunning,
    loading,
    preferences.platform_tour_completed,
    run,
    startTour,
  ]);

  const value = useMemo(
    () => ({
      isRunning,
      startTour,
      stopTour,
      markOAuthResume,
    }),
    [isRunning, markOAuthResume, startTour, stopTour]
  );

  return (
    <PlatformTourContext.Provider value={value}>
      {children}
      <PlatformTour
        run={run}
        initialStepIndex={initialStepIndex}
        onComplete={() => {
          void completeTour();
        }}
        onRunningChange={setIsRunning}
      />
    </PlatformTourContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function usePlatformTour() {
  const context = useContext(PlatformTourContext);
  if (!context) {
    throw new Error(
      'usePlatformTour must be used within a PlatformTourProvider'
    );
  }
  return context;
}
