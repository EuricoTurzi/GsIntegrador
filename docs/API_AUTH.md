# 🔐 API de Autenticação - Documentação

## Endpoints Disponíveis

### 1. Registro de Usuário

**POST** `/api/auth/register/`

Cria um novo usuário no sistema.

**Request Body:**

```json
{
  "username": "transportadora1",
  "email": "contato@transportadora1.com",
  "password": "senha_segura_123",
  "password2": "senha_segura_123",
  "first_name": "João",
  "last_name": "Silva",
  "user_type": "TRANSPORTADORA",
  "company_name": "Transportadora Silva LTDA",
  "cnpj": "12.345.678/0001-90",
  "phone": "(11) 98765-4321"
}
```

**Response (201):**

```json
{
  "user": {
    "id": 1,
    "username": "transportadora1",
    "email": "contato@transportadora1.com",
    "first_name": "João",
    "last_name": "Silva",
    "user_type": "TRANSPORTADORA",
    "company_name": "Transportadora Silva LTDA",
    "cnpj": "12.345.678/0001-90",
    "phone": "(11) 98765-4321",
    "is_active": true,
    "is_verified": false
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGci...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGci..."
  },
  "message": "Usuário registrado com sucesso!"
}
```

---

### 2. Login

**POST** `/api/auth/login/`

Autentica um usuário e retorna tokens JWT.

**Request Body:**

```json
{
  "username": "transportadora1",
  "password": "senha_segura_123"
}
```

**Response (200):**

```json
{
  "user": {
    "id": 1,
    "username": "transportadora1",
    "email": "contato@transportadora1.com",
    "user_type": "TRANSPORTADORA",
    "company_name": "Transportadora Silva LTDA"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGci...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGci..."
  },
  "message": "Login realizado com sucesso!"
}
```

---

### 3. Logout

**POST** `/api/auth/logout/`

Faz logout do usuário e adiciona o token à blacklist.

**Headers:**

```
Authorization: Bearer {access_token}
```

**Request Body:**

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}
```

**Response (200):**

```json
{
  "message": "Logout realizado com sucesso!"
}
```

---

### 4. Atualizar Token

**POST** `/api/auth/token/refresh/`

Gera um novo access token usando o refresh token.

**Request Body:**

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}
```

**Response (200):**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}
```

---

### 5. Meu Perfil (GET)

**GET** `/api/auth/me/`

Retorna os dados do usuário autenticado.

**Headers:**

```
Authorization: Bearer {access_token}
```

**Response (200):**

```json
{
  "id": 1,
  "username": "transportadora1",
  "email": "contato@transportadora1.com",
  "first_name": "João",
  "last_name": "Silva",
  "user_type": "TRANSPORTADORA",
  "company_name": "Transportadora Silva LTDA",
  "cnpj": "12.345.678/0001-90",
  "phone": "(11) 98765-4321",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-10-07T10:30:00Z",
  "updated_at": "2025-10-07T10:30:00Z"
}
```

---

### 6. Atualizar Perfil (PUT/PATCH)

**PUT/PATCH** `/api/auth/me/`

Atualiza os dados do usuário autenticado.

**Headers:**

```
Authorization: Bearer {access_token}
```

**Request Body (exemplo parcial):**

```json
{
  "first_name": "João Carlos",
  "phone": "(11) 91234-5678"
}
```

**Response (200):**

```json
{
  "user": {
    "id": 1,
    "username": "transportadora1",
    "first_name": "João Carlos",
    "phone": "(11) 91234-5678",
    ...
  },
  "message": "Perfil atualizado com sucesso!"
}
```

---

### 7. Alterar Senha

**POST** `/api/auth/change-password/`

Altera a senha do usuário autenticado.

**Headers:**

```
Authorization: Bearer {access_token}
```

**Request Body:**

```json
{
  "old_password": "senha_antiga",
  "new_password": "nova_senha_segura_456",
  "new_password2": "nova_senha_segura_456"
}
```

**Response (200):**

```json
{
  "message": "Senha alterada com sucesso!"
}
```

---

### 8. Listar Usuários

**GET** `/api/auth/users/`

Lista todos os usuários (apenas para GR e staff).

**Headers:**

```
Authorization: Bearer {access_token}
```

**Response (200):**

```json
[
  {
    "id": 1,
    "username": "transportadora1",
    "email": "contato@transportadora1.com",
    "user_type": "TRANSPORTADORA",
    "company_name": "Transportadora Silva LTDA",
    ...
  },
  {
    "id": 2,
    "username": "gr_user",
    "email": "gr@empresa.com",
    "user_type": "GR",
    ...
  }
]
```

---

## Tipos de Usuário

### GR (Gerente de Risco)

- Acesso completo ao sistema
- Pode visualizar todas as SMs de todas as transportadoras
- Gerencia e monitora todo o sistema
- Campos obrigatórios: username, email, password

### TRANSPORTADORA

- Gerencia seus próprios dados
- Cadastra motoristas, veículos e cria SMs
- Visualiza apenas suas próprias SMs
- Campos obrigatórios: username, email, password, company_name, cnpj

---

## Autenticação

### JWT (JSON Web Token)

O sistema utiliza JWT para autenticação. Existem dois tipos de tokens:

1. **Access Token**:

   - Duração: 12 horas
   - Usado em todas as requisições autenticadas
   - Enviado no header: `Authorization: Bearer {access_token}`

2. **Refresh Token**:
   - Duração: 7 dias
   - Usado para gerar novos access tokens
   - Enviado no endpoint `/api/auth/token/refresh/`

### Exemplo de uso:

```javascript
// 1. Login
const loginResponse = await fetch("/api/auth/login/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username: "user", password: "pass" }),
});
const { tokens } = await loginResponse.json();

// 2. Usar access token nas requisições
const response = await fetch("/api/auth/me/", {
  headers: {
    Authorization: `Bearer ${tokens.access}`,
  },
});

// 3. Renovar token quando expirar
const refreshResponse = await fetch("/api/auth/token/refresh/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ refresh: tokens.refresh }),
});
const newTokens = await refreshResponse.json();
```

---

## Códigos de Status HTTP

- **200 OK**: Sucesso
- **201 Created**: Recurso criado com sucesso
- **400 Bad Request**: Dados inválidos
- **401 Unauthorized**: Não autenticado
- **403 Forbidden**: Sem permissão
- **404 Not Found**: Recurso não encontrado
- **500 Internal Server Error**: Erro no servidor

---

## Validações

### Registro de Usuário:

- ✅ Username único
- ✅ Email único e válido
- ✅ Senha forte (mínimo 8 caracteres, letras e números)
- ✅ Senhas devem coincidir
- ✅ CNPJ único (para Transportadora)
- ✅ Company name obrigatório (para Transportadora)

### Login:

- ✅ Credenciais válidas
- ✅ Conta ativa

### Alteração de Senha:

- ✅ Senha antiga correta
- ✅ Nova senha forte
- ✅ Senhas devem coincidir
