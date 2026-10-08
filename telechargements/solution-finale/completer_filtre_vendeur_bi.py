#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEXORA — complète le filtre vendeur de l'écran BI (/reports).

À utiliser quand le premier correctif a signalé :

    frontend/src/app/reports/page.tsx   corrigé par insertions ciblées

Ce message signifie que le fichier avait été modifié depuis l'extraction : le
premier script n'avait alors posé que l'état React et la clé de requête, sans
la liste déroulante ni l'envoi de « seller_id » à l'API. Ce script vérifie
chaque élément séparément et complète uniquement ceux qui manquent :

  1. état React   : const [selectedSeller, setSelectedSeller] = ...
  2. type réponse : available_sellers / selected_seller
  3. clé requête  : queryKey = ['bi-analytics', view, days, seller]
  4. appel API    : /reports/bi-analytics/ + &seller_id=<vendeur>
  5. sélecteur UI : liste déroulante « Tous les vendeurs / <vendeur> »
  6. rappel       : périmètre analysé dans l'encart explicatif
  7. export PDF   : conservation du vendeur sélectionné

Le script :
  * travaille par ancres vérifiées, une insertion à la fois ;
  * ne réinsère jamais ce qui est déjà présent (relançable) ;
  * écrit une sauvegarde horodatée avant toute modification ;
  * s'arrête sans rien écrire si un élément CRITIQUE est introuvable ;
  * conserve la mise en forme du fichier (fins de ligne CRLF).

Usage :
    py completer_filtre_vendeur_bi.py --racine D:\\NEXORA
    py completer_filtre_vendeur_bi.py --racine D:\\NEXORA --verifier
    py completer_filtre_vendeur_bi.py --racine D:\\NEXORA --dry-run
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import os
import re
import shutil
import sys

CHEMIN_PAGE = os.path.join('frontend', 'src', 'app', 'reports', 'page.tsx')
CHEMIN_BI = os.path.join('apps', 'reports', 'bi_analytics.py')
CHEMIN_TESTS = os.path.join('tests', 'test_bi_vendeur_filtre.py')

# ---------------------------------------------------------------- fragments --

ETAT_VENDEUR = (
    "  // Filtre vendeur : '' = tous les vendeurs, sinon identifiant du vendeur sélectionné\n"
    "  const [selectedSeller, setSelectedSeller] = React.useState<string>('');\n"
)

TYPE_REPONSE = (
    "    available_sellers?: Array<{ id: string; email: string }>;\n"
    "    selected_seller?: string;\n"
)

REQUETE_API = (
    "    queryFn: () =>\n"
    "      apiRequest(\n"
    "        `/reports/bi-analytics/?view=${selectedView}&days=${days}${\n"
    "          selectedSeller ? `&seller_id=${selectedSeller}` : ''\n"
    "        }`\n"
    "      ),\n"
)

SELECTEUR = (
    "            {/* Filtre vendeur : bilan de vente par vendeur */}\n"
    "            <div className=\"flex items-center gap-1.5 bg-muted/60 px-2 py-1 rounded-xl border text-xs self-start md:self-auto\">\n"
    "              <Users className=\"h-4 w-4 text-primary shrink-0\" />\n"
    "              <select\n"
    "                aria-label=\"Filtrer le bilan par vendeur\"\n"
    "                title=\"Filtrer le bilan de vente par vendeur\"\n"
    "                value={selectedSeller}\n"
    "                onChange={(e) => setSelectedSeller(e.target.value)}\n"
    "                className=\"bg-transparent py-1.5 pr-1 font-bold text-xs rounded-lg outline-none cursor-pointer max-w-[220px]\"\n"
    "              >\n"
    "                <option value=\"\">Tous les vendeurs</option>\n"
    "                {(biData?.available_sellers ?? []).map((s) => (\n"
    "                  <option key={s.id} value={s.id}>\n"
    "                    {s.email || `Vendeur #${s.id}`}\n"
    "                  </option>\n"
    "                ))}\n"
    "              </select>\n"
    "              {selectedSeller ? (\n"
    "                <button\n"
    "                  type=\"button\"\n"
    "                  onClick={() => setSelectedSeller('')}\n"
    "                  title=\"Réinitialiser le filtre vendeur\"\n"
    "                  className=\"px-1 font-bold text-muted-foreground hover:text-foreground\"\n"
    "                >\n"
    "                  ✕\n"
    "                </button>\n"
    "              ) : null}\n"
    "            </div>\n\n"
)

LIBELLE = (
    "  const selectedSellerLabel =\n"
    "    (biData?.available_sellers ?? []).find((s) => s.id === selectedSeller)?.email ||\n"
    "    (selectedSeller ? `#${selectedSeller}` : '');\n\n"
)

