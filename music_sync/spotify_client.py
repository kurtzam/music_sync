import string
import secrets
from urllib.parse import urlparse, urlunparse, urlencode

import requests
import pkce

from music_sync.models import SpotifyUserAuthRequest, SpotifyToken


class SpotifyClient:
    def __init__(
        self,
        spotify_client_id: str = "",
        redirect_uri: str = "",
    ) -> None:
        self.spotify_api_base = "https://api.spotify.com"
        self.spotify_client_id = spotify_client_id
        self.redirect_uri = redirect_uri
        self.scope = "user-library-read playlist-read-private"
        self.spotify_token: SpotifyToken

    def _generate_random_string(self, size: int = 128) -> str:
        """
        Generates random string of specified `size` using uppercase, lowercase,
        and digit characters.

        Ref: https://stackoverflow.com/a/63485691/161002
        """
        letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
        random_string: str = "".join(secrets.choice(letters) for _ in range(size))
        return random_string

    def generate_auth_request(self) -> SpotifyUserAuthRequest:
        state = self._generate_random_string(16)
        code_verifier, code_challenge = pkce.generate_pkce_pair(code_verifier_length=128)

        if not self.spotify_client_id:
            raise self.MissingValues("Missing Spotify client ID")
        elif not self.redirect_uri:
            raise self.MissingValues("Missing redirect URI")

        request_args = {
            "response_type": "code",
            "client_id": self.spotify_client_id,
            "scope": self.scope,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "code_challenge_method": "S256",
            "code_challenge": code_challenge,
        }

        # ref: https://stackoverflow.com/questions/2506379/add-params-to-given-url-in-python#2506477
        url_parts = list(urlparse("https://accounts.spotify.com/authorize"))
        url_parts[4] = urlencode(request_args)
        auth_url = urlunparse(url_parts)

        return SpotifyUserAuthRequest(
            auth_url=auth_url,
            state=state,
            code_verifier=code_verifier,
        )

    def request_auth_token(self, code: str, code_verifier: str):
        if not self.spotify_client_id:
            raise self.MissingValues("Missing Spotify client ID")
        elif not self.redirect_uri:
            raise self.MissingValues("Missing redirect URI")

        body_params = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.spotify_client_id,
            "code_verifier": code_verifier
        }
        resp = requests.post(
            url="https://accounts.spotify.com/api/token",
            data=body_params,
        )
        resp.raise_for_status()

        self.spotify_token = SpotifyToken.model_validate_json(resp.text)
        return self.spotify_token

    def get_current_user_profile(self, access_token: str):
        endpoint = "/v1/me"
        resp = requests.get(
            url=f"{self.spotify_api_base}{endpoint}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        resp.raise_for_status()
        resp_json = resp.json()
        return {
            "display_name": resp_json.get("display_name"),
            "images": resp_json.get("images")
        }

    class MissingValues(Exception):
        pass
