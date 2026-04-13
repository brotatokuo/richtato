import { useHousehold, Scope } from '@/contexts/HouseholdContext';
import { cn } from '@/lib/utils';
import { User, Users } from 'lucide-react';

interface ScopeToggleProps {
  className?: string;
}

export function ScopeToggle({ className }: ScopeToggleProps) {
  const { isInHousehold, scope, setScope } = useHousehold();

  if (!isInHousehold) return null;

  const options: {
    value: Scope;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
  }[] = [
    { value: 'personal', label: 'Personal', icon: User },
    { value: 'household', label: 'Household', icon: Users },
  ];

  return (
    <div
      className={cn(
        'inline-flex items-center rounded-lg bg-muted p-1 gap-1',
        className
      )}
    >
      {options.map(opt => {
        const Icon = opt.icon;
        const isActive = scope === opt.value;
        return (
          <button
            key={opt.value}
            onClick={() => setScope(opt.value)}
            className={cn(
              'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              isActive
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            <Icon className="h-3.5 w-3.5" />
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