RAPPEL = "              {selectedSeller ? ` — Vendeur : ${selectedSellerLabel}` : ' — Tous les vendeurs'}\n"

EXPORT_OBJET = (
    "      if (selectedSeller) {\n"
    "        queryParams.set('seller_id', selectedSeller);\n"
    "      }\n"
)

EXPORT_LIEN = (
    "                href={`/api/v1/reports/export-bi-pdf/?days=${pdfPeriodDays}&view=${selectedView}${\n"
    "                  selectedSeller ? `&seller_id=${selectedSeller}` : ''\n"
    "                }`}\n"
)

# ------------------------------------------------------------------ moteur --

ANCRE_ETAT = "  const [days, setDays] = React.useState<number>(30);\n"
ANCRE_TYPE = "    stores_performance: Array<{ store: string; revenue: string }>;\n"
ANCRE_TYPE_REPLI = "    sellers_performance: Array<{ seller: string; revenue: string; transactions: number }>;\n"
ANCRE_QUERYKEY = "    queryKey: ['bi-analytics', selectedView, days],\n"
ANCRE_SELECTEUR_1 = "            {/* Timeframe switch */}\n"
ANCRE_SELECTEUR_2 = "            {/* Export PDF Button */}\n"
ANCRE_LIBELLE = "  const categoryBarData = biData?.categories?.map((c) => ({\n"
ANCRE_RAPPEL = "              Compréhension automatique des variations observées sur les {days} derniers jours\n"
ANCRE_EXPORT_OBJET = "      });\n"
ANCRE_EXPORT_LIEN_1 = "                href={`/api/v1/reports/export-bi-pdf/?days=${pdfPeriodDays}&view=${selectedView}`}\n"
ANCRE_EXPORT_LIEN_2 = "                href={`/api/v1/reports/export-bi-pdf/?days=${pdfPeriodDays}&view=${selectedView}`}"

MOTIF_REQUETE = re.compile(
    r"(?m)^([ \t]*)queryFn:[ \t]*\(\)[ \t]*=>[ \t]*apiRequest\([ \t]*`[^`\n]*bi-analytics[^`\n]*`[ \t]*\),[ \t]*$"
)


def lire(chemin: str):
    """Lit le fichier et retourne (texte normalisé en \\n, le fichier était-il en CRLF ?)."""
    with open(chemin, 'r', encoding='utf-8-sig', newline='') as f:
        brut = f.read()
    crlf = '\r\n' in brut
    return brut.replace('\r\n', '\n').replace('\r', '\n'), crlf


def ecrire(chemin: str, texte: str, crlf: bool) -> None:
    sortie = texte.replace('\n', '\r\n') if crlf else texte
    with open(chemin, 'w', encoding='utf-8', newline='') as f:
        f.write(sortie)


def inserer_avant(texte: str, ancre: str, bloc: str) -> bool:
    if ancre not in texte:
        return False
    texte = texte.replace(ancre, bloc + ancre, 1)
    return texte


def insere(texte: str, ancre: str, bloc: str):
    """Insère `bloc` avant `ancre` ; retourne (texte, ok)."""
    if ancre not in texte:
        return texte, False
    return texte.replace(ancre, bloc + ancre, 1), True


def reindenter(bloc: str, indent: str) -> str:
    """Réécrit un bloc écrit avec 4 espaces d'indentation de base vers `indent`."""
    lignes = bloc.split('\n')
    sortie = []
    for ligne in lignes:
        if not ligne.strip():
            sortie.append('')
        elif ligne.startswith('    '):
            sortie.append(indent + ligne[4:])
        else:
            sortie.append(indent + ligne)
    return '\n'.join(sortie)


def journal_lignes(texte: str, motif: str, maximum: int = 6):
    sortie = []
    for numero, ligne in enumerate(texte.splitlines(), 1):
        if motif in ligne:
            sortie.append('%5d | %s' % (numero, ligne.rstrip()[:160]))
        if len(sortie) >= maximum:
            break
    return sortie


