import { ThemeToggle } from '@/components/ThemeToggle';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';
import {
  ChevronLeft,
  ChevronRight,
  CloudUpload,
  FileText,
  Home,
  LogOut,
  Settings,
  Table,
  TrendingUp,
  User,
} from 'lucide-react';
import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

interface SidebarProps {
  className?: string;
}

const navigationItems = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: Home,
  },
  {
    name: 'Data',
    href: '/data',
    icon: Table,
  },
  {
    name: 'Cashflow',
    href: '/cashflow',
    icon: TrendingUp,
  },
  {
    name: 'Upload',
    href: '/upload',
    icon: CloudUpload,
  },
  {
    name: 'Profile',
    href: '/profile',
    icon: User,
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
  },
  {
    name: 'File Management',
    href: '/file-management',
    icon: FileText,
  },
];

export function Sidebar({ className }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();
  const { user, logout } = useAuth();

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

  return (
    <div
      className={cn(
        'group relative flex h-screen flex-col border-r',
        isCollapsed ? 'w-16' : 'w-64',
        className
      )}
    >
      {/* Header */}
      <div className="flex h-16 items-center border-b border-slate-200/50 dark:border-slate-700/50 px-4">
        <div className="flex items-center gap-3">
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
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-3" role="navigation">
        {navigationItems.map(item => {
          const isActive = location.pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition-all duration-200 group',
                isActive
                  ? 'bg-blue-600 text-white shadow-lg'
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
              {!isCollapsed && <span>{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-200/50 dark:border-slate-700/50 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-500 text-white text-sm font-medium shadow-lg">
            {user
              ? user.first_name?.charAt(0) ||
                user.username.charAt(0).toUpperCase()
              : 'U'}
          </div>
          {!isCollapsed && (
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-900 dark:text-white">
                {user
                  ? `${user.first_name} ${user.last_name}`.trim() ||
                    user.username
                  : 'User'}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Logged in as
              </p>
            </div>
          )}
        </div>
        {!isCollapsed && (
          <>
            <ThemeToggle className="mt-3 w-full" isCollapsed={false} />
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
            <Button
              variant="ghost"
              size="sm"
              className="mt-2 w-full justify-start gap-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              onClick={toggleSidebar}
              aria-label="Toggle sidebar"
            >
              {isCollapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
              {isCollapsed ? 'Expand' : 'Collapse'}
            </Button>
          </>
        )}
        {isCollapsed && (
          <div className="mt-3 flex flex-col items-center gap-2">
            <ThemeToggle isCollapsed={true} />
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              onClick={toggleSidebar}
              aria-label="Toggle sidebar"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
