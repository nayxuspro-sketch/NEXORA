# NEXORA - Design System & Directives Ergonomiques

## 1. Philosophie Visuelle & Tokens Sémantiques

Le Design System de NEXORA repose sur la rigueur et l'élégance des interfaces professionnelles modernes (style **shadcn/ui** combiné à la flexibilité de **Tailwind CSS**).

### Palette de Couleurs Sémantiques (Mode Clair & Sombre)

```css
:root {
  --background: 220 20% 98%;      /* Fond principal reposant */
  --foreground: 222.2 84% 4.9%;   /* Texte haute lisibilité */
  --card: 0 0% 100%;             /* Cartes et panneaux blancs purs */
  --primary: 221.2 83.2% 53.3%;   /* Bleu profond d'entreprise (Action clé) */
  --primary-foreground: 210 40% 98%;
  --destructive: 0 84.2% 60.2%;   /* Rouge alertes et ruptures */
  --border: 214.3 31.8% 91.4%;   /* Séparateurs discrets */
  --radius: 0.5rem;              /* Arrondi moderne équilibré */
}
```

---

## 2. Principes d'Expérience Utilisateur (UX)

1. **Vitesse & Zéro Friction** :
   - Tout workflow critique de caisse (Point de Vente) doit pouvoir se conclure en moins de 10 secondes.
   - Contrôle intégral au clavier via des raccourcis dédiés (`F2`, `F4`, `F8`, `F10`, `ESC`).
   - Palette de commande rapide universelle accessible par `Cmd + K` ou `Ctrl + K`.

2. **Densité d'Information Maîtrisée** :
   - Tableaux compacts avec étiquettes de statut claires (`Badge`).
   - Squelettes de chargement animés (`skeleton pulse`) évitant les sauts d'interface ("Cumulative Layout Shift").

3. **Responsive & Mobile First** :
   - Écrans optimisés pour smartphones (utilisation sur le terrain, inventaire en rayon) et tablettes tactiles (terminaux de caisse).
   - Tiroir de menu rétractable avec fond flouté sur petit écran.

4. **Clarté du Feedback Visuel** :
   - Système de notifications toast temporisées (4.5s) avec icônes distinctes (succès émeraude, avertissement ambre, erreur rose).
