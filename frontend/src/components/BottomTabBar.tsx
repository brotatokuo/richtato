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
  { name: 'Dashboard', href: '/dashboard', icon: BarChart3 },
  { name: 'Accounts', href: '/accounts', icon: Landmark },
  { name: 'Budget', href: '/budget', icon: Wallet },
  { name: 'Transactions', href: '/transactions', icon: Table },
  { name: 'More', href: '/more', icon: MoreHorizontal },
];

const moreRoutes = [
  '/household',
  '/setup',
  '/preferences',
  '/formulas',
  '/more',
];

export function BottomTabBar() {
  const location = useLocation();

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
              <Icon className="h-5 w-5" />
              <span>{tab.name}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
