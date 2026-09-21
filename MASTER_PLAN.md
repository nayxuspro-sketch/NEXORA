# NEXORA - Master Plan Stratégique & Feuille de Route d'Orchestration

## 1. Vision et Proposition de Valeur

**NEXORA** est un ERP et Point de Vente Intelligent (POS) nouvelle génération pour entreprises commerciales. Sa valeur s'articule autour de la chaîne séquentielle vertueuse :

$$\begin{aligned}
\mathbf{VENDRE} &\longrightarrow \text{Comptoir ultra-rapide, encaissement fluide, tickets certifiés} \\
&\downarrow \\
\mathbf{GÉRER} &\longrightarrow \text{Stock multi-dépôts, inventaires, réceptions, tiers et caisses} \\
&\downarrow \\
\mathbf{COMPRENDRE} &\longrightarrow \text{Business Intelligence explicative, marges réelles, rentabilité} \\
&\downarrow \\
\mathbf{ANTICIPER} &\longrightarrow \text{Détection des risques de rupture, rotation, stocks dormants} \\
&\downarrow \\
\mathbf{AUTOMATISER} &\longrightarrow \text{Moteur de règles conditionnelles (SI condition } \to \text{ ALORS action)}
\end{aligned}$$

---

## 2. Matrice d'Alignement des 10 Rôles Spécialisés

| Étape | Agent Spécialisé | Contrat / Périmètre | Statut |
| :---: | :--- | :--- | :---: |
| **01** | **Architecture & BDD** | Modèles de base, multi-tenant obligatoire, schémas PostgreSQL & SQLite | ✅ VALIDÉ |
| **02** | **UX/UI & Design System** | Tokens sémantiques Tailwind, accessibilité, mobile-first, style shadcn/ui | ✅ VALIDÉ |
| **03** | **Backend & API** | Django REST Framework, atomicité, OpenAPI 3.0, gestion d'erreurs | ✅ VALIDÉ |
| **04** | **Frontend Client** | Next.js 14, React 18, TanStack Query, React Hook Form, raccourcis `Cmd+K` | ✅ VALIDÉ |
| **05** | **Point de Vente (POS)** | Vente en quelques clics, raccourcis `F2/F4/F8/F10`, scan, monnaie, ticket | ✅ VALIDÉ |
| **06** | **Stock Logistique** | 11 mouvements, transferts inter-dépôts, inventaires complets/tournants | ✅ VALIDÉ |
| **07** | **Business Intelligence** | Moteur explicatif en langage naturel, dashboards par profil, KPIs | ✅ VALIDÉ |
| **08** | **IA & Automatisation** | Assistant conversationnel avec cadre d'explicabilité, moteur SI/ALORS | ✅ VALIDÉ |
| **09** | **Sécurité & Audit** | Tests d'intrusion (IDOR, RBAC, SQLi), modèle STRIDE, middleware audit | ✅ VALIDÉ |
| **10** | **Déploiement & DevOps** | Scripts 1-clic (`start-local`), stack Docker Compose, healthcheck, backup | ✅ VALIDÉ |

---

## 3. Critères d'Acceptance & Exigences d'Excellence Commerciale

1. **Non-régression absolue** : 100% des tests unitaires, d'intégration et de sécurité doivent passer (`Ran 31 tests ... OK`).
2. **Cloisonnement multi-tenant sans compromis** : Aucun identifiant ni donnée d'un client ne peut transiter vers un autre tenant (garanti par le type `TenantModel` et les tests de pénétration).
3. **Explicabilité de l'IA & IA Responsable** : Toute recommandation d'IA inclut la source, la période et la mention d'estimation indicative, sans jamais se substituer à la signature d'un décideur humain.
4. **Zéro friction de prise en main** : Démarrage local en 1 clic pour un profil non technique et déploiement de conteneurs de niveau entreprise pour la production.
