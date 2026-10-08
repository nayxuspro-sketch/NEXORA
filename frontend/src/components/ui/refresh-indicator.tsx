'use client';

import * as React from 'react';
import { useIsFetching, useQueryClient } from '@tanstack/react-query';
import { RefreshCw, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export function RefreshIndicator() {
  const queryClient = useQueryClient();
  const isFetching = useIsFetching();
  const [lastRefreshed, setLastRefreshed] = React.useState<Date>(new Date());
  const [timeAgo, setTimeAgo] = React.useState<string>('À l\'instant');

  // Met à jour l'heure de dernier rafraîchissement lorsque le fetch se termine
  const prevFetching = React.useRef(isFetching);
  React.useEffect(() => {
    if (prevFetching.current > 0 && isFetching === 0) {
      setLastRefreshed(new Date());
    }
    prevFetching.current = isFetching;
  }, [isFetching]);

  // Actualise le texte "il y a X min / à l'instant"
  React.useEffect(() => {
    const interval = setInterval(() => {
      const diffSec = Math.floor((Date.now() - lastRefreshed.getTime()) / 1000);
      if (diffSec < 15) {
        setTimeAgo("À l'instant");
      } else if (diffSec < 60) {
        setTimeAgo(`Il y a ${diffSec}s`);
      } else {
        const min = Math.floor(diffSec / 60);
        setTimeAgo(`Il y a ${min} min`);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [lastRefreshed]);

  const handleManualRefresh = () => {
    queryClient.invalidateQueries();
    setLastRefreshed(new Date());
  };

  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-border/60 bg-muted/30 text-[11px] text-muted-foreground transition-all">
      <button
        type="button"
        onClick={handleManualRefresh}
        title="Actualiser les données maintenant"
        className="flex items-center gap-1.5 hover:text-foreground transition-colors group cursor-pointer focus:outline-hidden"
      >
        <RefreshCw
          className={cn(
            'h-3.5 w-3.5 transition-transform group-hover:rotate-180 duration-500 text-muted-foreground',
            isFetching > 0 && 'animate-spin text-primary'
          )}
        />
        <span className="hidden sm:inline font-medium">
          {isFetching > 0 ? 'Synchronisation...' : timeAgo}
        </span>
      </button>
    </div>
  );
}
