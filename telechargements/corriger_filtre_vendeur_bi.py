#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Correctif NEXORA : filtre « bilan de vente par vendeur » sur l'écran BI réel.

Ce script corrige EXACTEMENT les deux fichiers qui alimentent l'écran
« Business Intelligence & Décision » (frontend/src/app/reports/page.tsx) et
son API (/api/v1/reports/bi-analytics/) :

  1. apps/reports/bi_analytics.py
     - lit le paramètre HTTP `seller_id` ;
     - restreint les ventes de la période courante ET de la période précédente
       au vendeur choisi (les KPI, produits, catégories, vendeurs et magasins
       en découlent automatiquement) ;
     - renvoie `available_sellers` (liste des vendeurs de l'entreprise) et
       `selected_seller` pour alimenter le sélecteur de l'interface.

  2. frontend/src/app/reports/page.tsx
     - ajoute le sélecteur « Tous les vendeurs / <vendeur> » ;
     - transmet `seller_id` à l'API, au changement de vendeur comme à l'export PDF.

Le script :
  * travaille par repérage AST (pas de « chercher/remplacer » hasardeux) ;
  * vérifie chaque point d'insertion avant d'écrire quoi que ce soit ;
  * crée une sauvegarde horodatée des deux fichiers ;
  * est idempotent (relançable sans effet si le correctif est déjà présent) ;
  * ne touche à aucun autre fichier du projet.

Usage (PowerShell, depuis D:\\NEXORA) :

    python corriger_filtre_vendeur_bi.py --racine D:\\NEXORA
    python corriger_filtre_vendeur_bi.py --racine D:\\NEXORA --verifier
    python corriger_filtre_vendeur_bi.py --racine D:\\NEXORA --dry-run
"""

from __future__ import annotations

import argparse
import ast
import datetime
import hashlib
import os
import shutil
import sys

# --------------------------------------------------------------------------
# Constantes
# --------------------------------------------------------------------------

SHA_PAGE_ORIGINAL = 'fab7f3c7f440f74c31e780041fd78d60ab8dbc71179b16b24c0234c7f97dc636'
CHEMIN_PAGE = os.path.join('frontend', 'src', 'app', 'reports', 'page.tsx')
CHEMIN_BI = os.path.join('apps', 'reports', 'bi_analytics.py')
CHEMIN_TESTS = os.path.join('tests', 'test_bi_vendeur_filtre.py')
NOM_CLASSE = 'BusinessIntelligenceAnalyticsView'

MARQUEUR_DERNIER = 'MARQUEUR-FILTRE-VENDEUR'

# --- extraits insérés dans apps/reports/bi_analytics.py ---------------------

LIGNES_PARAMETRES = [
    'seller_id = (request.query_params.get("seller_id") or "").strip()',
    'if seller_id and not seller_id.isdigit():',
    '    return Response({"detail": "Paramètre seller_id invalide."}, status=400)',
]

def lignes_filtre(variable: str) -> list:
    return [
        'if seller_id:',
        '    %s = %s.filter(seller_id=int(seller_id))' % (variable, variable),
    ]

LIGNES_REPONSE = [
    'response_payload["selected_seller"] = seller_id',
    'response_payload["available_sellers"] = [',
    '    {"id": str(row["seller_id"]), "email": row["seller__email"] or ""}',
    '    for row in Sale.objects.filter(company=company)',
    '    .exclude(seller__isnull=True)',
    '    .values("seller_id", "seller__email")',
    '    .distinct()',
    '    .order_by("seller__email")',
    ']',
]

# --------------------------------------------------------------------------
# Utilitaires
# --------------------------------------------------------------------------


class ErreurCorrectif(Exception):
    pass


def sha256(chemin: str) -> str:
    with open(chemin, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def lire_texte(chemin: str) -> str:
    with open(chemin, 'r', encoding='utf-8-sig', newline='') as f:
        return f.read()


def ecrire_texte(chemin: str, contenu: str) -> None:
    with open(chemin, 'w', encoding='utf-8', newline='') as f:
        f.write(contenu)


def sauvegarder(racine: str, chemins: list, dossier: str) -> list:
    copies = []
    for rel in chemins:
        source = os.path.join(racine, rel)
        if not os.path.exists(source):
            continue
        cible = os.path.join(dossier, rel)
        os.makedirs(os.path.dirname(cible), exist_ok=True)
        shutil.copy2(source, cible)
        copies.append(cible)
    return copies


def parcourir_sans_descendre(node: ast.AST):
    """Parcourt un nœud sans entrer dans les fonctions/lambdas imbriquées."""
    pile = [node]
    while pile:
        courant = pile.pop()
        yield courant
        for enfant in ast.iter_child_nodes(courant):
            if isinstance(enfant, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                continue
            pile.append(enfant)


def cible_assignation(node: ast.AST, nom: str) -> bool:
    if not isinstance(node, ast.Assign):
        return False
    return any(isinstance(t, ast.Name) and t.id == nom for t in node.targets)


def appel_sale_filter(node: ast.AST) -> bool:
    """Vrai si le nœud contient un appel Sale.objects.filter(...) / <qs>.filter(...)."""
    for n in parcourir_sans_descendre(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'filter':
            valeur = n.func.value
            if isinstance(valeur, ast.Attribute) and valeur.attr == 'objects':
                if isinstance(valeur.value, ast.Name) and valeur.value.id == 'Sale':
                    return True
    return False


def indentation_de(source: str, ligne: int) -> str:
    """Retourne l'indentation (espaces) de la ligne 1-based donnée du source."""
    lignes = source.splitlines()
    if 1 <= ligne <= len(lignes):
        brut = lignes[ligne - 1]
        return brut[:len(brut) - len(brut.lstrip())]
    return ' ' * 8


# --------------------------------------------------------------------------
# Correctif backend
# --------------------------------------------------------------------------


def analyser_backend(source: str):
    try:
        arbre = ast.parse(source)
    except SyntaxError as exc:
        raise ErreurCorrectif("apps/reports/bi_analytics.py : syntaxe Python invalide (%s)." % exc)

    classe = None
    for n in ast.walk(arbre):
        if isinstance(n, ast.ClassDef) and n.name == NOM_CLASSE:
            classe = n
            break
    if classe is None:
        raise ErreurCorrectif("Classe %s introuvable dans bi_analytics.py." % NOM_CLASSE)

    fonction = None
    for n in classe.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == 'get':
            fonction = n
            break
    if fonction is None:
        raise ErreurCorrectif("Méthode get() introuvable dans %s." % NOM_CLASSE)

    noeuds = list(parcourir_sans_descendre(fonction))

    deja_parametre = any(
        isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'seller_id' for t in n.targets)
        for n in noeuds
    )
    deja_reponse = 'available_sellers' in source and 'selected_seller' in source
    deja = deja_parametre and deja_reponse

    cible_jours = None
    cible_courantes = None
    cible_precedentes = None
    cible_retour = None

    for n in noeuds:
        if cible_assignation(n, 'days'):
            # On privilégie l'affectation alimentée par request.query_params
            if cible_jours is None or 'query_params' in ast.dump(n.value):
                cible_jours = n
        if cible_courantes is None and cible_assignation(n, 'current_sales') and appel_sale_filter(n):
            cible_courantes = n
        if cible_precedentes is None and cible_assignation(n, 'prev_sales') and appel_sale_filter(n):
            cible_precedentes = n
        if isinstance(n, ast.Return) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) \
                and n.value.func.id == 'Response' and n.value.args \
                and isinstance(n.value.args[0], ast.Name) and n.value.args[0].id == 'response_payload':
            cible_retour = n

    manquants = []
    if cible_jours is None:
        manquants.append("affectation 'days = int(request.query_params.get(...))'")
    if cible_courantes is None:
        manquants.append("requête 'current_sales = Sale.objects.filter(...)'")
    if cible_precedentes is None:
        manquants.append("requête 'prev_sales = Sale.objects.filter(...)'")
    if cible_retour is None:
        manquants.append("'return Response(response_payload)'")

    return {
        'deja': deja,
        'manquants': manquants,
        'jours': cible_jours,
        'courantes': cible_courantes,
        'precedentes': cible_precedentes,
        'retour': cible_retour,
    }


