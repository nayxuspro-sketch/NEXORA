'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Modal } from '@/components/ui/modal';
import { KpiCard } from '@/components/ui/kpi-card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { SimpleBarChart } from '@/components/ui/simple-chart';
import { useToast } from '@/components/ui/toast';
import { apiRequest } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';
import { downloadPdfFile } from '@/lib/pdf-export';
import {
  TrendingUp,
  PieChart,
  Coins,
  BarChart3,
  Lightbulb,
  Building2,
  Users,
  Layers,
  ShoppingCart,
  Calendar,
  Sparkles,
  ArrowUpRight,
  ArrowDownRight,
  ShieldAlert,
  Wallet,
  FileText,
  Download
} from 'lucide-react';

export default function ReportsPage() {
  const { toast } = useToast();
  const [selectedView, setSelectedView] = React.useState<'executive' | 'manager' | 'sales' | 'stock' | 'cashier'>('executive');
  const [days, setDays] = React.useState<number>(30);
  // BI PDF Export Modal State
  const [isBiPdfModalOpen, setIsBiPdfModalOpen] = React.useState(false);
  const [pdfPeriodDays, setPdfPeriodDays] = React.useState<number>(days);
  const [isExportingPdf, setIsExportingPdf] = React.useState(false);

  React.useEffect(() => {
    setPdfPeriodDays(days);
  }, [days]);

  const handleExportBiPdf = async () => {
    try {
      setIsExportingPdf(true);
      const queryParams = new URLSearchParams({
        days: pdfPeriodDays.toString(),
        view: selectedView,
      });
      await downloadPdfFile(
        `/api/v1/reports/export-bi-pdf/?${queryParams.toString()}`,
        `Rapport_BI_Decision_${pdfPeriodDays}j_${new Date().toISOString().split('T')[0]}.pdf`
      );

      toast({
        type: 'success',
        title: 'Rapport BI Téléchargé',
        message: `Le rapport décisionnel (${pdfPeriodDays} jours) a été téléchargé en PDF.`,
      });
      setIsBiPdfModalOpen(false);
    } catch (err: any) {
      console.error('Erreur export BI PDF:', err);
      toast({
        type: 'error',
        title: 'Erreur Export PDF',
        message: err.message || 'Impossible d\'exporter le rapport BI en PDF.',
      });
    } finally {
      setIsExportingPdf(false);
    }
  };

  const { data: biData, isLoading } = useQuery<{
    requested_view: string;
    period_days: number;
    insights_explanation: string[];
    sales_overview: {
      current_revenue: string;
      previous_revenue: string;
      growth_pct: string;
      sales_count: number;
      avg_basket: string;
      tax_collected: string;
      discounts_granted: string;
    };
    profitability: {
      gross_revenue: string;
      total_cost_of_goods: string;
      estimated_profit: string;
      margin_rate_pct: string;
    };
    stock_health: {
      total_cost_valuation: string;
      total_retail_valuation: string;
      total_units: string;
      critical_items_count: number;
    };
    customer_insights: {
      total_customer_accounts: number;
      active_buying_customers: number;
      customer_retention_rate: string;
    };
    top_products: Array<{ name: string; sku: string; qty: string; revenue: string }>;
    categories: Array<{ category: string; revenue: string; qty: string }>;
    sellers_performance: Array<{ seller: string; revenue: string; transactions: number }>;
    stores_performance: Array<{ store: string; revenue: string }>;
  }>({
    queryKey: ['bi-analytics', selectedView, days],
    queryFn: () => apiRequest(`/reports/bi-analytics/?view=${selectedView}&days=${days}`),
    placeholderData: {
      requested_view: 'executive',
      period_days: 30,
      insights_explanation: [
        "Le chiffre d'affaires progresse de 14.2%, principalement porté par une hausse du panier moyen passé de 185 000 FCFA à 245 000 FCFA.",
        "La performance commerciale est fortement consolidée par 'Ordinateur Portable HP ProBook 15', qui génère à lui seul 48% des recettes analysées.",
        "Attention : 2 référence(s) sont sous le seuil d'alerte, présentant un risque direct de rupture."
      ],
      sales_overview: {
        current_revenue: '24850000.00',
        previous_revenue: '21760000.00',
        growth_pct: '14.2',
        sales_count: 142,
        avg_basket: '175000.00',
        tax_collected: '4473000.00',
        discounts_granted: '350000.00',
      },
      profitability: {
        gross_revenue: '24850000.00',
        total_cost_of_goods: '16200000.00',
        estimated_profit: '8650000.00',
        margin_rate_pct: '34.8',
      },
      stock_health: {
        total_cost_valuation: '28500000.00',
        total_retail_valuation: '42800000.00',
        total_units: '1840.00',
        critical_items_count: 2,
      },
      customer_insights: {
        total_customer_accounts: 38,
        active_buying_customers: 24,
        customer_retention_rate: '63.2%',
      },
      top_products: [
        { name: 'Ordinateur Portable HP ProBook 15', sku: 'LAPTOP-HP-01', qty: '28', revenue: '12600000.00' },
        { name: 'Écran Dell 24 Pouces Full HD', sku: 'DISP-DELL-24', qty: '35', revenue: '3850000.00' },
        { name: 'Clavier USB Bureautique AZERTY', sku: 'KEYB-USB-01', qty: '80', revenue: '1000000.00' },
      ],
      categories: [
        { category: 'Informatique & PC', revenue: '15500000.00', qty: '46' },
        { category: 'Périphériques', revenue: '6250000.00', qty: '92' },
        { category: 'Accessoires', revenue: '3100000.00', qty: '120' },
      ],
      sellers_performance: [
        { seller: 'vendeur.ouaga@nexora-bf.com', revenue: '14800000.00', transactions: 84 },
        { seller: 'vendeur.bobo@nexora-bf.com', revenue: '10050000.00', transactions: 58 },
      ],
      stores_performance: [
        { store: 'Magasin Ouaga Central', revenue: '16800000.00' },
        { store: 'Dépôt Bobo-Dioulasso', revenue: '8050000.00' },
      ],
    },
  });

  const categoryBarData = biData?.categories?.map((c) => ({
    label: c.category.slice(0, 10),
    value: Math.round(parseFloat(c.revenue)),
  })) || [];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header & Controls */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground flex items-center gap-2">
              <BarChart3 className="h-7 w-7 text-primary" /> Business Intelligence & Décision
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
              Cycle analytique : <span className="font-semibold text-primary">Données → Information → Compréhension → Décision</span>
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Export PDF Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsBiPdfModalOpen(true)}
              className="text-xs font-semibold border-primary/30 text-primary hover:bg-primary/10 transition-all shadow-xs"
            >
              <FileText className="h-4 w-4 mr-1.5 text-primary" /> Exporter Rapport BI en PDF
            </Button>

            {/* Timeframe switch */}
            <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-xl border self-start md:self-auto text-xs">
              {[7, 30, 90].map((d) => (
                <button
                  key={d}
                  onClick={() => setDays(d)}
                  className={`px-3 py-1.5 rounded-lg font-bold transition-all ${
                    days === d
                      ? 'bg-primary text-primary-foreground shadow-xs'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {d === 7 ? '7 jours' : d === 30 ? '30 jours' : 'Trimestre'}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Multi-Role Dashboard Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-border text-xs sm:text-sm font-semibold">
          {[
            { id: 'executive', label: 'Dashboard Direction', icon: Building2 },
            { id: 'manager', label: 'Gérant de Magasin', icon: Wallet },
            { id: 'sales', label: 'Performance Commerciale', icon: Users },
            { id: 'stock', label: 'Rotation & Logistique', icon: Layers },
            { id: 'cashier', label: 'Point de Vente & Caisses', icon: ShoppingCart },
          ].map((tab) => {
            const Icon = tab.icon;
            const isSelected = selectedView === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setSelectedView(tab.id as any)}
                className={`px-3.5 py-2.5 rounded-lg flex items-center gap-2 transition-all shrink-0 ${
                  isSelected
                    ? 'bg-card border shadow-xs text-primary font-bold'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
              >
                <Icon className={`h-4 w-4 ${isSelected ? 'text-primary' : 'text-muted-foreground'}`} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* DATA-DRIVEN EXPLANATIONS BOX (Ne pas afficher que X, mais expliquer pourquoi) */}
        <Card className="border-primary/30 bg-gradient-to-r from-primary/5 via-blue-500/5 to-transparent shadow-xs">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold flex items-center gap-2 text-primary">
              <Sparkles className="h-4 w-4" /> Analyse Explicative & Facteurs d'Évolution
            </CardTitle>
            <CardDescription className="text-xs">
              Compréhension automatique des variations observées sur les {days} derniers jours
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-xs sm:text-sm pt-1">
            {biData?.insights_explanation?.map((item, i) => (
              <div key={i} className="flex items-start gap-2.5 text-foreground/90 font-medium">
                <Lightbulb className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                <span>{item}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* KPI CARDS GRID */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            title="Chiffre d'Affaires Net"
            value={formatCurrency(biData?.sales_overview.current_revenue || '0')}
            change={`${parseFloat(biData?.sales_overview.growth_pct || '0') >= 0 ? '+' : ''}${biData?.sales_overview.growth_pct}%`}
            changeType={parseFloat(biData?.sales_overview.growth_pct || '0') >= 0 ? 'positive' : 'negative'}
            icon={<TrendingUp className="h-5 w-5" />}
            description={`Vs période précédente: ${formatCurrency(biData?.sales_overview.previous_revenue || '0')}`}
          />
          <KpiCard
            title="Marge Brute Estimée"
            value={formatCurrency(biData?.profitability.estimated_profit || '0')}
            change={`Taux: ${biData?.profitability.margin_rate_pct}%`}
            changeType="positive"
            icon={<Wallet className="h-5 w-5" />}
            description="Revenus moins coût d'achat des marchandises"
          />
          <KpiCard
            title="Panier Moyen"
            value={formatCurrency(biData?.sales_overview.avg_basket || '0')}
            icon={<Coins className="h-5 w-5" />}
            description={`${biData?.sales_overview.sales_count} transactions au total`}
          />
          <KpiCard
            title="Fidélisation Clients"
            value={biData?.customer_insights.customer_retention_rate || '0%'}
            change={`${biData?.customer_insights.active_buying_customers} acheteurs`}
            changeType="positive"
            icon={<Users className="h-5 w-5" />}
            description={`Sur ${biData?.customer_insights.total_customer_accounts} comptes enregistrés`}
          />
        </div>

        {/* MID SECTION: REVENUE BREAKDOWN & TOP PRODUCTS */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Revenue by category */}
          <div className="lg:col-span-2">
            <SimpleBarChart
              title={`Chiffre d'Affaires par Famille de Produits (FCFA) — ${days}j`}
              data={categoryBarData}
              height={220}
            />
          </div>

          {/* Top Selling Products */}
          <Card className="flex flex-col">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold flex items-center justify-between">
                <span>Top Produits Contributeurs</span>
                <Badge variant="outline" className="text-[10px]">Volume</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 divide-y text-xs">
              {biData?.top_products?.map((p, idx) => (
                <div key={idx} className="py-2.5 flex items-center justify-between">
                  <div className="min-w-0 pr-2">
                    <p className="font-bold text-foreground truncate">{p.name}</p>
                    <p className="text-[10px] text-muted-foreground font-mono">{p.sku}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="font-bold text-primary block">{formatCurrency(p.revenue)}</span>
                    <span className="text-[10px] text-muted-foreground">{p.qty} vendus</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* BOTTOM SECTION: SELLERS & STORES PERFORMANCE */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Sellers */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Users className="h-4 w-4 text-primary" /> Performance des Vendeurs / Caissiers
              </CardTitle>
            </CardHeader>
            <CardContent className="divide-y text-xs">
              {biData?.sellers_performance?.map((s, i) => (
                <div key={i} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="font-bold text-foreground">{s.seller}</p>
                    <p className="text-muted-foreground">{s.transactions} ventes validées</p>
                  </div>
                  <span className="text-sm font-black text-foreground">
                    {formatCurrency(s.revenue)}
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Stores */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Building2 className="h-4 w-4 text-primary" /> Contribution par Magasin
              </CardTitle>
            </CardHeader>
            <CardContent className="divide-y text-xs">
              {biData?.stores_performance?.map((st, i) => (
                <div key={i} className="py-3 flex items-center justify-between">
                  <p className="font-bold text-foreground">{st.store}</p>
                  <span className="text-sm font-black text-primary">
                    {formatCurrency(st.revenue)}
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* MODAL: EXPORT RAPPORT BI & DECISION */}
        <Modal
          isOpen={isBiPdfModalOpen}
          onClose={() => setIsBiPdfModalOpen(false)}
          title="Exporter le Rapport Business Intelligence & Décision (PDF)"
          maxWidth="md"
        >
          <div className="space-y-4 pt-2">
            <div className="p-3 rounded-xl bg-primary/10 border border-primary/20 text-xs text-foreground space-y-1">
              <p className="font-bold flex items-center gap-1.5 text-primary">
                <Sparkles className="h-4 w-4" /> Rapport Stratégique de Direction sur 2 Pages :
              </p>
              <ul className="list-disc pl-4 space-y-0.5 text-muted-foreground text-[11px]">
                <li><strong>Page 1 :</strong> Scorecard exécutif (CA net, marges, panier moyen, stocks valorisés), explications diagnostiques et contribution par famille en FCFA.</li>
                <li><strong>Page 2 :</strong> Matrice de rentabilité des produits phares, vitesse d'écoulement et plan d'action d'aide à la décision stratégique.</li>
              </ul>
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Horizon d'Analyse Temporelle *
              </label>
              <select
                className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm font-semibold"
                value={pdfPeriodDays}
                onChange={(e) => setPdfPeriodDays(parseInt(e.target.value))}
              >
                <option value={7}>Semaine Écoulée (7 derniers jours)</option>
                <option value={30}>Mois d'Activité Standard (30 derniers jours)</option>
                <option value={90}>Trimestre Complet (90 derniers jours)</option>
              </select>
            </div>

            <div className="p-3 rounded-lg bg-muted/40 border border-border text-xs text-muted-foreground flex items-center justify-between">
              <span>Format du document :</span>
              <span className="font-bold text-foreground">Document Exécutif A4 Portrait (2 Pages)</span>
            </div>

            <div className="flex flex-col sm:flex-row justify-end gap-2 pt-4 border-t border-border">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsBiPdfModalOpen(false)}
              >
                Annuler
              </Button>
              <a
                href={`/api/v1/reports/export-bi-pdf/?days=${pdfPeriodDays}&view=${selectedView}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center px-4 py-2 rounded-md font-semibold text-xs border border-input bg-background hover:bg-muted text-foreground transition-colors"
                onClick={() => setTimeout(() => setIsBiPdfModalOpen(false), 500)}
              >
                Ouvrir dans un onglet (Direct)
              </a>
              <Button
                type="button"
                onClick={handleExportBiPdf}
                isLoading={isExportingPdf}
              >
                <Download className="h-4 w-4 mr-1.5" /> Télécharger le Rapport BI (PDF)
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </DashboardLayout>
  );
}
