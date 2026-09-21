'use client';

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Modal } from '@/components/ui/modal';
import { Input } from '@/components/ui/input';
import { DataTable } from '@/components/ui/data-table';
import { useToast } from '@/components/ui/toast';
import { apiRequest } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import {
  Workflow,
  Plus,
  Play,
  CheckCircle2,
  AlertTriangle,
  History,
  Zap,
  Bell,
  Mail,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';

interface AutomationRuleItem {
  id: string;
  name: string;
  description: string;
  trigger_type: string;
  action_type: string;
  parameters: any;
  is_active: boolean;
  last_triggered_at: string | null;
  execution_count: number;
  created_at: string;
}

export default function AutomationPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [isNewRuleModalOpen, setIsNewRuleModalOpen] = React.useState(false);

  const [ruleForm, setRuleForm] = React.useState({
    name: '',
    description: '',
    trigger_type: 'STOCK_BELOW_THRESHOLD',
    action_type: 'CREATE_NOTIFICATION',
    threshold: '5',
    days_overdue: '15',
  });

  // Query rules
  const { data: rulesData, isLoading } = useQuery<{ results: AutomationRuleItem[] }>({
    queryKey: ['automation-rules'],
    queryFn: () => apiRequest('/automation-rules/'),
    placeholderData: {
      results: [
        {
          id: 'rule-1',
          name: 'Alerte Rupture de Stock Préventive',
          description: 'Alerte les responsables dès qu\'un produit passe sous le seuil critique.',
          trigger_type: 'STOCK_BELOW_THRESHOLD',
          action_type: 'CREATE_NOTIFICATION',
          parameters: { threshold: 5 },
          is_active: true,
          last_triggered_at: new Date().toISOString(),
          execution_count: 14,
          created_at: new Date().toISOString(),
        },
        {
          id: 'rule-2',
          name: 'Relance Factures Clients Impayées',
          description: 'Notifie la comptabilité pour toute facture non réglée après 15 jours.',
          trigger_type: 'OVERDUE_INVOICE',
          action_type: 'CREATE_NOTIFICATION',
          parameters: { days_overdue: 15 },
          is_active: true,
          last_triggered_at: new Date(Date.now() - 86400000).toISOString(),
          execution_count: 6,
          created_at: new Date().toISOString(),
        },
      ],
    },
  });

  // Trigger engine manually
  const triggerMutation = useMutation({
    mutationFn: async () => {
      return await apiRequest('/automation-rules/trigger_engine/', {
        method: 'POST',
      });
    },
    onSuccess: (data: any) => {
      toast({
        type: 'success',
        title: 'Moteur exécuté',
        message: data.message || 'Évaluation des règles terminée avec succès.',
      });
      queryClient.invalidateQueries({ queryKey: ['automation-rules'] });
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur',
        message: err.message || 'Impossible d\'exécuter le moteur d\'automatisation.',
      });
    },
  });

  // Create rule mutation
  const createRuleMutation = useMutation({
    mutationFn: async (data: typeof ruleForm) => {
      return await apiRequest('/automation-rules/', {
        method: 'POST',
        body: JSON.stringify({
          name: data.name,
          description: data.description,
          trigger_type: data.trigger_type,
          action_type: data.action_type,
          parameters:
            data.trigger_type === 'STOCK_BELOW_THRESHOLD'
              ? { threshold: Number(data.threshold) }
              : { days_overdue: Number(data.days_overdue) },
          is_active: true,
        }),
      });
    },
    onSuccess: () => {
      toast({
        type: 'success',
        title: 'Règle créée',
        message: 'La règle d\'automatisation est désormais active.',
      });
      setIsNewRuleModalOpen(false);
      setRuleForm({
        name: '',
        description: '',
        trigger_type: 'STOCK_BELOW_THRESHOLD',
        action_type: 'CREATE_NOTIFICATION',
        threshold: '5',
        days_overdue: '15',
      });
      queryClient.invalidateQueries({ queryKey: ['automation-rules'] });
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Erreur',
        message: err.message || 'Impossible d\'enregistrer la règle.',
      });
    },
  });

  const columns = [
    {
      header: 'Règle d\'Automatisation',
      cell: (row: AutomationRuleItem) => (
        <div>
          <p className="font-bold text-foreground">{row.name}</p>
          <p className="text-xs text-muted-foreground">{row.description}</p>
        </div>
      ),
    },
    {
      header: 'Déclencheur (SI Condition)',
      cell: (row: AutomationRuleItem) => (
        <Badge variant="outline" className="text-xs font-mono">
          {row.trigger_type}
        </Badge>
      ),
    },
    {
      header: 'Action Réalisée (ALORS Action)',
      cell: (row: AutomationRuleItem) => (
        <Badge variant="default" className="text-xs">
          {row.action_type}
        </Badge>
      ),
    },
    {
      header: 'Dernière Exécution',
      cell: (row: AutomationRuleItem) => (
        <span className="text-xs text-muted-foreground">
          {row.last_triggered_at ? formatDate(row.last_triggered_at) : 'Jamais'}
        </span>
      ),
    },
    {
      header: 'Compteur',
      cell: (row: AutomationRuleItem) => (
        <span className="font-bold text-primary">{row.execution_count} fois</span>
      ),
    },
    {
      header: 'Statut',
      cell: (row: AutomationRuleItem) => (
        <Badge variant={row.is_active ? 'success' : 'destructive'}>
          {row.is_active ? 'Active' : 'Désactivée'}
        </Badge>
      ),
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-foreground flex items-center gap-2">
              <Zap className="h-6 w-6 text-amber-500" /> Moteur d'Automatisation & Règles Métier
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
              Architecture conditionnelle : <span className="font-semibold text-primary">SI &lt;condition&gt; → ALORS &lt;action&gt;</span>
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => triggerMutation.mutate()}
              isLoading={triggerMutation.isPending}
              className="text-xs font-bold"
            >
              <Play className="h-4 w-4 mr-1.5 text-emerald-600" /> Évaluer les Règles Maintenant
            </Button>
            <Button size="sm" onClick={() => setIsNewRuleModalOpen(true)} className="text-xs font-bold">
              <Plus className="h-4 w-4 mr-1.5" /> Nouvelle Règle
            </Button>
          </div>
        </div>

        {/* Informational banner */}
        <div className="p-4 rounded-xl border bg-card text-xs text-muted-foreground flex items-start gap-3 shadow-xs">
          <Workflow className="h-5 w-5 text-primary shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-bold text-foreground">Principe de l'IA Responsable & Automatisation</p>
            <p>
              Les règles automatisées déchargent les équipes des tâches répétitives (alertes de réassort, relances).
              Les actions critiques impliquant des engagements financiers restent soumises à la validation finale de l'utilisateur.
            </p>
          </div>
        </div>

        {/* Rules Table */}
        <DataTable columns={columns} data={rulesData?.results || []} isLoading={isLoading} />

        {/* Create Rule Modal */}
        <Modal
          isOpen={isNewRuleModalOpen}
          onClose={() => setIsNewRuleModalOpen(false)}
          title="Créer une Règle d'Automatisation"
          maxWidth="md"
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createRuleMutation.mutate(ruleForm);
            }}
            className="space-y-4 pt-2"
          >
            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Nom de la règle *
              </label>
              <Input
                required
                placeholder="Ex: Alerte rupture automatique"
                value={ruleForm.name}
                onChange={(e) => setRuleForm({ ...ruleForm, name: e.target.value })}
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground block mb-1">
                Description métier
              </label>
              <Input
                placeholder="Explication du comportement..."
                value={ruleForm.description}
                onChange={(e) => setRuleForm({ ...ruleForm, description: e.target.value })}
              />
            </div>

            <div className="p-3 rounded-xl bg-muted/40 border space-y-3">
              <div>
                <label className="text-xs font-bold text-foreground block mb-1">
                  1. Déclencheur : SI Condition *
                </label>
                <select
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                  value={ruleForm.trigger_type}
                  onChange={(e) => setRuleForm({ ...ruleForm, trigger_type: e.target.value })}
                >
                  <option value="STOCK_BELOW_THRESHOLD">Le stock d'un produit passe sous son seuil d'alerte</option>
                  <option value="OVERDUE_INVOICE">Une vente / facture client dépasse X jours d'impayé</option>
                </select>
              </div>

              {ruleForm.trigger_type === 'OVERDUE_INVOICE' && (
                <div>
                  <label className="text-xs font-semibold text-muted-foreground block mb-1">
                    Jours d'impayé avant déclenchement
                  </label>
                  <Input
                    type="number"
                    min="1"
                    value={ruleForm.days_overdue}
                    onChange={(e) => setRuleForm({ ...ruleForm, days_overdue: e.target.value })}
                  />
                </div>
              )}
            </div>

            <div className="p-3 rounded-xl bg-muted/40 border space-y-3">
              <div>
                <label className="text-xs font-bold text-foreground block mb-1">
                  2. Conséquence : ALORS Action *
                </label>
                <select
                  className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm"
                  value={ruleForm.action_type}
                  onChange={(e) => setRuleForm({ ...ruleForm, action_type: e.target.value })}
                >
                  <option value="CREATE_NOTIFICATION">Créer une notification prioritaire pour les gérants</option>
                  <option value="LOG_AUDIT_WARNING">Consigner un événement d'avertissement dans le journal d'audit</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setIsNewRuleModalOpen(false)}>
                Annuler
              </Button>
              <Button type="submit" isLoading={createRuleMutation.isPending}>
                Activer la Règle
              </Button>
            </div>
          </form>
        </Modal>
      </div>
    </DashboardLayout>
  );
}
