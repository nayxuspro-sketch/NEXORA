import re
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F

from apps.sales.models import Sale, SaleItem, SaleStatus
from apps.inventory.models import StockLevel, StockMovementType
from apps.catalog.models import Product


class AIAssistantService:
    """
    Role-aware Conversational AI Assistant.
    Strictly enforces role-based access control (RBAC):
    - CASHIER: Can only view daily cashier stats, today's sales volume.
    - STOCK_KEEPER: Can view stock levels, shortages, dormant stock, but NOT total financial profit.
    - MANAGER / ADMIN: Full access to financial profitability, margins, and activity summaries.
    """

    @classmethod
    def process_query(cls, query: str, user, company) -> dict:
        q = query.strip().lower()
        role = user.role

        # Intent 1: "Combien ai-je vendu aujourd'hui ?"
        if any(w in q for w in ["vendu aujourd'hui", "vente aujourd'hui", "combien aujourd'hui", "ventes du jour"]):
            return cls._handle_today_sales(user, company, role)

        # Intent 2: "Quels sont mes produits les plus rentables ?"
        if any(w in q for w in ["rentable", "plus rentables", "meilleure marge", "rentabilité"]):
            if role in ['CASHIER', 'STOCK_KEEPER']:
                return {
                    'answer': "Accès restreint : Votre rôle actuel ne vous permet pas de consulter les données de marge financière et de rentabilité.",
                    'role_blocked': True,
                    'explanation': None
                }
            return cls._handle_most_profitable_products(company)

        # Intent 3: "Quels produits risquent de manquer ?"
        if any(w in q for w in ["risquent de manquer", "rupture", "manquer", "stock bas", "seuil critique"]):
            return cls._handle_stock_shortage_risks(company)

        # Intent 4: "Quels produits sont dormants ?"
        if any(w in q for w in ["dormant", "dormants", "en sommeil", "invendu", "sans vente"]):
            return cls._handle_dormant_products(company)

        # Intent 5: "Résume mon activité."
        if any(w in q for w in ["résume", "resume", "activité", "bilan", "synthèse"]):
            return cls._handle_activity_summary(user, company, role)

        # Fallback / General intent
        return {
            'answer': (
                f"Bonjour {user.first_name} ! Je suis l'assistant intelligent de NEXORA. "
                "Je peux vous renseigner sur : vos ventes du jour, les produits les plus rentables, "
                "les risques imminents de rupture de stock, les produits dormants ou vous dresser une synthèse d'activité."
            ),
            'suggestions': [
                "Combien ai-je vendu aujourd'hui ?",
                "Quels produits risquent de manquer ?",
                "Quels sont mes produits les plus rentables ?",
                "Résume mon activité.",
                "Quels produits sont dormants ?"
            ]
        }

    @classmethod
    def _handle_today_sales(cls, user, company, role):
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        sales_qs = Sale.objects.filter(
            company=company,
            status=SaleStatus.COMPLETED,
            created_at__gte=today_start
        )

        if role == 'CASHIER':
            sales_qs = sales_qs.filter(seller=user)

        agg = sales_qs.aggregate(total=Sum('total_amount'), count=Count('id'))
        total_revenue = agg['total'] or Decimal('0.00')
        count = agg['count'] or 0

        scope = "sur votre caisse" if role == 'CASHIER' else "à l'échelle de l'entreprise"

        return {
            'answer': (
                f"Aujourd'hui, vous avez enregistré un chiffre d'affaires de {total_revenue} € {scope}, "
                f"pour un volume de {count} vente(s) validée(s)."
            ),
            'metrics': {
                'today_revenue': str(total_revenue),
                'today_count': count,
            },
            'explanation': {
                'data_source': "Table des ventes (Sale)",
                'timeframe': "Depuis aujourd'hui 00:00 UTC",
                'logic': "Somme des ventes finalisées (status=COMPLETED)",
                'limits': "Ne prend pas en compte les paniers en cours ou annulés."
            }
        }

    @classmethod
    def _handle_most_profitable_products(cls, company):
        now = timezone.now()
        since = now - timedelta(days=30)

        items = SaleItem.objects.filter(
            company=company,
            sale__status=SaleStatus.COMPLETED,
            sale__created_at__gte=since
        ).select_related('product')

        profit_by_prod = {}
        for it in items:
            pid = str(it.product.id)
            if pid not in profit_by_prod:
                profit_by_prod[pid] = {
                    'name': it.product.name,
                    'sku': it.product.sku,
                    'revenue': Decimal('0.00'),
                    'cost': Decimal('0.00'),
                }
            profit_by_prod[pid]['revenue'] += it.total
            profit_by_prod[pid]['cost'] += (it.quantity * it.product.cost_price)

        results = []
        for pid, data in profit_by_prod.items():
            profit = data['revenue'] - data['cost']
            margin_rate = ((profit / data['revenue']) * 100).quantize(Decimal('0.1')) if data['revenue'] > 0 else Decimal('0.0')
            results.append({
                'name': data['name'],
                'sku': data['sku'],
                'profit': profit,
                'margin_rate': margin_rate
            })

        results = sorted(results, key=lambda x: x['profit'], reverse=True)[:3]

        if not results:
            return {
                'answer': "Aucune vente n'a encore été enregistrée sur les 30 derniers jours pour déterminer les articles les plus rentables.",
                'explanation': None
            }

        top_names = ", ".join([f"'{r['name']}' (Marge brute: {r['profit']:.2f} €, Taux: {r['margin_rate']}%)" for r in results])

        return {
            'answer': (
                f"Sur les 30 derniers jours, vos articles les plus rentables sont : {top_names}. "
                "Ces articles dégagent le bénéfice brut cumulé le plus élevé pour l'entreprise."
            ),
            'top_profitable': [
                {'name': r['name'], 'sku': r['sku'], 'profit': str(r['profit']), 'margin_rate': str(r['margin_rate'])}
                for r in results
            ],
            'explanation': {
                'data_source': "Lignes de vente (SaleItem) et Coûts de revient produits (Product.cost_price)",
                'timeframe': "30 derniers jours d'activité",
                'logic': "Marge = Chiffre d'Affaires réalisé - Coût de revient d'achat",
                'limits': "Estimation indicative basée sur le prix d'achat standard actuel, hors frais généraux de structure."
            }
        }

    @classmethod
    def _handle_stock_shortage_risks(cls, company):
        low_stocks = StockLevel.objects.filter(
            company=company,
            quantity__lte=F('product__alert_threshold')
        ).select_related('product', 'store')

        if not low_stocks.exists():
            return {
                'answer': "Excellente nouvelle ! Tous vos articles sont actuellement au-dessus de leur seuil d'alerte. Aucun risque de rupture immédiat.",
                'explanation': None
            }

        count = low_stocks.count()
        sample = [f"'{ls.product.name}' ({ls.quantity} pcs restantes @ {ls.store.name}, seuil: {ls.product.alert_threshold})" for ls in low_stocks[:3]]
        sample_str = ", ".join(sample)

        return {
            'answer': (
                f"Attention : {count} référence(s) sont sous leur seuil d'alerte critique. "
                f"Les plus urgentes sont : {sample_str}. Un réapprovisionnement rapide est fortement conseillé."
            ),
            'critical_count': count,
            'explanation': {
                'data_source': "Niveaux de stock (StockLevel) et Seuils configurés (Product.alert_threshold)",
                'timeframe': "État instantané en temps réel",
                'logic': "Condition de risque : Quantité en stock <= Seuil d'alerte",
                'limits': "Ne préjuge pas des commandes fournisseurs déjà en cours de livraison."
            }
        }

    @classmethod
    def _handle_dormant_products(cls, company):
        since = timezone.now() - timedelta(days=30)
        sold_prod_ids = SaleItem.objects.filter(
            company=company,
            sale__status=SaleStatus.COMPLETED,
            sale__created_at__gte=since
        ).values_list('product_id', flat=True).distinct()

        dormant_levels = StockLevel.objects.filter(
            company=company,
            quantity__gt=Decimal('0.00')
        ).exclude(product_id__in=sold_prod_ids).select_related('product', 'store')[:5]

        if not dormant_levels.exists():
            return {
                'answer': "Aucun stock dormant détecté : toutes vos références actives en rayon ont enregistré des ventes au cours des 30 derniers jours.",
                'explanation': None
            }

        names = ", ".join([f"'{d.product.name}' ({d.quantity} pcs)" for d in dormant_levels])

        return {
            'answer': (
                f"Nous avons identifié des produits avec stock positif mais zéro vente sur les 30 derniers jours : {names}. "
                "Ces articles immobilisent inutilement de la trésorerie. Une action de déstockage ou de promotion est envisageable."
            ),
            'explanation': {
                'data_source': "Croisement entre StockLevel > 0 et absence de SaleItem",
                'timeframe': "Fenêtre glissante de 30 jours",
                'logic': "Quantité disponible positive sans aucune transaction d'écoulement",
                'limits': "Les produits récemment introduits dans le catalogue peuvent temporairement apparaître ici."
            }
        }

    @classmethod
    def _handle_activity_summary(cls, user, company, role):
        since = timezone.now() - timedelta(days=7)
        sales = Sale.objects.filter(company=company, status=SaleStatus.COMPLETED, created_at__gte=since)
        agg = sales.aggregate(total=Sum('total_amount'), count=Count('id'))
        total_rev = agg['total'] or Decimal('0.00')
        tx_count = agg['count'] or 0

        low_count = StockLevel.objects.filter(company=company, quantity__lte=F('product__alert_threshold')).count()

        summary_text = (
            f"Synthèse de vos 7 derniers jours : {tx_count} vente(s) enregistrée(s) pour un chiffre d'affaires de {total_rev} €. "
            f"Sur le plan logistique, {low_count} article(s) nécessitent un réapprovisionnement."
        )

        return {
            'answer': summary_text,
            'summary': {
                'revenue_7d': str(total_rev),
                'sales_7d': tx_count,
                'low_stock_count': low_count
            },
            'explanation': {
                'data_source': "Agrégation des transactions et du stock",
                'timeframe': "7 derniers jours glissants",
                'logic': "Synthèse globale de performance commerciale et opérationnelle",
                'limits': "Vue d'ensemble générale."
            }
        }
