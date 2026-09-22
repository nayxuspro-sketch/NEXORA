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
import { downloadPdfFile } from '@/lib/pdf-export';
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
  Layers,
  Store as StoreIcon,
  PauseCircle,
  PlayCircle,
  MapPin,
  Phone,
  Award,
  FileCheck,
  Download,
  AlertOctagon,
  Copy
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

interface LicenseItem {
  id: string;
  store: string;
  store_name: string;
  store_code: string;
  license_key: string;
  plan_type: string;
  max_registers: number;
  issued_to_name: string;
  valid_from: string;
  expires_at: string;
  signature_hash: string;
  is_revoked: boolean;
  is_valid: boolean;
  remaining_days: number;
  created_at: string;
}

interface StoreItem {
  id: string;
  name: string;
  code: string;
  address: string;
  phone: string;
  manager?: string;
  manager_name?: string;
  is_active: boolean;
  created_at: string;
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

  const [activeTab, setActiveTab] = React.useState<'users' | 'groups' | 'stores' | 'licenses'>('users');
  const [searchQuery, setSearchQuery] = React.useState('');

  // Modals state
  const [isUserModalOpen, setIsUserModalOpen] = React.useState(false);
  const [isGroupModalOpen, setIsGroupModalOpen] = React.useState(false);
  const [editingUser, setEditingUser] = React.useState<UserItem | null>(null);
  const [editingGroup, setEditingGroup] = React.useState<GroupItem | null>(null);
  // Store states
  const [isStoreModalOpen, setIsStoreModalOpen] = React.useState(false);
  const [editingStore, setEditingStore] = React.useState<StoreItem | null>(null);
  // License state
  const [isLicenseModalOpen, setIsLicenseModalOpen] = React.useState(false);
  const [licenseForm, setLicenseForm] = React.useState({
    store: '',
    plan_type: 'PRO',
    duration_months: 12,
    max_registers: 3,
    issued_to_name: '',
  });
  const [storeForm, setStoreForm] = React.useState({
    name: '',
    code: '',
    address: '',
    phone: '',
    manager: '',
    is_active: true,
  });

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

  // 5. Fetch Store Licenses
  const { data: licensesData, isLoading: isLoadingLicenses } = useQuery<{ results: LicenseItem[] }>({
    queryKey: ['settings-licenses'],
    queryFn: () => apiRequest<{ results: LicenseItem[] }>('/store-licenses/'),
  });

