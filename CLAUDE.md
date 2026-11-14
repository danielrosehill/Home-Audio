# Home-Audio (plugin `home-audio`)

Public, generic plugin. Follows the Public Plugin, Private Overlay standard
(github.com/danielrosehill/Public-Plugin-Private-Overlay): no hosts, IPs, names or secret
routes in this repo; the user's installation lives in the overlay (`scripts/overlay-paths.sh`).

- Release tier: **small** (`v1.0`, `v1.1`, ...). `plugin.json` version follows semver-ish 1.x.y
  for Claude Code; release tags use the tier.
- `scripts/audioctl.py` is stdlib-only Python; keep it that way (runs on any endpoint).
- MA command names were checked against `music-assistant/server` source (2.10, 2026-11-14).
  When updating, grep `@api_command(` and `register_api_command(` in `music_assistant/controllers`.
- Folded in 2026-11-14 from: `smart-home` (snapcast-ops refs, sc-/sp- commands),
  `media-assistant-ops` (DSP presets, MA reference), `music-assistant-ops` (playlists, logs).
