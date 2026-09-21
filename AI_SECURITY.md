# NEXORA - Sécurité, Confidentialité & Éthique de l'IA

## 1. Cloisonnement Multi-Tenant de l'IA

L'assistant conversationnel et les moteurs de prédiction appliquent un partitionnement strict :
- L'IA filtre systématiquement et nativement les requêtes par `company_id`.
- Il est mathématiquement et logiquement impossible qu'une réponse fournie à l'utilisateur de l'entreprise A s'appuie sur, ou divulgue, les données de l'entreprise B.

---

## 2. Respect Rigoureux du RBAC (Contrôle d'Accès basé sur les Rôles)

L'IA n'est pas un pont permettant de contourner les droits d'accès :
- Si un utilisateur au rôle `CASHIER` ou `STOCK_KEEPER` interroge l'IA sur la marge nette, les bénéfices de l'entreprise ou les coûts d'achat confidentiels, l'IA bloque la requête avec le message :
  *« Accès restreint : Votre rôle actuel ne vous permet pas de consulter les données de marge financière et de rentabilité. »*
- Le caissier est cantonné aux métriques de son propre tiroir de caisse et de sa journée.

---

## 3. Garde-Fous & Non-Substitution Décisionnelle

- L'IA n'a pas le pouvoir de :
  - Débiter un compte bancaire ou émettre un paiement réel.
  - Modifier le prix de vente catalogue sans validation humaine.
  - Passer une commande d'achat ferme engageant juridiquement l'entreprise.
- Les actions automatisées se limitent à la création d'alertes ou de brouillons nécessitant une signature humaine finale.
