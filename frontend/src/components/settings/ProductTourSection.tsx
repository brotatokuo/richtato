import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { usePlatformTour } from '@/contexts/PlatformTourContext';
import { Compass } from 'lucide-react';

export function ProductTourSection() {
  const { startTour, isRunning } = usePlatformTour();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Compass className="h-4 w-4" />
          Product tour
        </CardTitle>
        <CardDescription>
          Walk through accounts, Google Drive statement setup, and the core
          Richtato workflow.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button
          type="button"
          variant="outline"
          disabled={isRunning}
          onClick={() => startTour(0)}
        >
          {isRunning ? 'Tour in progress…' : 'Replay tour'}
        </Button>
      </CardContent>
    </Card>
  );
}
