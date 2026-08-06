# django-sabia-auth

![PyPI Version](https://img.shields.io/pypi/v/django-sabia-auth)
[![PyPI version](https://badge.fury.io/py/django-sabia-auth.svg)](https://pypi.org/project/django-sabia-auth/)
[![Tests](https://github.com/kelsoncm/django-sabia-auth/actions/workflows/test.yml/badge.svg)](https://github.com/kelsoncm/django-sabia-auth/actions/workflows/test.yml)
[![Coverage](https://codecov.io/gh/kelsoncm/django-sabia-auth/branch/main/graph/badge.svg)](https://codecov.io/gh/kelsoncm/django-sabia-auth)
[![Python CI and PyPI Deploy](https://github.com/kelsoncm/django-sabia-auth/actions/workflows/publish.yml/badge.svg)](https://github.com/kelsoncm/django-sabia-auth/actions/workflows/publish.yml)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-sabia-auth.svg)](https://pypi.org/project/django-sabia-auth/)
[![Django Versions](https://img.shields.io/badge/django-5.2-blue.svg)](https://www.djangoproject.com/)
[![Django Versions](https://img.shields.io/badge/django-6.0-blue.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


Django OAuth2 authentication backend for **Sabiá**, Brazil's SUS (Sistema Único de Saúde) identity provider, hosted at [login.sabia.ufrn.br](https://login.sabia.ufrn.br).

## Installation

```bash
uv add django-sabia-auth
# or via pip:
# pip install django-sabia-auth
```

## Configuration

Add to `INSTALLED_APPS` and configure settings:

```python
INSTALLED_APPS = [
    ...
    "django_sabia_auth",
]

AUTHENTICATION_BACKENDS = [
    "django_sabia_auth.backends.SabiaAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
]

SABIA_CLIENT_ID = "your-client-id"
SABIA_CLIENT_SECRET = "your-client-secret"
SABIA_REDIRECT_URI = "https://yourapp.example.com/auth/sabia/callback/"
SABIA_SCOPES = ["cpf", "email"]  # optional, these are the defaults
LOGIN_REDIRECT_URL = "/dashboard/"
LOGIN_URL = "/login/"
```

## URL Setup

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path("auth/sabia/", include("django_sabia_auth.urls")),
    ...
]
```

## Usage

Add a login button to your template:

```html
<a href="{% url 'sabia_auth:login' %}">Login with Sabiá</a>
```

## Documentation

Full documentation is available in the [`docs/`](docs/) directory.

## Sabiá Developer Portal

For API credentials, visit the [Sabiá developer page](https://login.sabia.ufrn.br).

## License

MIT © 2026 kelsoncm
