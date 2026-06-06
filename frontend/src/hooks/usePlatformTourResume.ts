import { PLATFORM_TOUR_RESUME_KEY } from '@/lib/tour/platformTourSteps';
import { useEffect } from 'react';

export function usePlatformTourResumeEffect(
  runTour: (stepIndex?: number) => void,
  isTourRunning: boolean
) {
  useEffect(() => {
    const resumeValue = sessionStorage.getItem(PLATFORM_TOUR_RESUME_KEY);
    if (!resumeValue || isTourRunning) {
      return;
    }

    const resumeIndex = Number.parseInt(resumeValue, 10);
    if (Number.isNaN(resumeIndex)) {
      sessionStorage.removeItem(PLATFORM_TOUR_RESUME_KEY);
      return;
    }

    runTour(resumeIndex);
  }, [isTourRunning, runTour]);
}
