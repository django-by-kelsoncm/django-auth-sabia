from urllib.parse import urlencode, urljoin

import requests

from .exceptions import SabiaAPIError, SabiaTokenError, SabiaUserInfoError

DEFAULT_BASE_URL = "https://login.sabia.ufrn.br"
DEFAULT_API_URL = "https://api.sabia.ufrn.br"

AUTHORIZE_PATH = "/oauth/authorize/"
TOKEN_PATH = "/oauth/token/"
PROFILE_PATH = "/api/perfil/dados/"


class SabiaOAuth2Client:
    """Handles the OAuth2 authorization code flow with Sabiá."""

    def __init__(self, client_id, client_secret, redirect_uri, scopes=None, base_url=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or ["cpf", "email"]
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._session = requests.Session()

    def get_authorization_url(self, state):
        """Return the full authorization URL to redirect the user to."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
        }
        return f"{self.base_url}{AUTHORIZE_PATH}?{urlencode(params)}"

    def exchange_code_for_token(self, code, timeout=30):
        """Exchange an authorization code for an access token."""
        url = f"{self.base_url}{TOKEN_PATH}"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        try:
            response = self._session.post(url, data=data, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            raise SabiaTokenError(f"Token exchange failed: {exc}") from exc
        except requests.RequestException as exc:
            raise SabiaTokenError(f"Token exchange request error: {exc}") from exc

    def get_endpoint_data(self, access_token, path_or_url, timeout=30):
        """Fetch JSON data from a specific Sabiá API endpoint or full URL."""
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            url = path_or_url
        else:
            url = f"{self.base_url}/{path_or_url.lstrip('/')}"
        headers = {"Authorization": f"Bearer {access_token}"}
        data = {"scope": " ".join(self.scopes)}
        try:
            response = self._session.post(url, headers=headers, data=data, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception:
            try:
                response = self._session.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
                return response.json()
            except Exception as exc:
                raise SabiaUserInfoError(f"Failed to fetch endpoint '{path_or_url}': {exc}") from exc

    def get_user_info(self, access_token, timeout=30):
        """Fetch the authenticated user's profile from Sabiá via the fetcher chain."""
        from .fetchers import run_user_info_fetcher_chain

        return run_user_info_fetcher_chain(self, access_token)


class SabiaAPIClient:
    """Handles the Sabiá user management API."""

    def __init__(self, client_id, base_url=None):
        self.base_url = (base_url or DEFAULT_API_URL).rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Token {client_id}"})

    def get_user(self, cpf_or_email, timeout=30):
        """
        Look up a user by CPF or email.

        Returns a dict on 200, None on 404, raises SabiaAPIError on 403 or other errors.
        """
        url = f"{self.base_url}/usuarios/{cpf_or_email}/"
        try:
            response = self._session.get(url, timeout=timeout)
            if response.status_code == 404:
                return None
            if response.status_code == 403:
                raise SabiaAPIError("Access denied", status_code=403)
            response.raise_for_status()
            return response.json()
        except SabiaAPIError:
            raise
        except requests.HTTPError as exc:
            raise SabiaAPIError(f"API error: {exc}", status_code=exc.response.status_code) from exc
        except requests.RequestException as exc:
            raise SabiaAPIError(f"API request error: {exc}") from exc

    def list_users(self, cpfs, page=1, timeout=30):
        """
        List users by CPF list.

        Returns a list of user dicts.
        """
        cpfs_str = ",".join(cpfs) if isinstance(cpfs, (list, tuple)) else cpfs
        url = f"{self.base_url}/usuarios/?cpfs={cpfs_str}&page={page}"
        try:
            response = self._session.get(url, timeout=timeout)
            if response.status_code == 403:
                raise SabiaAPIError("Access denied", status_code=403)
            response.raise_for_status()
            return response.json()
        except SabiaAPIError:
            raise
        except requests.HTTPError as exc:
            raise SabiaAPIError(f"API error: {exc}", status_code=exc.response.status_code) from exc
        except requests.RequestException as exc:
            raise SabiaAPIError(f"API request error: {exc}") from exc

    def create_user(self, cpf, email, nome, genero, data_de_nascimento, timeout=30):
        """
        Create a new user.

        Returns (True, data) on 201 (created) or (False, data) on 200 (already exists).
        Raises SabiaAPIError on 400, 403, or other errors.
        """
        url = f"{self.base_url}/usuarios/"
        data = {
            "cpf": cpf,
            "email": email,
            "nome": nome,
            "genero": genero,
            "data_de_nascimento": data_de_nascimento,
        }
        try:
            response = self._session.post(url, data=data, timeout=timeout)
            if response.status_code == 201:
                return True, response.json()
            if response.status_code == 200:
                return False, response.json()
            if response.status_code == 403:
                raise SabiaAPIError("Access denied", status_code=403)
            if response.status_code == 400:
                raise SabiaAPIError(f"Bad request: {response.text}", status_code=400)
            response.raise_for_status()
            return False, response.json()
        except SabiaAPIError:
            raise
        except requests.HTTPError as exc:
            raise SabiaAPIError(f"API error: {exc}", status_code=exc.response.status_code) from exc
        except requests.RequestException as exc:
            raise SabiaAPIError(f"API request error: {exc}") from exc
