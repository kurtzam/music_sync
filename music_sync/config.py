from music_sync.models import MusicSyncConfig

with open("config.json") as fh:
    conf_json = fh.read()

MUSIC_SYNC_CONF = MusicSyncConfig.model_validate_json(
    json_data=conf_json,
    strict=True,
)
