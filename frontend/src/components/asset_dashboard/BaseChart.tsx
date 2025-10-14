import * as echarts from 'echarts';
import { useEffect, useRef } from 'react';

interface BaseChartProps {
  type: 'line' | 'bar' | 'doughnut' | 'pie';
  data: any;
  options: any;
  height?: string | number;
  width?: string | number;
}

export function BaseChart({
  type,
  data,
  options,
  height = '400px',
  width = '100%',
}: BaseChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (chartRef.current) {
      // Destroy existing chart if it exists
      if (chartInstanceRef.current) {
        chartInstanceRef.current.dispose();
      }

      // Create new chart instance
      chartInstanceRef.current = echarts.init(chartRef.current);

      // Set chart option with default styling
      const defaultOptions = {
        ...options,
        series: data.series || data,
        // Always hide grid for all chart types
        grid: {
          show: false, // Hide exterior border for all charts
          ...options.grid,
        },
        // Only apply axis styling for non-pie charts
        ...(type !== 'pie' && type !== 'doughnut'
          ? {
              xAxis: {
                axisLine: {
                  lineStyle: {
                    color: '#6b7280', // Darker axis line
                  },
                },
                axisTick: {
                  lineStyle: {
                    color: '#6b7280', // Darker tick lines
                  },
                },
                splitLine: {
                  show: false, // Hide vertical grid lines
                },
                ...options.xAxis,
              },
              yAxis: {
                axisLine: {
                  lineStyle: {
                    color: '#6b7280', // Darker axis line
                  },
                },
                axisTick: {
                  lineStyle: {
                    color: '#6b7280', // Darker tick lines
                  },
                },
                splitLine: {
                  show: true,
                  lineStyle: {
                    color: '#374151', // Darker horizontal grid lines
                    type: 'solid',
                    width: 1,
                  },
                },
                ...options.yAxis,
              },
            }
          : {}),
      };

      chartInstanceRef.current.setOption(defaultOptions);

      // Handle window resize
      const handleResize = () => {
        if (chartInstanceRef.current) {
          chartInstanceRef.current.resize();
        }
      };

      window.addEventListener('resize', handleResize);

      // Cleanup function
      return () => {
        window.removeEventListener('resize', handleResize);
        if (chartInstanceRef.current) {
          chartInstanceRef.current.dispose();
          chartInstanceRef.current = null;
        }
      };
    }
  }, [type, data, options]);

  return (
    <div
      ref={chartRef}
      style={{
        height: typeof height === 'number' ? `${height}px` : height,
        width: typeof width === 'number' ? `${width}px` : width,
      }}
    />
  );
}
