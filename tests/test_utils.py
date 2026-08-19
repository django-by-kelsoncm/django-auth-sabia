import pytest
from django.core.exceptions import ImproperlyConfigured

from django_sabia_auth.utils import apply_user_attr_map, generate_state, get_sabia_settings


def test_get_sabia_settings_returns_dict():
    cfg = get_sabia_settings()
    assert cfg["client_id"] == "test-client-id"
    assert cfg["client_secret"] == "test-client-secret"
    assert cfg["redirect_uri"] == "http://localhost:8000/auth/sabia/callback/"
    assert cfg["scopes"] == ["cpf", "email"]
    assert cfg["base_url"] == "https://login.sabia.ufrn.br"
    assert cfg["api_url"] == "https://api.sabia.ufrn.br"
    assert cfg["user_lookup_field"] == "username"


def test_get_sabia_settings_raises_on_missing(settings):
    del settings.SABIA_CLIENT_ID
    with pytest.raises(ImproperlyConfigured):
        get_sabia_settings()


def test_generate_state_returns_string():
    state = generate_state()
    assert isinstance(state, str)
    assert len(state) > 20


def test_generate_state_is_unique():
    states = {generate_state() for _ in range(10)}
    assert len(states) == 10


# ---------------------------------------------------------------------------
# apply_user_attr_map
# ---------------------------------------------------------------------------

def test_apply_user_attr_map_simple_fields():
    info = {"cpf": "12345678900", "email": "test@example.com"}
    result = apply_user_attr_map(info, {"username": "cpf", "email": "email"})
    assert result == {"username": "12345678900", "email": "test@example.com"}


def test_apply_user_attr_map_name_split():
    info = {"name": "Maria Silva Santos"}
    result = apply_user_attr_map(info, {("first_name", "last_name"): "name"})
    assert result["first_name"] == "Maria"
    assert result["last_name"] == "Silva Santos"


def test_apply_user_attr_map_name_single_word():
    info = {"name": "Cher"}
    result = apply_user_attr_map(info, {("first_name", "last_name"): "name"})
    assert result["first_name"] == "Cher"
    assert result["last_name"] == ""


def test_apply_user_attr_map_name_to_single_field():
    info = {"name": "Maria Silva"}
    result = apply_user_attr_map(info, {"nome_completo": "name"})
    assert result["nome_completo"] == "Maria Silva"


def test_apply_user_attr_map_nested_dotted_key():
    info = {"receita_federal": {"dtNascimento": "1990-05-20", "sexo": "F"}}
    result = apply_user_attr_map(info, {
        "data_nascimento": "receita_federal.dtNascimento",
        "sexo": "receita_federal.sexo",
    })
    assert result["data_nascimento"] == "1990-05-20"
    assert result["sexo"] == "F"


def test_apply_user_attr_map_skips_error_dicts():
    info = {"receita_federal": {"erro": "Dados não validados."}}
    result = apply_user_attr_map(info, {"data_nascimento": "receita_federal.dtNascimento"})
    assert "data_nascimento" not in result


def test_apply_user_attr_map_skips_top_level_error_dict():
    """A top-level key whose value is an error dict should be skipped."""
    info = {"receita_federal": {"erro": "Não validado."}}
    result = apply_user_attr_map(info, {"rf": "receita_federal"})
    assert "rf" not in result


def test_apply_user_attr_map_fulljson():
    info = {"cpf": "12345678900", "cnes": [{"cnes": "001"}]}
    result = apply_user_attr_map(info, {"perfil_json": "fulljson"})
    assert result["perfil_json"] is info


def test_extract_nested_non_dict_mid_path():
    """Traversal through a non-dict intermediate value should return None."""
    from django_sabia_auth.utils import _extract_nested
    info = {"receita_federal": "not_a_dict"}
    assert _extract_nested(info, "receita_federal.dtNascimento") is None


def test_get_sabia_settings_raises_on_missing_secret(settings):
    del settings.SABIA_CLIENT_SECRET
    with pytest.raises(ImproperlyConfigured):
        get_sabia_settings()


def test_get_sabia_settings_raises_on_missing_redirect_uri(settings):
    del settings.SABIA_REDIRECT_URI
    with pytest.raises(ImproperlyConfigured):
        get_sabia_settings()


def test_get_api_client_returns_client():
    from django_sabia_auth.utils import get_api_client
    from django_sabia_auth.client import SabiaAPIClient
    client = get_api_client()
    assert isinstance(client, SabiaAPIClient)


def test_apply_user_attr_map_skips_missing_keys():
    info = {"cpf": "12345678900"}
    result = apply_user_attr_map(info, {"username": "cpf", "email": "email"})
    assert "email" not in result


def test_apply_user_attr_map_skips_none_values():
    info = {"cpf": None}
    result = apply_user_attr_map(info, {"username": "cpf"})
    assert "username" not in result
