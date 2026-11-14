---
name: install-server
description: Install a home audio server: Music Assistant (HA add-on or Docker), Lyrion Music Server, or snapserver. Use on "install the audio server".
---

# Install a server

## Load

Overlay `DIR` via `bash ${CLAUDE_PLUGIN_ROOT}/scripts/overlay-paths.sh dir`; read
`profile.env`, `installation.json`, `install-server.md`. Read `${CLAUDE_PLUGIN_ROOT}/reference/backends.md` to pick.

## Pick the backend (state the choice in one line)

| Want | Install |
| --- | --- |
| One server for Squeezelite, Snapcast, AirPlay, Cast; HA control; streaming providers | **Music Assistant** |
| Mature Squeezebox ecosystem, local library, LMS plugins | **Lyrion Music Server** |
| Tight multi-room sync from any source, no library | **snapserver** (alone, or under MA) |

Never run Lyrion and Music Assistant's Squeezelite provider on the same host: both want
3483. One slimproto server per LAN is the safe default.

## Steps

1. Check the target host: arch, RAM (MA wants ~1 GB free), Docker present, ports free:
   `ss -ltnup | grep -E ':(3483|8095|8097|9000|9090|1704|1705|1780)\b'`.
2. Install with the recipe in `${CLAUDE_PLUGIN_ROOT}/reference/servers.md` for the chosen backend:
   - MA in HA: add-on store, "Music Assistant Server".
   - MA in Docker: `network_mode: host` is required (discovery and stream ports).
   - Lyrion: `lmscommunity/lyrionmusicserver`, host network or macvlan with its own IP.
   - snapserver: distro package or GitHub release `.deb`; check version compatibility with
     MA if MA will drive it (MA's external-server support has version limits; see
     `${CLAUDE_PLUGIN_ROOT}/reference/servers.md`).
3. Prefer a static IP or DHCP reservation for the server. Clients point at it.
4. Verify by asking the server, not by the container state:
   `curl -s http://<h>:8095/info`, `audioctl.py lms serverstatus 0 10`, `audioctl.py snap-status`.
5. Record it in `installation.json` `servers[]` (backend, host, IP, ports, how deployed,
   where the compose file or add-on lives, version, date) and log it in `changelog.md`.
6. Next: `install-client` for endpoints, then `connect-server`.

## Notes

Runs package installs and containers on the target host over SSH: confirm the host first.
Never ask for tokens in chat; name the env var in `profile.env`.

## Data storage

Updates `installation.json` and `changelog.md` in the overlay.
