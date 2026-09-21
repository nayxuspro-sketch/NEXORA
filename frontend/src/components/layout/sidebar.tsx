import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  ShoppingCart,
  Package,
  Layers,
  Users,
  Building2,
  FileText,
  Bell,
  ShieldCheck,
  Menu,
  X,
  CreditCard,
  LogOut,
  ChevronDown
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/lib/auth';
import { Badge } from '@/components/ui/badge';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const navigation = [
    { name: 'Tableau de bord', href: '/', icon: LayoutDashboard },
    { name: 'Caisse & Vente (POS)', href: '/pos', icon: ShoppingCart, badge: 'Direct' },
    { name: 'Ventes & Commandes', href: '/sales', icon: FileText },
    { name: 'Catalogue & Produits', href: '/products', icon: Package },
    { name: 'Stocks & Inventaires', href: '/inventory', icon: Layers },
    { name: 'Clients & Fournisseurs', href: '/partners', icon: Users },
    { name: 'Rapports & BI', href: '/reports', icon: CreditCard },
    { name: 'Assistant IA', href: '/ai', icon: Bell, badge: 'Copilot' },
    { name: 'Automatisation', href: '/automation', icon: ShieldCheck },
    { name: 'Audit & Sécurité', href: '/audit', icon: ShieldCheck },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={cn(
          'fixed top-0 bottom-0 left-0 z-50 flex flex-col w-72 bg-card border-r border-border transition-transform duration-200 ease-in-out lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Brand header */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-primary text-primary-foreground flex items-center justify-center font-black tracking-wider text-lg shadow-md">
              N
            </div>
            <div>
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-primary to-blue-600 bg-clip-text text-transparent">
                NEXORA
              </span>
              <span className="text-[10px] block uppercase font-bold tracking-widest text-muted-foreground -mt-1">
                Enterprise ERP
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-muted-foreground hover:bg-muted lg:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tenant company badge */}
        <div className="px-5 py-3 mx-4 my-3 rounded-xl bg-muted/60 border border-border/80 flex items-center justify-between">
          <div className="flex items-center gap-2 overflow-hidden">
            <Building2 className="h-4 w-4 text-primary shrink-0" />
            <span className="text-xs font-semibold truncate text-foreground">
              {user?.company_name || 'Nexora Alpha'}
            </span>
          </div>
          <Badge variant="outline" className="text-[10px] uppercase font-bold shrink-0">
            {user?.role || 'ADMIN'}
          </Badge>
        </div>

        {/* Navigation items */}
        <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={onClose}
                className={cn(
                  'flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )}
              >
                <div className="flex items-center gap-3">
                  <Icon className={cn('h-4 w-4', isActive ? 'text-primary-foreground' : 'text-muted-foreground')} />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <Badge variant={isActive ? 'secondary' : 'default'} className="text-[10px] px-1.5 py-0">
                    {item.badge}
                  </Badge>
                )}
              </Link>
            );
          })}
        </nav>

        {/* User profile & footer */}
        <div className="p-4 border-t border-border mt-auto">
          <div className="flex items-center justify-between p-2 rounded-lg bg-muted/40 hover:bg-muted/70 transition-colors">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="h-9 w-9 rounded-full bg-primary/20 text-primary font-bold flex items-center justify-center text-sm shrink-0">
                {user?.first_name?.[0] || 'U'}
              </div>
              <div className="truncate">
                <p className="text-xs font-bold truncate text-foreground">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-[10px] text-muted-foreground truncate">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={logout}
              title="Déconnexion"
              className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-md transition-colors"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
