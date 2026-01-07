# 🔥 RPG Game Generator - Backend API

<p align="center">
  <img alt="FastAPI" height="80" width="80" src="https://raw.githubusercontent.com/devicons/devicon/master/icons/fastapi/fastapi-original.svg">
  <img alt="Firebase" height="80" width="80" src="https://raw.githubusercontent.com/devicons/devicon/master/icons/firebase/firebase-plain.svg">
  <img alt="Python" height="80" width="80" src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg">
</p>

<p align="center">
  <em>API RESTful para geração de histórias interativas de RPG com IA</em>
</p>

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Stack Tecnológica](#-stack-tecnológica)
- [Arquitetura do Sistema](#-arquitetura-do-sistema)
- [Estrutura de Pastas](#-estrutura-de-pastas)
- [Modelo de Dados](#-modelo-de-dados)
- [Endpoints da API](#-endpoints-da-api)
- [Fluxo de Autenticação](#-fluxo-de-autenticação)
- [Sistema de Energias (Tokens)](#-sistema-de-energias-tokens)
- [Fluxo de Assinaturas](#-fluxo-de-assinaturas-stripe)
- [Diagramas](#-diagramas)
- [Configuração e Instalação](#-configuração-e-instalação)
- [Variáveis de Ambiente](#-variáveis-de-ambiente)

---

## 🎯 Visão Geral

Backend responsável por gerenciar:
- ✅ Autenticação e autorização de usuários
- 🎮 Geração de histórias interativas com OpenAI GPT
- 💎 Sistema de energias (tokens) para gamificação
- 💳 Integração com Stripe para assinaturas
- 📚 Histórico e continuidade de histórias
- 👤 Gerenciamento de perfil de usuário

---

## 🛠️ Stack Tecnológica

| Tecnologia | Versão | Função |
|------------|--------|--------|
| **Python** | 3.11+ | Linguagem base |
| **FastAPI** | 0.104+ | Framework web |
| **Firebase Admin** | 6.2+ | Firestore, Auth |
| **OpenAI API** | 1.3+ | Geração de histórias |
| **Stripe** | 7.0+ | Pagamentos e assinaturas |
| **PyJWT** | 2.8+ | Tokens JWT |
| **Pydantic** | 2.4+ | Validação de dados |
| **Uvicorn** | 0.24+ | Servidor ASGI |

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENTE (Flutter App)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTPS + JWT
                         │
┌────────────────────────▼────────────────────────────────────┐
│                      FASTAPI SERVER                         │
│  ┌──────────────────────────────────────────────────┐      │
│  │              Middleware Layer                     │      │
│  │  • CORS                                           │      │
│  │  • JWT Authentication                             │      │
│  │  • Rate Limiting                                  │      │
│  │  • Request Validation                             │      │
│  └──────────────┬───────────────────────────────────┘      │
│                 │                                            │
│  ┌──────────────▼───────────────────────────────────┐      │
│  │              Router Layer                         │      │
│  │  • /auth     (Autenticação)                      │      │
│  │  • /users    (Perfil)                            │      │
│  │  • /stories  (Histórias)                         │      │
│  │  • /payment  (Assinaturas)                       │      │
│  └──────────────┬───────────────────────────────────┘      │
│                 │                                            │
│  ┌──────────────▼───────────────────────────────────┐      │
│  │            Service Layer                          │      │
│  │  • AuthService                                    │      │
│  │  • StoryService                                   │      │
│  │  • PaymentService                                 │      │
│  │  • EnergyService                                  │      │
│  └──────────────┬───────────────────────────────────┘      │
└─────────────────┼───────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼────────┐  ┌──────▼───────┐  ┌────────────┐
│   FIREBASE     │  │   OPENAI     │  │   STRIPE   │
│   FIRESTORE    │  │   GPT-4      │  │  PAYMENTS  │
│                │  │              │  │            │
│ • users        │  │ • História   │  │ • Subs     │
│ • stories      │  │ • Opções     │  │ • Plans    │
│ • transactions │  │ • Continue   │  │ • Invoices │
└────────────────┘  └──────────────┘  └────────────┘
```

---

## 📁 Estrutura de Pastas

```
rpg-backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # 🚀 Ponto de entrada da API
│   │
│   ├── config/                    # ⚙️ Configurações
│   │   ├── __init__.py
│   │   ├── settings.py           # Variáveis de ambiente
│   │   ├── firebase.py           # Inicialização Firebase
│   │   └── openai_client.py      # Cliente OpenAI
│   │
│   ├── models/                    # 📦 Modelos Pydantic
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── story.py
│   │   ├── subscription.py
│   │   └── energy.py
│   │
│   ├── schemas/                   # 📋 Schemas de requisição/resposta
│   │   ├── __init__.py
│   │   ├── auth_schemas.py
│   │   ├── story_schemas.py
│   │   ├── user_schemas.py
│   │   └── payment_schemas.py
│   │
│   ├── services/                  # 💼 Lógica de negócios
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── story_service.py
│   │   ├── user_service.py
│   │   ├── energy_service.py
│   │   ├── openai_service.py
│   │   └── payment_service.py
│   │
│   ├── routers/                   # 🛣️ Endpoints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── stories.py
│   │   └── payments.py
│   │
│   ├── middlewares/               # 🔒 Middlewares
│   │   ├── __init__.py
│   │   ├── auth_middleware.py
│   │   └── rate_limiter.py
│   │
│   └── utils/                     # 🛠️ Utilitários
│       ├── __init__.py
│       ├── security.py           # JWT, hash senha
│       ├── validators.py
│       └── exceptions.py
│
├── tests/                         # 🧪 Testes
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_stories.py
│   └── test_payments.py
│
├── firebase-admin-sdk.json        # 🔐 Credenciais Firebase
├── requirements.txt               # 📋 Dependências
├── .env                          # 🔐 Variáveis de ambiente
├── .gitignore
└── README.md
```

---

## 💾 Modelo de Dados

### 📊 Estrutura do Firebase Firestore

```
📁 Firestore Database
│
├── 📂 users/
│   └── {user_id}/
│       ├── username: string
│       ├── email: string
│       ├── password_hash: string
│       ├── created_at: timestamp
│       ├── updated_at: timestamp
│       ├── avatar_url: string | null
│       ├── energy: number (default: 100)
│       ├── max_energy: number (default: 100)
│       ├── subscription_tier: string ("free" | "basic" | "premium" | "ultimate")
│       ├── subscription_status: string ("active" | "inactive" | "canceled")
│       └── stripe_customer_id: string | null
│
├── 📂 stories/
│   └── {story_id}/
│       ├── user_id: string
│       ├── title: string
│       ├── theme: string
│       ├── character_description: string
│       ├── created_at: timestamp
│       ├── updated_at: timestamp
│       ├── status: string ("in_progress" | "completed" | "abandoned")
│       ├── total_chapters: number
│       ├── current_chapter: number
│       ├── energy_cost: number
│       └── chapters: array[
│           {
│               chapter_number: number,
│               content: string,
│               choices: array[string],
│               selected_choice: number | null,
│               timestamp: timestamp
│           }
│       ]
│
├── 📂 subscriptions/
│   └── {subscription_id}/
│       ├── user_id: string
│       ├── stripe_subscription_id: string
│       ├── plan_name: string
│       ├── plan_price: number
│       ├── energy_bonus: number
│       ├── status: string
│       ├── current_period_start: timestamp
│       ├── current_period_end: timestamp
│       └── cancel_at_period_end: boolean
│
└── 📂 transactions/
    └── {transaction_id}/
        ├── user_id: string
        ├── type: string ("story_creation" | "story_continuation" | "subscription_purchase")
        ├── energy_spent: number
        ├── story_id: string | null
        ├── amount: number | null
        ├── timestamp: timestamp
        └── description: string
```

---

## 🛣️ Endpoints da API

### 🔐 Autenticação (`/api/v1/auth`)

```
POST   /auth/register
POST   /auth/login
POST   /auth/refresh
POST   /auth/logout
POST   /auth/forgot-password
POST   /auth/reset-password
```

### 👤 Usuários (`/api/v1/users`)

```
GET    /users/me
PUT    /users/me
GET    /users/me/energy
GET    /users/me/subscription
DELETE /users/me
```

### 📚 Histórias (`/api/v1/stories`)

```
POST   /stories/create
POST   /stories/{story_id}/continue
GET    /stories
GET    /stories/{story_id}
DELETE /stories/{story_id}
PUT    /stories/{story_id}/status
```

### 💳 Pagamentos (`/api/v1/payments`)

```
GET    /payments/plans
POST   /payments/create-subscription
POST   /payments/cancel-subscription
POST   /payments/webhook
GET    /payments/history
```

---

## 🔒 Fluxo de Autenticação

```
┌──────────────┐
│   CLIENTE    │
└──────┬───────┘
       │
       │ 1. POST /auth/register
       │    { username, email, password, confirm_password }
       │
┌──────▼──────────────────────────────────────────────┐
│  BACKEND - Validação                                │
│  • Verifica se email já existe                      │
│  • Valida formato email                             │
│  • Verifica senha == confirm_password               │
│  • Hash da senha (bcrypt)                           │
└──────┬──────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────┐
│  FIREBASE                                            │
│  • Cria documento em /users/{user_id}               │
│  • Define energy inicial = 100                      │
│  • subscription_tier = "free"                       │
└──────┬──────────────────────────────────────────────┘
       │
       │ 2. Retorna sucesso
       │
┌──────▼───────┐
│   CLIENTE    │
│              │
│ 3. POST /auth/login
│    { email, password }
└──────┬───────┘
       │
┌──────▼──────────────────────────────────────────────┐
│  BACKEND - Autenticação                             │
│  • Busca usuário no Firestore por email            │
│  • Verifica hash da senha                           │
│  • Gera JWT Token (expires: 24h)                   │
│  • Gera Refresh Token (expires: 7d)                │
└──────┬──────────────────────────────────────────────┘
       │
       │ 4. Retorna tokens
       │    { 
       │      access_token,
       │      refresh_token,
       │      user_data 
       │    }
       │
┌──────▼───────┐
│   CLIENTE    │
│  • Armazena  │
│    tokens    │
└──────────────┘
```

---

## ⚡ Sistema de Energias (Tokens)

### 💎 Conceito

As **Energias Mágicas** são a moeda do jogo. Cada ação consome energia:

| Ação | Custo de Energia |
|------|------------------|
| Criar nova história | 20 ⚡ |
| Continuar história (por capítulo) | 10 ⚡ |

### 📊 Recarregamento de Energia

```
┌─────────────────────────────────────────────────────┐
│              PLANOS DE ASSINATURA                   │
├──────────────┬──────────┬────────────┬──────────────┤
│ Plano        │ Energia  │ Preço/Mês  │ Benefícios   │
├──────────────┼──────────┼────────────┼──────────────┤
│ Free         │ 100 ⚡   │ R$ 0,00    │ • Básico     │
│              │          │            │ • 5 histórias│
├──────────────┼──────────┼────────────┼──────────────┤
│ Basic        │ 300 ⚡   │ R$ 19,90   │ • +Histórias │
│              │ /mês     │            │ • Recarga    │
├──────────────┼──────────┼────────────┼──────────────┤
│ Premium      │ 600 ⚡   │ R$ 34,90   │ • Ilimitado  │
│              │ /mês     │            │ • Prioridade │
├──────────────┼──────────┼────────────┼──────────────┤
│ Ultimate     │ 1000 ⚡  │ R$ 49,90   │ • Sem limite │
│              │ /mês     │            │ • IA Premium │
└──────────────┴──────────┴────────────┴──────────────┘
```

### 🔄 Fluxo de Verificação de Energia

```
┌──────────────┐
│   USUÁRIO    │
└──────┬───────┘
       │
       │ Tenta criar/continuar história
       │
┌──────▼──────────────────────────────────────┐
│  BACKEND - EnergyService                    │
│                                              │
│  1. Busca energia atual do usuário          │
│  2. Verifica se energia >= custo_ação       │
└──────┬───────────────────┬──────────────────┘
       │                   │
       │ SIM               │ NÃO
       │                   │
┌──────▼────────┐    ┌─────▼─────────────────┐
│  Desconta     │    │  Retorna erro 402     │
│  energia      │    │  {                     │
│               │    │    "message":          │
│  Executa ação │    │    "Energias          │
│               │    │     insuficientes!",   │
│  Registra em  │    │    "current": 5,       │
│  transactions │    │    "required": 20      │
│               │    │  }                     │
└───────────────┘    └───────────────────────┘
```

---

## 💳 Fluxo de Assinaturas (Stripe)

```
┌─────────────────────────────────────────────────────────┐
│                   1. USUÁRIO SELECIONA PLANO             │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ POST /payments/create-subscription
                         │ { plan_id: "premium" }
                         │
┌────────────────────────▼────────────────────────────────┐
│  BACKEND - PaymentService                               │
│                                                          │
│  1. Verifica se já tem Stripe Customer                  │
│  2. Se não, cria: stripe.Customer.create()              │
│  3. Cria Checkout Session:                              │
│     stripe.checkout.Session.create({                    │
│       customer: customer_id,                            │
│       mode: 'subscription',                             │
│       line_items: [{ price: price_id }],                │
│       success_url: 'app://payment/success',             │
│       cancel_url: 'app://payment/cancel'                │
│     })                                                   │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ Retorna checkout_url
                         │
┌────────────────────────▼────────────────────────────────┐
│  CLIENTE abre checkout_url no navegador                 │
│  • Usuário insere dados do cartão                       │
│  • Stripe processa pagamento                            │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ Webhook: checkout.session.completed
                         │
┌────────────────────────▼────────────────────────────────┐
│  POST /payments/webhook (Stripe Webhook)                │
│                                                          │
│  1. Valida assinatura do webhook                        │
│  2. Atualiza Firestore:                                 │
│     • subscription_tier = "premium"                     │
│     • subscription_status = "active"                    │
│     • energy = 600                                      │
│  3. Cria documento em /subscriptions/                   │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ Notifica usuário
                         │
┌────────────────────────▼────────────────────────────────┐
│  USUÁRIO recebe confirmação                             │
│  • Energia atualizada                                   │
│  • Acesso aos benefícios premium                        │
└─────────────────────────────────────────────────────────┘
```

---

## 🎮 Fluxo de Criação de História

```
┌──────────────────────────────────────────────────────────┐
│  1. USUÁRIO INICIA NOVA HISTÓRIA                         │
│     POST /stories/create                                 │
│     {                                                     │
│       "theme": "Aventura medieval",                      │
│       "character_description": "Guerreiro corajoso..."   │
│     }                                                     │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│  2. BACKEND - Verificação                                │
│     • Verifica JWT                                       │
│     • Checa energia (precisa de 20⚡)                    │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│  3. OPENAI SERVICE                                       │
│                                                          │
│     Prompt para GPT-4:                                   │
│     """                                                  │
│     Você é um mestre de RPG. Crie o início de uma       │
│     história com tema: {theme}                           │
│     Personagem: {character_description}                  │
│                                                          │
│     Formato da resposta:                                 │
│     {                                                    │
│       "chapter_content": "texto da história...",         │
│       "choices": [                                       │
│         "Opção 1: ...",                                  │
│         "Opção 2: ..."                                   │
│       ]                                                  │
│     }                                                    │
│     """                                                  │
└────────────────────────┬─────────────────────────────────┘
                         │
                         │ Resposta da IA
                         │
┌────────────────────────▼─────────────────────────────────┐
│  4. SALVAR NO FIRESTORE                                  │
│     /stories/{story_id}                                  │
│     {                                                    │
│       user_id,                                           │
│       theme,                                             │
│       character_description,                             │
│       status: "in_progress",                            │
│       chapters: [{                                       │
│         chapter_number: 1,                               │
│         content: "...",                                  │
│         choices: ["...", "..."],                         │
│         selected_choice: null                            │
│       }]                                                 │
│     }                                                    │
│                                                          │
│     • Desconta 20⚡ do usuário                           │
│     • Registra em /transactions                          │
└────────────────────────┬─────────────────────────────────┘
                         │
                         │ Retorna história criada
                         │
┌────────────────────────▼─────────────────────────────────┐
│  5. USUÁRIO VISUALIZA HISTÓRIA                           │
│     • Lê o capítulo                                      │
│     • Vê 2 opções de escolha                             │
└──────────────────────────────────────────────────────────┘
```

### 🔄 Continuação da História

```
┌──────────────────────────────────────────────────────────┐
│  USUÁRIO ESCOLHE UMA OPÇÃO                               │
│  POST /stories/{story_id}/continue                       │
│  { "choice_index": 0 }                                   │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│  BACKEND                                                 │
│  • Verifica energia (10⚡)                               │
│  • Busca história atual                                  │
│  • Atualiza selected_choice do capítulo anterior         │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│  OPENAI SERVICE                                          │
│                                                          │
│  Prompt:                                                 │
│  """                                                     │
│  Continue a história baseado na escolha: {escolha}       │
│  História até agora: {contexto_anterior}                 │
│                                                          │
│  Número de capítulos: {current_chapter}                  │
│  - Se capítulo 2-3: retorne 3 escolhas                  │
│  - Se capítulo 4-5: retorne 4 escolhas                  │
│  - Se capítulo >= 6: considere finalizar história       │
│  """                                                     │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│  ATUALIZA FIRESTORE                                      │
│  • Adiciona novo capítulo ao array                       │
│  • current_chapter++                                     │
│  • Se história finalizou: status = "completed"           │
│  • Desconta 10⚡                                          │
└────────────────────────┬─────────────────────────────────┘
                         │
                         │ Retorna novo capítulo
                         │
┌────────────────────────▼─────────────────────────────────┐
│  USUÁRIO CONTINUA LENDO                                  │
│  • Agora vê 3 ou 4 opções                                │
│  • Processo se repete...                                 │
└──────────────────────────────────────────────────────────┘
```

---

## 📊 Diagrama de Casos de Uso

```
                        ┌─────────────────────┐
                        │   Sistema RPG API   │
                        └──────────┬──────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
┌───────▼────────┐       ┌─────────▼────────┐      ┌────────▼─────────┐
│                │       │                  │      │                  │
│   USUÁRIO      │       │   STRIPE         │      │   OPENAI         │
│   NÃO AUTH    │       │   (Webhook)      │      │   (API)          │
│                │       │                  │      │                  │
└───────┬────────┘       └─────────┬────────┘      └────────┬─────────┘
        │                          │                         │
        │                          │                         │
    UC1: Registrar                 │                         │
    UC2: Login                     │                         │
        │                          │                         │
        └──────────┐               │                         │
                   │               │                         │
            ┌──────▼───────┐       │                         │
            │              │       │                         │
            │   USUÁRIO    │       │                         │
            │ AUTENTICADO  │       │                         │
            │              │       │                         │
            └──────┬───────┘       │                         │
                   │               │                         │
    UC3: Ver perfil               │                         │
    UC4: Editar perfil            │                         │
    UC5: Consultar energia        │                         │
    UC6: Criar história ──────────┼─────────────────────────┤
    UC7: Continuar história ──────┼─────────────────────────┤
    UC8: Listar histórias         │                         │
    UC9: Ver detalhes história    │                         │
    UC10: Deletar história        │                         │
    UC11: Ver planos              │                         │
    UC12: Assinar plano ──────────┤                         │
    UC13: Cancelar assinatura ────┤                         │
    UC14: Ver histórico pagamento │                         │
                   │               │                         │
                   │       UC15: Processar webhook          │
                   │               │                         │
```

---

## 🔐 Segurança e Boas Práticas

### 🛡️ Implementações de Segurança

- **JWT com expiração**: Access token (24h), Refresh token (7 dias)
- **Hash de senha**: bcrypt com salt rounds = 12
- **CORS**: Configurado apenas para domínios permitidos
- **Rate Limiting**: Máximo de requisições por IP/usuário
- **Validação de dados**: Pydantic schemas em todos os endpoints
- **HTTPS obrigatório**: Certificado SSL/TLS
- **Webhook validation**: Assinatura Stripe verificada
- **Environment variables**: Credenciais em .env

---

## ⚙️ Configuração e Instalação

### 1️⃣ Clonar o Repositório

```bash
git clone https://github.com/seuusuario/rpg-backend.git
cd rpg-backend
```

### 2️⃣ Criar Ambiente Virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3️⃣ Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4️⃣ Configurar Firebase

1. Acesse [Firebase Console](https://console.firebase.google.com/)
2. Crie um novo projeto
3. Ative Firestore Database
4. Gere credenciais de Service Account
5. Baixe `firebase-admin-sdk.json` e coloque na raiz

### 5️⃣ Configurar Variáveis de Ambiente

Crie arquivo `.env`:

```bash
# Firebase
FIREBASE_PROJECT_ID=seu-projeto-id
FIREBASE_PRIVATE_KEY_ID=sua-private-key-id
FIREBASE_PRIVATE_KEY=sua-private-key
FIREBASE_CLIENT_EMAIL=seu-client-email

# JWT
JWT_SECRET_KEY=sua-chave-secreta-super-segura
JWT_ALGORITHM=HS256
ACCESS_TOKEN=token 
```


🚀 Fluxo de Implementação - Passo a Passo
Fase 1: Setup Inicial (1-2 dias)
bash# 1. Instalar dependências

pip install stripe pydantic-settings

# 2. Criar conta no Stripe
```bash
# https://dashboard.stripe.com/register

# 3. Configurar produto no Stripe
# Dashboard > Products > Add Product
# Nome: "RPG Premium"
# Preço: R$ 19,99/mês recorrente
# Copiar PRICE_ID

# 4. Criar webhook no Stripe
# Dashboard > Developers > Webhooks > Add endpoint
# URL: https://seu-dominio.com/api/subscriptions/webhook
# Eventos a escutar:
#   - customer.subscription.created
#   - customer.subscription.updated
#   - customer.subscription.deleted
#   - invoice.payment_succeeded
#   - invoice.payment_failed
# Copiar WEBHOOK_SECRET
```

# 5. Adicionar ao .env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...






## Execute : ##
uvicorn app.main:app --reload


# Ativar Ngrok PARA TESTAR WEBHOOK DE PAGAMENTOS : 

ngrok http 8000