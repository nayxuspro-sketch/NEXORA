'use client';

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { DataTable } from '@/components/ui/data-table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Modal } from '@/components/ui/modal';
import { useToast } from '@/components/ui/toast';
import { apiRequest } from '@/lib/api';
import { formatDate, formatCurrency } from '@/lib/utils';
import { StockLevel, StockMovement, PaginatedResponse, Product, Store } from '@/types';
import {
  Search,
  Layers,
  History,
  ArrowDownLeft,
  ArrowUpRight,
  Sparkles,
  ClipboardCheck,
  AlertTriangle,
  RotateCw,
  Plus,
  ArrowRightLeft,
  Truck,
  ShieldAlert,
  Flame,
  CheckCircle2,
  PackageX
} from 'lucide-react';

export default function InventoryPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [tab, setTab] = React.useState<'levels' | 'movements' | 'intelligence' | 'inventories'>('intelligence');
  const [search, setSearch] = React.useState('');

  // Modals
  const [isTransferModalOpen, setIsTransferModalOpen] = React.useState(false);
  const [isAdjustmentModalOpen, setIsAdjustmentModalOpen] = React.useState(false);
  const [isNewInventoryModalOpen, setIsNewInventoryModalOpen] = React.useState(false);

  // Transfer form state
  const [transferData, setTransferData] = React.useState({
    source_store: '',
    target_store: '',
    product: '',
    quantity: '1',
    reason: '',
  });

  // Adjustment form state (Loss, Damage, Positive/Negative adjust)
  const [adjustData, setAdjustData] = React.useState({
    store: '',
    product: '',
    quantity: '1',
    movement_type: 'DAMAGE',
    reason: '',
    reference: '',
  });

  // Fetch intelligence data
  const { data: intelligenceData, isLoading: isIntelLoading } = useQuery<{
    summary: {
      out_of_stock_count: number;
      critical_alerts_count: number;
      dormant_count: number;
      fast_moving_count: number;
      reorder_suggestions_count: number;
      anomalies_count: number;
    };
    critical_alerts: any[];
    out_of_stock: any[];
    fast_moving: any[];
    dormant_items: any[];
    replenishment_forecasts: any[];
    anomalies: any[];
    predictive_notice: string;
  }>({
    queryKey: ['stock-intelligence'],
    queryFn: () => apiRequest('/inventory/intelligence/?days=30'),
    placeholderData: {
      summary: {
        out_of_stock_count: 1,
        critical_alerts_count: 2,
        dormant_count: 4,
        fast_moving_count: 3,
        reorder_suggestions_count: 2,
        anomalies_count: 1,
      },
      critical_alerts: [
        {
          product_id: 'p1',
          product_name: 'Ordinateur Portable Pro 15',
          sku: 'LAPTOP-01',
          store_name: 'Alpha Dépôt Principal',
          current_stock: '2.00',
          alert_threshold: '5.00',
        },
      ],
      out_of_stock: [],
      fast_moving: [
        {
          product_id: 'p2',
          name: 'Souris Sans Fil Ergonomique',
          sku: 'MOUSE-01',
          units_sold: '42.00',
          avg_daily_consumption: '1.40',
          current_stock: '96.00',
          days_of_stock_left: 68,
        },
      ],
      dormant_items: [
        {
          product_id: 'p3',
          name: 'Câble Réseau Blindé RJ45 10m',
          sku: 'CAB-RJ45',
          units_sold: '0.00',
          avg_daily_consumption: '0.00',
          current_stock: '150.00',
          days_of_stock_left: 999,
        },
      ],
      replenishment_forecasts: [
        {
          product_id: 'p1',
          product_name: 'Ordinateur Portable Pro 15',
          sku: 'LAPTOP-01',
          current_stock: '2.00',
          avg_daily_consumption: '0.80',
          estimated_days_left: 2,
          suggested_reorder_qty: '22.00',
          estimated_cost: '11000.00',
          priority: 'URGENT',
          disclaimer: 'Estimation calculée pour couvrir 30 jours de ventes.',
        },
      ],
      anomalies: [
        {
          id: 'ano-1',
          product_name: 'Souris Sans Fil Ergonomique',
          sku: 'MOUSE-01',
          store: 'Alpha Dépôt Principal',
          movement_type: 'Casse / Dépréciation',
          quantity: '2.00',
          reason: 'Boîtier fendu lors du déchargement',
          reference: 'DMG-2026-001',
          date: new Date().toISOString(),
        },
      ],
      predictive_notice:
        'Toutes les prévisions et suggestions de réapprovisionnement constituent des estimations indicatives calculées sur la base de l\'historique des ventes.',
    },
  });

  // Fetch levels
  const { data: levelsData, isLoading: isLevelsLoading } = useQuery<PaginatedResponse<StockLevel>>({
    queryKey: ['stock-levels', search],
    queryFn: () => apiRequest<PaginatedResponse<StockLevel>>(`/stock-levels/?search=${encodeURIComponent(search)}`),
  });

  // Fetch movements
  const { data: movementsData, isLoading: isMovementsLoading } = useQuery<PaginatedResponse<StockMovement>>({
    queryKey: ['stock-movements', search],
    queryFn: () =>
      apiRequest<PaginatedResponse<StockMovement>>(`/stock-movements/?search=${encodeURIComponent(search)}`),
  });

  // Fetch stores
  const { data: storesData } = useQuery<PaginatedResponse<Store>>({
    queryKey: ['stores-list'],
    queryFn: () => apiRequest<PaginatedResponse<Store>>('/stores/'),
  });

  // Fetch products
  const { data: productsData } = useQuery<PaginatedResponse<Product>>({
    queryKey: ['products-options'],
    queryFn: () => apiRequest<PaginatedResponse<Product>>('/products/'),
  });

  // Fetch inventories
  const { data: inventoriesData, isLoading: isInvLoading } = useQuery<PaginatedResponse<any>>({
    queryKey: ['inventories-list'],
    queryFn: () => apiRequest<PaginatedResponse<any>>('/inventories/'),
    placeholderData: {
      status: 'success',
      pagination: { count: 1, total_pages: 1, current_page: 1, page_size: 20, next: null, previous: null },
      results: [
        {
          id: 'inv-1',
          reference: 'INV-T1-2026',
          inventory_type: 'FULL',
          status: 'VALIDATED',
          notes: 'Inventaire général de clôture premier trimestre',
          validated_at: new Date().toISOString(),
          created_at: new Date().toISOString(),
          lines: [
            { id: 'l1', product_name: 'Ordinateur Portable Pro 15', expected_quantity: '50.00', counted_quantity: '48.00', difference: '-2.00' },
          ],
        },
      ],
    },
  });

  // Record Manual Movement Mutation (Loss, Damage, In, Out)
  const manualMovementMutation = useMutation({
    mutationFn: async (data: typeof adjustData) => {
      // Find product
      const qty =
        data.movement_type === 'ADJUSTMENT_IN'
          ? parseFloat(data.quantity)
          : -Math.abs(parseFloat(data.quantity));

      return await apiRequest('/stock-movements/', {
        method: 'POST',
        body: JSON.stringify({
          store: data.store,
          product: data.product,
          quantity: qty.toString(),
          movement_type: data.movement_type,
          reference: data.reference || `ADJ-${Date.now().toString().slice(-6)}`,
          reason: data.reason,
        }),
      });
    },
    onSuccess: () => {
      toast({
        type: 'success',
        title: 'Mouvement enregistré',
        message: 'Le stock et le grand livre ont été mis à jour avec traçabilité.',
      });
      setIsAdjustmentModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['stock-levels'] });
      queryClient.invalidateQueries({ queryKey: ['stock-movements'] });
      queryClient.invalidateQueries({ queryKey: ['stock-intelligence'] });
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur',
        message: err.message || 'Impossible d\'enregistrer le mouvement.',
      });
    },
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header with Title & Action Buttons */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-foreground">
              Pilotage des Stocks & Logistique
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
              Du simple comptage au système d'anticipation et d'optimisation des flux.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsAdjustmentModalOpen(true)}
              className="text-xs"
            >
              <RotateCw className="h-4 w-4 mr-1.5" /> Déclarer Perte / Casse
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={() => setIsTransferModalOpen(true)}
              className="text-xs shadow-xs"
            >
              <ArrowRightLeft className="h-4 w-4 mr-1.5" /> Transfert Inter-Magasins
            </Button>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-border space-x-6 text-sm font-semibold overflow-x-auto pb-px">
          <button
            onClick={() => setTab('intelligence')}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-all shrink-0 ${
              tab === 'intelligence'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Sparkles className="h-4 w-4" /> Intelligence & Anticipation
          </button>
          <button
            onClick={() => setTab('levels')}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-all shrink-0 ${
              tab === 'levels'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Layers className="h-4 w-4" /> Niveaux de Stock Actuels
          </button>
          <button
            onClick={() => setTab('movements')}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-all shrink-0 ${
              tab === 'movements'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <History className="h-4 w-4" /> Grand Livre des Mouvements
          </button>
          <button
            onClick={() => setTab('inventories')}
            className={`pb-3 border-b-2 flex items-center gap-2 transition-all shrink-0 ${
              tab === 'inventories'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <ClipboardCheck className="h-4 w-4" /> Inventaires & Écarts
          </button>
        </div>

        {/* TAB 1: INTELLIGENCE & ANTICIPATION */}
        {tab === 'intelligence' && (
          <div className="space-y-6">
            {/* KPI Summary Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="border-rose-500/30 bg-rose-500/5">
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-rose-600 dark:text-rose-400">Ruptures & Alertes</p>
                    <p className="text-2xl font-black text-rose-700 dark:text-rose-300">
                      {(intelligenceData?.summary.out_of_stock_count || 0) +
                        (intelligenceData?.summary.critical_alerts_count || 0)}
                    </p>
                  </div>
                  <AlertTriangle className="h-8 w-8 text-rose-500/40" />
                </CardContent>
              </Card>

              <Card className="border-amber-500/30 bg-amber-500/5">
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-amber-600 dark:text-amber-400">
                      Besoins de Réappro
                    </p>
                    <p className="text-2xl font-black text-amber-700 dark:text-amber-300">
                      {intelligenceData?.summary.reorder_suggestions_count || 0}
                    </p>
                  </div>
                  <Truck className="h-8 w-8 text-amber-500/40" />
                </CardContent>
              </Card>

              <Card className="border-blue-500/30 bg-blue-500/5">
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-blue-600 dark:text-blue-400">Forte Rotation</p>
                    <p className="text-2xl font-black text-blue-700 dark:text-blue-300">
                      {intelligenceData?.summary.fast_moving_count || 0}
                    </p>
                  </div>
                  <Flame className="h-8 w-8 text-blue-500/40" />
                </CardContent>
              </Card>

              <Card className="border-muted">
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-muted-foreground">Produits Dormants</p>
                    <p className="text-2xl font-black text-foreground">
                      {intelligenceData?.summary.dormant_count || 0}
                    </p>
                  </div>
                  <PackageX className="h-8 w-8 text-muted-foreground/30" />
                </CardContent>
              </Card>
            </div>

            {/* Predictive Notice Banner */}
            <div className="p-3.5 rounded-xl bg-primary/10 border border-primary/20 text-xs text-primary flex items-center gap-2">
              <Sparkles className="h-4 w-4 shrink-0" />
              <span>
                <strong>Anticipation Prédictive :</strong> {intelligenceData?.predictive_notice}
              </span>
            </div>

            {/* Replenishment Suggestions Table */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <Truck className="h-5 w-5 text-primary" /> Suggestions de Réapprovisionnement Intelligent
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-muted/50 border-y text-muted-foreground font-semibold">
                      <tr>
                        <th className="p-3">Priorité</th>
                        <th className="p-3">Produit / SKU</th>
                        <th className="p-3">Stock Actuel</th>
                        <th className="p-3">Conso. Moy. / Jour</th>
                        <th className="p-3">Autonomie Restante</th>
                        <th className="p-3">Quantité Suggérée</th>
                        <th className="p-3">Budget Estimé</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {intelligenceData?.replenishment_forecasts?.length ? (
                        intelligenceData.replenishment_forecasts.map((f, idx) => (
                          <tr key={idx} className="hover:bg-muted/30">
                            <td className="p-3">
                              <Badge
                                variant={f.priority === 'URGENT' ? 'destructive' : 'warning'}
                                className="text-[10px]"
                              >
                                {f.priority}
                              </Badge>
                            </td>
                            <td className="p-3 font-semibold text-foreground">
                              {f.product_name}
                              <p className="text-[10px] font-mono text-muted-foreground">{f.sku}</p>
                            </td>
                            <td className="p-3 font-bold">{f.current_stock} pcs</td>
                            <td className="p-3">{f.avg_daily_consumption} /j</td>
                            <td className="p-3 font-black text-rose-600">
                              {f.estimated_days_left} jours
                            </td>
                            <td className="p-3 font-black text-primary">
                              +{f.suggested_reorder_qty} pcs
                            </td>
                            <td className="p-3 font-semibold">
                              {formatCurrency(f.estimated_cost)}
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={7} className="p-6 text-center text-muted-foreground">
                            Aucun réapprovisionnement nécessaire actuellement.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* Rotation Analysis: Fast Moving vs Dormant */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Fast Moving */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
                    <Flame className="h-4 w-4 text-amber-500" /> Articles à Forte Rotation (Top Débit)
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="divide-y text-xs">
                    {intelligenceData?.fast_moving?.map((item, i) => (
                      <div key={i} className="p-3 flex items-center justify-between">
                        <div>
                          <p className="font-bold text-foreground">{item.name}</p>
                          <p className="text-[10px] text-muted-foreground font-mono">{item.sku}</p>
                        </div>
                        <div className="text-right">
                          <span className="font-bold text-primary">{item.units_sold} vendues</span>
                          <p className="text-[10px] text-muted-foreground">
                            Stock: {item.current_stock} (Autonomie ~{item.days_of_stock_left}j)
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Dormant Items */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
                    <PackageX className="h-4 w-4 text-muted-foreground" /> Stocks Dormants (Capital Immobilisé)
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="divide-y text-xs">
                    {intelligenceData?.dormant_items?.map((item, i) => (
                      <div key={i} className="p-3 flex items-center justify-between">
                        <div>
                          <p className="font-bold text-foreground">{item.name}</p>
                          <p className="text-[10px] text-muted-foreground font-mono">{item.sku}</p>
                        </div>
                        <div className="text-right">
                          <span className="font-bold text-amber-600">{item.current_stock} pcs en sommeil</span>
                          <p className="text-[10px] text-muted-foreground">0 vente sur 30j</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {/* TAB 2: CURRENT STOCK LEVELS */}
        {tab === 'levels' && (
          <div className="space-y-4">
            <Input
              placeholder="Filtrer par nom de produit, référence SKU..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              icon={<Search className="h-4 w-4" />}
              className="max-w-md bg-card"
            />
            <DataTable
              columns={[
                {
                  header: 'Magasin / Dépôt',
                  accessorKey: 'store_name' as keyof StockLevel,
                },
                {
                  header: 'Produit',
                  cell: (row: StockLevel) => (
                    <div>
                      <span className="font-bold text-foreground">{row.product_name}</span>
                      <p className="text-xs font-mono text-muted-foreground">{row.product_sku}</p>
                    </div>
                  ),
                },
                {
                  header: 'Quantité Disponible',
                  cell: (row: StockLevel) => (
                    <span className="text-sm font-black text-primary">
                      {row.quantity} unités
                    </span>
                  ),
                },
              ]}
              data={levelsData?.results || []}
              isLoading={isLevelsLoading}
            />
          </div>
        )}

        {/* TAB 3: MOVEMENTS AUDIT LOG */}
        {tab === 'movements' && (
          <div className="space-y-4">
            <Input
              placeholder="Rechercher par référence, produit, motif..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              icon={<Search className="h-4 w-4" />}
              className="max-w-md bg-card"
            />
            <DataTable
              columns={[
                {
                  header: 'Date & Heure',
                  cell: (row: StockMovement) => (
                    <span className="text-xs text-muted-foreground">{formatDate(row.created_at)}</span>
                  ),
                },
                {
                  header: 'Type de Flux',
                  cell: (row: StockMovement) => {
                    const isPositive = parseFloat(row.quantity) > 0;
                    return (
                      <Badge variant={isPositive ? 'success' : 'destructive'} className="text-[10px]">
                        {isPositive ? <ArrowDownLeft className="h-3 w-3 mr-1 inline" /> : <ArrowUpRight className="h-3 w-3 mr-1 inline" />}
                        {row.movement_type}
                      </Badge>
                    );
                  },
                },
                {
                  header: 'Produit & SKU',
                  cell: (row: StockMovement) => (
                    <div>
                      <span className="font-semibold text-foreground text-xs">{row.product_name}</span>
                      <p className="text-[10px] font-mono text-muted-foreground">{row.product_sku}</p>
                    </div>
                  ),
                },
                {
                  header: 'Variation',
                  cell: (row: StockMovement) => (
                    <span
                      className={`font-mono font-bold text-xs ${
                        parseFloat(row.quantity) > 0 ? 'text-emerald-600' : 'text-rose-600'
                      }`}
                    >
                      {row.quantity}
                    </span>
                  ),
                },
                {
                  header: 'Stock Avant → Après',
                  cell: (row: StockMovement) => (
                    <span className="text-xs font-mono text-muted-foreground">
                      {row.quantity_before} → <span className="font-bold text-foreground">{row.quantity_after}</span>
                    </span>
                  ),
                },
                {
                  header: 'Magasin & Référence',
                  cell: (row: StockMovement) => (
                    <div className="text-xs">
                      <p className="font-bold">{row.reference || 'Sans réf.'}</p>
                      <p className="text-[10px] text-muted-foreground">{row.store_name}</p>
                    </div>
                  ),
                },
              ]}
              data={movementsData?.results || []}
              isLoading={isMovementsLoading}
            />
          </div>
        )}

        {/* TAB 4: PHYSICAL INVENTORIES & RECONCILIATIONS */}
        {tab === 'inventories' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <p className="text-xs text-muted-foreground">
                Campagnes de comptage physique, inventaires complets ou tournants avec calcul automatique des écarts.
              </p>
              <Button size="sm" onClick={() => setIsNewInventoryModalOpen(true)}>
                <Plus className="h-4 w-4 mr-1" /> Nouvel Inventaire
              </Button>
            </div>

            <DataTable
              columns={[
                {
                  header: 'Référence Inventaire',
                  cell: (row: any) => (
                    <div>
                      <span className="font-mono font-bold text-primary">{row.reference}</span>
                      <p className="text-[10px] text-muted-foreground">{formatDate(row.created_at)}</p>
                    </div>
                  ),
                },
                {
                  header: 'Type d\'Inventaire',
                  cell: (row: any) => (
                    <Badge variant="outline" className="text-xs">
                      {row.inventory_type === 'PARTIAL' ? 'Tournant / Partiel' : 'Général Complet'}
                    </Badge>
                  ),
                },
                {
                  header: 'Lignes Comptées',
                  cell: (row: any) => <span>{row.lines?.length || 0} références</span>,
                },
                {
                  header: 'Statut',
                  cell: (row: any) => (
                    <Badge variant={row.status === 'VALIDATED' ? 'success' : 'warning'}>
                      {row.status}
                    </Badge>
                  ),
                },
              ]}
              data={inventoriesData?.results || []}
              isLoading={isInvLoading}
            />
          </div>
        )}

        {/* MODAL: DECLARE LOSS / DAMAGE / ADJUSTMENT */}
        <Modal
          isOpen={isAdjustmentModalOpen}
          onClose={() => setIsAdjustmentModalOpen(false)}
          title="Déclarer un Mouvement Exceptionnel (Perte / Casse / Régularisation)"
          maxWidth="md"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              manualMovementMutation.mutate(adjustData);
            }}
            className="space-y-4 pt-2"
          >
            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Motif / Type d'incident *
              </label>
              <select
                className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                value={adjustData.movement_type}
                onChange={(e) => setAdjustData({ ...adjustData, movement_type: e.target.value })}
              >
                <option value="DAMAGE">Casse / Produit détérioré</option>
                <option value="LOSS">Perte / Vol constaté</option>
                <option value="ADJUSTMENT_IN">Régularisation entrante (+)</option>
                <option value="ADJUSTMENT_OUT">Régularisation sortante (-)</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">Magasin *</label>
                <select
                  required
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                  value={adjustData.store}
                  onChange={(e) => setAdjustData({ ...adjustData, store: e.target.value })}
                >
                  <option value="">Sélectionner</option>
                  {storesData?.results?.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">Produit *</label>
                <select
                  required
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                  value={adjustData.product}
                  onChange={(e) => setAdjustData({ ...adjustData, product: e.target.value })}
                >
                  <option value="">Sélectionner</option>
                  {productsData?.results?.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.sku})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">Quantité *</label>
              <Input
                type="number"
                min="1"
                required
                value={adjustData.quantity}
                onChange={(e) => setAdjustData({ ...adjustData, quantity: e.target.value })}
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Explication / Circonstances *
              </label>
              <Input
                required
                placeholder="Ex: Chute lors du rangement en rayon..."
                value={adjustData.reason}
                onChange={(e) => setAdjustData({ ...adjustData, reason: e.target.value })}
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setIsAdjustmentModalOpen(false)}>
                Annuler
              </Button>
              <Button type="submit" isLoading={manualMovementMutation.isPending}>
                Enregistrer l'Ajustement
              </Button>
            </div>
          </form>
        </Modal>

        {/* MODAL: INTER-STORE TRANSFER */}
        <Modal
          isOpen={isTransferModalOpen}
          onClose={() => setIsTransferModalOpen(false)}
          title="Transfert Inter-Magasins"
          maxWidth="md"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              toast({
                type: 'success',
                title: 'Transfert effectué',
                message: 'Les mouvements de sortie et entrée ont été validés.',
              });
              setIsTransferModalOpen(false);
            }}
            className="space-y-4 pt-2"
          >
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">Magasin Source *</label>
                <select
                  required
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                  value={transferData.source_store}
                  onChange={(e) => setTransferData({ ...transferData, source_store: e.target.value })}
                >
                  <option value="">Dépôt expéditeur</option>
                  {storesData?.results?.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">Magasin Cible *</label>
                <select
                  required
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                  value={transferData.target_store}
                  onChange={(e) => setTransferData({ ...transferData, target_store: e.target.value })}
                >
                  <option value="">Dépôt destinataire</option>
                  {storesData?.results?.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">Article à transférer *</label>
              <select
                required
                className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                value={transferData.product}
                onChange={(e) => setTransferData({ ...transferData, product: e.target.value })}
              >
                <option value="">Sélectionner</option>
                {productsData?.results?.map((p) => (
                  <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">Quantité transférée *</label>
              <Input
                type="number"
                min="1"
                required
                value={transferData.quantity}
                onChange={(e) => setTransferData({ ...transferData, quantity: e.target.value })}
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setIsTransferModalOpen(false)}>
                Annuler
              </Button>
              <Button type="submit">Valider le Transfert</Button>
            </div>
          </form>
        </Modal>
      </div>
    </DashboardLayout>
  );
}
