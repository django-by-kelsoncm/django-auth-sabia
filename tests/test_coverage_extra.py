import pytest
import responses as rsps_lib
from django_sabia_auth.client import SabiaOAuth2Client, SabiaUserInfoError
from django_sabia_auth.mappers import BaseUserMapper, DefaultAttrMapUserMapper, run_user_info_mapper_chain

CLIENT_ID = "test-client-id"
CLIENT_SECRET = "test-secret"
REDIRECT_URI = "http://localhost/callback/"
BASE_URL = "https://login.sabia.ufrn.br"

@pytest.fixture
def oauth_client():
    return SabiaOAuth2Client(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scopes=["cpf", "email"],
        base_url=BASE_URL,
    )

# Ensure that get_endpoint_data raises SabiaUserInfoError on HTTP error codes
@rsps_lib.activate
def test_get_endpoint_data_raises_on_http_error(oauth_client):
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE_URL}/api/perfil/dados/",
        json={"detail": "unauthorized"},
        status=401,
    )
    with pytest.raises(SabiaUserInfoError) as exc:
        oauth_client.get_endpoint_data("dummy", "/api/perfil/dados/")
    assert "HTTP 401" in str(exc.value)

# Ensure that network errors are caught and wrapped in SabiaUserInfoError
@rsps_lib.activate
def test_get_endpoint_data_network_error(oauth_client):
    import requests as req_lib
    rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/api/perfil/dados/", body=req_lib.ConnectionError())
    with pytest.raises(SabiaUserInfoError):
        oauth_client.get_endpoint_data("dummy", "/api/perfil/dados/")

# Test mapper handling of missing keys and default values
def test_base_user_mapper_missing_key_and_default():
    user_info = {"cpf": "12345678901"}
    attr_map = {"email": {"key": "email", "default": "noemail@example.com"}}
    mapper = BaseUserMapper()
    attrs = mapper.map_attributes(user_info, attr_map)
    assert attrs["email"] == "noemail@example.com"

# Test DefaultAttrMapUserMapper uses settings when attr_map not provided
def test_default_attr_map_user_mapper_uses_settings(monkeypatch):
    dummy_cfg = {"user_attr_map": {"name": "fulljson"}}
    mapper = DefaultAttrMapUserMapper(sabia_settings=dummy_cfg)
    result = mapper.map_attributes({"full": "data"})
    assert result["name"] == {"full": "data"}

# Test run_user_info_mapper_chain integrates multiple mappers
def test_run_user_info_mapper_chain_combines_results(monkeypatch):
    # Mock get_user_info_mappers to return a BaseUserMapper and a lambda
    from django_sabia_auth import mappers as mmod
    def fake_mapper(user_info, attr_map=None):
        return {"extra": "value"}
    monkeypatch.setattr(mmod, "get_user_info_mappers", lambda cfg=None: [BaseUserMapper(), fake_mapper])
    user_info = {"cpf": "123"}
    attrs = run_user_info_mapper_chain(user_info)
    assert "extra" in attrs
    assert attrs["extra"] == "value"
