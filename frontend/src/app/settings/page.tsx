'use client';

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { DataTable } from '@/components/ui/data-table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Modal } from '@/components/ui/modal';
import { useToast } from '@/components/ui/toast';
import { apiRequest } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import {
  Users,
  Shield,
  UserPlus,
  KeyRound,
  CheckCircle2,
  Lock,
  Plus,
  Edit2,
  Trash2,
  ShieldCheck,
  Building2,
  Search,
  Layers
} from 'lucide-react';

interface GroupItem {
  id: number;
  name: string;
  permissions_details: Array<{
    id: number;
    name: string;
    codename: string;
    app_label: string;
  }>;
  users_count: number;
}

interface UserItem {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  phone?: string;
  company_name?: string;
  is_active: boolean;
  date_joined: string;
  groups_details?: Array<{ id: number; name: string }>;
}

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [activeTab, setActiveTab] = React.useState<'users' | 'groups'>('users');
  const [searchQuery, setSearchQuery] = React.useState('');

  // Modals state
  const [isUserModalOpen, setIsUserModalOpen] = React.useState(false);
  const [isGroupModalOpen, setIsGroupModalOpen] = React.useState(false);
  const [editingUser, setEditingUser] = React.useState<UserItem | null>(null);
  const [editingGroup, setEditingGroup] = React.useState<GroupItem | null>(null);

  // Form state: User
  const [userForm, setUserForm] = React.useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    role: 'CASHIER',
    phone: '',
    is_active: true,
    group_ids: [] as number[],
  });

  // Form state: Group & Permissions
  const [groupForm, setGroupForm] = React.useState({
    name: '',
    permission_ids: [] as number[],
  });

  // 1. Fetch Users
  const { data: usersData, isLoading: isLoadingUsers } = useQuery<{ results: UserItem[] }>({
    queryKey: ['settings-users'],
    queryFn: () => apiRequest<{ results: UserItem[] }>('/users/'),
  });

  // 2. Fetch Groups
  const { data: groupsData, isLoading: isLoadingGroups } = useQuery<{ results: GroupItem[] }>({
    queryKey: ['settings-groups'],
    queryFn: () => apiRequest<{ results: GroupItem[] }>('/groups/'),
  });

  // 3. Fetch System Permissions grouped by module
  const { data: permsData } = useQuery<{
    permissions_by_module: Record<string, Array<{ id: number; name: string; codename: string }>>;
  }>({
    queryKey: ['system-permissions'],
    queryFn: () => apiRequest<any>('/settings/permissions/'),
  });

  // Mutation: Save User
  const userMutation = useMutation({
    mutationFn: async (payload: any) => {
      if (editingUser) {
        return apiRequest(`/users/${editingUser.id}/`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        });
      } else {
        return apiRequest('/users/', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings-users'] });
      queryClient.invalidateQueries({ queryKey: ['settings-groups'] });
      toast({
        type: 'success',
        title: editingUser ? 'Utilisateur Modifié' : 'Utilisateur Créé',
        message: `Le compte utilisateur a été enregistré avec succès.`,
      });
      setIsUserModalOpen(false);
      resetUserForm();
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur Enregistrement Utilisateur',
        message: err.message || 'Impossible d’enregistrer l’utilisateur.',
      });
    },
  });

  // Mutation: Save Group
  const groupMutation = useMutation({
    mutationFn: async (payload: any) => {
      if (editingGroup) {
        return apiRequest(`/groups/${editingGroup.id}/`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        });
      } else {
        return apiRequest('/groups/', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings-groups'] });
      queryClient.invalidateQueries({ queryKey: ['settings-users'] });
      toast({
        type: 'success',
        title: editingGroup ? 'Profil/Groupe Mis à jour' : 'Profil/Groupe Créé',
        message: `Les droits d'accès associés ont été enregistrés avec succès.`,
      });
      setIsGroupModalOpen(false);
      resetGroupForm();
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur Profil / Groupe',
        message: err.message || 'Impossible d’enregistrer le groupe.',
      });
    },
  });

  // Mutation: Delete Group
  const deleteGroupMutation = useMutation({
    mutationFn: async (groupId: number) => {
      return apiRequest(`/groups/${groupId}/`, { method: 'DELETE' });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings-groups'] });
      toast({
        type: 'success',
        title: 'Groupe Supprimé',
        message: 'Le profil de droits a été retiré.',
      });
    },
  });

  const resetUserForm = () => {
    setEditingUser(null);
    setUserForm({
      first_name: '',
      last_name: '',
      email: '',
      password: '',
      role: 'CASHIER',
      phone: '',
      is_active: true,
      group_ids: [],
    });
  };

  const resetGroupForm = () => {
    setEditingGroup(null);
    setGroupForm({
      name: '',
      permission_ids: [],
    });
  };

  const openCreateUserModal = () => {
    resetUserForm();
    setIsUserModalOpen(true);
  };

  const openEditUserModal = (u: UserItem) => {
    setEditingUser(u);
    setUserForm({
      first_name: u.first_name,
      last_name: u.last_name,
      email: u.email,
      password: '',
      role: u.role,
      phone: u.phone || '',
      is_active: u.is_active,
      group_ids: u.groups_details?.map((g) => g.id) || [],
    });
    setIsUserModalOpen(true);
  };

  const openCreateGroupModal = () => {
    resetGroupForm();
    setIsGroupModalOpen(true);
  };

  const openEditGroupModal = (g: GroupItem) => {
    setEditingGroup(g);
    setGroupForm({
      name: g.name,
      permission_ids: g.permissions_details?.map((p) => p.id) || [],
    });
    setIsGroupModalOpen(true);
  };

  const handleTogglePermission = (permId: number) => {
    setGroupForm((prev) => {
      const exists = prev.permission_ids.includes(permId);
      return {
        ...prev,
        permission_ids: exists
          ? prev.permission_ids.filter((id) => id !== permId)
          : [...prev.permission_ids, permId],
      };
    });
  };

  const handleToggleAllModulePerms = (perms: Array<{ id: number }>) => {
    const permIds = perms.map((p) => p.id);
    const allSelected = permIds.every((id) => groupForm.permission_ids.includes(id));

    setGroupForm((prev) => ({
      ...prev,
      permission_ids: allSelected
        ? prev.permission_ids.filter((id) => !permIds.includes(id))
        : Array.from(new Set([...prev.permission_ids, ...permIds])),
    }));
  };

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'ADMIN':
        return <Badge variant="default">Directeur / Admin</Badge>;
      case 'MANAGER':
        return <Badge variant="secondary">Responsable Magasin</Badge>;
      case 'CASHIER':
        return <Badge variant="success">Caissier / Vendeur</Badge>;
      case 'STOCK_KEEPER':
        return <Badge variant="warning">Gestionnaire Stocks</Badge>;
      case 'ACCOUNTANT':
        return <Badge variant="outline">Comptable</Badge>;
      case 'AUDITOR':
        return <Badge variant="outline">Auditeur</Badge>;
      default:
        return <Badge variant="outline">{role}</Badge>;
    }
  };

  const userColumns = [
    {
      header: 'Collaborateur & Contact',
      cell: (row: UserItem) => (
        <div>
          <span className="font-bold text-foreground block text-sm">
            {row.first_name} {row.last_name}
          </span>
          <span className="font-mono text-xs text-muted-foreground">{row.email}</span>
        </div>
      ),
    },
    {
      header: 'Rôle Système',
      cell: (row: UserItem) => getRoleBadge(row.role),
    },
    {
      header: 'Groupes & Profils Assignés',
      cell: (row: UserItem) => (
        <div className="flex flex-wrap gap-1 max-w-xs">
          {row.groups_details && row.groups_details.length > 0 ? (
            row.groups_details.map((g) => (
              <Badge key={g.id} variant="outline" className="text-[10px] bg-primary/5 text-primary border-primary/20">
                <ShieldCheck className="h-3 w-3 mr-1" />
                {g.name}
              </Badge>
            ))
          ) : (
            <span className="text-xs text-muted-foreground italic">Aucun groupe</span>
          )}
        </div>
      ),
    },
    {
      header: 'État Compte',
      cell: (row: UserItem) => (
        <Badge variant={row.is_active ? 'success' : 'destructive'} className="text-[10px]">
          {row.is_active ? 'Actif' : 'Désactivé'}
        </Badge>
      ),
    },
    {
      header: 'Date d’arrivée',
      cell: (row: UserItem) => (
        <span className="text-xs text-muted-foreground">{formatDate(row.date_joined)}</span>
      ),
    },
    {
      header: 'Actions',
      cell: (row: UserItem) => (
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => openEditUserModal(row)}
            className="h-7 text-xs px-2.5 font-medium"
          >
            <Edit2 className="h-3.5 w-3.5 mr-1" /> Modifier
          </Button>
        </div>
      ),
    },
  ];

  const groupColumns = [
    {
      header: 'Nom du Profil / Groupe',
      cell: (row: GroupItem) => (
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold">
            <Shield className="h-4 w-4" />
          </div>
          <div>
            <span className="font-bold text-foreground block text-sm">{row.name}</span>
            <span className="text-xs text-muted-foreground">
              {row.users_count} utilisateur(s) membre(s)
            </span>
          </div>
        </div>
      ),
    },
    {
      header: 'Droits & Permissions Incluses',
      cell: (row: GroupItem) => (
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="font-mono text-xs font-semibold bg-muted/40">
            {row.permissions_details?.length || 0} permissions actives
          </Badge>
        </div>
      ),
    },
    {
      header: 'Actions',
      cell: (row: GroupItem) => (
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => openEditGroupModal(row)}
            className="h-7 text-xs px-2.5 font-medium"
          >
            <KeyRound className="h-3.5 w-3.5 mr-1 text-primary" /> Configurer Droits
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              if (confirm(`Voulez-vous vraiment supprimer le groupe "${row.name}" ?`)) {
                deleteGroupMutation.mutate(row.id);
              }
            }}
            className="h-7 text-xs px-2 text-rose-500 hover:text-rose-600 hover:bg-rose-500/10"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      ),
    },
  ];

  const filteredUsers = (usersData?.results || []).filter((u) => {
    const q = searchQuery.toLowerCase();
    return (
      u.email.toLowerCase().includes(q) ||
      u.first_name.toLowerCase().includes(q) ||
      u.last_name.toLowerCase().includes(q) ||
      u.role.toLowerCase().includes(q)
    );
  });

  const filteredGroups = (groupsData?.results || []).filter((g) =>
    g.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-border/60">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-extrabold tracking-tight text-foreground flex items-center gap-2">
                <Shield className="h-7 w-7 text-primary" /> Paramètres & Gestion des Droits d’Accès
              </h1>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-md bg-primary/10 text-primary border border-primary/20">
                RBAC Sécurisé
              </span>
            </div>
            <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
              Gestion centralisée des utilisateurs, profils de postes (groupes) et habilitations fines sur tous les modules.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {activeTab === 'users' ? (
              <Button onClick={openCreateUserModal} size="sm" className="font-semibold shadow-xs">
                <UserPlus className="h-4 w-4 mr-1.5" /> Nouvel Utilisateur
              </Button>
            ) : (
              <Button onClick={openCreateGroupModal} size="sm" className="font-semibold shadow-xs">
                <Plus className="h-4 w-4 mr-1.5" /> Nouveau Profil / Groupe
              </Button>
            )}
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-3 border-b border-border">
          <button
            type="button"
            onClick={() => setActiveTab('users')}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-bold border-b-2 transition-all ${
              activeTab === 'users'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Users className="h-4 w-4" /> Utilisateurs ({usersData?.results?.length || 0})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('groups')}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-bold border-b-2 transition-all ${
              activeTab === 'groups'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <ShieldCheck className="h-4 w-4" /> Groupes & Profils d’Accès ({groupsData?.results?.length || 0})
          </button>
        </div>

        {/* Filter bar */}
        <div className="flex items-center gap-3 bg-card p-3 rounded-xl border">
          <div className="max-w-md w-full">
            <Input
              placeholder={activeTab === 'users' ? 'Rechercher un collaborateur par nom, email...' : 'Rechercher un groupe ou profil...'}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              icon={<Search className="h-4 w-4" />}
              className="bg-background"
            />
          </div>
        </div>

        {/* TAB 1: USERS */}
        {activeTab === 'users' && (
          <div className="space-y-4">
            <DataTable
              columns={userColumns}
              data={filteredUsers}
              isLoading={isLoadingUsers}
            />
          </div>
        )}

        {/* TAB 2: GROUPS & PERMISSIONS */}
        {activeTab === 'groups' && (
          <div className="space-y-4">
            <DataTable
              columns={groupColumns}
              data={filteredGroups}
              isLoading={isLoadingGroups}
            />
          </div>
        )}

        {/* MODAL 1: CRÉER / MODIFIER UTILISATEUR */}
        <Modal
          isOpen={isUserModalOpen}
          onClose={() => {
            setIsUserModalOpen(false);
            resetUserForm();
          }}
          title={editingUser ? `Modifier le compte de ${editingUser.first_name}` : 'Créer un Nouvel Utilisateur'}
          maxWidth="md"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const payload: any = {
                first_name: userForm.first_name,
                last_name: userForm.last_name,
                email: userForm.email,
                role: userForm.role,
                phone: userForm.phone,
                is_active: userForm.is_active,
                group_ids: userForm.group_ids,
              };
              if (userForm.password) {
                payload.password = userForm.password;
              }
              userMutation.mutate(payload);
            }}
            className="space-y-4 pt-1"
          >
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">Prénom *</label>
                <Input
                  required
                  value={userForm.first_name}
                  onChange={(e) => setUserForm({ ...userForm, first_name: e.target.value })}
                  placeholder="Ex: Ibrahim"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">Nom *</label>
                <Input
                  required
                  value={userForm.last_name}
                  onChange={(e) => setUserForm({ ...userForm, last_name: e.target.value })}
                  placeholder="Ex: Ouedraogo"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">Adresse Email *</label>
                <Input
                  type="email"
                  required
                  value={userForm.email}
                  onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                  placeholder="agent@nexora-bf.com"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">Téléphone</label>
                <Input
                  value={userForm.phone}
                  onChange={(e) => setUserForm({ ...userForm, phone: e.target.value })}
                  placeholder="+226 70 00 00 00"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Mot de Passe {editingUser ? '(Laisser vide pour ne pas modifier)' : '*'}
              </label>
              <Input
                type="password"
                required={!editingUser}
                value={userForm.password}
                onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                placeholder="••••••••••••"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">Rôle Principal Métier *</label>
                <select
                  className="w-full h-10 px-3 rounded-lg border border-input bg-background text-xs font-semibold"
                  value={userForm.role}
                  onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}
                >
                  <option value="ADMIN">Directeur Général / Administrateur</option>
                  <option value="MANAGER">Responsable Commercial / Manager</option>
                  <option value="CASHIER">Caissier / Opérateur Caisse</option>
                  <option value="STOCK_KEEPER">Gestionnaire de Stock & Magasin</option>
                  <option value="ACCOUNTANT">Comptable / Gestionnaire Financier</option>
                  <option value="AUDITOR">Auditeur Interne / Contrôleur</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">Statut du Compte</label>
                <div className="flex items-center gap-2 h-10">
                  <label className="flex items-center gap-2 cursor-pointer text-xs font-medium">
                    <input
                      type="checkbox"
                      checked={userForm.is_active}
                      onChange={(e) => setUserForm({ ...userForm, is_active: e.target.checked })}
                      className="rounded border-input text-primary h-4 w-4"
                    />
                    Autoriser la connexion (Compte Actif)
                  </label>
                </div>
              </div>
            </div>

            {/* Attribution des groupes */}
            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1.5">
                Attribuer des Groupes / Profils d'Habilitations :
              </label>
              <div className="space-y-2 p-3 rounded-xl border bg-muted/20 max-h-40 overflow-y-auto">
                {(groupsData?.results || []).map((grp) => {
                  const isChecked = userForm.group_ids.includes(grp.id);
                  return (
                    <label
                      key={grp.id}
                      className="flex items-center justify-between p-2 rounded-lg border border-border/50 bg-card hover:bg-muted/40 cursor-pointer text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {
                            setUserForm((prev) => ({
                              ...prev,
                              group_ids: isChecked
                                ? prev.group_ids.filter((id) => id !== grp.id)
                                : [...prev.group_ids, grp.id],
                            }));
                          }}
                          className="rounded border-input text-primary h-4 w-4"
                        />
                        <span className="font-bold text-foreground">{grp.name}</span>
                      </div>
                      <Badge variant="outline" className="text-[10px]">
                        {grp.permissions_details?.length || 0} permissions
                      </Badge>
                    </label>
                  );
                })}
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsUserModalOpen(false);
                  resetUserForm();
                }}
              >
                Annuler
              </Button>
              <Button type="submit" isLoading={userMutation.isPending}>
                <CheckCircle2 className="h-4 w-4 mr-1.5" /> Enregistrer l'Utilisateur
              </Button>
            </div>
          </form>
        </Modal>

        {/* MODAL 2: CRÉER / CONFIGURER GROUPE & DROITS D'ACCÈS */}
        <Modal
          isOpen={isGroupModalOpen}
          onClose={() => {
            setIsGroupModalOpen(false);
            resetGroupForm();
          }}
          title={editingGroup ? `Configurer les Droits : ${editingGroup.name}` : 'Créer un Profil de Droits / Groupe'}
          maxWidth="xl"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              groupMutation.mutate({
                name: groupForm.name,
                permission_ids: groupForm.permission_ids,
              });
            }}
            className="space-y-4 pt-1"
          >
            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Nom du Profil / Rôle Métier *
              </label>
              <Input
                required
                value={groupForm.name}
                onChange={(e) => setGroupForm({ ...groupForm, name: e.target.value })}
                placeholder="Ex: Contrôleurs de Caisse & Auditeurs"
              />
            </div>

            {/* Sélecteur de Permissions par Module */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-bold text-foreground">
                  Grille des Droits d'Accès & Permissions Granulaires
                </label>
                <span className="text-xs font-bold text-primary">
                  {groupForm.permission_ids.length} sélectionnée(s)
                </span>
              </div>

              <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
                {permsData?.permissions_by_module &&
                  Object.entries(permsData.permissions_by_module).map(([moduleName, perms]) => {
                    const allSelected = perms.every((p) => groupForm.permission_ids.includes(p.id));

                    // Module friendly label
                    const moduleLabels: Record<string, string> = {
                      sales: 'Ventes, Règlements & Facturation',
                      pos: 'Caisse & Point de Vente (POS)',
                      inventory: 'Stocks, Entrepôts & Inventaires',
                      purchases: 'Achats & Commandes Fournisseurs',
                      catalog: 'Catalogue Articles & Tarification',
                      accounts: 'Gestion des Utilisateurs & Équipes',
                      audit: 'Journal d’Audit & Sécurité Légale',
                      ai_assistant: 'Assistant IA & Règles d’Automatisation',
                      companies: 'Structure & Paramètres Société',
                    };

                    return (
                      <div key={moduleName} className="p-3 rounded-xl border bg-card space-y-2">
                        <div className="flex items-center justify-between border-b pb-1.5">
                          <span className="text-xs font-extrabold uppercase tracking-wide text-foreground flex items-center gap-1.5">
                            <Layers className="h-3.5 w-3.5 text-primary" />
                            {moduleLabels[moduleName] || moduleName}
                          </span>
                          <button
                            type="button"
                            onClick={() => handleToggleAllModulePerms(perms)}
                            className="text-[11px] font-semibold text-primary hover:underline"
                          >
                            {allSelected ? 'Tout décocher' : 'Tout sélectionner'}
                          </button>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                          {perms.map((perm) => {
                            const isChecked = groupForm.permission_ids.includes(perm.id);
                            return (
                              <label
                                key={perm.id}
                                className={`flex items-center gap-2 p-2 rounded-lg border text-xs cursor-pointer transition-colors ${
                                  isChecked
                                    ? 'bg-primary/10 border-primary/30 text-foreground font-semibold'
                                    : 'bg-muted/30 border-transparent text-muted-foreground hover:bg-muted/60'
                                }`}
                              >
                                <input
                                  type="checkbox"
                                  checked={isChecked}
                                  onChange={() => handleTogglePermission(perm.id)}
                                  className="rounded border-input text-primary h-3.5 w-3.5 shrink-0"
                                />
                                <span className="truncate">{perm.name}</span>
                              </label>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsGroupModalOpen(false);
                  resetGroupForm();
                }}
              >
                Annuler
              </Button>
              <Button type="submit" isLoading={groupMutation.isPending}>
                <CheckCircle2 className="h-4 w-4 mr-1.5" /> Enregistrer le Profil et les Droits
              </Button>
            </div>
          </form>
        </Modal>
      </div>
    </DashboardLayout>
  );
}
