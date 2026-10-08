#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vérification du backend corrigé, SANS Django (ORM simulé).

Ce harnais rejoue le comportement du bilan vendeur du POS en injectant de faux
modules Django / DRF / reportlab, puis exécute réellement la vue
SellerSalesReportPdfView jusqu'à la génération du PDF.

Il imite volontairement les pièges de Django :
  * filter() refuse un champ inexistant (FieldError) -> un champ « username »
    absent du modèle NEXORA fait échouer la vérification au lieu de passer
    inaperçu ;
  * un objet passé à filter() est remplacé par sa clé primaire ;
  * les objets reportlab acceptent tout appel (objets permissifs).

Usage :
    py outils/verifier_correctif.py
    py outils/verifier_correctif.py chemin/vers/pdf_seller_report.py
"""
from __future__ import annotations

import datetime
import os
import sys
import types
import uuid
from decimal import Decimal

DOSSIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHEMIN_DEFAUT = os.path.join(DOSSIER, 'fichiers', 'apps', 'sales', 'pdf_seller_report.py')
CHEMIN = sys.argv[1] if len(sys.argv) > 1 else CHEMIN_DEFAUT

MAINTENANT = datetime.datetime(2026, 10, 7, 12, 0, tzinfo=datetime.timezone.utc)
ENTREPRISE = 'ENT-1'
AUTRE = 'ENT-2'
VENDEUR1 = uuid.UUID('11111111-1111-1111-1111-111111111111')
VENDEUR2 = uuid.UUID('22222222-2222-2222-2222-222222222222')
AUTRE_USER = uuid.UUID('33333333-3333-3333-3333-333333333333')

CHAMPS_MODELE = {
    'User': {'id', 'company', 'email', 'first_name', 'last_name', 'role',
             'phone', 'is_active', 'date_joined'},
    'Sale': {'id', 'company', 'store', 'register', 'customer', 'seller', 'status',
             'payment_status', 'subtotal_amount', 'tax_amount', 'discount_amount',
             'total_amount', 'paid_amount', 'notes', 'reference', 'created_at',
             'updated_at'},
    'Company': {'id', 'name', 'slug'},
    'Store': {'id', 'company', 'name', 'code', 'logo', 'address', 'is_active'},
}

UTILISATEURS = [
    {'id': VENDEUR1, 'company': ENTREPRISE, 'email': 'august.nanema@nexora-bf.com',
     'first_name': 'August', 'last_name': 'NANEMA', 'role': 'CASHIER'},
    {'id': VENDEUR2, 'company': ENTREPRISE, 'email': 'vendeur.bobo@nexora-bf.com',
     'first_name': 'Awa', 'last_name': 'SAWADOGO', 'role': 'CASHIER'},
    {'id': AUTRE_USER, 'company': AUTRE, 'email': 'chef@autre.com',
     'first_name': 'Chef', 'last_name': 'Autre', 'role': 'ADMIN'},
]


def vente(identifiant, vendeur, statut, jours, montant, entreprise=ENTREPRISE):
    montant = Decimal(str(montant))
    return {
        'id': identifiant, 'company': entreprise, 'seller': vendeur, 'status': statut,
        'reference': 'POS-%03d' % identifiant, 'subtotal_amount': montant,
        'tax_amount': Decimal('0.00'), 'discount_amount': Decimal('0.00'),
        'total_amount': montant, 'paid_amount': montant, 'notes': '',
        'payment_status': 'PAID', 'status_label': 'Validée',
        'created_at': MAINTENANT - datetime.timedelta(days=jours),
        'store': None, 'customer': None, 'register': None,
    }


VENTES = [
    vente(1, VENDEUR1, 'COMPLETED', 5, 1000),
    vente(2, VENDEUR1, 'COMPLETED', 10, 2000),
    vente(3, VENDEUR2, 'COMPLETED', 3, 4000),
    vente(4, VENDEUR1, 'CANCELLED', 2, 9999),
    vente(5, VENDEUR2, 'DRAFT', 1, 5555),
    vente(6, None, 'COMPLETED', 4, 8000),
    vente(7, VENDEUR1, 'COMPLETED', 40, 6000),
    vente(8, VENDEUR1, 'COMPLETED', 6, 700, entreprise=AUTRE),
]


class FieldError(Exception):
    pass


class Meta:
    def __init__(self, champs):
        self._champs = champs

    def get_fields(self):
        return [types.SimpleNamespace(name=n) for n in sorted(self._champs)]


def _normaliser(valeur):
    if isinstance(valeur, dict):
        return valeur.get('id', valeur)
    if not isinstance(valeur, (str, int, uuid.UUID, type(None))):
        identifiant = getattr(valeur, 'id', None)
        if identifiant is None:
            identifiant = getattr(valeur, 'pk', None)
        if identifiant is not None:
            return identifiant
    return valeur


def _champ(cle):
    for suffixe in ('__iexact', '__icontains', '__gte', '__lte', '__exact'):
        if cle.endswith(suffixe):
            return cle[:-len(suffixe)], suffixe
    return cle, ''


class UtilisateurFactice(dict):
    @property
    def id(self):
        return self['id']

    @property
    def email(self):
        return self['email']

    def get_full_name(self):
        return ('%s %s' % (self.get('first_name', ''), self.get('last_name', ''))).strip()

    def get_role_display(self):
        return self.get('role', '')


class RelatedVide:
    def all(self):
        return []

    def exists(self):
        return False

    def count(self):
        return 0


class VenteFactice(dict):
    def __getattr__(self, nom):
        try:
            return self[nom]
        except KeyError:
            if nom in ('items', 'payments', 'returns'):
                return RelatedVide()
            return None

    @property
    def items(self):
        return RelatedVide()

    @property
    def payments(self):
        return RelatedVide()


def _envelopper(lignes, modele):
    if modele == 'User':
        return [UtilisateurFactice(ligne) for ligne in lignes]
    if modele == 'Sale':
        return [VenteFactice(ligne) for ligne in lignes]
    return list(lignes)


class QuerySet:
    def __init__(self, lignes, modele):
        self.lignes = _envelopper(lignes, modele)
        self.modele = modele

    def _verifier(self, criteres):
        connus = CHAMPS_MODELE[self.modele]
        for cle in criteres:
            champ, _ = _champ(cle)
            if champ not in connus:
                raise FieldError("Cannot resolve keyword '%s' into field." % champ)

    def filter(self, **criteres):
        self._verifier(criteres)
        criteres = {c: _normaliser(v) for c, v in criteres.items()}

        def garde(ligne):
            for cle, valeur in criteres.items():
                champ, suffixe = _champ(cle)
                reel = ligne.get(champ)
                if suffixe == '__iexact':
                    if str(reel if reel is not None else '').lower() != str(valeur).lower():
                        return False
                elif suffixe == '__icontains':
                    if str(valeur).lower() not in str(reel if reel is not None else '').lower():
                        return False
                elif suffixe == '__gte':
                    if not (reel is not None and reel >= valeur):
                        return False
                elif suffixe == '__lte':
                    if not (reel is not None and reel <= valeur):
                        return False
                else:
                    if reel != valeur:
                        return False
            return True

        return QuerySet([dict(l) for l in self.lignes if garde(l)], self.modele)

    def exclude(self, **criteres):
        self._verifier(criteres)
        criteres = {c: _normaliser(v) for c, v in criteres.items()}
        return QuerySet([dict(l) for l in self.lignes
                         if all(l.get(c) != v for c, v in criteres.items())], self.modele)

    def order_by(self, *a, **k):
        return self

    def prefetch_related(self, *a):
        return self

    def first(self):
        return self.lignes[0] if self.lignes else None

    def count(self):
        return len(self.lignes)

    def exists(self):
        return bool(self.lignes)

    def values_list(self, champ, flat=False):
        return [ligne.get(champ) for ligne in self.lignes]

    def __getitem__(self, index):
        if isinstance(index, slice):
            return QuerySet(self.lignes[index], self.modele)
        return self.lignes[index]

    def __iter__(self):
        return iter(self.lignes)


class Manager:
    def __init__(self, lignes, modele):
        self.lignes = lignes
        self.modele = modele

    def filter(self, **criteres):
        return QuerySet(self.lignes, self.modele).filter(**criteres)

    def exclude(self, **criteres):
        return QuerySet(self.lignes, self.modele).exclude(**criteres)

    def all(self):
        return QuerySet(self.lignes, self.modele)

    def first(self):
        return self.lignes[0] if self.lignes else None


class ObjetPdf:
    def __getattr__(self, nom):
        return lambda *a, **k: None

    def __call__(self, *a, **k):
        return None


def installer_modules():
    modules = {}

    def module(nom):
        if nom not in modules:
            modules[nom] = types.ModuleType(nom)
            sys.modules[nom] = modules[nom]
        return modules[nom]

    module('django')
    module('django.utils')
    module('django.conf').settings = types.SimpleNamespace(USE_TZ=True, TIME_ZONE='UTC')
    zone = module('django.utils.timezone')
    zone.now = lambda: MAINTENANT
    zone.make_aware = (lambda valeur, tz=None: valeur.replace(tzinfo=datetime.timezone.utc)
                       if valeur.tzinfo is None else valeur)
    zone.timedelta = datetime.timedelta
    module('django.db')
    module('django.db.models')

    reponse = module('django.http')

    class HttpResponse:
        def __init__(self, contenu=b'', status=200, content_type='text/html; charset=utf-8'):
            self.content = contenu if isinstance(contenu, bytes) else str(contenu).encode('utf-8')
            self.status_code = status
            self.headers = {'Content-Type': content_type}

        def __setitem__(self, nom, valeur):
            self.headers[nom] = valeur

        def __getitem__(self, nom):
            return self.headers[nom]

        def get(self, nom, defaut=None):
            return self.headers.get(nom, defaut)

    reponse.HttpResponse = HttpResponse

    module('rest_framework')
    drf_views = module('rest_framework.views')

    class APIView:
        pass

    drf_views.APIView = APIView
    module('rest_framework.permissions').AllowAny = object
    module('rest_framework.response')

    module('reportlab')
    reportlab_lib = module('reportlab.lib')
    colors = module('reportlab.lib.colors')
    for nom in ('HexColor', 'white'):
        setattr(colors, nom, lambda *a, **k: ObjetPdf())
    reportlab_lib.colors = colors
    pagesizes = module('reportlab.lib.pagesizes')
    pagesizes.A4 = (595, 842)
    pagesizes.portrait = lambda x: x
    styles = module('reportlab.lib.styles')
    styles.getSampleStyleSheet = lambda: {
        'Heading1': ObjetPdf(), 'Heading2': ObjetPdf(), 'Normal': ObjetPdf()}
    styles.ParagraphStyle = lambda *a, **k: ObjetPdf()
    platypus = module('reportlab.platypus')
    for nom in ('SimpleDocTemplate', 'Paragraph', 'Spacer', 'Table', 'TableStyle',
                'PageBreak', 'KeepTogether'):
        setattr(platypus, nom, lambda *a, **k: ObjetPdf())

    module('apps')
    module('apps.common')
    module('apps.common.renderers').PassthroughBinaryRenderer = type(
        'PassthroughBinaryRenderer', (), {})
    module('apps.common.pdf_header').get_store_logo_flowable = lambda *a, **k: ObjetPdf()
    module('apps.common.pdf_header').create_header_with_logo = lambda *a, **k: []

    module('apps.companies')

    class Company:
        objects = Manager([{'id': ENTREPRISE, 'name': 'NEXORA BF'}], 'Company')
        _meta = Meta(CHAMPS_MODELE['Company'])

    module('apps.companies.models').Company = Company
    module('apps.accounts')

    class User:
        objects = Manager(UTILISATEURS, 'User')
        _meta = Meta(CHAMPS_MODELE['User'])

    module('apps.accounts.models').User = User
    module('apps.sales')
    sales_models = module('apps.sales.models')

    class Sale:
        objects = Manager(VENTES, 'Sale')
        _meta = Meta(CHAMPS_MODELE['Sale'])

    class SaleItem:
        objects = Manager([], 'Sale')

    class Payment:
        objects = Manager([], 'Sale')

    class SaleStatus:
        COMPLETED = 'COMPLETED'
        CANCELLED = 'CANCELLED'
        DRAFT = 'DRAFT'

    sales_models.Sale = Sale
    sales_models.SaleItem = SaleItem
    sales_models.Payment = Payment
    sales_models.SaleStatus = SaleStatus
    module('apps.inventory')
    module('apps.inventory.models').Store = type('Store', (), {
        'objects': Manager([{'id': 'S1', 'company': ENTREPRISE, 'name': 'Ouaga'}], 'Store'),
        '_meta': Meta(CHAMPS_MODELE['Store'])})


def charger_module():
    import importlib.util as util

    spec = util.spec_from_file_location('pdf_seller_simule', CHEMIN)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    installer_modules()
    try:
        module = charger_module()
    except Exception as erreur:
        print('ÉCHEC DE CHARGEMENT : %r' % erreur)
        return 2

    resoudre = (getattr(module, '_nexora_resolve_seller', None)
                or getattr(module, 'resolve_seller', None))
    ventes_de = (getattr(module, '_nexora_ventes_du_vendeur', None)
                 or getattr(module, 'sales_queryset_for_seller', None))
    if resoudre is None or ventes_de is None:
        print('ÉCHEC : fonctions du correctif introuvables dans %s' % CHEMIN)
        return 2

    echecs = []

    def verifier(condition, message):
        print(('  [OK]   ' if condition else '  [ECHEC] ') + message)
        if not condition:
            echecs.append(message)

    print('Fichier testé : %s' % CHEMIN)

    print('\n1) résolution du vendeur')
    v, err = resoudre(ENTREPRISE, str(VENDEUR1))
    verifier(v is not None and v['email'] == 'august.nanema@nexora-bf.com' and err is None,
             'UUID -> vendeur trouvé')
    v, err = resoudre(ENTREPRISE, 'vendeur.bobo@nexora-bf.com')
    verifier(v is not None and v['id'] == VENDEUR2 and err is None, 'email exact -> vendeur trouvé')
    v, err = resoudre(ENTREPRISE, 'VENDEUR.BOBO@NEXORA-BF.COM')
    verifier(v is not None and v['id'] == VENDEUR2, 'email exact insensible à la casse')
    v, err = resoudre(ENTREPRISE, 'bobo@nexora-bf')
    verifier(v is not None and v['id'] == VENDEUR2, 'email partiel unique -> vendeur trouvé')
    v, err = resoudre(ENTREPRISE, 'Awa SAWADOGO')
    verifier(v is not None and v['id'] == VENDEUR2, 'nom complet -> vendeur trouvé')
    v, err = resoudre(ENTREPRISE, 'nexora-bf.com')
    verifier(v is None and err is not None, 'email partiel AMBIGU -> erreur explicite')
    v, err = resoudre(ENTREPRISE, 'inconnu@nexora-bf.com')
    verifier(v is None and err is not None, 'vendeur inconnu -> erreur explicite')
    v, err = resoudre(ENTREPRISE, None)
    verifier(v is None and err is None, 'aucun paramètre -> comportement par défaut')
    v, err = resoudre(ENTREPRISE, 'chef@autre.com')
    verifier(v is None and err is not None, 'vendeur d’une autre entreprise -> refusé')
    v, err = resoudre(ENTREPRISE, str(AUTRE_USER))
    verifier(v is None and err is not None, 'UUID d’une autre entreprise -> refusé')

    print('\n2) ventes retenues pour le bilan')
    debut = MAINTENANT - datetime.timedelta(days=30)
    fin = MAINTENANT + datetime.timedelta(hours=4)
    qs = ventes_de(ENTREPRISE, UTILISATEURS[0], debut, fin)
    identifiants = [ligne['id'] for ligne in qs]
    print('   ventes retenues : %s' % identifiants)
    verifier(identifiants == [1, 2], 'uniquement les ventes validées du vendeur, dans la période')
    for exclue, libelle in ((4, 'annulée'), (5, 'brouillon'), (6, 'sans vendeur'),
                            (7, 'hors période'), (8, 'autre entreprise')):
        verifier(exclue not in identifiants, 'vente %s exclue' % libelle)
    total = sum(ligne['total_amount'] for ligne in qs)
    verifier(total == 3000, 'CA du vendeur = 3 000 (obtenu : %s)' % total)
    qs2 = ventes_de(ENTREPRISE, UTILISATEURS[1], debut, fin)
    verifier([l['id'] for l in qs2] == [3], 'le vendeur 2 ne voit que sa vente')
    verifier(sum(l['total_amount'] for l in qs2) == 4000, 'CA vendeur 2 = 4 000')

    print('\n3) vue complète (jusqu’au PDF)')
    classe = module.SellerSalesReportPdfView

    class Requete:
        def __init__(self, params, utilisateur=None):
            self.query_params = params
            self.user = utilisateur or types.SimpleNamespace(
                is_authenticated=False, company=None, role=None)

    societe = types.SimpleNamespace(id=ENTREPRISE, name='NEXORA BF')
    utilisateur = types.SimpleNamespace(
        is_authenticated=True, company=societe, role='ADMIN', email='admin@nexora-bf.com',
        id=uuid.UUID('99999999-9999-9999-9999-999999999999'))

    vue = classe()
    try:
        reponse = vue.get(Requete({'start_date': '2026-09-07', 'end_date': '2026-10-07',
                                   'seller_id': str(AUTRE_USER)}, utilisateur))
        verifier(getattr(reponse, 'status_code', None) == 404,
                 'vendeur inconnu -> 404 (obtenu : %s)' % getattr(reponse, 'status_code', None))
    except Exception as erreur:
        import traceback
        traceback.print_exc()
        verifier(False, 'vendeur inconnu -> exception %r' % erreur)

    try:
        reponse = vue.get(Requete({'start_date': '2026-09-07', 'end_date': '2026-10-07',
                                   'seller_id': str(VENDEUR1)}, utilisateur))
        verifier(getattr(reponse, 'status_code', None) == 200,
                 'vendeur valide -> PDF généré (statut %s)' % getattr(reponse, 'status_code', None))
    except Exception as erreur:
        import traceback
        traceback.print_exc()
        verifier(False, 'vendeur valide -> exception %r' % erreur)

    print('\n' + ('TOUS LES CONTRÔLES SONT PASSÉS (%d)' % (10 + 9 + 2)
                  if not echecs else 'ÉCHECS : %d' % len(echecs)))
    for message in echecs:
        print('  - %s' % message)
    return 1 if echecs else 0


if __name__ == '__main__':
    sys.exit(main())
