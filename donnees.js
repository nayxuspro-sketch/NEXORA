/* ============================================================
   NEXORA — Données métier de la fenêtre
   « Configurer les Droits : Direction & Administration Générale »
   Tous les libellés sont en français (fr-FR).
   ============================================================ */

const NIVEAUX = [
  { id: "aucun",        libelle: "Aucun",           couleur: "neutre",     ordre: 0 },
  { id: "lecture",      libelle: "Lecture",         couleur: "info",       ordre: 1 },
  { id: "creation",     libelle: "Création",        couleur: "positif",    ordre: 2 },
  { id: "modification", libelle: "Modification",    couleur: "averti",     ordre: 3 },
  { id: "suppression",  libelle: "Suppression",     couleur: "negatif",    ordre: 4 },
  { id: "complet",      libelle: "Accès complet",   couleur: "accent",     ordre: 5 }
];

const PORTEES = [
  { id: "personnelle", libelle: "Mes données uniquement" },
  { id: "equipe",      libelle: "Mon équipe" },
  { id: "structure",   libelle: "Ma structure" },
  { id: "groupe",      libelle: "Mon groupe de sociétés" },
  { id: "totale",      libelle: "Toutes les données" }
];

const ACTIONS_DROIT = [
  { id: "consulter",  libelle: "Consulter",              icone: "👁" },
  { id: "creer",      libelle: "Créer",                  icone: "＋" },
  { id: "modifier",   libelle: "Modifier",               icone: "✎" },
  { id: "supprimer",  libelle: "Supprimer",              icone: "🗑" },
  { id: "valider",    libelle: "Valider",                icone: "✓" },
  { id: "rejeter",    libelle: "Rejeter",                icone: "✕" },
  { id: "signer",     libelle: "Signer électroniquement", icone: "🖋" },
  { id: "deleguer",   libelle: "Déléguer",               icone: "⇄" },
  { id: "exporter",   libelle: "Exporter",               icone: "⭳" },
  { id: "imprimer",   libelle: "Imprimer",               icone: "🖨" },
  { id: "archiver",   libelle: "Archiver",               icone: "🗄" }
];

