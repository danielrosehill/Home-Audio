---
name: music-assistant
description: Drive the Music Assistant API: players, playback, volume, queues, playlists, DSP/EQ presets, logs, announcements.
---

# Music Assistant API

## Load

Overlay `DIR` via `bash ${CLAUDE_PLUGIN_ROOT}/scripts/overlay-paths.sh dir`; read
`profile.env` (`HOME_AUDIO_MA_URL`, `HOME_AUDIO_MA_TOKEN_VAR`), `installation.json` (player
names by room) and `music-assistant.md`. Run calls through the user's secrets route if
`profile.env` names one.

`MA="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audioctl.py ma"`: `$MA <command> '<args json>'`.
It POSTs `{"message_id","command","args"}` to `<url>/api` with `Authorization: Bearer <token>`.

## Auth

Every request needs a token (MA 2.x with auth). The user creates a long-lived token in the
MA UI (Settings > Profile, or `auth/token/create`). It goes in the env var named by
`HOME_AUDIO_MA_TOKEN_VAR`, never in a file this plugin writes. HTTP 401 = missing or
expired token. `GET <url>/info` needs no token and gives the version.

## Common jobs (verified against server source, MA 2.10)

| Job | Command and args |
| --- | --- |
| List players | `players/all` (or `audioctl.py ma-players` for a summary) |
| One player | `players/get {"player_id"}`, `players/get_by_name {"name"}` |
| Play / pause / stop / next | `players/cmd/play|pause|play_pause|stop|next|previous {"player_id"}` |
| Volume | `players/cmd/volume_set {"player_id","volume_level":0-100}`; `volume_mute {"player_id","muted"}` |
| Power | `players/cmd/power {"player_id","powered":true}` |
| Play media | `player_queues/play_media {"queue_id":<player_id>,"media":"<uri or list>","option":"play|replace|next|add"}` |
| Find media | `music/search {"search_query","media_types":["track","playlist",...],"limit":5}`; `music/item_by_uri {"uri"}` |
| Queue | `player_queues/get {"queue_id"}`, `player_queues/items {"queue_id","limit","offset"}` |
| Announcement / TTS | `players/cmd/play_announcement {"player_id","url","volume_level"}` |
| Sync players | `players/cmd/set_members {"target_player","player_ids_to_add":[...],"player_ids_to_remove":[...]}`; older: `group_many`, `ungroup` |
| Group player | `players/create_group_player {"provider","name","members":[...]}` |
| Playlists | `music/playlists/library_items`, `music/playlists/create_playlist {"name"}`, `music/playlists/add_playlist_tracks {"db_playlist_id","uris"}`, `music/playlists/remove_playlist_tracks`, `music/playlists/playlist_tracks` |
| DSP | `config/players/dsp/get {"player_id"}`, `config/players/dsp/save {"player_id","config"}`, `config/players/dsp/apply_preset {"player_id","preset_id"}` |
| Player settings | `config/players/get {"player_id"}`, `config/players/save` |
| Providers | `config/providers` |
| Add a provider | `config/providers/setup {"provider_domain"}` returns a form step with `flow_id`; then `config/flows/submit {"flow_id","values":{...}}` until `type` is `finish` (result `instance_id`). `config/providers/save` refuses new providers |
| Add podcasts | `audioctl.py ma-add-podcast <feed url>... [--opml <url>]`: one `podcastfeed` instance per feed via the setup flow (`values: {"feed_url"}`); list with `music/podcasts/library_items` |
| Test playback | `audioctl.py test-play -p <player> -s 10|30|60|90 [--volume N]` (see the debug skill) |
| Logs | `logging/get` (admin scope) |

Names drift between releases. On an unknown-command error, read
`http://<ma>:8095/api-docs` on the user's server and adapt. Full notes:
`${CLAUDE_PLUGIN_ROOT}/reference/music-assistant-api.md`.

## Steps

1. Resolve the target player by room or name from `installation.json`, then confirm the
   `player_id` with `players/all`. Never guess IDs.
2. Run the command. Read back state (`players/get`) to confirm it took effect.
3. **DSP / EQ changes**: first save the current config to
   `DIR/state/dsp-<player>-<date>.json` (the rollback), then build the new config from the
   *shape `dsp/get` returned* plus the preset bands (`overlay-paths.sh template <name>.json`
   finds a preset: the user's `dsp-presets/` wins over built-ins in `${CLAUDE_PLUGIN_ROOT}/templates/dsp/`).
   Save, read back, ask the user to listen. To keep a tuned config, write it to
   `DIR/dsp-presets/<name>.json`.
4. Playlist deletes and provider changes are destructive: confirm first.

## Data storage

Rollback snapshots in `DIR/state/`, user presets in `DIR/dsp-presets/`. Nothing else is written.
