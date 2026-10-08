# -*- coding: utf-8 -*-
"""Diagnostic des magasins et des caisses, entreprise par entreprise.

Repond a la question : « pourquoi la caisse affiche-t-elle Magasin
introuvable dans votre entreprise ? »

    py manage.py diagnostiquer_caisses

Le rapport est en LECTURE SEULE : il ne modifie aucune donnee.
"""

from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.companies.models import Company
from apps.inventory.models import Store
from apps.pos.models import CashRegister


class Command(BaseCommand):
    help = 'Montre les magasins, les caisses et les comptes par entreprise.'

    def handle(self, *args, **options):
        entreprises = list(Company.objects.all().order_by('name'))
        if not entreprises:
            self.stdout.write('Aucune entreprise en base : creez-en une, puis un magasin, puis une caisse.')
            return

        self.stdout.write('DIAGNOSTIC DES CAISSES NEXORA')
        self.stdout.write('=' * 74)

        total_magasins = Store.objects.count()
        total_caisses = CashRegister.objects.count()
        self.stdout.write('%d entreprise(s), %d magasin(s), %d caisse(s) au total.'
                          % (len(entreprises), total_magasins, total_caisses))
        self.stdout.write('')

        for entreprise in entreprises:
            magasins = Store.objects.filter(company=entreprise).order_by('name')
            caisses = CashRegister.objects.filter(company=entreprise).select_related('store')
            self.stdout.write('ENTREPRISE : %s' % entreprise.name)
            self.stdout.write('  magasins : %s' % (
                ', '.join('%s (%s)' % (m.name, m.code) for m in magasins) or 'AUCUN'))
            if caisses:
                for caisse in caisses:
                    self.stdout.write('  caisse   : %s (%s) -> magasin %s [%s]'
                                      % (caisse.name, caisse.code, caisse.store.name, caisse.status))
            else:
                self.stdout.write('  caisse   : AUCUNE')
            comptes = User.objects.filter(company=entreprise).order_by('email')
            self.stdout.write('  comptes  : %s' % (
                ', '.join('%s (%s)' % (u.email, u.role) for u in comptes) or 'AUCUN'))
            self.stdout.write('')

        # --- anomalies qui provoquent exactement le message signale ---
        anomalies = 0
        for caisse in CashRegister.objects.select_related('store', 'company'):
            if caisse.store.company_id != caisse.company_id:
                anomalies += 1
                self.stdout.write('ANOMALIE : la caisse %s (%s) appartient a « %s » mais vise le '
                                  'magasin « %s » de « %s »'
                                  % (caisse.name, caisse.code, caisse.company.name,
                                     caisse.store.name, caisse.store.company.name))
        for compte in User.objects.select_related('company').all():
            if compte.is_superuser or compte.company_id is None:
                continue
            if not Store.objects.filter(company_id=compte.company_id).exists():
                anomalies += 1
                self.stdout.write('ANOMALIE : le compte %s n\'a AUCUN magasin dans son entreprise '
                                  '(« %s ») : la caisse ne peut rien vendre.'
                                  % (compte.email, compte.company.name if compte.company else '—'))
            elif not CashRegister.objects.filter(company_id=compte.company_id).exists():
                anomalies += 1
                self.stdout.write('A REMARQUER : le compte %s n\'a AUCUNE caisse dans son entreprise '
                                  '(« %s ») : le POS proposera d\'en creer une.'
                                  % (compte.email, compte.company.name if compte.company else '—'))

        self.stdout.write('=' * 74)
        if anomalies:
            self.stdout.write('%d point(s) a regarder (voir ci-dessus).' % anomalies)
            self.stdout.write('Correction conseillee : lancer corriger_caisses_pos.py, puis')
            self.stdout.write('creer magasin et caisse directement depuis l\'ecran de caisse du POS.')
        else:
            self.stdout.write('Aucune anomalie : chaque caisse vise un magasin de sa propre entreprise.')
