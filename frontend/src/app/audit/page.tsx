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
  Lock,
  FileText,
  Download
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
  // PDF Export Modal State
  const [isPdfModalOpen, setIsPdfModalOpen] = React.useState(false);
  const [pdfPeriod, setPdfPeriod] = React.useState({
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    action: '',
  });
  const [isExportingPdf, setIsExportingPdf] = React.useState(false);

  const handleExportPdf = async () => {
    try {
      setIsExportingPdf(true);
      const queryParams = new URLSearchParams({
        start_date: pdfPeriod.start_date,
        end_date: pdfPeriod.end_date,
        ...(pdfPeriod.action ? { action: pdfPeriod.action } : {}),
      });
      const response = await fetch(`/api/v1/audit/export-pdf/?${queryParams.toString()}`);
      if (!response.ok) {
        throw new Error('Erreur lors de la génération du rapport PDF d\'audit');
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Journal_Audit_${pdfPeriod.start_date}_${pdfPeriod.end_date}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setIsPdfModalOpen(false);
    } catch (err: any) {
      console.error('Erreur export audit PDF:', err);
    } finally {
      setIsExportingPdf(false);
    }
  };

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
              onClick={() => setIsPdfModalOpen(true)}
              className="text-xs font-semibold border-primary/30 text-primary hover:bg-primary/10 transition-all shadow-xs"
            >
              <FileText className="h-3.5 w-3.5 mr-1.5 text-primary" /> Exporter en PDF (par période)
            </Button>
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

        {/* MODAL: EXPORT PDF DU JOURNAL D'AUDIT PAR PÉRIODE DÉFINIE */}
        <Modal
          isOpen={isPdfModalOpen}
          onClose={() => setIsPdfModalOpen(false)}
          title="Exporter le Journal d'Audit & Sécurité en PDF"
          maxWidth="md"
        >
          <div className="space-y-4 pt-2">
            <p className="text-xs text-muted-foreground">
              Générez un rapport officiel et inaltérable des journaux d'audit et de conformité pour la période de date de votre choix (A4 Paysage Haute Définition).
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Date de Début Définie *
                </label>
                <Input
                  type="date"
                  required
                  value={pdfPeriod.start_date}
                  onChange={(e) => setPdfPeriod({ ...pdfPeriod, start_date: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Date de Fin Définie *
                </label>
                <Input
                  type="date"
                  required
                  value={pdfPeriod.end_date}
                  onChange={(e) => setPdfPeriod({ ...pdfPeriod, end_date: e.target.value })}
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Filtrer par Catégorie d'Événement (Optionnel)
              </label>
              <select
                className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm font-medium"
                value={pdfPeriod.action}
                onChange={(e) => setPdfPeriod({ ...pdfPeriod, action: e.target.value })}
              >
                <option value="">Tous les événements de traçabilité</option>
                <option value="LOGIN">Authentifications & Connexions (LOGIN)</option>
                <option value="SALES">Transactions & Ventes Caisse (SALES)</option>
                <option value="PRODUCTS">Articles & Catalogue (PRODUCTS)</option>
                <option value="PARTNERS">Clients & Fournisseurs (PARTNERS)</option>
              </select>
            </div>

            <div className="p-3 rounded-xl bg-muted/40 border border-border text-xs text-muted-foreground flex items-center justify-between">
              <span>Format du document :</span>
              <span className="font-bold text-foreground">Registre d'Audit A4 Paysage (Landscape)</span>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-border">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsPdfModalOpen(false)}
              >
                Annuler
              </Button>
              <Button
                type="button"
                onClick={handleExportPdf}
                isLoading={isExportingPdf}
              >
                <Download className="h-4 w-4 mr-1.5" /> Télécharger le Journal PDF
              </Button>
            </div>
          </div>
        </Modal>

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
