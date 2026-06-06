import { describe, expect, it } from 'vitest';
import {
  createPlatformTourSteps,
  getPlatformTourStepIndex,
  PLATFORM_TOUR_STEP_DEFINITIONS,
  PLATFORM_TOUR_STEP_IDS,
} from '@/lib/tour/platformTourSteps';
import {
  queryFirstSelector,
  waitForAnyTarget,
  waitForTarget,
} from '@/lib/tour/waitForTarget';

describe('platformTourSteps', () => {
  it('defines nine ordered steps with stable ids', () => {
    expect(PLATFORM_TOUR_STEP_IDS).toHaveLength(9);
    expect(PLATFORM_TOUR_STEP_DEFINITIONS.map(step => step.id)).toEqual([
      ...PLATFORM_TOUR_STEP_IDS,
    ]);
  });

  it('maps step ids to indexes', () => {
    expect(getPlatformTourStepIndex('drive-folder-actions')).toBe(7);
    expect(getPlatformTourStepIndex('finish')).toBe(8);
  });

  it('creates joyride steps with routes and hooks', () => {
    const steps = createPlatformTourSteps(() => undefined);
    expect(steps).toHaveLength(9);
    expect(steps[0]?.id).toBe('welcome');
    expect(steps[4]?.id).toBe('setup-statements');
    expect(typeof steps[4]?.before).toBe('function');
  });
});

describe('waitForTarget', () => {
  it('resolves when the selector appears', async () => {
    const marker = document.createElement('div');
    marker.setAttribute('data-testid', 'tour-target');
    document.body.appendChild(marker);

    await expect(
      waitForTarget('[data-testid="tour-target"]', { timeout: 500 })
    ).resolves.toBe(marker);

    marker.remove();
  });

  it('resolves when any selector appears', async () => {
    const marker = document.createElement('div');
    marker.setAttribute('data-testid', 'tour-target-alt');
    document.body.appendChild(marker);

    await expect(
      waitForAnyTarget(
        ['[data-testid="missing"]', '[data-testid="tour-target-alt"]'],
        { timeout: 500 }
      )
    ).resolves.toBe(marker);

    marker.remove();
  });

  it('queryFirstSelector returns the first matching element', () => {
    const first = document.createElement('div');
    first.setAttribute('data-testid', 'first');
    const second = document.createElement('div');
    second.setAttribute('data-testid', 'second');
    document.body.append(first, second);

    expect(
      queryFirstSelector('[data-testid="missing"]', '[data-testid="first"]')
    ).toBe(first);

    first.remove();
    second.remove();
  });
});
