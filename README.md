# Home Audio

Agent skills for a home network-speaker system, whatever the backend: **Music Assistant**,
**Lyrion (LMS) + Squeezelite**, **Snapcast**, with AirPlay and Spotify Connect endpoints
covered where they meet those. Install servers and endpoint clients, document what is on
the network, change the speaker an endpoint plays to, debug, group rooms, and drive the
**Music Assistant** and **Home Assistant** APIs.

The plugin is generic. Your installation (servers, endpoints, rooms, sinks, history) lives
in a private overlay folder outside the plugin, which the `setup` skill can turn into a
private git repo.

## Skills

| Skill | Does |
| --- | --- |
| `setup` | Creates the private record: `profile.env`, `installation.json`; offers a private repo |
| `inventory` | Scans the LAN, asks each server, reads endpoint configs, writes `installation.json`/`.md` |
| `install-server` | Music Assistant (HA add-on or Docker), Lyrion, or snapserver |
| `install-client` | Squeezelite or snapclient (or shairport-sync, librespot) as a resilient systemd unit |
| `connect-server` | Points clients at a server, enables MA providers, migrates between backends |
| `set-speaker` | Changes an endpoint's output device: ALSA card, PipeWire sink, second speaker |
| `debug` | Walks source -> server -> network -> client -> device; records the fix |
| `groups` | Multi-room sync in MA, Snapcast, LMS or HA |
| `music-assistant` | MA API: players, play media, volume, queues, playlists, DSP presets, logs, announcements |
| `home-assistant` | `music_assistant` / `snapcast` / `squeezebox` integrations, media_player calls, automations |

## `audioctl.py`

One stdlib-only CLI the skills share (`scripts/audioctl.py`, JSON output):

```bash
audioctl.py scan --subnet 192.168.1.0/24   # which hosts expose audio ports
audioctl.py mdns                            # audio-related mDNS services
audioctl.py ma-players                      # Music Assistant players
audioctl.py ma players/cmd/volume_set '{"player_id":"<id>","volume_level":30}'
audioctl.py lms serverstatus 0 100          # LMS, or MA's Squeezelite provider
audioctl.py snap-status                     # Snapcast groups and clients
audioctl.py ha GET /api/states/media_player.kitchen
```

## Overlay (your private data)

`scripts/overlay-paths.sh` prints where it is and why. Order: `$HOME_AUDIO_HOME`,
`$CLAUDE_USER_DATA/home-audio`, `~/.claude-user-data/home-audio` (if that root exists),
`$XDG_DATA_HOME/claude-plugins/home-audio` (if that root exists), else
`~/.claude-user-data/home-audio`.

```
profile.env          settings (keys below)
installation.json    servers, endpoints, groups, HA entities, history
installation.md      human rendering
endpoints/<host>.md  per-endpoint notes and fixes
dsp-presets/*.json   your EQ presets (same name overrides a built-in)
changelog.md         dated changes made by the skills
<skill>.md           private notes for one skill; they override its defaults
```

| Key | Used by | Default |
| --- | --- | --- |
| `HOME_AUDIO_BACKEND` | all | `music-assistant` |
| `HOME_AUDIO_SUBNET` | inventory, setup | none |
| `HOME_AUDIO_MA_URL` | music-assistant, inventory, groups | none |
| `HOME_AUDIO_MA_TOKEN_VAR` | music-assistant | `MA_TOKEN` (name of the env var, not the token) |
| `HOME_AUDIO_LMS` | inventory, groups, debug | none |
| `HOME_AUDIO_SNAPSERVER` | inventory, groups, debug | none |
| `HOME_AUDIO_HA_URL` | home-assistant | none |
| `HOME_AUDIO_HA_TOKEN_VAR` | home-assistant | `HA_TOKEN` |
| `HOME_AUDIO_SSH_USER` | install-*, set-speaker, inventory | SSH config |

Tokens are never written by the plugin; `profile.env` names the environment variables.

## Installation

```bash
claude plugins install home-audio@danielrosehill
```

Then run `setup`.

## History

Replaces the Snapcast and Spotify-network parts of `smart-home`, and the
`media-assistant-ops` and `music-assistant-ops` plugins (2026-11-14).

## License

MIT