def construire_backend(source: str, infos: dict) -> str:
    lignes = source.splitlines(keepends=True)
    insertions = []

    # 1) Lecture du paramètre seller_id (après l'affectation de `days`)
    indent = indentation_de(source, infos['jours'].lineno)
    insertions.append((infos['jours'].end_lineno, [indent + l + '\n' for l in LIGNES_PARAMETRES]))

    # 2) Filtre sur la période courante
    for cle, variable in (('courantes', 'current_sales'), ('precedentes', 'prev_sales')):
        node = infos[cle]
        indent = indentation_de(source, node.lineno)
        insertions.append((node.end_lineno, [indent + l + '\n' for l in lignes_filtre(variable)]))

    # 3) Liste des vendeurs + vendeur sélectionné dans la réponse HTTP
    indent = indentation_de(source, infos['retour'].lineno)
    bloc = [indent + ligne_reponse + '\n' for ligne_reponse in LIGNES_REPONSE]
    insertions.append((infos['retour'].lineno - 1, bloc))

    # Application en partant de la fin pour ne pas décaler les index
    for index, bloc_lignes in sorted(insertions, key=lambda x: x[0], reverse=True):
        lignes[index:index] = bloc_lignes

    return ''.join(lignes)


def patcher_backend(racine: str, dry_run: bool) -> str:
    chemin = os.path.join(racine, CHEMIN_BI)
    if not os.path.exists(chemin):
        raise ErreurCorrectif("Fichier introuvable : %s" % chemin)

    source = lire_texte(chemin)
    infos = analyser_backend(source)

    if infos['deja']:
        return "déjà corrigé (aucune modification)"

    if infos['manquants']:
        raise ErreurCorrectif(
            "Points d'insertion introuvables dans %s : %s.\n"
            "Aucune modification n'a été écrite. Envoyez ce fichier pour un correctif adapté."
            % (CHEMIN_BI, ' ; '.join(infos['manquants']))
        )

    nouveau = construire_backend(source, infos)

    try:
        ast.parse(nouveau)
    except SyntaxError as exc:
        raise ErreurCorrectif("Le fichier corrigé serait invalide (%s) : rien n'a été écrit." % exc)

    for marqueur in ('seller_id', 'available_sellers', 'selected_seller'):
        if marqueur not in nouveau:
            raise ErreurCorrectif("Insertion incomplète (%s manquant) : rien n'a été écrit." % marqueur)

    if dry_run:
        return "simulation OK (4 insertions prévues, fichier non modifié)"

    ecrire_texte(chemin, nouveau)
    return "corrigé (%d lignes ajoutées)" % (len(nouveau.splitlines()) - len(source.splitlines()))


