# NEXORA - Documentation des Composants UI (Design System)

L'architecture des composants UI de NEXORA suit les principes de **shadcn/ui** : des primitives réutilisables, modulaires, non dupliquées, hautement accessibles et stylées avec **Tailwind CSS**.

---

## 1. Composants Primitifs (`src/components/ui/`)

### `Button`
Bouton interactif avec gestion des états de chargement (`isLoading`), tailles et variantes sémantiques.

- **Fichier** : `src/components/ui/button.tsx`
- **Variantes** : `default`, `destructive`, `outline`, `secondary`, `ghost`, `link`
- **Tailles** : `sm`, `default`, `lg`, `icon`
- **Exemple** :
```tsx
<Button variant="default" size="lg" isLoading={isSubmitting}>
  Valider l'encaissement
</Button>
```

---

### `Input`
Champ de saisie textuelle enrichi avec support d'icônes à gauche et affichage automatique des messages d'erreur.

- **Fichier** : `src/components/ui/input.tsx`
- **Propriétés** : `error?: string`, `icon?: React.ReactNode`
- **Exemple** :
```tsx
<Input
  placeholder="Scanner code-barres..."
  value={barcode}
  onChange={(e) => setBarcode(e.target.value)}
  icon={<Search className="h-4 w-4" />}
  error={errors.barcode?.message}
/>
```

---

### `Card`, `CardHeader`, `CardTitle`, `CardContent`, `CardFooter`
Ensemble de blocs structurants pour l'affichage de métriques, formulaires ou sections de contenu.

- **Fichier** : `src/components/ui/card.tsx`
- **Exemple** :
```tsx
<Card>
  <CardHeader>
    <CardTitle>Session de Caisse</CardTitle>
  </CardHeader>
  <CardContent>
    <p>Solde actuel : 450,00 €</p>
  </CardContent>
</Card>
```

---

### `Badge`
Indicateur visuel d'état (statut de commande, niveau de stock, type de partenaire).

- **Fichier** : `src/components/ui/badge.tsx`
- **Variantes** : `default`, `secondary`, `destructive`, `outline`, `success`, `warning`
- **Exemple** :
```tsx
<Badge variant="success">PAYÉ</Badge>
<Badge variant="warning">STOCK BAS</Badge>
```

---

### `Modal`
Fenêtre modale accessible avec fond flouté, fermeture par touche `Échap`, clic extérieur et animation fluide.

- **Fichier** : `src/components/ui/modal.tsx`
- **Propriétés** : `isOpen`, `onClose`, `title`, `description`, `children`, `footer`, `maxWidth`
- **Exemple** :
```tsx
<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Ajouter un Produit"
  maxWidth="lg"
>
  <ProductForm onSubmit={handleSubmit} />
</Modal>
```

---

### `DataTable`
Tableau de données générique, réactif, supportant le chargement par squelette (`skeleton pulse`), les colonnes sur-mesure et la pagination.

- **Fichier** : `src/components/ui/data-table.tsx`
- **Propriétés** : `columns`, `data`, `isLoading`, `emptyMessage`, `pagination`
- **Exemple** :
```tsx
<DataTable
  columns={[
    { header: 'Article', cell: (row) => <span>{row.name}</span> },
    { header: 'Prix', cell: (row) => <span>{formatCurrency(row.price)}</span> },
  ]}
  data={products}
  isLoading={isLoading}
  pagination={{
    currentPage: 1,
    totalPages: 5,
    onPageChange: (p) => setPage(p),
  }}
/>
```

---

### `KpiCard`
Carte de synthèse analytique mettant en valeur un KPI clé, son évolution en pourcentage et une icône dédiée.

- **Fichier** : `src/components/ui/kpi-card.tsx`
- **Propriétés** : `title`, `value`, `change`, `changeType` (`positive` | `negative` | `neutral`), `icon`, `description`
- **Exemple** :
```tsx
<KpiCard
  title="Chiffre d'Affaires"
  value="48 950,00 €"
  change="+14.2%"
  changeType="positive"
  icon={<TrendingUp className="h-5 w-5" />}
/>
```

---

### `SimpleBarChart`
Composant de visualisation graphique en colonnes avec infobulles au survol pour les tendances de ventes et marges.

- **Fichier** : `src/components/ui/simple-chart.tsx`
- **Exemple** :
```tsx
<SimpleBarChart
  title="Ventes de la semaine"
  data={[
    { label: 'Lun', value: 4500 },
    { label: 'Mar', value: 6800 },
  ]}
/>
```

---

### `Toast` & `ToastProvider`
Système de notifications toast non intrusif pour les alertes d'action (succès d'encaissement, erreur de saisie).

- **Fichier** : `src/components/ui/toast.tsx`
- **Hook** : `useToast()`
- **Exemple** :
```tsx
const { toast } = useToast();
toast({
  type: 'success',
  title: 'Vente effectuée',
  message: 'Le ticket VNT-001 a été édité.',
});
```

---

## 2. Composants de Layout (`src/components/layout/`)

### `Sidebar`
Navigation principale de l'ERP avec affichage de l'entreprise connectée, rôle utilisateur, badges directs et déclenchement mobile.

### `Topbar`
Barre d'en-tête supérieure avec raccourci de recherche globale (`Cmd + K`), notifications et informations de profil.

### `QuickSearchModal`
Palette de commandes rapide pour accéder instantanément à n'importe quel écran clé sans utiliser la souris.

### `DashboardLayout`
Conteneur principal enveloppant les pages avec la structure Sidebar + Topbar + Zone de contenu réactive.