def completer_page(texte: str, journal: list) -> str:
    """Applique les 7 compléments manquants. `journal` reçoit l'état de chacun."""

    def noter(nom, statut, critique):
        journal.append((nom, statut, critique))

    # 1) état React -----------------------------------------------------------
    if 'const [selectedSeller, setSelectedSeller]' in texte:
        noter('état React du vendeur', 'déjà présent', True)
    elif ANCRE_ETAT in texte:
        texte = texte.replace(ANCRE_ETAT, ANCRE_ETAT + ETAT_VENDEUR, 1)
        noter('état React du vendeur', 'ajouté', True)
    else:
        noter('état React du vendeur', 'ancre absente', True)

    # 2) type de la réponse ---------------------------------------------------
    if 'available_sellers?:' in texte:
        noter('type available_sellers/selected_seller', 'déjà présent', True)
    elif ANCRE_TYPE in texte:
        texte = texte.replace(ANCRE_TYPE, ANCRE_TYPE + TYPE_REPONSE, 1)
        noter('type available_sellers/selected_seller', 'ajouté', True)
    elif ANCRE_TYPE_REPLI in texte:
        texte = texte.replace(ANCRE_TYPE_REPLI, ANCRE_TYPE_REPLI + TYPE_REPONSE, 1)
        noter('type available_sellers/selected_seller', 'ajouté', True)
    else:
        noter('type available_sellers/selected_seller', 'ancre absente', True)

    # 3) clé de requête -------------------------------------------------------
    if "queryKey: ['bi-analytics', selectedView, days, selectedSeller]," in texte:
        noter('clé de requête React Query', 'déjà présent', True)
    elif ANCRE_QUERYKEY in texte:
        texte = texte.replace(
            ANCRE_QUERYKEY,
            "    queryKey: ['bi-analytics', selectedView, days, selectedSeller],\n",
            1,
        )
        noter('clé de requête React Query', 'ajouté', True)
    else:
        noter('clé de requête React Query', 'ancre absente', True)

    # 4) appel API avec seller_id --------------------------------------------
    if 'seller_id=${selectedSeller}' in texte:
        noter("envoi de seller_id à l'API", 'déjà présent', True)
    else:
        correspondance = MOTIF_REQUETE.search(texte)
        if correspondance:
            indent = correspondance.group(1)
            bloc = reindenter(REQUETE_API, indent).rstrip('\n')
            texte = texte[:correspondance.start()] + bloc + texte[correspondance.end():]
            noter("envoi de seller_id à l'API", 'ajouté', True)
        else:
            noter("envoi de seller_id à l'API", 'ligne apiRequest introuvable', True)

    # 5) sélecteur visible ----------------------------------------------------
    if 'Filtrer le bilan par vendeur' in texte:
        noter('sélecteur de vendeur', 'déjà présent', True)
    else:
        texte, ok = insere(texte, ANCRE_SELECTEUR_1, SELECTEUR)
        if not ok:
            texte, ok = insere(texte, ANCRE_SELECTEUR_2, SELECTEUR)
        noter('sélecteur de vendeur', 'ajouté' if ok else 'ancre absente', True)

    # 6) libellé + rappel (facultatifs) --------------------------------------
    libelle_ok = 'selectedSellerLabel' in texte
    if not libelle_ok:
        texte, libelle_ok = insere(texte, ANCRE_LIBELLE, LIBELLE)
    if 'selectedSellerLabel' in texte:
        if RAPPEL.strip() in texte:
            noter('rappel du périmètre', 'déjà présent', False)
        elif ANCRE_RAPPEL in texte:
            texte = texte.replace(ANCRE_RAPPEL, ANCRE_RAPPEL + RAPPEL, 1)
            noter('rappel du périmètre', 'ajouté', False)
        else:
            noter('rappel du périmètre', 'ancre absente (facultatif)', False)
    else:
        noter('rappel du périmètre', 'ignoré (libellé non insérable)', False)

    # 7) export PDF (facultatif) ---------------------------------------------
    if "queryParams.set('seller_id'" in texte:
        noter('export PDF (boutons)', 'déjà présent', False)
    else:
        applique = False
        if ANCRE_EXPORT_OBJET in texte and 'new URLSearchParams(' in texte:
            position = texte.index('new URLSearchParams(')
            fin = texte.index(ANCRE_EXPORT_OBJET, position)
            texte = texte[:fin + len(ANCRE_EXPORT_OBJET)] + EXPORT_OBJET + texte[fin + len(ANCRE_EXPORT_OBJET):]
            applique = True
        if 'export-bi-pdf' in texte and 'export-bi-pdf/?days=${pdfPeriodDays}&view=${selectedView}$' not in texte:
            if ANCRE_EXPORT_LIEN_1 in texte:
                texte = texte.replace(ANCRE_EXPORT_LIEN_1, EXPORT_LIEN, 1)
                applique = True
            elif ANCRE_EXPORT_LIEN_2 in texte:
                texte = texte.replace(ANCRE_EXPORT_LIEN_2, EXPORT_LIEN, 1)
                applique = True
        noter('export PDF (boutons)', 'ajouté' if applique else 'ancre absente (facultatif)', False)

    return texte


def diagnostiquer(texte: str) -> str:
    lignes = []
    for motif in ('bi-analytics', 'queryFn', 'Timeframe', 'sellers_performance', 'export-bi-pdf'):
        trouvees = journal_lignes(texte, motif)
        if trouvees:
            lignes.append('  lignes contenant « %s » :' % motif)
            lignes.extend('  ' + l for l in trouvees)
    return '\n'.join(lignes) if lignes else "  (aucune ligne de repère trouvée)"


