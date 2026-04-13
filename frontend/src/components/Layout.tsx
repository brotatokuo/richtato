import {
  HeaderSlotProvider,
  useHeaderSlot,
} from '@/contexts/HeaderSlotContext';
import { useSyncStatus } from '@/hooks/useSyncStatus';
import {
  BarChart3,
  Calculator,
  CloudUpload,
  Heart,
  Landmark,
  MoreHorizontal,
  Settings,
  SlidersHorizontal,
  Table,
  Wallet,
} from 'lucide-react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { toast } from 'sonner';
import { BottomTabBar } from './BottomTabBar';
import { ScopeToggle } from './household/ScopeToggle';
import { Sidebar } from './Sidebar';

// Route to page title and icon mapping
const routeConfig: Record<
  string,
  { title: string; icon: React.ComponentType<{ className?: string }> }
> = {
  '/accounts': { title: 'Accounts', icon: Landmark },
  '/budget': { title: 'Budget', icon: Wallet },
  '/transactions': { title: 'Transactions', icon: Table },
  '/report': { title: 'Dashboard', icon: BarChart3 },
  '/upload': { title: 'Upload', icon: CloudUpload },
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

  // Global sync status monitoring for toast notifications
  useSyncStatus({
    onSyncComplete: newCount => {
      if (newCount > 0) {
        toast.success('Sync complete', {
          description: `${newCount} new transaction${newCount === 1 ? '' : 's'} synced`,
        });
      } else {
        toast.success('Sync complete', {
          description: 'All accounts are up to date',
        });
      }
    },
    onSyncError: error => {
      toast.error('Sync failed', {
        description: error || 'An error occurred during sync',
      });
    },
  });

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
        <header className="sticky top-0 z-40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
          <div className="mx-auto px-4 md:px-6 py-4">
            <div className="flex items-center gap-3">
              {/* Mobile: app logo in header */}
              <Link to="/report">
                <img
                  src="/richtato.png"
                  alt="Richtato"
                  className="h-7 w-7 rounded md:hidden"
                />
              </Link>
              <div className="flex items-center gap-2 flex-1">
                <IconComponent className="h-5 w-5 md:h-6 md:w-6 text-foreground" />
                <h1 className="text-lg md:text-2xl font-semibold text-foreground">
                  {currentPageConfig.title}
                </h1>
              </div>
              {headerSlot && (
                <div className="hidden md:flex items-center">{headerSlot}</div>
              )}
              <ScopeToggle className="hidden md:inline-flex" />
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
