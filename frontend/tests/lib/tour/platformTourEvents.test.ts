import { ACTIONS, EVENTS, STATUS, type EventData } from 'react-joyride';
import { describe, expect, it } from 'vitest';
import {
  getNextPlatformTourStepIndex,
  shouldEndPlatformTour,
} from '@/lib/tour/platformTourEvents';

const STEP_COUNT = 9;

function makeEvent(partial: Partial<EventData>): EventData {
  return {
    action: ACTIONS.NEXT,
    controlled: true,
    error: null,
    index: 0,
    lifecycle: 'complete',
    origin: null,
    scroll: null,
    scrolling: false,
    size: STEP_COUNT,
    status: STATUS.RUNNING,
    step: {} as EventData['step'],
    type: EVENTS.STEP_AFTER,
    waiting: false,
    ...partial,
  };
}

describe('platformTourEvents', () => {
  it('ends the tour when skipped or finished', () => {
    expect(
      shouldEndPlatformTour(
        makeEvent({ status: STATUS.SKIPPED, type: EVENTS.TOUR_END }),
        STEP_COUNT
      )
    ).toBe(true);
    expect(
      shouldEndPlatformTour(
        makeEvent({ status: STATUS.FINISHED, type: EVENTS.TOUR_END }),
        STEP_COUNT
      )
    ).toBe(true);
  });

  it('ends the tour when advancing past the last step', () => {
    expect(
      shouldEndPlatformTour(
        makeEvent({
          action: ACTIONS.NEXT,
          index: STEP_COUNT - 1,
          type: EVENTS.STEP_AFTER,
        }),
        STEP_COUNT
      )
    ).toBe(true);
  });

  it('does not advance past the last step index', () => {
    expect(
      getNextPlatformTourStepIndex(
        makeEvent({
          action: ACTIONS.NEXT,
          index: STEP_COUNT - 1,
          type: EVENTS.STEP_AFTER,
        }),
        STEP_COUNT
      )
    ).toBeNull();
  });

  it('advances to the next step for intermediate next actions', () => {
    expect(
      getNextPlatformTourStepIndex(
        makeEvent({
          action: ACTIONS.NEXT,
          index: 2,
          type: EVENTS.STEP_AFTER,
        }),
        STEP_COUNT
      )
    ).toBe(3);
  });
});
