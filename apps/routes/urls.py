"""
URLs para a aplicação de rotas.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RouteViewSet, GeocodeView, ReverseGeocodeView

router = DefaultRouter()
router.register(r'', RouteViewSet, basename='route')

urlpatterns = [
    # Geocoding endpoints
    path('geocode/', GeocodeView.as_view(), name='geocode'),
    path('reverse-geocode/', ReverseGeocodeView.as_view(), name='reverse-geocode'),
    
    # Rotas CRUD
    path('', include(router.urls)),
]
