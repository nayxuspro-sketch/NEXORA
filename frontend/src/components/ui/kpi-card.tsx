import * as React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface KpiCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
  description?: string;
}

export function KpiCard({ title, value, change, changeType = 'neutral', icon, description }: KpiCardProps) {
  const changeColors = {
    positive: 'text-emerald-600 bg-emerald-500/10 border-emerald-500/20',
    negative: 'text-rose-600 bg-rose-500/10 border-rose-500/20',
    neutral: 'text-muted-foreground bg-muted border-border',
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-6">
        <div className="flex items-center justify-between space-y-0 pb-2">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <div className="h-10 w-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
            {icon}
          </div>
        </div>
        <div className="mt-2 flex items-baseline justify-between">
          <h2 className="text-2xl font-bold tracking-tight text-foreground">{value}</h2>
          {change && (
            <span
              className={cn(
                'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border',
                changeColors[changeType]
              )}
            >
              {change}
            </span>
          )}
        </div>
        {description && <p className="mt-1 text-xs text-muted-foreground">{description}</p>}
      </CardContent>
    </Card>
  );
}
