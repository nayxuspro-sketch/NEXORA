# -*- coding: utf-8 -*-
"""NEXORA : « Magasin introuvable dans votre entreprise » en caisse.

LE MESSAGE SIGNALE
    Echec de la transaction
    Magasin introuvable dans votre entreprise

CE QUI SE PASSE VRAIMENT
  1. Le POS lit la liste des caisses (/api/v1/registers/) et prend la
     PREMIERE. Si cette liste est vide, il utilise une caisse INVENTEE
     (« Caisse Comptoir Principal », code REG-01, id « reg-01 », magasin
     « store-01 »). Or le serveur exige un identifiant (UUID) reel : un
     magasin inexistant est donc refuse par la garde de securite livree
     precedemment (« Magasin introuvable dans votre entreprise »). Le POS
     masquait le vrai probleme : « aucune caisse », pas « magasin inconnu ».
  2. Cette caisse inventee ne s'affiche jamais comme telle : elle ressemble
     a une vraie caisse (nom, solde 125 000 F, magasin).
  3. Le serveur ne peut pas creer proprement les caisses : son controle
     laisse passer une caisse rattachee au magasin d'une AUTRE entreprise
     (faille reproduite : 201 au lieu de 400). Une telle caisse envoie le
     magasin d'une autre entreprise a chaque vente, d'ou le message.

CE QUE FAIT CE CORRECTEUR
  Cote serveur, ventes (apps/sales/views.py) :
    - si la vente n'indique pas de magasin, prendre celui de SA CAISSE
      (avant : le premier magasin de l'entreprise, ce qui pouvait rattacher
      la vente a un autre magasin que celui de la caisse) ;
    - si le magasin ET la caisse sont fournis mais ne vont pas ensemble,
      refuser avec un message precis (« La caisse choisie n'appartient pas a
      ce magasin ») au lieu d'une erreur incomprehensible.
  Cote serveur (apps/pos/serializers.py) :
    - valider a l'ecriture que le magasin de la caisse appartient bien a
      l'entreprise de l'utilisateur (refus 400 explicite sinon). Le magasin
      reste choisissable a la creation (c'est le parcours normal) ; c'est le
      magasin d'une AUTRE entreprise qui est refuse.
  Cote caisse (app/pos/page.tsx) :
    - plus de caisse inventee : si aucune caisse n'existe ou si elle est
      fermee, le POS affiche un ecran d'installation clair avec les deux
      raccourcis qui manquaient (creer une caisse deja rattachee au bon
      magasin, creer un magasin) — la commande de bascule redevient claire
      et l'echec s'affiche franchement sur le ticket.

Usage, dans le dossier du projet (celui qui contient manage.py) :

    py corriger_caisses_pos.py --verifier   # fait le point, ne modifie rien
    py corriger_caisses_pos.py              # corrige
    py corriger_caisses_pos.py --racine C:\\NEXORA
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

DOSSIER_SAUVEGARDE = 'sauvegardes-caisses-pos'
COMMANDE_DIAGNOSTIC = Path('apps/pos/management/commands/diagnostiquer_caisses.py')
FICHIER_TEST = Path('tests/test_caisse_pos_magasin.py')
FICHIER_SERIALISEUR = Path('apps/pos/serializers.py')
FICHIER_POS = Path('frontend/src/app/pos/page.tsx')
FICHIER_VENTES = Path('apps/sales/views.py')
FICHIER_SERIALISEUR_VENTE = Path('apps/sales/serializers.py')

ANCRE_STORE_REQUIS = "    store = serializers.UUIDField()"
REMPLACEMENT_STORE_OPTIONNEL = """    # Le magasin n'est plus obligatoire : si la caisse est fournie, le
    # serveur en deduit le magasin (une vente ne peut ainsi pas porter un
    # autre magasin que celui de sa caisse).
    store = serializers.UUIDField(required=False, allow_null=True)"""

DIAGNOSTIC_TEXTE = '# -*- coding: utf-8 -*-\n"""Diagnostic des magasins et des caisses, entreprise par entreprise.\n\nRepond a la question : « pourquoi la caisse affiche-t-elle Magasin\nintrouvable dans votre entreprise ? »\n\n    py manage.py diagnostiquer_caisses\n\nLe rapport est en LECTURE SEULE : il ne modifie aucune donnee.\n"""\n\nfrom django.core.management.base import BaseCommand\n\nfrom apps.accounts.models import User\nfrom apps.companies.models import Company\nfrom apps.inventory.models import Store\nfrom apps.pos.models import CashRegister\n\n\nclass Command(BaseCommand):\n    help = \'Montre les magasins, les caisses et les comptes par entreprise.\'\n\n    def handle(self, *args, **options):\n        entreprises = list(Company.objects.all().order_by(\'name\'))\n        if not entreprises:\n            self.stdout.write(\'Aucune entreprise en base : creez-en une, puis un magasin, puis une caisse.\')\n            return\n\n        self.stdout.write(\'DIAGNOSTIC DES CAISSES NEXORA\')\n        self.stdout.write(\'=\' * 74)\n\n        total_magasins = Store.objects.count()\n        total_caisses = CashRegister.objects.count()\n        self.stdout.write(\'%d entreprise(s), %d magasin(s), %d caisse(s) au total.\'\n                          % (len(entreprises), total_magasins, total_caisses))\n        self.stdout.write(\'\')\n\n        for entreprise in entreprises:\n            magasins = Store.objects.filter(company=entreprise).order_by(\'name\')\n            caisses = CashRegister.objects.filter(company=entreprise).select_related(\'store\')\n            self.stdout.write(\'ENTREPRISE : %s\' % entreprise.name)\n            self.stdout.write(\'  magasins : %s\' % (\n                \', \'.join(\'%s (%s)\' % (m.name, m.code) for m in magasins) or \'AUCUN\'))\n            if caisses:\n                for caisse in caisses:\n                    self.stdout.write(\'  caisse   : %s (%s) -> magasin %s [%s]\'\n                                      % (caisse.name, caisse.code, caisse.store.name, caisse.status))\n            else:\n                self.stdout.write(\'  caisse   : AUCUNE\')\n            comptes = User.objects.filter(company=entreprise).order_by(\'email\')\n            self.stdout.write(\'  comptes  : %s\' % (\n                \', \'.join(\'%s (%s)\' % (u.email, u.role) for u in comptes) or \'AUCUN\'))\n            self.stdout.write(\'\')\n\n        # --- anomalies qui provoquent exactement le message signale ---\n        anomalies = 0\n        for caisse in CashRegister.objects.select_related(\'store\', \'company\'):\n            if caisse.store.company_id != caisse.company_id:\n                anomalies += 1\n                self.stdout.write(\'ANOMALIE : la caisse %s (%s) appartient a « %s » mais vise le \'\n                                  \'magasin « %s » de « %s »\'\n                                  % (caisse.name, caisse.code, caisse.company.name,\n                                     caisse.store.name, caisse.store.company.name))\n        for compte in User.objects.select_related(\'company\').all():\n            if compte.is_superuser or compte.company_id is None:\n                continue\n            if not Store.objects.filter(company_id=compte.company_id).exists():\n                anomalies += 1\n                self.stdout.write(\'ANOMALIE : le compte %s n\\\'a AUCUN magasin dans son entreprise \'\n                                  \'(« %s ») : la caisse ne peut rien vendre.\'\n                                  % (compte.email, compte.company.name if compte.company else \'—\'))\n            elif not CashRegister.objects.filter(company_id=compte.company_id).exists():\n                anomalies += 1\n                self.stdout.write(\'A REMARQUER : le compte %s n\\\'a AUCUNE caisse dans son entreprise \'\n                                  \'(« %s ») : le POS proposera d\\\'en creer une.\'\n                                  % (compte.email, compte.company.name if compte.company else \'—\'))\n\n        self.stdout.write(\'=\' * 74)\n        if anomalies:\n            self.stdout.write(\'%d point(s) a regarder (voir ci-dessus).\' % anomalies)\n            self.stdout.write(\'Correction conseillee : lancer corriger_caisses_pos.py, puis\')\n            self.stdout.write(\'creer magasin et caisse directement depuis l\\\'ecran de caisse du POS.\')\n        else:\n            self.stdout.write(\'Aucune anomalie : chaque caisse vise un magasin de sa propre entreprise.\')\n'


def installer_diagnostic(racine):
    """Installe (ou met a jour) la commande de diagnostic."""
    chemin = racine / COMMANDE_DIAGNOSTIC
    chemin.parent.mkdir(parents=True, exist_ok=True)
    for paquet in (chemin.parent, chemin.parent.parent):
        marqueur = chemin.parent.parent / '__init__.py' if paquet == chemin.parent.parent else paquet / '__init__.py'
        if not marqueur.exists():
            marqueur.write_text('', encoding='utf-8')
    return _mettre_a_jour_mon_fichier(
        racine, chemin, DIAGNOSTIC_TEXTE, 'diagnostiquer_caisses',
        'commande py manage.py diagnostiquer_caisses')


TEST_TEXTE = '"""La caisse du POS doit etre rattachee a un magasin de SON entreprise.\n\nReproduit l\'erreur signalee en caisse :\n\n    Echec de la transaction\n    Magasin introuvable dans votre entreprise\n\nTrois regles sont verrouillees ici :\n\n  1. le magasin d\'une AUTRE entreprise est refuse (c\'est le message signale) ;\n  2. une caisse ne peut pas viser le magasin d\'une autre entreprise (trou\n     ferme par le correctif : avant, la creation passait en 201) ;\n  3. le parcours normal fonctionne : creer la caisse sur son magasin,\n     l\'ouvrir, vendre, et retrouver la vente — y compris en n\'envoyant que\n     la caisse (le serveur en deduit le magasin).\n\nLancer :\n\n    py manage.py test tests.test_caisse_pos_magasin -v 2\n"""\n\nfrom decimal import Decimal\n\nfrom rest_framework import status\n\nfrom tests.test_nexora_backend import BaseNexoraTestCase\n\n\nclass CaissePosMagasinTests(BaseNexoraTestCase):\n\n    def test_1_magasin_d_une_autre_entreprise_refuse_avec_le_message_signe(self):\n        """Le message exact signale en caisse est bien produit par le serveur."""\n        reponse = self.client_a.post(\'/api/v1/sales/\', {\n            \'store\': str(self.store_b.id),       # magasin de l\'entreprise B\n            \'items\': [{\'product\': str(self.product_a1.id), \'quantity\': Decimal(\'1.00\'),\n                       \'unit_price\': Decimal(\'800.00\'), \'tax_rate\': Decimal(\'20.00\')}],\n            \'payment\': {\'amount\': \'944.00\', \'method\': \'CASH\', \'reference\': \'POS-PAY-000001\'},\n        }, format=\'json\')\n        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST, reponse.content[:300])\n        self.assertEqual(reponse.data.get(\'error\'), \'Magasin introuvable dans votre entreprise\')\n\n    def test_2_magasin_non_identifiant_refuse_clairement(self):\n        """Un magasin qui n\'est pas un identifiant reel (« store-01 ») est refuse.\n\n        Selon la version de vos fichiers, ce refus vient du formulaire d\'entree\n        (details.store) ou de la garde du serveur (error) : dans les deux cas,\n        le message designe clairement le magasin.\n        """\n        reponse = self.client_a.post(\'/api/v1/sales/\', {\n            \'store\': \'store-01\',                 # valeur inventee (caisse fictive)\n            \'register\': \'reg-01\',\n            \'items\': [{\'product\': str(self.product_a1.id), \'quantity\': Decimal(\'1.00\'),\n                       \'unit_price\': Decimal(\'800.00\'), \'tax_rate\': Decimal(\'20.00\')}],\n            \'payment\': {\'amount\': \'944.00\', \'method\': \'CASH\', \'reference\': \'POS-PAY-000002\'},\n        }, format=\'json\')\n        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST, reponse.content[:300])\n        details = reponse.data.get(\'details\') or {}\n        message = \'%s %s\' % (reponse.data.get(\'error\', \'\'), reponse.data.get(\'message\', \'\'))\n        self.assertTrue(\'store\' in details or \'magasin\' in message.lower(),\n                        \'le refus doit designer le magasin : %s\' % reponse.content[:300])\n\n    def test_3_caisse_ne_peut_pas_viser_le_magasin_d_une_autre_entreprise(self):\n        """Creation d\'une caisse sur le magasin d\'une autre entreprise : refus."""\n        reponse = self.client_b.post(\'/api/v1/registers/\', {\n            \'store\': str(self.store_a.id),       # magasin de l\'entreprise A\n            \'name\': \'Caisse Beta\',\n            \'code\': \'REG-B1\',\n        }, format=\'json\')\n        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST, reponse.content[:300])\n\n    def test_4_parcours_normal_creation_ouverture_vente(self):\n        """Creer la caisse sur son magasin, l\'ouvrir, vendre, retrouver la vente."""\n        creation = self.client_a.post(\'/api/v1/registers/\', {\n            \'store\': str(self.store_a.id),\n            \'name\': \'Caisse Comptoir Principal\',\n            \'code\': \'REG-A1\',\n        }, format=\'json\')\n        self.assertEqual(creation.status_code, status.HTTP_201_CREATED, creation.content[:300])\n        caisse = creation.data[\'id\']\n\n        ouverture = self.client_a.post(\n            f\'/api/v1/registers/{caisse}/open_session/\',\n            {\'opening_balance\': 0}, format=\'json\')\n        self.assertIn(ouverture.status_code, (status.HTTP_200_OK, status.HTTP_201_CREATED),\n                      ouverture.content[:300])\n\n        # Le POS corrige n\'envoie QUE la caisse : le serveur en deduit le magasin.\n        vente = self.client_a.post(\'/api/v1/sales/\', {\n            \'register\': caisse,\n            \'items\': [{\'product\': str(self.product_a1.id), \'quantity\': Decimal(\'2.00\'),\n                       \'unit_price\': Decimal(\'800.00\'), \'tax_rate\': Decimal(\'20.00\')}],\n            \'payment\': {\'amount\': \'1920.00\', \'method\': \'CASH\', \'reference\': \'POS-PAY-000003\'},\n        }, format=\'json\')\n        self.assertEqual(vente.status_code, status.HTTP_201_CREATED, vente.content[:300])\n        self.assertEqual(str(vente.data[\'store\']), str(self.store_a.id),\n                         \'la vente doit porter le magasin de sa caisse\')\n        self.assertEqual(Decimal(vente.data[\'total_amount\']), Decimal(\'1920.00\'))\n\n        liste = self.client_a.get(\'/api/v1/sales/\', {\'page\': 1})\n        self.assertEqual(liste.status_code, status.HTTP_200_OK)\n        self.assertIn(vente.data[\'reference\'],\n                      [ligne[\'reference\'] for ligne in liste.data[\'results\']])\n\n    def test_5_caisse_hors_magasin_refusee_avec_un_message_precis(self):\n        """Magasin et caisse fournis mais incoherents : refus explicite."""\n        creation = self.client_a.post(\'/api/v1/registers/\', {\n            \'store\': str(self.store_a.id), \'name\': \'Caisse Comptoir\', \'code\': \'REG-A2\',\n        }, format=\'json\')\n        self.assertEqual(creation.status_code, status.HTTP_201_CREATED, creation.content[:300])\n\n        from apps.inventory.models import StockMovementType, Store\n        from apps.inventory.services import StockService\n        magasin_bis = Store.objects.create(company=self.company_a, name=\'Annexe\', code=\'MAG-A2\')\n        StockService.record_movement(\n            company=self.company_a, store=magasin_bis, product=self.product_a1,\n            quantity=Decimal(\'10.00\'), movement_type=StockMovementType.INITIAL,\n            reference=\'INIT-ANNEXE\', reason=\'Stock initial annexe\')\n        reponse = self.client_a.post(\'/api/v1/sales/\', {\n            \'store\': str(magasin_bis.id),\n            \'register\': creation.data[\'id\'],      # caisse du premier magasin\n            \'items\': [{\'product\': str(self.product_a1.id), \'quantity\': Decimal(\'1.00\'),\n                       \'unit_price\': Decimal(\'800.00\'), \'tax_rate\': Decimal(\'20.00\')}],\n            \'payment\': {\'amount\': \'944.00\', \'method\': \'CASH\', \'reference\': \'POS-PAY-000004\'},\n        }, format=\'json\')\n        self.assertEqual(reponse.status_code, status.HTTP_400_BAD_REQUEST, reponse.content[:300])\n        self.assertEqual(reponse.data.get(\'error\'), "La caisse choisie n\'appartient pas a ce magasin")\n\n    def test_6_la_liste_des_caisses_reste_dans_l_entreprise(self):\n        """L\'entreprise A ne voit jamais les caisses de l\'entreprise B."""\n        self.client_b.post(\'/api/v1/registers/\', {\n            \'store\': str(self.store_b.id), \'name\': \'Caisse Beta\', \'code\': \'REG-B2\',\n        }, format=\'json\')\n        reponse = self.client_a.get(\'/api/v1/registers/\')\n        self.assertEqual(reponse.status_code, status.HTTP_200_OK)\n        codes = [c[\'code\'] for c in reponse.data[\'results\']]\n        self.assertNotIn(\'REG-B2\', codes)\n'


