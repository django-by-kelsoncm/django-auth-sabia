# Pipeline de Busca e Mapeamento de Perfil

O `django-sabia-auth` utiliza o padrão de projeto **Chain of Responsibility (Cadeia de Responsabilidade)** para busca de dados (`SABIA_USER_INFO_FETCHERS`) e mapeamento de atributos (`SABIA_USER_INFO_MAPPERS`).

---

## 1. Cadeia de Busca (`SABIA_USER_INFO_FETCHERS`)

O elo padrão `DefaultEndpointsUserInfoFetcher` consome os endpoints listados em `SABIA_USER_INFO_ENDPOINTS`:

```python
SABIA_USER_INFO_ENDPOINTS = [
    "/api/perfil/dados/",
]
```

Você pode estender a cadeia `SABIA_USER_INFO_FETCHERS` no `settings.py` para consultar APIs externas ou LDAP:

```python
# meu_app/fetchers.py
from django_sabia_auth.fetchers import BaseUserInfoFetcher

class ExternalLdapFetcher(BaseUserInfoFetcher):
    def fetch(self, client, access_token, user_info=None):
        user_info = super().fetch(client, access_token, user_info)
        cpf = user_info.get("cpf")
        if cpf:
            user_info["ldap"] = meu_ldap.buscar_por_cpf(cpf)
        return user_info
```

```python
# settings.py
SABIA_USER_INFO_FETCHERS = [
    "django_sabia_auth.fetchers.DefaultEndpointsUserInfoFetcher",
    "meu_app.fetchers.ExternalLdapFetcher",
]
```

---

## 2. Cadeia de Mapeamento (`SABIA_USER_INFO_MAPPERS`)

O elo padrão `DefaultAttrMapUserMapper` aplica o dicionário de regras `SABIA_USER_ATTR_MAP`:

```python
SABIA_USER_INFO_MAPPERS = [
    "django_sabia_auth.mappers.DefaultAttrMapUserMapper",
]

SABIA_USER_ATTR_MAP = {
    "username": "cpf",
    "email": "email",
    "cpf": {
        "key": "cpf",
        "transform": "django_sabia_auth.transformers.format_cpf",
    },
    "foto": {
        "key": "foto_url",
        "transform": "django_sabia_auth.transformers.fetch_image_file",
    },
}
```
