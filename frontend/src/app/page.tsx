'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { KpiCard } from '@/components/ui/kpi-card';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SimpleBarChart } from '@/components/ui/simple-chart';
import { formatCurrency } from '@/lib/utils';
import { apiRequest } from '@/lib/api';
import { DashboardReport } from '@/types';
import {
  TrendingUp,
  ShoppingCart,
  AlertTriangle,
  Wallet,
  ShieldAlert,
  Layers,
  ArrowRight,
  PackagePlus,
  FileSpreadsheet
} from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function DashboardPage() {
  const { data: report, isLoading, isError } = useQuery<DashboardReport>({
    queryKey: ['dashboard-report'],
    queryFn: () => apiRequest<DashboardReport>('/reports/dashboard/?days=30'),
    staleTime: 1000 * 60,
    refetchOnWindowFocus: true,
  });

  const chartData = report?.weekly_chart && report.weekly_chart.length > 0
    ? report.weekly_chart.map((c) => ({
        label: `${c.label} ${c.date || ''}`.trim(),
        value: c.value,
      }))
    : [
        { label: 'J-6', value: 0 },
        { label: 'J-5', value: 0 },
        { label: 'J-4', value: 0 },
        { label: 'J-3', value: 0 },
        { label: 'J-2', value: 0 },
        { label: 'Hier', value: 0 },
        { label: "Aujourd'hui", value: 0 },
      ];

  const salesCount = report?.sales?.count ?? 0;
  const salesTotal = report?.sales?.total_amount ? formatCurrency(report.sales.total_amount) : '0 FCFA';
  const taxCollected = report?.sales?.tax_collected ? formatCurrency(report.sales.tax_collected) : '0 FCFA';
  const marginEst = report?.profitability?.gross_estimate ? formatCurrency(report.profitability.gross_estimate) : '0 FCFA';
  const marginPct = (parseFloat(report?.sales?.total_amount || '0') > 0 && parseFloat(report?.profitability?.gross_estimate || '0') > 0)
    ? `${Math.round((parseFloat(report?.profitability?.gross_estimate || '0') / parseFloat(report?.sales?.total_amount || '1')) * 100)}% de marge`
    : '0% de marge';

  const unitsStocked = report?.inventory?.total_units_stocked
    ? `${Number(report.inventory.total_units_stocked).toLocaleString('fr-FR')} pcs`
    : '0 pcs';

  const alertsCount = report?.inventory?.low_stock_alerts_count ?? 0;

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-7xl mx-auto">
        {/* Niveau 1 : En-tête contextuel & Action primaire claire */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-border/60">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                Tableau de bord
              </h1>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-md bg-primary/10 text-primary border border-primary/20">
                XOF • FCFA
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Synthèse d'activité commerciale en temps réel — Derniers 30 jours
            </p>
          </div>

          {/* Actions principales */}
          <div className="flex items-center gap-3">
            <Link href="/sales">
              <Button variant="outline" size="sm" className="hidden sm:inline-flex text-xs font-medium">
                <FileSpreadsheet className="h-3.5 w-3.5 mr-1.5 text-muted-foreground" />
                Journal des ventes
              </Button>
            </Link>
            <Link href="/pos">
              <Button size="default" className="shadow-xs font-semibold px-5">
                <ShoppingCart className="h-4 w-4 mr-2" />
                Ouvrir la Caisse
                <kbd className="ml-2 hidden sm:inline-flex px-1.5 py-0.5 text-[10px] bg-primary-foreground/20 rounded font-mono">
                  F8
                </kbd>
              </Button>
            </Link>
          </div>
        </div>

        {/* Niveau 2 : Indicateurs Clés Métier */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            title="Chiffre d'Affaires"
            value={salesTotal}
            change={`${salesCount} transaction(s)`}
            changeType="positive"
            icon={<TrendingUp className="h-4 w-4 text-primary" />}
            description={`TVA collectée : ${taxCollected}`}
          />
          <KpiCard
            title="Marge Brute Réalisée"
            value={marginEst}
            change={marginPct}
            changeType="positive"
            icon={<Wallet className="h-4 w-4 text-emerald-600" />}
            description="Revenus nets moins coût de revient"
          />
          <KpiCard
            title="Articles en Stock"
            value={unitsStocked}
            change="Disponibilité immédiate"
            changeType="positive"
            icon={<Layers className="h-4 w-4 text-slate-600" />}
            description="Unités physiques en dépôt"
          />
          <KpiCard
            title="Alertes Rupture"
            value={alertsCount}
            change={alertsCount > 0 ? "Réapprovisionner" : "Stock sain"}
            changeType={alertsCount > 0 ? "negative" : "positive"}
            icon={<AlertTriangle className="h-4 w-4 text-amber-500" />}
            description="Articles sous le seuil critique"
          />
        </div>

        {/* Niveau 3 : Graphique d'activité & Alertes Prioritaires */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Graphique des tendances de ventes */}
          <div className="lg:col-span-2">
            <SimpleBarChart
              title="Activité Hebdomadaire des Ventes (FCFA)"
              data={chartData}
              height={230}
            />
          </div>

          {/* Cartes d'alertes de stock prioritaires */}
          <Card className="flex flex-col shadow-xs border-border/80">
            <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-border/40">
              <div className="flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-amber-500 shrink-0" />
                <CardTitle className="text-sm font-semibold text-foreground">
                  Alertes de Stock
                </CardTitle>
              </div>
              <Badge variant={alertsCount > 0 ? "warning" : "outline"} className="text-[11px] font-semibold">
                {alertsCount} {alertsCount > 1 ? "critiques" : alertsCount === 1 ? "critique" : "en alerte"}
              </Badge>
            </CardHeader>

            <CardContent className="flex-1 flex flex-col justify-between pt-4 space-y-3">
              <div className="space-y-2.5">
                {report?.inventory?.low_stock_items?.length ? (
                  report.inventory.low_stock_items.map((item) => (
                    <div
                      key={item.product_id}
                      className="p-2.5 rounded-lg border border-border/60 bg-muted/20 hover:bg-muted/40 transition-colors flex items-center justify-between gap-3"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-semibold text-foreground truncate">
                          {item.product_name}
                        </p>
                        <p className="text-[11px] text-muted-foreground truncate">
                          SKU : {item.sku}
                        </p>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="text-xs font-bold text-destructive block tabular-nums">
                          {item.current_stock} pcs
                        </span>
                        <span className="text-[10px] text-muted-foreground">
                          Min : {item.alert_threshold}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <p className="text-xs text-muted-foreground">Aucun article sous le seuil d'alerte.</p>
                  </div>
                )}
              </div>

              <div className="pt-2 border-t border-border/40">
                <Link href="/inventory" className="block w-full">
                  <Button variant="ghost" size="sm" className="w-full text-xs text-primary font-medium hover:text-primary hover:bg-primary/5 justify-center">
                    Gérer les réapprovisionnements
                    <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
