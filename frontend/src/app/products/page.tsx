'use client';

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { DataTable } from '@/components/ui/data-table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Modal } from '@/components/ui/modal';
import { useToast } from '@/components/ui/toast';
import { apiRequest } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';
import { Product, PaginatedResponse } from '@/types';
import { Plus, Search, Package, Edit, Trash2 } from 'lucide-react';

export default function ProductsPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [search, setSearch] = React.useState('');
  const [currentPage, setCurrentPage] = React.useState(1);
  const [isCreateModalOpen, setIsCreateModalOpen] = React.useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = React.useState(false);
  const [editingProduct, setEditingProduct] = React.useState<Product | null>(null);

  // Edit form state
  const [editFormData, setEditFormData] = React.useState({
    name: '',
    sku: '',
    barcode: '',
    cost_price: '0.00',
    selling_price: '0.00',
    tax_rate: '18.00',
    alert_threshold: '5.00',
    description: '',
    is_active: true,
  });

  // Form state
  const [formData, setFormData] = React.useState({
    name: '',
    sku: '',
    barcode: '',
    cost_price: '0.00',
    selling_price: '0.00',
    tax_rate: '20.00',
    alert_threshold: '5.00',
    description: '',
  });

  const { data: productsData, isLoading } = useQuery<PaginatedResponse<Product>>({
    queryKey: ['products-list', search, currentPage],
    queryFn: () =>
      apiRequest<PaginatedResponse<Product>>(
        `/products/?page=${currentPage}&search=${encodeURIComponent(search)}`
      ),
    placeholderData: {
      status: 'success',
      pagination: { count: 3, total_pages: 1, current_page: 1, page_size: 20, next: null, previous: null },
      results: [
        {
          id: 'p1',
          name: 'Ordinateur Portable Pro 15',
          sku: 'LAPTOP-01',
          barcode: '3700123456789',
          description: 'Intel i7, 16Go RAM, 512Go SSD',
          cost_price: '500.00',
          selling_price: '800.00',
          tax_rate: '20.00',
          alert_threshold: '5.00',
          is_active: true,
          unit_symbol: 'pcs',
        },
        {
          id: 'p2',
          name: 'Souris Sans Fil Ergonomique',
          sku: 'MOUSE-01',
          barcode: '3700123456790',
          description: 'Capteur laser haute précision',
          cost_price: '15.00',
          selling_price: '35.00',
          tax_rate: '20.00',
          alert_threshold: '10.00',
          is_active: true,
          unit_symbol: 'pcs',
        },
      ],
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      return await apiRequest('/products/', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      toast({
        type: 'success',
        title: 'Produit créé',
        message: 'Le nouvel article a été ajouté au catalogue avec succès.',
      });
      setIsCreateModalOpen(false);
      setFormData({
        name: '',
        sku: '',
        barcode: '',
        cost_price: '0.00',
        selling_price: '0.00',
        tax_rate: '20.00',
        alert_threshold: '5.00',
        description: '',
      });
      queryClient.invalidateQueries({ queryKey: ['products-list'] });
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur',
        message: err.message || 'Impossible de créer le produit.',
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: typeof editFormData }) => {
      return await apiRequest(`/products/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      toast({
        type: 'success',
        title: 'Produit modifié',
        message: 'Les modifications de l\'article ont été enregistrées avec succès.',
      });
      setIsEditModalOpen(false);
      setEditingProduct(null);
      queryClient.invalidateQueries({ queryKey: ['products-list'] });
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur',
        message: err.message || 'Impossible de modifier le produit.',
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      return await apiRequest(`/products/${id}/`, {
        method: 'DELETE',
      });
    },
    onSuccess: () => {
      toast({
        type: 'success',
        title: 'Produit supprimé',
        message: 'L\'article a été retiré du catalogue.',
      });
      queryClient.invalidateQueries({ queryKey: ['products-list'] });
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur',
        message: err.message || 'Impossible de supprimer le produit.',
      });
    },
  });

  const handleOpenEdit = (product: Product) => {
    setEditingProduct(product);
    setEditFormData({
      name: product.name,
      sku: product.sku,
      barcode: product.barcode || '',
      cost_price: product.cost_price || '0.00',
      selling_price: product.selling_price || '0.00',
      tax_rate: (product as any).tax_rate || '18.00',
      alert_threshold: product.alert_threshold || '5.00',
      description: product.description || '',
      is_active: product.is_active ?? true,
    });
    setIsEditModalOpen(true);
  };

  const columns = [
    {
      header: 'Produit / Article',
      cell: (row: Product) => (
        <div>
          <p className="font-bold text-foreground">{row.name}</p>
          <p className="text-xs text-muted-foreground">{row.description || 'Aucune description'}</p>
        </div>
      ),
    },
    {
      header: 'SKU / Code-Barres',
      cell: (row: Product) => (
        <div className="font-mono text-xs">
          <span className="font-bold text-primary">{row.sku}</span>
          {row.barcode && <p className="text-muted-foreground">{row.barcode}</p>}
        </div>
      ),
    },
    {
      header: 'Prix Achat HT',
      cell: (row: Product) => <span>{formatCurrency(row.cost_price)}</span>,
    },
    {
      header: 'Prix Vente TTC',
      cell: (row: Product) => (
        <span className="font-bold text-foreground">{formatCurrency(row.selling_price)}</span>
      ),
    },
    {
      header: 'Seuil Alerte',
      cell: (row: Product) => (
        <Badge variant="outline" className="text-xs">
          {row.alert_threshold} {row.unit_symbol || 'u'}
        </Badge>
      ),
    },
    {
      header: 'Statut',
      cell: (row: Product) => (
        <Badge variant={row.is_active ? 'success' : 'destructive'}>
          {row.is_active ? 'Actif' : 'Inactif'}
        </Badge>
      ),
    },
    {
      header: 'Actions',
      cell: (row: Product) => (
        <div className="flex items-center gap-1.5">
          <Button
            variant="outline"
            size="sm"
            className="h-8 px-2 text-xs font-semibold hover:bg-primary/10 hover:text-primary transition-all"
            onClick={() => handleOpenEdit(row)}
            title="Modifier ce produit"
          >
            <Edit className="h-3.5 w-3.5 mr-1" /> Modifier
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 text-rose-500 hover:bg-rose-500/10 transition-all"
            onClick={() => {
              if (confirm(`Confirmez-vous la suppression de "${row.name}" ?`)) {
                deleteMutation.mutate(row.id);
              }
            }}
            title="Supprimer ce produit"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-foreground">
              Catalogue des Produits
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
              Gestion centralisée des prix de revient, tarifs de vente et seuils d'alerte.
            </p>
          </div>
          <Button onClick={() => setIsCreateModalOpen(true)}>
            <Plus className="h-4 w-4 mr-1.5" /> Nouveau Produit
          </Button>
        </div>

        {/* Filter bar */}
        <div className="flex items-center gap-3">
          <Input
            placeholder="Filtrer par nom, référence SKU ou code-barres..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            icon={<Search className="h-4 w-4" />}
            className="max-w-md bg-card"
          />
        </div>

        {/* Data Table */}
        <DataTable
          columns={columns}
          data={productsData?.results || []}
          isLoading={isLoading}
          pagination={{
            currentPage,
            totalPages: productsData?.pagination?.total_pages || 1,
            onPageChange: setCurrentPage,
          }}
        />

        {/* Create Modal */}
        <Modal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title="Ajouter un Produit au Catalogue"
          maxWidth="lg"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createMutation.mutate(formData);
            }}
            className="space-y-4 pt-2"
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Nom du produit *
                </label>
                <Input
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Ex: Écran 27 Pouces 4K"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Référence SKU *
                </label>
                <Input
                  required
                  value={formData.sku}
                  onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                  placeholder="Ex: DISP-4K-27"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Prix de revient HT (FCFA)
                </label>
                <Input
                  type="number"
                  step="1"
                  value={formData.cost_price}
                  onChange={(e) => setFormData({ ...formData, cost_price: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Prix de vente TTC (FCFA)
                </label>
                <Input
                  type="number"
                  step="1"
                  value={formData.selling_price}
                  onChange={(e) => setFormData({ ...formData, selling_price: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Seuil d'alerte stock
                </label>
                <Input
                  type="number"
                  step="1"
                  value={formData.alert_threshold}
                  onChange={(e) => setFormData({ ...formData, alert_threshold: e.target.value })}
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Description & Caractéristiques
              </label>
              <Input
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Détails techniques, garantie, options..."
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setIsCreateModalOpen(false)}>
                Annuler
              </Button>
              <Button type="submit" isLoading={createMutation.isPending}>
                Enregistrer le Produit
              </Button>
            </div>
          </form>
        </Modal>

        {/* Edit Modal */}
        <Modal
          isOpen={isEditModalOpen}
          onClose={() => {
            setIsEditModalOpen(false);
            setEditingProduct(null);
          }}
          title={`Modifier l'article : ${editingProduct?.name || ''}`}
          maxWidth="lg"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!editingProduct) return;
              updateMutation.mutate({ id: editingProduct.id, data: editFormData });
            }}
            className="space-y-4 pt-2"
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Nom du produit *
                </label>
                <Input
                  required
                  value={editFormData.name}
                  onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                  placeholder="Ex: Écran 27 Pouces 4K"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Référence SKU *
                </label>
                <Input
                  required
                  value={editFormData.sku}
                  onChange={(e) => setEditFormData({ ...editFormData, sku: e.target.value })}
                  placeholder="Ex: DISP-4K-27"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Prix de revient HT (FCFA)
                </label>
                <Input
                  type="number"
                  step="1"
                  value={editFormData.cost_price}
                  onChange={(e) => setEditFormData({ ...editFormData, cost_price: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Prix de vente TTC (FCFA) *
                </label>
                <Input
                  type="number"
                  step="1"
                  required
                  value={editFormData.selling_price}
                  onChange={(e) => setEditFormData({ ...editFormData, selling_price: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Seuil d'alerte stock
                </label>
                <Input
                  type="number"
                  step="1"
                  value={editFormData.alert_threshold}
                  onChange={(e) => setEditFormData({ ...editFormData, alert_threshold: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Code-barres / EAN
                </label>
                <Input
                  value={editFormData.barcode}
                  onChange={(e) => setEditFormData({ ...editFormData, barcode: e.target.value })}
                  placeholder="Ex: 3700123456789"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Statut de l'article
                </label>
                <select
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                  value={editFormData.is_active ? 'true' : 'false'}
                  onChange={(e) => setEditFormData({ ...editFormData, is_active: e.target.value === 'true' })}
                >
                  <option value="true">Actif (disponible à la vente)</option>
                  <option value="false">Inactif (archivé / désactivé)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Description & Caractéristiques
              </label>
              <Input
                value={editFormData.description}
                onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
                placeholder="Détails techniques, garantie, options..."
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsEditModalOpen(false);
                  setEditingProduct(null);
                }}
              >
                Annuler
              </Button>
              <Button type="submit" isLoading={updateMutation.isPending}>
                Enregistrer les Modifications
              </Button>
            </div>
          </form>
        </Modal>
      </div>
    </DashboardLayout>
  );
}
