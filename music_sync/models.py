from typing import Optional
from pydantic import BaseModel, HttpUrl


class WebAppConfig(BaseModel):
    secret_key: str


class SpotifyConfig(BaseModel):
    client_id: str
    redirect_uri: str


class MusicSyncConfig(BaseModel):
    music_sync: WebAppConfig
    spotify: SpotifyConfig


class SpotifyUserAuthRequest(BaseModel):
    auth_url: str
    state: str
    code_verifier: str


class SpotifyToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str


class SpotifyImage(BaseModel):
    url: str
    height: Optional[int]
    width: Optional[int]


class SpotifyUserProfile(BaseModel):
    id: str
    display_name: str
    images: list[SpotifyImage]


class SpotifyPlaylistTracks(BaseModel):
    href: str
    total: int


class SpotifyExternalUrl(BaseModel):
    spotify: HttpUrl


class SpotifyUserPlaylist(BaseModel):
    description: str
    external_urls: SpotifyExternalUrl
    id: str
    images: list[SpotifyImage]
    name: str
    tracks: SpotifyPlaylistTracks
    uri: str
