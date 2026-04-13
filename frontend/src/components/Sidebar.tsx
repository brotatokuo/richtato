import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useHousehold } from '@/contexts/HouseholdContext';
import { useAuth } from '@/hooks/useAuth';
import { useSyncStatus } from '@/hooks/useSyncStatus';
import { cn } from '@/lib/utils';
import {
  BarChart3,
  Calculator,
  ChevronLeft,
  ChevronRight,
  Heart,
  Landmark,
  Loader2,
  LogOut,
  Settings as SettingsIcon,
  SlidersHorizontal,
  Table,
  TrendingUp,
  Wallet,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

interface SidebarProps {
  className?: string;
  hideCollapseToggle?: boolean;
}

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

export function Sidebar({
  className,
  hideCollapseToggle = false,
}: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { status: syncStatus } = useSyncStatus();
  const { isInHousehold } = useHousehold();

  const navigationItems: NavItem[] = useMemo(() => {
    const items: NavItem[] = [
      { name: 'Report', href: '/report', icon: BarChart3 },
      { name: 'Accounts', href: '/accounts', icon: Landmark },
      { name: 'Budget', href: '/budget', icon: Wallet },
      { name: 'Cashflow', href: '/cashflow', icon: TrendingUp },
    ];
    if (isInHousehold) {
      items.push({ name: 'Household', href: '/household', icon: Heart });
    }
    items.push(
      { name: 'Data', href: '/data', icon: Table },
      { name: 'Setup', href: '/setup', icon: SlidersHorizontal },
      { name: 'Preferences', href: '/preferences', icon: SettingsIcon },
      { name: 'Formulas', href: '/formulas', icon: Calculator }
    );
    return items;
  }, [isInHousehold]);

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handleProfileClick = () => {
    navigate('/profile');
  };

  return (
    <div
      className={cn(
        'group relative z-50 flex h-dvh flex-col border-r',
        isCollapsed ? 'w-16' : 'w-64',
        className
      )}
    >
      {/* Header */}
      <div className="flex h-16 items-center justify-between border-b border-slate-200/50 dark:border-slate-700/50 px-4">
        <Link to="/report" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center">
            <img
              src="/richtato.png"
              alt="Richtato Logo"
              className="h-8 w-8 rounded-lg"
            />
          </div>
          {!isCollapsed && (
            <span className="text-lg font-bold text-slate-900 dark:text-white">
              Richtato
            </span>
          )}
        </Link>
        {!hideCollapseToggle && (
          <Button
            variant="ghost"
            size="icon"
            className="text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-transparent focus:ring-0 focus:outline-none"
            onClick={toggleSidebar}
            aria-label="Toggle sidebar"
          >
            {isCollapsed ? (
              <ChevronRight className="h-4 w-4 opacity-70" />
            ) : (
              <ChevronLeft className="h-4 w-4 opacity-70" />
            )}
          </Button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-3" role="navigation">
        {navigationItems.map(item => {
          const isActive = location.pathname === item.href;
          const Icon = item.icon;

          // Show sync indicator and badge on Data page
          const isDataPage = item.href === '/data';
          const isSyncing = isDataPage && syncStatus?.is_syncing;
          const newTransactionCount =
            isDataPage && syncStatus?.new_transaction_count
              ? syncStatus.new_transaction_count
              : 0;

          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition-all duration-200 group',
                isActive
                  ? 'bg-primary text-primary-foreground shadow-lg'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white',
                isCollapsed && 'justify-center px-2'
              )}
            >
              {isSyncing ? (
                <Loader2 className="h-5 w-5 shrink-0 animate-spin" />
              ) : (
                <Icon
                  className={cn(
                    'h-5 w-5 shrink-0 transition-transform group-hover:scale-110',
                    isActive && 'text-white'
                  )}
                />
              )}
              {!isCollapsed && (
                <span className="flex-1 flex items-center justify-between">
                  <span>{item.name}</span>
                  {newTransactionCount > 0 && (
                    <Badge
                      variant="default"
                      className="ml-2 bg-emerald-500 hover:bg-emerald-600 text-white text-xs px-1.5 py-0.5"
                    >
                      {newTransactionCount > 99 ? '99+' : newTransactionCount}
                    </Badge>
                  )}
                </span>
              )}
              {isCollapsed && newTransactionCount > 0 && (
                <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-emerald-500" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-200/50 dark:border-slate-700/50 p-4">
        <div className="flex items-center gap-3">
          <button
            onClick={handleProfileClick}
            className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-500 text-white text-xs font-medium shadow-lg hover:bg-slate-600 transition-colors cursor-pointer shrink-0"
            aria-label="Go to profile"
          >
            {user
              ? user.first_name?.charAt(0) ||
                user.username.charAt(0).toUpperCase()
              : 'U'}
          </button>
          {!isCollapsed && (
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-900 dark:text-white">
                {user ? user.username : 'User'}
              </p>
            </div>
          )}
        </div>
        {!isCollapsed && (
          <>
            <Button
              variant="ghost"
              size="sm"
              className="mt-2 w-full justify-start gap-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              aria-label="Logout"
              onClick={handleLogout}
            >
              <LogOut className="h-4 w-4" />
              Logout
            </Button>
            {/* Footer collapse toggle removed - now in header */}
          </>
        )}
        {/* Collapsed footer toggle removed - now in header */}
      </div>
    </div>
  );
}
