import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useHousehold } from '@/contexts/HouseholdContext';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';
import {
  BarChart3,
  Calculator,
  ChevronLeft,
  ChevronRight,
  Heart,
  Landmark,
  LogOut,
  Settings as SettingsIcon,
  SlidersHorizontal,
  Table,
  User,
  Wallet,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

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
  const { user, logout } = useAuth();
  const { isInHousehold } = useHousehold();

  const navigationItems: NavItem[] = useMemo(() => {
    const items: NavItem[] = [
      { name: 'Dashboard', href: '/dashboard', icon: BarChart3 },
      { name: 'Transactions', href: '/transactions', icon: Table },
      { name: 'Accounts', href: '/accounts', icon: Landmark },
      { name: 'Budget', href: '/budget', icon: Wallet },
    ];
    if (isInHousehold) {
      items.push({ name: 'Household', href: '/household', icon: Heart });
    }
    return items;
  }, [isInHousehold]);

  const pathOf = (href: string): string => href.split('?')[0] ?? href;

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // Logout failures are surfaced by auth state remaining unchanged.
    }
  };

  const initial = user
    ? user.first_name?.charAt(0) || user.username.charAt(0).toUpperCase()
    : 'U';

  return (
    <div
      className={cn(
        'group relative z-50 flex h-dvh flex-col border-r',
        isCollapsed ? 'w-16' : 'w-64',
        className
      )}
    >
      {/* Header */}
      <div
        className={cn(
          'relative flex h-16 items-center border-b border-border px-3',
          isCollapsed ? 'justify-center' : 'justify-between'
        )}
      >
        <Link
          to="/dashboard"
          className={cn(
            'flex min-w-0 items-center rounded-xl transition-colors hover:bg-muted/70',
            isCollapsed ? 'justify-center p-2' : 'gap-3 py-2 pl-2 pr-3'
          )}
          aria-label="Go to dashboard"
        >
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-border/60 bg-background shadow-sm">
            <img
              src="/richtato.png"
              alt="Richtato Logo"
              className="h-7 w-7 rounded-lg"
            />
          </div>
          {!isCollapsed && (
            <span className="truncate text-base font-semibold tracking-tight text-foreground">
              Richtato
            </span>
          )}
        </Link>
        {!hideCollapseToggle && (
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              'text-muted-foreground hover:bg-muted hover:text-foreground focus:outline-none focus:ring-0',
              isCollapsed
                ? 'absolute -right-3 top-1/2 h-6 w-6 -translate-y-1/2 rounded-full border border-border bg-background shadow-sm'
                : 'h-9 w-9'
            )}
            onClick={toggleSidebar}
            aria-label="Toggle sidebar"
          >
            {isCollapsed ? (
              <ChevronRight className="h-3.5 w-3.5 opacity-70" />
            ) : (
              <ChevronLeft className="h-4 w-4 opacity-70" />
            )}
          </Button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-3" role="navigation">
        {navigationItems.map(item => {
          const itemPath = pathOf(item.href);
          const isActive = location.pathname === itemPath;
          const Icon = item.icon;

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
              <Icon
                className={cn(
                  'h-5 w-5 shrink-0 transition-transform group-hover:scale-110',
                  isActive && 'text-white'
                )}
              />
              {!isCollapsed && (
                <span className="flex-1 flex items-center justify-between">
                  <span>{item.name}</span>
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-200/50 dark:border-slate-700/50 p-4">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className={cn(
                'flex w-full items-center gap-3 rounded-xl p-2 text-left transition-colors hover:bg-slate-100 dark:hover:bg-slate-800',
                isCollapsed && 'justify-center'
              )}
              aria-label="Open user menu"
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-500 text-xs font-medium text-white shadow-lg">
                {initial}
              </span>
              {!isCollapsed && (
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium text-slate-900 dark:text-white">
                    {user ? user.username : 'User'}
                  </span>
                  <span className="block text-xs text-slate-500 dark:text-slate-400">
                    Settings and account
                  </span>
                </span>
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            side={isCollapsed ? 'right' : 'top'}
            className="w-56"
          >
            <DropdownMenuLabel>
              {user ? user.username : 'Account'}
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link to="/profile" className="gap-2">
                <User className="h-4 w-4" />
                Profile
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/preferences" className="gap-2">
                <SettingsIcon className="h-4 w-4" />
                Preferences
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/setup" className="gap-2">
                <SlidersHorizontal className="h-4 w-4" />
                Setup
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/formulas" className="gap-2">
                <Calculator className="h-4 w-4" />
                Formulas
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={handleLogout}
              className="gap-2 text-destructive focus:text-destructive"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
