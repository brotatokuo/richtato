import type { Step } from 'react-joyride';
import { waitForTarget } from '@/lib/tour/waitForTarget';

export const PLATFORM_TOUR_RESUME_KEY = 'platform_tour_resume_step';

export const TOUR_TARGETS = {
  dashboardOverview: '[data-tour="dashboard-overview"]',
  navAccounts: '[data-tour="nav-accounts"]',
  addAccount: '[data-tour="add-account"]',
  navSetup: '[data-tour="nav-setup"]',
  navSetupMobile: '[data-tour="nav-setup-mobile"]',
  navMoreMobile: '[data-tour="nav-more-mobile"]',
  setupStatementsTab: '[data-tour="setup-statements-tab"]',
  driveStatus: '[data-tour="drive-status"]',
  driveConnect: '[data-tour="drive-connect"]',
  driveFolderActions: '[data-tour="drive-folder-actions"]',
} as const;

export const PLATFORM_TOUR_STEP_IDS = [
  'welcome',
  'dashboard-overview',
  'nav-accounts',
  'add-account',
  'setup-statements',
  'drive-status',
  'drive-connect',
  'drive-folder-actions',
  'finish',
] as const;

export type PlatformTourStepId = (typeof PLATFORM_TOUR_STEP_IDS)[number];

export interface PlatformTourStepDefinition {
  id: PlatformTourStepId;
  route: string;
}

export const PLATFORM_TOUR_STEP_DEFINITIONS: PlatformTourStepDefinition[] = [
  { id: 'welcome', route: '/dashboard' },
  { id: 'dashboard-overview', route: '/dashboard' },
  { id: 'nav-accounts', route: '/dashboard' },
  { id: 'add-account', route: '/accounts' },
  { id: 'setup-statements', route: '/setup?tab=statements' },
  { id: 'drive-status', route: '/setup?tab=statements' },
  { id: 'drive-connect', route: '/setup?tab=statements' },
  { id: 'drive-folder-actions', route: '/setup?tab=statements' },
  { id: 'finish', route: '/setup?tab=statements' },
];

async function ensureRoute(
  navigate: (path: string) => void,
  route: string,
  targetSelector: string
): Promise<void> {
  const url = new URL(route, window.location.origin);
  const needsNavigation =
    window.location.pathname !== url.pathname ||
    window.location.search !== url.search;

  if (needsNavigation) {
    navigate(`${url.pathname}${url.search}`);
  }

  await waitForTarget(targetSelector);
}

export function getPlatformTourStepIndex(stepId: PlatformTourStepId): number {
  return PLATFORM_TOUR_STEP_IDS.indexOf(stepId);
}

export function createPlatformTourSteps(
  navigate: (path: string) => void
): Step[] {
  const goTo = (route: string, targetSelector: string) =>
    ensureRoute(navigate, route, targetSelector);

  return [
    {
      id: 'welcome',
      target: 'body',
      placement: 'center',
      title: 'Welcome to Richtato',
      content:
        'This quick tour shows how to add accounts and connect Google Drive for statement storage—the foundation for tracking your finances here.',
      skipBeacon: true,
      before: () => goTo('/dashboard', TOUR_TARGETS.dashboardOverview),
    },
    {
      id: 'dashboard-overview',
      target: TOUR_TARGETS.dashboardOverview,
      placement: 'bottom',
      title: 'Your financial dashboard',
      content:
        'See income, spending, net worth, and trends at a glance. Data fills in once you add accounts and import statements.',
      skipBeacon: true,
      before: () => goTo('/dashboard', TOUR_TARGETS.dashboardOverview),
    },
    {
      id: 'nav-accounts',
      target: TOUR_TARGETS.navAccounts,
      placement: 'right',
      title: 'Accounts',
      content:
        'Start by adding your bank, credit card, and investment accounts. Each account gets its own folder in Google Drive later.',
      skipBeacon: true,
      before: () => goTo('/dashboard', TOUR_TARGETS.navAccounts),
    },
    {
      id: 'add-account',
      target: TOUR_TARGETS.addAccount,
      placement: 'bottom',
      title: 'Create an account',
      content:
        'Click Add Account to set up checking, savings, credit cards, and more. You can use manual entry until Drive is connected.',
      skipBeacon: true,
      before: () => goTo('/accounts', TOUR_TARGETS.addAccount),
    },
    {
      id: 'setup-statements',
      target: TOUR_TARGETS.setupStatementsTab,
      placement: 'bottom',
      title: 'Statement storage',
      content:
        'Richtato stores original statement files in your Google Drive. On desktop, open your profile menu → Setup. On mobile, go to More → Setup, then open the Statements tab.',
      skipBeacon: true,
      before: () =>
        goTo('/setup?tab=statements', TOUR_TARGETS.setupStatementsTab),
    },
    {
      id: 'drive-status',
      target: TOUR_TARGETS.driveStatus,
      placement: 'bottom',
      title: 'Google Drive status',
      content:
        'This card shows whether Drive is connected and active. When active, Richtato creates one subfolder per account using the pattern {account_id}-{name}.',
      skipBeacon: true,
      before: () => goTo('/setup?tab=statements', TOUR_TARGETS.driveStatus),
    },
    {
      id: 'drive-connect',
      target: () =>
        document.querySelector(TOUR_TARGETS.driveConnect) ??
        document.querySelector(TOUR_TARGETS.driveFolderActions) ??
        document.querySelector(TOUR_TARGETS.driveStatus),
      placement: 'top',
      title: 'Connect Google Drive',
      content:
        'Click Connect Google Drive when you are ready—you will sign in with Google and return here. The tour will pick up at the folder setup step.',
      skipBeacon: true,
      blockTargetInteraction: false,
      before: () => goTo('/setup?tab=statements', TOUR_TARGETS.driveStatus),
    },
    {
      id: 'drive-folder-actions',
      target: () =>
        document.querySelector(TOUR_TARGETS.driveFolderActions) ??
        document.querySelector(TOUR_TARGETS.driveStatus),
      placement: 'top',
      title: 'Choose a folder structure',
      content:
        'Create New Structure for a fresh root folder, or Use Existing Folders to link a Richtato-style layout you already have in Drive.',
      skipBeacon: true,
      before: () =>
        goTo('/setup?tab=statements', TOUR_TARGETS.driveFolderActions),
    },
    {
      id: 'finish',
      target: TOUR_TARGETS.driveStatus,
      placement: 'center',
      title: 'You are ready to go',
      content:
        'Once Drive is active, upload statements from each account’s Statements tab and review transactions on the Transactions page. You can replay this tour anytime from Settings.',
      skipBeacon: true,
      before: () => goTo('/setup?tab=statements', TOUR_TARGETS.driveStatus),
    },
  ];
}
