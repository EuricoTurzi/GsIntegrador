"""
URLs para a aplicação de veículos.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VehicleViewSet

app_name = 'vehicles'

router = DefaultRouter()
router.register(r'', VehicleViewSet, basename='vehicle')

urlpatterns = router.urls
