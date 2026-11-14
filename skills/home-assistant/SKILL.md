---
name: home-assistant
description: Integrate home audio with Home Assistant: MA/Snapcast/Squeezebox integrations, media_player calls, TTS, automations via HA API.
---

# Home Assistant integration

## Load

Overlay `DIR` via `bash ${CLAUDE_PLUGIN_ROOT}/scripts/overlay-paths.sh dir`; read
`profile.env` (`HOME_AUDIO_HA_URL`, `HOME_AUDIO_HA_TOKEN_VAR`), `installation.json`
(`home_assistant` block: entity IDs per endpoint) and `home-assistant.md`.

`HA="python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audioctl.py ha"`: `$HA GET|POST <path> [json]`
with a long-lived access token (HA profile > Security).

## Which integration

| Backend | HA integration | Notes |
| --- | --- | --- |
| Music Assistant (2.4+) | `music_assistant` | Players appear as `media_player.*`; adds actions `music_assistant.play_media`, `search`, `get_library`, `get_queue`, `transfer_queue`, `play_announcement` |
| Lyrion / LMS | `squeezebox` | Do not also add it for MA's Squeezelite provider players; use `music_assistant` |
| snapserver | `snapcast` | Groups and clients as media players; volume, mute, `snapcast.join`/`unjoin` |

Avoid double control: a Squeezelite player under MA should be driven through the
`music_assistant` integration, not also `squeezebox`/`slimproto`.

## Steps

1. **Check what is configured**: `$HA GET /api/config` (version), then integrations via
   `$HA GET /api/config/config_entries/entry` and filter `domain` in
   (`music_assistant`, `snapcast`, `squeezebox`). Map entities: `$HA GET /api/states`
   filtered to `media_player.`.
2. **Add an integration** (when missing): config flow via REST:
   `$HA POST /api/config/config_entries/flow '{"handler":"music_assistant"}'`, then answer
   the returned step (`POST /api/config/config_entries/flow/<flow_id>` with the URL, e.g.
   `{"url":"http://<ma>:8095"}`). MA as an HA add-on is usually auto-discovered: confirm
   the discovered flow instead.
3. **Drive playback**:
   - `$HA POST /api/services/music_assistant/play_media '{"entity_id":"media_player.<x>","media_id":"<name or uri>","media_type":"playlist","enqueue":"replace"}'`
   - Volume: `/api/services/media_player/volume_set` `{"entity_id","volume_level":0.0-1.0}`
   - Group: `/api/services/media_player/join` `{"entity_id","group_members":[...]}`
   - Announce: `/api/services/music_assistant/play_announcement` `{"entity_id","url"}` or
     `tts.speak` with `media_player_entity_id`.
   Add `?return_response` for actions that return data (`search`, `get_queue`).
4. **Automations**: write YAML (`${CLAUDE_PLUGIN_ROOT}/reference/home-assistant.md` has patterns: resume after
   announcement, room follow, night volume cap), show it, then create via
   `$HA POST /api/config/automation/config/<id>` and reload with
   `/api/services/automation/reload`.
5. Record entity IDs per endpoint in `installation.json` `home_assistant.entities`.

## Notes

Config entries and automations change HA: show the payload before posting. Entity IDs
change when an integration is re-added; re-map after.

## Data storage

Updates `home_assistant` in `installation.json` in the overlay.
