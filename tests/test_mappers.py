from datetime import date
from unittest.mock import MagicMock, patch

from django.core.files.base import ContentFile
import pytest

from django_sabia_auth.mappers import BaseSabiaUserMapper, DefaultSabiaUserMapper, resolve_callable
from django_sabia_auth.transformers import fetch_image_file, format_cpf, parse_date, to_bool, to_lower, to_upper
from django_sabia_auth.utils import apply_user_attr_map, get_sabia_settings, get_user_mapper


def test_resolve_callable_direct_func():
    assert resolve_callable(format_cpf) is format_cpf


def test_resolve_callable_import_string():
    fn = resolve_callable("django_sabia_auth.transformers.format_cpf")
    assert fn is format_cpf


def test_resolve_callable_invalid():
    with pytest.raises(TypeError):
        resolve_callable(12345)


def test_transformers_parse_date():
    assert parse_date("1995-01-15") == date(1995, 1, 15)
    assert parse_date(date(2020, 5, 20)) == date(2020, 5, 20)
    assert parse_date("invalid-date") is None
    assert parse_date("") is None


def test_transformers_format_cpf():
    assert format_cpf("12345678901") == "123.456.789-01"
    assert format_cpf("123.456.789-01") == "123.456.789-01"
    assert format_cpf("123") == "123"
    assert format_cpf("") == ""


def test_transformers_to_upper_and_lower():
    assert to_upper("teste") == "TESTE"
    assert to_lower("TESTE") == "teste"


def test_transformers_to_bool():
    assert to_bool(True) is True
    assert to_bool("sim") is True
    assert to_bool("1") is True
    assert to_bool("false") is False
    assert to_bool(0) is False


@patch("requests.get")
def test_transformers_fetch_image_file(mock_get):
    mock_response = MagicMock()
    mock_response.content = b"fake-image-bytes"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_image_file("https://api.sabia.ufrn.br/foto/12345.jpg")
    assert isinstance(result, ContentFile)
    assert result.read() == b"fake-image-bytes"
    assert result.name == "12345.jpg"


@patch("requests.get")
def test_transformers_fetch_image_file_failure(mock_get):
    mock_get.side_effect = Exception("Connection error")
    result = fetch_image_file("https://api.sabia.ufrn.br/foto/12345.jpg")
    assert result is None


def test_mapper_lambda_and_callable_in_attr_map():
    info = {
        "cpf": "12345678901",
        "name": "Maria Silva",
    }
    attr_map = {
        "username": "cpf",
        "full_name": lambda info: f"Dr. {info['name']}",
    }
    mapper = DefaultSabiaUserMapper()
    result = mapper.map_attributes(info, attr_map)

    assert result["username"] == "12345678901"
    assert result["full_name"] == "Dr. Maria Silva"


def test_mapper_dict_spec_with_transformer_and_default():
    info = {
        "cpf": "12345678901",
        "receita_federal": {"dtNascimento": "1990-10-25"},
    }
    attr_map = {
        "cpf": {"key": "cpf", "transform": "django_sabia_auth.transformers.format_cpf"},
        "data_nascimento": {"key": "receita_federal.dtNascimento", "transform": parse_date},
        "role": {"key": "role", "default": "usuario"},
    }
    mapper = DefaultSabiaUserMapper()
    result = mapper.map_attributes(info, attr_map)

    assert result["cpf"] == "123.456.789-01"
    assert result["data_nascimento"] == date(1990, 10, 25)
    assert result["role"] == "usuario"


def test_mapper_skips_dict_with_error():
    info = {
        "cpf": "12345678901",
        "receita_federal": {"erro": "Serviço indisponível"},
    }
    attr_map = {
        "cpf": "cpf",
        "data_nascimento": "receita_federal.dtNascimento",
    }
    mapper = DefaultSabiaUserMapper()
    result = mapper.map_attributes(info, attr_map)

    assert result["cpf"] == "12345678901"
    assert "data_nascimento" not in result


class CustomTestUserMapper(BaseSabiaUserMapper):
    def map_attributes(self, user_info, attr_map=None):
        res = super().map_attributes(user_info, attr_map)
        res["custom_flag"] = True
        return res


def test_custom_user_mapper_setting(settings):
    settings.SABIA_CLIENT_ID = "test-id"
    settings.SABIA_CLIENT_SECRET = "test-secret"
    settings.SABIA_REDIRECT_URI = "http://localhost/callback/"
    settings.SABIA_USER_INFO_MAPPERS = [CustomTestUserMapper]
    settings.SABIA_USER_ATTR_MAP = {"username": "cpf"}

    cfg = get_sabia_settings()
    mapper = get_user_mapper(cfg)
    assert isinstance(mapper, CustomTestUserMapper)

    info = {"cpf": "12345678901"}
    result = apply_user_attr_map(info, cfg["user_attr_map"], cfg=cfg)
    assert result["username"] == "12345678901"
    assert result["custom_flag"] is True
