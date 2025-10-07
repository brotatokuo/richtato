import { BaseChart } from '@/components/asset_dashboard/BaseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Info } from 'lucide-react';
import { ReactNode } from 'react';

interface PieWithDetailedLegendProps {
  title: string;
  chartData: any;
  chartOptions: any;
  centerPrimary: string | number;
  centerSecondaryLabel?: string;
  centerTertiaryLabel?: string;
  legend: ReactNode;
  height?: string | number;
  chartKey?: number;
  info?: ReactNode;
}

export function PieWithDetailedLegend({
  title,
  chartData,
  chartOptions,
  centerPrimary,
  centerSecondaryLabel,
  centerTertiaryLabel,
  legend,
  height = '20rem',
  chartKey,
  info,
}: PieWithDetailedLegendProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-2">
          <CardTitle>{title}</CardTitle>
          {info && (
            <Dialog>
              <DialogTrigger asChild>
                <button
                  type="button"
                  aria-label={`How ${title} is calculated`}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                >
                  <Info className="h-4 w-4" />
                </button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>{title} calculation</DialogTitle>
                  <DialogDescription>{info}</DialogDescription>
                </DialogHeader>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </CardHeader>
      <CardContent className="overflow-y-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="relative h-80 flex items-center justify-center">
            <div className="w-full h-full">
              <BaseChart
                key={chartKey}
                type="pie"
                data={chartData}
                options={chartOptions}
                height="100%"
              />
            </div>
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center flex flex-col items-center justify-center">
                <div className="text-3xl font-bold text-foreground leading-none">
                  {centerPrimary}
                </div>
                {centerSecondaryLabel ? (
                  <div className="text-sm text-muted-foreground mt-1">
                    {centerSecondaryLabel}
                  </div>
                ) : null}
                {centerTertiaryLabel ? (
                  <div className="text-xs text-muted-foreground/70 mt-1">
                    {centerTertiaryLabel}
                  </div>
                ) : null}
              </div>
            </div>
          </div>

          {legend}
        </div>
      </CardContent>
    </Card>
  );
}
