# Fetchers (Busca de Dados do Sabiá)

O `django-sabia-auth` utiliza o padrão **Chain of Responsibility (Cadeia de Responsabilidade)** para consultar o endpoint `/api/v1/userinfo` do Sabiá (provedor de identidade do SUS) e endpoints adicionais de APIs ou sistemas corporativos.

---

## Como Funcionam os Fetchers

Após a autenticação via OAuth2, o `access_token` é obtido e a cadeia de fetchers (`SABIA_USER_INFO_FETCHERS`) é executada. Cada fetcher recebe o dicionário acumulado `user_info` e realiza chamadas HTTP ou consultas para enriquecê-lo.

```
[Access Token] ──> Fetcher 1 (DefaultEndpointsUserInfoFetcher)
                       │ user_info obtido do /api/v1/userinfo
                       ▼
                   Fetcher 2 (Fetcher Customizado / LDAP)
                       │ user_info final
                       ▼
                   Cadeia de Mappers
```

---

## Configuração: `SABIA_USER_INFO_FETCHERS`

No `settings.py`, configure a lista de fetchers:

```python
SABIA_CLIENT_ID = "seu-client-id"
SABIA_CLIENT_SECRET = "seu-client-secret"
SABIA_REDIRECT_URI = "https://sua-app.com/auth/sabia/callback/"

SABIA_USER_INFO_FETCHERS = [
    "django_sabia_auth.fetchers.DefaultEndpointsUserInfoFetcher",
    "meu_app.fetchers.ExternalLdapFetcher",
]
```

---

## Fetcher Padrão: `DefaultEndpointsUserInfoFetcher`

O fetcher padrão consome a lista `SABIA_USER_INFO_ENDPOINTS` (por padrão `["/api/v1/userinfo"]`) e efetua chamadas autorizadas para cada endpoint.

### Formatos de Endpoints Suportados (`SABIA_USER_INFO_ENDPOINTS`)

#### 1. Endpoint Simples (String)
```python
SABIA_USER_INFO_ENDPOINTS = [
    "/api/v1/userinfo",
]
```

#### 2. Endpoint com Formatação Dinâmica (String com `{chave}`)
```python
SABIA_USER_INFO_ENDPOINTS = [
    "/api/v1/userinfo",
    "/api/v1/profissionais/{cpf}/vinculos/",
]
```
Chaves `{cpf}`, `{email}`, etc. são preenchidas dinamicamente a partir dos campos presentes em `user_info`.

#### 3. Especificação por Dicionário (`dict` spec)
Permite isolar respostas sob um *namespace*, extrair listas de respostas paginadas ou iterar sobre coleções:

```python
SABIA_USER_INFO_ENDPOINTS = [
    "/api/v1/userinfo",
    {
        "endpoint": "/api/v1/estabelecimentos/",
        "namespace": "estabelecimentos",
        "extract_list": "results",
    },
    {
        "endpoint": "/api/v1/estabelecimentos/{cnes}/detalhes/",
        "namespace": "detalhes_cnes",
        "for_each": "estabelecimentos", # Itera sobre cada item retornado
    },
]
```

---

## Criando um Fetcher Customizado

Para criar um fetcher customizado, herde de `BaseUserInfoFetcher` e sobrescreva o método `fetch`:

```python
# meu_app/fetchers.py
from django_sabia_auth.fetchers import BaseUserInfoFetcher

class ExternalLdapFetcher(BaseUserInfoFetcher):
    """Fetcher que enriquece os dados do profissional consultando o LDAP corporativo via CPF."""

    def fetch(self, client, access_token, user_info=None):
        user_info = super().fetch(client, access_token, user_info)
        
        cpf = user_info.get("cpf")
        if cpf:
            user_info["ldap_info"] = meu_ldap.buscar_por_cpf(cpf)
            
        return user_info
```

---

## Funções Utilitárias da API de Fetchers

- `get_user_info_fetchers(cfg=None)`: retorna a lista de instâncias dos fetchers configurados.
- `run_user_info_fetcher_chain(client, access_token, cfg=None)`: executa toda a cadeia de fetchers e retorna o dicionário `user_info` consolidado.
