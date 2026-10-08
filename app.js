/* ============================================================
   NEXORA — Logique de la fenêtre
   « Configurer les Droits : Direction & Administration Générale »
   Interface intégralement en français (fr-FR).
   ============================================================ */

(function () {
  "use strict";

  /* ---------- Chaînes françaises (chargées depuis i18n/fr-FR.json) ---------- */
  let CHAINES = null;

  /* ---------- État ---------- */
  const etatInitial = MODULES.map(cloneModule);
  let etatCourant = MODULES.map(cloneModule);
  let groupeOuvert = new Set([MODULES[0].id, MODULES[1].id]);
  let filtreTexte = "";
  let uniquementModifies = false;

  /* ---------- Utilitaires ---------- */
  function cloneModule(m) {
    return {
      ...m,
      droits: m.droits.map(d => ({ ...d, actions: new Set(ACTIONS_PAR_NIVEAU[d.niveau]) }))
    };
  }

  function normaliser(texte) {
    return String(texte || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function niveau(niveauId) {
    return NIVEAUX.find(n => n.id === niveauId) || NIVEAUX[0];
  }

  function portee(porteeId) {
    return (PORTEES.find(p => p.id === porteeId) || PORTEES[0]).libelle;
  }

  function formaterMontant(valeur) {
    return new Intl.NumberFormat("fr-FR", { style: "currency", currency: "XOF", maximumFractionDigits: 0 })
      .format(valeur || 0);
  }

  function element(tag, classes, texte) {
    const noeud = document.createElement(tag);
    if (classes) noeud.className = classes;
    if (texte !== undefined) noeud.textContent = texte;
    return noeud;
  }

  function notifier(message, type) {
    const zone = document.getElementById("notifications");
    const n = element("div", "notification" + (type ? " " + type : ""), message);
    zone.appendChild(n);
    setTimeout(() => { n.style.opacity = "0"; n.style.transition = "opacity .3s"; }, 3600);
    setTimeout(() => n.remove(), 4000);
  }

  /* ---------- Différences avec l'état enregistré ---------- */
  function droitModifie(moduleId, droitId) {
    const avant = etatInitial.find(m => m.id === moduleId)?.droits.find(d => d.id === droitId);
    const apres = etatCourant.find(m => m.id === moduleId)?.droits.find(d => d.id === droitId);
    if (!avant || !apres) return false;
    if (avant.niveau !== apres.niveau || avant.portee !== apres.portee || avant.actif !== apres.actif) return true;
    const a = [...avant.actions].sort().join("|");
    const b = [...apres.actions].sort().join("|");
    return a !== b;
  }

  function nombreModifications() {
    let n = 0;
    etatCourant.forEach(m => m.droits.forEach(d => { if (droitModifie(m.id, d.id)) n++; }));
    return n;
  }

  /* ---------- État d'un droit (Autorisé / Partiel / Refusé) ---------- */
  function etatDroit(d) {
    if (d.actif === false || d.niveau === "aucun") return { cle: "refuse", libelle: "Refusé", classe: "negatif" };
    const total = d.actions.size;
    if (total === 0) return { cle: "refuse", libelle: "Refusé", classe: "negatif" };
    if (total < ACTIONS_PAR_NIVEAU[d.niveau].length) return { cle: "partiel", libelle: "Partiel", classe: "averti" };
    return { cle: "autorise", libelle: "Autorisé", classe: "positif" };
  }

  /* ============================================================
     Rendu — Bandeau de contexte
     ============================================================ */
  function remplirSelects() {
    const selectProfil = document.getElementById("select-profil");
    PROFILS.forEach(p => selectProfil.appendChild(new Option(p.nom, p.id)));
    selectProfil.value = "direction-generale";

    const selectStructure = document.getElementById("select-structure");
    STRUCTURES.forEach(s => selectStructure.appendChild(new Option(s.libelle, s.id)));
    selectStructure.value = "toutes";

    const selectNiveau = document.getElementById("select-niveau-defaut");
    NIVEAUX.forEach(n => selectNiveau.appendChild(new Option(n.libelle, n.id)));
    selectNiveau.value = "lecture";

    const selectDelegue = document.getElementById("select-delegue");
    Object.entries({
      directeurGeneral: "Directeur Général",
      secretaireGeneral: "Secrétaire Général",
      directeurAdministratifFinancier: "Directeur Administratif et Financier",
      directeurRessourcesHumaines: "Directeur des Ressources Humaines",
      chefServiceComptabilite: "Chef de service Comptabilité",
      responsableAchats: "Responsable Achats",
      juriste: "Juriste d'entreprise",
      controleurGestion: "Contrôleur de gestion"
    }).forEach(([cle, libelle]) => selectDelegue.appendChild(new Option(libelle, cle)));
    selectDelegue.value = "secretaireGeneral";

    document.getElementById("nombre-utilisateurs").textContent = UTILISATEURS_RATTACHES;
    document.getElementById("derniere-modification").textContent = DERNIERE_MODIFICATION;
  }

  /* ============================================================
     Rendu — Matrice des droits
     ============================================================ */
  function matriceFiltree() {
    const q = normaliser(filtreTexte);
    return etatCourant.map(m => {
      const droits = m.droits.filter(d => {
        const correspond = !q
          || normaliser(d.libelle).includes(q)
          || normaliser(m.titre).includes(q)
          || normaliser(m.description).includes(q);
        const modifie = droitModifie(m.id, d.id);
        return correspond && (!uniquementModifies || modifie);
      });
      return { module: m, droits };
    }).filter(g => g.droits.length > 0);
  }

  function niveauDominant(module) {
    const actifs = module.droits.filter(d => d.actif !== false && d.niveau !== "aucun");
    if (!actifs.length) return niveau("aucun");
    const moyen = actifs.reduce((s, d) => s + niveau(d.niveau).ordre, 0) / actifs.length;
    return NIVEAUX.reduce((a, b) => Math.abs(b.ordre - moyen) < Math.abs(a.ordre - moyen) ? b : a);
  }

  function rendreMatrice() {
    const conteneur = document.getElementById("contenu-matrice");
    conteneur.innerHTML = "";

    const groupes = matriceFiltree();
    if (!groupes.length) {
      const vide = element("div", "message-vide", "Aucun droit ne correspond à votre recherche.");
      conteneur.appendChild(vide);
      mettreAJourCompteurs();
      return;
    }

    groupes.forEach(({ module, droits }) => {
      const ouvert = groupeOuvert.has(module.id) || !!filtreTexte || uniquementModifies;
      const groupe = element("div", "groupe" + (ouvert ? " ouvert" : ""));

      /* En-tête du module */
      const entete = element("div", "entete-groupe");
      entete.setAttribute("role", "button");
      entete.setAttribute("tabindex", "0");
      entete.setAttribute("aria-expanded", ouvert ? "true" : "false");
      entete.setAttribute("aria-label", "Développer ou réduire le module " + module.titre);
      entete.innerHTML =
        '<span class="chevron" aria-hidden="true">▶</span>' +
        '<span class="icone-module" aria-hidden="true">' + module.icone + '</span>';
      const bloc = element("div");
      bloc.appendChild(element("div", "nom", module.titre));
      bloc.appendChild(element("div", "description", module.description));
      entete.appendChild(bloc);

      const dom = niveauDominant(module);
      const pastille = element("span", "pastille-niveau " + dom.couleur, dom.libelle);
      entete.appendChild(pastille);

      const interrupteur = element("button", "interrupteur");
      interrupteur.type = "button";
      interrupteur.setAttribute("role", "switch");
      const moduleActif = droits.some(d => d.actif !== false && d.niveau !== "aucun");
      interrupteur.setAttribute("aria-checked", moduleActif ? "true" : "false");
      interrupteur.setAttribute("aria-label", "Activer ou désactiver le module " + module.titre);
      interrupteur.title = moduleActif ? "Désactiver tout le module" : "Activer tout le module";
      interrupteur.addEventListener("click", (e) => { e.stopPropagation(); basculerModule(module.id, !moduleActif); });
      entete.appendChild(interrupteur);

      entete.addEventListener("click", () => {
        if (groupeOuvert.has(module.id)) groupeOuvert.delete(module.id);
        else groupeOuvert.add(module.id);
        rendreMatrice();
      });
      entete.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); entete.click(); }
      });
      groupe.appendChild(entete);

      if (!ouvert) { conteneur.appendChild(groupe); return; }

      /* Tableau des droits */
      const tableau = element("table", "tableau-droits");
      tableau.innerHTML =
        "<thead><tr>" +
        "<th scope='col' style='width:34%'>Droit / Fonctionnalité</th>" +
        "<th scope='col' style='width:16%'>Niveau d'accès</th>" +
        "<th scope='col' style='width:18%'>Portée</th>" +
        "<th scope='col'>Actions autorisées</th>" +
        "<th scope='col' style='width:15%'>État</th>" +
        "</tr></thead>";
      const corps = element("tbody");

      droits.forEach(d => {
        const ligne = element("tr");
        if (droitModifie(module.id, d.id)) ligne.classList.add("modifie");

        /* Colonne 1 : libellé */
        const tdLibelle = element("td");
        const blocLibelle = element("div", "libelle-droit");
        blocLibelle.appendChild(element("span", "", d.libelle));
        if (d.sensible) blocLibelle.appendChild(element("span", "sensible", "Sensible"));
        tdLibelle.appendChild(blocLibelle);
        ligne.appendChild(tdLibelle);

        /* Colonne 2 : niveau d'accès */
        const tdNiveau = element("td");
        const selectNiveau = element("select", "select-niveau");
        selectNiveau.setAttribute("aria-label", "Niveau d'accès du droit « " + d.libelle + " »");
        NIVEAUX.forEach(n => selectNiveau.appendChild(new Option(n.libelle, n.id)));
        selectNiveau.value = d.niveau;
        selectNiveau.disabled = d.actif === false;
        selectNiveau.addEventListener("change", () => {
          d.niveau = selectNiveau.value;
          d.actions = new Set(ACTIONS_PAR_NIVEAU[d.niveau]);
          if (d.niveau !== "aucun") d.actif = true;
          rendreTout();
        });
        tdNiveau.appendChild(selectNiveau);
        ligne.appendChild(tdNiveau);

        /* Colonne 3 : portée */
        const tdPortee = element("td");
        const selectPortee = element("select", "select-portee");
        selectPortee.setAttribute("aria-label", "Portée du droit « " + d.libelle + " »");
        PORTEES.forEach(p => selectPortee.appendChild(new Option(p.libelle, p.id)));
        selectPortee.value = d.portee;
        selectPortee.disabled = d.actif === false;
        selectPortee.addEventListener("change", () => { d.portee = selectPortee.value; rendreTout(); });
        tdPortee.appendChild(selectPortee);
        ligne.appendChild(tdPortee);

        /* Colonne 4 : actions autorisées */
        const tdActions = element("td");
        const puces = element("div", "puces-actions");
        if (d.actif === false || d.niveau === "aucun") {
          puces.appendChild(element("span", "", "—"));
          puces.style.color = "var(--texte-faible)";
        } else {
          ACTIONS_DROIT.forEach(a => {
            const puce = element("button", "puce-action" + (d.actions.has(a.id) ? " active" : ""));
            puce.type = "button";
            puce.setAttribute("aria-pressed", d.actions.has(a.id) ? "true" : "false");
            puce.setAttribute("aria-label", "Action « " + a.libelle + " » sur « " + d.libelle + " »");
            puce.title = a.libelle;
            puce.innerHTML = '<span aria-hidden="true">' + a.icone + '</span>' + a.libelle;
            puce.addEventListener("click", () => {
              if (d.actions.has(a.id)) d.actions.delete(a.id); else d.actions.add(a.id);
              rendreTout();
            });
            puces.appendChild(puce);
          });
        }
        tdActions.appendChild(puces);
        ligne.appendChild(tdActions);

        /* Colonne 5 : état */
        const tdEtat = element("td");
        const cellule = element("div", "cellule-etat");
        const e = etatDroit(d);
        const sw = element("button", "interrupteur");
        sw.type = "button";
        sw.setAttribute("role", "switch");
        sw.setAttribute("aria-checked", d.actif === false ? "false" : "true");
        sw.setAttribute("aria-label", "Activer ou désactiver « " + d.libelle + " »");
        sw.addEventListener("click", () => { basculerDroit(module.id, d.id); });
        cellule.appendChild(sw);
        cellule.appendChild(element("span", "etat " + e.classe, e.libelle));
        if (droitModifie(module.id, d.id)) cellule.appendChild(element("span", "etiquette-modifie", "Modifié"));
        tdEtat.appendChild(cellule);
        ligne.appendChild(tdEtat);

        corps.appendChild(ligne);
      });

      tableau.appendChild(corps);
      groupe.appendChild(tableau);
      conteneur.appendChild(groupe);
    });

    mettreAJourCompteurs();
  }

  function basculerDroit(moduleId, droitId) {
    const d = etatCourant.find(m => m.id === moduleId).droits.find(x => x.id === droitId);
    d.actif = !(d.actif !== false);
    rendreTout();
  }

  function basculerModule(moduleId, actif) {
    const m = etatCourant.find(x => x.id === moduleId);
    m.droits.forEach(d => {
      d.actif = actif;
      if (!actif) d.actions = new Set();
      else d.actions = new Set(ACTIONS_PAR_NIVEAU[d.niveau]);
    });
    rendreTout();
    notifier(actif ? "Module « " + m.titre + " » activé." : "Module « " + m.titre + " » désactivé.", actif ? "succes" : "avertissement");
  }

  /* ============================================================
     Rendu — Récapitulatif, séparation des tâches, droits sensibles
     ============================================================ */
  function rendreResume() {
    let accordes = 0, partiels = 0, refuses = 0, total = 0;
    const sensibles = [];

    etatCourant.forEach(m => m.droits.forEach(d => {
      total++;
      const e = etatDroit(d);
      if (e.cle === "autorise") accordes++;
      else if (e.cle === "partiel") partiels++;
      else refuses++;
      if (d.sensible && d.actif !== false && d.niveau !== "aucun") sensibles.push(m.titre + " › " + d.libelle);
    }));

    document.getElementById("resume-accordes").textContent = accordes;
    document.getElementById("resume-partiels").textContent = partiels;
    document.getElementById("resume-refuses").textContent = refuses;
    document.getElementById("resume-modifies").textContent = nombreModifications();

    const pct = v => total ? (v / total * 100).toFixed(1) + "%" : "0%";
    document.getElementById("barre-autorises").style.width = pct(accordes);
    document.getElementById("barre-partiels").style.width = pct(partiels);
    document.getElementById("barre-refuses").style.width = pct(refuses);

    const global = niveauDominant({ droits: etatCourant.flatMap(m => m.droits) });
    const pastille = document.getElementById("resume-niveau-global");
    pastille.textContent = global.libelle;
    pastille.className = "pastille-niveau " + global.couleur;

    /* Séparation des tâches */
    const zoneSeparation = document.getElementById("contenu-separation");
    zoneSeparation.innerHTML = "";
    const conflits = [];
    REGLES_SEPARATION.forEach(r => {
      const d1 = trouverDroitParLibelle(r.droit1);
      const d2 = trouverDroitParLibelle(r.droit2);
      if (d1 && d2 && d1.niveau !== "aucun" && d2.niveau !== "aucun" && d1.actif !== false && d2.actif !== false) {
        const cumulEcriture = ["modification", "suppression", "complet"];
        if (cumulEcriture.includes(d1.niveau) && cumulEcriture.includes(d2.niveau)) conflits.push(r);
      }
    });
    if (!conflits.length) {
      zoneSeparation.appendChild(element("div", "alerte succes", "✓ Aucun conflit détecté sur ce profil."));
    } else {
      conflits.forEach(c => {
        zoneSeparation.appendChild(element("div", "alerte danger",
          "⚠ Conflit : « " + c.droit1 + " » et « " + c.droit2 + " » cumulés sur le module « " + c.module + " »."));
      });
    }

    /* Droits sensibles */
    const liste = document.getElementById("liste-sensibles");
    liste.innerHTML = "";
    if (!sensibles.length) {
      liste.appendChild(element("div", "", "Aucun droit sensible accordé."));
    } else {
      const ul = element("ul");
      ul.style.cssText = "margin:0;padding-left:18px;";
      sensibles.forEach(s => ul.appendChild(element("li", "", s)));
      liste.appendChild(ul);
    }

    document.getElementById("compteur-matrice").textContent = total + " droits";
    document.getElementById("compteur-circuits").textContent = CIRCUITS.length;
    document.getElementById("compteur-profils").textContent = PROFILS.length;
  }

  function trouverDroitParLibelle(libelle) {
    for (const m of etatCourant) {
      const d = m.droits.find(x => normaliser(x.libelle) === normaliser(libelle));
      if (d) return d;
    }
    return null;
  }

  /* ============================================================
     Rendu — Circuits de validation
     ============================================================ */
  function rendreCircuits() {
    const conteneur = document.getElementById("contenu-circuits");
    conteneur.innerHTML = "";

    const tableau = element("table", "tableau-simple");
    tableau.innerHTML =
      "<thead><tr>" +
      "<th scope='col' style='width:22%'>Opération</th>" +
      "<th scope='col' style='width:16%'>Seuil (FCFA)</th>" +
      "<th scope='col' style='width:17%'>Validateur</th>" +
      "<th scope='col' style='width:17%'>Second validateur</th>" +
      "<th scope='col' style='width:13%'>Délai</th>" +
      "<th scope='col' style='width:15%'>Au-delà du seuil</th>" +
      "</tr></thead>";
    const corps = element("tbody");

    CIRCUITS.forEach(c => {
      const ligne = element("tr");
      ligne.appendChild(celluleOperation(c.operation));
      ligne.appendChild(celluleSeuil(c));
      ligne.appendChild(celluleSelect(c, "validateur", VALIDATEURS));
      ligne.appendChild(celluleSelect(c, "secondValidateur", VALIDATEURS, true));
      ligne.appendChild(celluleSelect(c, "delai", DELAIS));
      ligne.appendChild(celluleSelect(c, "auDela", ESCALADES));
      corps.appendChild(ligne);
    });

    tableau.appendChild(corps);
    conteneur.appendChild(tableau);
  }

  const VALIDATEURS = [
    { id: "", libelle: "—" },
    { id: "directeurGeneral", libelle: "Directeur Général" },
    { id: "secretaireGeneral", libelle: "Secrétaire Général" },
    { id: "directeurAdministratifFinancier", libelle: "Directeur Administratif et Financier" },
    { id: "directeurRessourcesHumaines", libelle: "Directeur des Ressources Humaines" },
    { id: "chefServiceComptabilite", libelle: "Chef de service Comptabilité" },
    { id: "responsableAchats", libelle: "Responsable Achats" },
    { id: "juriste", libelle: "Juriste d'entreprise" },
    { id: "controleurGestion", libelle: "Contrôleur de gestion" }
  ];
  const DELAIS = [
    { id: "unJour", libelle: "1 jour ouvré" },
    { id: "deuxJours", libelle: "2 jours ouvrés" },
    { id: "troisJours", libelle: "3 jours ouvrés" },
    { id: "cinqJours", libelle: "5 jours ouvrés" }
  ];
  const ESCALADES = [
    { id: "directionGenerale", libelle: "Escalade vers la Direction Générale" },
    { id: "comiteDirection", libelle: "Comité de direction" },
    { id: "blocage", libelle: "Blocage de l'opération" },
    { id: "autorisationAutomatique", libelle: "Autorisation automatique" }
  ];

  function celluleOperation(libelle) {
    const td = element("td");
    td.appendChild(element("span", "operation", libelle));
    return td;
  }

  function celluleSeuil(c) {
    const td = element("td");
    const champ = element("input");
    champ.type = "number";
    champ.min = "0";
    champ.step = "100000";
    champ.value = c.seuil;
    champ.setAttribute("aria-label", "Seuil en francs CFA pour « " + c.operation + " »");
    champ.addEventListener("change", () => {
      c.seuil = Number(champ.value) || 0;
      td.title = formaterMontant(c.seuil);
    });
    td.title = formaterMontant(c.seuil);
    td.appendChild(champ);
    return td;
  }

  function celluleSelect(c, propriete, options, optionVide) {
    const td = element("td");
    const select = element("select");
    select.setAttribute("aria-label", libelleColonne(propriete) + " pour « " + c.operation + " »");
    options.forEach(o => select.appendChild(new Option(o.libelle, o.id)));
    select.value = c[propriete] || "";
    select.addEventListener("change", () => { c[propriete] = select.value; });
    td.appendChild(select);
    return td;
  }

  function libelleColonne(p) {
    return {
      validateur: "Validateur",
      secondValidateur: "Second validateur",
      delai: "Délai de validation",
      auDela: "Règle au-delà du seuil"
    }[p] || p;
  }

  /* ============================================================
     Rendu — Profils & modèles
     ============================================================ */
  function rendreProfils() {
    const conteneur = document.getElementById("contenu-profils");
    conteneur.innerHTML = "";
    PROFILS.forEach(p => {
      const carte = element("div", "carte-profil");
      carte.appendChild(element("h4", "", p.nom));
      carte.appendChild(element("p", "", p.resume));
      carte.appendChild(element("span", "meta", p.utilisateurs + " utilisateurs affectés"));
      const actions = element("div", "actions-profil");
      const appliquer = element("button", "bouton primaire", "Appliquer ce modèle");
      appliquer.type = "button";
      appliquer.addEventListener("click", () => appliquerModele(p));
      const apercu = element("button", "bouton", "Voir le détail");
      apercu.type = "button";
      apercu.addEventListener("click", () => notifier("Détail du modèle « " + p.nom + " » : " + p.resume));
      actions.appendChild(appliquer);
      actions.appendChild(apercu);
      carte.appendChild(actions);
      conteneur.appendChild(carte);
    });
  }

  function appliquerModele(profil) {
    const niveauCible = {
      "direction-generale": "complet",
      "secretaire-general": "modification",
      "daf": "modification",
      "assistant-direction": "lecture",
      "responsable-rh": "modification",
      "controleur-gestion": "lecture",
      "audit": "lecture"
    }[profil.id] || "lecture";

    etatCourant.forEach(m => m.droits.forEach(d => {
      d.niveau = d.sensible && niveauCible === "complet" ? "modification" : niveauCible;
      d.actions = new Set(ACTIONS_PAR_NIVEAU[d.niveau]);
      d.actif = true;
      if (profil.id === "audit") { d.actions.add("exporter"); d.actions.delete("modifier"); d.actions.delete("creer"); }
    }));
    document.getElementById("select-profil").value = profil.id;
    rendreTout();
    notifier("Le modèle « " + profil.nom + " » a été appliqué.", "succes");
  }

  /* ============================================================
     Rendu — Historique
     ============================================================ */
  function rendreHistorique() {
    const conteneur = document.getElementById("contenu-historique");
    conteneur.innerHTML = "";
    const tableau = element("table", "tableau-simple");
    tableau.innerHTML =
      "<thead><tr>" +
      "<th scope='col'>Date</th><th scope='col'>Utilisateur</th><th scope='col'>Module</th>" +
      "<th scope='col'>Droit</th><th scope='col'>Avant</th><th scope='col'>Après</th>" +
      "</tr></thead>";
    const corps = element("tbody");
    HISTORIQUE.forEach(h => {
      const ligne = element("tr");
      [h.date, h.utilisateur, h.module, h.droit].forEach(v => ligne.appendChild(element("td", "", v)));
      ligne.appendChild(element("td", "", h.avant));
      const apres = element("td");
      apres.appendChild(element("strong", "", h.apres));
      ligne.appendChild(apres);
      corps.appendChild(ligne);
    });
    tableau.appendChild(corps);
    conteneur.appendChild(tableau);
  }

  /* ============================================================
     Rendu global & compteurs
     ============================================================ */
  function rendreTout() {
    rendreMatrice();
    rendreResume();
  }

  function mettreAJourCompteurs() {
    const total = etatCourant.reduce((s, m) => s + m.droits.length, 0);
    document.getElementById("compteur-matrice").textContent = total + " droits";
  }

  /* ============================================================
     Onglets
     ============================================================ */
  function initialiserOnglets() {
    const onglets = [...document.querySelectorAll(".onglet")];
    onglets.forEach((onglet, index) => {
      onglet.addEventListener("click", () => activerOnglet(index));
      onglet.addEventListener("keydown", (e) => {
        if (e.key === "ArrowRight") { e.preventDefault(); activerOnglet((index + 1) % onglets.length, true); }
        if (e.key === "ArrowLeft") { e.preventDefault(); activerOnglet((index - 1 + onglets.length) % onglets.length, true); }
      });
    });
    function activerOnglet(i, focus) {
      onglets.forEach((o, j) => {
        o.setAttribute("aria-selected", j === i ? "true" : "false");
        o.tabIndex = j === i ? 0 : -1;
        document.getElementById(o.dataset.panneau).hidden = j !== i;
      });
      if (focus) onglets[i].focus();
    }
  }

  /* ============================================================
     Barre d'outils & pied de fenêtre
     ============================================================ */
  function initialiserEvenements() {
    document.getElementById("champ-recherche").addEventListener("input", (e) => {
      filtreTexte = e.target.value;
      rendreMatrice();
    });

    document.getElementById("select-niveau-defaut").addEventListener("change", (e) => {
      const nouveau = e.target.value;
      etatCourant.forEach(m => m.droits.forEach(d => {
        d.niveau = nouveau;
        d.actions = new Set(ACTIONS_PAR_NIVEAU[nouveau]);
        d.actif = nouveau !== "aucun";
      }));
      rendreTout();
      notifier("Le niveau « " + niveau(nouveau).libelle + " » a été appliqué à tous les droits.", "avertissement");
    });

    document.getElementById("bouton-developper").addEventListener("click", () => {
      groupeOuvert = new Set(etatCourant.map(m => m.id));
      rendreMatrice();
    });

    document.getElementById("bouton-reduire").addEventListener("click", () => {
      groupeOuvert = new Set();
      rendreMatrice();
    });

    const boutonModifies = document.getElementById("bouton-modifies");
    boutonModifies.addEventListener("click", () => {
      uniquementModifies = !uniquementModifies;
      boutonModifies.setAttribute("aria-pressed", uniquementModifies ? "true" : "false");
      rendreMatrice();
    });

    document.getElementById("bouton-exporter").addEventListener("click", exporter);
    document.getElementById("bouton-imprimer").addEventListener("click", () => window.print());

    document.getElementById("bouton-reinitialiser").addEventListener("click", () => {
      etatCourant = etatInitial.map(cloneModule);
      rendreTout();
      notifier("La configuration a été réinitialisée à son état initial.");
    });

    document.getElementById("bouton-annuler").addEventListener("click", () => {
      if (nombreModifications() > 0 &&
          !window.confirm("Des modifications ne sont pas enregistrées. Voulez-vous vraiment fermer la fenêtre ?")) return;
      notifier("Fermeture de la fenêtre sans enregistrer les modifications.");
    });

    document.getElementById("bouton-fermer").addEventListener("click", () =>
      document.getElementById("bouton-annuler").click());

    document.getElementById("bouton-enregistrer").addEventListener("click", () => enregistrer(false));
    document.getElementById("bouton-enregistrer-appliquer").addEventListener("click", () => enregistrer(true));

    document.getElementById("bouton-enregistrer-modele").addEventListener("click", () => {
      const nom = window.prompt("Nom du modèle :", "Nouveau modèle de droits");
      if (!nom) return;
      notifier("Le modèle « " + nom + " » a été enregistré.", "succes");
    });

    const sw = document.getElementById("switch-delegation");
    sw.addEventListener("click", () => {
      sw.setAttribute("aria-checked", sw.getAttribute("aria-checked") === "true" ? "false" : "true");
    });
  }

  function enregistrer(appliquer) {
    const modifs = nombreModifications();
    for (let i = 0; i < etatInitial.length; i++) etatInitial[i] = cloneModule(etatCourant[i]);
    rendreTout();
    const profil = document.getElementById("select-profil").selectedOptions[0].text;
    notifier(
      modifs === 0
        ? "Aucune modification à enregistrer."
        : (appliquer
          ? modifs + " modification(s) enregistrée(s) et appliquée(s) au profil « " + profil + " »."
          : modifs + " modification(s) enregistrée(s) pour le profil « " + profil + " »."),
      modifs === 0 ? "avertissement" : "succes"
    );
  }

  function exporter() {
    const configuration = {
      fenetre: "Configurer les Droits — Direction & Administration Générale",
      langue: "fr-FR",
      profil: document.getElementById("select-profil").selectedOptions[0].text,
      structure: document.getElementById("select-structure").selectedOptions[0].text,
      exporteLe: new Date().toLocaleString("fr-FR"),
      modules: etatCourant.map(m => ({
        module: m.titre,
        droits: m.droits.map(d => ({
          droit: d.libelle,
          niveau: niveau(d.niveau).libelle,
          porte: portee(d.portee),
          actif: d.actif !== false,
          sensible: !!d.sensible,
          actions: ACTIONS_DROIT.filter(a => d.actions.has(a.id)).map(a => a.libelle)
        }))
      })),
      circuits: CIRCUITS.map(c => ({
        operation: c.operation,
        seuil: c.seuil,
        seuilFormate: formaterMontant(c.seuil),
        validateur: (VALIDATEURS.find(v => v.id === c.validateur) || { libelle: "—" }).libelle,
        secondValidateur: (VALIDATEURS.find(v => v.id === c.secondValidateur) || { libelle: "—" }).libelle,
        delai: (DELAIS.find(v => v.id === c.delai) || { libelle: "—" }).libelle,
        auDela: (ESCALADES.find(v => v.id === c.auDela) || { libelle: "—" }).libelle
      }))
    };

    const blob = new Blob([JSON.stringify(configuration, null, 2)], { type: "application/json;charset=utf-8" });
    const lien = document.createElement("a");
    lien.href = URL.createObjectURL(blob);
    lien.download = "droits-direction-administration-generale.json";
    lien.click();
    URL.revokeObjectURL(lien.href);
    notifier("La configuration a été exportée au format JSON.", "succes");
  }

  /* ============================================================
     Chargement des chaînes françaises (facultatif : l'interface
     est déjà en français dans le code source).
     ============================================================ */
  function chargerChaines() {
    return fetch("i18n/fr-FR.json")
      .then(r => (r.ok ? r.json() : null))
      .then(j => { CHAINES = j; document.documentElement.lang = (j && j.meta && j.meta.langue) || "fr"; })
      .catch(() => { CHAINES = null; });
  }

  /* ============================================================
     Démarrage
     ============================================================ */
  function demarrer() {
    remplirSelects();
    initialiserOnglets();
    initialiserEvenements();
    rendreCircuits();
    rendreProfils();
    rendreHistorique();
    rendreTout();
    chargerChaines();
  }

  document.addEventListener("DOMContentLoaded", demarrer);
})();
