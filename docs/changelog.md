# Changelog

All notable changes to `django-sabia-auth` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-08-06

### Added

- Arquitetura **Chain of Responsibility** para busca de dados de perfil (`SABIA_USER_INFO_FETCHERS`):
  - `BaseUserInfoFetcher` e `DefaultEndpointsUserInfoFetcher`.
  - Suporte a endpoints configuráveis em `SABIA_USER_INFO_ENDPOINTS` via string, substituição dinâmica (`{cpf}`) e especificações em dicionário (`namespace`, `extract_list`).
- Arquitetura **Chain of Responsibility** para mapeamento de atributos (`SABIA_USER_INFO_MAPPERS`):
  - `BaseUserMapper` e `DefaultAttrMapUserMapper`.
  - Mapeamento avançado com suporte a transformadores em `SABIA_USER_ATTR_MAP` (assinaturas flexíveis de parâmetros).
- Pacote de transformadores (`django_sabia_auth.transformers`):
  - `format_cpf`, `parse_date`, `to_upper`, `to_lower`, `to_bool`, `fetch_image_file` (download de avatares/fotos em Django `ContentFile`).
- Reativação automática de contas inativas no backend de autenticação (`SabiaAuthBackend`).
- Cobertura de testes unitários expandida para **99.59%** com integração `pytest-cov`.

### Fixed

- Tratamento de exceções no cliente OAuth2 (`SabiaOAuth2Client`), propagando `SabiaUserInfoError` em falhas HTTP e mantendo o comportamento de fallback GET.
- Atualização da documentação padrão do endpoint do Sabiá de `/api/v1/userinfo` para `/api/perfil/dados/`.

## [1.1.0] - 2026-04-15

### Added

- Suporte a mapeamento extensível de atributos no perfil de usuário Sabiá.
- Novas opções de configuração `SABIA_USER_LOOKUP_FIELD` e `SABIA_USER_ATTR_MAP`.

## [0.1.0] - 2026-01-01

### Added

- Initial release
- `SabiaOAuth2Client` for OAuth2 authorization code flow
- `SabiaAPIClient` for user management API
- `SabiaAuthBackend` Django authentication backend
- `SabiaLoginView` and `SabiaCallbackView` class-based views
- Utility functions: `get_sabia_settings`, `get_oauth2_client`, `get_api_client`, `generate_state`
- Custom exceptions: `SabiaAuthError`, `SabiaTokenError`, `SabiaUserInfoError`, `SabiaAPIError`, `SabiaStateMismatchError`
- GitHub Actions CI workflow
- Pre-commit configuration
