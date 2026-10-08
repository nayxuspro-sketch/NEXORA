'use client';

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { DataTable } from '@/components/ui/data-table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { apiRequest } from '@/lib/api';
import { formatCurrency, formatDate } from '@/lib/utils';
import { downloadPdfFile } from '@/lib/pdf-export';
import { Sale, PaginatedResponse } from '@/types';
import { Search, FileText, Eye, Download, CreditCard, CheckCircle2, Banknote, Smartphone } from 'lucide-react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/toast';

export default function SalesPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [search, setSearch] = React.useState('');
  const [currentPage, setCurrentPage] = React.useState(1);
  const [selectedSale, setSelectedSale] = React.useState<Sale | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = React.useState(false);

  // Modal: Bilan Vendeur / État de Vente PDF
  const [isSellerPdfModalOpen, setIsSellerPdfModalOpen] = React.useState(false);
  const [isExportingSellerPdf, setIsExportingSellerPdf] = React.useState(false);
  const [sellerPdfPeriod, setSellerPdfPeriod] = React.useState({
    start_date: new Date(Date.now() - 30 * 86400000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    seller_email: '',
  });

  const handleExportSellerPdf = async () => {
    try {
      setIsExportingSellerPdf(true);
      const queryParams = new URLSearchParams({
        start_date: sellerPdfPeriod.start_date,
        end_date: sellerPdfPeriod.end_date,
        ...(sellerPdfPeriod.seller_email ? { seller: sellerPdfPeriod.seller_email } : {}),
      });
      await downloadPdfFile(
        `/api/v1/sales/export-seller-pdf/?${queryParams.toString()}`,
        `Bilan_Ventes_${sellerPdfPeriod.start_date}_${sellerPdfPeriod.end_date}.pdf`
      );

      toast({
        type: 'success',
        title: 'Bilan Ventes Téléchargé',
        message: "L'état de vente et l'analyse avec suggestions ont été générés en PDF.",
      });
      setIsSellerPdfModalOpen(false);
    } catch (err: any) {
      toast({
        type: 'error',
        title: 'Erreur Export PDF',
        message: err.message || 'Impossible de générer le bilan des ventes en PDF.',
      });
    } finally {
      setIsExportingSellerPdf(false);
    }
  };

  // Modal: Compléter Solde Partiel
  const [isPayModalOpen, setIsPayModalOpen] = React.useState(false);
  const [saleToPay, setSaleToPay] = React.useState<Sale | null>(null);
  const [payAmount, setPayAmount] = React.useState('');
  const [payMethod, setPayMethod] = React.useState<'CASH' | 'MOBILE_MONEY' | 'CARD' | 'BANK_TRANSFER' | 'CHECK'>('CASH');
  const [payReference, setPayReference] = React.useState('');

  const openPayModal = (sale: Sale) => {
    const total = parseFloat(sale.total_amount?.toString() || '0');
    const paid = parseFloat(sale.paid_amount?.toString() || '0');
    const remaining = Math.max(0, total - paid);
    setSaleToPay(sale);
    setPayAmount(remaining > 0 ? remaining.toString() : '');
    setPayMethod('CASH');
    setPayReference(`REG-SOLDE-${Date.now().toString().slice(-4)}`);
    setIsPayModalOpen(true);
  };

  const payMutation = useMutation({
    mutationFn: async () => {
      if (!saleToPay) throw new Error('Vente non sélectionnée');
      const amt = parseFloat(payAmount);
      if (isNaN(amt) || amt <= 0) {
        throw new Error('Veuillez saisir un montant valide');
      }
      return await apiRequest(`/sales/${saleToPay.id}/pay/`, {
        method: 'POST',
        body: JSON.stringify({
          amount: amt,
          method: payMethod,
          reference: payReference,
        }),
      });
    },
    onSuccess: () => {
      toast({
        type: 'success',
        title: 'Paiement Enregistré avec Succès',
        message: `Le versement de ${formatCurrency(payAmount)} a été crédité sur la facture.`,
      });
      setIsPayModalOpen(false);
      setSaleToPay(null);
      setPayAmount('');
      // Invalidation des caches
      queryClient.invalidateQueries({ queryKey: ['sales-list'] });
      queryClient.invalidateQueries({ queryKey: ['registers'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-report'] });
      queryClient.invalidateQueries({ queryKey: ['bi-analytics'] });
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur lors du règlement',
        message: err.message || 'Impossible d\'enregistrer le versement.',
      });
    },
  });

  const { data: salesData, isLoading, isError, error, refetch } = useQuery<PaginatedResponse<Sale>>({
    queryKey: ['sales-list', search, currentPage],
    queryFn: () => apiRequest<PaginatedResponse<Sale>>(`/sales/?page=${currentPage}&search=${encodeURIComponent(search)}`),
    staleTime: 1000 * 60,
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
      cell: (row: Sale) => {
        const total = parseFloat(row.total_amount?.toString() || '0');
        const paid = parseFloat(row.paid_amount?.toString() || '0');
        const remaining = total - paid;
        const canPay = remaining > 0 && row.status !== 'CANCELLED';

        return (
          <div className="flex items-center gap-1.5">
            {canPay && (
              <Button
                variant="default"
                size="sm"
                className="h-8 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs"
                onClick={() => openPayModal(row)}
              >
                <CreditCard className="h-3.5 w-3.5 mr-1" /> Encaisser solde
              </Button>
            )}
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
          </div>
        );
      },
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-foreground">
              Historique des Ventes & Factures
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
              Suivi des encaissements, soldes partiels et pièces comptables générées.
            </p>
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={() => setIsSellerPdfModalOpen(true)}
            className="flex items-center gap-2 border-primary/30 hover:bg-primary/10 hover:text-primary font-bold text-xs"
          >
            <Download className="h-4 w-4 text-primary" />
            Exporter Bilan & Ventes (PDF)
          </Button>
        </div>

        <Input
          placeholder="Rechercher par référence, nom client..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          icon={<Search className="h-4 w-4" />}
          className="max-w-md bg-card"
        />

        {isError && (
          <div className="flex flex-col gap-2 rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200 sm:flex-row sm:items-center sm:justify-between">
            <span>
              Aucune donnee n'a ete chargee depuis le serveur :{' '}
              {(error as any)?.message || 'erreur inconnue'}. Les ventes ci-dessous ne
              sont PAS la liste officielle.
            </span>
            <button
              type="button"
              onClick={() => refetch()}
              className="rounded-md border border-red-400/60 px-3 py-1.5 text-xs font-semibold text-red-100 hover:bg-red-500/20"
            >
              Reessayer
            </button>
          </div>
        )}

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

              <div className="flex justify-end gap-2 pt-3 border-t">
                {parseFloat(selectedSale.total_amount?.toString() || '0') > parseFloat(selectedSale.paid_amount?.toString() || '0') && selectedSale.status !== 'CANCELLED' && (
                  <Button
                    type="button"
                    variant="default"
                    className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs"
                    onClick={() => {
                      setIsDetailModalOpen(false);
                      openPayModal(selectedSale);
                    }}
                  >
                    <CreditCard className="h-4 w-4 mr-1.5" /> Encaisser le solde restant
                  </Button>
                )}
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

        {/* MODAL: COMPLÉTER UN SOLDE PARTIEL */}
        <Modal
          isOpen={isPayModalOpen}
          onClose={() => {
            setIsPayModalOpen(false);
            setSaleToPay(null);
          }}
          title={`Encaisser un Versement — Facture ${saleToPay?.reference || ''}`}
          maxWidth="md"
        >
          {saleToPay && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                payMutation.mutate();
              }}
              className="space-y-4 pt-2"
            >
              {/* Récapitulatif financier */}
              <div className="p-3.5 rounded-xl bg-muted/40 border space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Client :</span>
                  <span className="font-bold text-foreground">{saleToPay.customer_name || 'Client Comptoir'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Total Facture TTC :</span>
                  <span className="font-mono font-bold text-foreground">{formatCurrency(saleToPay.total_amount)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Déjà Encaissé :</span>
                  <span className="font-mono font-semibold text-emerald-600">{formatCurrency(saleToPay.paid_amount)}</span>
                </div>
                <div className="flex justify-between pt-2 border-t text-sm">
                  <span className="font-bold text-foreground">Reste à payer :</span>
                  <span className="font-mono font-black text-rose-600">
                    {formatCurrency(Math.max(0, parseFloat(saleToPay.total_amount?.toString() || '0') - parseFloat(saleToPay.paid_amount?.toString() || '0')))}
                  </span>
                </div>
              </div>

              {/* Mode de règlement */}
              <div>
                <label className="text-xs font-bold text-foreground block mb-1.5">
                  Mode de Versement *
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <button
                    type="button"
                    onClick={() => setPayMethod('CASH')}
                    className={`p-2.5 rounded-xl border flex flex-col items-center gap-1 text-xs font-bold transition-all ${
                      payMethod === 'CASH'
                        ? 'border-primary bg-primary/10 text-primary ring-2 ring-primary'
                        : 'hover:bg-muted text-muted-foreground'
                    }`}
                  >
                    <Banknote className="h-4 w-4" /> Espèces
                  </button>
                  <button
                    type="button"
                    onClick={() => setPayMethod('MOBILE_MONEY')}
                    className={`p-2.5 rounded-xl border flex flex-col items-center gap-1 text-xs font-bold transition-all ${
                      payMethod === 'MOBILE_MONEY'
                        ? 'border-primary bg-primary/10 text-primary ring-2 ring-primary'
                        : 'hover:bg-muted text-muted-foreground'
                    }`}
                  >
                    <Smartphone className="h-4 w-4" /> Mobile Money
                  </button>
                  <button
                    type="button"
                    onClick={() => setPayMethod('CARD')}
                    className={`p-2.5 rounded-xl border flex flex-col items-center gap-1 text-xs font-bold transition-all ${
                      payMethod === 'CARD'
                        ? 'border-primary bg-primary/10 text-primary ring-2 ring-primary'
                        : 'hover:bg-muted text-muted-foreground'
                    }`}
                  >
                    <CreditCard className="h-4 w-4" /> Carte Bancaire
                  </button>
                  <button
                    type="button"
                    onClick={() => setPayMethod('BANK_TRANSFER')}
                    className={`p-2.5 rounded-xl border flex flex-col items-center gap-1 text-xs font-bold transition-all ${
                      payMethod === 'BANK_TRANSFER'
                        ? 'border-primary bg-primary/10 text-primary ring-2 ring-primary'
                        : 'hover:bg-muted text-muted-foreground'
                    }`}
                  >
                    <FileText className="h-4 w-4" /> Virement / Chèque
                  </button>
                </div>
              </div>

              {/* Montant versé */}
              <div>
                <label className="text-xs font-bold text-foreground block mb-1">
                  Montant du Versement (FCFA) *
                </label>
                <Input
                  type="number"
                  step="any"
                  min="1"
                  required
                  placeholder="Ex: 25000"
                  value={payAmount}
                  onChange={(e) => setPayAmount(e.target.value)}
                  className="font-mono font-bold text-base"
                />
                <p className="text-[11px] text-muted-foreground mt-1">
                  Vous pouvez encaisser la totalité du restant ou un acompte partiel additionnel.
                </p>
              </div>

              {/* Référence ou reçu */}
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Référence du Reçu / Bordereau (Optionnel)
                </label>
                <Input
                  placeholder="Ex: REG-MOBILE-998822"
                  value={payReference}
                  onChange={(e) => setPayReference(e.target.value)}
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsPayModalOpen(false);
                    setSaleToPay(null);
                  }}
                >
                  Annuler
                </Button>
                <Button
                  type="submit"
                  isLoading={payMutation.isPending}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold"
                >
                  <CheckCircle2 className="h-4 w-4 mr-1.5" /> Valider l'Encaissement
                </Button>
              </div>
            </form>
          )}
        </Modal>

        {/* MODAL: EXPORT BILAN DES VENTES PDF */}
        <Modal
          isOpen={isSellerPdfModalOpen}
          onClose={() => setIsSellerPdfModalOpen(false)}
          title="Exporter le Bilan des Ventes & Analyses (PDF)"
          maxWidth="md"
        >
          <div className="space-y-4 pt-2">
            <p className="text-xs text-muted-foreground">
              Générez un rapport PDF officiel sur 2 pages comprenant l&apos;état certifié des transactions, la marge commerciale brute, ainsi que des suggestions personnalisées basées sur les tendances de vente.
            </p>

            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-foreground block mb-1">Date Début *</label>
                  <Input
                    type="date"
                    value={sellerPdfPeriod.start_date}
                    onChange={(e) => setSellerPdfPeriod(prev => ({ ...prev, start_date: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-foreground block mb-1">Date Fin *</label>
                  <Input
                    type="date"
                    value={sellerPdfPeriod.end_date}
                    onChange={(e) => setSellerPdfPeriod(prev => ({ ...prev, end_date: e.target.value }))}
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-foreground block mb-1">Filtre Vendeur / Caissier (Optionnel)</label>
                <Input
                  placeholder="Laisser vide pour toutes les ventes ou email vendeur"
                  value={sellerPdfPeriod.seller_email}
                  onChange={(e) => setSellerPdfPeriod(prev => ({ ...prev, seller_email: e.target.value }))}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsSellerPdfModalOpen(false)}
              >
                Annuler
              </Button>
              <Button
                type="button"
                onClick={handleExportSellerPdf}
                isLoading={isExportingSellerPdf}
                className="bg-primary hover:bg-primary/90 text-primary-foreground font-bold"
              >
                <Download className="h-4 w-4 mr-1.5" /> Télécharger Rapport PDF
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </DashboardLayout>
  );
}
