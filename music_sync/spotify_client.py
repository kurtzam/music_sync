import string
import secrets
from urllib.parse import urlparse, urlunparse, urlencode
from uuid import uuid4
import json
from typing import Any

import requests
import pkce

from music_sync.models import (
    SpotifyUserAuthRequest,
    SpotifyToken,
    SpotifyUserProfile,
    SpotifyUserPlaylist,
    SpotifyUserPlaylistTracks,
    SpotifyTrack,
)


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

    def _paginate_get_request(self, access_token: str, endpoint: str, limit: int) -> list[Any]:
        responses = []
        offset = 0
        total = 0
        counter = 0
        while True:
            resp = requests.get(
                url=f"{self.spotify_api_base}{endpoint}",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "limit": limit,
                    "offset": offset
                }
            )
            resp_json = resp.json()
            total = resp_json.get("total")
            resp_items = resp_json.get("items")
            responses.append(resp_items)
            counter += len(resp_items)
            if total <= limit:
                break
            else:
                if counter == total:
                    break
                else:
                    offset = counter
        return responses

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

    def request_auth_token(self, code: str, code_verifier: str) -> SpotifyToken:
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

    def get_current_user_profile(self, access_token: str) -> SpotifyUserProfile:
        endpoint = "/v1/me"
        resp = requests.get(
            url=f"{self.spotify_api_base}{endpoint}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        resp.raise_for_status()
        profile = SpotifyUserProfile.model_validate_json(resp.text)
        return profile

    # TODO use pagination method
    def get_current_user_playlists(
        self,
        access_token: str,
        session_id: str
    ) -> dict[str, list[SpotifyUserPlaylist]]:
        endpoint = "/v1/me/playlists"
        limit = 20
        offset = 0
        total = 0
        counter = 0
        playlists: list[SpotifyUserPlaylist] = []
        while True:
            resp = requests.get(
                url=f"{self.spotify_api_base}{endpoint}",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "limit": limit,
                    "offset": offset
                }
            )
            resp_json = resp.json()
            total = resp_json.get("total")
            resp_playlists = resp_json.get("items")
            counter += len(resp_playlists)
            for p in resp_playlists:
                playlists.append(SpotifyUserPlaylist.model_validate(p))
            if total <= limit:
                break
            else:
                if counter == total:
                    break
                else:
                    offset = counter
        playlist_data_file = f"data/{session_id}-playlists.json"
        playlists_json = [p.model_dump() for p in playlists]
        with open(playlist_data_file, "w") as playlist_fh:
            json.dump(
                playlists_json,
                playlist_fh,
                indent=4,
                default=str
            )
        return {
            "playlists_data_file": playlist_data_file,
            "playlists": playlists
        }

    def get_playlist_tracks(
        self,
        access_token: str,
        playlist_id: str,
        session_id: str
    ) -> SpotifyUserPlaylistTracks:
        endpoint = f"/v1/playlists/{playlist_id}/tracks"
        responses = self._paginate_get_request(
            access_token=access_token,
            endpoint=endpoint,
            limit=50
        )
        tracks: list[SpotifyTrack] = []
        for r in responses:
            for t in r:
                track = SpotifyTrack.model_validate(t["track"])
                tracks.append(track)
        playlist = SpotifyUserPlaylistTracks(
            playlist_id=playlist_id,
            tracks=tracks
        )
        return playlist

    def get_tracks_for_multi_playlists(
        self,
        access_token: str,
        playlist_ids: list[str],
        session_id: str
    ) -> list[SpotifyUserPlaylistTracks]:
        playlists: list[SpotifyUserPlaylistTracks] = []
        for id in playlist_ids:
            playlists.append(self.get_playlist_tracks(access_token=access_token, playlist_id=id, session_id=session_id))
        playlist_tracks_data_file = f"data/{session_id}-playlist_tracks.json"
        playlist_tracks_json = [p.model_dump() for p in playlists]
        with open(playlist_tracks_data_file, "w") as playlist_tracks_fh:
            json.dump(
                playlist_tracks_json,
                playlist_tracks_fh,
                indent=4,
                default=str
            )
        return playlists

    class MissingValues(Exception):
        pass
