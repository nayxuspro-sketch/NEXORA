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
  ChevronDown,
  Settings
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

  const isSuperAdmin = user?.is_superuser || user?.role === 'ADMIN';
  const userPerms = user?.permissions || [];
  const userGroups = (user?.groups || []).map((g) => g.toLowerCase());

  // Vérificateur dynamique de permissions et profil
  const hasAccess = (requiredModule: string, requiredPerms: string[], allowedRoles: string[]) => {
    if (isSuperAdmin) return true;

    // 1. Vérification par rôle
    if (user?.role && allowedRoles.includes(user.role)) return true;

    // 2. Vérification par nom de groupe / profil
    if (userGroups.some((g) => g.includes(requiredModule.toLowerCase()))) return true;

    // 3. Vérification par permissions granulaires incluses
    if (requiredPerms.some((p) => userPerms.includes(p) || userPerms.some((up) => up.startsWith(requiredModule)))) {
      return true;
    }

    return false;
  };

  const allNavigation = [
    {
      name: 'Tableau de bord',
      href: '/',
      icon: LayoutDashboard,
      visible: true // Toujours accessible
    },
    {
      name: 'Caisse & Vente (POS)',
      href: '/pos',
      icon: ShoppingCart,
      badge: 'Direct',
      visible: hasAccess('pos', ['pos.view_cashregister', 'sales.add_sale', 'sales.view_sale'], ['ADMIN', 'MANAGER', 'CASHIER'])
    },
    {
      name: 'Ventes & Commandes',
      href: '/sales',
      icon: FileText,
      visible: hasAccess('sales', ['sales.view_sale', 'sales.change_sale'], ['ADMIN', 'MANAGER', 'ACCOUNTANT', 'AUDITOR', 'CASHIER'])
    },
    {
      name: 'Catalogue & Produits',
      href: '/products',
      icon: Package,
      visible: hasAccess('catalog', ['catalog.view_product', 'inventory.view_stocklevel'], ['ADMIN', 'MANAGER', 'STOCK_KEEPER', 'CASHIER'])
    },
    {
      name: 'Stocks & Inventaires',
      href: '/inventory',
      icon: Layers,
      visible: hasAccess('inventory', ['inventory.view_stocklevel', 'inventory.view_inventory', 'inventory.view_store'], ['ADMIN', 'MANAGER', 'STOCK_KEEPER'])
    },
    {
      name: 'Clients & Fournisseurs',
      href: '/partners',
      icon: Users,
      visible: hasAccess('partners', ['partners.view_partner'], ['ADMIN', 'MANAGER', 'ACCOUNTANT', 'CASHIER'])
    },
    {
      name: 'Rapports & BI',
      href: '/reports',
      icon: CreditCard,
      visible: hasAccess('reports', ['sales.view_sale', 'audit.view_auditlog'], ['ADMIN', 'MANAGER', 'ACCOUNTANT', 'AUDITOR'])
    },
    {
      name: 'Assistant IA',
      href: '/ai',
      icon: Bell,
      badge: 'Copilot',
      visible: hasAccess('ai', ['ai_assistant.view_aisuggestion'], ['ADMIN', 'MANAGER'])
    },
    {
      name: 'Automatisation',
      href: '/automation',
      icon: ShieldCheck,
      visible: isSuperAdmin || user?.role === 'ADMIN'
    },
    {
      name: 'Audit & Sécurité',
      href: '/audit',
      icon: ShieldCheck,
      visible: hasAccess('audit', ['audit.view_auditlog'], ['ADMIN', 'AUDITOR', 'MANAGER'])
    },
    {
      name: 'Paramètres & Droits',
      href: '/settings',
      icon: Settings,
      badge: 'RBAC',
      visible: isSuperAdmin || user?.role === 'ADMIN'
    },
  ];

  const navigation = allNavigation.filter((item) => item.visible);

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
