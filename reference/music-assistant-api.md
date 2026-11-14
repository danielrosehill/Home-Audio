# Music Assistant API notes

Checked 2026-11-14 against music-assistant.io/api and the `music-assistant/server` source
(command decorators in `music_assistant/controllers/**`), server 2.10.x.

- Transport: `POST http://<ma>:8095/api`, body `{"message_id":"1","command":"<name>","args":{...}}`.
  Response: `{"message_id","result"}` or `{"message_id","error_code","details"}`.
  The UI and HA integration use a WebSocket at `/ws` with the same commands.
- Auth: `Authorization: Bearer <long-lived token>`, created in the UI (Settings > Profile)
  or with `auth/token/create`. Commands carry scopes (e.g. `players:control`,
  `config:players:write`, `system:manage` for `logging/get`); a non-admin token gets 403
  on admin commands.
- Discovery of the API itself: `GET /api-docs` on the running server is authoritative for
  that version. `GET /info` (no auth) gives `server_version`, `homeassistant_addon`, `base_url`.
- Command families: `players/*`, `players/cmd/*`, `player_queues/*`, `music/*`,
  `music/<media_type>s/*` (`library_items`, `get`, `remove`, `count`), `music/playlists/*`,
  `config/players/*`, `config/players/dsp/*`, `config/providers*`, `auth/*`, `logging/get`, `info`.
- `player_queues/play_media`: `queue_id` (usually the player_id), `media` (URI, item, or
  list), `option` (`play`, `replace`, `next`, `replace_next`, `add`), `radio_mode`,
  `start_item`, `shuffle`.
- Syncing: `players/cmd/set_members` (`target_player`, `player_ids_to_add`,
  `player_ids_to_remove`) is current; `group`, `group_many`, `ungroup`, `ungroup_many` remain.
- DSP: `config/players/dsp/get {"player_id"}` returns the DSPConfig; edit and send back with
  `config/players/dsp/save {"player_id","config"}`. Server-side presets:
  `config/players/dsp/apply_preset {"player_id","preset_id"}`. DSP applies to players MA
  streams to (Squeezelite, Snapcast, AirPlay, Cast), not hardware that decodes itself.
- Filter types in MA's parametric EQ: `peaking`, `high_shelf`, `low_shelf`, `high_pass`,
  `low_pass`, `notch`, `all_pass`; plus a preamp gain. Bands unlimited; per-channel optional.
- Playlists: `music/playlists/create_playlist {"name","provider_instance_or_domain"}`,
  `add_playlist_tracks {"db_playlist_id","uris"}`, `remove_playlist_tracks`,
  `playlist_tracks`, `library_items`. (Older notes saying `music/playlists/create` are wrong.)
