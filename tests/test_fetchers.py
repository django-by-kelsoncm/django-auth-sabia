from unittest.mock import MagicMock

from django_sabia_auth.fetchers import BaseUserInfoFetcher, DefaultEndpointsUserInfoFetcher, run_user_info_fetcher_chain
from django_sabia_auth.utils import get_sabia_settings


def test_base_user_info_fetcher():
    fetcher = BaseUserInfoFetcher()
    info = fetcher.fetch(None, "token", {"initial": "val"})
    assert info == {"initial": "val"}


def test_default_endpoints_user_info_fetcher():
    mock_client = MagicMock()
    mock_client.get_endpoint_data.side_effect = lambda token, path: {
        "/api/v1/userinfo": {"cpf": "12345678901", "name": "Maria"},
    }.get(path, {})

    cfg = {
        "user_info_endpoints": [
            "/api/v1/userinfo",
        ]
    }

    fetcher = DefaultEndpointsUserInfoFetcher(sabia_settings=cfg)
    result = fetcher.fetch(mock_client, "fake-access-token")

    assert result["cpf"] == "12345678901"
    assert result["name"] == "Maria"


class CustomExternalLdapFetcher(BaseUserInfoFetcher):
    def fetch(self, client, access_token, user_info=None):
        user_info = super().fetch(client, access_token, user_info)
        user_info["ldap_group"] = "sysadmins"
        return user_info


def test_run_user_info_fetcher_chain(settings):
    settings.SABIA_CLIENT_ID = "test-id"
    settings.SABIA_CLIENT_SECRET = "test-secret"
    settings.SABIA_REDIRECT_URI = "http://localhost/callback/"
    settings.SABIA_USER_INFO_FETCHERS = [
        DefaultEndpointsUserInfoFetcher,
        CustomExternalLdapFetcher,
    ]
    settings.SABIA_USER_INFO_ENDPOINTS = ["/api/v1/userinfo"]

    mock_client = MagicMock()
    mock_client.get_endpoint_data.return_value = {"cpf": "12345678901"}

    cfg = get_sabia_settings()
    res = run_user_info_fetcher_chain(mock_client, "fake-token", cfg=cfg)

    assert res["cpf"] == "12345678901"
    assert res["ldap_group"] == "sysadmins"