# --------------------------------------------------------------------------
# Correctif frontend
# --------------------------------------------------------------------------


def patcher_frontend(racine: str, chemin_modele: str, dry_run: bool) -> str:
    chemin = os.path.join(racine, CHEMIN_PAGE)
    if not os.path.exists(chemin):
        raise ErreurCorrectif("Fichier introuvable : %s" % chemin)
    if not os.path.exists(chemin_modele):
        raise ErreurCorrectif("Modèle introuvable : %s" % chemin_modele)

    actuel = sha256(chemin)
    with open(chemin_modele, 'rb') as f:
        nouveau = f.read()
    nouveau_txt = nouveau.decode('utf-8')
    source = lire_texte(chemin)

    if MARQUEUR_DERNIER in nouveau_txt:
        raise ErreurCorrectif("Le modèle page-bi-filtre-vendeur.tsx a été altéré : utilisez le fichier d'origine.")

    if ('selectedSeller' in source
            and 'seller_id=${selectedSeller}' in source
            and 'Filtrer le bilan par vendeur' in source):
        return "déjà corrigé (aucune modification)"

    if actuel == SHA_PAGE_ORIGINAL:
        if dry_run:
            return "simulation OK (remplacement intégral par la version avec filtre vendeur)"
        shutil.copyfile(chemin_modele, chemin)
        return "corrigé (version avec sélecteur vendeur installée)"

    # Le fichier a changé depuis l'extraction : on délègue au compléteur, qui vérifie
    # chaque élément séparément et n'écrit que ce qui manque réellement.
    completeur = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'completer_filtre_vendeur_bi.py')
    if not os.path.exists(completeur):
        raise ErreurCorrectif(
            "page.tsx a été modifié depuis l'extraction (empreinte %s) : lancez "
            "completer_filtre_vendeur_bi.py, livré dans le même ZIP." % actuel[:12]
        )

    import importlib.util

    specification = importlib.util.spec_from_file_location('completer_filtre_vendeur_bi', completeur)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)

    texte, crlf = module.lire(chemin)
    journal = []
    nouveau = module.completer_page(texte, journal)
    critiques = [nom for nom, statut, critique in journal if critique and statut not in ('déjà présent', 'ajouté')]
    if critiques:
        raise ErreurCorrectif(
            "page.tsx a été modifié depuis l'extraction (empreinte %s) et ces éléments ne peuvent pas "
            "être insérés automatiquement : %s.\nRien n'a été écrit : lancez "
            "completer_filtre_vendeur_bi.py --verifier pour obtenir les repères de lignes."
            % (actuel[:12], ', '.join(critiques))
        )
    if nouveau == texte:
        return "déjà corrigé (aucune modification)"
    complements = sum(1 for _, statut, _ in journal if statut == 'ajouté')
    if dry_run:
        return "simulation OK (%d complément(s) par insertions ciblées)" % complements

    module.ecrire(chemin, nouveau, crlf)
    return "complété par insertions ciblées (%d complément(s))" % complements


# --------------------------------------------------------------------------
# Programme principal
# --------------------------------------------------------------------------


