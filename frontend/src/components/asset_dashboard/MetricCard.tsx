import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingDown, TrendingUp } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  trend?: {
    value: number;
    label: string;
  };
  icon?: React.ReactNode;
}

export function MetricCard({
  title,
  value,
  subtitle,
  trend,
  icon,
}: MetricCardProps) {
  const isPositiveTrend = trend && trend.value > 0;
  const isNegativeTrend = trend && trend.value < 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-foreground">{value}</div>
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
        )}
        {trend && (
          <div className="flex items-center mt-2">
            {isPositiveTrend ? (
              <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
            ) : isNegativeTrend ? (
              <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
            ) : null}
            <span
              className={`text-xs font-medium ${
                isPositiveTrend
                  ? 'text-green-500'
                  : isNegativeTrend
                    ? 'text-red-500'
                    : 'text-muted-foreground'
              }`}
            >
              {trend.value > 0 ? '+' : ''}
              {trend.value}% {trend.label}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
