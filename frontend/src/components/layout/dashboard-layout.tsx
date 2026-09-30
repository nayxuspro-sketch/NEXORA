'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { Sidebar } from './sidebar';
import { Topbar } from './topbar';
import { QuickSearchModal } from './quick-search';

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, token, isLoading } = useAuth();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const [searchOpen, setSearchOpen] = React.useState(false);

  React.useEffect(() => {
    // Si le chargement est terminé et qu'aucun utilisateur n'est authentifié,
    // redirection stricte et immédiate vers /login
    if (!isLoading && (!user || !token)) {
      router.replace('/login');
    }
  }, [isLoading, user, token, router]);

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Pendant la vérification initiale de l'authentification obligatoire, afficher un écran neutre
  if (isLoading || !user || !token) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-primary flex items-center justify-center text-white font-black text-lg animate-pulse">
            N
          </div>
          <span className="text-xs font-semibold text-slate-400">
            Vérification de la session sécurisée...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="lg:pl-72 flex flex-col min-h-screen">
        <Topbar
          onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
          onOpenQuickSearch={() => setSearchOpen(true)}
        />
        <main className="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto">{children}</main>
      </div>

      <QuickSearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </div>
  );
}