def main(argv=None) -> int:
    parseur = argparse.ArgumentParser(description="Correctif du filtre vendeur du bilan BI.")
    parseur.add_argument('--racine', default=None, help="Racine du projet (défaut : D:\\NEXORA si présent, sinon dossier courant)")
    parseur.add_argument('--modele', default=None, help="Chemin du fichier page.tsx corrigé (défaut : à côté de ce script)")
    parseur.add_argument('--dry-run', action='store_true', help="Simule sans rien écrire")
    parseur.add_argument('--verifier', action='store_true', help="N'applique rien : indique seulement l'état")
    parseur.add_argument('--sans-frontend', action='store_true', help="Ne corrige que le backend Django")
    parseur.add_argument('--sans-tests', action='store_true', help="Ne copie pas le test de vérification")
    options = parseur.parse_args(argv)

    if options.racine:
        racine = os.path.abspath(options.racine)
    elif os.path.isdir('D:\\NEXORA'):
        racine = 'D:\\NEXORA'
    else:
        racine = os.getcwd()
    modele = options.modele or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'page-bi-filtre-vendeur.tsx')

    print("=" * 76)
    print("NEXORA - filtre vendeur du bilan BI (écran Business Intelligence & Décision)")
    print("=" * 76)
    print("Racine du projet : %s" % racine)
    if not os.path.isdir(racine):
        print("ERREUR : le dossier n'existe pas.")
        return 2
    for rel in (CHEMIN_BI, CHEMIN_PAGE):
        etat = "présent" if os.path.exists(os.path.join(racine, rel)) else "ABSENT"
        print("  %-45s %s" % (rel, etat))
    print("-" * 76)

    if options.verifier:
        try:
            infos = analyser_backend(lire_texte(os.path.join(racine, CHEMIN_BI)))
            print("Backend  : %s" % ("déjà corrigé" if infos['deja'] else "à corriger (" + (', '.join(infos['manquants']) or 'points OK') + ")"))
        except (ErreurCorrectif, OSError) as exc:
            print("Backend  : %s" % exc)
        try:
            page = lire_texte(os.path.join(racine, CHEMIN_PAGE))
            complet = ('selectedSeller' in page
                       and 'seller_id=${selectedSeller}' in page
                       and 'Filtrer le bilan par vendeur' in page)
            if complet:
                etat = "déjà corrigé"
            elif 'selectedSeller' in page:
                etat = "correction PARTIELLE (complétez avec completer_filtre_vendeur_bi.py)"
            else:
                etat = "à corriger"
            print("Frontend : %s" % etat)
        except OSError as exc:
            print("Frontend : %s" % exc)
        return 0

    dossier_sauvegarde = None
    if not options.dry_run:
        horodatage = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        dossier_sauvegarde = os.path.join(racine, 'sauvegardes-filtre-vendeur-%s' % horodatage)
        copies = sauvegarder(racine, [CHEMIN_BI, CHEMIN_PAGE], dossier_sauvegarde)
        print("Sauvegarde : %s (%d fichier(s))" % (dossier_sauvegarde, len(copies)))

    resultats = []
    try:
        resultats.append(("apps/reports/bi_analytics.py", patcher_backend(racine, options.dry_run)))
    except ErreurCorrectif as exc:
        print("ECHEC backend : %s" % exc)
        return 1

    if not options.sans_frontend:
        try:
            resultats.append((CHEMIN_PAGE, patcher_frontend(racine, modele, options.dry_run)))
        except ErreurCorrectif as exc:
            print("ECHEC frontend : %s" % exc)
            return 1

    if not options.dry_run and not options.sans_tests:
        source_test = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_bi_vendeur_filtre.py')
        dossier_tests = os.path.join(racine, 'tests')
        if os.path.exists(source_test) and os.path.isdir(dossier_tests):
            cible = os.path.join(racine, CHEMIN_TESTS)
            if not os.path.exists(cible):
                shutil.copyfile(source_test, cible)
                resultats.append((CHEMIN_TESTS, "copié (test de vérification)"))

    print("-" * 76)
    for nom, etat in resultats:
        print("  %-45s %s" % (nom, etat))
    print("-" * 76)
    if options.dry_run:
        print("Mode simulation : aucun fichier n'a été modifié.")
    else:
        print("Correctif appliqué. Redémarrez le backend Django et le front (npm run dev).")
    print("Vérifications conseillées :")
    print("  python manage.py test tests.test_bi_analytics -v 2")
    print("  python manage.py test tests.test_bi_vendeur_filtre -v 2")
    print("  http://127.0.0.1:8000/api/v1/reports/bi-analytics/?view=executive&days=30")
    print("  http://127.0.0.1:8000/api/v1/reports/bi-analytics/?view=executive&days=30&seller_id=2")
    return 0


if __name__ == '__main__':
    sys.exit(main())
