# Sandbox — Teste funcional do django-sabia-auth

Este diretório contém um projeto Django **independente** (não faz parte do pacote
`django-sabia-auth`) para testar o funcionamento do pacote usando a interface web do
Django, sem precisar de uma aplicação real.

## Estrutura

```
sandbox/
├── manage.py
├── .env.example          # variáveis de ambiente necessárias
├── config/
│   ├── settings.py       # configurações do projeto
│   ├── urls.py           # URLs raiz
│   └── wsgi.py
└── home/                 # aplicação de demonstração
    ├── views.py
    └── templates/home/
        ├── base.html
        ├── index.html    # página pública
        ├── login.html    # página de login (botão "Entrar com o Sabiá")
        └── dashboard.html # página protegida (requer autenticação)
```

## Pré-requisitos

- Python 3.11+
- Credenciais OAuth2 do Sabiá (Client ID e Client Secret)
- `django-sabia-auth` instalado (instale a partir da raiz do repositório)

## Configuração

### 1. Instale as dependências

A partir da **raiz do repositório**:

```bash
pip install -e ".[dev]"
```

### 2. Configure as variáveis de ambiente

```bash
cd sandbox
cp .env.example .env
# edite o arquivo .env com suas credenciais
```

Ou exporte diretamente no terminal:

```bash
export SABIA_CLIENT_ID="seu-client-id"
export SABIA_CLIENT_SECRET="seu-client-secret"
export SABIA_REDIRECT_URI="http://localhost:8001/auth/sabia/callback/"
```

### 3. Crie o banco de dados

```bash
cd sandbox
python manage.py migrate
python manage.py runserver
```

Acesse: **http://localhost:8000**

## Páginas disponíveis

| URL | Descrição |
|-----|-----------|
| `/` | Página inicial — mostra se o usuário está autenticado |
| `/login/` | Página de login com botão "Entrar com o Sabiá" |
| `/auth/sabia/login/` | Inicia o fluxo OAuth2 (redireciona para o Sabiá) |
| `/auth/sabia/callback/` | Callback OAuth2 (configurar como Redirect URI no Sabiá) |
| `/dashboard/` | Página protegida — exibe dados do usuário autenticado |
| `/logout/` | Encerra a sessão |
| `/admin/` | Interface administrativa do Django |

## Fluxo de teste

1. Acesse `http://localhost:8000`
2. Clique em **Entrar com o Sabiá** → você vai para `/login/`
3. Clique em **Entrar com o Sabiá** → o pacote gera um `state`, salva na sessão e redireciona para o servidor Sabiá
4. Autentique-se no Sabiá com suas credenciais
5. O Sabiá redireciona para `/auth/sabia/callback/` com `code` e `state`
6. O pacote valida o `state`, troca o `code` pelo token de acesso, busca o perfil e cria/atualiza o usuário Django
7. Você é redirecionado para `/dashboard/` já autenticado

## Observações

- O banco de dados `db.sqlite3` é criado dentro de `sandbox/` e já está ignorado pelo `.gitignore`
- Este projeto **não é distribuído** junto com o pacote (veja `pyproject.toml` — só `django_sabia_auth*` é incluído)
- A `SABIA_REDIRECT_URI` cadastrada no portal do Sabiá deve ser exatamente `http://localhost:8001/auth/sabia/callback/`
