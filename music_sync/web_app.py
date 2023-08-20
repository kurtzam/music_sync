from typing import Type
from uuid import uuid4

from flask import Flask, request, session, render_template, redirect, url_for
from pydantic import BaseModel

from music_sync.config import MUSIC_SYNC_CONF
from music_sync.spotify_client import SpotifyClient


app = Flask(__name__)
app.secret_key = MUSIC_SYNC_CONF.music_sync.secret_key


@app.route("/")
def main():
    sc = SpotifyClient(
        spotify_client_id=MUSIC_SYNC_CONF.spotify.client_id,
        redirect_uri=MUSIC_SYNC_CONF.spotify.redirect_uri,
    )
    spotify_auth_req = sc.generate_auth_request()
    session["session_id"] = str(uuid4())
    session["spotify_auth_state"] = spotify_auth_req.state
    session["spotify_code_verifier"] = spotify_auth_req.code_verifier
    return render_template("index.html.jinja", spotify_auth_url=spotify_auth_req.auth_url)


@app.route("/spotify_auth")
def spotify_auth():
    # check args
    for arg in ("code", "state"):
        if not request.args.get(arg):
            raise MissingArguments(f"Missing argument `{arg}`")

    # check state
    if request.args.get("state") != session["spotify_auth_state"]:
        raise StateCheckFailed()

    # check session
    if not session.get("spotify_code_verifier"):
        raise SessionCheckFailed("Missing `spotify_code_verifier`")

    # request access token
    sc = SpotifyClient(
        spotify_client_id=MUSIC_SYNC_CONF.spotify.client_id,
        redirect_uri=MUSIC_SYNC_CONF.spotify.redirect_uri,
    )
    spotify_token_resp = sc.request_auth_token(
        code=request.args.get("code", ""),
        code_verifier=session["spotify_code_verifier"]
    )

    session["spotify_access_token"] = spotify_token_resp.access_token
    # NB maybe keep other things, like the refresh token and timeout

    return redirect(url_for('spotify'))


@app.route("/spotify")
def spotify():
    if not (access_token := session.get("spotify_access_token")):
        return redirect(url_for("spotify_auth"))
    sc = SpotifyClient()
    profile = sc.get_current_user_profile(access_token)
    set_session_model("spotify_profile", profile)
    playlist_data = sc.get_current_user_playlists(access_token=access_token, session_id=session["session_id"])
    session["playlists_data_file"] = playlist_data["playlists_data_file"]
    return render_template(
        "spotify.html.jinja",
        playlists=playlist_data["playlists"],
    )


def set_session_model(session_key: str, session_value: BaseModel):
    session[session_key] = session_value.model_dump()


def get_session_model(session_key: str, model: Type[BaseModel]) -> BaseModel:
    return model.model_validate(session[session_key])


class MissingArguments(Exception):
    pass


class StateCheckFailed(Exception):
    pass


class SessionCheckFailed(Exception):
    pass
