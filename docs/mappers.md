# Mappers (Mapeamento de Atributos do Sabiá)

O `django-sabia-auth` utiliza o padrão **Chain of Responsibility (Cadeia de Responsabilidade)** para converter o dicionário de atributos do usuário retornado pelo Sabiá (`user_info`) em campos do modelo `User` do Django.

---

## Como Funcionam os Mappers

A cadeia de mappers (`SABIA_USER_INFO_MAPPERS`) é executada imediatamente após a consulta dos fetchers. Cada mapper recebe o dicionário `user_info` unificado e o dicionário de campos `attrs` a ser aplicado no modelo `User`.

```
[user_info consolidado] ──> Mapper 1 (DefaultAttrMapUserMapper)
                                │ attrs = {'username': '12345678900', 'email': '...'}
                                ▼
                            Mapper 2 (Mapper Customizado / Permissões)
                                │ attrs final
                                ▼
                            SabiaAuthBackend (get_or_create)
```

---

## Configuração: `SABIA_USER_INFO_MAPPERS`

No `settings.py`, configure a lista de mappers:

```python
SABIA_USER_INFO_MAPPERS = [
    "django_sabia_auth.mappers.DefaultAttrMapUserMapper",
    "meu_app.mappers.CustomSabiaMapper",
]
```

---

## Mapper Padrão: `DefaultAttrMapUserMapper`

O mapper padrão aplica as regras definidas no dicionário `SABIA_USER_ATTR_MAP`.

### Formatos de Regras em `SABIA_USER_ATTR_MAP`

#### 1. Mapeamento Direto ou Dotted Path
```python
SABIA_USER_ATTR_MAP = {
    "username": "cpf",       # CPF do profissional no Sabiá
    "email": "email",
    "cnes": "vinculo.cnes",  # acessa dicionário aninhado
}
```

#### 2. Dicionário Bruto Completo (`fulljson`)
```python
SABIA_USER_ATTR_MAP = {
    "sabia_data": "fulljson", # atribui o dict user_info completo ao campo
}
```

#### 3. Divisão de Nome Completo (Tupla)
```python
SABIA_USER_ATTR_MAP = {
    ("first_name", "last_name"): "name",
    # "João Silva Santos" -> first_name="João", last_name="Silva Santos"
}
```

#### 4. Lambdas e Callables Customizados
```python
SABIA_USER_ATTR_MAP = {
    "is_staff": lambda info: info.get("perfil") == "Administrador",
}
```

#### 5. Especificação com Transformadores (`dict` spec)
```python
SABIA_USER_ATTR_MAP = {
    "cpf_formatado": {
        "key": "cpf",
        "transform": "django_sabia_auth.transformers.format_cpf",
    },
    "foto": {
        "key": "foto_url",
        "transform": "django_sabia_auth.transformers.fetch_image_file",
    },
}
```

---

## Transformadores Embutidos (`django_sabia_auth.transformers`)

- `fetch_image_file`: baixa a imagem e retorna um `ContentFile` do Django.
- `parse_date`: converte string de data ISO em `datetime.date`.
- `format_cpf`: formata CPF (`XXX.XXX.XXX-XX`).
- `to_upper` / `to_lower` / `to_bool`.

---

## Criando um Mapper Customizado

Para criar um mapper customizado, herde de `BaseUserMapper` (ou do seu alias `BaseSabiaUserMapper`):

```python
# meu_app/mappers.py
from django_sabia_auth.mappers import BaseUserMapper

class CustomSabiaMapper(BaseUserMapper):
    """Mapper que atribui permissões com base no perfil de saúde do Sabiá."""

    def map_attributes(self, user_info, attrs=None):
        attrs = super().map_attributes(user_info, attrs)
        
        # Exemplo: define is_staff para gestores de saúde
        if user_info.get("is_gestor"):
            attrs["is_staff"] = True
            
        return attrs
```

---

## Funções Utilitárias da API de Mappers

- `get_user_info_mappers(cfg=None)`: retorna a lista de instâncias dos mappers configurados.
- `run_user_info_mapper_chain(user_info, attr_map=None, cfg=None)`: executa a cadeia de mappers e retorna o dicionário `attrs` final.
