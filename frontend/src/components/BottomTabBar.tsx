import { Badge } from '@/components/ui/badge';
import { useSyncStatus } from '@/hooks/useSyncStatus';
import { cn } from '@/lib/utils';
import {
  BarChart3,
  Landmark,
  MoreHorizontal,
  Table,
  Wallet,
} from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

const primaryTabs = [
  { name: 'Report', href: '/report', icon: BarChart3 },
  { name: 'Accounts', href: '/accounts', icon: Landmark },
  { name: 'Budget', href: '/budget', icon: Wallet },
  { name: 'Data', href: '/data', icon: Table },
  { name: 'More', href: '/more', icon: MoreHorizontal },
];

const moreRoutes = ['/cashflow', '/setup', '/preferences', '/profile', '/more'];

export function BottomTabBar() {
  const location = useLocation();
  const { status: syncStatus } = useSyncStatus();

  const newTransactionCount = syncStatus?.new_transaction_count ?? 0;

  const isMoreActive = moreRoutes.some(r => location.pathname.startsWith(r));

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-background border-t border-border"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="flex items-stretch h-16 pb-safe">
        {primaryTabs.map(tab => {
          const Icon = tab.icon;
          const isMore = tab.href === '/more';
          const isActive = isMore
            ? isMoreActive
            : location.pathname === tab.href ||
              location.pathname.startsWith(`${tab.href}/`);
          const isData = tab.href === '/data';
          const isSyncing = isData && syncStatus?.is_syncing;

          return (
            <Link
              key={tab.name}
              to={tab.href}
              className={cn(
                'relative flex flex-1 flex-col items-center justify-center gap-1 text-xs font-medium transition-colors',
                isActive
                  ? 'text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              )}
              aria-current={isActive ? 'page' : undefined}
            >
              <div className="relative">
                <Icon className={cn('h-5 w-5', isSyncing && 'animate-spin')} />
                {isData && newTransactionCount > 0 && (
                  <Badge
                    variant="default"
                    className="absolute -top-2 -right-3 min-w-[1.1rem] h-[1.1rem] px-1 py-0 text-[10px] leading-none flex items-center justify-center bg-emerald-500 hover:bg-emerald-500 text-white"
                  >
                    {newTransactionCount > 99 ? '99+' : newTransactionCount}
                  </Badge>
                )}
              </div>
              <span>{tab.name}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
