import pytest
import responses as rsps_lib
from django_sabia_auth.client import SabiaOAuth2Client, SabiaUserInfoError, SabiaAPIError, SabiaAPIClient
from django_sabia_auth.backends import SabiaAuthBackend
from django_sabia_auth.fetchers import DefaultEndpointsUserInfoFetcher, BaseUserInfoFetcher
from django_sabia_auth.mappers import BaseUserMapper, DefaultAttrMapUserMapper, resolve_callable_or_class
from django_sabia_auth.transformers import parse_date, format_cpf, to_upper, to_bool, fetch_image_file
from django_sabia_auth.utils import apply_user_attr_map
from django.contrib.auth import get_user_model

BASE_URL = "https://login.sabia.ufrn.br"
API_URL = "https://api.sabia.ufrn.br"
CLIENT_ID = "cid"
CLIENT_SECRET = "csecret"
REDIRECT_URI = "http://localhost"

@pytest.fixture
def oauth_client():
    return SabiaOAuth2Client(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scopes=["cpf", "email"],
        base_url=BASE_URL,
    )

# --------------------------------------------------
# Client: full URL handling and fallback GET
# --------------------------------------------------
@rsps_lib.activate
def test_get_endpoint_data_full_url_success(oauth_client):
    rsps_lib.add(
        rsps_lib.POST,
        f"{BASE_URL}/api/perfil/dados/",
        json={"cpf": "123"},
        status=200,
    )
    data = oauth_client.get_endpoint_data("tok", f"{BASE_URL}/api/perfil/dados/")
    assert data["cpf"] == "123"

@rsps_lib.activate
def test_get_endpoint_data_fallback_get(oauth_client):
    import requests as req_lib
    rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/api/perfil/dados/", body=req_lib.ConnectionError())
    rsps_lib.add(rsps_lib.GET, f"{BASE_URL}/api/perfil/dados/", json={"ok": True}, status=200)
    result = oauth_client.get_endpoint_data("tok", "/api/perfil/dados/")
    assert result["ok"] is True

# --------------------------------------------------
# Backend: re‑activate inactive user
# --------------------------------------------------
@pytest.mark.django_db
def test_backend_reactivate_inactive(monkeypatch, oauth_client):
    User = get_user_model()
    user = User.objects.create_user(username="12345678901", is_active=False)
    # Mock utils.apply_user_attr_map to return expected mapping
    monkeypatch.setattr('django_sabia_auth.utils.apply_user_attr_map', lambda info, attr_map, cfg=None: {"cpf": "12345678901", "email": "a@b.com"})
    backend = SabiaAuthBackend()
    auth_user = backend.authenticate(None, {"cpf": "12345678901"})
    assert auth_user.pk == user.pk
    assert auth_user.is_active

# --------------------------------------------------
# Fetchers: resolve_callable_or_class errors and dict handling
# --------------------------------------------------
def test_resolve_callable_or_class_invalid():
    with pytest.raises(TypeError):
        resolve_callable_or_class(123)

def test_default_endpoints_user_info_fetcher_skips_error_dict(oauth_client):
    @rsps_lib.activate
    def inner():
        rsps_lib.add(rsps_lib.POST, f"{BASE_URL}/api/perfil/dados/", json={"erro": "bad"}, status=200)
        fetcher = DefaultEndpointsUserInfoFetcher()
        result = fetcher.fetch(oauth_client, "tok", {})
        assert result == {}
    inner()

def test_base_user_info_fetcher_returns_input():
    fetcher = BaseUserInfoFetcher()
    info = {"a": 1}
    assert fetcher.fetch(None, None, info) == info

# --------------------------------------------------
# Mappers: resolve_callable alias and missing key handling
# --------------------------------------------------
def test_resolve_callable_alias():
    # alias should behave same as resolve_callable_or_class
    fn = lambda x: x
    assert resolve_callable_or_class(fn) is fn
    # using alias via import (resolve_callable is defined in mappers)
    from django_sabia_auth.mappers import resolve_callable
    assert resolve_callable(fn) is fn

def test_base_user_mapper_missing_key_and_default():
    mapper = BaseUserMapper()
    user_info = {"cpf": "123"}
    attr_map = {"email": {"key": "email", "default": "default@example.com"}}
    result = mapper.map_attributes(user_info, attr_map)
    assert result["email"] == "default@example.com"

# --------------------------------------------------
# Transformers: cover remaining branches
# --------------------------------------------------
def test_transformers_extra_cases():
    # parse_date with invalid format returns None
    assert parse_date("invalid") is None
    # format_cpf with non‑numeric string returns original
    assert format_cpf("abc") == "abc"
    # to_upper with empty string
    assert to_upper("") == ""
    # to_bool with various truthy values
    for val in ["yes", "True", "1", 1, True]:
        assert to_bool(val) is True
    for val in ["no", "False", "0", 0, False, None]:
        assert to_bool(val) is False

@rsps_lib.activate
def test_transformers_fetch_image_no_ext_and_none():
    assert fetch_image_file(None) is None
    rsps_lib.add(rsps_lib.GET, "http://example.com/avatar", body=b"imgdata", status=200)
    img = fetch_image_file("http://example.com/avatar")
    assert img is not None
    assert img.name == "avatar.jpg"

