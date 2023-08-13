from flask import Flask, request, session, render_template

from music_sync.config import MUSIC_SYNC_CONF
from music_sync.spotify_auth import SpotifyAuth


app = Flask(__name__)
app.secret_key = MUSIC_SYNC_CONF.music_sync.secret_key


@app.route("/")
def main():
    sa = SpotifyAuth(
        spotify_client_id=MUSIC_SYNC_CONF.spotify.client_id,
        redirect_uri=MUSIC_SYNC_CONF.spotify.redirect_uri,
    )
    spotify_auth_req = sa.generate_auth_request()
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
    sa = SpotifyAuth(
        spotify_client_id=MUSIC_SYNC_CONF.spotify.client_id,
        redirect_uri=MUSIC_SYNC_CONF.spotify.redirect_uri,
    )
    session["spotify_token"] = sa.request_auth_token(
        code=request.args.get("code", ""),
        code_verifier=session["spotify_code_verifier"]
    )

    return "<p>Spotify auth landing page</p>"


class MissingArguments(Exception):
    pass


class StateCheckFailed(Exception):
    pass


class SessionCheckFailed(Exception):
    pass
