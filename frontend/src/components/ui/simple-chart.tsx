import * as React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

interface DataPoint {
  label: string;
  value: number;
}

interface BarChartProps {
  title: string;
  data: DataPoint[];
  height?: number;
}

export function SimpleBarChart({ title, data, height = 180 }: BarChartProps) {
  const maxValue = Math.max(...data.map((d) => d.value), 1);

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-end justify-between gap-2 pt-4" style={{ height: `${height}px` }}>
          {data.map((d, i) => {
            const heightPercent = Math.round((d.value / maxValue) * 100);
            return (
              <div key={i} className="flex-1 flex flex-col items-center gap-2 h-full justify-end group">
                <span className="text-[10px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity font-semibold">
                  {d.value}
                </span>
                <div
                  className="w-full bg-primary/80 group-hover:bg-primary transition-all rounded-t-md"
                  style={{ height: `${Math.max(heightPercent, 4)}%` }}
                />
                <span className="text-xs text-muted-foreground truncate max-w-[50px] text-center font-medium">
                  {d.label}
                </span>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