@pytest.mark.django_db
def test_backend_reactivate_inactive_user_no_other_field_changed(monkeypatch):
    User = get_user_model()
    user = User.objects.create_user(username="99999999999", email="a@b.com", is_active=False)
    monkeypatch.setattr('django_sabia_auth.utils.apply_user_attr_map', lambda info, attr_map, cfg=None: {"cpf": "99999999999", "email": "a@b.com"})
    backend = SabiaAuthBackend()
    auth_user = backend.authenticate(None, {"cpf": "99999999999"})
    assert auth_user.pk == user.pk
    assert auth_user.is_active is True

@rsps_lib.activate
def test_api_client_missing_coverage():
    api_client = SabiaAPIClient(client_id=CLIENT_ID, base_url=API_URL)
    import requests as req_lib
    rsps_lib.add(rsps_lib.GET, f"{API_URL}/usuarios/?cpfs=123&page=1", body=req_lib.ConnectionError())
    with pytest.raises(SabiaAPIError):
        api_client.list_users(["123"])

    rsps_lib.add(rsps_lib.POST, f"{API_URL}/usuarios/", status=500)
    with pytest.raises(SabiaAPIError):
        api_client.create_user("11111111111", "a@b.com", "Ana", "F", "1990-01-01")

def test_fetcher_and_mapper_func_targets():
    import django_sabia_auth.fetchers as fetchers_mod
    import django_sabia_auth.mappers as mappers_mod

    def custom_fetcher(client, access_token, user_info=None):
        user_info = user_info or {}
        user_info["func"] = True
        return user_info

    def custom_mapper(user_info, attr_map=None):
        return {"func": True}

    cfg = {
        "user_info_fetchers": [custom_fetcher],
        "user_info_endpoints": [{}],
        "user_info_mappers": [custom_mapper],
    }

    f_list = fetchers_mod.get_user_info_fetchers(cfg)
    assert len(f_list) == 1
    f_res = fetchers_mod.run_user_info_fetcher_chain(None, "tok", cfg)
    assert f_res["func"] is True

    default_f = fetchers_mod.DefaultEndpointsUserInfoFetcher(sabia_settings=cfg)
    assert default_f.fetch(None, "tok", None) == {}

    m_list = mappers_mod.get_user_info_mappers(cfg)
    assert len(m_list) == 1

def test_mapper_edge_cases():
    import django_sabia_auth.mappers as mappers_mod
    assert mappers_mod._extract_nested({}, None) is None

    def flex_transformer(*args):
        return "flex"

    mapper = mappers_mod.BaseUserMapper()
    res = mapper.map_attributes({}, {"field": {"transform": flex_transformer}})
    assert res["field"] == "flex"

def test_utils_sabia_user_mapper_fallback(settings):
    import django_sabia_auth.utils as utils_mod
    settings.SABIA_CLIENT_ID = "cid"
    settings.SABIA_CLIENT_SECRET = "csec"
    settings.SABIA_REDIRECT_URI = "http://localhost"
    settings.SABIA_USER_MAPPER = "django_sabia_auth.mappers.DefaultAttrMapUserMapper"
    if hasattr(settings, "SABIA_USER_INFO_MAPPERS"):
        delattr(settings, "SABIA_USER_INFO_MAPPERS")
    cfg = utils_mod.get_sabia_settings()
    assert cfg["user_info_mappers"] == ["django_sabia_auth.mappers.DefaultAttrMapUserMapper"]

@rsps_lib.activate
def test_create_user_returns_202_status():
    from django_sabia_auth.client import SabiaAPIClient
    api_client = SabiaAPIClient(client_id=CLIENT_ID, base_url=API_URL)
    rsps_lib.add(rsps_lib.POST, f"{API_URL}/usuarios/", json={"queued": True}, status=202)
    created, data = api_client.create_user("11111111111", "a@b.com", "Ana", "F", "1990-01-01")
    assert created is False
    assert data["queued"] is True

def test_fetcher_dict_endpoints_and_generic_exception():
    class DummyClient:
        def get_endpoint_data(self, token, path):
            if path == "/api/details/":
                return {"age": 30}
            if path == "/api/items/":
                return {"data": [1, 2, 3]}
            if path == "/api/direct/":
                return {"direct_key": "val"}
            if path == "/api/error/":
                raise RuntimeError("Generic network error")
            return {}

    cfg = {
        "user_info_endpoints": [
            {"endpoint": "/api/details/", "namespace": "details"},
            {"endpoint": "/api/items/", "extract_list": "data"},
            {"endpoint": "/api/direct/"},
            {"endpoint": "/api/error/"},
        ]
    }
    fetcher = DefaultEndpointsUserInfoFetcher(sabia_settings=cfg)
    res = fetcher.fetch(DummyClient(), "tok", None)
    assert res.get("details") == {"age": 30}
    assert res.get("direct_key") == "val"

def test_mapper_multi_param_type_error_and_missing_key_dict_spec():
    def multi_param(raw_val, user_info, extra=None):
        raise TypeError("Custom type error")

    mapper = BaseUserMapper()
    # Test transformer raising TypeError when param_count > 2
    try:
        mapper.map_attributes({"a": 1}, {"field": {"key": "a", "transform": multi_param}})
    except TypeError:
        pass
    # Test dict spec with missing key and no default/transform (line 105)
    res2 = mapper.map_attributes({}, {"field2": {"key": "missing_key"}})
    assert "field2" not in res2


