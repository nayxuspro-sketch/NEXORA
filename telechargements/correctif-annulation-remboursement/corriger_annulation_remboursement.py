# -*- coding: utf-8 -*-
"""Annulation d'une vente encaissee : remboursement automatique (NEXORA).

REGLE VALIDEE PAR LE COMMERCANT (8 octobre 2026) : annuler une vente deja
encaissee rembourse ce qui a ete encaisse.

    AVANT : la vente passait en « Annulee », le stock etait rendu, mais
            l'argent restait dans la caisse et le montant paye restait affiche.
    APRES : un CONTRE-MOUVEMENT est ecrit pour chaque paiement (montant
            negatif, meme methode, meme caisse, reference ANNUL-...) ;
            les especes sont retirees du solde de la caisse ; la creance du
            client est diminuee du credit accorde ; le montant paye revient a
            zero, statut « Rembourse » ; le stock est rendu comme avant.

Garde-fous inclus :
  - caisse non ouverte (session deja cloturee) : le solde n'est PAS touche,
    la trace du contre-mouvement le precise ;
  - un retour deja enregistre sur la vente : l'annulation est REFUSEE (sinon
    l'argent serait rendu deux fois) ;
  - creance client jamais negative : plafonnee a zero, et tracee ;
  - vente non payee : annulation sans aucun mouvement d'argent.

Ce que fait ce correcteur :
  - remplace la fonction cancel_sale de apps/sales/services.py par la version
    qui rembourse (rien d'autre n'est touche dans le fichier) ;
  - installe ou met a jour tests/test_annulation_remboursement.py (9 tests) ;
  - met a jour tests/test_regles_argent.py : l'ancien test qui CONSTATAIT
    l'absence de remboursement est remplace par celui de la nouvelle regle
    (l'ancien est garde en .py.ancien) ;
  - sauvegarde chaque fichier modifie dans sauvegardes-annulation-remboursement/ ;
  - verifie que le fichier corrige compile AVANT d'ecrire ;
  - ne touche PAS au calcul du vendeur ni aux marqueurs _nexora_* du correctif
    POS, ni au reste du service.

Usage, dans le dossier du projet (celui qui contient manage.py) :

    py corriger_annulation_remboursement.py --verifier   # fait le point
    py corriger_annulation_remboursement.py              # corrige
    py corriger_annulation_remboursement.py --racine D:\\NEXORA
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

CHEMIN_SERVICES = Path('apps/sales/services.py')
NOM_SERVICES = 'services.py'
DOSSIER_SAUVEGARDE = 'sauvegardes-annulation-remboursement'

# Le fichier ne doit pas etre modifie si le correctif POS n'est pas reconnu :
# on ne touche jamais a un service inattendu.
MARQUEUR_NOUVEAU = 'MOUVEMENT D\'ARGENT (regle validee le 8 octobre 2026)'
MARQUEUR_ANCIEN = 'Cancels a sale, reverts all stock deductions, and adjusts payments.'
MARQUEUR_ANCIEN_2 = 'AUCUN MOUVEMENT D\'ARGENT'

# Nouvelle fonction, inseree telle quelle (extraite du fichier corrige).
NOUVELLE_FONCTION = '''    def cancel_sale(cls, sale, user=None, reason=''):
        """
        Annule une vente et rend les articles au stock.

        MOUVEMENT D'ARGENT (regle validee le 8 octobre 2026) : annuler une vente
        deja encaissee rembourse ce qui a ete encaisse.
          1. un CONTRE-MOUVEMENT est ecrit pour chaque paiement (montant negatif,
             meme methode, meme caisse, reference ANNUL-...) : trace complete ;
          2. les especes sont retirees du solde de la caisse concernee ;
          3. la creance du client est diminuee du credit accorde sur la vente ;
          4. le montant paye revient a zero, statut « Rembourse ».

        Garde-fous :
          - caisse non ouverte (session deja cloturee) : le solde n'est PAS
            touche, la trace du contre-mouvement le precise ;
          - retour deja enregistre sur la vente : l'annulation est refusee
            (sinon l'argent serait rendu deux fois) ;
          - creance client plafonnee a zero, jamais negative, et tracee ;
          - vente non payee : aucun mouvement d'argent.
        """
        if sale.status == SaleStatus.CANCELLED:
            raise ValidationError("Cette vente est déjà annulée.")

        # Un retour a deja rendu du stock ET de l'argent : annuler en plus
        # rembourserait le client deux fois.
        retour = sale.returns.first()
        if retour is not None:
            raise ValidationError(
                "Un retour (%s) a déjà été enregistré sur cette vente : "
                "l'annuler rembourserait deux fois. Passez par le retour, ou "
                "supprimez-le d'abord." % retour.reference
            )

        # 1-2-3. Contre-mouvement par paiement, caisse et creance ajustees.
        rembourse = False
        for paiement in sale.payments.all():
            montant_oppose = -paiement.amount
            if montant_oppose == Decimal('0.00'):
                continue
            rembourse = True
            traces = []

            caisse_cible = paiement.register or sale.register
            if paiement.payment_method == PaymentMethod.CASH and caisse_cible is not None:
                if caisse_cible.status == RegisterStatus.OPEN:
                    caisse_cible.current_balance += montant_oppose
                    caisse_cible.save()
                else:
                    # Garde-fou : la caisse est deja cloturee, son solde a ete
                    # controle et arrete. On ne le modifie pas apres coup, mais
                    # le contre-mouvement est ecrit : l'argent rendu est trace.
                    traces.append('caisse fermee : solde non modifie')

            if paiement.payment_method == PaymentMethod.CREDIT and sale.customer is not None:
                creance = sale.customer.current_balance + montant_oppose
                if creance < Decimal('0.00'):
                    creance = Decimal('0.00')
                    traces.append('creance plafonnee a zero')
                sale.customer.current_balance = creance
                sale.customer.save()

            reference = 'ANNUL-%s' % sale.reference
            if reason:
                reference = '%s (%s)' % (reference, reason)
            if traces:
                reference = '%s [%s]' % (reference, ' ; '.join(traces))

            Payment.objects.create(
                company=sale.company,
                sale=sale,
                amount=montant_oppose,
                payment_method=paiement.payment_method,
                register=paiement.register,
                partner=paiement.partner,
                reference=reference[:100],
                processed_by=user,
            )

        # 4. Remboursement au niveau de la vente
        if rembourse:
            sale.paid_amount = Decimal('0.00')
            sale.payment_status = PaymentStatus.REFUNDED

        # 5. Retour des articles au stock (comportement inchange)
        for item in sale.items.all():
            StockService.record_movement(
                company=sale.company,
                store=sale.store,
                product=item.product,
                quantity=item.quantity, # positive adjustment to restore
                movement_type=StockMovementType.RETURN_CUSTOMER,
                reference=f"CANCEL-{sale.reference}",
                reason=f"Annulation vente: {reason}",
                user=user,
                allow_negative=True
            )

        sale.status = SaleStatus.CANCELLED
        sale.save()
        return sale
'''

# Tests livres avec le correcteur : destination -> nom du fichier a cote du script
TESTS = [
    ('tests/test_annulation_remboursement.py', 'test_annulation_remboursement.py'),
    ('tests/test_regles_argent.py', 'test_regles_argent.py'),
]

MOTIF_FONCTION = re.compile(
    r'(?P<entete>[ \t]*def cancel_sale\((?:cls|self)[^\n]*\):\n.*?)'
    r'(?=\n[ \t]*@classmethod)',
    re.S,
)


def dossier_projet(demande):
    if demande:
        return Path(demande).resolve()
    return Path(__file__).resolve().parent


def trouver_services(racine):
    attendu = racine / CHEMIN_SERVICES
    if attendu.exists():
        return attendu
    for candidat in racine.rglob(NOM_SERVICES):
        if 'node_modules' in candidat.parts or '.git' in candidat.parts:
            continue
        if contient_annulation(candidat):
            return candidat
    return None


def contient_annulation(chemin):
    try:
        return 'def cancel_sale(' in chemin.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return False


def sauvegarder(racine, chemin, marqueur_racine=True):
    relatif = chemin.relative_to(racine) if racine in chemin.parents else Path(chemin.name)
    destination = racine / DOSSIER_SAUVEGARDE / relatif
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copy2(chemin, destination)
        return destination, True
    return destination, False


def installer_test(racine, cible_relative, nom_livre, verifier, journal):
    ici = Path(__file__).resolve().parent
    cible = racine / cible_relative
    origine = next((chemin for chemin in
                    (ici / nom_livre, ici / 'fichiers' / cible_relative,
                     ici / cible_relative, ici / 'fichiers' / nom_livre,
                     racine / nom_livre)
                    if chemin.exists()), None)
    if origine is None:
        journal.append('%s introuvable a cote du script' % nom_livre)
        return
    if origine.resolve() == cible.resolve():
        journal.append('%s deja en place' % cible_relative)
        return
    if verifier:
        journal.append('%s sera installe' % cible_relative)
        return
    cible.parent.mkdir(parents=True, exist_ok=True)
    if cible.exists() and cible.read_bytes() != origine.read_bytes():
        secours = cible.with_suffix('.py.ancien')
        shutil.copy2(cible, secours)
        journal.append('%s : ancienne version gardee en %s' % (cible_relative, secours.name))
    shutil.copy2(origine, cible)
    journal.append('%s installe' % cible_relative)


def corriger(racine, verifier):
    print('=' * 76)
    print('NEXORA - annulation d une vente encaissee : REMBOURSEMENT automatique')
    print('projet : %s' % racine)
    print('mode   : %s' % ('verification (aucune modification)' if verifier else 'correction'))
    print('=' * 76)

    resultat = 0
    journal = []

    services = trouver_services(racine)
    if services is None:
        print('  [ECHEC] apps/sales/services.py introuvable sous %s' % racine)
        print('          Indiquez le dossier du projet avec --racine.')
        return 1

    print('  fichier : %s' % (services.relative_to(racine) if racine in services.parents else services))
    source = services.read_text(encoding='utf-8')

    if MARQUEUR_NOUVEAU in source:
        print('  [DEJA OK] l annulation rembourse deja (correctif deja en place)')
    else:
        if MARQUEUR_ANCIEN not in source and MARQUEUR_ANCIEN_2 not in source:
            print('  [ATTENTION] la fonction d annulation de ce fichier ne ressemble')
            print('              pas a celle attendue. Le fichier n a PAS ete modifie.')
            print('              Envoyez-le tel quel : la correction sera adaptee.')
            resultat = 1
        elif verifier:
            print('  [A FAIRE] l annulation ne rembourse pas encore l encaissement')
            resultat = 1
        else:
            trouve = MOTIF_FONCTION.search(source)
            if trouve is None:
                print('  [ECHEC] fonction cancel_sale introuvable ou de forme inattendue.')
                print('          Le fichier n a PAS ete modifie.')
                return 1
            modifie = source[:trouve.start()] + NOUVELLE_FONCTION + source[trouve.end():]
            if MARQUEUR_NOUVEAU not in modifie:
                print('  [ECHEC] insertion impossible : le fichier n a PAS ete modifie.')
                return 1
            try:
                compile(modifie, str(services), 'exec')
            except SyntaxError as erreur:
                print('  [ECHEC] le fichier corrige ne compile pas : %s' % erreur)
                print('          RIEN n a ete ecrit.')
                return 1

            destination, creee = sauvegarder(racine, services)
            services.write_text(modifie, encoding='utf-8')
            print('  [CORRIGE] l annulation rembourse desormais l encaissement')
            print('            (%s : %s)' % ('sauvegarde creee' if creee else 'sauvegarde deja presente',
                                            destination))
            compile(services.read_text(encoding='utf-8'), str(services), 'exec')

    for cible, nom in TESTS:
        installer_test(racine, cible, nom, verifier, journal)

    print('\n' + '-' * 76)
    if journal:
        for ligne in journal:
            print('  %s' % ligne)
        print('-' * 76)
    if verifier:
        print('Pour corriger :  py corriger_annulation_remboursement.py')
    else:
        print('Verification a lancer maintenant :')
        print('    py manage.py test tests.test_annulation_remboursement -v 2   (attendu : 9 OK)')
        print('    py manage.py test tests.test_regles_argent -v 2             (attendu : 16 OK)')
        print('    py manage.py test                                          (attendu : OK)')
        print('Controle dans l application : annulez une vente encaissee en especes.')
        print('La caisse doit diminuer du montant rembourse, la vente afficher 0 F')
        print('paye en « Rembourse », et la trace ANNUL-... doit exister.')
    print('-' * 76)
    return resultat


def main():
    analyseur = argparse.ArgumentParser(
        description="Corrige l'annulation des ventes : remboursement automatique (NEXORA).")
    analyseur.add_argument('--racine', help='dossier du projet (defaut : celui de ce script)')
    analyseur.add_argument('--verifier', action='store_true',
                           help='ne rien modifier, seulement faire le point')
    options = analyseur.parse_args()
    return corriger(dossier_projet(options.racine), options.verifier)


if __name__ == '__main__':
    sys.exit(main())
