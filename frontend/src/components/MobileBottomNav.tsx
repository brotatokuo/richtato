import { Badge } from '@/components/ui/badge';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { useAuth } from '@/hooks/useAuth';
import { useSyncStatus } from '@/hooks/useSyncStatus';
import { cn } from '@/lib/utils';
import {
  BarChart3,
  Loader2,
  LogOut,
  MoreHorizontal,
  PieChart,
  Settings as SettingsIcon,
  SlidersHorizontal,
  Table,
  User,
  Wallet,
} from 'lucide-react';
import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

const primaryTabs = [
  { name: 'Dashboard', href: '/report', icon: BarChart3 },
  { name: 'Budget', href: '/budget', icon: Wallet },
  { name: 'Accounts', href: '/accounts', icon: PieChart },
];

const secondaryItems = [
  { name: 'Transactions', href: '/transactions', icon: Table },
  { name: 'Setup', href: '/setup', icon: SlidersHorizontal },
  { name: 'Preferences', href: '/preferences', icon: SettingsIcon },
  { name: 'Profile', href: '/profile', icon: User },
];

export function MobileBottomNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { status: syncStatus } = useSyncStatus();
  const [moreOpen, setMoreOpen] = useState(false);

  const newTransactionCount = syncStatus?.new_transaction_count ?? 0;
  const isSyncing = syncStatus?.is_syncing ?? false;

  const isSecondaryActive = secondaryItems.some(
    item =>
      location.pathname === item.href ||
      location.pathname.startsWith(`${item.href}/`)
  );

  const handleLogout = async () => {
    setMoreOpen(false);
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <nav
      className="fixed bottom-0 inset-x-0 z-50 border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 md:hidden"
      style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
      role="navigation"
      aria-label="Mobile navigation"
    >
      <div className="flex items-center justify-around h-16">
        {primaryTabs.map(tab => {
          const isActive =
            location.pathname === tab.href ||
            location.pathname.startsWith(`${tab.href}/`);
          const Icon = tab.icon;

          return (
            <Link
              key={tab.name}
              to={tab.href}
              className={cn(
                'flex flex-col items-center justify-center gap-0.5 flex-1 h-full text-[10px] font-medium transition-colors',
                isActive
                  ? 'text-primary'
                  : 'text-muted-foreground active:text-foreground'
              )}
            >
              <Icon className="h-5 w-5" />
              <span>{tab.name}</span>
            </Link>
          );
        })}

        <Popover open={moreOpen} onOpenChange={setMoreOpen}>
          <PopoverTrigger asChild>
            <button
              className={cn(
                'relative flex flex-col items-center justify-center gap-0.5 flex-1 h-full text-[10px] font-medium transition-colors',
                isSecondaryActive
                  ? 'text-primary'
                  : 'text-muted-foreground active:text-foreground'
              )}
            >
              <MoreHorizontal className="h-5 w-5" />
              <span>More</span>
              {(newTransactionCount > 0 || isSyncing) && (
                <span className="absolute top-2 right-1/4 h-2 w-2 rounded-full bg-emerald-500" />
              )}
            </button>
          </PopoverTrigger>
          <PopoverContent
            side="top"
            align="end"
            sideOffset={8}
            className="w-56 p-2"
          >
            <div className="space-y-1">
              {secondaryItems.map(item => {
                const isActive =
                  location.pathname === item.href ||
                  location.pathname.startsWith(`${item.href}/`);
                const Icon = item.icon;
                const isDataPage = item.href === '/transactions';

                return (
                  <button
                    key={item.name}
                    onClick={() => {
                      setMoreOpen(false);
                      navigate(item.href);
                    }}
                    className={cn(
                      'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-foreground hover:bg-muted'
                    )}
                  >
                    {isDataPage && isSyncing ? (
                      <Loader2 className="h-4 w-4 shrink-0 animate-spin" />
                    ) : (
                      <Icon className="h-4 w-4 shrink-0" />
                    )}
                    <span className="flex-1 text-left">{item.name}</span>
                    {isDataPage && newTransactionCount > 0 && (
                      <Badge
                        variant="default"
                        className="bg-emerald-500 hover:bg-emerald-600 text-white text-xs px-1.5 py-0"
                      >
                        {newTransactionCount > 99 ? '99+' : newTransactionCount}
                      </Badge>
                    )}
                  </button>
                );
              })}

              <div className="my-1 border-t border-border" />

              <div className="px-3 py-2 flex items-center gap-3">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-500 text-white text-[10px] font-medium shrink-0">
                  {user
                    ? user.first_name?.charAt(0) ||
                      user.username.charAt(0).toUpperCase()
                    : 'U'}
                </div>
                <span className="text-sm text-muted-foreground truncate">
                  {user ? user.username : 'User'}
                </span>
              </div>

              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-destructive hover:bg-destructive/10 transition-colors"
              >
                <LogOut className="h-4 w-4 shrink-0" />
                Logout
              </button>
            </div>
          </PopoverContent>
        </Popover>
      </div>
    </nav>
  );
}
