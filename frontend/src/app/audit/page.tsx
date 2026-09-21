'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { DataTable } from '@/components/ui/data-table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Modal } from '@/components/ui/modal';
import { apiRequest } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { PaginatedResponse } from '@/types';
import {
  Search,
  ShieldCheck,
  RefreshCw,
  Eye,
  ShieldAlert,
  Server,
  User,
  Activity,
  Calendar,
  Lock
} from 'lucide-react';

interface AuditLogItem {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  user_email: string;
  ip_address: string;
  details?: any;
  created_at: string;
}

export default function AuditPage() {
  const [search, setSearch] = React.useState('');
  const [currentPage, setCurrentPage] = React.useState(1);
  const [actionFilter, setActionFilter] = React.useState('');
  const [selectedLog, setSelectedLog] = React.useState<AuditLogItem | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = React.useState(false);

  // Auto-refresh interval (every 10 seconds)
  const { data: auditData, isLoading, refetch, isFetching } = useQuery<PaginatedResponse<AuditLogItem>>({
    queryKey: ['audit-logs', search, currentPage, actionFilter],
    queryFn: () => {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        search: search.trim(),
        ...(actionFilter ? { action: actionFilter } : {})
      });
      return apiRequest<PaginatedResponse<AuditLogItem>>(`/audit-logs/?${params.toString()}`);
    },
    refetchInterval: 10000, // Live poll every 10s for real-time security monitoring
  });

  // Traduction française et stylisation visuelle des actions
  const formatActionDetails = (action: string) => {
    const act = action.toUpperCase();
    if (act.includes('LOGIN') || act.includes('AUTH')) {
      return {
        label: act.includes('FAIL') ? 'Échec Connexion' : 'Connexion Réussie',
        variant: act.includes('FAIL') ? 'destructive' : 'success',
        icon: <Lock className="h-3 w-3 mr-1 inline" />
      };
    }
    if (act.includes('SALE') || act.includes('PAYMENT')) {
      return {
        label: act.includes('POST') || act.includes('CREATE') ? 'Création Vente / Caisse' : 'Paiement / Vente',
        variant: 'default',
        icon: <Activity className="h-3 w-3 mr-1 inline" />
      };
    }
    if (act.includes('PRODUCT') || act.includes('CATALOG')) {
      return {
        label: 'Catalogue & Articles',
        variant: 'outline',
        icon: <Activity className="h-3 w-3 mr-1 inline" />
      };
    }
    if (act.includes('INVENTORY') || act.includes('STOCK')) {
      return {
        label: 'Ajustement / Inventaire',
        variant: 'warning',
        icon: <ShieldAlert className="h-3 w-3 mr-1 inline" />
      };
    }
    return {
      label: action,
      variant: 'outline',
      icon: <Activity className="h-3 w-3 mr-1 inline" />
    };
  };

  const columns = [
    {
      header: 'Date & Heure (UTC/Local)',
      cell: (row: AuditLogItem) => (
        <div>
          <span className="font-mono text-xs font-semibold text-foreground">
            {formatDate(row.created_at)}
          </span>
        </div>
      ),
    },
    {
      header: 'Action Réalisée',
      cell: (row: AuditLogItem) => {
        const info = formatActionDetails(row.action);
        return (
          <Badge variant={info.variant as any} className="text-[11px] font-semibold">
            {info.icon}
            {info.label}
          </Badge>
        );
      },
    },
    {
      header: 'Entité Cible',
      cell: (row: AuditLogItem) => (
        <div className="text-xs">
          <span className="font-bold text-foreground capitalize">{row.resource_type}</span>
          <p className="text-[10px] font-mono text-muted-foreground truncate max-w-[200px]">
            {row.resource_id}
          </p>
        </div>
      ),
    },
    {
      header: 'Opérateur / Utilisateur',
      cell: (row: AuditLogItem) => (
        <span className="font-mono text-xs text-foreground">
          {row.user_email || 'Système Automatique'}
        </span>
      ),
    },
    {
      header: 'Adresse IP',
      cell: (row: AuditLogItem) => (
        <Badge variant="outline" className="font-mono text-[10px] bg-muted/40">
          {row.ip_address || '127.0.0.1'}
        </Badge>
      ),
    },
    {
      header: 'Actions',
      cell: (row: AuditLogItem) => (
        <Button
          variant="outline"
          size="sm"
          className="h-7 text-xs px-2 font-medium hover:bg-primary/10 hover:text-primary transition-all"
          onClick={() => {
            setSelectedLog(row);
            setIsDetailModalOpen(true);
          }}
        >
          <Eye className="h-3.5 w-3.5 mr-1" /> Inspecter
        </Button>
      ),
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* En-tête */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-extrabold tracking-tight text-foreground flex items-center gap-2">
                <ShieldCheck className="h-7 w-7 text-emerald-500" /> Journal d'Audit & Sécurité Inaltérable
              </h1>
              <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold border border-emerald-500/20">
                Temps Réel Actif
              </span>
            </div>
            <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
              Registre d'audit cryptographique et traçabilité exhaustive de toutes les transactions et modifications.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isFetching}
              className="text-xs font-semibold"
            >
              <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${isFetching ? 'animate-spin text-primary' : ''}`} />
              Actualiser
            </Button>
          </div>
        </div>

        {/* Barre de filtres */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-card p-3 rounded-xl border">
          <div className="flex-1 max-w-md">
            <Input
              placeholder="Filtrer par ressource, URL, email opérateur..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              icon={<Search className="h-4 w-4" />}
              className="bg-background"
            />
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="text-muted-foreground font-medium">Filtrer par type :</span>
            <select
              className="h-9 px-3 rounded-lg border border-input bg-background text-xs font-medium"
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
            >
              <option value="">Tous les types d'actions</option>
              <option value="LOGIN_SUCCESS">Connexions réussies</option>
              <option value="POST_SALES">Encaissements & Ventes</option>
              <option value="POST_PRODUCTS">Modifications Produits</option>
              <option value="POST_PARTNERS">Tiers & Clients</option>
            </select>
          </div>
        </div>

        {/* Tableau d'Audit avec Pagination */}
        <DataTable
          columns={columns}
          data={auditData?.results || []}
          isLoading={isLoading}
          pagination={{
            currentPage,
            totalPages: auditData?.pagination?.total_pages || 1,
            onPageChange: setCurrentPage,
          }}
        />

        {/* MODAL: DÉTAIL D'UNE ENTRÉE DU JOURNAL D'AUDIT */}
        <Modal
          isOpen={isDetailModalOpen}
          onClose={() => {
            setIsDetailModalOpen(false);
            setSelectedLog(null);
          }}
          title="Détail de l'Événement de Sécurité & d'Audit"
          maxWidth="lg"
        >
          {selectedLog && (
            <div className="space-y-4 pt-1">
              <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-muted/40 border text-xs">
                <div>
                  <span className="text-muted-foreground block">Action enregistrée :</span>
                  <span className="font-mono font-bold text-foreground">{selectedLog.action}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block">Horodatage précis :</span>
                  <span className="font-semibold text-foreground">{formatDate(selectedLog.created_at)}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block">Opérateur :</span>
                  <span className="font-semibold text-foreground">{selectedLog.user_email || 'Système'}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block">Adresse IP cliente :</span>
                  <span className="font-mono text-foreground">{selectedLog.ip_address}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-muted-foreground block">Ressource affectée :</span>
                  <span className="font-mono text-primary font-bold">{selectedLog.resource_type} (#{selectedLog.resource_id})</span>
                </div>
              </div>

              {/* Payload brut ou détails JSON */}
              <div>
                <span className="text-xs font-bold text-foreground block mb-1">
                  Payload & Détails Techniques Enregistrés :
                </span>
                <pre className="p-3 rounded-xl bg-slate-950 text-slate-100 font-mono text-[11px] overflow-x-auto max-h-56 border">
                  {JSON.stringify(selectedLog.details || {}, null, 2)}
                </pre>
              </div>

              <div className="flex justify-end pt-2 border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsDetailModalOpen(false);
                    setSelectedLog(null);
                  }}
                >
                  Fermer
                </Button>
              </div>
            </div>
          )}
        </Modal>
      </div>
    </DashboardLayout>
  );
}
