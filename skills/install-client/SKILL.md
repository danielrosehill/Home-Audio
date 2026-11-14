---
name: install-client
description: Install a speaker client on an endpoint (Squeezelite, snapclient) as a reliable systemd service and register it. Use on "add a speaker".
---

# Install a client on an endpoint

## Inputs

Endpoint host (SSH alias or IP), room/player name, backend (default: `HOME_AUDIO_BACKEND`),
output device if known.

## Load

Overlay `DIR` via `bash ${CLAUDE_PLUGIN_ROOT}/scripts/overlay-paths.sh dir`; read
`profile.env`, `installation.json`, `install-client.md` and `endpoints/<host>.md`.

## Pick the client

| Server | Client |
| --- | --- |
| Music Assistant, Squeezelite provider, or Lyrion | `squeezelite` |
| snapserver, or MA's Snapcast provider | `snapclient` |
| MA's AirPlay provider, no extra client wanted | `shairport-sync` (AirPlay 1) |
| Spotify Connect target (no server) | `librespot` / `raspotify` (`${CLAUDE_PLUGIN_ROOT}/reference/spotify-connect/`) |

One endpoint should run one client per output device. Two clients on one ALSA `hw:` device
fight for it.

## Steps

1. Profile the endpoint: `uname -m`, distro, `aplay -l`, whether PipeWire runs
   (`pactl info`), and whether a client is already installed (`${CLAUDE_PLUGIN_ROOT}/reference/clients.md`).
2. Install: `sudo apt install squeezelite` or `snapclient` (Debian/Raspberry Pi OS). For a
   newer snapclient than the distro ships, use the GitHub release `.deb` matching the
   server's version.
3. Choose the output device with `set-speaker` step 1-2 (list, then pick a stable name such
   as `plughw:CARD=<name>,DEV=0`, never a card index).
4. Configure (templates in `${CLAUDE_PLUGIN_ROOT}/templates/systemd/`):
   - Squeezelite, headless: `/etc/default/squeezelite`: `SL_NAME`, `SL_SOUNDCARD`,
     `SB_SERVER_IP`; or a system unit with `-n <name> -o <device> -s <server> -m <mac>`.
     Set `-m` explicitly so the player keeps its identity across NIC changes.
   - Squeezelite on a desktop with PipeWire: user unit, `-o pulse` or `-o pipewire`.
   - snapclient: `/etc/default/snapclient` `SNAPCLIENT_OPTS="--host <server> --hostID <name> --soundcard <device>"`;
     user unit with `--player pulse` when routing through PipeWire.
5. Make it survive: `Restart=always`, `RestartSec=5`, `After=network-online.target`
   (`sound.target` for ALSA, `pipewire.service` for user units). User units need
   `loginctl enable-linger <user>` on headless boxes.
6. Enable and start; confirm the player appears on the server (`audioctl.py ma-players`,
   `lms players 0 100`, `snap-status`), then play a test tone (`speaker-test -D <device> -c2 -t sine -l1`
   with the client stopped, or a play command from the server with it running).
7. Record in `installation.json` `endpoints[]` and `endpoints/<host>.md`; log in `changelog.md`.

## Notes

Uses sudo on the endpoint over SSH. Confirm the host before installing. Audio heard by a
person is the real test; say when only the ALSA level was verified.

## Data storage

Updates `installation.json`, `endpoints/<host>.md` and `changelog.md` in the overlay.
