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
import { Search, FileText } from 'lucide-react';

export default function SalesPage() {
  const [search, setSearch] = React.useState('');

  const { data: salesData, isLoading } = useQuery<PaginatedResponse<Sale>>({
    queryKey: ['sales-list', search],
    queryFn: () => apiRequest<PaginatedResponse<Sale>>(`/sales/?search=${encodeURIComponent(search)}`),
    placeholderData: {
      status: 'success',
      pagination: { count: 2, total_pages: 1, current_page: 1, page_size: 20, next: null, previous: null },
      results: [
        {
          id: 's1',
          reference: 'VNT-20260919-001',
          store: 'store-01',
          store_name: 'Magasin & Dépôt Ouaga Central',
          customer_name: 'Client Comptoir',
          seller_name: 'caissier@nexora-bf.com',
          status: 'COMPLETED',
          payment_status: 'PAID',
          subtotal_amount: '465000.00',
          tax_amount: '83700.00',
          discount_amount: '0.00',
          total_amount: '548700.00',
          paid_amount: '548700.00',
          items: [],
          created_at: new Date().toISOString(),
        },
        {
          id: 's2',
          reference: 'VNT-20260919-002',
          store: 'store-01',
          store_name: 'Alpha Dépôt Principal',
          customer_name: 'Entreprise Partenaire B',
          seller_name: 'admin@alpha.com',
          status: 'COMPLETED',
          payment_status: 'PARTIAL',
          subtotal_amount: '700.00',
          tax_amount: '140.00',
          discount_amount: '40.00',
          total_amount: '800.00',
          paid_amount: '400.00',
          items: [],
          created_at: new Date(Date.now() - 7200000).toISOString(),
        },
      ],
    },
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
        return <Badge variant={variants[row.payment_status] || 'outline'}>{row.payment_status}</Badge>;
      },
    },
    {
      header: 'Statut Vente',
      cell: (row: Sale) => (
        <Badge variant={row.status === 'COMPLETED' ? 'success' : 'destructive'}>{row.status}</Badge>
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

        <DataTable columns={columns} data={salesData?.results || []} isLoading={isLoading} />
      </div>
    </DashboardLayout>
  );
}
