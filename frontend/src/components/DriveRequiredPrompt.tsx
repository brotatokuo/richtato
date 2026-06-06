import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Cloud, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';

interface DriveRequiredPromptProps {
  title?: string;
  description?: string;
  variant?: 'inline' | 'card';
  className?: string;
}

export function DriveRequiredPrompt({
  title = 'Google Drive required',
  description = 'Connect and activate Google Drive in Setup → Statements to store and sync statement files.',
  variant = 'inline',
  className,
}: DriveRequiredPromptProps) {
  if (variant === 'card') {
    return (
      <div
        className={cn(
          'mx-auto flex max-w-lg flex-col items-center rounded-2xl border border-border bg-card px-6 py-10 text-center shadow-sm',
          className
        )}
      >
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
          <Cloud className="h-6 w-6" />
        </div>
        <h2 className="text-lg font-semibold text-foreground">{title}</h2>
        <p className="mt-2 text-sm text-muted-foreground">{description}</p>
        <Button asChild className="mt-6">
          <Link to="/setup?tab=statements">
            Set up Google Drive
            <ExternalLink className="ml-2 h-4 w-4" />
          </Link>
        </Button>
      </div>
    );
  }

  return (
    <div
      className={cn(
        'flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-300',
        className
      )}
    >
      <Cloud className="mt-0.5 h-4 w-4 shrink-0" />
      <p>
        {description}{' '}
        <Link
          to="/setup?tab=statements"
          className="font-medium underline underline-offset-2"
        >
          Setup → Statements
        </Link>
      </p>
    </div>
  );
}
