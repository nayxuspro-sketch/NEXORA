'use client';

import * as React from 'react';
import {
  Menu,
  Search,
  Bell,
  Command,
  HelpCircle,
  FileText,
  Download,
  BookOpen,
  Wifi,
  ChevronDown
} from 'lucide-react';

interface TopbarProps {
  onToggleSidebar: () => void;
  onOpenQuickSearch: () => void;
}

export function Topbar({ onToggleSidebar, onOpenQuickSearch }: TopbarProps) {
  const [docMenuOpen, setDocMenuOpen] = React.useState(false);

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-4 md:px-8 border-b border-border/80 bg-card/95 backdrop-blur-md transition-all">
      {/* Côté gauche : Toggle mobile + Recherche rapide globale */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-lg text-muted-foreground hover:bg-muted/80 focus:outline-hidden focus:ring-2 focus:ring-primary lg:hidden transition-colors"
          aria-label="Ouvrir le menu de navigation"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Barre de recherche avec déclencheur Cmd/Ctrl+K */}
        <button
          onClick={onOpenQuickSearch}
          className="hidden md:flex items-center justify-between w-72 lg:w-96 px-3.5 py-2 text-xs text-muted-foreground bg-muted/40 border border-input/80 rounded-lg hover:border-primary/50 hover:bg-muted/70 transition-all text-left shadow-2xs group"
          aria-label="Recherche rapide"
        >
          <div className="flex items-center gap-2.5">
            <Search className="h-4 w-4 text-muted-foreground/70 group-hover:text-primary transition-colors" />
            <span className="truncate">Rechercher article, vente, client...</span>
          </div>
          <kbd className="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-semibold bg-background border border-border/80 rounded-md text-muted-foreground shadow-2xs">
            <Command className="h-3 w-3" /> K
          </kbd>
        </button>
      </div>

      {/* Côté droit : Statut réseau + Menu d'aide unifié + Notifications */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Badge réseau discret */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200/60">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>En ligne</span>
        </div>

        {/* Menu Documentations & Guides (Évite la saturation visuelle) */}
        <div className="relative">
          <button
            onClick={() => setDocMenuOpen(!docMenuOpen)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 hover:text-slate-900 bg-muted/60 hover:bg-muted border border-border/60 transition-all"
            aria-expanded={docMenuOpen}
          >
            <HelpCircle className="h-3.5 w-3.5 text-primary" />
            <span className="hidden md:inline">Guides & Manuels</span>
            <ChevronDown className="h-3 w-3 text-muted-foreground" />
          </button>

          {docMenuOpen && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setDocMenuOpen(false)}
              />
              <div className="absolute right-0 mt-2 w-64 bg-card border border-border/80 rounded-xl shadow-xl z-50 p-1.5 text-xs animate-scale-in">
                <div className="px-3 py-2 border-b border-border/60">
                  <p className="font-semibold text-foreground">Documentation Officielle</p>
                  <p className="text-[11px] text-muted-foreground">Téléchargement et consultation</p>
                </div>

                <a
                  href="/GUIDE_UTILISATEUR.pdf"
                  download="NEXORA_Guide_Utilisateur.pdf"
                  onClick={() => setDocMenuOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-foreground hover:bg-muted/80 transition-colors"
                >
                  <Download className="h-4 w-4 text-primary shrink-0" />
                  <div>
                    <p className="font-medium">Guide Utilisateur (PDF)</p>
                    <p className="text-[10px] text-muted-foreground">Caisse, ventes, stocks et raccourcis</p>
                  </div>
                </a>

                <a
                  href="/GUIDE_DEPLOIEMENT.html"
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => setDocMenuOpen(false)}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-foreground hover:bg-muted/80 transition-colors"
                >
                  <BookOpen className="h-4 w-4 text-slate-600 shrink-0" />
                  <div>
                    <p className="font-medium">Guide de Déploiement</p>
                    <p className="text-[10px] text-muted-foreground">Installation réseau & production</p>
                  </div>
                </a>
              </div>
            </>
          )}
        </div>

        {/* Bouton recherche mobile */}
        <button
          onClick={onOpenQuickSearch}
          className="md:hidden p-2 rounded-lg text-muted-foreground hover:bg-muted"
          aria-label="Recherche"
        >
          <Search className="h-5 w-5" />
        </button>

        {/* Notifications discrètes */}
        <button
          title="Notifications"
          className="relative p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-primary" />
        </button>
      </div>
    </header>
  );
}
