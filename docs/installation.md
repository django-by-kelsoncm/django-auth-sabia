# Installation

## Requirements

- Python >= 3.11
- Django >= 5.2
- requests >= 2.31

## Install via uv (recommended)

```bash
uv add django-sabia-auth
```

## Install via pip

```bash
pip install django-sabia-auth
```

## Install from source

```bash
git clone https://github.com/kelsoncm/django-sabia-auth.git
cd django-sabia-auth
uv pip install -e ".[dev]" # or pip install -e ".[dev]"
```

## Add to Django

Add `django_sabia_auth` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "django_sabia_auth",
]
```
