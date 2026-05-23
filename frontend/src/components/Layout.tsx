import {
  HeaderSlotProvider,
  useHeaderSlot,
} from '@/contexts/HeaderSlotContext';
import {
  BarChart3,
  Calculator,
  Heart,
  Landmark,
  MoreHorizontal,
  Settings,
  SlidersHorizontal,
  Table,
  Wallet,
} from 'lucide-react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { BottomTabBar } from './BottomTabBar';
import { Sidebar } from './Sidebar';

// Route to page title and icon mapping
const routeConfig: Record<
  string,
  { title: string; icon: React.ComponentType<{ className?: string }> }
> = {
  '/accounts': { title: 'Accounts', icon: Landmark },
  '/budget': { title: 'Budget', icon: Wallet },
  '/transactions': { title: 'Transactions', icon: Table },
  '/dashboard': { title: 'Dashboard', icon: BarChart3 },
  '/preferences': { title: 'Preferences', icon: Settings },
  '/setup': { title: 'Setup', icon: SlidersHorizontal },
  '/settings': { title: 'Settings', icon: Settings },
  '/more': { title: 'More', icon: MoreHorizontal },
  '/household': { title: 'Household', icon: Heart },
  '/formulas': { title: 'Formulas', icon: Calculator },
};

export function Layout() {
  return (
    <HeaderSlotProvider>
      <LayoutInner />
    </HeaderSlotProvider>
  );
}

function LayoutInner() {
  const location = useLocation();
  const { headerSlot } = useHeaderSlot();

  // Get the current page config based on the route (supports nested paths)
  const matchedKey = Object.keys(routeConfig).find(
    key => location.pathname === key || location.pathname.startsWith(`${key}/`)
  );
  const currentPageConfig = matchedKey
    ? routeConfig[matchedKey]
    : { title: 'Dashboard', icon: Landmark };
  const IconComponent = currentPageConfig.icon;

  return (
    <div className="flex h-screen bg-background">
      <Sidebar className="hidden md:flex" />
      <div className="flex-1 flex flex-col isolate min-w-0">
        {/* Header */}
        <header className="sticky top-0 z-40 h-16 border-b border-border bg-background/90 backdrop-blur supports-[backdrop-filter]:bg-background/70">
          <div className="flex h-full items-center px-4 md:px-6">
            <div className="flex min-w-0 flex-1 items-center gap-3">
              {/* Mobile: app logo in header */}
              <Link
                to="/dashboard"
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-border/60 bg-card shadow-sm md:hidden"
                aria-label="Go to dashboard"
              >
                <img
                  src="/richtato.png"
                  alt="Richtato"
                  className="h-6 w-6 rounded"
                />
              </Link>
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-muted text-muted-foreground">
                <IconComponent className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <h1 className="truncate text-xl font-semibold tracking-tight text-foreground">
                  {currentPageConfig.title}
                </h1>
              </div>
            </div>
            <div className="ml-auto flex shrink-0 items-center gap-2">
              {headerSlot && (
                <div className="hidden items-center md:flex">{headerSlot}</div>
              )}
            </div>
          </div>
        </header>

        {/* Main Content — extra bottom padding on mobile for the tab bar */}
        <main className="flex-1 overflow-auto scrollbar-thin min-w-0">
          <div className="w-full max-w-full p-4 md:p-6 pb-20 md:pb-6 overflow-x-hidden">
            <Outlet />
          </div>
        </main>
      </div>

      <BottomTabBar />
    </div>
  );
}
