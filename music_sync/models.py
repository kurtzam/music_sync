from typing import Optional, Literal
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


class SpotifyPlaylistTrackSummary(BaseModel):
    href: str
    total: int


class SpotifyExternalUrls(BaseModel):
    spotify: HttpUrl


class SpotifyUserPlaylist(BaseModel):
    description: str
    external_urls: SpotifyExternalUrls
    id: str
    images: list[SpotifyImage]
    name: str
    tracks: SpotifyPlaylistTrackSummary
    uri: str


class SpotifyExternalIds(BaseModel):
    isrc: str


class SpotifyAlbum(BaseModel):
    album_type: str
    name: str


class SpotifyArtist(BaseModel):
    name: str


class SpotifyTrack(BaseModel):
    external_ids: SpotifyExternalIds
    external_urls: SpotifyExternalUrls
    id: str
    name: str
    artists: list[SpotifyArtist]
    album: SpotifyAlbum
    track: bool
    type: Literal["track"]
    uri: str


class SpotifyUserPlaylistTracks(BaseModel):
    playlist_id: str
    tracks: list[SpotifyTrack]
