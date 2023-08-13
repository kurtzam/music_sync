from pydantic import BaseModel


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
