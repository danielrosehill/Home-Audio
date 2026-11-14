# Music Assistant API notes

Checked 2026-11-14 against music-assistant.io/api and the `music-assistant/server` source
(command decorators in `music_assistant/controllers/**`), server 2.10.x.

- Transport: `POST http://<ma>:8095/api`, body `{"message_id":"1","command":"<name>","args":{...}}`.
  Response over HTTP: the result itself, bare (confirmed 2026-11-14, 2.10.11); errors come as
  HTTP 500 with the traceback only in the server log. The WebSocket wraps results as
  `{"message_id","result"}` or `{"message_id","error_code","details"}`. Do not unwrap a
  bare result's `result` key: setup-flow steps carry `"result": null`.
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

## Setup flows (adding providers), 2.10.x

Checked against `music_assistant/controllers/config/flows.py` at tag 2.10.11 and used live
2026-11-14.

- `config/providers/setup {"provider_domain":"<domain>"}` -> `SetupFlowStep`
  (`flow_id`, `step_id`, `type`: `form|external|progress|finish|abort`, `entries`, `errors`,
  `result`, `reason`). A provider without a setup flow is created at once (`type: finish`).
  `abort` with `reason` `already_configured` (single-instance), `missing_dependency`,
  `provider_retired`.
- `config/flows/submit {"flow_id","values":{<entry key>: value}}` -> the next step;
  `finish` has `result.instance_id`. `config/flows/get {"flow_id"}`, `config/flows/abort`.
- `config/providers/reconfigure {"instance_id"}` starts the same flow for an existing instance.
- `config/providers/save` for a new provider fails: "only possible through the setup flow".
- `podcastfeed` (multi-instance): one entry, `feed_url`. Each feed is its own instance; the
  instance's `config/providers/get` does not show the URL (it is a setup value), so dedupe by
  podcast title from `music/podcasts/library_items`. The feed's episodes appear in the
  library within seconds.
