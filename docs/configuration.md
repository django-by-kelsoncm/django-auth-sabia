# Configuration

## Required Settings

| Setting | Description |
|---------|-------------|
| `SABIA_CLIENT_ID` | Your OAuth2 client ID from Sabiá |
| `SABIA_CLIENT_SECRET` | Your OAuth2 client secret from Sabiá |
| `SABIA_REDIRECT_URI` | The callback URL registered with Sabiá |

## Optional Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `SABIA_SCOPES` | `["cpf", "email"]` | OAuth2 scopes to request. See [Scopes](scopes.md) for all options. |
| `SABIA_BASE_URL` | `https://login.sabia.ufrn.br` | Sabiá OAuth2 base URL |
| `SABIA_API_URL` | `https://api.sabia.ufrn.br` | Sabiá user management API base URL |
| `SABIA_USER_LOOKUP_FIELD` | `"username"` | User model field used to look up/create users |
| `SABIA_USER_ATTR_MAP`     | see below | Maps Sabiá response keys to user model fields |
| `SABIA_USER_INFO_FETCHERS` | `["django_sabia_auth.fetchers.DefaultEndpointsUserInfoFetcher"]` | List of fetcher classes in Chain of Responsibility |
| `SABIA_USER_INFO_ENDPOINTS` | `["/api/perfil/dados/"]` | List of Sabiá API endpoints to query and merge |
| `SABIA_USER_INFO_MAPPERS` | `["django_sabia_auth.mappers.DefaultAttrMapUserMapper"]` | List of mapper classes in Chain of Responsibility |
| `SABIA_USER_MAPPER`       | `"django_sabia_auth.mappers.DefaultSabiaUserMapper"` | Custom mapper class path or class (legacy alias) |

## Authentication Backend

```python
AUTHENTICATION_BACKENDS = [
    "django_sabia_auth.backends.SabiaAuthBackend",
    "django.contrib.auth.backends.ModelBackend",  # optional, for admin
]
```

## Basic Example

```python
SABIA_CLIENT_ID = "my-client-id"
SABIA_CLIENT_SECRET = "my-client-secret"
SABIA_REDIRECT_URI = "https://myapp.com/auth/sabia/callback/"
SABIA_SCOPES = ["cpf", "email"]
LOGIN_REDIRECT_URL = "/dashboard/"
LOGIN_URL = "/login/"
```

---

## User Model Mapping

### Default behavior

When using Django's default `User` model (no custom `AUTH_USER_MODEL`), the library works
out of the box. It looks up users by `username` (storing the CPF there) and maps:

| Sabiá field | User model field | Notes                       |
|-------------|------------------|-----------------------------|
| `cpf`       | `username`       | Used as the lookup key      |
| `email`     | `email`          |                             |
| `name`      | `first_name` + `last_name` | Split on the first space |

---

### Mapeamentos Avançados (`SABIA_USER_ATTR_MAP`)

#### 1. Lambdas e Callables
```python
SABIA_USER_ATTR_MAP = {
    "username": "cpf",
    "full_name": lambda info: f"Dr(a). {info.get('name')}",
}
```

#### 2. Dicionários de Especificação (`dict` spec) e Transformadores
```python
SABIA_USER_ATTR_MAP = {
    "username": "cpf",
    "cpf": {
        "key": "cpf",
        "transform": "django_sabia_auth.transformers.format_cpf",
    },
    "data_nascimento": {
        "key": "receita_federal.dtNascimento",
        "transform": "django_sabia_auth.transformers.parse_date",
    },
}
```

#### 3. Mapeamento de Fotos (URL vs Download para ImageField)
```python
# Apenas a URL
SABIA_USER_ATTR_MAP = {
    "foto_url": "foto_url",
}

# Download e salvamento em ImageField / FileField do Django:
SABIA_USER_ATTR_MAP = {
    "foto": {
        "key": "foto_url",
        "transform": "django_sabia_auth.transformers.fetch_image_file",
    },
}
```

#### Transformadores Embutidos (`django_sabia_auth.transformers`)
- `fetch_image_file`: baixa a imagem e retorna um `ContentFile` do Django.
- `parse_date`: converte string de data ISO em `datetime.date`.
- `format_cpf`: formata CPF (`XXX.XXX.XXX-XX`).
- `to_upper` / `to_lower` / `to_bool`.

---

### Class-Based Mapper Customizado (`SABIA_USER_MAPPER`)

```python
# mappers.py
from django_sabia_auth.mappers import BaseSabiaUserMapper

class CustomSabiaUserMapper(BaseSabiaUserMapper):
    def map_attributes(self, user_info, attr_map=None):
        attrs = super().map_attributes(user_info, attr_map)
        attrs["custom_field"] = True
        return attrs
```

```python
# settings.py
SABIA_USER_MAPPER = "meu_app.mappers.CustomSabiaUserMapper"
```