def main(argv=None) -> int:
    parseur = argparse.ArgumentParser(description="Complète le filtre vendeur de l'écran BI NEXORA.")
    parseur.add_argument('--racine', default=None, help="Racine du projet (défaut : D:\\NEXORA si présent)")
    parseur.add_argument('--fichier', default=None, help="Chemin explicite du page.tsx à compléter")
    parseur.add_argument('--dry-run', action='store_true', help="Simule sans écrire")
    parseur.add_argument('--verifier', action='store_true', help="État seulement, sans modification")
    parseur.add_argument('--sans-tests', action='store_true', help="Ne pas rafraîchir le test Django")
    options = parseur.parse_args(argv)

    if options.fichier:
        chemin = os.path.abspath(options.fichier)
        racine = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(chemin)))))
    else:
        racine = os.path.abspath(options.racine) if options.racine else ('D:\\NEXORA' if os.path.isdir('D:\\NEXORA') else os.getcwd())
        chemin = os.path.join(racine, CHEMIN_PAGE)

    print("=" * 76)
    print("NEXORA — complément du filtre vendeur de l'écran BI (/reports)")
    print("=" * 76)
    print("Fichier : %s" % chemin)
    if not os.path.exists(chemin):
        print("ERREUR : fichier introuvable. Vérifiez --racine.")
        return 2

    texte, crlf = lire(chemin)
    empreinte = hashlib.sha256(open(chemin, 'rb').read()).hexdigest()[:12]
    journal = []
    nouveau = completer_page(texte, journal)

    if options.verifier:
        print("(empreinte actuelle : %s)" % empreinte)
        for nom, statut, critique in journal:
            print("  %-38s %s" % (nom, statut))
        manquants = [n for n, s, c in journal if c and s not in ('déjà présent', 'ajouté')]
        print("-" * 76)
        if manquants:
            print("À COMPLÉTER : %s" % ', '.join(manquants))
            print(diagnostiquer(texte))
            return 1
        print("Le filtre vendeur est complet dans ce fichier.")
        return 0

    critiques_ko = [n for n, s, c in journal if c and s not in ('déjà présent', 'ajouté')]
    if critiques_ko:
        print("ARRÊT SANS MODIFICATION — élément(s) critique(s) non insérable(s) :")
        for nom in critiques_ko:
            print("  - %s" % nom)
        print("-" * 76)
        print("Repères pour un correctif sur mesure :")
        print(diagnostiquer(texte))
        return 1

    if nouveau == texte:
        print("Aucune modification nécessaire : le filtre vendeur est déjà complet.")
        return 0

    print("Modifications à appliquer :")
    for nom, statut, _ in journal:
        if statut == 'ajouté':
            print("  + %-38s ajouté" % nom)
        elif statut.startswith('ancre absente'):
            print("  ~ %-38s ignoré (%s)" % (nom, statut))

    # Contrôles de sécurité avant écriture
    for marqueur in ('selectedSeller', 'seller_id', 'available_sellers'):
        if marqueur not in nouveau:
            print("ARRÊT : le résultat ne contient pas « %s »." % marqueur)
            return 1

    if options.dry_run:
        print("-" * 76)
        print("Mode simulation : aucun fichier modifié.")
        return 0

    horodatage = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    dossier = os.path.join(racine, 'sauvegardes-filtre-vendeur-%s' % horodatage)
    cible = os.path.join(dossier, CHEMIN_PAGE)
    os.makedirs(os.path.dirname(cible), exist_ok=True)
    shutil.copy2(chemin, cible)
    print("-" * 76)
    print("Sauvegarde : %s" % cible)

    ecrire(chemin, nouveau, crlf)
    print("Fichier complété : %s" % chemin)
    print("  fins de ligne : %s" % ('CRLF (inchangées)' if crlf else 'LF (inchangées)'))

    # Rafraîchit le test Django livré, s'il est déjà en place
    if not options.sans_tests:
        source_test = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_bi_vendeur_filtre.py')
        test_local = os.path.join(racine, CHEMIN_TESTS)
        if os.path.exists(source_test) and os.path.isdir(os.path.dirname(test_local)):
            if not os.path.exists(test_local) or open(source_test, 'rb').read() != open(test_local, 'rb').read():
                shutil.copyfile(source_test, test_local)
                print("Test mis à jour : %s" % CHEMIN_TESTS)

    print("-" * 76)
    print("Terminé. Relancez le frontend (npm run dev) puis rechargez /reports :")
    print("la liste déroulante doit proposer « Tous les vendeurs » et chaque vendeur.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
