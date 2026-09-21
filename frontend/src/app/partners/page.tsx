'use client';

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { DataTable } from '@/components/ui/data-table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Modal } from '@/components/ui/modal';
import { useToast } from '@/components/ui/toast';
import { apiRequest } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';
import { Partner, PaginatedResponse } from '@/types';
import { Search, Users, Plus } from 'lucide-react';

export default function PartnersPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [search, setSearch] = React.useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = React.useState(false);

  const [formData, setFormData] = React.useState({
    name: '',
    partner_type: 'CUSTOMER',
    email: '',
    phone: '',
    address: '',
    tax_number: '',
    credit_limit: '0.00',
  });

  const { data: partnersData, isLoading } = useQuery<PaginatedResponse<Partner>>({
    queryKey: ['partners-list', search],
    queryFn: () => apiRequest<PaginatedResponse<Partner>>(`/partners/?search=${encodeURIComponent(search)}`),
  });

  const createMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      return await apiRequest('/partners/', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      toast({
        type: 'success',
        title: 'Partenaire enregistré',
        message: 'Le compte client/fournisseur a été créé avec succès.',
      });
      setIsCreateModalOpen(false);
      setFormData({
        name: '',
        partner_type: 'CUSTOMER',
        email: '',
        phone: '',
        address: '',
        tax_number: '',
        credit_limit: '0.00',
      });
      queryClient.invalidateQueries({ queryKey: ['partners-list'] });
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur',
        message: err.message || 'Impossible d\'enregistrer le partenaire.',
      });
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
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-foreground">
              Répertoire Clients & Fournisseurs
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
              Suivi des comptes tiers, encours de crédit et historique de facturation.
            </p>
          </div>
          <Button onClick={() => setIsCreateModalOpen(true)}>
            <Plus className="h-4 w-4 mr-1.5" /> Nouveau Client / Fournisseur
          </Button>
        </div>

        <Input
          placeholder="Rechercher par nom, téléphone, numéro fiscal..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          icon={<Search className="h-4 w-4" />}
          className="max-w-md bg-card"
        />

        <DataTable columns={columns} data={partnersData?.results || []} isLoading={isLoading} />

        {/* Modal Création Partenaire */}
        <Modal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title="Ajouter un Compte Tiers (Client ou Fournisseur)"
          maxWidth="md"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createMutation.mutate(formData);
            }}
            className="space-y-4 pt-2"
          >
            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Nom complet / Raison Sociale *
              </label>
              <Input
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Ex: Établissement Ouédraogo & Frères"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Type de partenaire *
                </label>
                <select
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                  value={formData.partner_type}
                  onChange={(e) => setFormData({ ...formData, partner_type: e.target.value })}
                >
                  <option value="CUSTOMER">Client</option>
                  <option value="SUPPLIER">Fournisseur</option>
                  <option value="BOTH">Client & Fournisseur</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Téléphone
                </label>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="+226 70 00 00 00"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Email
                </label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="contact@societe.bf"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Plafond Crédit Autorisé (FCFA)
                </label>
                <Input
                  type="number"
                  value={formData.credit_limit}
                  onChange={(e) => setFormData({ ...formData, credit_limit: e.target.value })}
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Adresse physique
              </label>
              <Input
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                placeholder="Ouagadougou, Secteur 15"
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setIsCreateModalOpen(false)}>
                Annuler
              </Button>
              <Button type="submit" isLoading={createMutation.isPending}>
                Enregistrer le Partenaire
              </Button>
            </div>
          </form>
        </Modal>
      </div>
    </DashboardLayout>
  );
}
