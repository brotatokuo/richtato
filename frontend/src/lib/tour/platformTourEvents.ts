import { ACTIONS, EVENTS, STATUS, type EventData } from 'react-joyride';

export const JOYRIDE_PORTAL_ID = 'react-joyride-portal';

export function cleanupJoyridePortal() {
  document.getElementById(JOYRIDE_PORTAL_ID)?.remove();
}

export function shouldEndPlatformTour(
  data: EventData,
  stepCount: number
): boolean {
  const { action, index, status, type } = data;

  if (status === STATUS.FINISHED || status === STATUS.SKIPPED) {
    return true;
  }

  if (type === EVENTS.TOUR_END) {
    return true;
  }

  if (action === ACTIONS.SKIP || action === ACTIONS.CLOSE) {
    return true;
  }

  if (
    (type === EVENTS.STEP_AFTER || type === EVENTS.TARGET_NOT_FOUND) &&
    action === ACTIONS.NEXT &&
    index + 1 >= stepCount
  ) {
    return true;
  }

  return false;
}

export function getNextPlatformTourStepIndex(
  data: EventData,
  stepCount: number
): number | null {
  const { action, index, type } = data;

  if (type !== EVENTS.STEP_AFTER && type !== EVENTS.TARGET_NOT_FOUND) {
    return null;
  }

  if (action === ACTIONS.NEXT) {
    const nextIndex = index + 1;
    return nextIndex < stepCount ? nextIndex : null;
  }

  if (action === ACTIONS.PREV) {
    return Math.max(index - 1, 0);
  }

  return null;
}
