from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer
)


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    
    Endpoint para registro de novos usuários.
    Público (sem autenticação necessária).
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Gerar tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Usuário registrado com sucesso!'
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    POST /api/auth/login/
    
    Endpoint para login de usuários.
    Retorna tokens JWT (access e refresh).
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Fazer login do usuário
        login(request, user)
        
        # Gerar tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Login realizado com sucesso!'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    
    Endpoint para logout de usuários.
    Adiciona o refresh token à blacklist.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            logout(request)
            
            return Response({
                'message': 'Logout realizado com sucesso!'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Token inválido ou expirado.'
            }, status=status.HTTP_400_BAD_REQUEST)


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET /api/auth/me/
    PUT/PATCH /api/auth/me/
    
    Endpoint para ver e atualizar dados do usuário autenticado.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'user': serializer.data,
            'message': 'Perfil atualizado com sucesso!'
        })


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    
    Endpoint para alteração de senha do usuário autenticado.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Senha alterada com sucesso!'
        }, status=status.HTTP_200_OK)


class UserListView(generics.ListAPIView):
    """
    GET /api/auth/users/
    
    Lista todos os usuários (apenas para GR e staff).
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Apenas GR e staff podem ver todos os usuários
        if user.is_staff or user.is_gr:
            return User.objects.all()
        
        # Transportadora vê apenas seu próprio perfil
        return User.objects.filter(id=user.id)


# =============== TEMPLATE VIEWS ===============

def login_view(request):
    """View para processar login com formulário HTML"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        from django.contrib.auth import authenticate, login as auth_login
        
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            messages.success(request, f'Bem-vindo de volta, {user.username}!')
            
            # Redirecionar para o next ou dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    
    return render(request, 'authentication/login.html')


def register_view(request):
    """View para renderizar o template de registro"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'authentication/register.html')


@login_required
def profile_view(request):
    """View para renderizar o template de perfil"""
    return render(request, 'authentication/profile.html')


@login_required
def change_password_view(request):
    """View para renderizar o template de alteração de senha"""
    return render(request, 'authentication/change_password.html')


@login_required
def user_list_view(request):
    """View para renderizar o template de lista de usuários (GR only)"""
    if not (request.user.is_superuser or request.user.user_type == 'GR'):
        messages.error(request, 'Acesso negado. Apenas GR pode acessar esta página.')
        return redirect('dashboard')
    
    users = User.objects.all().order_by('-date_joined')
    
    # Stats
    stats = {
        'total': users.count(),
        'active': users.filter(is_active=True).count(),
        'gr': users.filter(user_type='GR').count(),
        'transportadora': users.filter(user_type='TRANSPORTADORA').count(),
    }
    
    return render(request, 'authentication/user_list.html', {
        'users': users,
        'stats': stats
    })
