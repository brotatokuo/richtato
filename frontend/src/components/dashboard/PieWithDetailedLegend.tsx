import { BaseChart } from '@/components/dashboard/BaseChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
}: PieWithDetailedLegendProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
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
