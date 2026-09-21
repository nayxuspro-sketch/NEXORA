'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { DataTable } from '@/components/ui/data-table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { apiRequest } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { PaginatedResponse } from '@/types';
import { Search, ShieldCheck } from 'lucide-react';

interface AuditLogItem {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  user_email: string;
  ip_address: string;
  created_at: string;
}

export default function AuditPage() {
  const [search, setSearch] = React.useState('');

  const { data: auditData, isLoading } = useQuery<PaginatedResponse<AuditLogItem>>({
    queryKey: ['audit-logs', search],
    queryFn: () => apiRequest<PaginatedResponse<AuditLogItem>>(`/audit-logs/?search=${encodeURIComponent(search)}`),
    placeholderData: {
      status: 'success',
      pagination: { count: 3, total_pages: 1, current_page: 1, page_size: 20, next: null, previous: null },
      results: [
        {
          id: 'log-1',
          action: 'CREATE_SALE',
          resource_type: 'Sale',
          resource_id: 'VNT-20260919-001',
          user_email: 'cashier@alpha.com',
          ip_address: '192.168.1.45',
          created_at: new Date().toISOString(),
        },
        {
          id: 'log-2',
          action: 'RECEIVE_PURCHASE',
          resource_type: 'Purchase',
          resource_id: 'PO-ACH-2026-01',
          user_email: 'admin@alpha.com',
          ip_address: '192.168.1.10',
          created_at: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          id: 'log-3',
          action: 'VALIDATE_INVENTORY',
          resource_type: 'Inventory',
          resource_id: 'INV-2026-001',
          user_email: 'admin@alpha.com',
          ip_address: '192.168.1.10',
          created_at: new Date(Date.now() - 86400000).toISOString(),
        },
      ],
    },
  });

  const columns = [
    {
      header: 'Horodatage',
      cell: (row: AuditLogItem) => <span className="text-xs text-muted-foreground">{formatDate(row.created_at)}</span>,
    },
    {
      header: 'Action Réalisée',
      cell: (row: AuditLogItem) => (
        <Badge variant="outline" className="font-mono text-xs">
          {row.action}
        </Badge>
      ),
    },
    {
      header: 'Cible / Entité',
      cell: (row: AuditLogItem) => (
        <span className="text-xs font-semibold">
          {row.resource_type} (#{row.resource_id})
        </span>
      ),
    },
    {
      header: 'Opérateur',
      accessorKey: 'user_email' as keyof AuditLogItem,
    },
    {
      header: 'Adresse IP',
      accessorKey: 'ip_address' as keyof AuditLogItem,
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-foreground">
            Journal d'Audit & Sécurité
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            Registre d'audit immuable des actions sensibles (ventes, annulations, inventaires).
          </p>
        </div>

        <Input
          placeholder="Rechercher par identifiant de ressource, opérateur..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          icon={<Search className="h-4 w-4" />}
          className="max-w-md bg-card"
        />

        <DataTable columns={columns} data={auditData?.results || []} isLoading={isLoading} />
      </div>
    </DashboardLayout>
  );
}
