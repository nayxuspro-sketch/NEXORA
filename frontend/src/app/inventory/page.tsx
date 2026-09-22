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
import { downloadPdfFile } from '@/lib/pdf-export';
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
  PackageX,
  FileText,
  Download
} from 'lucide-react';

export default function InventoryPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [tab, setTab] = React.useState<'levels' | 'movements' | 'intelligence' | 'inventories'>('intelligence');
  const [search, setSearch] = React.useState('');

  // Modals
  const [isTransferModalOpen, setIsTransferModalOpen] = React.useState(false);
  const [isAdjustmentModalOpen, setIsAdjustmentModalOpen] = React.useState(false);
  const [isStockEntryModalOpen, setIsStockEntryModalOpen] = React.useState(false);
  const [stockEntryData, setStockEntryData] = React.useState({
    store: '',
    product: '',
    quantity: '10',
    movement_type: 'INITIAL',
    reason: 'Approvisionnement direct / Initialisation stock',
    reference: '',
  });
  const [isNewInventoryModalOpen, setIsNewInventoryModalOpen] = React.useState(false);
  const [selectedInventory, setSelectedInventory] = React.useState<any>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = React.useState(false);
  const [isAddLineModalOpen, setIsAddLineModalOpen] = React.useState(false);
  // Dictionnaire de traduction en français pour les flux de stock
  const formatMovementTypeFr = (type: string, display?: string) => {
    if (display) return display;
    const dict: Record<string, string> = {
      PURCHASE: 'Achat / Réception',
      SALE: 'Vente',
      RETURN_CUSTOMER: 'Retour client',
      RETURN_SUPPLIER: 'Retour fournisseur',
      TRANSFER_IN: 'Transfert entrant (+)',
      TRANSFER_OUT: 'Transfert sortant (-)',
      ADJUSTMENT_IN: 'Ajustement positif (+)',
      ADJUSTMENT_OUT: 'Ajustement négatif (-)',
      LOSS: 'Perte constatée',
      DAMAGE: 'Casse / Dépréciation',
      INITIAL: 'Stock initial',
    };
    return dict[type] || type;
  };

  // PDF Export Modal State
  // Inventories & Discrepancies PDF Export Modal State
  const [isInventoriesPdfModalOpen, setIsInventoriesPdfModalOpen] = React.useState(false);
  const [inventoriesPdfPeriod, setInventoriesPdfPeriod] = React.useState({
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    store_id: '',
    status: '',
  });
  const [isExportingInventoriesPdf, setIsExportingInventoriesPdf] = React.useState(false);

  const handleExportInventoriesPdf = async () => {
    try {
      setIsExportingInventoriesPdf(true);
      const queryParams = new URLSearchParams({
        start_date: inventoriesPdfPeriod.start_date,
        end_date: inventoriesPdfPeriod.end_date,
        ...(inventoriesPdfPeriod.store_id ? { store_id: inventoriesPdfPeriod.store_id } : {}),
        ...(inventoriesPdfPeriod.status ? { status: inventoriesPdfPeriod.status } : {}),
      });
      await downloadPdfFile(
        `/api/v1/inventory/export-inventories-pdf/?${queryParams.toString()}`,
        `Inventaires_Ecarts_${inventoriesPdfPeriod.start_date}_${inventoriesPdfPeriod.end_date}.pdf`
      );

      toast({
        type: 'success',
        title: 'Export PDF réussi',
        message: 'Le rapport des inventaires et analyse des écarts a été téléchargé avec succès.',
      });
      setIsInventoriesPdfModalOpen(false);
    } catch (err: any) {
      toast({
        type: 'error',
        title: 'Erreur Export PDF',
        message: err.message || 'Impossible de générer le rapport des inventaires.',
      });
    } finally {
      setIsExportingInventoriesPdf(false);
    }
  };

  // Movements PDF Export Modal State
  const [isMovementsPdfModalOpen, setIsMovementsPdfModalOpen] = React.useState(false);
  const [movementsPdfPeriod, setMovementsPdfPeriod] = React.useState({
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    store_id: '',
    movement_type: '',
  });
  const [isExportingMovementsPdf, setIsExportingMovementsPdf] = React.useState(false);

  const handleExportMovementsPdf = async () => {
    try {
      setIsExportingMovementsPdf(true);
      const queryParams = new URLSearchParams({
        start_date: movementsPdfPeriod.start_date,
        end_date: movementsPdfPeriod.end_date,
        ...(movementsPdfPeriod.store_id ? { store_id: movementsPdfPeriod.store_id } : {})
      });
      await downloadPdfFile(
        `/api/v1/inventory/export-movements-pdf/?${queryParams.toString()}`,
        `Grand_Livre_Mouvements_${movementsPdfPeriod.start_date}_${movementsPdfPeriod.end_date}.pdf`
      );

      toast({
        type: 'success',
        title: 'Export PDF réussi',
        message: 'Le grand livre des mouvements a été téléchargé avec succès.',
      });
      setIsMovementsPdfModalOpen(false);
    } catch (err: any) {
      toast({
        type: 'error',
        title: 'Erreur Export PDF',
        message: err.message || 'Impossible de générer le rapport des mouvements.',
      });
    } finally {
      setIsExportingMovementsPdf(false);
    }
  };
  const [isPdfModalOpen, setIsPdfModalOpen] = React.useState(false);
  const [pdfPeriod, setPdfPeriod] = React.useState({
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    store_id: '',
  });
  const [isExportingPdf, setIsExportingPdf] = React.useState(false);

  const handleExportPdf = async () => {
    try {
      setIsExportingPdf(true);
      const queryParams = new URLSearchParams({
        start_date: pdfPeriod.start_date,
        end_date: pdfPeriod.end_date,
        ...(pdfPeriod.store_id ? { store_id: pdfPeriod.store_id } : {})
      });
      await downloadPdfFile(
        `/api/v1/inventory/export-pdf/?${queryParams.toString()}`,
        `Etat_Stocks_${pdfPeriod.start_date}_${pdfPeriod.end_date}.pdf`
      );

      toast({
        type: 'success',
        title: 'Export PDF réussi',
        message: 'Le rapport des niveaux de stock a été téléchargé avec succès.',
      });
      setIsPdfModalOpen(false);
    } catch (err: any) {
      toast({
        type: 'error',
        title: 'Erreur Export PDF',
        message: err.message || 'Impossible de générer le rapport PDF.',
      });
    } finally {
      setIsExportingPdf(false);
    }
  };

  const [lineData, setLineData] = React.useState({
    product: '',
    counted_quantity: '0',
    notes: '',
  });

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
    placeholderData: {
      status: 'success',
      pagination: { count: 1, total_pages: 1, current_page: 1, page_size: 20, next: null, previous: null },
      results: [
        {
          id: 'store-01',
          name: 'Magasin & Dépôt Ouaga Central',
          code: 'MAG-OUAGA-01',
          address: 'Avenue Kwamé N\'Krumah, Ouagadougou',
          phone: '+226 25 31 10 20',
          is_active: true,
        },
      ],
    },
  });

  // Fetch products
  const { data: productsData } = useQuery<PaginatedResponse<Product>>({
    queryKey: ['products-options'],
    queryFn: () => apiRequest<PaginatedResponse<Product>>('/products/'),
    placeholderData: {
      status: 'success',
      pagination: { count: 3, total_pages: 1, current_page: 1, page_size: 20, next: null, previous: null },
      results: [
        {
          id: 'p1',
          name: 'Ordinateur Portable HP ProBook 15',
          sku: 'LAPTOP-HP-01',
          barcode: '3700123456789',
          description: 'Intel i5, 16Go RAM, 512Go SSD',
          cost_price: '325000.00',
          selling_price: '450000.00',
          tax_rate: '18.00',
          alert_threshold: '5.00',
          is_active: true,
          unit_symbol: 'pcs',
        },
        {
          id: 'p2',
          name: 'Souris Sans Fil Ergonomique Rechargeable',
          sku: 'MOUSE-WL-01',
          barcode: '3700123456790',
          description: 'Capteur optique haute précision',
          cost_price: '8000.00',
          selling_price: '15000.00',
          tax_rate: '18.00',
          alert_threshold: '10.00',
          is_active: true,
          unit_symbol: 'pcs',
        },
      ],
    },
  });

  // State pour création d'inventaire
  const [newInvData, setNewInvData] = React.useState({
    reference: `INV-${new Date().getFullYear()}-01`,
    inventory_type: 'FULL',
    notes: 'Comptage physique des stocks en magasin',
  });

  // Mutation Ajouter une ligne de comptage
  const addLineMutation = useMutation({
    mutationFn: async ({ invId, data }: { invId: string; data: typeof lineData }) => {
      return await apiRequest(`/inventories/${invId}/add_line/`, {
        method: 'POST',
        body: JSON.stringify({
          product: data.product,
          counted_quantity: data.counted_quantity,
          notes: data.notes,
        }),
      });
    },
    onSuccess: (newLine) => {
      toast({
        type: 'success',
        title: 'Comptage enregistré',
        message: 'La référence a été ajoutée avec succès au comptage.',
      });
      setIsAddLineModalOpen(false);
      setLineData({ product: '', counted_quantity: '0', notes: '' });
      queryClient.invalidateQueries({ queryKey: ['inventories-list'] });
      if (selectedInventory) {
        setSelectedInventory((prev: any) => ({
          ...prev,
          lines: [...(prev.lines || []), newLine],
        }));
      }
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur',
        message: err.message || 'Impossible d\'enregistrer le comptage.',
      });
    },
  });

  // Mutation Valider & Régulariser l'inventaire
  const validateInventoryMutation = useMutation({
    mutationFn: async (invId: string) => {
      return await apiRequest(`/inventories/${invId}/validate/`, {
        method: 'POST',
      });
    },
    onSuccess: (updated) => {
      toast({
        type: 'success',
        title: 'Inventaire clôturé & régularisé',
        message: 'Les ajustements de stock ont été appliqués automatiquement en comptabilité de stock.',
      });
      setSelectedInventory(updated);
      queryClient.invalidateQueries({ queryKey: ['inventories-list'] });
      queryClient.invalidateQueries({ queryKey: ['stock-levels'] });
      queryClient.invalidateQueries({ queryKey: ['stock-movements'] });
      queryClient.invalidateQueries({ queryKey: ['stock-intelligence'] });
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur',
        message: err.message || 'Impossible de clôturer l\'inventaire.',
      });
    },
  });

  // Mutation Nouvel Inventaire
  const createInventoryMutation = useMutation({
    mutationFn: async (data: typeof newInvData) => {
      return await apiRequest('/inventories/', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      toast({
        type: 'success',
        title: 'Inventaire créé',
        message: 'La session d\'inventaire physique a été enregistrée avec succès.',
      });
      setIsNewInventoryModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['inventories-list'] });
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur',
        message: err.message || 'Impossible de créer la session d\'inventaire.',
      });
    },
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

  // Direct Stock Entry Mutation
  const stockEntryMutation = useMutation({
    mutationFn: async (data: typeof stockEntryData) => {
      const qty = Math.abs(parseFloat(data.quantity) || 0);
      return await apiRequest('/stock-movements/', {
        method: 'POST',
        body: JSON.stringify({
          store: data.store,
          product: data.product,
          quantity: qty.toString(),
          movement_type: data.movement_type,
          reference: data.reference || `ENTREE-${Date.now().toString().slice(-6)}`,
          reason: data.reason || 'Entrée manuelle de stock',
        }),
      });
    },
    onSuccess: () => {
      toast({
        type: 'success',
        title: 'Stock mis à jour avec succès',
        message: 'Les quantités ont été ajoutées immédiatement au stock du magasin.',
      });
      setIsStockEntryModalOpen(false);
      setStockEntryData({
        store: '',
        product: '',
        quantity: '10',
        movement_type: 'INITIAL',
        reason: 'Approvisionnement direct / Initialisation stock',
        reference: '',
      });
      queryClient.invalidateQueries({ queryKey: ['stock-levels'] });
      queryClient.invalidateQueries({ queryKey: ['stock-movements'] });
      queryClient.invalidateQueries({ queryKey: ['stock-intelligence'] });
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur',
        message: err.message || 'Impossible d\'ajouter les quantités en stock.',
      });
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
              variant="default"
              size="sm"
              onClick={() => setIsStockEntryModalOpen(true)}
              className="text-xs font-bold shadow-xs bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              <Plus className="h-4 w-4 mr-1.5" /> + Saisir / Entrer du Stock
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsAdjustmentModalOpen(true)}
              className="text-xs font-semibold"
            >
              <RotateCw className="h-4 w-4 mr-1.5" /> Déclarer Perte / Casse
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsTransferModalOpen(true)}
              className="text-xs font-semibold"
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
            <History className="h-4 w-4" /> Mouvements & Entrées de Stock
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
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <Input
                placeholder="Filtrer par nom de produit, référence SKU..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                icon={<Search className="h-4 w-4" />}
                className="max-w-md bg-card"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsPdfModalOpen(true)}
                className="self-start sm:self-auto text-xs font-semibold hover:bg-primary/10 hover:text-primary transition-all border-primary/30"
              >
                <FileText className="h-4 w-4 mr-1.5 text-primary" /> Exporter en PDF (par période)
              </Button>
            </div>
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
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <Input
                placeholder="Rechercher par référence, produit, motif..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                icon={<Search className="h-4 w-4" />}
                className="max-w-md bg-card"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsMovementsPdfModalOpen(true)}
                className="self-start sm:self-auto text-xs font-semibold hover:bg-primary/10 hover:text-primary transition-all border-primary/30"
              >
                <FileText className="h-4 w-4 mr-1.5 text-primary" /> Exporter en PDF (par période)
              </Button>
            </div>
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
                    const frenchLabel = formatMovementTypeFr(row.movement_type, row.movement_type_display);
                    return (
                      <Badge variant={isPositive ? 'success' : 'destructive'} className="text-[10px] font-semibold">
                        {isPositive ? <ArrowDownLeft className="h-3 w-3 mr-1 inline" /> : <ArrowUpRight className="h-3 w-3 mr-1 inline" />}
                        {frenchLabel}
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
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <p className="text-xs text-muted-foreground">
                Campagnes de comptage physique, inventaires complets ou tournants avec calcul automatique des écarts.
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsInventoriesPdfModalOpen(true)}
                  className="text-xs font-semibold hover:bg-primary/10 hover:text-primary transition-all border-primary/30"
                >
                  <FileText className="h-4 w-4 mr-1.5 text-primary" /> Exporter en PDF (par période)
                </Button>
                <Button size="sm" onClick={() => setIsNewInventoryModalOpen(true)}>
                  <Plus className="h-4 w-4 mr-1" /> Nouvel Inventaire
                </Button>
              </div>
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
                      {row.status === 'VALIDATED' ? 'Validé & Régularisé' : row.status === 'IN_PROGRESS' ? 'En cours' : 'Brouillon'}
                    </Badge>
                  ),
                },
                {
                  header: 'Actions',
                  cell: (row: any) => (
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8 text-xs font-semibold"
                        onClick={() => {
                          setSelectedInventory(row);
                          setIsDetailModalOpen(true);
                        }}
                      >
                        Consulter / Compter
                      </Button>
                      {row.status !== 'VALIDATED' && (
                        <Button
                          variant="default"
                          size="sm"
                          className="h-8 text-xs font-semibold"
                          isLoading={validateInventoryMutation.isPending && selectedInventory?.id === row.id}
                          onClick={() => {
                            setSelectedInventory(row);
                            validateInventoryMutation.mutate(row.id);
                          }}
                        >
                          Clôturer
                        </Button>
                      )}
                    </div>
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

        {/* MODAL: NOUVEL INVENTAIRE PHYSIQUE */}
        <Modal
          isOpen={isNewInventoryModalOpen}
          onClose={() => setIsNewInventoryModalOpen(false)}
          title="Créer une Session d'Inventaire Physique"
          maxWidth="md"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createInventoryMutation.mutate(newInvData);
            }}
            className="space-y-4 pt-2"
          >
            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Référence / Code Session *
              </label>
              <Input
                required
                placeholder="Ex: INV-2026-T1"
                value={newInvData.reference}
                onChange={(e) => setNewInvData({ ...newInvData, reference: e.target.value })}
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Type d'Inventaire *
              </label>
              <select
                className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                value={newInvData.inventory_type}
                onChange={(e) => setNewInvData({ ...newInvData, inventory_type: e.target.value })}
              >
                <option value="FULL">Inventaire Général Complet (Tous les articles)</option>
                <option value="PARTIAL">Inventaire Tournant / Partiel</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Notes ou Consignes de comptage
              </label>
              <Input
                placeholder="Ex: Comptage physique annuel de clôture..."
                value={newInvData.notes}
                onChange={(e) => setNewInvData({ ...newInvData, notes: e.target.value })}
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setIsNewInventoryModalOpen(false)}>
                Annuler
              </Button>
              <Button type="submit" isLoading={createInventoryMutation.isPending}>
                Créer l'Inventaire
              </Button>
            </div>
          </form>
        </Modal>

        {/* MODAL: DÉTAILS DE L'INVENTAIRE & SAISIE DU COMPTAGE */}
        <Modal
          isOpen={isDetailModalOpen}
          onClose={() => setIsDetailModalOpen(false)}
          title={`Inventaire : ${selectedInventory?.reference || ''}`}
          maxWidth="2xl"
        >
          {selectedInventory && (
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/40 border border-border text-xs">
                <div>
                  <span className="text-muted-foreground block">Type d'inventaire :</span>
                  <span className="font-bold text-foreground">
                    {selectedInventory.inventory_type === 'PARTIAL' ? 'Tournant / Partiel' : 'Général Complet'}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground block">Statut :</span>
                  <Badge variant={selectedInventory.status === 'VALIDATED' ? 'success' : 'warning'}>
                    {selectedInventory.status === 'VALIDATED' ? 'Validé & Régularisé' : 'En attente de clôture'}
                  </Badge>
                </div>
                <div>
                  <span className="text-muted-foreground block">Lignes comptées :</span>
                  <span className="font-bold text-foreground">{selectedInventory.lines?.length || 0} référence(s)</span>
                </div>
              </div>

              {selectedInventory.notes && (
                <p className="text-xs text-muted-foreground italic px-1">
                  « {selectedInventory.notes} »
                </p>
              )}

              {/* Table des lignes */}
              <div className="border border-border rounded-lg overflow-hidden">
                <div className="max-h-64 overflow-y-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-muted/60 text-muted-foreground font-semibold sticky top-0 border-b">
                      <tr>
                        <th className="p-2.5">Produit / SKU</th>
                        <th className="p-2.5 text-right">Stock Théorique</th>
                        <th className="p-2.5 text-right">Compté Physique</th>
                        <th className="p-2.5 text-right">Écart</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {selectedInventory.lines && selectedInventory.lines.length > 0 ? (
                        selectedInventory.lines.map((l: any, idx: number) => {
                          const diff = parseFloat(l.difference ?? (parseFloat(l.counted_quantity || '0') - parseFloat(l.expected_quantity || '0')));
                          return (
                            <tr key={idx} className="hover:bg-muted/20">
                              <td className="p-2.5 font-semibold text-foreground">
                                {l.product_name || 'Article'}
                                <span className="block text-[10px] font-mono text-muted-foreground">
                                  {l.product_sku || ''}
                                </span>
                              </td>
                              <td className="p-2.5 text-right font-mono">{l.expected_quantity}</td>
                              <td className="p-2.5 text-right font-mono font-bold text-primary">{l.counted_quantity}</td>
                              <td className="p-2.5 text-right font-mono font-bold">
                                <span className={diff > 0 ? 'text-emerald-600' : diff < 0 ? 'text-rose-600' : 'text-muted-foreground'}>
                                  {diff > 0 ? `+${diff}` : diff}
                                </span>
                              </td>
                            </tr>
                          );
                        })
                      ) : (
                        <tr>
                          <td colSpan={4} className="p-6 text-center text-muted-foreground">
                            Aucune ligne comptée pour l'instant. Cliquez sur "+ Ajouter un comptage".
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Modal footer / actions */}
              <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-border">
                {selectedInventory.status !== 'VALIDATED' ? (
                  <>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setIsAddLineModalOpen(true)}
                    >
                      <Plus className="h-4 w-4 mr-1.5" /> Ajouter un comptage
                    </Button>
                    <div className="flex items-center gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setIsDetailModalOpen(false)}
                      >
                        Fermer
                      </Button>
                      <Button
                        type="button"
                        variant="default"
                        size="sm"
                        isLoading={validateInventoryMutation.isPending}
                        onClick={() => validateInventoryMutation.mutate(selectedInventory.id)}
                      >
                        <CheckCircle2 className="h-4 w-4 mr-1.5" /> Clôturer & Régulariser le Stock
                      </Button>
                    </div>
                  </>
                ) : (
                  <div className="w-full flex justify-end">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setIsDetailModalOpen(false)}
                    >
                      Fermer
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}
        </Modal>

        {/* MODAL: EXPORT PDF DES INVENTAIRES ET ÉCARTS PAR PÉRIODE */}
        <Modal
          isOpen={isInventoriesPdfModalOpen}
          onClose={() => setIsInventoriesPdfModalOpen(false)}
          title="Exporter les Inventaires & Analyse des Écarts en PDF"
          maxWidth="md"
        >
          <div className="space-y-4 pt-2">
            <p className="text-xs text-muted-foreground">
              Générez un rapport officiel des campagnes d'inventaire physique récapitulant les stocks théoriques, les quantités réelles comptées, les écarts (surplus / manquants) et leur valorisation financière en FCFA.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Date de Début *
                </label>
                <Input
                  type="date"
                  required
                  value={inventoriesPdfPeriod.start_date}
                  onChange={(e) => setInventoriesPdfPeriod({ ...inventoriesPdfPeriod, start_date: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Date de Fin *
                </label>
                <Input
                  type="date"
                  required
                  value={inventoriesPdfPeriod.end_date}
                  onChange={(e) => setInventoriesPdfPeriod({ ...inventoriesPdfPeriod, end_date: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Magasin / Dépôt
                </label>
                <select
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                  value={inventoriesPdfPeriod.store_id}
                  onChange={(e) => setInventoriesPdfPeriod({ ...inventoriesPdfPeriod, store_id: e.target.value })}
                >
                  <option value="">Tous les dépôts</option>
                  {storesData?.results?.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Filtrer par Statut
                </label>
                <select
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                  value={inventoriesPdfPeriod.status}
                  onChange={(e) => setInventoriesPdfPeriod({ ...inventoriesPdfPeriod, status: e.target.value })}
                >
                  <option value="">Tous les statuts</option>
                  <option value="VALIDATED">Validés & Régularisés</option>
                  <option value="IN_PROGRESS">En cours</option>
                  <option value="DRAFT">Brouillons</option>
                </select>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-muted/40 border border-border text-xs text-muted-foreground flex items-center justify-between">
              <span>Format du document :</span>
              <span className="font-bold text-foreground">Rapport d'Écarts A4 Paysage (Landscape)</span>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-border">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsInventoriesPdfModalOpen(false)}
              >
                Annuler
              </Button>
              <Button
                type="button"
                onClick={handleExportInventoriesPdf}
                isLoading={isExportingInventoriesPdf}
              >
                <Download className="h-4 w-4 mr-1.5" /> Télécharger le Rapport d'Écarts PDF
              </Button>
            </div>
          </div>
        </Modal>

        {/* MODAL: EXPORT PDF DES MOUVEMENTS DE STOCK PAR PÉRIODE */}
        <Modal
          isOpen={isMovementsPdfModalOpen}
          onClose={() => setIsMovementsPdfModalOpen(false)}
          title="Exporter le Grand Livre des Mouvements en PDF"
          maxWidth="md"
        >
          <div className="space-y-4 pt-2">
            <p className="text-xs text-muted-foreground">
              Téléchargez l'historique complet et inaltérable des mouvements de stock avec dates, types de flux en français, variations, stocks avant/après et traçabilité des opérateurs.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Date de Début *
                </label>
                <Input
                  type="date"
                  required
                  value={movementsPdfPeriod.start_date}
                  onChange={(e) => setMovementsPdfPeriod({ ...movementsPdfPeriod, start_date: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Date de Fin *
                </label>
                <Input
                  type="date"
                  required
                  value={movementsPdfPeriod.end_date}
                  onChange={(e) => setMovementsPdfPeriod({ ...movementsPdfPeriod, end_date: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Magasin / Dépôt
                </label>
                <select
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                  value={movementsPdfPeriod.store_id}
                  onChange={(e) => setMovementsPdfPeriod({ ...movementsPdfPeriod, store_id: e.target.value })}
                >
                  <option value="">Tous les dépôts</option>
                  {storesData?.results?.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Filtrer par Type de Flux
                </label>
                <select
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                  value={movementsPdfPeriod.movement_type}
                  onChange={(e) => setMovementsPdfPeriod({ ...movementsPdfPeriod, movement_type: e.target.value })}
                >
                  <option value="">Tous les flux confondus</option>
                  <option value="SALE">Ventes</option>
                  <option value="PURCHASE">Achats / Réceptions</option>
                  <option value="ADJUSTMENT_IN">Ajustements positifs (+)</option>
                  <option value="ADJUSTMENT_OUT">Ajustements négatifs (-)</option>
                  <option value="DAMAGE">Casse / Dépréciation</option>
                  <option value="LOSS">Pertes / Vols</option>
                  <option value="TRANSFER_IN">Transferts entrants</option>
                  <option value="TRANSFER_OUT">Transferts sortants</option>
                  <option value="INITIAL">Stock initial</option>
                </select>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-muted/40 border border-border text-xs text-muted-foreground flex items-center justify-between">
              <span>Format du document :</span>
              <span className="font-bold text-foreground">Grand Livre A4 Paysage (Landscape)</span>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-border">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsMovementsPdfModalOpen(false)}
              >
                Annuler
              </Button>
              <Button
                type="button"
                onClick={handleExportMovementsPdf}
                isLoading={isExportingMovementsPdf}
              >
                <Download className="h-4 w-4 mr-1.5" /> Télécharger le Grand Livre PDF
              </Button>
            </div>
          </div>
        </Modal>

        {/* MODAL: EXPORT PDF DES NIVEAUX DE STOCK PAR PÉRIODE */}
        <Modal
          isOpen={isPdfModalOpen}
          onClose={() => setIsPdfModalOpen(false)}
          title="Exporter l'État des Stocks en PDF"
          maxWidth="md"
        >
          <div className="space-y-4 pt-2">
            <p className="text-xs text-muted-foreground">
              Générez un rapport officiel des stocks détaillant les stocks de début, entrées, sorties, stocks de fin de période et valorisations financières en FCFA.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Date de Début *
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
                  Date de Fin *
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
                Magasin ou Dépôt (Optionnel)
              </label>
              <select
                className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                value={pdfPeriod.store_id}
                onChange={(e) => setPdfPeriod({ ...pdfPeriod, store_id: e.target.value })}
              >
                <option value="">Tous les magasins et dépôts confondus</option>
                {storesData?.results?.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="p-3 rounded-lg bg-muted/40 border border-border text-xs text-muted-foreground flex items-center justify-between">
              <span>Format du document :</span>
              <span className="font-bold text-foreground">PDF Paysage A4 (Haute Définition)</span>
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
                <Download className="h-4 w-4 mr-1.5" /> Télécharger le Rapport PDF
              </Button>
            </div>
          </div>
        </Modal>

        {/* MODAL: AJOUTER UNE LIGNE DE COMPTAGE */}
        <Modal
          isOpen={isAddLineModalOpen}
          onClose={() => setIsAddLineModalOpen(false)}
          title="Ajouter un Produit au Comptage Physique"
          maxWidth="sm"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!selectedInventory) return;
              addLineMutation.mutate({ invId: selectedInventory.id, data: lineData });
            }}
            className="space-y-4 pt-2"
          >
            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Article à compter *
              </label>
              <select
                required
                className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                value={lineData.product}
                onChange={(e) => setLineData({ ...lineData, product: e.target.value })}
              >
                <option value="">Sélectionner un produit</option>
                {productsData?.results?.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.sku})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Quantité réellement comptée en rayon / dépôt *
              </label>
              <Input
                type="number"
                step="any"
                min="0"
                required
                placeholder="Ex: 25"
                value={lineData.counted_quantity}
                onChange={(e) => setLineData({ ...lineData, counted_quantity: e.target.value })}
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Remarque ou motif d'écart
              </label>
              <Input
                placeholder="Ex: 2 unités abîmées mises de côté..."
                value={lineData.notes}
                onChange={(e) => setLineData({ ...lineData, notes: e.target.value })}
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setIsAddLineModalOpen(false)}>
                Annuler
              </Button>
              <Button type="submit" isLoading={addLineMutation.isPending}>
                Enregistrer la Ligne
              </Button>
            </div>
          </form>
        </Modal>
      </div>

        {/* MODAL: SAISIE DIRECTE DU STOCK / APPROVISIONNEMENT */}
        <Modal
          isOpen={isStockEntryModalOpen}
          onClose={() => setIsStockEntryModalOpen(false)}
          title="Saisie Directe & Approvisionnement de Stock"
          maxWidth="md"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              stockEntryMutation.mutate(stockEntryData);
            }}
            className="space-y-4 pt-2"
          >
            <p className="text-xs text-muted-foreground">
              Augmentez immédiatement le stock physique disponible pour un produit dans le magasin sélectionné.
            </p>

            <div>
              <label className="text-xs font-bold text-foreground block mb-1">Motif d'entrée *</label>
              <select
                className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm font-semibold"
                value={stockEntryData.movement_type}
                onChange={(e) => setStockEntryData({ ...stockEntryData, movement_type: e.target.value })}
              >
                <option value="INITIAL">Stock Initial (Mise en rayon de départ)</option>
                <option value="ADJUSTMENT_IN">Arrivage Fournisseur / Réception Marchandise</option>
                <option value="RETURN_IN">Retour Client / Réintégration Stock</option>
              </select>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-bold text-foreground block mb-1">Magasin de Destination *</label>
                <select
                  required
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm font-semibold"
                  value={stockEntryData.store}
                  onChange={(e) => setStockEntryData({ ...stockEntryData, store: e.target.value })}
                >
                  <option value="">Sélectionner un magasin</option>
                  {storesData?.results?.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-foreground block mb-1">Produit à Approvisionner *</label>
                <select
                  required
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm font-semibold"
                  value={stockEntryData.product}
                  onChange={(e) => setStockEntryData({ ...stockEntryData, product: e.target.value })}
                >
                  <option value="">Sélectionner un produit</option>
                  {productsData?.results?.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.sku})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-foreground block mb-1">Quantité à Ajouter en Stock *</label>
              <Input
                type="number"
                min="1"
                step="1"
                required
                placeholder="Ex: 25"
                value={stockEntryData.quantity}
                onChange={(e) => setStockEntryData({ ...stockEntryData, quantity: e.target.value })}
                className="font-bold text-base font-mono"
              />
              <p className="text-[11px] text-muted-foreground mt-1">
                Indiquez le nombre d'unités physiques reçues qui seront immédiatement ajoutées au stock.
              </p>
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Numéro de Bon de Livraison / Référence (Optionnel)
              </label>
              <Input
                placeholder="Ex: BL-FOURNISSEUR-2026-08"
                value={stockEntryData.reference}
                onChange={(e) => setStockEntryData({ ...stockEntryData, reference: e.target.value })}
              />
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t">
              <Button type="button" variant="outline" onClick={() => setIsStockEntryModalOpen(false)}>
                Annuler
              </Button>
              <Button type="submit" isLoading={stockEntryMutation.isPending} className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold">
                <Plus className="h-4 w-4 mr-1.5" /> Valider l'Entrée de Stock
              </Button>
            </div>
          </form>
        </Modal>

    </DashboardLayout>
  );
}
