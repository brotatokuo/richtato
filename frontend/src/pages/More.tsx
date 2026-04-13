import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';
import {
  ChevronRight,
  LogOut,
  Settings as SettingsIcon,
  SlidersHorizontal,
  TrendingUp,
  User,
} from 'lucide-react';
import { Link } from 'react-router-dom';

interface MenuRowProps {
  href?: string;
  onClick?: () => void;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  destructive?: boolean;
}

function MenuRow({
  href,
  onClick,
  icon: Icon,
  label,
  destructive,
}: MenuRowProps) {
  const className = cn(
    'flex items-center gap-3 px-4 py-3.5 text-sm font-medium transition-colors active:bg-muted',
    destructive ? 'text-destructive' : 'text-foreground hover:bg-muted/50'
  );

  const inner = (
    <>
      <Icon
        className={cn(
          'h-5 w-5 shrink-0',
          destructive ? 'text-destructive' : 'text-muted-foreground'
        )}
      />
      <span className="flex-1">{label}</span>
      {!destructive && (
        <ChevronRight className="h-4 w-4 text-muted-foreground/50" />
      )}
    </>
  );

  if (onClick) {
    return (
      <button className={cn(className, 'w-full text-left')} onClick={onClick}>
        {inner}
      </button>
    );
  }

  return (
    <Link to={href!} className={className}>
      {inner}
    </Link>
  );
}

interface SectionProps {
  title: string;
  children: React.ReactNode;
}

function Section({ title, children }: SectionProps) {
  return (
    <div className="mb-6">
      <p className="px-4 pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        {title}
      </p>
      <div className="divide-y divide-border rounded-xl border border-border overflow-hidden bg-card mx-4">
        {children}
      </div>
    </div>
  );
}

export function More() {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // ignore
    }
  };

  const initial = user
    ? user.first_name?.charAt(0) || user.username.charAt(0).toUpperCase()
    : 'U';

  return (
    <div className="pb-4">
      {/* Profile row */}
      <Link
        to="/profile"
        className="flex items-center gap-3 px-4 py-4 mb-6 transition-colors hover:bg-muted/50 active:bg-muted"
      >
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-slate-500 text-white text-sm font-semibold shrink-0 shadow">
          {initial}
        </div>
        <div className="flex-1">
          <p className="text-sm font-semibold text-foreground">
            {user ? user.username : 'User'}
          </p>
          <p className="text-xs text-muted-foreground">View profile</p>
        </div>
        <ChevronRight className="h-4 w-4 text-muted-foreground/50" />
      </Link>

      <Section title="Navigation">
        <MenuRow href="/cashflow" icon={TrendingUp} label="Cashflow" />
      </Section>

      <Section title="Settings">
        <MenuRow href="/setup" icon={SlidersHorizontal} label="Setup" />
        <MenuRow href="/preferences" icon={SettingsIcon} label="Preferences" />
      </Section>

      <Section title="Account">
        <MenuRow href="/profile" icon={User} label="Profile" />
        <MenuRow
          onClick={handleLogout}
          icon={LogOut}
          label="Logout"
          destructive
        />
      </Section>
    </div>
  );
}
