import secrets

from django.core.exceptions import ImproperlyConfigured

# Default mapping: user model field → Sabiá response key.
DEFAULT_USER_ATTR_MAP = {
    "username": "cpf",
    "email": "email",
    ("first_name", "last_name"): "name",
}

DEFAULT_SABIA_ENDPOINTS = [
    "/api/v1/userinfo",
]


def get_sabia_settings():
    """Read and validate Sabiá settings from Django settings."""
    from django.conf import settings

    client_id = getattr(settings, "SABIA_CLIENT_ID", None)
    client_secret = getattr(settings, "SABIA_CLIENT_SECRET", None)
    redirect_uri = getattr(settings, "SABIA_REDIRECT_URI", None)

    missing = []
    if not client_id:
        missing.append("SABIA_CLIENT_ID")
    if not client_secret:
        missing.append("SABIA_CLIENT_SECRET")
    if not redirect_uri:
        missing.append("SABIA_REDIRECT_URI")

    if missing:
        raise ImproperlyConfigured(f"Missing required Sabiá settings: {', '.join(missing)}")

    user_mapper_setting = getattr(settings, "SABIA_USER_MAPPER", None)
    user_info_mappers = getattr(settings, "SABIA_USER_INFO_MAPPERS", None)

    if user_info_mappers is None:
        if user_mapper_setting:
            user_info_mappers = [user_mapper_setting]
        else:
            user_info_mappers = ["django_sabia_auth.mappers.DefaultAttrMapUserMapper"]

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "scopes": getattr(settings, "SABIA_SCOPES", ["cpf", "email"]),
        "base_url": getattr(settings, "SABIA_BASE_URL", "https://login.sabia.ufrn.br"),
        "api_url": getattr(settings, "SABIA_API_URL", "https://api.sabia.ufrn.br"),
        "user_lookup_field": getattr(settings, "SABIA_USER_LOOKUP_FIELD", "username"),
        "user_attr_map": getattr(settings, "SABIA_USER_ATTR_MAP", DEFAULT_USER_ATTR_MAP),
        "user_info_fetchers": getattr(
            settings,
            "SABIA_USER_INFO_FETCHERS",
            ["django_sabia_auth.fetchers.DefaultEndpointsUserInfoFetcher"],
        ),
        "user_info_endpoints": getattr(settings, "SABIA_USER_INFO_ENDPOINTS", DEFAULT_SABIA_ENDPOINTS),
        "user_info_mappers": user_info_mappers,
    }


def _extract_nested(data, dotted_key):
    """Extract a value from a (possibly nested) dict using a dotted key path."""
    from .mappers import _extract_nested as mapper_extract
    return mapper_extract(data, dotted_key)


def get_user_mapper(cfg=None):
    """Instantiate and return the configured Sabiá user mapper chain or first mapper."""
    from .mappers import get_user_info_mappers
    mappers = get_user_info_mappers(cfg)
    return mappers[0] if mappers else None


def apply_user_attr_map(user_info, attr_map, cfg=None):
    """Translate a Sabiá user_info dict into a flat dict of user model field→value pairs.

    Executes the configured SABIA_USER_INFO_MAPPERS Chain of Responsibility.
    """
    from .mappers import run_user_info_mapper_chain
    return run_user_info_mapper_chain(user_info, attr_map, cfg=cfg)


def get_oauth2_client():
    """Return a SabiaOAuth2Client configured from Django settings."""
    from .client import SabiaOAuth2Client

    cfg = get_sabia_settings()
    return SabiaOAuth2Client(
        client_id=cfg["client_id"],
        client_secret=cfg["client_secret"],
        redirect_uri=cfg["redirect_uri"],
        scopes=cfg["scopes"],
        base_url=cfg["base_url"],
    )


def get_api_client():
    """Return a SabiaAPIClient configured from Django settings."""
    from .client import SabiaAPIClient

    cfg = get_sabia_settings()
    return SabiaAPIClient(client_id=cfg["client_id"], base_url=cfg["api_url"])


def generate_state():
    """Generate a cryptographically secure random state token for OAuth2 CSRF protection."""
    return secrets.token_urlsafe(32)
