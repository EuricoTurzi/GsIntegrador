from django.urls import path
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    MeView,
    ChangePasswordView,
    UserListView,
    # Template views
    login_view,
    register_view,
    profile_view,
    change_password_view,
    user_list_view,
)

app_name = 'authentication'

urlpatterns = [
    # Template views (HTML)
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('profile/', profile_view, name='profile'),
    path('change-password/', change_password_view, name='change-password'),
    path('logout/', DjangoLogoutView.as_view(), name='logout'),
    path('users/', user_list_view, name='user-list'),
    path('users/<int:pk>/', profile_view, name='user-detail'),  # Temporário, usa profile view
    path('users/<int:pk>/edit/', profile_view, name='user-edit'),  # Temporário, usa profile view
    
    # API Autenticação
    path('api/register/', RegisterView.as_view(), name='api-register'),
    path('api/login/', LoginView.as_view(), name='api-login'),
    path('api/logout/', LogoutView.as_view(), name='api-logout'),
    
    # JWT Token Refresh
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Perfil do usuário
    path('api/me/', MeView.as_view(), name='me'),
    path('api/change-password/', ChangePasswordView.as_view(), name='api-change-password'),
    
    # API Lista de usuários
    path('api/users/', UserListView.as_view(), name='api-user-list'),
]
