from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from apps.common.health import HealthCheckView
from apps.accounts.views import CustomTokenObtainPairView, UserViewSet
from apps.companies.views import CompanyViewSet
from apps.catalog.views import CategoryViewSet, UnitViewSet, ProductViewSet
from apps.partners.views import PartnerViewSet
from apps.inventory.views import StoreViewSet, StockLevelViewSet, StockMovementViewSet, InventoryViewSet
from apps.inventory.analytics import StockIntelligenceAnalyticsView
from apps.pos.views import CashRegisterViewSet, RegisterSessionViewSet
from apps.pos.suggestions import SmartSuggestionsView
from apps.sales.views import SaleViewSet, PaymentViewSet, SaleReturnViewSet
from apps.purchases.views import PurchaseViewSet, PurchaseReturnViewSet
from apps.notifications.views import NotificationViewSet
from apps.audit.views import AuditLogViewSet
from apps.reports.views import DashboardSummaryReportView, InventoryValuationReportView
from apps.reports.bi_analytics import BusinessIntelligenceAnalyticsView
from apps.ai_assistant.views import AutomationRuleViewSet, AutomationLogViewSet, AIChatAssistantView

router = DefaultRouter()

# Core & Tenants
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'users', UserViewSet, basename='user')

# Catalog
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'units', UnitViewSet, basename='unit')
router.register(r'products', ProductViewSet, basename='product')

# Partners
router.register(r'partners', PartnerViewSet, basename='partner')

# Inventory & Stores
router.register(r'stores', StoreViewSet, basename='store')
router.register(r'stock-levels', StockLevelViewSet, basename='stock-level')
router.register(r'stock-movements', StockMovementViewSet, basename='stock-movement')
router.register(r'inventories', InventoryViewSet, basename='inventory')

# POS
router.register(r'registers', CashRegisterViewSet, basename='register')
router.register(r'sessions', RegisterSessionViewSet, basename='session')

# Sales & Payments
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'sale-returns', SaleReturnViewSet, basename='sale-return')

# Purchases
router.register(r'purchases', PurchaseViewSet, basename='purchase')
router.register(r'purchase-returns', PurchaseReturnViewSet, basename='purchase-return')

# Notifications & Audit
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

# AI Automation Rules & Execution Logs
router.register(r'automation-rules', AutomationRuleViewSet, basename='automation-rule')
router.register(r'automation-logs', AutomationLogViewSet, basename='automation-log')

urlpatterns = [
    # Healthcheck Monitoring
    path('health/', HealthCheckView.as_view(), name='healthcheck'),

    # OpenAPI Schema & Docs
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # JWT Authentication
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # AI Conversational Assistant
    path('ai/chat/', AIChatAssistantView.as_view(), name='ai_chat'),

    # Stock Intelligence & Anticipation
    path('inventory/intelligence/', StockIntelligenceAnalyticsView.as_view(), name='stock_intelligence'),

    # Smart POS Suggestions
    path('pos/suggestions/', SmartSuggestionsView.as_view(), name='pos_suggestions'),

    # Reports & BI
    path('reports/dashboard/', DashboardSummaryReportView.as_view(), name='report_dashboard'),
    path('reports/inventory-valuation/', InventoryValuationReportView.as_view(), name='report_inventory_valuation'),
    path('reports/bi-analytics/', BusinessIntelligenceAnalyticsView.as_view(), name='report_bi_analytics'),

    # ViewSets Router
    path('', include(router.urls)),
]
