"""
URLs para a aplicação de motoristas.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DriverViewSet

app_name = 'drivers'

router = DefaultRouter()
router.register(r'', DriverViewSet, basename='driver')

urlpatterns = router.urls
