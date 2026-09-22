'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { DataTable } from '@/components/ui/data-table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { apiRequest } from '@/lib/api';
import { formatCurrency, formatDate } from '@/lib/utils';
import { Sale, PaginatedResponse } from '@/types';
import { Search, FileText, Eye, Download } from 'lucide-react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';

export default function SalesPage() {
  const [search, setSearch] = React.useState('');
  const [currentPage, setCurrentPage] = React.useState(1);
  const [selectedSale, setSelectedSale] = React.useState<Sale | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = React.useState(false);

  const { data: salesData, isLoading } = useQuery<PaginatedResponse<Sale>>({
    queryKey: ['sales-list', search, currentPage],
    queryFn: () => apiRequest<PaginatedResponse<Sale>>(`/sales/?page=${currentPage}&search=${encodeURIComponent(search)}`),
  });

  const columns = [
    {
      header: 'Référence Vente',
      cell: (row: Sale) => (
        <div>
          <span className="font-mono font-bold text-primary">{row.reference}</span>
          <p className="text-[11px] text-muted-foreground">{formatDate(row.created_at)}</p>
        </div>
      ),
    },
    {
      header: 'Client & Magasin',
      cell: (row: Sale) => (
        <div>
          <p className="font-medium text-foreground">{row.customer_name || 'Client Comptoir'}</p>
          <p className="text-xs text-muted-foreground">{row.store_name}</p>
        </div>
      ),
    },
    {
      header: 'Articles Vendus',
      cell: (row: Sale) => {
        const items = row.items || [];
        const totalQty = items.reduce((sum, item) => sum + parseFloat(item.quantity?.toString() || '0'), 0);
        return (
          <div className="max-w-xs">
            <div className="flex items-center gap-1.5 font-semibold text-xs text-foreground">
              <span className="inline-flex items-center justify-center px-1.5 py-0.5 rounded bg-primary/10 text-primary font-bold text-[10px]">
                {items.length} réf.
              </span>
              <span>({totalQty} art.)</span>
            </div>
            <p className="text-[11px] text-muted-foreground truncate mt-0.5" title={items.map(it => `${it.quantity}x ${it.product_name}`).join(', ')}>
              {items.map(it => `${it.product_name}`).join(', ')}
            </p>
          </div>
        );
      },
    },
    {
      header: 'Total TTC',
      cell: (row: Sale) => <span className="font-bold text-foreground">{formatCurrency(row.total_amount)}</span>,
    },
    {
      header: 'Montant Réglé',
      cell: (row: Sale) => (
        <span className="font-semibold text-emerald-600">{formatCurrency(row.paid_amount)}</span>
      ),
    },
    {
      header: 'Statut Règlement',
      cell: (row: Sale) => {
        const variants: Record<string, 'success' | 'warning' | 'destructive'> = {
          PAID: 'success',
          PARTIAL: 'warning',
          PENDING: 'destructive',
          REFUNDED: 'destructive',
        };
        const labels: Record<string, string> = {
          PAID: 'Payé Intégral',
          PARTIAL: 'Solde Partiel',
          PENDING: 'En Attente',
          REFUNDED: 'Remboursé',
        };
        return (
          <Badge variant={variants[row.payment_status] || 'outline'} className="text-[11px] font-semibold">
            {labels[row.payment_status] || row.payment_status}
          </Badge>
        );
      },
    },
    {
      header: 'Statut Vente',
      cell: (row: Sale) => {
        const labels: Record<string, string> = {
          COMPLETED: 'Clôturée / Livrée',
          DRAFT: 'Brouillon',
          CANCELLED: 'Annulée',
        };
        return (
          <Badge variant={row.status === 'COMPLETED' ? 'success' : 'destructive'} className="text-[11px] font-semibold">
            {labels[row.status] || row.status}
          </Badge>
        );
      },
    },
    {
      header: 'Actions',
      cell: (row: Sale) => (
        <Button
          variant="outline"
          size="sm"
          className="h-8 text-xs font-semibold hover:bg-primary/10 hover:text-primary transition-all"
          onClick={() => {
            setSelectedSale(row);
            setIsDetailModalOpen(true);
          }}
        >
          <Eye className="h-3.5 w-3.5 mr-1 text-primary" /> Détails
        </Button>
      ),
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-foreground">
            Historique des Ventes & Factures
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            Suivi des encaissements, soldes partiels et pièces comptables générées.
          </p>
        </div>

        <Input
          placeholder="Rechercher par référence, nom client..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          icon={<Search className="h-4 w-4" />}
          className="max-w-md bg-card"
        />

        <DataTable
          columns={columns}
          data={salesData?.results || []}
          isLoading={isLoading}
          pagination={{
            currentPage,
            totalPages: salesData?.pagination?.total_pages || 1,
            onPageChange: setCurrentPage,
          }}
        />

        {/* MODAL: DÉTAIL INTÉGRAL DE LA FACTURE / VENTE */}
        <Modal
          isOpen={isDetailModalOpen}
          onClose={() => {
            setIsDetailModalOpen(false);
            setSelectedSale(null);
          }}
          title={`Détail de la Facture : ${selectedSale?.reference || ''}`}
          maxWidth="2xl"
        >
          {selectedSale && (
            <div className="space-y-4 pt-1">
              {/* Synthèse client & magasin */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 rounded-xl bg-muted/40 border text-xs">
                <div>
                  <span className="text-muted-foreground block">Client :</span>
                  <span className="font-bold text-foreground">
                    {selectedSale.customer_name || 'Client Comptoir'}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground block">Magasin :</span>
                  <span className="font-bold text-foreground">{selectedSale.store_name}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block">Vendeur / Caissier :</span>
                  <span className="font-mono text-muted-foreground truncate block">
                    {selectedSale.seller_name || 'Système'}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground block">Date & Heure :</span>
                  <span className="font-medium text-foreground">{formatDate(selectedSale.created_at)}</span>
                </div>
              </div>

              {/* Lignes d'articles vendus */}
              <div className="border rounded-xl overflow-hidden">
                <div className="bg-muted/60 px-3 py-2 border-b flex justify-between items-center text-xs font-bold text-foreground">
                  <span>Articles & Lignes de Vente</span>
                  <span>{selectedSale.items?.length || 0} référence(s)</span>
                </div>
                <div className="max-h-56 overflow-y-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-muted/30 text-muted-foreground font-semibold border-b">
                      <tr>
                        <th className="p-2.5">Article & SKU</th>
                        <th className="p-2.5 text-right">Prix Unitaire</th>
                        <th className="p-2.5 text-right">Qté</th>
                        <th className="p-2.5 text-right">TVA</th>
                        <th className="p-2.5 text-right">Total TTC</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {selectedSale.items && selectedSale.items.length > 0 ? (
                        selectedSale.items.map((item: any, i: number) => (
                          <tr key={i} className="hover:bg-muted/20">
                            <td className="p-2.5 font-semibold text-foreground">
                              {item.product_name}
                              <span className="block text-[10px] font-mono text-muted-foreground">
                                {item.product_sku}
                              </span>
                            </td>
                            <td className="p-2.5 text-right font-mono">
                              {formatCurrency(item.unit_price)}
                            </td>
                            <td className="p-2.5 text-right font-bold font-mono">
                              {item.quantity}
                            </td>
                            <td className="p-2.5 text-right font-mono text-muted-foreground">
                              {item.tax_rate}%
                            </td>
                            <td className="p-2.5 text-right font-bold text-foreground font-mono">
                              {formatCurrency(item.total)}
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={5} className="p-4 text-center text-muted-foreground">
                            Aucun détail de ligne disponible.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Totaux financiers */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 p-3 rounded-xl bg-card border text-xs">
                <div>
                  <span className="text-muted-foreground block">Sous-total HT :</span>
                  <span className="font-bold text-foreground">{formatCurrency(selectedSale.subtotal_amount)}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block">TVA Collectée :</span>
                  <span className="font-bold text-foreground">{formatCurrency(selectedSale.tax_amount)}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block">Remise :</span>
                  <span className="font-bold text-amber-600">{formatCurrency(selectedSale.discount_amount)}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block">Total TTC :</span>
                  <span className="font-black text-primary text-sm">{formatCurrency(selectedSale.total_amount)}</span>
                </div>
              </div>

              {/* Règlements associés */}
              {selectedSale.payments && selectedSale.payments.length > 0 && (
                <div className="border rounded-xl p-3 bg-muted/20 space-y-1.5 text-xs">
                  <span className="font-bold text-foreground block">Mode(s) de Règlement Enregistré(s) :</span>
                  <div className="space-y-1">
                    {selectedSale.payments.map((p: any, idx: number) => (
                      <div key={idx} className="flex items-center justify-between font-mono">
                        <span className="text-muted-foreground">
                          {p.payment_method === 'MOBILE_MONEY' ? 'Mobile Money (Orange / Moov)' : p.payment_method === 'CASH' ? 'Espèces' : p.payment_method === 'CARD' ? 'Carte Bancaire' : 'À Crédit'}
                          {p.reference ? ` (${p.reference})` : ''}
                        </span>
                        <span className="font-bold text-emerald-600">
                          {formatCurrency(p.amount)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-end pt-3 border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsDetailModalOpen(false);
                    setSelectedSale(null);
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