def _mettre_a_jour_mon_fichier(racine, chemin, texte_voulu, marqueur, description):
    """Ecrit un fichier installe par ce correcteur, sans jamais ecraser le votre.

    - fichier absent           -> on l'installe ;
    - identique                -> rien a faire ;
    - different mais marque    -> c'est une version precedente de CE correcteur :
                                  on la conserve en .ancien et on met a jour ;
    - different sans marque    -> c'est votre fichier : on n'y touche pas.
    """
    if not chemin.exists():
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(texte_voulu, encoding='utf-8')
        return '%s installe' % description, True
    contenu = chemin.read_text(encoding='utf-8', errors='replace')
    if contenu == texte_voulu:
        return 'deja installe', False
    if marqueur not in contenu:
        return ('fichier existant different (le votre) : conserve tel quel'), False
    ancien_chemin = racine / DOSSIER_SAUVEGARDE / (str(chemin.relative_to(racine)) + '.ancien')
    ancien_chemin.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(chemin, ancien_chemin)
    chemin.write_text(texte_voulu, encoding='utf-8')
    return '%s mis a jour (ancienne version en .ancien)' % description, True


def installer_test(racine):
    """Installe (ou met a jour) le test des caisses."""
    if not (racine / 'tests').is_dir():
        return 'dossier tests absent : test non installe', False
    return _mettre_a_jour_mon_fichier(
        racine, racine / FICHIER_TEST, TEST_TEXTE, 'CaissePosMagasinTests',
        'test tests/test_caisse_pos_magasin.py')


