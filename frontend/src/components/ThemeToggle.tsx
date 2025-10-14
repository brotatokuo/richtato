import { Button } from '@/components/ui/button';
import { useTheme } from '@/contexts/useTheme';
import { cn } from '@/lib/utils';
import { Moon, Sun } from 'lucide-react';

interface ThemeToggleProps {
  className?: string;
  isCollapsed?: boolean;
}

export function ThemeToggle({
  className,
  isCollapsed = false,
}: ThemeToggleProps) {
  const { theme, setTheme } = useTheme();

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const getIcon = () => {
    return theme === 'light' ? (
      <Sun className="h-4 w-4" data-testid="sun-icon" />
    ) : (
      <Moon className="h-4 w-4" data-testid="moon-icon" />
    );
  };

  const getLabel = () => {
    return theme === 'light' ? 'Light' : 'Dark';
  };

  return (
    <Button
      variant="ghost"
      size={isCollapsed ? 'icon' : 'sm'}
      className={cn(
        'gap-2',
        isCollapsed ? 'h-8 w-8' : 'w-full justify-start',
        className
      )}
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
    >
      {getIcon()}
      {!isCollapsed && <span>{getLabel()}</span>}
    </Button>
  );
}
