from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin para o modelo User customizado"""
    
    list_display = ('username', 'email', 'user_type', 'company_name', 'is_verified', 'is_active', 'created_at')
    list_filter = ('user_type', 'is_verified', 'is_active', 'is_staff', 'created_at')
    search_fields = ('username', 'email', 'company_name', 'cnpj', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Informações Pessoais'), {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        (_('Tipo de Usuário'), {'fields': ('user_type', 'company_name', 'cnpj')}),
        (_('Permissões'), {
            'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Datas Importantes'), {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type', 'company_name', 'cnpj'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # GR pode ver todos os usuários
        # Transportadora vê apenas seu próprio perfil
        if request.user.is_superuser or request.user.is_gr:
            return qs
        return qs.filter(id=request.user.id)