MOTIF_STORE_VENTE = re.compile(
    r'^(?P<indent>[ \t]*)store[ \t]*=[ \t]*serializers\.[A-Za-z_]+Field\([^\n]*\)[ \t]*$', re.M)


def _bloc_classe(texte, nom):
    """Etendue d'une classe : de « class nom » a la classe suivante."""
    position = texte.find('class %s' % nom)
    if position == -1:
        return None
    suivant = texte.find('\nclass ', position)
    return position, (suivant if suivant != -1 else len(texte))


def corriger_serialiseur_vente(racine):
    """Ventes : le magasin peut etre deduit de la caisse.

    La ligne du champ est cherchee DANS la classe d'entree des ventes, quelle
    que soit sa forme exacte (UUIDField, CharField, avec ou sans arguments) :
    un arbre reel peut differer d'une version a l'autre.
    """
    chemin = racine / FICHIER_SERIALISEUR_VENTE
    if not chemin.exists():
        return 'fichier absent', False
    texte, retours, bom = lire_fichier(chemin)

    bloc = _bloc_classe(texte, 'SaleCreateInputSerializer')
    if bloc is None:
        return 'classe SaleCreateInputSerializer introuvable : fichier non modifie', False
    debut, fin = bloc
    morceau = texte[debut:fin]

    if 'store = serializers.UUIDField(required=False, allow_null=True)' in morceau:
        return 'deja corrige', False

    correspondance = MOTIF_STORE_VENTE.search(morceau)
    if not correspondance:
        apercu = ' | '.join(ligne.strip() for ligne in morceau.split('\n')[:12] if ligne.strip())
        return ('ligne « store = serializers... » introuvable dans '
                'SaleCreateInputSerializer. Vu : %s' % apercu[:400]), False

    indentation = correspondance.group('indent')
    lignes_nouvelles = [
        "# Le magasin n'est plus obligatoire : s'il est absent, le serveur le",
        "# deduit de la caisse (une vente ne peut donc pas porter un autre",
        "# magasin que celui de sa caisse).",
        "store = serializers.UUIDField(required=False, allow_null=True)",
    ]
    remplacement = chr(10).join(indentation + ligne for ligne in lignes_nouvelles)
    morceau = morceau[:correspondance.start()] + remplacement + morceau[correspondance.end():]
    texte = texte[:debut] + morceau + texte[fin:]

    ok, message = equilibre(texte)
    if not ok:
        return 'ANNULE : %s' % message, False
    ecrire_fichier(chemin, texte, retours, bom)
    return 'magasin deduisible de la caisse', True


