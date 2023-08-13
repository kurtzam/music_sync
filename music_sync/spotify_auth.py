import string
import secrets
import hashlib
from base64 import urlsafe_b64encode
from urllib.parse import urlparse, urlunparse, urlencode

import requests
import pkce

from music_sync.models import SpotifyUserAuthRequest, SpotifyToken


class SpotifyAuth:
    def __init__(
        self,
        spotify_client_id: str,
        redirect_uri: str
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

    def _prepare_code_verifier_and_challenge(self):
        code_verifier_str = self._generate_random_string(128)
        code_verifier_digest = hashlib.sha256(code_verifier_str.encode("utf-8")).digest()
        code_verifier_b64 = urlsafe_b64encode(code_verifier_digest)
        code_challenge = code_verifier_b64.decode("utf-8")[:-1]
        return {
            "code_verifier_str": code_verifier_str,
            "code_verifier_digest": code_verifier_digest,
            "code_verifier_b64": code_verifier_b64,
            "code_challenge": code_challenge,
        }

    def generate_auth_request(self) -> SpotifyUserAuthRequest:
        state = self._generate_random_string(16)
        code_verifier, code_challenge = pkce.generate_pkce_pair(code_verifier_length=128)

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

        self.spotify_token = SpotifyToken.model_validate_json(resp.text)
        return self.spotify_token
