'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { DataTable } from '@/components/ui/data-table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { apiRequest } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';
import { Partner, PaginatedResponse } from '@/types';
import { Search, Users } from 'lucide-react';

export default function PartnersPage() {
  const [search, setSearch] = React.useState('');

  const { data: partnersData, isLoading } = useQuery<PaginatedResponse<Partner>>({
    queryKey: ['partners-list', search],
    queryFn: () => apiRequest<PaginatedResponse<Partner>>(`/partners/?search=${encodeURIComponent(search)}`),
    placeholderData: {
      status: 'success',
      pagination: { count: 2, total_pages: 1, current_page: 1, page_size: 20, next: null, previous: null },
      results: [
        {
          id: 'part-1',
          name: 'Tech Distribution Grossiste',
          partner_type: 'SUPPLIER',
          email: 'contact@tech-distrib.com',
          phone: '+33 1 23 45 67 89',
          address: '45 Avenue de l\'Industrie, Paris',
          tax_number: 'FR12345678901',
          credit_limit: '15000.00',
          current_balance: '0.00',
          is_active: true,
        },
        {
          id: 'part-2',
          name: 'SARL Alpha Client Entreprise',
          partner_type: 'CUSTOMER',
          email: 'achats@alphaclient.com',
          phone: '+33 6 12 34 56 78',
          address: '12 Rue du Commerce, Lyon',
          tax_number: 'FR98765432100',
          credit_limit: '5000.00',
          current_balance: '800.00',
          is_active: true,
        },
      ],
    },
  });

  const columns = [
    {
      header: 'Nom de l\'Entreprise / Tiers',
      cell: (row: Partner) => (
        <div>
          <span className="font-bold text-foreground">{row.name}</span>
          <p className="text-xs text-muted-foreground">{row.email} • {row.phone}</p>
        </div>
      ),
    },
    {
      header: 'Type',
      cell: (row: Partner) => (
        <Badge variant="outline" className="text-xs">
          {row.partner_type === 'CUSTOMER' ? 'Client' : row.partner_type === 'SUPPLIER' ? 'Fournisseur' : 'Mixte'}
        </Badge>
      ),
    },
    {
      header: 'Solde En-cours',
      cell: (row: Partner) => (
        <span className={`font-mono font-bold text-xs ${parseFloat(row.current_balance) > 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
          {formatCurrency(row.current_balance)}
        </span>
      ),
    },
    {
      header: 'Plafond Crédit Autorisé',
      cell: (row: Partner) => <span className="text-xs">{formatCurrency(row.credit_limit)}</span>,
    },
    {
      header: 'Statut',
      cell: (row: Partner) => (
        <Badge variant={row.is_active ? 'success' : 'destructive'}>
          {row.is_active ? 'Actif' : 'Inactif'}
        </Badge>
      ),
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-foreground">
            Répertoire Clients & Fournisseurs
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            Suivi des comptes tiers, encours de crédit et historique de facturation.
          </p>
        </div>

        <Input
          placeholder="Rechercher par nom, téléphone, numéro fiscal..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          icon={<Search className="h-4 w-4" />}
          className="max-w-md bg-card"
        />

        <DataTable columns={columns} data={partnersData?.results || []} isLoading={isLoading} />
      </div>
    </DashboardLayout>
  );
}
