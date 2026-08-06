import inspect
import logging

from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)

DEFAULT_SABIA_ENDPOINTS = [
    "/api/perfil/dados/",
]


def resolve_callable_or_class(target):
    """Resolve a callable, class, or python import path string."""
    if callable(target):
        return target
    if isinstance(target, str):
        return import_string(target)
    raise TypeError(f"Expected callable, class, or import path string, got {type(target)}")


class BaseUserInfoFetcher:
    """Base class for User Info Fetchers in the Chain of Responsibility."""

    def __init__(self, sabia_settings=None):
        self.sabia_settings = sabia_settings or {}

    def fetch(self, client, access_token, user_info=None):
        if user_info is None:
            user_info = {}
        return user_info


class DefaultEndpointsUserInfoFetcher(BaseUserInfoFetcher):
    """Fetcher link that iterates over SABIA_USER_INFO_ENDPOINTS and merges profile data."""

    def fetch(self, client, access_token, user_info=None):
        if user_info is None:
            user_info = {}

        endpoints = self.sabia_settings.get("user_info_endpoints", DEFAULT_SABIA_ENDPOINTS)

        for endpoint_spec in endpoints:
            try:
                if isinstance(endpoint_spec, str):
                    url_path = endpoint_spec
                    data = client.get_endpoint_data(access_token, url_path)
                    if isinstance(data, dict):
                        user_info.update(data)

                elif isinstance(endpoint_spec, dict):
                    url_path = endpoint_spec.get("endpoint")
                    namespace = endpoint_spec.get("namespace")
                    extract_list = endpoint_spec.get("extract_list")

                    if not url_path:
                        continue

                    data = client.get_endpoint_data(access_token, url_path)

                    if extract_list and isinstance(data, dict):
                        data_to_store = data.get(extract_list, [])
                    else:
                        data_to_store = data

                    if namespace:
                        user_info[namespace] = data_to_store
                    elif isinstance(data_to_store, dict):
                        user_info.update(data_to_store)
            except Exception as exc:
                logger.warning("Failed to fetch Sabiá user info endpoint '%s': %s", endpoint_spec, exc)
                # Re‑raise to allow the client to surface SabiaUserInfoError
                raise

        return user_info


def get_user_info_fetchers(cfg=None):
    """Instantiate and return the list of fetchers in the Chain of Responsibility."""
    from .utils import get_sabia_settings

    if cfg is None:
        cfg = get_sabia_settings()

    fetcher_targets = cfg.get(
        "user_info_fetchers", ["django_sabia_auth.fetchers.DefaultEndpointsUserInfoFetcher"]
    )
    fetchers = []

    for target in fetcher_targets:
        cls = resolve_callable_or_class(target)
        if inspect.isclass(cls):
            fetchers.append(cls(sabia_settings=cfg))
        elif callable(cls):
            fetchers.append(cls)

    return fetchers


def run_user_info_fetcher_chain(client, access_token, cfg=None):
    """Execute the Chain of Responsibility for fetching user profile info."""
    fetchers = get_user_info_fetchers(cfg)
    user_info = {}

    for fetcher in fetchers:
        if hasattr(fetcher, "fetch"):
            user_info = fetcher.fetch(client, access_token, user_info)
        elif callable(fetcher):
            user_info = fetcher(client, access_token, user_info)

    return user_info
