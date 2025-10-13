"""
URLs para a aplicação de monitoramento.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MonitoringSystemViewSet

router = DefaultRouter()
router.register(r'', MonitoringSystemViewSet, basename='monitoring')

urlpatterns = router.urls
