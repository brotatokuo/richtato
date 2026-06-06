import { getJoyrideThemeOptions } from '@/lib/tour/tourTheme';
import {
  cleanupJoyridePortal,
  getNextPlatformTourStepIndex,
  shouldEndPlatformTour,
} from '@/lib/tour/platformTourEvents';
import {
  createPlatformTourSteps,
  PLATFORM_TOUR_RESUME_KEY,
} from '@/lib/tour/platformTourSteps';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Joyride, type EventData } from 'react-joyride';
import { useNavigate } from 'react-router-dom';

interface PlatformTourProps {
  run: boolean;
  initialStepIndex?: number;
  onComplete: () => void;
  onRunningChange?: (running: boolean) => void;
}

export function PlatformTour({
  run,
  initialStepIndex = 0,
  onComplete,
  onRunningChange,
}: PlatformTourProps) {
  const navigate = useNavigate();
  const [stepIndex, setStepIndex] = useState(initialStepIndex);
  const finishedRef = useRef(false);

  const steps = useMemo(
    () => createPlatformTourSteps(path => navigate(path)),
    [navigate]
  );

  useEffect(() => {
    onRunningChange?.(run);
  }, [onRunningChange, run]);

  useEffect(() => {
    if (run) {
      finishedRef.current = false;
      setStepIndex(initialStepIndex);
    }
  }, [initialStepIndex, run]);

  useEffect(() => {
    if (!run) {
      cleanupJoyridePortal();
    }
  }, [run]);

  const endTour = useCallback(() => {
    if (finishedRef.current) {
      return;
    }
    finishedRef.current = true;
    sessionStorage.removeItem(PLATFORM_TOUR_RESUME_KEY);
    onComplete();
  }, [onComplete]);

  const handleEvent = useCallback(
    (data: EventData) => {
      if (shouldEndPlatformTour(data, steps.length)) {
        endTour();
        return;
      }

      const nextIndex = getNextPlatformTourStepIndex(data, steps.length);
      if (nextIndex !== null) {
        setStepIndex(nextIndex);
      }
    },
    [endTour, steps.length]
  );

  const theme = getJoyrideThemeOptions();

  return (
    <Joyride
      continuous
      run={run}
      stepIndex={stepIndex}
      steps={steps}
      scrollToFirstStep
      onEvent={handleEvent}
      locale={{
        back: 'Back',
        close: 'Close',
        last: 'Finish',
        next: 'Next',
        nextWithProgress: 'Next ({current} of {total})',
        skip: 'Skip tour',
      }}
      options={{
        ...theme,
        overlayClickAction: false,
        dismissKeyAction: 'close',
        closeButtonAction: 'skip',
        buttons: ['back', 'skip', 'primary'],
        showProgress: true,
        targetWaitTimeout: 5000,
        beforeTimeout: 10000,
      }}
      styles={{
        tooltip: {
          borderRadius: 12,
          padding: 16,
        },
        tooltipTitle: {
          fontSize: '1rem',
          fontWeight: 600,
          marginBottom: 8,
        },
        tooltipContent: {
          fontSize: '0.875rem',
          lineHeight: 1.5,
        },
        buttonPrimary: {
          borderRadius: 8,
          fontSize: '0.875rem',
        },
        buttonBack: {
          borderRadius: 8,
          fontSize: '0.875rem',
        },
        buttonSkip: {
          fontSize: '0.875rem',
        },
      }}
    />
  );
}
