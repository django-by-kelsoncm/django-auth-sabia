# Usage

## URL Configuration

Include the Sabiá auth URLs in your project:

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path("auth/sabia/", include("django_sabia_auth.urls")),
]
```

This registers two endpoints:
- `GET /auth/sabia/login/` — initiates the OAuth2 flow
- `GET /auth/sabia/callback/` — handles the OAuth2 callback

## Template Login Button

```html
{% raw %}
<a href="{% url 'sabia_auth:login' %}">Login com Sabiá</a>
{% endraw %}
```

## User Model Integration

When a user authenticates through Sabiá, `django-sabia-auth` will:

1. Look up an existing Django user by CPF (stored as `username`)
2. Create a new user if none is found
3. Update `email`, `first_name`, `last_name` if they changed

## Using the API Client

```python
from django_sabia_auth.utils import get_api_client

api = get_api_client()

# Look up a user
user = api.get_user("12345678901")

# List users by CPF
users = api.list_users(["12345678901", "09876543210"])

# Create a user
created, data = api.create_user(
    cpf="12345678901",
    email="user@example.com",
    nome="João Silva",
    genero="M",
    data_de_nascimento="1990-01-15",
)
```
