---
name: debug
description: Debug home audio: silent speaker, player missing/offline, dropouts, out of sync, wrong server. Squeezelite, Snapcast, MA, LMS.
---

# Debug

## Load

Overlay `DIR` via `bash ${CLAUDE_PLUGIN_ROOT}/scripts/overlay-paths.sh dir`; read
`installation.json` (what *should* exist), `debug.md`, `endpoints/<host>.md` (known quirks).

## Method: walk the chain, one link at a time

source -> server -> network -> client process -> output device -> amplifier/speaker.
Find the first link that fails. Check the thing itself at each link, not a status that
stands in for it (an "active" unit can be playing to a missing device).

1. **Server sees the player?** `audioctl.py ma-players`, `audioctl.py lms players 0 100`,
   `audioctl.py snap-status`. Note `connected`, `available`, `powered`, the IP it reports.
2. **Network.** From the endpoint: `nc -zv <server> 3483` (Squeezelite) or `1704`/`1705`
   (Snapcast). Wi-Fi: `iw dev wlan0 link`, power save `iw dev wlan0 get power_save`
   (turn it off for audio endpoints).
3. **Client process.** `systemctl status <unit>`, `journalctl -u <unit> -n 100`
   (`--user` for user units). Look for: wrong server IP, "device busy", "No such device",
   reconnect loops, version mismatch.
4. **Device.** Stop the client, `speaker-test -D <device> -c 2 -t sine -l 1`. Check mixer
   levels and mute (`amixer -c <card>`, `alsamixer`). USB speakers re-enumerate after
   reboot or replug: is the `CARD=` name still the same (`aplay -l`)?
5. **Server logs.** Music Assistant: `audioctl.py ma logging/get` if the version has it,
   else `GET <ma>/log` or the HA add-on log (`audioctl.py ha GET /api/hassio/addons/<slug>/logs`,
   needs an admin token). LMS: `server.log` in its config volume. snapserver:
   `journalctl -u snapserver`.
6. Use `${CLAUDE_PLUGIN_ROOT}/reference/troubleshooting.md` (symptom table, all backends) and
   `${CLAUDE_PLUGIN_ROOT}/reference/snapcast/troubleshooting-matrix.md`.

## After the fix

Write it down: `endpoints/<host>.md` gets what was broken, what fixed it, and what was
ruled out; one dated line in `changelog.md`. If the fix generalises, say so.

## Notes

Read-only until a cause is found. Restarting units is a change: say so before doing it.

## Data storage

Writes `endpoints/<host>.md` and `changelog.md` in the overlay.