  // Mutation: Generate License
  const generateLicenseMutation = useMutation({
    mutationFn: async (payload: any) => {
      // Calculate expires_at date based on months
      const d = new Date();
      d.setMonth(d.getMonth() + parseInt(payload.duration_months.toString(), 10));
      const expires_at = d.toISOString().split('T')[0];

      return apiRequest('/store-licenses/', {
        method: 'POST',
        body: JSON.stringify({
          store: payload.store,
          plan_type: payload.plan_type,
          max_registers: parseInt(payload.max_registers.toString(), 10),
          issued_to_name: payload.issued_to_name,
          expires_at: expires_at,
        }),
      });
    },
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['settings-licenses'] });
      toast({
        type: 'success',
        title: 'Licence d’Exploitation Générée',
        message: `Clé d'activation créée avec succès pour le magasin.`,
      });
      setIsLicenseModalOpen(false);
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur Génération Licence',
        message: err.message || 'Impossible de générer la licence.',
      });
    },
  });

  // Mutation: Revoke / Reactivate License
  const toggleLicenseRevocationMutation = useMutation({
    mutationFn: async ({ licId, is_revoked }: { licId: string; is_revoked: boolean }) => {
      return apiRequest(`/store-licenses/${licId}/`, {
        method: 'PATCH',
        body: JSON.stringify({ is_revoked }),
      });
    },
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ['settings-licenses'] });
      toast({
        type: 'success',
        title: vars.is_revoked ? 'Licence Révoquée' : 'Licence Réactivée',
        message: vars.is_revoked
          ? 'La licence d’exploitation a été invalidée pour ce magasin.'
          : 'La licence d’exploitation a été rétablie.',
      });
    },
  });

  const downloadLicensePdf = async (licenseId: string, storeCode: string) => {
    try {
      await downloadPdfFile(
        `/api/v1/store-licenses/${licenseId}/certificate-pdf/`,
        `Certificat_Licence_${storeCode}.pdf`
      );

      toast({
        type: 'success',
        title: 'Certificat Officiel Téléchargé',
        message: 'Le certificat de licence haute définition a été généré.',
      });
    } catch (err: any) {
      toast({
        type: 'error',
        title: 'Erreur Téléchargement PDF',
        message: err.message || 'Impossible de télécharger le certificat.',
      });
    }
  };

  // 4. Fetch Stores (Magasins)
  const { data: storesData, isLoading: isLoadingStores } = useQuery<{ results: StoreItem[] }>({
    queryKey: ['settings-stores'],
    queryFn: () => apiRequest<{ results: StoreItem[] }>('/stores/'),
  });

  // Mutation: Save Store
  const storeMutation = useMutation({
    mutationFn: async (payload: any) => {
      if (editingStore) {
        return apiRequest(`/stores/${editingStore.id}/`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        });
      } else {
        return apiRequest('/stores/', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings-stores'] });
      toast({
        type: 'success',
        title: editingStore ? 'Magasin Mis à Jour' : 'Nouveau Magasin Créé',
        message: 'Les données du magasin ont été enregistrées avec succès.',
      });
      setIsStoreModalOpen(false);
      resetStoreForm();
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur Enregistrement Magasin',
        message: err.message || 'Impossible d’enregistrer le magasin.',
      });
    },
  });

  // Mutation: Toggle Store Active Status (Suspendre / Réactiver l'activité)
  const toggleStoreStatusMutation = useMutation({
    mutationFn: async ({ storeId, is_active }: { storeId: string; is_active: boolean }) => {
      return apiRequest(`/stores/${storeId}/`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active }),
      });
    },
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ['settings-stores'] });
      toast({
        type: 'success',
        title: vars.is_active ? 'Activité du Magasin Réactivée' : 'Activité du Magasin Suspendue',
        message: vars.is_active
          ? 'Le magasin est de nouveau opérationnel pour les ventes et mouvements.'
          : 'Le magasin a été suspendu temporairement (activité gelée).',
      });
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur Changement Statut',
        message: err.message || 'Impossible de modifier le statut.',
      });
    },
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

  const resetStoreForm = () => {
    setEditingStore(null);
    setStoreForm({
      name: '',
      code: '',
      address: '',
      phone: '',
      manager: '',
      is_active: true,
    });
  };

  const openCreateStoreModal = () => {
    resetStoreForm();
    setIsStoreModalOpen(true);
  };

  const openEditStoreModal = (s: StoreItem) => {
    setEditingStore(s);
    setStoreForm({
      name: s.name,
      code: s.code,
      address: s.address || '',
      phone: s.phone || '',
      manager: s.manager || '',
      is_active: s.is_active,
    });
    setIsStoreModalOpen(true);
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

  // Columns for Licenses table
  const licenseColumns = [
    {
      header: 'Magasin & Clé d’Activation',
      cell: (row: LicenseItem) => (
        <div>
          <span className="font-bold text-foreground block text-sm flex items-center gap-1.5">
            <Award className="h-4 w-4 text-primary" /> {row.store_name}
          </span>
          <div className="flex items-center gap-1.5 mt-0.5">
            <code className="text-xs font-mono font-bold text-primary bg-primary/10 px-2 py-0.5 rounded border border-primary/20">
              {row.license_key}
            </code>
            <button
              onClick={() => {
                navigator.clipboard.writeText(row.license_key);
                toast({ type: 'success', title: 'Clé Copiée', message: 'Clé de licence copiée dans le presse-papier.' });
              }}
              title="Copier la clé"
              className="text-muted-foreground hover:text-foreground p-0.5"
            >
              <Copy className="h-3 w-3" />
            </button>
          </div>
        </div>
      ),
    },
    {
      header: 'Formule & Postes',
      cell: (row: LicenseItem) => (
        <div className="text-xs space-y-0.5">
          <Badge variant="outline" className="font-semibold bg-muted/40">
            {row.plan_type === 'ENTERPRISE' ? 'Entreprise Illimitée' : (row.plan_type === 'PRO' ? 'Pro Multi-Caisses' : 'Standard 1 Poste')}
          </Badge>
          <p className="text-[11px] text-muted-foreground">
            Max : <span className="font-bold text-foreground">{row.max_registers} caisse(s)</span>
          </p>
        </div>
      ),
    },
    {
      header: 'Validité & Échéance',
      cell: (row: LicenseItem) => (
        <div className="text-xs">
          <span className="font-semibold text-foreground block">
            Jusqu’au {formatDate(row.expires_at)}
          </span>
          <span className={`text-[10px] font-bold ${row.remaining_days < 30 ? 'text-rose-500' : 'text-emerald-500'}`}>
            {row.remaining_days} jour(s) restant(s)
          </span>
        </div>
      ),
    },
    {
      header: 'État Licence',
      cell: (row: LicenseItem) => (
        <Badge
          variant={row.is_valid ? 'success' : 'destructive'}
          className="text-[10px] font-bold"
        >
          {row.is_revoked ? 'Révoquée' : (row.is_valid ? 'Active & Homologuée' : 'Expirée')}
        </Badge>
      ),
    },
    {
      header: 'Actions & Certificat',
      cell: (row: LicenseItem) => (
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => downloadLicensePdf(row.id, row.store_code)}
            className="h-7 text-xs px-2.5 font-medium border-primary/30 text-primary hover:bg-primary/10"
            title="Télécharger le certificat officiel PDF à remettre au magasin"
          >
            <Download className="h-3.5 w-3.5 mr-1" /> Certificat PDF
          </Button>

          {row.is_revoked ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => toggleLicenseRevocationMutation.mutate({ licId: row.id, is_revoked: false })}
              className="h-7 text-xs px-2 text-emerald-600 border-emerald-500/30 hover:bg-emerald-500/10"
            >
              Réactiver
            </Button>
          ) : (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => {
                if (confirm(`Voulez-vous vraiment révoquer la licence du magasin "${row.store_name}" ? Le magasin ne pourra plus opérer.`)) {
                  toggleLicenseRevocationMutation.mutate({ licId: row.id, is_revoked: true });
                }
              }}
              className="h-7 text-xs px-2 bg-rose-600 hover:bg-rose-700 text-white"
            >
              Révoquer
            </Button>
          )}
        </div>
      ),
    },
  ];

  // Columns for Stores table
  const storeColumns = [
    {
      header: 'Identifiant & Magasin',
      cell: (row: StoreItem) => (
        <div className="flex items-center gap-2.5">
          <div className={`h-9 w-9 rounded-xl flex items-center justify-center font-bold text-white shadow-xs ${
            row.is_active ? 'bg-primary' : 'bg-slate-500'
          }`}>
            <StoreIcon className="h-4.5 w-4.5" />
          </div>
          <div>
            <span className="font-bold text-foreground block text-sm">{row.name}</span>
            <span className="font-mono text-xs text-muted-foreground">Code : #{row.code}</span>
          </div>
        </div>
      ),
    },
    {
      header: 'Localisation & Contact',
      cell: (row: StoreItem) => (
        <div className="text-xs space-y-0.5">
          <div className="flex items-center gap-1 text-foreground">
            <MapPin className="h-3 w-3 text-muted-foreground shrink-0" />
            <span className="truncate max-w-[220px]">{row.address || 'Adresse non renseignée'}</span>
          </div>
          {row.phone && (
            <div className="flex items-center gap-1 text-muted-foreground font-mono">
              <Phone className="h-3 w-3 shrink-0" />
              <span>{row.phone}</span>
            </div>
          )}
        </div>
      ),
    },
    {
      header: 'Responsable Affecté',
      cell: (row: StoreItem) => (
        <span className="text-xs font-semibold text-foreground">
          {row.manager_name || 'Non assigné'}
        </span>
      ),
    },
    {
      header: 'Statut d’Activité',
      cell: (row: StoreItem) => (
        <Badge
          variant={row.is_active ? 'success' : 'destructive'}
          className="text-[11px] font-bold"
        >
          {row.is_active ? 'Activité Ouverte' : 'Activité Suspendue'}
        </Badge>
      ),
    },
    {
      header: 'Actions & Contrôle d’Activité',
      cell: (row: StoreItem) => (
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => openEditStoreModal(row)}
            className="h-7 text-xs px-2.5 font-medium"
          >
            <Edit2 className="h-3.5 w-3.5 mr-1" /> Modifier
          </Button>

          {/* Bouton Suspendre / Réactiver l'activité */}
          {row.is_active ? (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => {
                if (confirm(`Voulez-vous vraiment suspendre l'activité du magasin "${row.name}" ? Aucune vente ou mouvement ne pourra être initié tant qu'il est suspendu.`)) {
                  toggleStoreStatusMutation.mutate({ storeId: row.id, is_active: false });
                }
              }}
              className="h-7 text-xs px-2.5 font-bold bg-amber-600 hover:bg-amber-700 text-white"
              title="Geler temporairement l'activité commerciale du magasin"
            >
              <PauseCircle className="h-3.5 w-3.5 mr-1" /> Suspendre Activité
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                toggleStoreStatusMutation.mutate({ storeId: row.id, is_active: true });
              }}
              className="h-7 text-xs px-2.5 font-bold text-emerald-600 border-emerald-500/40 hover:bg-emerald-500/10"
              title="Réactiver l'exploitation normale du magasin"
            >
              <PlayCircle className="h-3.5 w-3.5 mr-1" /> Réactiver Activité
            </Button>
          )}
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

  const filteredLicenses = (licensesData?.results || []).filter((l) => {
    const q = searchQuery.toLowerCase();
    return (
      l.store_name.toLowerCase().includes(q) ||
      l.license_key.toLowerCase().includes(q) ||
      l.store_code.toLowerCase().includes(q)
    );
  });

  const filteredStores = (storesData?.results || []).filter((s) => {
    const q = searchQuery.toLowerCase();
    return (
      s.name.toLowerCase().includes(q) ||
      s.code.toLowerCase().includes(q) ||
      (s.address && s.address.toLowerCase().includes(q))
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
            {activeTab === 'users' && (
              <Button onClick={openCreateUserModal} size="sm" className="font-semibold shadow-xs">
                <UserPlus className="h-4 w-4 mr-1.5" /> Nouvel Utilisateur
              </Button>
            )}
            {activeTab === 'groups' && (
              <Button onClick={openCreateGroupModal} size="sm" className="font-semibold shadow-xs">
                <Plus className="h-4 w-4 mr-1.5" /> Nouveau Profil / Groupe
              </Button>
            )}
            {activeTab === 'stores' && (
              <Button onClick={openCreateStoreModal} size="sm" className="font-semibold shadow-xs bg-primary hover:bg-primary/90 text-primary-foreground">
                <StoreIcon className="h-4 w-4 mr-1.5" /> Nouveau Magasin / Dépôt
              </Button>
            )}
            {activeTab === 'licenses' && (
              <Button
                onClick={() => {
                  setLicenseForm({
                    store: storesData?.results?.[0]?.id || '',
                    plan_type: 'PRO',
                    duration_months: 12,
                    max_registers: 3,
                    issued_to_name: storesData?.results?.[0]?.name || '',
                  });
                  setIsLicenseModalOpen(true);
                }}
                size="sm"
                className="font-semibold shadow-xs bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                <Award className="h-4 w-4 mr-1.5" /> Générer Licence Magasin
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
          <button
            type="button"
            onClick={() => setActiveTab('stores')}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-bold border-b-2 transition-all ${
              activeTab === 'stores'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <StoreIcon className="h-4 w-4" /> Magasins & Dépôts ({storesData?.results?.length || 0})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('licenses')}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-bold border-b-2 transition-all ${
              activeTab === 'licenses'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Award className="h-4 w-4" /> Licences d’Exploitation ({licensesData?.results?.length || 0})
          </button>
        </div>

        {/* Filter bar */}
        <div className="flex items-center gap-3 bg-card p-3 rounded-xl border">
          <div className="max-w-md w-full">
            <Input
              placeholder={activeTab === 'users' ? 'Rechercher un collaborateur par nom, email...' : (activeTab === 'groups' ? 'Rechercher un groupe ou profil...' : (activeTab === 'stores' ? 'Rechercher un magasin...' : 'Rechercher une licence par magasin, clé...'))}
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

        {/* TAB 3: STORES & MANAGEMENT */}
        {activeTab === 'stores' && (
          <div className="space-y-4">
            <DataTable
              columns={storeColumns}
              data={filteredStores}
              isLoading={isLoadingStores}
            />
          </div>
        )}

        {/* TAB 4: STORE LICENSES MANAGEMENT */}
        {activeTab === 'licenses' && (
          <div className="space-y-4">
            <DataTable
              columns={licenseColumns}
              data={filteredLicenses}
              isLoading={isLoadingLicenses}
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


        {/* MODAL 4: GÉNÉRER UNE LICENCE D'UTILISATION POUR UN MAGASIN */}
        <Modal
          isOpen={isLicenseModalOpen}
          onClose={() => setIsLicenseModalOpen(false)}
          title="Générer une Licence d’Utilisation Magasin"
          maxWidth="md"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              generateLicenseMutation.mutate(licenseForm);
            }}
            className="space-y-4 pt-1"
          >
            <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300">
              <div className="flex items-center gap-1.5 font-bold text-emerald-400 mb-1">
                <Award className="h-4 w-4" /> Certification de Droit d’Exploitation
              </div>
              Génération d’une clé cryptographique HMAC-SHA256 inaltérable liée au magasin bénéficiaire, avec délivrance du certificat officiel PDF.
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Sélectionner le Magasin Acquéreur *
              </label>
              <select
                required
                className="w-full h-10 px-3 rounded-lg border border-input bg-background text-xs font-bold text-foreground"
                value={licenseForm.store}
                onChange={(e) => {
                  const selStore = storesData?.results?.find((s) => s.id === e.target.value);
                  setLicenseForm({
                    ...licenseForm,
                    store: e.target.value,
                    issued_to_name: selStore ? selStore.name : '',
                  });
                }}
              >
                <option value="">-- Choisir un magasin enregistré --</option>
                {(storesData?.results || []).map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} (#{s.code})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Édition / Formule Logicielle *
                </label>
                <select
                  className="w-full h-10 px-3 rounded-lg border border-input bg-background text-xs font-medium"
                  value={licenseForm.plan_type}
                  onChange={(e) => {
                    const plan = e.target.value;
                    let maxReg = 3;
                    if (plan === 'STANDARD') maxReg = 1;
                    if (plan === 'ENTERPRISE') maxReg = 10;
                    setLicenseForm({ ...licenseForm, plan_type: plan, max_registers: maxReg });
                  }}
                >
                  <option value="STANDARD">Standard (1 Caisse)</option>
                  <option value="PRO">Professionnel (3 Caisses)</option>
                  <option value="ENTERPRISE">Entreprise Illimitée (10+ Caisses)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Durée de Validité *
                </label>
                <select
                  className="w-full h-10 px-3 rounded-lg border border-input bg-background text-xs font-medium"
                  value={licenseForm.duration_months}
                  onChange={(e) => setLicenseForm({ ...licenseForm, duration_months: parseInt(e.target.value, 10) })}
                >
                  <option value="1">1 Mois (Essai)</option>
                  <option value="6">6 Mois (Semestriel)</option>
                  <option value="12">12 Mois (Annuel - Recommandé)</option>
                  <option value="24">24 Mois (Pluriannuel)</option>
                  <option value="60">60 Mois (Quinquennal)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Nombre Maximal de Caisses / Postes *
                </label>
                <Input
                  type="number"
                  min="1"
                  required
                  value={licenseForm.max_registers}
                  onChange={(e) => setLicenseForm({ ...licenseForm, max_registers: parseInt(e.target.value, 10) || 1 })}
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Nom Inscrit sur le Certificat *
                </label>
                <Input
                  required
                  value={licenseForm.issued_to_name}
                  onChange={(e) => setLicenseForm({ ...licenseForm, issued_to_name: e.target.value })}
                  placeholder="Nom officiel du magasin ou gérant"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsLicenseModalOpen(false)}
              >
                Annuler
              </Button>
              <Button
                type="submit"
                isLoading={generateLicenseMutation.isPending}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold"
              >
                <Award className="h-4 w-4 mr-1.5" /> Émettre la Licence Officielle
              </Button>
            </div>
          </form>
        </Modal>

        {/* MODAL 3: CRÉER / MODIFIER MAGASIN */}
        <Modal
          isOpen={isStoreModalOpen}
          onClose={() => {
            setIsStoreModalOpen(false);
            resetStoreForm();
          }}
          title={editingStore ? `Modifier le Magasin : ${editingStore.name}` : 'Créer un Nouveau Magasin / Dépôt'}
          maxWidth="md"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              storeMutation.mutate({
                name: storeForm.name,
                code: storeForm.code,
                address: storeForm.address,
                phone: storeForm.phone,
                manager: storeForm.manager || null,
                is_active: storeForm.is_active,
              });
            }}
            className="space-y-4 pt-1"
          >
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Nom du Magasin / Dépôt *
                </label>
                <Input
                  required
                  value={storeForm.name}
                  onChange={(e) => setStoreForm({ ...storeForm, name: e.target.value })}
                  placeholder="Ex: Dépôt Bobo-Dioulasso"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Code Magasin Unique *
                </label>
                <Input
                  required
                  value={storeForm.code}
                  onChange={(e) => setStoreForm({ ...storeForm, code: e.target.value.toUpperCase() })}
                  placeholder="Ex: MAG-BOBO-02"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Adresse Complète / Localisation
              </label>
              <Input
                value={storeForm.address}
                onChange={(e) => setStoreForm({ ...storeForm, address: e.target.value })}
                placeholder="Ex: Secteur 4, Rue du Commerce, Bobo-Dioulasso"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Téléphone Contact
                </label>
                <Input
                  value={storeForm.phone}
                  onChange={(e) => setStoreForm({ ...storeForm, phone: e.target.value })}
                  placeholder="+226 20 98 00 00"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground block mb-1">
                  Responsable / Gérant du Magasin
                </label>
                <select
                  className="w-full h-10 px-3 rounded-lg border border-input bg-background text-xs font-medium"
                  value={storeForm.manager}
                  onChange={(e) => setStoreForm({ ...storeForm, manager: e.target.value })}
                >
                  <option value="">-- Aucun responsable assigné --</option>
                  {(usersData?.results || []).map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.first_name} {u.last_name} ({u.role})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="p-3 rounded-xl border bg-muted/20">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-medium">
                <input
                  type="checkbox"
                  checked={storeForm.is_active}
                  onChange={(e) => setStoreForm({ ...storeForm, is_active: e.target.checked })}
                  className="rounded border-input text-primary h-4 w-4"
                />
                <div>
                  <span className="font-bold text-foreground block">Activité Opérationnelle Ouverte</span>
                  <span className="text-[11px] text-muted-foreground">
                    Si décoché, l'activité commerciale du magasin est immédiatement suspendue (aucun encaissement ni transfert).
                  </span>
                </div>
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsStoreModalOpen(false);
                  resetStoreForm();
                }}
              >
                Annuler
              </Button>
              <Button type="submit" isLoading={storeMutation.isPending}>
                <CheckCircle2 className="h-4 w-4 mr-1.5" /> Enregistrer le Magasin
              </Button>
            </div>
          </form>
        </Modal>
      </div>
    </DashboardLayout>

  );
}