ANCRE_MAGASIN_AUTO = """        if not store:
            # Aucun magasin precise : comportement d'origine (premier magasin).
            store = Store.objects.filter(company=company).first()"""
REMPLACEMENT_MAGASIN_AUTO = """        if not store:
            # Aucun magasin precise : celui de la caisse fait foi, sinon
            # comportement d'origine (premier magasin). Sans cela, une vente
            # pouvait etre rattachee a un autre magasin que celui de sa caisse.
            caisse_du_payload = None
            caisse_val = data.get('register')
            caisse_uuid = parse_safe_uuid(caisse_val)
            if caisse_uuid:
                caisse_du_payload = CashRegister.objects.filter(
                    id=caisse_uuid, company=company).select_related('store').first()
            elif caisse_val:
                caisse_du_payload = CashRegister.objects.filter(
                    company=company, code__iexact=str(caisse_val).strip()).select_related('store').first()
            store = (caisse_du_payload.store if caisse_du_payload else None) or Store.objects.filter(company=company).first()"""

ANCRE_CAISSE_AUTO = """        if not register:
            # Aucune caisse precise : comportement d'origine (premiere caisse).
            register = CashRegister.objects.filter(company=company).first()"""
REMPLACEMENT_CAISSE_AUTO = """        if not register:
            # Aucune caisse precise : comportement d'origine (premiere caisse).
            register = CashRegister.objects.filter(company=company).first()
        if store and register and register.store_id != store.id:
            # Le magasin et la caisse ne vont pas ensemble : on le dit, au lieu
            # de laisser partir une vente incoherente (rapport Z et cloture
            # d'une caisse, magasin d'une autre).
            return Response(
                {'error': "La caisse choisie n'appartient pas a ce magasin"},
                status=status.HTTP_400_BAD_REQUEST)"""

def corriger_ventes_magasin(racine):
    """Ventes : magasin deduit de la caisse, et coherence verifiee."""
    chemin = racine / FICHIER_VENTES
    if not chemin.exists():
        return 'fichier absent', False
    texte, retours, bom = lire_fichier(chemin)
    if 'caisse_du_payload' in texte and "n'appartient pas a ce magasin" in texte:
        return 'deja corrige', False
    texte, fait1 = remplacer(texte, ANCRE_MAGASIN_AUTO, REMPLACEMENT_MAGASIN_AUTO)
    texte, fait2 = remplacer(texte, ANCRE_CAISSE_AUTO, REMPLACEMENT_CAISSE_AUTO)
    if not (fait1 and fait2):
        return 'ancres introuvables (%s%s) : fichier non modifie' % (fait1, fait2), False
    ok, message = equilibre(texte)
    if not ok:
        return 'ANNULE : %s' % message, False
    ecrire_fichier(chemin, texte, retours, bom)
    return 'magasin deduit de la caisse, coherence verifiee', True

BLOC_BACKEND_TEMOIN = """        read_only_fields = ['id', 'company', 'status', 'current_cashier', 'current_balance', 'created_at']"""

BLOC_BACKEND_AJOUT = """        read_only_fields = ['id', 'company', 'status', 'current_cashier', 'current_balance', 'created_at']

    def validate_store(self, magasin):
        # Une caisse doit etre rattachee a un magasin de SON entreprise.
        # Sans ce controle, une caisse pouvait viser le magasin d'une autre
        # entreprise : chaque vente passait alors ce magasin etranger au
        # serveur, qui la refusait (« Magasin introuvable dans votre
        # entreprise »). La compagnie etant posee par la vue, elle n'est pas
        # encore connue ici : on retombe sur celle de l'utilisateur.
        utilisateur = getattr(self.context.get('request'), 'user', None)
        compagnie = getattr(utilisateur, 'company', None)
        if compagnie is None:
            compagnie = getattr(self.instance, 'company', None)
        if compagnie is not None and magasin.company_id != compagnie.id:
            raise serializers.ValidationError(
                'Ce magasin ne fait pas partie de votre entreprise.')
        return magasin"""

ANCIENNE_CAISSE = """  const activeRegister = registersData?.results?.[0] || {
    id: 'reg-01',
    name: 'Caisse Comptoir Principal',
    code: 'REG-01',
    status: 'OPEN',
    current_balance: '125000.00',
    store_name: 'Magasin & Dépôt Ouaga Central',
    store: 'store-01',
  };"""