/* ---- Modules et droits du périmètre Direction & Administration Générale ---- */
const MODULES = [
  {
    id: "direction-generale",
    titre: "Direction Générale",
    description: "Pilotage stratégique et instances de gouvernance.",
    icone: "🏛",
    droits: [
      { id: "tableau-de-bord",    libelle: "Tableau de bord de direction",        niveau: "complet",        portee: "totale" },
      { id: "indicateurs",        libelle: "Indicateurs de performance (KPI)",    niveau: "modification",   portee: "groupe" },
      { id: "notes-de-service",   libelle: "Notes de service & décisions",        niveau: "complet",        portee: "totale" },
      { id: "conseil-adm",        libelle: "Conseil d'administration & procès-verbaux", niveau: "lecture",  portee: "structure" },
      { id: "budget-annuel",      libelle: "Budget annuel et plan stratégique",   niveau: "modification",   portee: "groupe" },
      { id: "delegation-pouvoir", libelle: "Délégations de pouvoirs et de signature", niveau: "complet",    portee: "totale", sensible: true }
    ]
  },
  {
    id: "administration-generale",
    titre: "Administration Générale",
    description: "Courrier, contrats et formalités de l'entreprise.",
    icone: "🗂",
    droits: [
      { id: "courrier-arrive",     libelle: "Courrier arrivé",                    niveau: "modification", portee: "structure" },
      { id: "courrier-depart",     libelle: "Courrier départ",                    niveau: "creation",     portee: "structure" },
      { id: "registre-courrier",   libelle: "Registre du courrier",               niveau: "lecture",      portee: "totale" },
      { id: "contrats",            libelle: "Contrats & conventions",             niveau: "modification", portee: "groupe", sensible: true },
      { id: "paraphes",            libelle: "Paraphes et signatures",             niveau: "complet",      portee: "totale", sensible: true },
      { id: "documents-officiels", libelle: "Documents officiels & pièces administratives", niveau: "lecture", portee: "structure" },
      { id: "archivage",           libelle: "Archivage & plan de classement",     niveau: "modification", portee: "structure" }
    ]
  },
  {
    id: "ressources-humaines",
    titre: "Ressources Humaines",
    description: "Dossiers du personnel, temps, paie et recrutement.",
    icone: "👥",
    droits: [
      { id: "dossiers-personnel",   libelle: "Dossiers du personnel",        niveau: "modification", portee: "structure", sensible: true },
      { id: "contrats-travail",     libelle: "Contrats de travail & avenants", niveau: "modification", portee: "structure" },
      { id: "conges-absences",      libelle: "Congés & absences",            niveau: "complet",      portee: "structure" },
      { id: "pointage",             libelle: "Pointages & horaires",         niveau: "lecture",      portee: "equipe" },
      { id: "paie",                 libelle: "Paie & bulletins",             niveau: "lecture",      portee: "structure", sensible: true },
      { id: "declarations-sociales",libelle: "Déclarations sociales",        niveau: "creation",     portee: "structure" },
      { id: "recrutement",          libelle: "Recrutement & mobilité interne", niveau: "modification", portee: "structure" },
      { id: "formation",            libelle: "Formation & évaluations",      niveau: "modification", portee: "structure" },
      { id: "discipline",           libelle: "Procédures disciplinaires",    niveau: "aucun",        portee: "personnelle", sensible: true }
    ]
  },
  {
    id: "finances-comptabilite",
    titre: "Finances & Comptabilité",
    description: "Comptabilité, trésorerie, fiscalité et reporting.",
    icone: "💰",
    droits: [
      { id: "ecritures",      libelle: "Écritures comptables",          niveau: "modification", portee: "structure" },
      { id: "journal",        libelle: "Journaux & grand livre",        niveau: "lecture",      portee: "totale" },
      { id: "rapprochement",  libelle: "Rapprochement bancaire",        niveau: "modification", portee: "structure" },
      { id: "tresorerie",     libelle: "Trésorerie & placements",       niveau: "lecture",      portee: "groupe", sensible: true },
      { id: "virements",      libelle: "Virements & ordres de paiement", niveau: "aucun",       portee: "structure", sensible: true },
      { id: "budget-suivi",   libelle: "Budget & suivi budgétaire",     niveau: "modification", portee: "groupe" },
      { id: "declarations-fiscales", libelle: "Déclarations fiscales",  niveau: "creation",     portee: "structure" },
      { id: "cloture",        libelle: "Clôture & bilan",               niveau: "aucun",        portee: "totale", sensible: true },
      { id: "reporting",      libelle: "Reporting financier & tableaux de bord", niveau: "lecture", portee: "groupe" }
    ]
  },
  {
    id: "achats",
    titre: "Achats & Approvisionnements",
    description: "Fournisseurs, commandes et appels d'offres.",
    icone: "🛒",
    droits: [
      { id: "fournisseurs",        libelle: "Fournisseurs & qualification", niveau: "modification", portee: "structure" },
      { id: "demandes-achat",      libelle: "Demandes d'achat",             niveau: "complet",      portee: "structure" },
      { id: "commandes",           libelle: "Commandes d'achat",            niveau: "modification", portee: "structure" },
      { id: "appels-offres",       libelle: "Appels d'offres & consultation", niveau: "lecture",    portee: "groupe" },
      { id: "reception",           libelle: "Réception & conformité",       niveau: "modification", portee: "equipe" },
      { id: "factures-fournisseurs", libelle: "Factures fournisseurs",      niveau: "lecture",      portee: "structure" },
      { id: "contrats-cadres",     libelle: "Contrats-cadres",              niveau: "lecture",      portee: "groupe" }
    ]
  },
  {
    id: "juridique",
    titre: "Juridique & Conformité",
    description: "Contentieux, conformité réglementaire et assurances.",
    icone: "⚖",
    droits: [
      { id: "contentieux",      libelle: "Contentieux & litiges",                          niveau: "modification", portee: "groupe" },
      { id: "conformite",       libelle: "Conformité réglementaire",                       niveau: "lecture",      portee: "totale" },
      { id: "protection-donnees", libelle: "Protection des données personnelles (RGPD/APDP)", niveau: "modification", portee: "totale", sensible: true },
      { id: "assurances",       libelle: "Assurances & sinistres",                         niveau: "modification", portee: "groupe" },
      { id: "propriete-intellectuelle", libelle: "Propriété intellectuelle & marques",     niveau: "lecture",      portee: "groupe" },
      { id: "registre-traitements", libelle: "Registre des traitements",                   niveau: "modification", portee: "totale" }
    ]
  },
  {
    id: "services-generaux",
    titre: "Services Généraux & Patrimoine",
    description: "Moyens généraux, logistique et immobilisations.",
    icone: "🏢",
    droits: [
      { id: "immobilisations", libelle: "Immobilisations & inventaire physique", niveau: "modification", portee: "groupe" },
      { id: "vehicules",       libelle: "Parc automobile & carburant",           niveau: "complet",      portee: "structure" },
      { id: "locaux",          libelle: "Locaux & entretien",                    niveau: "modification", portee: "structure" },
      { id: "securite-physique", libelle: "Sécurité & contrôle d'accès",         niveau: "lecture",      portee: "structure" },
      { id: "frais-generaux",  libelle: "Frais généraux & notes de frais",       niveau: "modification", portee: "equipe" },
      { id: "fournitures",     libelle: "Fournitures & petit matériel",          niveau: "complet",      portee: "equipe" }
    ]
  },
  {
    id: "informatique",
    titre: "Informatique & Sécurité",
    description: "Comptes, habilitations et exploitation.",
    icone: "🔐",
    droits: [
      { id: "comptes",         libelle: "Comptes utilisateurs",         niveau: "lecture",      portee: "structure", sensible: true },
      { id: "habilitations",   libelle: "Habilitations & rôles",        niveau: "aucun",        portee: "totale",      sensible: true },
      { id: "journal-audit",   libelle: "Journal d'audit & traçabilité", niveau: "lecture",     portee: "totale" },
      { id: "sauvegardes",     libelle: "Sauvegardes & plan de reprise", niveau: "aucun",      portee: "structure" },
      { id: "parametrage",     libelle: "Paramétrage applicatif",       niveau: "aucun",        portee: "structure" },
      { id: "politique-securite", libelle: "Politique de sécurité (PSSI)", niveau: "lecture",  portee: "totale" }
    ]
  }
];

