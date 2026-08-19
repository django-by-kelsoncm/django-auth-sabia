SECRET_KEY = "test-secret-key-not-for-production"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django_sabia_auth",
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
SABIA_CLIENT_ID = "test-client-id"
SABIA_CLIENT_SECRET = "test-client-secret"
SABIA_REDIRECT_URI = "http://localhost:8000/auth/sabia/callback/"
AUTHENTICATION_BACKENDS = ["django_sabia_auth.backends.SabiaAuthBackend"]
LOGIN_REDIRECT_URL = "/dashboard/"
LOGIN_URL = "/login/"
ROOT_URLCONF = "tests.urls"
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
SESSION_ENGINE = "django.contrib.sessions.backends.db"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ]
        },
    }
]
MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