NOUVELLE_CAISSE = """  // Plus de caisse inventee : une caisse doit exister reellement pour vendre.
  // (Avant, une caisse fictive « reg-01 » pointait vers un magasin fictif
  // « store-01 » : le serveur refusait alors chaque vente avec le message
  // « Magasin introuvable dans votre entreprise ».)
  const activeRegister = registersData?.results?.[0] || null;
  const caisseOuverte = !!activeRegister && activeRegister.status === 'OPEN';

  // Magasins de l'entreprise : necessaires pour creer la premiere caisse.
  const { data: storesData } = useQuery<PaginatedResponse<Store>>({
    queryKey: ['stores'],
    queryFn: () => apiRequest<PaginatedResponse<Store>>('/stores/'),
    staleTime: 1000 * 60,
  });

  const [isRegisterSetupOpen, setIsRegisterSetupOpen] = React.useState(false);
  const [registerSetupForm, setRegisterSetupForm] = React.useState({ name: '', code: '', store: '' });
  const [isCreatingStore, setIsCreatingStore] = React.useState(false);
  const [isCreatingRegister, setIsCreatingRegister] = React.useState(false);

  const handleCreateStore = async () => {
    setIsCreatingStore(true);
    try {
      const nom = window.prompt('Nom du magasin', 'Magasin principal');
      if (!nom) return;
      const code = window.prompt('Code du magasin', 'MAG-01');
      if (!code) return;
      const nouveauMagasin: any = await apiRequest('/stores/', {
        method: 'POST',
        body: JSON.stringify({ name: nom, code: code }),
      });
      queryClient.invalidateQueries({ queryKey: ['stores'] });
      setRegisterSetupForm((precedent) => ({ ...precedent, store: nouveauMagasin?.id || '' }));
      toast({ type: 'success', title: 'Magasin cree', message: nom + ' (' + code + ')' });
    } catch (erreur: any) {
      toast({
        type: 'error',
        title: 'Creation du magasin impossible',
        message: erreur?.message || 'Le magasin n\\'a pas ete enregistre.',
      });
    } finally {
      setIsCreatingStore(false);
    }
  };

  const handleCreateRegister = async () => {
    if (!registerSetupForm.store) {
      toast({ type: 'error', title: 'Magasin requis',
              message: 'Choisissez le magasin qui abritera cette caisse.' });
      return;
    }
    setIsCreatingRegister(true);
    try {
      const caisse: any = await apiRequest('/registers/', {
        method: 'POST',
        body: JSON.stringify({
          store: registerSetupForm.store,
          name: registerSetupForm.name || 'Caisse Comptoir Principal',
          code: registerSetupForm.code || 'REG-01',
        }),
      });
      const caisseCreee = { ...caisse, status: 'OPEN' };
      // La caisse ouvre sa session : le fond de caisse est documente.
      try {
        await apiRequest(`/registers/${caisse.id}/open_session/`, {
          method: 'POST',
          body: JSON.stringify({ opening_balance: 0 }),
        });
      } catch (erreurSession: any) {
        toast({
          type: 'error',
          title: 'Caisse creee, ouverture de session a refaire',
          message: erreurSession?.message || 'Ouvrez la session de cette caisse.',
        });
      }
      queryClient.setQueryData(['registers'], { results: [caisseCreee], pagination: {} });
      await queryClient.invalidateQueries({ queryKey: ['registers'] });
      setIsRegisterSetupOpen(false);
      toast({
        type: 'success',
        title: 'Caisse prete',
        message: caisseCreee.name + ' (' + caisseCreee.code + ') est ouverte : vous pouvez vendre.',
      });
    } catch (erreur: any) {
      toast({
        type: 'error',
        title: 'Creation de la caisse impossible',
        message: erreur?.message || 'La caisse n\\'a pas ete enregistree.',
      });
    } finally {
      setIsCreatingRegister(false);
    }
  };"""

ECRAN_CAISSE = """
  // Sans caisse reelle (ou caisse fermee), la vente est impossible : on le dit
  // clairement, avec les deux raccourcis qui manquaient (magasin puis caisse).
  if (!caisseOuverte) {
    return (
      <DashboardLayout>
        <div className="max-w-2xl mx-auto space-y-4">
          <div className="bg-card border rounded-2xl p-6 shadow-xs space-y-4">
            <div className="flex items-start gap-3">
              <div className="p-2.5 rounded-xl bg-amber-500/15 text-amber-500">
                <StoreIcon className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-foreground">
                  {activeRegister ? 'Caisse fermee' : 'Aucune caisse enregistree'}
                </h2>
                <p className="text-sm text-muted-foreground">
                  {activeRegister
                    ? 'La caisse « ' + activeRegister.name + ' » est fermee. Ouvrez sa session depuis le bouton ci-dessous pour encaisser.'
                    : 'Les ventes ne peuvent pas etre enregistrees sans caisse : le serveur refuse une vente dont le magasin n\\'existe pas. Creez le magasin, puis la caisse.'}
                </p>
              </div>
            </div>

            <div className="text-sm space-y-1">
              <p>
                Magasins de votre entreprise :{' '}
                <span className="font-semibold">{storesData?.results?.length || 0}</span>
              </p>
              <p>
                Caisses de votre entreprise :{' '}
                <span className="font-semibold">{registersData?.results?.length || 0}</span>
                {activeRegister ? ' (fermee : fond ' + formatCurrency(activeRegister.current_balance) + ')' : ''}
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleCreateStore}
                isLoading={isCreatingStore}
              >
                Creer un magasin
              </Button>
              {activeRegister ? (
                <Button
                  type="button"
                  onClick={() => {
                    setClosingCashAmount(activeRegister.current_balance);
                    setIsCloseRegisterModalOpen(true);
                  }}
                >
                  Ouvrir la session de cette caisse
                </Button>
              ) : (
                <Button
                  type="button"
                  onClick={() => {
                    const premierMagasin: any = storesData?.results?.[0];
                    setRegisterSetupForm((precedent) => ({
                      ...precedent,
                      store: precedent.store || premierMagasin?.id || '',
                    }));
                    setIsRegisterSetupOpen(true);
                  }}
                >
                  Creer une caisse
                </Button>
              )}
              <Button
                type="button"
                variant="outline"
                onClick={() => queryClient.invalidateQueries({ queryKey: ['registers'] })}
              >
                Recharger la liste
              </Button>
            </div>
          </div>
        </div>

        <Modal
          isOpen={isRegisterSetupOpen}
          onClose={() => setIsRegisterSetupOpen(false)}
          title="Nouvelle caisse"
        >
          <div className="space-y-3">
            <label className="block text-sm">
              Magasin d'affectation
              <select
                className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
                value={registerSetupForm.store}
                onChange={(evenement) =>
                  setRegisterSetupForm((precedent) => ({ ...precedent, store: evenement.target.value }))
                }
              >
                <option value="">— choisir un magasin —</option>
                {(storesData?.results || []).map((magasin) => (
                  <option key={magasin.id} value={magasin.id}>
                    {magasin.name} ({magasin.code})
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm">
              Nom de la caisse
              <Input
                className="mt-1"
                value={registerSetupForm.name}
                onChange={(evenement) =>
                  setRegisterSetupForm((precedent) => ({ ...precedent, name: evenement.target.value }))
                }
                placeholder="Caisse Comptoir Principal"
              />
            </label>
            <label className="block text-sm">
              Code de la caisse
              <Input
                className="mt-1"
                value={registerSetupForm.code}
                onChange={(evenement) =>
                  setRegisterSetupForm((precedent) => ({ ...precedent, code: evenement.target.value }))
                }
                placeholder="REG-01"
              />
            </label>
            {!storesData?.results?.length && (
              <p className="text-xs text-amber-500">
                Aucun magasin pour l'instant : cliquez d'abord sur « Creer un magasin ».
              </p>
            )}
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setIsRegisterSetupOpen(false)}>
                Annuler
              </Button>
              <Button type="button" onClick={handleCreateRegister} isLoading={isCreatingRegister}>
                Creer et ouvrir la caisse
              </Button>
            </div>
          </div>
        </Modal>
      </DashboardLayout>
    );
  }
"""