/* ---- Actions autorisées par défaut selon le niveau choisi ---- */
const ACTIONS_PAR_NIVEAU = {
  aucun:        [],
  lecture:      ["consulter", "imprimer"],
  creation:     ["consulter", "creer", "imprimer"],
  modification: ["consulter", "creer", "modifier", "exporter", "imprimer"],
  suppression:  ["consulter", "creer", "modifier", "supprimer", "exporter", "imprimer"],
  complet:      ["consulter", "creer", "modifier", "supprimer", "valider", "signer", "exporter", "imprimer", "archiver"]
};

/* ---- Structures / entités ---- */
const STRUCTURES = [
  { id: "toutes",  libelle: "Toutes les structures" },
  { id: "dg",      libelle: "Direction Générale" },
  { id: "sg",      libelle: "Secrétariat Général" },
  { id: "daf",     libelle: "Direction Administrative et Financière" },
  { id: "drh",     libelle: "Direction des Ressources Humaines" },
  { id: "jur",     libelle: "Service Juridique & Conformité" },
  { id: "achats",  libelle: "Service Achats & Approvisionnements" },
  { id: "sgx",     libelle: "Services Généraux" },
  { id: "dsi",     libelle: "Direction des Systèmes d'Information" }
];

/* ---- Circuits de validation & seuils d'engagement (montants en FCFA) ---- */
const CIRCUITS = [
  {
    id: "engagement-depense", operation: "Engagement de dépense",
    seuil: 5000000, validateur: "directeurAdministratifFinancier",
    secondValidateur: "directeurGeneral", delai: "deuxJours", auDela: "comiteDirection"
  },
  {
    id: "bon-commande", operation: "Bon de commande",
    seuil: 2000000, validateur: "responsableAchats",
    secondValidateur: "directeurAdministratifFinancier", delai: "unJour", auDela: "directionGenerale"
  },
  {
    id: "facture-fournisseur", operation: "Facture fournisseur",
    seuil: 3000000, validateur: "chefServiceComptabilite",
    secondValidateur: "directeurAdministratifFinancier", delai: "troisJours", auDela: "directionGenerale"
  },
  {
    id: "virement", operation: "Virement bancaire",
    seuil: 10000000, validateur: "directeurAdministratifFinancier",
    secondValidateur: "directeurGeneral", delai: "unJour", auDela: "comiteDirection"
  },
  {
    id: "note-de-frais", operation: "Note de frais",
    seuil: 500000, validateur: "secretaireGeneral",
    secondValidateur: "", delai: "troisJours", auDela: "directionGenerale"
  },
  {
    id: "recrutement", operation: "Recrutement / embauche",
    seuil: 0, validateur: "directeurRessourcesHumaines",
    secondValidateur: "directeurGeneral", delai: "cinqJours", auDela: "comiteDirection"
  },
  {
    id: "conge-exceptionnel", operation: "Congé exceptionnel",
    seuil: 0, validateur: "directeurRessourcesHumaines",
    secondValidateur: "", delai: "deuxJours", auDela: "directionGenerale"
  },
  {
    id: "contrat", operation: "Contrat & convention",
    seuil: 15000000, validateur: "juriste",
    secondValidateur: "directeurGeneral", delai: "cinqJours", auDela: "comiteDirection"
  },
  {
    id: "avoir", operation: "Avoir / annulation de pièce",
    seuil: 1000000, validateur: "controleurGestion",
    secondValidateur: "chefServiceComptabilite", delai: "deuxJours", auDela: "blocage"
  }
];

