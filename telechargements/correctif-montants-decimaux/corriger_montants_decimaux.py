# -*- coding: utf-8 -*-
"""Corrige les defauts flottants des champs de montant (NEXORA).

Un champ ecrit ainsi
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
rend un flottant (0.0) pour tout objet neuf qui n'a pas ete relu depuis la
base, et le premier calcul d'argent sur cet objet leve
    TypeError: unsupported operand type(s) for +=: 'float' and 'decimal.Decimal'

Ce correcteur remplace uniquement ces defauts par des Decimal :
    default=0.00  ->  default=Decimal('0.00')
Il ajoute l'import "from decimal import Decimal" quand il manque, sauvegarde
chaque fichier modifie dans sauvegardes-flottants/, installe le fichier de
tests tests/test_montants_decimaux.py et ne touche a aucune autre ligne.

Utilisation, dans le dossier du projet (celui qui contient manage.py) :

    py corriger_montants_decimaux.py              # corrige
    py corriger_montants_decimaux.py --verifier   # ne corrige rien, fait le point
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

# fichier -> (motif du champ, nombre de defauts attendus dans le projet d'origine)
FICHIERS = {
    'apps/catalog/models.py':    ('models', 4),
    'apps/inventory/models.py':  ('models', 7),
    'apps/partners/models.py':   ('models', 2),
    'apps/pos/models.py':        ('models', 5),
    'apps/purchases/models.py':  ('models', 6),
    'apps/sales/models.py':      ('models', 8),
    'apps/sales/serializers.py': ('serializers', 1),
}
TOTAL_ATTENDU = 33
TEST_A_INSTALLER = ('tests/test_montants_decimaux.py', 'test_montants_decimaux.py')


def motif(genre):
    """Motif precis : un DecimalField (modele ou formulaire) dont le defaut est un flottant."""
    return re.compile(r'(' + genre + r'\.DecimalField\(.*?default=)(\d+\.\d+)')


def dossier_projet(demande):
    if demande:
        return Path(demande).resolve()
    return Path(__file__).resolve().parent


def corriger(racine, verifier):
    sauvegardes = racine / 'sauvegardes-flottants'
    total, soucis, fichiers_touches = 0, [], 0

    print('=' * 72)
    print('NEXORA - defauts flottants sur les champs de montant')
    print('projet : %s' % racine)
    print('mode   : %s' % ('verification (aucune modification)' if verifier else 'correction'))
    print('=' * 72)

    for relatif, (genre, attendu) in FICHIERS.items():
        chemin = racine / relatif
        if not chemin.exists():
            print('  [ABSENT]  %-32s fichier introuvable' % relatif)
            soucis.append('%s : fichier introuvable' % relatif)
            continue

        source = chemin.read_text(encoding='utf-8')
        trouves = len(motif(genre).findall(source))
        if trouves == 0:
            print('  [DEJA OK] %-32s aucun defaut flottant' % relatif)
            continue

        if verifier:
            print('  [A FAIRE] %-32s %2d defaut(s) flottant(s)' % (relatif, trouves))
            total += trouves
            continue

        modifie = motif(genre).sub(r"\1Decimal('\2')", source)
        if 'from decimal import Decimal' not in modifie:
            for ancre in ('from django.db import models', 'from rest_framework import serializers'):
                if modifie.count(ancre) == 1:
                    modifie = modifie.replace(ancre, 'from decimal import Decimal\n\n' + ancre, 1)
                    break
            else:
                soucis.append('%s : import de Decimal a ajouter a la main' % relatif)

        reste = len(motif(genre).findall(modifie))
        if reste:
            soucis.append('%s : %d defaut(s) non corrige(s)' % (relatif, reste))
            continue

        destination = sauvegardes / relatif
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():          # on garde la premiere sauvegarde
            shutil.copy2(chemin, destination)
            etat_sauvegarde = 'sauvegarde creee'
        else:
            etat_sauvegarde = 'sauvegarde deja presente'
        chemin.write_text(modifie, encoding='utf-8')
        print('  [CORRIGE] %-32s %2d defaut(s)  (%s)' % (relatif, trouves, etat_sauvegarde))
        total += trouves
        fichiers_touches += 1

    if not verifier and total:
        print('\nTotal : %d defaut(s) flottant(s) corrige(s) dans %d fichier(s)'
              % (total, fichiers_touches))
        print('Sauvegardes : %s' % (racine / 'sauvegardes-flottants'))
        if total != TOTAL_ATTENDU:
            print('Note : %d defaut(s) trouve(s) au lieu des %d attendus.'
                  % (total, TOTAL_ATTENDU))
            print('       Votre arbre a evolue depuis la version corrigee :')
            print('       tous les defauts presents ont bien ete corriges.')
    elif verifier and total:
        print('\nTotal : %d defaut(s) flottant(s) restant(s)' % total)

    # installation du fichier de tests (a cote du script, ou deja dans tests/)
    ici = Path(__file__).resolve().parent
    cible_test = racine / TEST_A_INSTALLER[0]
    sources = [ici / TEST_A_INSTALLER[1], ici / TEST_A_INSTALLER[0], racine / TEST_A_INSTALLER[1]]
    source_test = next((chemin for chemin in sources if chemin.exists()), None)
    if source_test is None:
        soucis.append('%s : fichier de tests introuvable a cote du script' % TEST_A_INSTALLER[1])
    elif source_test.resolve() == cible_test.resolve():
        print('  [TEST] %s deja en place' % TEST_A_INSTALLER[0])
    elif not verifier:
        cible_test.parent.mkdir(parents=True, exist_ok=True)
        if cible_test.exists() and cible_test.read_bytes() != source_test.read_bytes():
            secours = cible_test.with_suffix('.py.ancien')
            shutil.copy2(cible_test, secours)
            print('  [NOTE] une version differente de %s existait : gardee en %s'
                  % (TEST_A_INSTALLER[0], secours.name))
        shutil.copy2(source_test, cible_test)
        print('  [TEST] %s installe' % TEST_A_INSTALLER[0])

    print('\n' + '-' * 72)
    if soucis:
        print('Points a signaler :')
        for souci in soucis:
            print('  - %s' % souci)
    if verifier:
        print('Verification terminee. Pour corriger :')
        print('    py corriger_montants_decimaux.py')
    else:
        print('Verification des tests a lancer maintenant :')
        print('    py manage.py test tests.test_montants_decimaux -v 2')
        print('    py manage.py test')
    print('-' * 72)
    return 1 if soucis else 0


def main():
    analyseur = argparse.ArgumentParser(description='Corrige les defauts flottants des champs de montant NEXORA.')
    analyseur.add_argument('--racine', help='dossier du projet (defaut : celui de ce script)')
    analyseur.add_argument('--verifier', action='store_true', help='ne rien modifier, seulement faire le point')
    options = analyseur.parse_args()
    return corriger(dossier_projet(options.racine), options.verifier)


if __name__ == '__main__':
    sys.exit(main())