ANCIEN_TICKET = """    onSuccess: (data: any) => {
      const saleDetails = {
        ...data,"""
NOUVEAU_TICKET = """    onSuccess: (data: any) => {
      const saleDetails = {"""
# --------------------------------------------------------------- outils de code

def lire_fichier(chemin):
    """Lit un fichier en ramenant les fins de ligne a \n.

    Retourne (texte, retours_crlf, bom). Les fichiers d'un projet Windows sont
    souvent en CRLF : sans cette normalisation, aucune ancre ne correspondrait.
    """
    donnees = chemin.read_bytes()
    bom = donnees.startswith(b'\xef\xbb\xbf')
    texte = donnees.decode('utf-8-sig')
    n_crlf = texte.count('\r\n')
    n_lf = texte.count('\n') - n_crlf
    return texte.replace('\r\n', '\n'), n_crlf > n_lf, bom


def ecrire_fichier(chemin, texte, crlf=False, bom=False):
    """Reecrit le fichier en conservant ses fins de ligne et son BOM d'origine."""
    sortie = texte.replace('\n', '\r\n') if crlf else texte
    donnees = sortie.encode('utf-8')
    if bom:
        donnees = b'\xef\xbb\xbf' + donnees
    chemin.write_bytes(donnees)


def _debut_de_chaine(texte, i):
    """Vrai si le guillemet a la position i ouvre une chaine de code.

    En JSX, l'apostrophe du texte francais (n'a, l'Encaissement, d'un) ne doit
    pas etre prise pour un guillemet : sinon l'analyse avale tout le fichier.
    Regle : une apostrophe precedee d'une lettre ou d'un chiffre est du texte.
    """
    if i == 0:
        return True
    return not texte[i - 1].isalnum()


def _fin_bloc(texte, index_accolade):
    """Index de l'accolade fermante correspondante (chaines/commentaires ignores)."""
    profondeur = 0
    i = index_accolade
    n = len(texte)
    while i < n:
        c = texte[i]
        if c in '\'"`' and _debut_de_chaine(texte, i):
            quote = c
            i += 1
            while i < n:
                if texte[i] == '\\':
                    i += 2
                    continue
                if texte[i] == quote:
                    break
                i += 1
        elif c == '/' and i + 1 < n and texte[i + 1] == '/':
            while i < n and texte[i] != '\n':
                i += 1
            continue
        elif c == '/' and i + 1 < n and texte[i + 1] == '*':
            fin = texte.find('*/', i + 2)
            i = (fin + 2) if fin != -1 else n
            continue
        elif c == '{':
            profondeur += 1
        elif c == '}':
            profondeur -= 1
            if profondeur == 0:
                return i
        i += 1
    return -1


def supprimer_propriete(texte, nom):
    """Supprime les blocs `nom: { ... },` (chaines et commentaires respectes)."""
    supprimees = 0
    while True:
        marqueur = '%s:' % nom
        position = texte.find(marqueur)
        if position == -1:
            break
        accolade = texte.find('{', position + len(marqueur))
        if accolade == -1:
            break
        fin = _fin_bloc(texte, accolade)
        if fin == -1:
            break
        debut_ligne = texte.rfind('\n', 0, position) + 1
        apres = fin + 1
        while apres < len(texte) and texte[apres] in ' \t':
            apres += 1
        if apres < len(texte) and texte[apres] == ',':
            apres += 1
        while apres < len(texte) and texte[apres] in ' \t':
            apres += 1
        if apres < len(texte) and texte[apres] == '\n':
            apres += 1
        texte = texte[:debut_ligne] + texte[apres:]
        supprimees += 1
    return texte, supprimees


def equilibre(texte):
    """Equilibre de (), {} et [] hors chaines et commentaires."""
    piles = []
    paires = {')': '(', '}': '{', ']': '['}
    i, n = 0, len(texte)
    while i < n:
        c = texte[i]
        if c in '\'"`' and _debut_de_chaine(texte, i):
            quote = c
            i += 1
            while i < n:
                if texte[i] == '\\':
                    i += 2
                    continue
                if texte[i] == quote:
                    break
                i += 1
        elif c == '/' and i + 1 < n and texte[i + 1] == '/':
            while i < n and texte[i] != '\n':
                i += 1
            continue
        elif c == '/' and i + 1 < n and texte[i + 1] == '*':
            fin = texte.find('*/', i + 2)
            i = (fin + 2) if fin != -1 else n
            continue
        elif c in '({[':
            piles.append(c)
        elif c in ')}]':
            if not piles or piles[-1] != paires[c]:
                return False, 'fermeture inattendue « %s »' % c
            piles.pop()
        i += 1
    if piles:
        return False, 'ouverts non fermes : %s' % ''.join(piles)
    return True, 'equilibre'


def remplacer(texte, avant, apres):
    """Remplacement exact, une seule fois. Retourne (texte, fait)."""
    if texte.count(avant) == 1:
        return texte.replace(avant, apres, 1), True
    return texte, False


def remplacer_entre(texte, debut, fin, remplacement):
    """Remplace tout ce qui va du debut a la fin (incluses). Retourne (texte, fait)."""
    try:
        i = texte.index(debut)
        j = texte.index(fin, i) + len(fin)
    except ValueError:
        return texte, False
    return texte[:i] + remplacement + texte[j:], True



# ------------------------------------------------------------------- patchs

def corriger_serialiseur_caisse(racine):
    """Serveur : une caisse ne peut viser que le magasin de son entreprise."""
    chemin = racine / FICHIER_SERIALISEUR
    if not chemin.exists():
        return 'fichier absent', False
    texte, retours, bom = lire_fichier(chemin)
    if 'def validate_store' in texte:
        return 'deja verrouille', False
    # le champ store doit etre immuable : sinon on peut creer la caisse sur son
    # magasin puis la rattacher au magasin d'une autre entreprise
    if "read_only_fields = ['id', 'company', 'status', 'current_cashier'," in texte:
        texte, fait1 = remplacer(texte, BLOC_BACKEND_TEMOIN, BLOC_BACKEND_AJOUT)
    else:
        fait1 = False
    if not fait1:
        return 'ancres introuvables : fichier non modifie', False
    ok, message = equilibre(texte)
    if not ok:
        return 'ANNULE : %s' % message, False
    ecrire_fichier(chemin, texte, retours, bom)
    return 'magasin de la caisse verrouille', True


ANCRE_FIN_CREATION = """      setIsCreatingRegister(false);
    }
  };"""

