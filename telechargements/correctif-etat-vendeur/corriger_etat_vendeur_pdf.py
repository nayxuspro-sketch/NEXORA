# -*- coding: utf-8 -*-
"""Corrige l'etat de vente individuel du vendeur (PDF) : la periode demandee
est respectee.

Symptome constate dans l'application :

    l'etat de vente individuel du vendeur (bouton du POS, rapport PDF de
    2 pages) n'affiche plus les donnees justes : un rapport demande sur une
    periode passee (par exemple du 01/01 au 31/01) contient des ventes
    enregistrees depuis, et ses totaux sont donc faux.

Cause exacte, une seule ligne de apps/sales/pdf_seller_report.py :

        if not end_date:
            end_date = now + timezone.timedelta(days=1)
        else:
            # S'assurer que les ventes de la minute presente ...
            end_date = max(end_date, now + timezone.timedelta(hours=4))

    La date de fin choisie est ECRASEE par « maintenant + 4 h ». La ligne etait
    la pour ne pas rater les ventes de la minute en cours, mais elle est inutile :
    la date de fin est deja placee a 23:59:59 de la journee selectionnee.

Ce que fait ce correcteur :
  - remplace ce bloc par la version juste (la date de fin choisie est respectee) ;
  - installe le fichier de tests tests/test_etat_vendeur_pdf.py (4 tests) ;
  - sauvegarde le fichier modifie dans sauvegardes-etat-vendeur/ ;
  - ne touche a rien d'autre. Relance = aucun changement (idempotent).

Usage, dans le dossier du projet (celui qui contient manage.py) :

    py corriger_etat_vendeur_pdf.py --verifier     # fait le point, ne modifie rien
    py corriger_etat_vendeur_pdf.py                # corrige
    py corriger_etat_vendeur_pdf.py --racine D:\\NEXORA
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

NOM_FICHIER = 'pdf_seller_report.py'
CHEMIN_ATTENDU = Path('apps/sales/pdf_seller_report.py')
DOSSIER_SAUVEGARDE = 'sauvegardes-etat-vendeur'
FICHIER_TEST = ('tests/test_etat_vendeur_pdf.py', 'test_etat_vendeur_pdf.py')

# Le bloc fautif, tolere sur les espaces et sur la presence du commentaire.
MOTIF_FAUTIF = re.compile(
    r'(?P<ind>[ \t]*)if not end_date:\n'
    r'(?P=ind)[ \t]+end_date = now \+ timezone\.timedelta\(days=1\)\n'
    r'(?P=ind)else:\n'
    r'(?:[ \t]*#[^\n]*\n)*'
    r'(?P=ind)[ \t]+end_date = max\(end_date, now \+ timezone\.timedelta\(hours=4\)\)\n'
)

# Marqueur du correctif : sa presence signifie que le fichier est deja juste.
MARQUEUR = 'date de fin choisie est respectee'

REMPLACEMENT = (
    '{ind}if not end_date:\n'
    '{ind}    end_date = now + timezone.timedelta(days=1)\n'
    '{ind}# La date de fin choisie est respectee telle quelle : elle couvre deja\n'
    '{ind}# toute la journee selectionnee (23:59:59). L\'ancien code la remplacait\n'
    '{ind}# par « maintenant + 4 h » : un rapport demande sur une periode passee\n'
    '{ind}# contenait alors toutes les ventes enregistrees depuis.\n'
)


def dossier_projet(demande):
    if demande:
        return Path(demande).resolve()
    return Path(__file__).resolve().parent


def trouver_fichier(racine):
    """Le fichier du rapport PDF vendeur : au chemin attendu, sinon recherche."""
    attendu = racine / CHEMIN_ATTENDU
    if attendu.exists():
        return attendu
    for candidat in racine.rglob(NOM_FICHIER):
        if 'node_modules' in candidat.parts or '.git' in candidat.parts:
            continue
        return candidat
    return None


def corriger(racine, verifier):
    print('=' * 74)
    print('NEXORA - etat de vente individuel du vendeur : periode respectee')
    print('projet : %s' % racine)
    print('mode   : %s' % ('verification (aucune modification)' if verifier else 'correction'))
    print('=' * 74)

    fichier = trouver_fichier(racine)
    if fichier is None:
        print('  [ECHEC] %s introuvable sous %s' % (NOM_FICHIER, racine))
        print('\nIndiquez le dossier du projet avec --racine, ou lancez ce script')
        print('depuis le dossier qui contient manage.py.')
        return 1

    relatif = fichier.relative_to(racine) if racine in fichier.parents else fichier
    source = fichier.read_text(encoding='utf-8')
    print('  fichier : %s' % relatif)

    fautifs = MOTIF_FAUTIF.findall(source)
    deja_corrige = 'timedelta(hours=4)' not in source

    if deja_corrige:
        if MARQUEUR in source:
            print('  [DEJA OK] la date de fin choisie est deja respectee')
            resultat = 0
        else:
            print("  [ATTENTION] 'timedelta(hours=4)' est absent de ce fichier, mais")
            print("              il ne vient pas de ce correcteur : verifiez a la main.")
            print('              Le fichier n\'a PAS ete modifie.')
            resultat = 1
    elif len(fautifs) != 1:
        print('  [ANOMALIE] %d bloc(s) correspondant(s) attendu(s) : 1.' % len(fautifs))
        print('              Le fichier n\'a PAS ete modifie. Envoyez le fichier tel')
        print('              quel : la correction sera adaptee a vos lignes exactes.')
        resultat = 1
    elif verifier:
        print('  [A FAIRE] la date de fin choisie est ecrasee par « maintenant + 4 h »')
        print('            -> un rapport sur une periode passee contient des ventes')
        print('               enregistrees depuis : les totaux sont faux.')
        resultat = 1
    else:
        indentation = fautifs[0]
        modifie = MOTIF_FAUTIF.sub(REMPLACEMENT.format(ind=indentation), source, count=1)
        if 'timedelta(hours=4)' in modifie:
            print('  [ECHEC] le bloc fautif est toujours present apres correction.')
            return 1
        try:
            compile(modifie, str(fichier), 'exec')       # syntaxe verifiee avant ecriture
        except SyntaxError as erreur:
            print('  [ECHEC] le fichier corrige ne compile pas : %s' % erreur)
            print('          RIEN n\'a ete ecrit.')
            return 1

        sauvegarde = racine / DOSSIER_SAUVEGARDE / relatif
        sauvegarde.parent.mkdir(parents=True, exist_ok=True)
        if not sauvegarde.exists():
            shutil.copy2(fichier, sauvegarde)
            etat = 'sauvegarde creee'
        else:
            etat = 'sauvegarde deja presente'
        fichier.write_text(modifie, encoding='utf-8')
        print('  [CORRIGE] la date de fin choisie est desormais respectee (%s)' % etat)
        print('            sauvegarde : %s' % sauvegarde)
        resultat = 0

        # le fichier corrige doit toujours compiler
        compile(fichier.read_text(encoding='utf-8'), str(fichier), 'exec')

    # installation du fichier de tests
    ici = Path(__file__).resolve().parent
    cible = racine / FICHIER_TEST[0]
    sources = [ici / FICHIER_TEST[1], ici / FICHIER_TEST[0], racine / FICHIER_TEST[1]]
    origine = next((chemin for chemin in sources if chemin.exists()), None)
    if origine is None:
        print('  [NOTE] %s introuvable a cote du script : tests non installes' % FICHIER_TEST[1])
    elif origine.resolve() == cible.resolve():
        print('  [TEST] %s deja en place' % FICHIER_TEST[0])
    elif verifier:
        print('  [TEST] %s sera installe' % FICHIER_TEST[0])
    else:
        cible.parent.mkdir(parents=True, exist_ok=True)
        if cible.exists() and cible.read_bytes() != origine.read_bytes():
            shutil.copy2(cible, cible.with_suffix('.py.ancien'))
            print('  [NOTE] ancienne version de %s gardee en .py.ancien' % FICHIER_TEST[0])
        shutil.copy2(origine, cible)
        print('  [TEST] %s installe' % FICHIER_TEST[0])

    print('\n' + '-' * 74)
    if verifier:
        print('Pour corriger :  py corriger_etat_vendeur_pdf.py')
    else:
        print('Verification a lancer maintenant :')
        print('    py manage.py test tests.test_etat_vendeur_pdf -v 2     (attendu : 4 OK)')
        print('    py manage.py test                                     (attendu : OK)')
        print('Controle dans l\'application : bouton « Rapport Individuel Vendeur »,')
        print('periode du 01/01 au 31/01 : le PDF ne doit contenir que les ventes de')
        print('cette periode, et les totaux doivent y correspondre.')
    print('-' * 74)
    return resultat


def main():
    analyseur = argparse.ArgumentParser(
        description="Corrige la periode de l'etat de vente individuel du vendeur (NEXORA).")
    analyseur.add_argument('--racine', help='dossier du projet (defaut : celui de ce script)')
    analyseur.add_argument('--verifier', action='store_true',
                           help='ne rien modifier, seulement faire le point')
    options = analyseur.parse_args()
    return corriger(dossier_projet(options.racine), options.verifier)


if __name__ == '__main__':
    sys.exit(main())