/* ---- Profils / modèles de droits prêts à l'emploi ---- */
const PROFILS = [
  { id: "direction-generale",  nom: "Direction Générale — Accès complet",      utilisateurs: 2,  resume: "Tous les modules en accès complet, signature électronique incluse." },
  { id: "secretaire-general",  nom: "Secrétaire Général — Pilotage",           utilisateurs: 1,  resume: "Pilotage transversal, validation des courriers et paraphe." },
  { id: "daf",                 nom: "Directeur Administratif et Financier",    utilisateurs: 1,  resume: "Finances, comptabilité, achats et services généraux." },
  { id: "assistant-direction", nom: "Assistant(e) de Direction",               utilisateurs: 4,  resume: "Courrier, agenda, classement ; lecture des dossiers de direction." },
  { id: "responsable-rh",      nom: "Responsable Ressources Humaines",         utilisateurs: 2,  resume: "Administration du personnel, congés, paie en consultation." },
  { id: "controleur-gestion",  nom: "Contrôleur de gestion — Lecture seule",   utilisateurs: 3,  resume: "Lecture et export des données budgétaires et comptables." },
  { id: "audit",               nom: "Auditeur interne — Lecture & export",     utilisateurs: 2,  resume: "Lecture globale, journal d'audit, export autorisé, aucune écriture." }
];

/* ---- Historique des modifications (traçabilité) ---- */
const HISTORIQUE = [
  { date: "28/09/2026 09:14", utilisateur: "A. OUÉDRAOGO",  module: "Finances & Comptabilité", avant: "Lecture",     apres: "Modification", droit: "Écritures comptables" },
  { date: "24/09/2026 16:02", utilisateur: "M. SAWADOGO",   module: "Ressources Humaines",     avant: "Modification", apres: "Aucun",        droit: "Procédures disciplinaires" },
  { date: "19/09/2026 11:47", utilisateur: "A. OUÉDRAOGO",  module: "Informatique & Sécurité",  avant: "Aucun",       apres: "Lecture",      droit: "Journal d'audit & traçabilité" },
  { date: "12/09/2026 08:31", utilisateur: "R. ZONGO",      module: "Juridique & Conformité",   avant: "Lecture",     apres: "Modification", droit: "Protection des données personnelles" }
];

/* ---- Paires de droits à contrôler (séparation des tâches) ---- */
const REGLES_SEPARATION = [
  { droit1: "Virements & ordres de paiement", droit2: "Rapprochement bancaire", module: "Finances & Comptabilité" },
  { droit1: "Paie & bulletins",               droit2: "Virements & ordres de paiement", module: "Finances & Comptabilité" },
  { droit1: "Commandes d'achat",              droit2: "Factures fournisseurs",  module: "Achats & Approvisionnements" },
  { droit1: "Habilitations & rôles",          droit2: "Journal d'audit & traçabilité", module: "Informatique & Sécurité" }
];

const UTILISATEURS_RATTACHES = 14;
const DERNIERE_MODIFICATION = "28 septembre 2026 à 09:14";