HANDLER_OUVERTURE = "\n  // Ouvrir reellement la session d'une caisse fermee (l'ecran precedent\n  // appelait la fermeture : le bouton « Ouvrir la session » ne l'ouvrait pas).\n  const handleOpenRegister = async () => {\n    if (!activeRegister) return;\n    try {\n      const fond = window.prompt('Fond de caisse a l\\'ouverture (en FCFA)', '0');\n      if (fond === null) return;\n      await apiRequest(`/registers/${activeRegister.id}/open_session/`, {\n        method: 'POST',\n        body: JSON.stringify({ opening_balance: Number(fond) || 0 }),\n      });\n      queryClient.setQueryData(['registers'], {\n        results: [{ ...activeRegister, status: 'OPEN' }],\n        pagination: {},\n      });\n      await queryClient.invalidateQueries({ queryKey: ['registers'] });\n      toast({\n        type: 'success',\n        title: 'Session ouverte',\n        message: activeRegister.name + ' est prete a encaisser.',\n      });\n    } catch (erreur: any) {\n      toast({\n        type: 'error',\n        title: 'Ouverture impossible',\n        message: erreur?.message || 'La session n\\'a pas ete ouverte.',\n      });\n    }\n  };\n"

ANCIEN_BOUTON_OUVERTURE = """              {activeRegister ? (
                <Button
                  type="button"
                  onClick={() => {
                    setClosingCashAmount(activeRegister.current_balance);
                    setIsCloseRegisterModalOpen(true);
                  }}
                >
                  Ouvrir la session de cette caisse
                </Button>
              ) : ("""

NOUVEAU_BOUTON_OUVERTURE = """              {activeRegister ? (
                <Button type="button" onClick={handleOpenRegister}>
                  Ouvrir la session de cette caisse
                </Button>
              ) : ("""


def _mettre_a_niveau_ouverture(texte):
    """Installe l'ouverture de session reelle (caisse fermee)."""
    fait = False
    if 'handleOpenRegister' not in texte:
        texte, insere = remplacer(texte, ANCRE_FIN_CREATION,
                                  ANCRE_FIN_CREATION + '\n' + HANDLER_OUVERTURE)
        fait = fait or insere
    if ANCIEN_BOUTON_OUVERTURE in texte:
        texte, remplace = remplacer(texte, ANCIEN_BOUTON_OUVERTURE, NOUVEAU_BOUTON_OUVERTURE)
        fait = fait or remplace
    return texte, fait


def corriger_pos_caisse(racine):
    """POS : plus de caisse inventee, ecran clair, ouverture de session reelle."""
    chemin = racine / FICHIER_POS
    if not chemin.exists():
        return 'fichier absent', False
    texte, retours, bom = lire_fichier(chemin)

    if ANCIENNE_CAISSE not in texte:
        # Caisse fictive deja retiree (ou arbre different) : on ne remplace
        # plus rien, on met seulement l'ouverture de session a niveau.
        if 'Aucune caisse enregistree' not in texte:
            return ('etat inconnu : ni caisse fictive ni ecran d installation '
                    '(fichier non modifie)'), False
        texte, fait_ouverture = _mettre_a_niveau_ouverture(texte)
        if not fait_ouverture:
            return 'deja corrige', False
        ok, message = equilibre(texte)
        if not ok:
            return 'ANNULE : %s' % message, False
        ecrire_fichier(chemin, texte, retours, bom)
        return 'ouverture de session mise a niveau (caisse fermee)', True

    # 1) remplacer la caisse inventee par une vraie lecture + outils d'installation
    texte, fait1 = remplacer(texte, ANCIENNE_CAISSE, NOUVELLE_CAISSE)
    # 2) retirer la ligne « store: activeRegister.store » : store et register
    #    designent le meme magasin, et un doublon inutile a deja provoque
    #    l'erreur « Magasin introuvable dans votre entreprise »
    if fait1:
        texte, _ = remplacer(texte, "        store: activeRegister.store,\n", "")
    # 3) ecran d'installation avant le POS (caisse absente ou fermee)
    if fait1:
        texte, fait2 = remplacer(texte, "\n  return (\n    <DashboardLayout>",
                                 ECRAN_CAISSE + "\n  return (\n    <DashboardLayout>")
    else:
        fait2 = False
    # 4) en cas d'echec du serveur, l'utilisateur voit le message exact
    if fait2:
        texte, fait3 = remplacer(texte, ANCIEN_TICKET, NOUVEAU_TICKET)
        texte, fait4 = remplacer(texte, "      setCompletedSale(saleDetails);",
                                 "      setCompletedSale({ ...saleDetails, saveError: true });")
    else:
        fait3, fait4 = False, False
    # 5) l'import du type Store (magasins) pour l'ecran d'installation
    texte, fait5 = remplacer(texte,
        "import { Product, CashRegister, Partner, PaginatedResponse } from '@/types';",
        "import { Product, CashRegister, Partner, Store, PaginatedResponse } from '@/types';")
    # 6) ouverture de session reelle quand la caisse est fermee
    if fait1 and fait2:
        texte, _ = _mettre_a_niveau_ouverture(texte)

    if not (fait1 and fait2 and fait3 and fait4 and fait5):
        return 'ancres introuvables (%s%s%s%s%s) : fichier non modifie' % (
            fait1, fait2, fait3, fait4, fait5), False
    ok, message = equilibre(texte)
    if not ok:
        return 'ANNULE : %s' % message, False
    ecrire_fichier(chemin, texte, retours, bom)
    return 'caisse inventee retiree, ecran d installation ajoute', True


# -------------------------------------------------------------- sauvegardes

def sauvegarder(racine, relatif):
    chemin = racine / relatif
    if not chemin.exists():
        return
    cible = racine / DOSSIER_SAUVEGARDE / relatif
    if cible.exists():
        return
    cible.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(chemin, cible)


# -------------------------------------------------------------- verification

