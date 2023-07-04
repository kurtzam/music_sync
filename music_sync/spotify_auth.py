import string
import secrets
import hashlib
from base64 import b64encode
from urllib.parse import urlparse, urlunparse, urlencode


class SpotifyAuth:
    def __init__(
        self,
        spotify_api_base: str = "https://api.spotify.com",
        spotify_client_id: str = "1062ee1594ea467798953b9ad30c6eca",
        redirect_uri: str = "http://localhost:5000",
    ) -> None:
        self.spotify_api_base = spotify_api_base
        self.spotify_client_id = spotify_client_id
        self.redirect_uri = redirect_uri

    def generate_random_string(self, size: int = 128) -> str:
        """
        Generates random string of specified `size` using uppercase, lowercase,
        and digit characters.

        Ref: https://stackoverflow.com/a/63485691/161002
        """
        letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
        random_string: str = "".join(secrets.choice(letters) for _ in range(size))
        return random_string

    def sha256_and_b64_encode(self, b: bytes) -> bytes:
        h = hashlib.sha256()
        h.update(b)
        # print(h.digest())
        # print(h.hexdigest())
        return b64encode(h.digest())

    def generate_auth_url(self, code_verifier: bytes) -> str:
        state = self.generate_random_string(16)
        scope = "user-library-read playlist-read-private"
        code_challenge = self.sha256_and_b64_encode(code_verifier)
        request_args = {
            "response_type": "code",
            "client_id": self.spotify_client_id,
            "scope": scope,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "code_challenge_method": "S256",
            "code_challenge": code_challenge,
        }

        # ref: https://stackoverflow.com/questions/2506379/add-params-to-given-url-in-python#2506477
        url_parts = list(urlparse("https://accounts.spotify.com/authorize"))
        url_parts[4] = urlencode(request_args)
        auth_url = urlunparse(url_parts)

        return auth_url


sa = SpotifyAuth()
code_verifier = sa.generate_random_string().encode()
print(sa.generate_auth_url(code_verifier=code_verifier))
