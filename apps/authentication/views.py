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
    """View para processar registro com formulário HTML"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            # Coletar dados do formulário
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            user_type = request.POST.get('user_type', 'TRANSPORTADORA')
            
            # Validações básicas
            if not username or not email or not password:
                messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
                return render(request, 'authentication/register.html')
            
            if password != password_confirm:
                messages.error(request, 'As senhas não coincidem.')
                return render(request, 'authentication/register.html')
            
            # Verificar se username já existe
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Este nome de usuário já está em uso.')
                return render(request, 'authentication/register.html')
            
            # Verificar se email já existe
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Este email já está cadastrado.')
                return render(request, 'authentication/register.html')
            
            # Validar campos de Transportadora
            if user_type == 'TRANSPORTADORA':
                company_name = request.POST.get('company_name')
                cnpj = request.POST.get('cnpj')
                
                if not company_name or not cnpj:
                    messages.error(request, 'Nome da empresa e CNPJ são obrigatórios para Transportadora.')
                    return render(request, 'authentication/register.html')
            
            # Criar usuário
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                user_type=user_type,
                company_name=request.POST.get('company_name', ''),
                cnpj=request.POST.get('cnpj', ''),
                phone=request.POST.get('phone', ''),
            )
            
            messages.success(request, 'Conta criada com sucesso! Faça login para continuar.')
            return redirect('authentication:login')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar conta: {str(e)}')
            return render(request, 'authentication/register.html')
    
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


@login_required
def user_detail_view(request, pk):
    """View para visualizar detalhes de um usuário específico"""
    from django.shortcuts import get_object_or_404
    
    # Verificar permissão
    if not (request.user.is_superuser or request.user.user_type == 'GR'):
        # Usuários normais só podem ver seu próprio perfil
        if request.user.id != pk:
            messages.error(request, 'Você não tem permissão para visualizar este perfil.')
            return redirect('authentication:profile')
    
    user = get_object_or_404(User, pk=pk)
    
    return render(request, 'authentication/user_detail.html', {
        'user_profile': user
    })


@login_required
def user_edit_view(request, pk):
    """View para editar um usuário específico"""
    from django.shortcuts import get_object_or_404
    
    # Verificar permissão
    if not (request.user.is_superuser or request.user.user_type == 'GR'):
        # Usuários normais só podem editar seu próprio perfil
        if request.user.id != pk:
            messages.error(request, 'Você não tem permissão para editar este perfil.')
            return redirect('authentication:profile')
    
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        # Atualizar dados do usuário
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        
        if user.user_type == 'TRANSPORTADORA':
            user.company_name = request.POST.get('company_name', user.company_name)
            user.cnpj = request.POST.get('cnpj', user.cnpj)
            user.phone = request.POST.get('phone', user.phone)
        
        # Apenas admin/GR pode alterar status e tipo
        if request.user.is_superuser or request.user.user_type == 'GR':
            user.is_active = request.POST.get('is_active') == 'on'
            user.is_verified = request.POST.get('is_verified') == 'on'
        
        user.save()
        messages.success(request, 'Usuário atualizado com sucesso!')
        return redirect('authentication:user-detail', pk=user.pk)
    
    return render(request, 'authentication/user_edit.html', {
        'user_profile': user
    })