def verifier(racine):
    resultats = []

    def lire(relatif):
        chemin = racine / relatif
        if not chemin.exists():
            return None
        return lire_fichier(chemin)[0]

    texte = lire(FICHIER_SERIALISEUR)
    if texte is None:
        resultats.append(('ABSENT', str(FICHIER_SERIALISEUR)))
    else:
        if 'def validate_store' in texte:
            resultats.append(('OK', 'serialiseur : magasin de la caisse verrouille'))
        else:
            resultats.append(('A FAIRE', 'serialiseur : caisse encore rattachable a un magasin etranger'))
        resultats.append(('OK' if equilibre(texte)[0] else 'A FAIRE', 'serialiseur : equilibre'))

    texte = lire(FICHIER_SERIALISEUR_VENTE)
    if texte is None:
        resultats.append(('ABSENT', str(FICHIER_SERIALISEUR_VENTE)))
    else:
        bloc = _bloc_classe(texte, 'SaleCreateInputSerializer')
        morceau = texte[bloc[0]:bloc[1]] if bloc else ''
        if 'store = serializers.UUIDField(required=False, allow_null=True)' in morceau:
            resultats.append(('OK', 'vente (entree) : magasin optionnel (deduit de la caisse)'))
        else:
            resultats.append(('A FAIRE', 'vente (entree) : magasin toujours obligatoire'))
        resultats.append(('OK' if equilibre(texte)[0] else 'A FAIRE', 'vente (entree) : equilibre'))

    texte = lire(FICHIER_VENTES)
    if texte is None:
        resultats.append(('ABSENT', str(FICHIER_VENTES)))
    else:
        if 'caisse_du_payload' in texte:
            resultats.append(('OK', 'ventes : magasin deduit de la caisse'))
        else:
            resultats.append(('A FAIRE', 'ventes : magasin encore deduit du premier magasin'))
        if "n'appartient pas a ce magasin" in texte:
            resultats.append(('OK', 'ventes : caisse hors magasin refusee avec message precis'))
        else:
            resultats.append(('A FAIRE', 'ventes : incoherence caisse/magasin non detectee'))
        resultats.append(('OK' if equilibre(texte)[0] else 'A FAIRE', 'ventes : equilibre'))

    if (racine / FICHIER_TEST).exists():
        resultats.append(('OK', 'test : py manage.py test tests.test_caisse_pos_magasin'))
    else:
        resultats.append(('A FAIRE', 'fichier de test absent'))

    if (racine / COMMANDE_DIAGNOSTIC).exists():
        resultats.append(('OK', 'outil : py manage.py diagnostiquer_caisses'))
    else:
        resultats.append(('A FAIRE', 'outil de diagnostic absent'))

    texte = lire(FICHIER_POS)
    if texte is None:
        resultats.append(('ABSENT', str(FICHIER_POS)))
    else:
        if "'reg-01'" in texte or "id: 'reg-01'" in texte:
            resultats.append(('A FAIRE', 'POS : caisse inventee encore presente'))
        else:
            resultats.append(('OK', 'POS : plus aucune caisse inventee'))
        if 'Aucune caisse enregistree' in texte and 'Creer une caisse' in texte:
            resultats.append(('OK', 'POS : ecran de creation de caisse (magasin puis caisse)'))
        else:
            resultats.append(('A FAIRE', 'POS : aucun ecran de creation de caisse'))
        if 'store: activeRegister.store' in texte:
            resultats.append(('A FAIRE', 'POS : magasin duplique dans l envoi de vente'))
        else:
            resultats.append(('OK', 'POS : vente envoyee avec la seule caisse (magasin deduit)'))
        if 'handleOpenRegister' in texte:
            resultats.append(('OK', 'POS : ouverture de session d une caisse fermee operationnelle'))
        else:
            resultats.append(('A FAIRE', 'POS : bouton « Ouvrir la session » sans action d ouverture'))
        if 'saveError' in texte:
            resultats.append(('OK', 'POS : echec d enregistrement affiche sur le ticket'))
        else:
            resultats.append(('A FAIRE', 'POS : echec d enregistrement encore silencieux'))
        if 'export-seller-pdf' in texte:
            resultats.append(('OK', 'POS : bilan vendeur (v3.1) intact'))
        else:
            resultats.append(('ATTENTION', 'POS : bilan vendeur introuvable'))
        ok, message = equilibre(texte)
        resultats.append(('OK' if ok else 'A FAIRE', 'POS : %s' % message))

    return resultats


def resume(racine):
    resultats = verifier(racine)
    bloquants = 0
    print('')
    print('ETAT DES CAISSES NEXORA')
    print('=' * 74)
    for etat, description in resultats:
        print('  [%s] %s' % (etat, description))
        if etat in ('A FAIRE', 'ABSENT') and 'bilan vendeur' not in description:
            bloquants += 1
    print('=' * 74)
    return bloquants


# ------------------------------------------------------------------ principal

def main():
    analyseur = argparse.ArgumentParser(
        description='NEXORA : caisse rattachee au bon magasin (message « Magasin introuvable »).')
    analyseur.add_argument('--racine', default='.',
                           help='dossier du projet (celui qui contient manage.py)')
    analyseur.add_argument('--verifier', action='store_true',
                           help='fait le point sans rien modifier')
    arguments = analyseur.parse_args()

    racine = Path(arguments.racine).expanduser().resolve()
    if not (racine / 'manage.py').exists() or not (racine / FICHIER_POS).is_file():
        print('Dossier invalide : %s' % racine)
        print('Indiquez la racine du projet (elle doit contenir manage.py et frontend/src).')
        print('Exemple : py %s --racine D:\\NEXORA' % Path(__file__).name)
        return 2

    print('NEXORA : caisse rattachee au bon magasin')
    print('Racine : %s' % racine)
    print('')

    if arguments.verifier:
        problemes = resume(racine)
        if problemes:
            print('Des corrections restent a faire : relancez sans --verifier.')
            return 1
        print('Tout est en place : la caisse ne peut plus viser un magasin etranger.')
        return 0

    for relatif in (FICHIER_SERIALISEUR, FICHIER_SERIALISEUR_VENTE, FICHIER_VENTES, FICHIER_POS):
        sauvegarder(racine, relatif)

    corrections = [
        ('Magasin de la caisse (serveur)', str(FICHIER_SERIALISEUR), corriger_serialiseur_caisse(racine)),
        ('Outil de diagnostic', str(COMMANDE_DIAGNOSTIC), installer_diagnostic(racine)),
        ('Test des caisses', str(FICHIER_TEST), installer_test(racine)),
        ('Entree de vente (serveur)', str(FICHIER_SERIALISEUR_VENTE), corriger_serialiseur_vente(racine)),
        ('Magasin de la vente (serveur)', str(FICHIER_VENTES), corriger_ventes_magasin(racine)),
        ('Caisse et magasin (caisse)', str(FICHIER_POS), corriger_pos_caisse(racine)),
    ]

    print('CORRECTIONS APPLIQUEES')
    print('-' * 74)
    for titre, fichier, (etat, fait) in corrections:
        if fait:
            symbole = 'CORRIGE'
        elif 'deja' in etat:
            symbole = 'DEJA OK'
        else:
            symbole = 'ATTENTION'
        print('  [%-9s] %-28s %s' % (symbole, fichier, etat))

    print('')
    print('Originaux conserves dans : %s/' % DOSSIER_SAUVEGARDE)
    problemes = resume(racine)
    print('')
    if problemes:
        print('ATTENTION : %d point(s) a revoir (voir le tableau ci-dessus).' % problemes)
        return 1
    print('CORRECTION TERMINEE.')
    print('1. Redemarrez le backend pour que le controle serveur prenne effet.')
    print('2. Relancez le frontend (npm run dev), puis Ctrl+F5 dans le navigateur.')
    print('3. Caisse vide : l\'ecran propose « Creer un magasin » puis « Creer une caisse ».')
    print('4. Magasin et caisse en place : la vente s\'enregistre normalement.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
